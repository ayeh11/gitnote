import pdfplumber
from collections import Counter
import os
import asyncio
import json
import re

async def extract_headers(words, normal_font_size, size_threshold):
    headers = []
    current_header = ''
    current_size = None
    current_doctop = None
    last_doctop = None  # Track the position of the last processed word

    for word in words:
        text = word['text']
        size = round(word['size'], 1)
        doctop = word['doctop']

        # Detect headers based on size
        if size >= normal_font_size * size_threshold:
            # If this is the first word of the header or the size is consistent with the current header
            if current_size is None or abs(size - current_size) < 0.1:
                # If this is the first word of a new header (detect via significant doctop gap)
                if current_header == '' or (last_doctop is not None and abs(doctop - last_doctop) > 5):  # Small gap for continuing a header
                    # Append the previous header if it's already populated
                    if current_header:
                        headers.append({
                            'text': current_header.strip(),
                            'doctop': current_doctop
                        })
                        current_header = ''

                    # Start a new header
                    current_header = text
                    current_size = size
                    current_doctop = doctop
                else:
                    # Continue appending words to the current header if on the same line
                    current_header += ' ' + text
            else:
                # Size has changed, so it's likely a new header
                headers.append({
                    'text': current_header.strip(),
                    'doctop': current_doctop
                })
                current_header = text
                current_size = size
                current_doctop = doctop

            last_doctop = doctop  # Update last word position

    # Append the last header if it exists
    if current_header:
        headers.append({
            'text': current_header.strip(),
            'doctop': current_doctop
        })

    return headers


def extract_sections(page, headers):
    sections = []
    # Add a sentinel header at the end to capture text after the last header
    headers.append({'text': None, 'doctop': float('inf')})

    # Get all text elements with their positions
    page_words = page.extract_words(use_text_flow=True, extra_attrs=["doctop"])
    text_elements = [{'text': word['text'], 'doctop': word['doctop']} for word in page_words]

    for i in range(len(headers) - 1):
        start_doctop = headers[i]['doctop']
        end_doctop = headers[i + 1]['doctop']

        # Collect text between current header and next header
        section_text = []
        for element in text_elements:
            if start_doctop < element['doctop'] < end_doctop:
                section_text.append(element['text'])

        # Combine text and parse bullet points
        combined_text = ' '.join(section_text)
        parsed_text = parse_bullet_points(combined_text)

        # Only add sections with non-empty parsed_text
        if parsed_text:  # This will filter out sections with empty text
            sections.append({
                'header': headers[i]['text'],
                'section_text': parsed_text
            })

    # Remove the sentinel header
    headers.pop()

    return sections


def parse_bullet_points(text):
    # Bullet patterns including their Unicode equivalents
    bullet_patterns = [
        r'(\s*[-]\s+)',               # Matches dash bullet (-) 
        r'(\s*\u2022\s+)',            # Matches bullet point (•) (Unicode: \u2022)
        r'(\s*\u25cb\s+)',            # Matches empty bullet point (Unicode: \u25cb)
        r'(\s*\u25aa\s+)',            # Matches black small square bullet (▪) (Unicode: \u25aa)
        r'(\s*\u25cf\s+)',            # Matches black circle bullet (●) (Unicode: \u25cf)
        r'(\s*\d+\.\s+)',             # Matches numbered lists (1. 2. 3.)
        r'(\s*\u2043\s+)'             # Matches hyphen bullet (⁃) (Unicode: \u2043)
    ]

    # Combine all bullet patterns into one regex to split the text
    combined_bullet_pattern = '|'.join(bullet_patterns)

    # Split the text based on bullet points and remove empty strings
    segments = re.split(combined_bullet_pattern, text)

    # Filter out None or empty segments caused by invalid splits
    segments = [segment.strip() for segment in segments if segment and segment.strip()]

    parsed_sections = []
    current_entry = ''

    for segment in segments:
        # Check if this segment is likely a bullet point starter (including unicode characters)
        if re.match(r'^[-\u2022\u25cb\u25aa\u25cf\u2043]|^\d+\.', segment):
            # If we have accumulated text, store it as an entry
            if current_entry:
                parsed_sections.append(current_entry.strip())
                current_entry = ''
            current_entry = segment
        else:
            # If it's part of an ongoing bullet point or subpoint, append it
            current_entry += ' ' + segment

    # Add the last accumulated entry
    if current_entry:
        parsed_sections.append(current_entry.strip())

    # Remove dashes that appear at the start of an entry, but preserve mid-sentence dashes
    parsed_sections = [re.sub(r'^\s*-\s*', '', entry) for entry in parsed_sections]

    # Remove any Unicode bullet characters that remain in the actual text
    unicode_bullet_removal = r'[\u2022\u25cb\u25aa\u25cf\u2043]'
    parsed_sections = [re.sub(unicode_bullet_removal, '', entry) for entry in parsed_sections]

    # Filter out headers or entries with no text content
    parsed_sections = [entry for entry in parsed_sections if entry.strip()]

    return parsed_sections


async def process_pdf(pdf_path, size_threshold=1.2):
    hierarchy = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages):
            words = page.extract_words(extra_attrs=["fontname", "size", "top", "doctop"])
            if not words:
                continue  # Skip pages without words

            # Determine normal font size
            font_sizes = [round(word['size'], 1) for word in words if 'size' in word]
            if not font_sizes:
                continue
            normal_font_size = Counter(font_sizes).most_common(1)[0][0]

            # Extract headers
            headers = await extract_headers(words, normal_font_size, size_threshold)

            if not headers:
                continue  # Skip pages without headers

            # Extract sections based on headers
            sections = extract_sections(page, headers)

            # Build hierarchy
            for section in sections:
                hierarchy.append({
                    'text': section['header'],
                    'page_num': page_number + 1,
                    'section_text': section['section_text'],
                })

    return hierarchy

def convert_headers_to_dict(pdf_id, hierarchy):
    result = {
        'pdf_id': pdf_id,
        'headers': hierarchy
    }
    return result

def save_dict_to_json(data, output_file="headers_dictionary.json"):
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

async def process_pdfs(pdf_paths, size_threshold=1.2):
    header_data = {}
    for pdf_path in pdf_paths:
        pdf_id = os.path.basename(pdf_path)
        hierarchy = await process_pdf(pdf_path, size_threshold)
        header_dict = convert_headers_to_dict(pdf_id, hierarchy)
        header_data[pdf_id] = header_dict
    save_dict_to_json(header_data)

# Testing
async def main():
    pdf_paths = [
        'data/data_ver1.pdf',
        'data/data_ver2.pdf'
    ]
    await process_pdfs(pdf_paths, size_threshold=1.2)

asyncio.run(main())

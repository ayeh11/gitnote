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

    for word in words:
        text = word['text']
        size = round(word['size'], 1)
        doctop = word['doctop']

        if size >= normal_font_size * size_threshold:
            if current_size is None or (abs(size - current_size) < 0.1):
                current_header += ' ' + text
                current_size = size
                current_doctop = doctop
            else:
                # Store the previous header
                headers.append({
                    'text': current_header.strip(),
                    'doctop': current_doctop
                })
                # Reset for the new header
                current_header = text
                current_size = size
                current_doctop = doctop

    # Append the last header
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
    # Bullet patterns
    bullet_patterns = [
        r'(\s*[-•*]\s+)',            # Matches bullets like - Item
        r'(\s*\d+\.\s+)',            # Matches numbered lists: 1. Item
        r'(\s*\(\d+\)\s+)',          # Matches numbered lists: (1) Item
        r'(\s*•\s+)',                # Matches bullet point: • Item
        r'(\s*▪\s+)',                # Matches bullet point: ▪ Item
        r'(\s*●\s+)'                 # Matches bullet point: ● Item
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
        # Check if this segment is likely a bullet point starter
        if re.match(r'^[-•*]|^\d+\.|^\(\d+\)|^•|^▪|^●', segment):
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
        'data/example1.pdf',
        'data/example2.pdf',
        'data/example3.pdf'
    ]
    await process_pdfs(pdf_paths, size_threshold=1.2)

asyncio.run(main())

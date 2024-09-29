import pdfplumber
from collections import Counter
import os
import asyncio
import json

# Extracts and groups headers by font size with a threshold
async def extract_headers(pdf_path, size_threshold=1.2):
    headers = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages):
            words = page.extract_words(extra_attrs=["fontname", "size", "top"])
            
            # Gets text, font size, and line
            word_data = [(word['text'], round(word['size'], 1), word['top']) for word in words if 'size' in word]
            
            if word_data:
                # Get body font size (most common font size)
                font_sizes = [word[1] for word in word_data]
                normal_font_size = Counter(font_sizes).most_common(1)[0][0]
                
                current_header = []
                current_top = None  # Track line of heading
                current_size = None  # Track the current font size
                
                for text, size, top in word_data:
                    if size >= normal_font_size * size_threshold:
                        # If this is the first word or the same size and position as the previous
                        if current_size is None or (abs(top - current_top) < 5 and abs(size - current_size) < 0.1):
                            current_header.append(text)
                            current_top = top
                            current_size = size
                        else:
                            # If the line or size changes, store the header
                            if current_header:
                                headers.append((page_number + 1, ' '.join(current_header), current_size))
                            # Reset for the next header
                            current_header = [text]
                            current_top = top
                            current_size = size
                
                # For the last header on the page
                if current_header:
                    headers.append((page_number + 1, ' '.join(current_header), current_size))
    
    return headers

# Categorize and nest headers like a directory
def group_headers(headers):
    # Get unique font sizes, sorted by descending order
    font_sizes = sorted(set([header[2] for header in headers]), reverse=True)
    
    hierarchy = []
    current_parent = None
    
    # Create a structure where larger headings are parents and smaller headings are children
    for header in headers:
        page_num, header_text, font_size = header
        header_level = font_sizes.index(font_size) + 1
        
        if header_level == 1:  # This is the largest heading (parent)
            current_parent = {'text': header_text, 'children': [], 'page_num': page_num, 'level': header_level}
            hierarchy.append(current_parent)
        elif current_parent:  # This is a smaller heading (child)
            current_parent['children'].append({'text': header_text, 'page_num': page_num, 'level': header_level})
    return hierarchy

# Print the hierarchy in a directory-like structure
def print_headers_pretty(hierarchy, file_handle):
    for item in hierarchy:
        file_handle.write(f"Page {item['page_num']}: Heading {item['level']} - {item['text']}\n")
        for child in item['children']:
            indent = '    ' * (child['level'] - 2)  # Indent based on hierarchy level
            file_handle.write(f"{indent}Page {child['page_num']}: Heading {child['level']} - {child['text']}\n")
        file_handle.write("\n")

# Converts hierarchy to a dictionary
def convert_headers_to_dict(pdf_id, hierarchy):
    result = {
        'pdf_id': pdf_id,
        'headers': []
    }
    
    for item in hierarchy:
        parent_data = {
            'text': item['text'],
            'page_num': item['page_num'],
            'level': item['level'],
            'children': []  
        }
        
        for child in item['children']:
            child_data = {
                'text': child['text'],
                'page_num': child['page_num'],
                'level': child['level']
            }
            parent_data['children'].append(child_data)  

        result['headers'].append(parent_data)
    
    return result

# Save the dictionary to a JSON file
def save_dict_to_json(data, output_file="headers_dictionary.txt"):
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

# Asynchronous function to process multiple PDFs and output results
async def process_pdfs(pdf_paths, size_threshold=1.2):
    header_data = {}
    output_file_pretty='headers_directory.txt'

    with open(output_file_pretty, 'w') as f:  # Open the file in write mode at the start (sync file handling)
        for pdf_path in pdf_paths:
            # Extract the PDF file name from the path
            pdf_id = os.path.basename(pdf_path)
            
            # Write headers to the directory-like file
            headers = await extract_headers(pdf_path, size_threshold)
            hierarchy = group_headers(headers)
            
            # Write results for the current PDF
            f.write(f"Headers for PDF: {pdf_id}\n")
            f.write("=" * (len(pdf_id) + 16) + "\n")
        
            # Write to the pretty directory file
            print_headers_pretty(hierarchy, f)

            # Convert hierarchy to a dictionary into JSON
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

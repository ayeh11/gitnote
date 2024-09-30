# test_client.py

import logging
import json
import time
import nltk
import os
from merge_logic import load_notes_from_files, merge_multiple_notes

# Adjust the directory to point to the directory where your JSON files are located
directory = os.path.join(os.path.dirname(__file__), 'test_files')  # Assuming 'test_files' is in the same directory

def configure_logging():
    """
    Configures logging to write to debug.log with INFO and DEBUG levels.
    Overwrites the debug.log file each time the script runs.
    """
    logging.basicConfig(
        level=logging.DEBUG,  # Set to DEBUG to capture all logs
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("debug.log", mode='w')  # Overwrite debug.log each time
            # No StreamHandler to prevent logging to console
        ]
    )

def main():
    """
    Main function to run the complex test by merging multiple notes from JSON files.
    Measures execution time, logs the process, and saves results to 'merged_results.json'.
    """
    configure_logging()

    # Download necessary NLTK data
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)

    # Start timer
    start_time = time.time()

    print("Starting the merging process...")

    # Load all notes from JSON files in 'test_files' directory
    notes = load_notes_from_files(directory)

    if not notes:
        logging.info("No note files found. Exiting.")
        return

    output_file = "merged_results.json"

    # Perform deduplication-based merging for multiple notes
    merged_text, merged_headers, sentence_to_sources = merge_multiple_notes(notes)

    # Structure the merged results to include conflicts for manual resolution
    headers_output = []
    for merged_header in merged_headers:
        header_name = merged_header['header_name']
        header_id = merged_header['header_id']
        note_id = merged_header['note_id']
        conflicts = merged_header['conflicts']
        bullets_output = []
        for bullet_info in merged_header['bullets']:
            bullet_note_id, bullet_id, bullet_text, _ = bullet_info
            data = merged_header['bullet_to_sources'][bullet_text]
            bullets_output.append({
                "bullet_id": f"{bullet_note_id}_{bullet_id}",
                "accepted_bullet_text": data["text"],
                "conflicting_bullets": data["conflicts"]
            })
        headers_output.append({
            "header_id": header_id,
            "accepted_header_name": header_name,
            "note_id": note_id,
            "conflicting_headers": conflicts,
            "bullets": bullets_output
        })

    # Create the merged_results dictionary
    merged_results = {
        "headers": headers_output
    }

    # Write the comprehensive results to the output JSON file
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(merged_results, f, indent=4)

    # Write the merged text to 'defaultmerge.txt' with actual line breaks
    with open("defaultmerge.txt", "w", encoding='utf-8') as f:
        f.write(merged_text)

    # End timer and calculate the duration
    end_time = time.time()
    time_taken = end_time - start_time

    print(f"Merged results saved to {output_file}")
    print(f"Merged text saved to defaultmerge.txt")
    print(f"Time taken for the merging process: {time_taken:.4f} seconds")

if __name__ == "__main__":
    main()

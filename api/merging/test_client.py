# test_client.py

import logging
import json
import time
import nltk
from merge_logic import load_notes_from_files, merge_multiple_notes

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
    notes = load_notes_from_files(directory="test_files")

    if not notes:
        logging.info("No note files found. Exiting.")
        return

    output_file = "merged_results.json"

    # Perform deduplication-based merging for multiple notes
    merged_text, merged_headers, sentence_to_sources = merge_multiple_notes(notes)

    # Structure the merged results as per your request
    headers_output = []
    for merged_header in merged_headers:
        header_name = merged_header['header_name']
        header_id = merged_header['header_id']
        bullets_output = []
        for bullet_info in merged_header['bullets']:
            note_id, bullet_id, bullet_text, _ = bullet_info
            data = merged_header['bullet_to_sources'][bullet_text]
            bullet_output = {
                "note_id": data["note_id"],
                "bullet_id": data["bullet_id"],
                "text": data["text"],
                "conflicts": data["conflicts"]
            }
            bullets_output.append(bullet_output)
        headers_output.append({
            "note_id": merged_header['note_id'],
            "header_id": header_id,
            "header_name": header_name,
            "conflicts": merged_header['conflicts'],
            "bullets": bullets_output
        })

    # Create the merged_results dictionary
    merged_results = {
        "merged_text": merged_text,
        "headers": headers_output
    }

    # Write the comprehensive results to the output JSON file
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(merged_results, f, indent=4)

    # End timer and calculate the duration
    end_time = time.time()
    time_taken = end_time - start_time

    print(f"Merged results saved to {output_file}")
    print(f"Time taken for the merging process: {time_taken:.4f} seconds")

if __name__ == "__main__":
    main()

import logging
import re
import os
import json
from embedding import generate_embeddings
from faiss_util import create_faiss_index_inner_product, add_embeddings_to_index
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download necessary NLTK data
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# Initialize lemmatizer and stopwords globally for efficiency
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Caches to store preprocessed sentences and embeddings
preprocess_cache = {}
embedding_cache = {}

def preprocess_sentence(sentence):
    """
    Preprocesses a sentence by lowercasing, tokenizing, lemmatizing, and removing stopwords.
    Utilizes caching to avoid redundant processing.
    Additionally calculates the average word length.
    """
    if sentence in preprocess_cache:
        logging.debug(f"Retrieved preprocessed sentence from cache: '{sentence}'")
        return preprocess_cache[sentence]

    words = re.findall(r'\b\w+\b', sentence.lower())
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    preprocessed = ' '.join(lemmatized_words)
    # Calculate average word length
    avg_word_length = np.mean([len(word) for word in lemmatized_words]) if lemmatized_words else 0
    preprocess_cache[sentence] = (preprocessed, avg_word_length)
    logging.debug(f"Preprocessed and cached sentence: '{sentence}' -> '{preprocessed}', avg_word_length: {avg_word_length}")
    return preprocessed, avg_word_length

def preprocess_header(header):
    """
    Preprocesses a header by lowercasing and stripping extra whitespace.
    Avoids removing any content to preserve the full meaning.
    """
    header = header.lower().strip()
    return header  # Do not remove punctuation or stop words

def calculate_overlap_ratio(pre_sentence1, pre_sentence2):
    """
    Calculates the overlap ratio of words between two preprocessed sentences.
    """
    words1 = set(pre_sentence1.split())
    words2 = set(pre_sentence2.split())
    overlap = words1.intersection(words2)
    ratio = len(overlap) / max(len(words1), len(words2)) if max(len(words1), len(words2)) > 0 else 0
    return ratio

def deduplicate_sentences(sentences_info, similarity_threshold=0.7, overlap_threshold=0.3):
    """
    Deduplicates sentences based on cosine similarity and overlap ratio.
    When duplicates are found, keeps the sentence with the highest average word length.
    Ensures conflicts are not nested but are all on the same level.
    """
    if not sentences_info:
        return [], {}

    retained_sentences = []
    retained_preprocessed = []
    sentence_to_sources = {}  # Maps kept sentences to their conflicts

    # Initialize FAISS index for Inner Product
    dimension = sentences_info[0][5].shape[0]  # embeddings are in index 5
    faiss_index = create_faiss_index_inner_product(dimension)

    for idx, (note_num, sentence_idx, sentence, pre_sentence, avg_word_length, embedding) in enumerate(sentences_info):
        sentence_clean = sentence.strip('.')
        logging.debug(f"Processing sentence {idx+1}: '{sentence_clean}' from note {note_num}, sentence {sentence_idx}")

        if faiss_index.ntotal == 0:
            # Retain the first sentence
            retained_sentences.append((note_num, sentence_idx, sentence_clean, avg_word_length))
            retained_preprocessed.append(pre_sentence)
            add_embeddings_to_index(faiss_index, embedding.reshape(1, -1))
            sentence_to_sources[sentence_clean] = {
                "note_id": note_num,
                "bullet_id": sentence_idx,
                "text": sentence_clean,
                "conflicts": []
            }
            logging.info(f"Retained sentence: '{sentence_clean}'")
            continue

        # Query FAISS for all similar sentences
        top_k = faiss_index.ntotal  # Retrieve all to compare with every retained sentence
        D, I = faiss_index.search(embedding.reshape(1, -1), top_k)
        similarities = D[0]
        indices = I[0]

        is_duplicate = False

        for sim, idx_retained in zip(similarities, indices):
            if sim >= similarity_threshold:
                # Calculate overlap ratio
                retained_sentence_tuple = retained_sentences[idx_retained]
                retained_avg_word_length = retained_sentence_tuple[3]
                retained_sentence = retained_sentence_tuple[2]
                retained_note_num = retained_sentence_tuple[0]
                retained_sentence_idx = retained_sentence_tuple[1]
                retained_pre_sentence = retained_preprocessed[idx_retained]
                overlap_ratio = calculate_overlap_ratio(pre_sentence, retained_pre_sentence)

                logging.debug(
                    f"Comparing with retained sentence: '{retained_sentence}' | "
                    f"Similarity: {sim:.4f} | Overlap Ratio: {overlap_ratio:.4f}"
                )

                if overlap_ratio >= overlap_threshold:
                    if avg_word_length > retained_avg_word_length:
                        # Replace the retained sentence with the current one
                        logging.info(
                            f"Replacing retained sentence '{retained_sentence}' (avg word length {retained_avg_word_length:.2f}) "
                            f"with '{sentence_clean}' (avg word length {avg_word_length:.2f}) due to higher average word length."
                        )
                        # Collect all conflicts from the old retained sentence, including itself
                        old_conflicts = sentence_to_sources.pop(retained_sentence)["conflicts"]
                        old_conflicts.append({
                            "note_id": retained_note_num,
                            "bullet_id": retained_sentence_idx,
                            "text": retained_sentence,
                            "similarity": float(sim),
                            "overlap_ratio": float(overlap_ratio)
                        })
                        # Add the old conflicts to the new retained sentence's conflicts
                        sentence_to_sources[sentence_clean] = {
                            "note_id": note_num,
                            "bullet_id": sentence_idx,
                            "text": sentence_clean,
                            "conflicts": old_conflicts
                        }
                        # Update retained_sentences and retained_preprocessed
                        retained_sentences[idx_retained] = (note_num, sentence_idx, sentence_clean, avg_word_length)
                        retained_preprocessed[idx_retained] = pre_sentence
                    else:
                        # Current sentence is a duplicate and will be discarded
                        logging.info(
                            f"Discarding sentence '{sentence_clean}' (avg word length {avg_word_length:.2f}) due to duplication with "
                            f"retained sentence '{retained_sentence}' (avg word length {retained_avg_word_length:.2f})."
                        )
                        conflict_info = {
                            "note_id": note_num,
                            "bullet_id": sentence_idx,
                            "text": sentence_clean,
                            "similarity": float(sim),
                            "overlap_ratio": float(overlap_ratio)
                        }
                        sentence_to_sources[retained_sentence]["conflicts"].append(conflict_info)
                    is_duplicate = True
                    break  # No need to check further

        if not is_duplicate:
            # Retain the sentence
            retained_sentences.append((note_num, sentence_idx, sentence_clean, avg_word_length))
            retained_preprocessed.append(pre_sentence)
            add_embeddings_to_index(faiss_index, embedding.reshape(1, -1))
            sentence_to_sources[sentence_clean] = {
                "note_id": note_num,
                "bullet_id": sentence_idx,
                "text": sentence_clean,
                "conflicts": []
            }
            logging.info(f"Retained sentence: '{sentence_clean}'")

    logging.info(f"Total retained sentences after deduplication: {len(retained_sentences)}")
    return retained_sentences, sentence_to_sources

def load_notes_from_files():
    """
    Loads notes from JSON files in the current directory matching the pattern 'notes.json', 'notes1.json', etc.
    Parses the notes into headers and bullets.
    """
    notes = []
    file_pattern = re.compile(r'^notes(\d*)\.json$')  # Matches 'notes.json', 'notes1.json', etc.
    for file_name in os.listdir():
        match = file_pattern.match(file_name)
        if match and os.path.isfile(file_name):
            note_num = match.group(1)
            note_num = int(note_num) if note_num else 0  # Start from 0 if no number
            logging.debug(f"Loading file: {file_name} as Note {note_num}")
            with open(file_name, 'r', encoding='utf-8') as f:
                note_data = json.load(f)
                headers = []
                # Assuming note_data is a list of sections
                for section in note_data:
                    header_name = section.get('text', 'Default Header')
                    bullets_text = section.get('section-text', '')
                    bullets = [line.strip('- ').strip() for line in bullets_text.split('\n') if line.strip().startswith('- ')]
                    headers.append({
                        'header_name': header_name,
                        'bullets': bullets
                    })
                notes.append({
                    'note_num': note_num,
                    'headers': headers
                })
    # Sort notes based on note_num to maintain order
    notes.sort(key=lambda x: x['note_num'])
    return notes

def merge_multiple_notes(notes, similarity_threshold=0.7, overlap_threshold=0.3, header_similarity_threshold=0.8):
    """
    Merges multiple notes by deduplicating their bullets under similar headers.
    """
    if not notes:
        logging.info("No notes to merge.")
        return "", {}, {}

    # First, collect all headers across all notes
    all_headers = []
    header_id = 0  # Unique ID for each header
    for note in notes:
        note_num = note['note_num']
        for header in note['headers']:
            header_name = header['header_name'].strip().strip(':')
            bullets = header['bullets']
            all_headers.append({
                'header_id': header_id,
                'note_num': note_num,
                'header_name': header_name,
                'bullets': bullets
            })
            header_id += 1

    # Preprocess header names and generate embeddings for all headers
    header_embeddings_list = []
    for header in all_headers:
        header_name = header['header_name'].strip()
        pre_header = preprocess_header(header_name)
        header['preprocessed_name'] = pre_header  # May not be necessary if not used later
        embedding_key = f"{header['note_num']}_{header_name}"
        if embedding_key in embedding_cache:
            embedding = embedding_cache[embedding_key]
            logging.debug(f"Retrieved embedding from cache for header: '{header_name}' with key '{embedding_key}'")
        else:
            embedding = generate_embeddings([header_name], normalize=True)[0]  # Use header_name, not pre_header
            embedding_cache[embedding_key] = embedding
            logging.debug(f"Generated and cached embedding for header: '{header_name}' with key '{embedding_key}'")
        header['embedding'] = embedding
        header_embeddings_list.append(embedding)

    if header_embeddings_list:
        header_embeddings = np.vstack(header_embeddings_list)
    else:
        header_embeddings = np.array([])

    if header_embeddings.size == 0:
        logging.info("No headers to process after parsing.")
        return "", {}, {}

    # Compute similarity matrix
    similarity_matrix = np.dot(header_embeddings, header_embeddings.T)

    # Initialize Union-Find data structure
    parent = [i for i in range(len(all_headers))]  # Initially, each header is its own parent

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]  # Path compression
            u = parent[u]
        return u

    def union(u, v):
        pu = find(u)
        pv = find(v)
        if pu != pv:
            parent[pu] = pv

    # For each pair of headers, check similarity and union
    for i in range(len(all_headers)):
        for j in range(i + 1, len(all_headers)):
            sim = similarity_matrix[i, j]
            if sim >= header_similarity_threshold:
                union(i, j)

    # Now, group headers by their parent
    groups = {}
    for idx in range(len(all_headers)):
        p = find(idx)
        if p not in groups:
            groups[p] = []
        groups[p].append(idx)

    header_groups = list(groups.values())

    # Now, for each header group, process bullets
    merged_headers = []
    sentence_to_sources = {}

    for group in header_groups:
        # Collect bullets from all headers in the group
        group_headers = [all_headers[idx] for idx in group]
        group_bullets_info = []  # Will be similar to sentences_info before

        # Collect conflicts for headers in this group
        conflicts = []
        accepted_header = group_headers[0]['header_name']
        for header in group_headers[1:]:
            conflict_header = header['header_name']
            sim = float(np.dot(header['embedding'], group_headers[0]['embedding']))
            conflicts.append({
                'note_id': header['note_num'],
                'header_id': header['header_id'],
                'header_name': conflict_header,
                'similarity': sim
            })

        for header in group_headers:
            note_num = header['note_num']
            header_name = header['header_name']
            bullets = header['bullets']
            for bullet_idx, bullet in enumerate(bullets):
                pre_bullet, avg_word_length = preprocess_sentence(bullet)
                group_bullets_info.append((
                    note_num,
                    bullet_idx + 1,
                    bullet,
                    pre_bullet,
                    avg_word_length
                ))

        # Deduplicate bullets in this group
        # Preprocess bullets and generate embeddings
        preprocessed_bullets = [info[3] for info in group_bullets_info]

        # Identify unique preprocessed bullets
        unique_pre_bullets = list(set(preprocessed_bullets))
        logging.debug(f"Found {len(unique_pre_bullets)} unique preprocessed bullets in header group.")

        # Generate embeddings for bullets
        bullet_embeddings_list = []
        for pre_bullet in unique_pre_bullets:
            if pre_bullet in embedding_cache:
                embedding = embedding_cache[pre_bullet]
                logging.debug(f"Retrieved embedding from cache for bullet: '{pre_bullet}'")
            else:
                embedding = generate_embeddings([pre_bullet], normalize=True)[0]
                embedding_cache[pre_bullet] = embedding
                logging.debug(f"Generated and cached embedding for bullet: '{pre_bullet}'")
            bullet_embeddings_list.append(embedding)
        if bullet_embeddings_list:
            bullet_embeddings = np.vstack(bullet_embeddings_list)
        else:
            bullet_embeddings = np.array([])

        pre_bullet_to_emb = {pre: emb for pre, emb in zip(unique_pre_bullets, bullet_embeddings)}

        # Assign embeddings to bullets
        bullets_info = []
        for info in group_bullets_info:
            note_num, bullet_idx, bullet, pre_bullet, avg_word_length = info
            embedding = pre_bullet_to_emb[pre_bullet]
            bullets_info.append((note_num, bullet_idx, bullet, pre_bullet, avg_word_length, embedding))

        # Deduplicate bullets
        merged_bullets, bullet_to_sources = deduplicate_sentences(
            bullets_info,
            similarity_threshold,
            overlap_threshold
        )

        # Collect merged bullets and their conflicts
        merged_header = {
            'header_name': accepted_header,
            'header_id': group_headers[0]['header_id'],
            'note_id': group_headers[0]['note_num'],
            'bullets': merged_bullets,
            'bullet_to_sources': bullet_to_sources,
            'conflicts': conflicts
        }
        merged_headers.append(merged_header)
        # Update sentence_to_sources
        sentence_to_sources.update(bullet_to_sources)

    # Construct the merged text
    merged_text_lines = []
    for merged_header in merged_headers:
        merged_text_lines.append(f"{merged_header['header_name']}:")
        for bullet in merged_header['bullets']:
            bullet_text = bullet[2]  # bullet[2] is the bullet text
            merged_text_lines.append(f"- {bullet_text}")

    merged_text = '\n'.join(merged_text_lines)

    return merged_text, merged_headers, sentence_to_sources

def run_complex_test():
    """
    Executes a comprehensive test by merging multiple notes from JSON files.
    Outputs merged text and detailed merge information to a single JSON file.
    """
    # Configure logging to write to debug.log with INFO and DEBUG levels
    logging.basicConfig(
        level=logging.DEBUG,  # Set to DEBUG to show DEBUG and higher level logs
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
        ]
    )

    # Load all notes from JSON files
    notes = load_notes_from_files()
    
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

    logging.info(f"Merged results saved to {output_file}")

if __name__ == "__main__":
    run_complex_test()

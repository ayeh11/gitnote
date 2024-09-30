# merge_logic.py

import logging
import re
import os
import json
import numpy as np
from preprocess import preprocess_sentence, preprocess_header
from deduplication import deduplicate_sentences
from embedding import generate_embeddings
from faiss_util import create_faiss_index_inner_product, add_embeddings_to_index

# Caches to store embeddings
embedding_cache = {}

def calculate_overlap_ratio_headers(header1, header2):
    """
    Calculates the overlap ratio of words between two headers.
    """
    words1 = set(header1.lower().split())
    words2 = set(header2.lower().split())
    overlap = words1.intersection(words2)
    ratio = len(overlap) / max(len(words1), len(words2)) if max(len(words1), len(words2)) > 0 else 0
    return ratio

def load_notes_from_files(directory="test_files"):
    """
    Loads notes from JSON files in the specified directory.
    Parses the notes into headers and bullets.

    Parameters:
        directory (str): Path to the directory containing JSON note files.

    Returns:
        notes (list): List of notes with headers and bullets.
    """
    notes = []
    file_pattern = re.compile(r'^notes(\d*)\.json$')  # Matches 'notes.json', 'notes1.json', etc.
    for file_name in os.listdir(directory):
        match = file_pattern.match(file_name)
        if match and os.path.isfile(os.path.join(directory, file_name)):
            note_num = match.group(1)
            note_num = int(note_num) if note_num else 0  # Start from 0 if no number
            logging.debug(f"Loading file: {file_name} as Note {note_num}")
            with open(os.path.join(directory, file_name), 'r', encoding='utf-8') as f:
                note_data = json.load(f)
                headers = []
                # Assuming note_data is a list of sections
                for section in note_data:
                    header_name = section.get('text', 'Default Header')
                    bullets_text = section.get('section-text', '')
                    bullets = [line.strip('- ').strip() for line in bullets_text.split('\n') if line.strip().startswith('-')]
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

    Parameters:
        notes (list): List of notes with headers and bullets.
        similarity_threshold (float): Cosine similarity threshold to consider duplicate bullets.
        overlap_threshold (float): Overlap ratio threshold to consider duplicate bullets.
        header_similarity_threshold (float): Cosine similarity threshold to consider duplicate headers.

    Returns:
        merged_text (str): The merged text of all notes.
        merged_headers (list): Detailed information about merged headers and bullets.
        sentence_to_sources (dict): Mapping of retained sentences to their sources and conflicts.
    """
    if not notes:
        logging.info("No notes to merge.")
        return "", [], {}

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
    logging.info("Generating embeddings for headers...")
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
        return "", [], {}

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
    logging.info("Comparing headers for similarity and overlap...")
    for i in range(len(all_headers)):
        for j in range(i + 1, len(all_headers)):
            sim = similarity_matrix[i, j]
            # Compute overlap ratio between headers
            overlap_ratio = calculate_overlap_ratio_headers(all_headers[i]['header_name'], all_headers[j]['header_name'])
            # Output the similarity and overlap scores to debug log
            logging.debug(f"Headers '{all_headers[i]['header_name']}' and '{all_headers[j]['header_name']}' have similarity {sim:.4f} and overlap ratio {overlap_ratio:.4f}")
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

    for group_idx, group in enumerate(header_groups, 1):
        # Collect bullets from all headers in the group
        group_headers = [all_headers[idx] for idx in group]
        group_bullets_info = []  # Will be similar to sentences_info before

        # Collect conflicts for headers in this group
        conflicts = []
        accepted_header = group_headers[0]['header_name']
        for header in group_headers[1:]:
            conflict_header = header['header_name']
            sim = float(np.dot(header['embedding'], group_headers[0]['embedding']))
            # Compute overlap ratio
            overlap_ratio = calculate_overlap_ratio_headers(group_headers[0]['header_name'], header['header_name'])
            conflicts.append({
                "note_id": header['note_num'],
                "header_id": header['header_id'],
                "header_name": conflict_header,
                "similarity": sim,
                "overlap_ratio": overlap_ratio
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
        logging.debug(f"Found {len(unique_pre_bullets)} unique preprocessed bullets in header group '{accepted_header}'.")

        # Generate embeddings for bullets
        logging.info(f"Generating embeddings for bullets in header '{accepted_header}' (Group {group_idx}/{len(header_groups)})...")
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

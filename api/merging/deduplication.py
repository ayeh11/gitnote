# deduplication.py

import logging
import numpy as np
from faiss_util import create_faiss_index_inner_product, add_embeddings_to_index

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
    
    Parameters:
        sentences_info (list of tuples): Each tuple contains:
            (note_num, sentence_idx, sentence, pre_sentence, avg_word_length, embedding)
        similarity_threshold (float): Cosine similarity threshold to consider duplicates.
        overlap_threshold (float): Overlap ratio threshold to consider duplicates.
    
    Returns:
        retained_sentences (list of tuples): Sentences retained after deduplication.
        sentence_to_sources (dict): Mapping of retained sentences to their sources and conflicts.
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

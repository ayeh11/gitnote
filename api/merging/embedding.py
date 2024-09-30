# embedding.py

import numpy as np
from sentence_transformers import SentenceTransformer
import logging
import warnings

# Suppress the FutureWarning from transformers
warnings.filterwarnings("ignore", category=FutureWarning)

# Load the transformer model once globally for efficiency
model = SentenceTransformer('paraphrase-mpnet-base-v2')  # More effective for paraphrase detection

# Function to generate embeddings for a list of texts using a pre-trained transformer model
def generate_embeddings(texts, normalize=True):
    logging.debug(f"Generating embeddings for {len(texts)} texts.")
    embeddings = model.encode(
        texts,
        convert_to_tensor=False,
        batch_size=64,
        show_progress_bar=False  # Suppress progress bar
    )
    embeddings = np.array(embeddings).astype('float32')  # Ensure float32 for FAISS
    if normalize:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        logging.debug("Normalized embeddings to unit vectors.")
    logging.debug(f"Generated embeddings shape: {embeddings.shape}")
    return embeddings

# Function to compute sentence-level similarity using cosine similarity on embeddings
def semantic_sentence_similarity(sentence1, sentence2):
    logging.debug(f"Comparing sentences: '{sentence1}' and '{sentence2}'")
    embeddings = model.encode(
        [sentence1, sentence2],
        convert_to_tensor=False,
        clean_up_tokenization_spaces=True,
        show_progress_bar=False  # Suppress progress bar
    )
    embeddings = np.array(embeddings).astype('float32')
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    similarity = np.dot(embeddings[0], embeddings[1])
    logging.debug(f"Similarity between sentences: {similarity:.4f}")
    return similarity

# faiss_util.py

import faiss
import numpy as np
import logging

# Function to create a FAISS index for Inner Product (to use with normalized embeddings)
def create_faiss_index_inner_product(dimension):
    index = faiss.IndexFlatIP(dimension)  # Inner Product for cosine similarity
    logging.debug(f"FAISS IndexFlatIP created for dimension: {dimension}.")
    return index

# Function to add embeddings to the FAISS index
def add_embeddings_to_index(index, embeddings):
    index.add(embeddings.astype(np.float32))  # Add embeddings to the FAISS index
    logging.debug(f"Added {embeddings.shape[0]} embeddings to FAISS index. Total embeddings: {index.ntotal}.")

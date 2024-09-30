# preprocess.py

import re
import logging
import numpy as np
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Initialize lemmatizer and stopwords globally for efficiency
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Caches to store preprocessed sentences
preprocess_cache = {}

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

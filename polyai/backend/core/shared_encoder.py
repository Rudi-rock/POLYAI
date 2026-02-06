"""
PolyAI Shared Encoder

Purpose: Single lightweight text representation layer shared by all agents.
Instead of multiple big models, we use ONE tiny shared encoder + multiple logic heads.

This encoder uses TF-IDF based vectorization (no external model needed):
- Keyword extraction using frequency analysis
- Sentence importance scoring
- Estimated ~3MB memory footprint

Why shared?
- Saves memory
- Ensures consistency across agents
- Avoids duplicate embeddings
"""

import re
import math
from typing import Dict, List, Any, Set
from collections import Counter

# Stop words to filter out
STOP_WORDS: Set[str] = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
    'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
    'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
    'below', 'between', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
    'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but',
    'if', 'or', 'because', 'until', 'while', 'this', 'that', 'these',
    'those', 'it', 'its', 'i', 'you', 'he', 'she', 'we', 'they', 'what',
    'which', 'who', 'whom', 'their', 'your', 'our', 'my', 'his', 'her'
}

# Key indicators that boost sentence importance
KEY_INDICATORS: List[str] = [
    'key', 'important', 'main', 'essential', 'critical', 'significant',
    'primary', 'focus', 'crucial', 'vital', 'fundamental', 'core',
    'because', 'therefore', 'thus', 'result', 'conclusion', 'summary',
    'in conclusion', 'to summarize', 'overall', 'finally', 'however',
    'consequently', 'hence', 'accordingly'
]


def encode(processed_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create shared encoding for text.
    
    Args:
        processed_input: Output from input_processor.process()
        
    Returns:
        Dictionary containing:
        - term_frequencies: Word frequency counts
        - tf_idf: TF-IDF scores for terms
        - keywords: Extracted keywords with scores
        - sentence_scores: Importance score for each sentence
        - key_sentences: Indices of most important sentences
    """
    if not processed_input or not processed_input.get('sentences'):
        return {
            "term_frequencies": {},
            "tf_idf": {},
            "keywords": [],
            "sentence_scores": [],
            "key_sentences": []
        }
    
    sentences = processed_input['sentences']
    words = processed_input.get('words', [])
    
    # Step 1: Calculate term frequencies
    term_freq = calculate_term_frequencies(words)
    
    # Step 2: Calculate TF-IDF scores
    tf_idf = calculate_tf_idf(sentences)
    
    # Step 3: Extract keywords
    keywords = extract_keywords(term_freq, tf_idf)
    
    # Step 4: Score sentences
    sentence_scores = score_sentences(sentences, keywords, tf_idf)
    
    # Step 5: Identify key sentences (top 30%)
    n_key = max(1, len(sentences) // 3)
    sorted_indices = sorted(range(len(sentence_scores)), 
                           key=lambda i: sentence_scores[i], 
                           reverse=True)
    key_sentences = sorted_indices[:n_key]
    
    return {
        "term_frequencies": term_freq,
        "tf_idf": tf_idf,
        "keywords": keywords,
        "sentence_scores": sentence_scores,
        "key_sentences": key_sentences
    }


def calculate_term_frequencies(words: List[str]) -> Dict[str, int]:
    """Calculate frequency of each term, excluding stop words."""
    filtered = [w.lower() for w in words 
                if w.lower() not in STOP_WORDS and len(w) > 2]
    return dict(Counter(filtered))


def calculate_tf_idf(sentences: List[str]) -> Dict[str, float]:
    """
    Calculate TF-IDF scores for all terms.
    
    TF-IDF = Term Frequency × Inverse Document Frequency
    Higher score = more important/distinctive term
    """
    if not sentences:
        return {}
    
    n_docs = len(sentences)
    
    # Document frequency: how many sentences contain each term
    doc_freq: Dict[str, int] = {}
    
    # Term frequency across all sentences
    all_terms: List[str] = []
    
    for sentence in sentences:
        words = set(re.findall(r'\b\w+\b', sentence.lower()))
        for word in words:
            if word not in STOP_WORDS and len(word) > 2:
                doc_freq[word] = doc_freq.get(word, 0) + 1
                all_terms.append(word)
    
    # Calculate TF-IDF for each term
    term_counts = Counter(all_terms)
    total_terms = len(all_terms) or 1
    
    tf_idf: Dict[str, float] = {}
    for term, count in term_counts.items():
        tf = count / total_terms
        df = doc_freq.get(term, 1)
        idf = math.log((n_docs + 1) / (df + 1)) + 1
        tf_idf[term] = tf * idf
    
    return tf_idf


def extract_keywords(term_freq: Dict[str, int], 
                    tf_idf: Dict[str, float],
                    top_n: int = 15) -> List[Dict[str, Any]]:
    """
    Extract top keywords based on frequency and TF-IDF.
    
    Returns list of keywords with their scores.
    """
    if not term_freq:
        return []
    
    # Combine frequency and TF-IDF scores
    combined_scores: Dict[str, float] = {}
    max_freq = max(term_freq.values()) or 1
    max_tfidf = max(tf_idf.values()) if tf_idf else 1
    
    for term, freq in term_freq.items():
        norm_freq = freq / max_freq
        norm_tfidf = tf_idf.get(term, 0) / max_tfidf if max_tfidf else 0
        # Combined score: weighted average
        combined_scores[term] = (0.4 * norm_freq) + (0.6 * norm_tfidf)
    
    # Sort and get top keywords
    sorted_terms = sorted(combined_scores.items(), 
                         key=lambda x: x[1], 
                         reverse=True)
    
    return [{"term": t, "score": round(s, 4)} for t, s in sorted_terms[:top_n]]


def score_sentences(sentences: List[str], 
                   keywords: List[Dict[str, Any]],
                   tf_idf: Dict[str, float]) -> List[float]:
    """
    Score each sentence for importance.
    
    Factors:
    - Position (first/last sentences weighted higher)
    - Keyword density
    - Key indicator presence
    - Sentence length (prefer medium length)
    """
    if not sentences:
        return []
    
    keyword_set = {kw['term'].lower() for kw in keywords}
    scores = []
    n = len(sentences)
    
    for i, sentence in enumerate(sentences):
        score = 0.0
        words = sentence.lower().split()
        word_count = len(words)
        
        # Position score (first 2 and last sentence)
        if i < 2:
            score += 0.3
        if i == n - 1:
            score += 0.2
        
        # Keyword density
        keyword_matches = sum(1 for w in words if w in keyword_set)
        if word_count > 0:
            score += 0.3 * (keyword_matches / word_count)
        
        # Key indicator bonus
        sentence_lower = sentence.lower()
        for indicator in KEY_INDICATORS:
            if indicator in sentence_lower:
                score += 0.15
                break  # Only count once
        
        # Length preference (10-30 words is ideal)
        if 10 <= word_count <= 30:
            score += 0.1
        elif word_count < 5:
            score -= 0.1  # Penalize very short
        
        # TF-IDF boost for sentences with high-scoring terms
        tfidf_sum = sum(tf_idf.get(w, 0) for w in words)
        score += 0.1 * min(tfidf_sum / 10, 0.3)  # Cap boost
        
        scores.append(round(score, 4))
    
    return scores


def get_important_terms(encoding: Dict[str, Any], top_n: int = 10) -> List[str]:
    """Get list of most important terms."""
    keywords = encoding.get('keywords', [])
    return [kw['term'] for kw in keywords[:top_n]]


def get_key_sentence_indices(encoding: Dict[str, Any]) -> List[int]:
    """Get indices of key sentences."""
    return encoding.get('key_sentences', [])

"""
PolyAI Input Processor

Purpose: Normalize and clean text for efficient processing by tiny models.
Every wasted token hurts reasoning quality in a <10MB system.

Operations:
- Lowercasing
- Sentence segmentation
- Noise removal (URLs, emails, special chars)
- Token trimming
- Whitespace normalization
"""

import re
from typing import Dict, List, Any

# Maximum words to process (prevents memory issues)
MAX_WORDS = 500

# Noise patterns to remove
URL_PATTERN = re.compile(r'https?://[^\s]+', re.IGNORECASE)
EMAIL_PATTERN = re.compile(r'[\w.-]+@[\w.-]+\.\w+', re.IGNORECASE)
SPECIAL_CHARS_PATTERN = re.compile(r'[^\w\s.,!?;:\'"()-]')


def process(text: str) -> Dict[str, Any]:
    """
    Main processing function.
    
    Args:
        text: Raw input text from user
        
    Returns:
        Dictionary containing:
        - original: Original text
        - normalized: Cleaned text
        - sentences: List of sentences
        - words: List of words
        - word_count: Total word count
        - truncated: Whether text was trimmed
    """
    if not text:
        return {
            "original": "",
            "normalized": "",
            "sentences": [],
            "words": [],
            "word_count": 0,
            "truncated": False
        }
    
    original = text.strip()
    processed = text
    
    # Step 1: Remove URLs
    processed = URL_PATTERN.sub('', processed)
    
    # Step 2: Remove email addresses
    processed = EMAIL_PATTERN.sub('', processed)
    
    # Step 3: Remove special characters (keep basic punctuation)
    processed = SPECIAL_CHARS_PATTERN.sub(' ', processed)
    
    # Step 4: Normalize whitespace
    processed = re.sub(r'\s+', ' ', processed).strip()
    
    # Step 5: Sentence segmentation
    sentences = segment_sentences(processed)
    
    # Step 6: Word tokenization
    words = processed.lower().split()
    
    # Step 7: Truncate if too long
    truncated = False
    if len(words) > MAX_WORDS:
        words = words[:MAX_WORDS]
        truncated = True
        # Rebuild processed text from truncated words
        processed = ' '.join(words)
        sentences = segment_sentences(processed)
    
    return {
        "original": original,
        "normalized": processed,
        "sentences": sentences,
        "words": words,
        "word_count": len(words),
        "truncated": truncated
    }


def segment_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Uses simple regex-based splitting on sentence-ending punctuation.
    Handles common abbreviations to avoid false splits.
    """
    if not text:
        return []
    
    # Common abbreviations to preserve
    abbreviations = ['Mr.', 'Mrs.', 'Dr.', 'Prof.', 'Sr.', 'Jr.', 'vs.', 'etc.', 'e.g.', 'i.e.']
    
    # Temporarily replace abbreviations
    temp_text = text
    placeholders = {}
    for i, abbr in enumerate(abbreviations):
        placeholder = f'__ABBR{i}__'
        placeholders[placeholder] = abbr
        temp_text = temp_text.replace(abbr, placeholder)
    
    # Split on sentence boundaries
    raw_sentences = re.split(r'(?<=[.!?])\s+', temp_text)
    
    # Restore abbreviations
    sentences = []
    for s in raw_sentences:
        for placeholder, abbr in placeholders.items():
            s = s.replace(placeholder, abbr)
        s = s.strip()
        if s and len(s) > 5:  # Skip very short fragments
            sentences.append(s)
    
    return sentences


def count_words(text: str) -> int:
    """Count words in text."""
    if not text:
        return 0
    return len(text.split())


def get_sentences_by_position(sentences: List[str], positions: List[str]) -> List[str]:
    """
    Get sentences by position indicators.
    
    Args:
        sentences: List of sentences
        positions: List of position types ('first', 'last', 'middle')
    
    Returns:
        Selected sentences
    """
    if not sentences:
        return []
    
    selected = []
    n = len(sentences)
    
    for pos in positions:
        if pos == 'first' and n > 0:
            selected.append(sentences[0])
        elif pos == 'last' and n > 0:
            selected.append(sentences[-1])
        elif pos == 'middle' and n > 2:
            mid_idx = n // 2
            selected.append(sentences[mid_idx])
    
    return selected

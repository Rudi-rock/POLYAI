"""
PolyAI Simplification Agent

Purpose: Reduce complexity and improve readability of the summary.
This is the "Editor" agent that makes text more accessible.

Strategy:
1. Replace complex words with simpler alternatives
2. Break long sentences into shorter ones
3. Remove redundancy
4. Improve sentence flow
5. Calculate readability metrics
"""

from typing import Dict, Any, List, Tuple
import re


# Complex word replacements
SIMPLIFICATIONS: Dict[str, str] = {
    'utilize': 'use',
    'implement': 'set up',
    'facilitate': 'help',
    'demonstrate': 'show',
    'significant': 'important',
    'approximately': 'about',
    'subsequently': 'then',
    'consequently': 'so',
    'nevertheless': 'but',
    'furthermore': 'also',
    'additionally': 'also',
    'therefore': 'so',
    'however': 'but',
    'regarding': 'about',
    'concerning': 'about',
    'commence': 'start',
    'terminate': 'end',
    'purchase': 'buy',
    'sufficient': 'enough',
    'numerous': 'many',
    'establish': 'set up',
    'accomplish': 'do',
    'endeavor': 'try',
    'component': 'part',
    'indicate': 'show',
    'determine': 'find',
    'obtain': 'get',
    'require': 'need',
    'assist': 'help',
    'prior': 'before',
    'subsequent': 'after',
    'initiate': 'start',
    'finalize': 'finish',
    'modifications': 'changes',
    'methodology': 'method',
    'functionality': 'function',
    'capability': 'ability',
    'characteristics': 'traits',
    'circumstances': 'conditions'
}


def run(processed_input: Dict[str, Any],
        encoding: Dict[str, Any],
        reasoning_result: Dict[str, Any],
        **kwargs) -> Dict[str, Any]:
    """
    Run the Simplification Agent.
    
    Args:
        processed_input: Output from input_processor
        encoding: Output from shared_encoder
        reasoning_result: Output from reasoning_agent
        
    Returns:
        Dictionary with simplified summary and metrics
    """
    summary = reasoning_result.get('summary', '')
    
    if not summary:
        return {
            "summary": "",
            "readability_improved": False,
            "avg_word_length": 0,
            "avg_sentence_length": 0,
            "simplifications_made": 0,
            "confidence": 0.0
        }
    
    # Calculate original metrics
    original_metrics = calculate_readability(summary)
    
    # Step 1: Replace complex words
    simplified, word_changes = simplify_vocabulary(summary)
    
    # Step 2: Break long sentences
    simplified, sentence_changes = shorten_sentences(simplified)
    
    # Step 3: Remove redundancy
    simplified, redundancy_changes = remove_redundancy(simplified)
    
    # Step 4: Clean up
    simplified = clean_text(simplified)
    
    # Calculate new metrics
    new_metrics = calculate_readability(simplified)
    
    # Check if readability improved
    readability_improved = (
        new_metrics['avg_word_length'] < original_metrics['avg_word_length'] or
        new_metrics['avg_sentence_length'] < original_metrics['avg_sentence_length']
    )
    
    total_changes = word_changes + sentence_changes + redundancy_changes
    confidence = calculate_confidence(readability_improved, total_changes, len(summary))
    
    return {
        "summary": simplified,
        "readability_improved": readability_improved,
        "avg_word_length": round(new_metrics['avg_word_length'], 2),
        "avg_sentence_length": round(new_metrics['avg_sentence_length'], 1),
        "simplifications_made": total_changes,
        "flesch_score": new_metrics.get('flesch_score', 0),
        "confidence": round(confidence, 3)
    }


def simplify_vocabulary(text: str) -> Tuple[str, int]:
    """
    Replace complex words with simpler alternatives.
    
    Returns simplified text and count of changes made.
    """
    result = text
    changes = 0
    
    for complex_word, simple_word in SIMPLIFICATIONS.items():
        # Case-insensitive replacement that preserves original case
        pattern = re.compile(re.escape(complex_word), re.IGNORECASE)
        matches = pattern.findall(result)
        
        if matches:
            # Replace while trying to preserve case
            def replace_case(match):
                word = match.group(0)
                if word.isupper():
                    return simple_word.upper()
                elif word[0].isupper():
                    return simple_word.capitalize()
                return simple_word
            
            result = pattern.sub(replace_case, result)
            changes += len(matches)
    
    return result, changes


def shorten_sentences(text: str, max_words: int = 25) -> Tuple[str, int]:
    """
    Break long sentences into shorter ones.
    
    Returns modified text and count of sentences split.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    new_sentences = []
    changes = 0
    
    for sentence in sentences:
        words = sentence.split()
        
        if len(words) > max_words:
            # Try to find a good breaking point
            split_points = find_split_points(sentence)
            
            if split_points:
                # Split at the best point
                best_point = split_points[0]
                first_part = sentence[:best_point].strip()
                second_part = sentence[best_point:].strip()
                
                # Clean up the split
                first_part = first_part.rstrip(',;')
                if first_part and not first_part.endswith(('.', '!', '?')):
                    first_part += '.'
                
                # Capitalize second part
                if second_part:
                    # Remove leading conjunctions
                    second_part = re.sub(r'^(and|but|or|so|yet)\s+', '', second_part, flags=re.IGNORECASE)
                    second_part = second_part[0].upper() + second_part[1:] if second_part else ''
                
                new_sentences.append(first_part)
                if second_part:
                    new_sentences.append(second_part)
                changes += 1
            else:
                new_sentences.append(sentence)
        else:
            new_sentences.append(sentence)
    
    return ' '.join(new_sentences), changes


def find_split_points(sentence: str) -> List[int]:
    """
    Find good points to split a long sentence.
    
    Looks for conjunctions, semicolons, and natural breaks.
    """
    split_markers = [
        ('; ', 0),           # Semicolons are great split points
        (', and ', 1),       # Comma + conjunction
        (', but ', 1),
        (', or ', 1),
        (', which ', 2),     # Relative clauses
        (', that ', 2),
        (' because ', 3),    # Causal
        (' while ', 3),
        (' although ', 3),
    ]
    
    points = []
    for marker, priority in split_markers:
        idx = sentence.lower().find(marker)
        if idx > 10:  # Ensure first part isn't too short
            points.append((idx + len(marker) - 1, priority))
    
    # Sort by position, preferring earlier splits
    points.sort(key=lambda x: (x[1], x[0]))
    
    return [p[0] for p in points]


def remove_redundancy(text: str) -> Tuple[str, int]:
    """
    Remove redundant phrases and words.
    
    Returns cleaned text and count of removals.
    """
    redundant_phrases = [
        (r'\bin order to\b', 'to'),
        (r'\bdue to the fact that\b', 'because'),
        (r'\bat this point in time\b', 'now'),
        (r'\bin the event that\b', 'if'),
        (r'\bfor the purpose of\b', 'for'),
        (r'\bwith regard to\b', 'about'),
        (r'\bin spite of the fact that\b', 'although'),
        (r'\bas a matter of fact\b', ''),
        (r'\bit is important to note that\b', ''),
        (r'\bit should be noted that\b', ''),
        (r'\bbasically\b', ''),
        (r'\bactually\b', ''),
        (r'\bgenerally speaking\b', ''),
        (r'\bfor all intents and purposes\b', ''),
    ]
    
    result = text
    changes = 0
    
    for pattern, replacement in redundant_phrases:
        matches = re.findall(pattern, result, re.IGNORECASE)
        if matches:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            changes += len(matches)
    
    return result, changes


def clean_text(text: str) -> str:
    """
    Clean up text after simplifications.
    """
    # Remove double spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Fix punctuation spacing
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    
    # Remove empty sentences
    text = re.sub(r'\.\s*\.', '.', text)
    
    # Ensure proper capitalization after periods
    text = re.sub(r'([.!?])\s+([a-z])', lambda m: m.group(1) + ' ' + m.group(2).upper(), text)
    
    return text.strip()


def calculate_readability(text: str) -> Dict[str, float]:
    """
    Calculate readability metrics.
    
    Includes average word length, sentence length, and Flesch score.
    """
    if not text:
        return {
            'avg_word_length': 0,
            'avg_sentence_length': 0,
            'flesch_score': 0
        }
    
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    
    word_count = len(words)
    sentence_count = len(sentences) or 1
    
    # Average word length
    total_chars = sum(len(word.strip('.,!?;:')) for word in words)
    avg_word_length = total_chars / word_count if word_count else 0
    
    # Average sentence length
    avg_sentence_length = word_count / sentence_count
    
    # Simplified Flesch Reading Ease (approximation)
    # Higher score = easier to read
    syllable_count = estimate_syllables(text)
    avg_syllables = syllable_count / word_count if word_count else 0
    
    flesch = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)
    flesch = max(0, min(100, flesch))  # Clamp to 0-100
    
    return {
        'avg_word_length': avg_word_length,
        'avg_sentence_length': avg_sentence_length,
        'flesch_score': round(flesch, 1)
    }


def estimate_syllables(text: str) -> int:
    """
    Estimate syllable count in text.
    
    Uses a simple vowel-counting heuristic.
    """
    text = text.lower()
    words = re.findall(r'[a-z]+', text)
    
    total = 0
    for word in words:
        # Count vowel groups
        syllables = len(re.findall(r'[aeiouy]+', word))
        
        # Adjust for silent e
        if word.endswith('e') and syllables > 1:
            syllables -= 1
        
        # Minimum 1 syllable per word
        total += max(syllables, 1)
    
    return total


def calculate_confidence(improved: bool, changes: int, text_length: int) -> float:
    """
    Calculate confidence in simplification.
    """
    base = 0.6 if improved else 0.4
    change_bonus = min(changes * 0.05, 0.3)
    length_factor = min(text_length / 500, 1.0) * 0.1
    
    return min(base + change_bonus + length_factor, 1.0)

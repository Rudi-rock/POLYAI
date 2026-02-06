"""
PolyAI Verification Agent

Purpose: Check claims against source text to reduce hallucinations.
This is the "Lawyer" agent that validates the summary against the original.

Strategy:
1. Extract claims from the summary
2. Verify each claim exists in the source
3. Flag any claims not supported by original text
4. Calculate coverage and accuracy metrics
"""

from typing import Dict, Any, List, Set
import re


def run(processed_input: Dict[str, Any],
        encoding: Dict[str, Any],
        reasoning_result: Dict[str, Any],
        **kwargs) -> Dict[str, Any]:
    """
    Run the Verification Agent.
    
    Args:
        processed_input: Output from input_processor
        encoding: Output from shared_encoder
        reasoning_result: Output from reasoning_agent
        
    Returns:
        Dictionary with verification results
    """
    original_text = processed_input.get('normalized', '')
    summary = reasoning_result.get('summary', '')
    
    if not original_text or not summary:
        return {
            "verified": False,
            "coverage": 0,
            "accuracy": 0,
            "issues": ["Empty input or summary"],
            "confidence": 0.0
        }
    
    # Step 1: Extract significant claims/terms from summary
    summary_terms = extract_significant_terms(summary)
    
    # Step 2: Verify terms against original
    verification = verify_terms(summary_terms, original_text)
    
    # Step 3: Check sentence-level claims
    sentence_verification = verify_sentences(summary, original_text)
    
    # Step 4: Calculate metrics
    coverage = verification['matched'] / max(verification['total'], 1)
    accuracy = sentence_verification['verified_count'] / max(sentence_verification['total_count'], 1)
    
    # Step 5: Identify issues
    issues = []
    if verification['unmatched']:
        issues.append(f"Unverified terms: {', '.join(verification['unmatched'][:3])}")
    if accuracy < 0.7:
        issues.append("Some claims may not be directly from source")
    
    # Overall verification
    verified = coverage >= 0.7 and accuracy >= 0.6
    confidence = (coverage + accuracy) / 2
    
    return {
        "verified": verified,
        "coverage": round(coverage * 100),
        "accuracy": round(accuracy * 100),
        "issues": issues,
        "matched_terms": verification['matched'],
        "unmatched_terms": verification['unmatched'],
        "confidence": round(confidence, 3)
    }


def extract_significant_terms(text: str, min_length: int = 4) -> List[str]:
    """
    Extract significant terms from text.
    
    Filters out common words and short terms.
    """
    # Common words to exclude
    stop_words = {
        'the', 'and', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
        'might', 'must', 'can', 'this', 'that', 'these', 'those', 'with', 'from',
        'for', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'under', 'again', 'here', 'there', 'when', 'where', 'which',
        'while', 'about', 'against', 'each', 'other', 'such', 'more', 'some',
        'than', 'very', 'just', 'also', 'only', 'over', 'your', 'their', 'what'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter significant terms
    significant = [
        word for word in words
        if len(word) >= min_length and word not in stop_words
    ]
    
    # Remove duplicates while preserving order
    seen: Set[str] = set()
    unique = []
    for term in significant:
        if term not in seen:
            seen.add(term)
            unique.append(term)
    
    return unique


def verify_terms(terms: List[str], original: str) -> Dict[str, Any]:
    """
    Verify terms exist in original text.
    
    Returns counts of matched and unmatched terms.
    """
    original_lower = original.lower()
    matched = []
    unmatched = []
    
    for term in terms:
        if term in original_lower:
            matched.append(term)
        else:
            unmatched.append(term)
    
    return {
        "matched": len(matched),
        "unmatched": unmatched[:5],  # Limit for readability
        "total": len(terms)
    }


def verify_sentences(summary: str, original: str) -> Dict[str, Any]:
    """
    Verify sentences in summary against original text.
    
    Checks if key phrases from summary sentences appear in original.
    """
    # Split summary into sentences
    summary_sentences = re.split(r'(?<=[.!?])\s+', summary)
    original_lower = original.lower()
    
    verified_count = 0
    total_count = len(summary_sentences)
    
    for sentence in summary_sentences:
        if not sentence.strip():
            total_count -= 1
            continue
            
        # Extract key phrases (3+ word sequences)
        words = sentence.lower().split()
        if len(words) < 3:
            # Very short sentence - check whole thing
            if sentence.lower().strip('.,!?') in original_lower:
                verified_count += 1
            continue
        
        # Check for phrase matches
        verified = False
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            if phrase in original_lower:
                verified = True
                break
        
        if verified:
            verified_count += 1
    
    return {
        "verified_count": verified_count,
        "total_count": max(total_count, 1)
    }


def check_contradiction(summary: str, original: str) -> List[str]:
    """
    Check for potential contradictions.
    
    Looks for negation patterns that might indicate misrepresentation.
    (Simplified heuristic approach)
    """
    contradictions = []
    
    # Check for negation inversions
    negative_patterns = [
        (r'\bnot\s+(\w+)', r'\b\1\b'),  # "not X" vs "X"
        (r'\bno\s+(\w+)', r'\b\1\b'),   # "no X" vs "X"
        (r'\bnever\s+(\w+)', r'\b\1\b'), # "never X" vs "X"
    ]
    
    summary_lower = summary.lower()
    original_lower = original.lower()
    
    for neg_pattern, pos_pattern in negative_patterns:
        neg_matches = re.findall(neg_pattern, summary_lower)
        for match in neg_matches:
            # Check if original has positive version
            if re.search(r'\b' + match + r'\b', original_lower):
                if not re.search(neg_pattern.replace(r'(\w+)', match), original_lower):
                    contradictions.append(f"Potential negation issue with '{match}'")
    
    return contradictions[:3]  # Limit results

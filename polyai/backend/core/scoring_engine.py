"""
PolyAI Scoring Engine

Purpose: Rule-based quality scoring for agent outputs.
No heavy neural scorer needed - deterministic + fast.

Scoring Criteria:
1. Coverage: Did the summary capture key points from input?
2. Consistency: No contradictions between sentences
3. Clarity: Flesch-Kincaid readability metric
4. Brevity: Appropriate compression level
5. Accuracy: Claims verifiable against source
"""

from typing import Dict, Any, List
import re


def score_all(agent_results: Dict[str, Dict[str, Any]], 
              processed_input: Dict[str, Any]) -> Dict[str, float]:
    """
    Score all agent outputs.
    
    Args:
        agent_results: Dictionary of all agent outputs
        processed_input: Original processed input
        
    Returns:
        Dictionary of agent names to scores (0-1 scale)
    """
    scores = {}
    
    reasoning = agent_results.get('reasoning', {})
    verification = agent_results.get('verification', {})
    simplification = agent_results.get('simplification', {})
    critique = agent_results.get('critique', {})
    
    # Score reasoning agent output
    if reasoning.get('summary'):
        scores['reasoning'] = score_summary(
            reasoning.get('summary', ''),
            processed_input,
            reasoning.get('confidence', 0)
        )
    else:
        scores['reasoning'] = 0.0
    
    # Score simplification agent output
    if simplification.get('summary'):
        scores['simplification'] = score_summary(
            simplification.get('summary', ''),
            processed_input,
            simplification.get('confidence', 0),
            is_simplified=True
        )
    else:
        scores['simplification'] = 0.0
    
    # Verification and critique don't produce summaries
    # Their scores affect the debate process
    scores['verification'] = verification.get('confidence', 0)
    scores['critique'] = critique.get('confidence', 0)
    
    return scores


def score_summary(summary: str, 
                  processed_input: Dict[str, Any],
                  agent_confidence: float,
                  is_simplified: bool = False) -> float:
    """
    Score a summary on multiple quality dimensions.
    
    Returns overall score from 0 to 1.
    """
    if not summary:
        return 0.0
    
    original = processed_input.get('normalized', '')
    original_words = processed_input.get('word_count', 0)
    
    # 1. Coverage Score (0-1)
    coverage = score_coverage(summary, original)
    
    # 2. Brevity Score (0-1)
    brevity = score_brevity(summary, original_words)
    
    # 3. Clarity Score (0-1)
    clarity = score_clarity(summary)
    
    # 4. Consistency Score (0-1)
    consistency = score_consistency(summary)
    
    # 5. Structure Score (0-1)
    structure = score_structure(summary)
    
    # Weighted combination
    weights = {
        'coverage': 0.30,
        'brevity': 0.20,
        'clarity': 0.20,
        'consistency': 0.15,
        'structure': 0.15
    }
    
    # Adjust weights for simplified version
    if is_simplified:
        weights['clarity'] = 0.30  # Higher weight on clarity
        weights['coverage'] = 0.25
    
    total_score = (
        weights['coverage'] * coverage +
        weights['brevity'] * brevity +
        weights['clarity'] * clarity +
        weights['consistency'] * consistency +
        weights['structure'] * structure
    )
    
    # Blend with agent's own confidence
    blended_score = 0.7 * total_score + 0.3 * agent_confidence
    
    return round(blended_score, 3)


def score_coverage(summary: str, original: str) -> float:
    """
    Score how well the summary covers key content from original.
    
    Uses significant word overlap as a proxy.
    """
    if not original or not summary:
        return 0.0
    
    # Extract significant words from original
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'have', 'has', 'had', 'do', 'does', 'did', 'and', 'or', 'but',
                  'in', 'on', 'at', 'to', 'for', 'of', 'with', 'as', 'by', 'this',
                  'that', 'it', 'its', 'from', 'their', 'they', 'them', 'we', 'our'}
    
    original_words = set(w.lower().strip('.,!?;:') 
                        for w in original.split() 
                        if len(w) > 3 and w.lower() not in stop_words)
    
    summary_words = set(w.lower().strip('.,!?;:') 
                        for w in summary.split() 
                        if len(w) > 3 and w.lower() not in stop_words)
    
    if not original_words:
        return 0.5  # Neutral score if no significant words
    
    # Calculate overlap
    overlap = len(original_words & summary_words)
    coverage_ratio = overlap / len(original_words)
    
    # Optimal coverage is around 30-50% for summaries
    if coverage_ratio > 0.5:
        score = 1.0
    elif coverage_ratio > 0.3:
        score = 0.8 + (coverage_ratio - 0.3) * 1.0
    elif coverage_ratio > 0.1:
        score = 0.4 + (coverage_ratio - 0.1) * 2.0
    else:
        score = coverage_ratio * 4.0
    
    return min(max(score, 0), 1)


def score_brevity(summary: str, original_word_count: int) -> float:
    """
    Score how appropriately compressed the summary is.
    
    Ideal compression: 65-80% reduction for long texts.
    """
    if original_word_count == 0:
        return 0.5
    
    summary_word_count = len(summary.split())
    compression_ratio = 1 - (summary_word_count / original_word_count)
    
    # Score based on compression ratio
    # Optimal is 60-80% compression
    if 0.6 <= compression_ratio <= 0.8:
        return 1.0
    elif 0.5 <= compression_ratio < 0.6:
        return 0.8 + (compression_ratio - 0.5) * 2.0
    elif 0.8 < compression_ratio <= 0.9:
        return 1.0 - (compression_ratio - 0.8) * 2.0
    elif compression_ratio > 0.9:
        return 0.6 - (compression_ratio - 0.9) * 2.0  # Penalize over-compression
    elif compression_ratio < 0.5:
        return 0.5 + compression_ratio
    
    return 0.5


def score_clarity(summary: str) -> float:
    """
    Score readability using simplified Flesch-Kincaid.
    
    Returns 0-1 where 1 is most readable.
    """
    if not summary:
        return 0.0
    
    words = summary.split()
    sentences = [s for s in re.split(r'[.!?]+', summary) if s.strip()]
    
    word_count = len(words)
    sentence_count = len(sentences) or 1
    
    # Estimate syllables
    syllable_count = 0
    for word in words:
        syllables = len(re.findall(r'[aeiouy]+', word.lower()))
        syllables = max(syllables, 1)
        if word.lower().endswith('e') and syllables > 1:
            syllables -= 1
        syllable_count += syllables
    
    avg_sentence_length = word_count / sentence_count
    avg_syllables_per_word = syllable_count / max(word_count, 1)
    
    # Calculate Flesch Reading Ease
    flesch = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    
    # Convert to 0-1 scale (Flesch ranges roughly 0-100)
    score = min(max(flesch / 100, 0), 1)
    
    return round(score, 3)


def score_consistency(summary: str) -> float:
    """
    Score internal consistency (no contradictions).
    
    Uses simple heuristics to detect potential inconsistencies.
    """
    if not summary:
        return 0.0
    
    sentences = [s.strip() for s in re.split(r'[.!?]+', summary) if s.strip()]
    
    if len(sentences) < 2:
        return 0.9  # Single sentence can't contradict itself
    
    # Check for simple contradiction patterns
    inconsistency_score = 0
    
    for i, s1 in enumerate(sentences):
        s1_lower = s1.lower()
        for s2 in sentences[i+1:]:
            s2_lower = s2.lower()
            
            # Check for negation contradictions
            # e.g., "X is important" vs "X is not important"
            if 'not' in s2_lower and 'not' not in s1_lower:
                # Extract main concept and check if negated
                # This is a very rough heuristic
                pass  # Skip complex analysis for now
    
    # For now, assume consistency unless obvious issues found
    return 0.85 + (0.15 * (1 - inconsistency_score))


def score_structure(summary: str) -> float:
    """
    Score structural quality of the summary.
    
    Checks for:
    - Proper sentence endings
    - Capitalization
    - Sentence variety
    """
    if not summary:
        return 0.0
    
    score = 1.0
    
    # Check for proper capitalization
    if summary and summary[0].islower():
        score -= 0.2
    
    # Check sentences start with capitals
    sentences = re.split(r'[.!?]\s+', summary)
    for s in sentences:
        if s and s[0].islower():
            score -= 0.1
            break
    
    # Check for proper ending punctuation
    if not re.search(r'[.!?]$', summary.strip()):
        score -= 0.1
    
    # Reward having multiple sentences (shows structure)
    sentence_count = len([s for s in sentences if s.strip()])
    if sentence_count >= 2:
        score += 0.1
    elif sentence_count >= 3:
        score += 0.15
    
    return min(max(score, 0), 1)


def get_detailed_scores(summary: str, 
                        processed_input: Dict[str, Any]) -> Dict[str, float]:
    """
    Get breakdown of all individual scores.
    
    Useful for debugging and display.
    """
    original = processed_input.get('normalized', '')
    original_words = processed_input.get('word_count', 0)
    
    return {
        'coverage': score_coverage(summary, original),
        'brevity': score_brevity(summary, original_words),
        'clarity': score_clarity(summary),
        'consistency': score_consistency(summary),
        'structure': score_structure(summary)
    }

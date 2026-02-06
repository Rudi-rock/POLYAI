"""
PolyAI Reasoning Agent

Purpose: Extract key ideas and build logical flow from the input text.
This is the "Architect" agent that creates the initial draft summary.

Strategy:
1. Identify key sentences using the shared encoder scores
2. Extract main points from high-scoring sentences
3. Build a logical flow from introduction to conclusion
4. Preserve essential facts and claims
"""

from typing import Dict, Any, List


def run(processed_input: Dict[str, Any], 
        encoding: Dict[str, Any],
        **kwargs) -> Dict[str, Any]:
    """
    Run the Reasoning Agent.
    
    Args:
        processed_input: Output from input_processor
        encoding: Output from shared_encoder
        
    Returns:
        Dictionary with summary and reasoning details
    """
    sentences = processed_input.get('sentences', [])
    sentence_scores = encoding.get('sentence_scores', [])
    key_sentence_indices = encoding.get('key_sentences', [])
    keywords = encoding.get('keywords', [])
    
    if not sentences:
        return {
            "summary": "",
            "confidence": 0.0,
            "key_points": [],
            "sentence_count": 0
        }
    
    # Step 1: Select key sentences based on scores and position
    selected_sentences = select_key_sentences(sentences, sentence_scores)
    
    # Step 2: Extract key points
    key_points = extract_key_points(selected_sentences, keywords)
    
    # Step 3: Build logical flow
    summary = build_summary(selected_sentences)
    
    # Step 4: Calculate confidence
    confidence = calculate_confidence(sentences, selected_sentences, key_points)
    
    return {
        "summary": summary,
        "confidence": confidence,
        "key_points": key_points,
        "sentence_count": len(selected_sentences)
    }


def select_key_sentences(sentences: List[str], 
                         scores: List[float],
                         max_sentences: int = 5) -> List[str]:
    """
    Select the most important sentences.
    
    Strategy:
    - Always include first sentence (often thesis/introduction)
    - Include highest scoring sentences
    - Include last sentence if it's a conclusion
    - Maintain original order
    """
    if not sentences:
        return []
    
    n = len(sentences)
    
    # Calculate how many sentences to include
    target_count = min(max_sentences, max(2, n // 3))
    
    # Create list of (index, score) tuples
    scored_indices = list(enumerate(scores)) if scores else [(i, 0) for i in range(n)]
    
    # Always include first sentence
    selected_indices = {0}
    
    # Add highest scoring sentences
    sorted_by_score = sorted(scored_indices, key=lambda x: x[1], reverse=True)
    for idx, score in sorted_by_score:
        if len(selected_indices) >= target_count:
            break
        selected_indices.add(idx)
    
    # Consider including last sentence
    if n > 3 and n - 1 not in selected_indices:
        # Check if last sentence seems like a conclusion
        last_sent_lower = sentences[-1].lower()
        conclusion_markers = ['therefore', 'thus', 'in conclusion', 'finally', 
                            'overall', 'to summarize', 'in summary']
        if any(marker in last_sent_lower for marker in conclusion_markers):
            selected_indices.add(n - 1)
    
    # Return sentences in original order
    ordered_indices = sorted(selected_indices)
    return [sentences[i] for i in ordered_indices]


def extract_key_points(sentences: List[str], 
                       keywords: List[Dict[str, Any]]) -> List[str]:
    """
    Extract key points from selected sentences.
    
    Each key point is a concise representation of a main idea.
    """
    key_points = []
    keyword_set = {kw['term'].lower() for kw in keywords[:10]}
    
    for sentence in sentences:
        # Find which keywords this sentence addresses
        words = sentence.lower().split()
        matching_keywords = [w for w in words if w in keyword_set]
        
        if matching_keywords:
            # Truncate long sentences for key points
            if len(sentence) > 100:
                # Keep first part
                point = sentence[:97] + "..."
            else:
                point = sentence
            key_points.append(point.strip())
    
    return key_points[:5]  # Max 5 key points


def build_summary(sentences: List[str]) -> str:
    """
    Build a coherent summary from selected sentences.
    
    Ensures proper formatting and flow.
    """
    if not sentences:
        return ""
    
    # Join sentences with proper spacing
    summary = ' '.join(s.strip() for s in sentences)
    
    # Clean up any double spaces
    summary = ' '.join(summary.split())
    
    # Ensure proper ending punctuation
    if summary and not summary.endswith(('.', '!', '?')):
        summary += '.'
    
    return summary


def calculate_confidence(original_sentences: List[str],
                         selected_sentences: List[str],
                         key_points: List[str]) -> float:
    """
    Calculate confidence score for the summary.
    
    Based on:
    - Coverage ratio
    - Key points extracted
    - Selection quality
    """
    if not original_sentences:
        return 0.0
    
    # Coverage score
    coverage = len(selected_sentences) / len(original_sentences)
    coverage_score = min(coverage * 2, 1.0)  # Optimal is ~50% coverage
    
    # Key points score
    key_points_score = min(len(key_points) / 3, 1.0)  # 3+ key points is good
    
    # Balance score (not too short, not too long)
    ratio = len(selected_sentences) / max(len(original_sentences), 1)
    balance_score = 1.0 - abs(ratio - 0.3) * 2  # Optimal is ~30%
    balance_score = max(0, min(balance_score, 1.0))
    
    # Weighted average
    confidence = (
        0.4 * coverage_score +
        0.3 * key_points_score +
        0.3 * balance_score
    )
    
    return round(confidence, 3)

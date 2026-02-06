"""
PolyAI Critique Agent

Purpose: Find gaps and attack weak summaries to improve quality.
This is the "Reviewer" agent that stress-tests other agents' work.

Strategy:
1. Check for over-compression (too much information lost)
2. Check for under-compression (summary too long)
3. Identify potentially missing key information
4. Look for logical gaps or weak arguments
5. Score overall quality
"""

from typing import Dict, Any, List, Set
import re


def run(processed_input: Dict[str, Any],
        encoding: Dict[str, Any],
        reasoning_result: Dict[str, Any],
        **kwargs) -> Dict[str, Any]:
    """
    Run the Critique Agent.
    
    Args:
        processed_input: Output from input_processor
        encoding: Output from shared_encoder
        reasoning_result: Output from reasoning_agent
        
    Returns:
        Dictionary with critique results and suggestions
    """
    original_text = processed_input.get('normalized', '')
    original_word_count = processed_input.get('word_count', 0)
    sentences = processed_input.get('sentences', [])
    keywords = encoding.get('keywords', [])
    summary = reasoning_result.get('summary', '')
    
    if not original_text or not summary:
        return {
            "quality": "Unknown",
            "compression_ratio": 0,
            "issues": ["Empty input or summary"],
            "suggestions": [],
            "confidence": 0.0
        }
    
    issues = []
    suggestions = []
    
    # Step 1: Check compression ratio
    summary_word_count = len(summary.split())
    compression_ratio = 1 - (summary_word_count / max(original_word_count, 1))
    compression_issues = check_compression(compression_ratio, original_word_count)
    issues.extend(compression_issues)
    
    # Step 2: Check keyword coverage
    keyword_issues = check_keyword_coverage(summary, keywords)
    issues.extend(keyword_issues['issues'])
    suggestions.extend(keyword_issues['suggestions'])
    
    # Step 3: Check for logical completeness
    logic_issues = check_logic(summary, sentences)
    issues.extend(logic_issues)
    
    # Step 4: Check sentence quality
    sentence_issues = check_sentence_quality(summary)
    issues.extend(sentence_issues)
    
    # Step 5: Determine overall quality
    quality = assess_quality(issues, compression_ratio)
    
    # Calculate confidence
    confidence = calculate_confidence(issues, compression_ratio)
    
    return {
        "quality": quality,
        "compression_ratio": round(compression_ratio * 100),
        "issues": issues[:5],  # Limit to top 5 issues
        "suggestions": suggestions[:3],  # Limit suggestions
        "missing_keywords": keyword_issues.get('missing', [])[:3],
        "confidence": round(confidence, 3)
    }


def check_compression(ratio: float, original_words: int) -> List[str]:
    """
    Check if compression ratio is appropriate.
    
    Ideal compression: 60-80% for most texts
    """
    issues = []
    
    if ratio > 0.9:
        issues.append("Summary may be over-compressed (>90% reduction)")
    elif ratio > 0.85 and original_words > 200:
        issues.append("Summary is very brief; may miss key details")
    
    if ratio < 0.3:
        issues.append("Summary could be more concise (<30% compression)")
    elif ratio < 0.5 and original_words > 300:
        issues.append("Consider further condensing the summary")
    
    return issues


def check_keyword_coverage(summary: str, 
                          keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check if important keywords are covered in summary.
    """
    summary_lower = summary.lower()
    top_keywords = [kw['term'] for kw in keywords[:10]]
    
    covered = []
    missing = []
    
    for keyword in top_keywords:
        if keyword in summary_lower:
            covered.append(keyword)
        else:
            missing.append(keyword)
    
    coverage_ratio = len(covered) / max(len(top_keywords), 1)
    
    issues = []
    suggestions = []
    
    if coverage_ratio < 0.5:
        issues.append(f"Low keyword coverage ({len(covered)}/{len(top_keywords)} key terms)")
    
    if missing and len(missing) <= 3:
        suggestions.append(f"Consider including: {', '.join(missing[:3])}")
    
    return {
        "issues": issues,
        "suggestions": suggestions,
        "missing": missing,
        "coverage_ratio": coverage_ratio
    }


def check_logic(summary: str, original_sentences: List[str]) -> List[str]:
    """
    Check for logical completeness and coherence.
    """
    issues = []
    
    # Check if summary has introduction-style content
    summary_lower = summary.lower()
    
    # Check for dangling references
    dangling_refs = [
        r'\bthis\b(?!\s+\w)',  # "this" without noun
        r'\bthese\b(?!\s+\w)',
        r'\bthat\b(?!\s+\w)',
        r'\bsuch\b(?!\s+\w)',
    ]
    
    for pattern in dangling_refs:
        if re.search(pattern, summary_lower):
            # This is a very rough heuristic
            pass  # Don't flag too aggressively
    
    # Check if summary starts abruptly
    first_words = summary_lower.split()[:3] if summary else []
    abrupt_starters = ['however', 'therefore', 'thus', 'hence', 'so', 'but', 'and']
    
    if first_words and first_words[0].strip('.,') in abrupt_starters:
        issues.append("Summary may start abruptly with a conjunction")
    
    # Check sentence count
    summary_sentences = [s for s in re.split(r'[.!?]+', summary) if s.strip()]
    if len(summary_sentences) == 1 and len(summary.split()) > 30:
        issues.append("Consider breaking into multiple sentences for clarity")
    
    return issues


def check_sentence_quality(summary: str) -> List[str]:
    """
    Check individual sentence quality.
    """
    issues = []
    sentences = [s for s in re.split(r'[.!?]+', summary) if s.strip()]
    
    for sentence in sentences:
        words = sentence.split()
        
        # Very long sentence
        if len(words) > 40:
            issues.append("Contains overly long sentence (40+ words)")
            break  # Only report once
        
        # Very short sentence (might be incomplete)
        if len(words) < 4 and len(sentences) > 1:
            issues.append("Contains very short sentence; may be incomplete")
            break
    
    # Check for repetition
    words = summary.lower().split()
    word_counts: Dict[str, int] = {}
    for word in words:
        word = word.strip('.,!?;:')
        if len(word) > 5:  # Only check substantial words
            word_counts[word] = word_counts.get(word, 0) + 1
    
    repeated = [w for w, c in word_counts.items() if c > 3]
    if repeated:
        issues.append(f"Word repetition detected: '{repeated[0]}'")
    
    return issues


def assess_quality(issues: List[str], compression_ratio: float) -> str:
    """
    Determine overall quality rating.
    """
    issue_count = len(issues)
    
    # Good compression range
    good_compression = 0.5 <= compression_ratio <= 0.85
    
    if issue_count == 0 and good_compression:
        return "Excellent"
    elif issue_count <= 1 and good_compression:
        return "Good"
    elif issue_count <= 2:
        return "Fair"
    elif issue_count <= 4:
        return "Needs improvement"
    else:
        return "Poor"


def calculate_confidence(issues: List[str], compression_ratio: float) -> float:
    """
    Calculate confidence score for critique.
    """
    base = 0.7
    
    # More issues = higher confidence in critique accuracy
    issue_bonus = min(len(issues) * 0.05, 0.2)
    
    # Good compression range = higher confidence
    if 0.5 <= compression_ratio <= 0.85:
        compression_bonus = 0.1
    else:
        compression_bonus = 0
    
    return min(base + issue_bonus + compression_bonus, 1.0)


def get_improvement_suggestions(issues: List[str], 
                                missing_keywords: List[str]) -> List[str]:
    """
    Generate actionable improvement suggestions.
    """
    suggestions = []
    
    for issue in issues:
        if 'over-compressed' in issue.lower():
            suggestions.append("Add more detail from key sections")
        elif 'concise' in issue.lower():
            suggestions.append("Remove redundant phrases and compress further")
        elif 'keyword' in issue.lower() and missing_keywords:
            suggestions.append(f"Include key terms: {', '.join(missing_keywords[:2])}")
        elif 'long sentence' in issue.lower():
            suggestions.append("Split long sentences for better readability")
    
    return suggestions[:3]

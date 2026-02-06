"""
PolyAI Debate Engine

Purpose: Orchestrate multi-agent debate to produce better outputs.
This is the "secret sauce" that makes collective reasoning > model size.

Debate Flow:
1. Round 1: All agents produce initial outputs
2. Round 2: Critique agent attacks each output
3. Round 3: Select best parts from all outputs
4. Final: Combine winning elements

The key insight: Instead of "first output wins", each agent
submits its version and outputs are scored locally.
"""

from typing import Dict, Any, List


def debate(agent_results: Dict[str, Dict[str, Any]], 
           scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Orchestrate debate between agents and determine winning output.
    
    Args:
        agent_results: Results from all four agents
        scores: Quality scores for each agent's output
        
    Returns:
        Dictionary with debate results and winning elements
    """
    reasoning = agent_results.get('reasoning', {})
    verification = agent_results.get('verification', {})
    simplification = agent_results.get('simplification', {})
    critique = agent_results.get('critique', {})
    
    # Round 1: Collect all candidate summaries
    candidates = {
        'reasoning': {
            'summary': reasoning.get('summary', ''),
            'score': scores.get('reasoning', 0),
            'confidence': reasoning.get('confidence', 0)
        },
        'simplification': {
            'summary': simplification.get('summary', ''),
            'score': scores.get('simplification', 0),
            'confidence': simplification.get('confidence', 0)
        }
    }
    
    # Round 2: Apply critique feedback
    critique_issues = critique.get('issues', [])
    critique_quality = critique.get('quality', 'Unknown')
    
    # Adjust scores based on critique
    adjusted_candidates = apply_critique_adjustments(
        candidates, 
        critique_issues,
        verification.get('verified', False),
        verification.get('coverage', 0)
    )
    
    # Round 3: Determine winner
    winner = select_winner(adjusted_candidates)
    
    # Collect all insights for refinement
    debate_result = {
        'winner': winner,
        'winning_summary': adjusted_candidates[winner]['summary'],
        'final_score': adjusted_candidates[winner]['score'],
        'candidates': adjusted_candidates,
        'critique_feedback': {
            'quality': critique_quality,
            'issues': critique_issues,
            'suggestions': critique.get('suggestions', [])
        },
        'verification_status': {
            'verified': verification.get('verified', False),
            'coverage': verification.get('coverage', 0),
            'issues': verification.get('issues', [])
        }
    }
    
    return debate_result


def apply_critique_adjustments(candidates: Dict[str, Dict[str, Any]],
                               critique_issues: List[str],
                               verified: bool,
                               coverage: int) -> Dict[str, Dict[str, Any]]:
    """
    Adjust candidate scores based on critique and verification feedback.
    
    Verification passing gives a bonus.
    Critique issues give penalties.
    """
    adjusted = {}
    
    for name, candidate in candidates.items():
        adjusted_score = candidate['score']
        
        # Verification bonus
        if verified:
            adjusted_score += 0.15
        elif coverage > 70:
            adjusted_score += 0.10
        
        # Critique penalty
        issue_penalty = min(len(critique_issues) * 0.05, 0.2)
        adjusted_score -= issue_penalty
        
        # Prefer simplified version if scores are close and verification passed
        if name == 'simplification' and verified:
            adjusted_score += 0.05  # Slight preference for readability
        
        adjusted[name] = {
            'summary': candidate['summary'],
            'score': round(max(0, min(1, adjusted_score)), 3),
            'confidence': candidate['confidence']
        }
    
    return adjusted


def select_winner(candidates: Dict[str, Dict[str, Any]]) -> str:
    """
    Select the winning candidate based on adjusted scores.
    
    In case of tie, prefer simplification for readability.
    """
    best_name = None
    best_score = -1
    
    for name, candidate in candidates.items():
        if candidate['score'] > best_score:
            best_score = candidate['score']
            best_name = name
        elif candidate['score'] == best_score and name == 'simplification':
            # Prefer simplification on tie
            best_name = name
    
    return best_name or 'reasoning'


def get_consensus_elements(agent_results: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Find elements that multiple agents agree on.
    
    These are high-confidence elements that should be preserved.
    """
    reasoning = agent_results.get('reasoning', {})
    simplification = agent_results.get('simplification', {})
    
    # Get key points from reasoning
    key_points = reasoning.get('key_points', [])
    
    # Find points also present in simplified version
    simplified_summary = simplification.get('summary', '').lower()
    
    consensus = []
    for point in key_points:
        # Check if key words from point appear in simplified
        words = [w for w in point.lower().split() if len(w) > 5]
        matches = sum(1 for w in words if w in simplified_summary)
        if matches >= len(words) * 0.5:  # At least 50% word match
            consensus.append(point)
    
    return consensus


def get_conflicting_elements(agent_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Identify elements where agents disagree.
    
    These need special handling in the output refiner.
    """
    verification = agent_results.get('verification', {})
    critique = agent_results.get('critique', {})
    
    conflicts = []
    
    # Check for unverified terms
    unverified = verification.get('unmatched_terms', [])
    if unverified:
        conflicts.append({
            'type': 'unverified_claim',
            'details': f"Terms not found in source: {', '.join(unverified[:3])}"
        })
    
    # Check for critique issues
    critique_issues = critique.get('issues', [])
    for issue in critique_issues[:2]:
        conflicts.append({
            'type': 'quality_issue',
            'details': issue
        })
    
    return conflicts


def calculate_debate_confidence(debate_result: Dict[str, Any]) -> float:
    """
    Calculate overall confidence in the debate outcome.
    
    Higher confidence when:
    - Winner has high score
    - Verification passed
    - Few critique issues
    """
    winner_score = debate_result.get('final_score', 0)
    verified = debate_result.get('verification_status', {}).get('verified', False)
    issues = debate_result.get('critique_feedback', {}).get('issues', [])
    
    confidence = winner_score * 0.5
    
    if verified:
        confidence += 0.3
    
    issue_penalty = min(len(issues) * 0.1, 0.2)
    confidence -= issue_penalty
    
    return round(max(0, min(1, confidence)), 3)

# PolyAI Backend - Python FastAPI Local Server
#
# This is the orchestrator layer that connects the frontend 
# to the PolyAI Core Engine for multi-agent summarization.
#
# Run with: uvicorn main:app --reload

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import time

# Import core engine components
from core import (
    input_processor,
    shared_encoder,
    debate_engine,
    scoring_engine,
    output_refiner
)
from core.agents import (
    reasoning_agent,
    verification_agent,
    simplification_agent,
    critique_agent
)

# ========================================
# FastAPI App Configuration
# ========================================
app = FastAPI(
    title="PolyAI",
    description="Offline Multi-Agent AI Summarization Engine",
    version="1.0.0"
)

# Enable CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# Request/Response Models
# ========================================
class SummarizeRequest(BaseModel):
    text: str
    debug: Optional[bool] = False
    max_length: Optional[int] = 500

class AgentResult(BaseModel):
    summary: Optional[str] = None
    confidence: float
    details: Dict[str, Any]

class SummarizeResponse(BaseModel):
    summary: str
    agents: Optional[Dict[str, AgentResult]] = None
    stats: Dict[str, Any]

# ========================================
# API Endpoints
# ========================================
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "PolyAI",
        "version": "1.0.0",
        "mode": "offline"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "input_processor": "ready",
            "shared_encoder": "ready",
            "agents": ["reasoning", "verification", "simplification", "critique"],
            "debate_engine": "ready",
            "output_refiner": "ready"
        }
    }

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """
    Main summarization endpoint.
    
    Orchestrates the multi-agent debate pipeline:
    1. Input Processing - Normalize and clean text
    2. Shared Encoding - Create text representation
    3. Agent Execution - Run all 4 agents
    4. Debate & Scoring - Evaluate agent outputs
    5. Output Refinement - Merge into final summary
    """
    start_time = time.time()
    
    # Validate input
    if not request.text or len(request.text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Text must be at least 50 characters long"
        )
    
    if len(request.text) > 50000:
        raise HTTPException(
            status_code=400,
            detail="Text exceeds maximum length of 50,000 characters"
        )
    
    try:
        # Step 1: Input Processing
        processed = input_processor.process(request.text)
        
        # Step 2: Shared Encoding
        encoding = shared_encoder.encode(processed)
        
        # Step 3: Run Agents
        reasoning_result = reasoning_agent.run(processed, encoding)
        verification_result = verification_agent.run(processed, encoding, reasoning_result)
        simplification_result = simplification_agent.run(processed, encoding, reasoning_result)
        critique_result = critique_agent.run(processed, encoding, reasoning_result)
        
        agent_results = {
            "reasoning": reasoning_result,
            "verification": verification_result,
            "simplification": simplification_result,
            "critique": critique_result
        }
        
        # Step 4: Debate & Scoring
        scores = scoring_engine.score_all(agent_results, processed)
        debate_result = debate_engine.debate(agent_results, scores)
        
        # Step 5: Output Refinement
        final_summary = output_refiner.refine(debate_result, agent_results)
        
        # Calculate stats
        end_time = time.time()
        latency_ms = round((end_time - start_time) * 1000)
        
        original_words = len(request.text.split())
        summary_words = len(final_summary.split())
        compression = round((1 - summary_words / original_words) * 100)
        
        # Build response
        response = SummarizeResponse(
            summary=final_summary,
            stats={
                "original_words": original_words,
                "summary_words": summary_words,
                "compression_percent": compression,
                "latency_ms": latency_ms
            }
        )
        
        # Include agent details if debug mode
        if request.debug:
            response.agents = {
                "reasoning": AgentResult(
                    summary=reasoning_result.get("summary"),
                    confidence=reasoning_result.get("confidence", 0),
                    details={
                        "key_points": reasoning_result.get("key_points", []),
                        "sentence_count": reasoning_result.get("sentence_count", 0)
                    }
                ),
                "verification": AgentResult(
                    confidence=verification_result.get("confidence", 0),
                    details={
                        "verified": verification_result.get("verified", False),
                        "coverage": verification_result.get("coverage", 0),
                        "issues": verification_result.get("issues", [])
                    }
                ),
                "simplification": AgentResult(
                    summary=simplification_result.get("summary"),
                    confidence=simplification_result.get("confidence", 0),
                    details={
                        "readability_improved": simplification_result.get("readability_improved", False),
                        "avg_word_length": simplification_result.get("avg_word_length", 0)
                    }
                ),
                "critique": AgentResult(
                    confidence=critique_result.get("confidence", 0),
                    details={
                        "quality": critique_result.get("quality", "Unknown"),
                        "compression_ratio": critique_result.get("compression_ratio", 0),
                        "issues": critique_result.get("issues", [])
                    }
                )
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(e)}"
        )


# ========================================
# Run Server
# ========================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

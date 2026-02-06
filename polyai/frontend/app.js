// ========================================
// PolyAI - Frontend Application Logic
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// ========================================
// State Management
// ========================================
const state = {
    isProcessing: false,
    debugMode: false,
    backendUrl: 'http://localhost:8000'
};

// ========================================
// Initialization
// ========================================
function initializeApp() {
    // Elements
    const inputText = document.getElementById('inputText');
    const summarizeBtn = document.getElementById('summarizeBtn');
    const clearBtn = document.getElementById('clearBtn');
    const pasteBtn = document.getElementById('pasteBtn');
    const copyBtn = document.getElementById('copyBtn');
    const debugToggle = document.getElementById('debugMode');
    
    // Event Listeners
    inputText.addEventListener('input', updateCharCount);
    summarizeBtn.addEventListener('click', handleSummarize);
    clearBtn.addEventListener('click', handleClear);
    pasteBtn.addEventListener('click', handlePaste);
    copyBtn.addEventListener('click', handleCopy);
    debugToggle.addEventListener('change', toggleDebugMode);
    
    // Initialize
    updateCharCount();
}

// ========================================
// Character & Word Count
// ========================================
function updateCharCount() {
    const inputText = document.getElementById('inputText');
    const charCount = document.getElementById('charCount');
    const wordCount = document.getElementById('wordCount');
    
    const text = inputText.value;
    charCount.textContent = text.length;
    wordCount.textContent = countWords(text);
}

function countWords(text) {
    if (!text.trim()) return 0;
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

// ========================================
// Button Handlers
// ========================================
function handleClear() {
    const inputText = document.getElementById('inputText');
    inputText.value = '';
    updateCharCount();
    inputText.focus();
}

async function handlePaste() {
    try {
        const text = await navigator.clipboard.readText();
        const inputText = document.getElementById('inputText');
        inputText.value = text;
        updateCharCount();
        showToast('Text pasted successfully');
    } catch (err) {
        showToast('Unable to paste from clipboard');
    }
}

async function handleCopy() {
    const outputContent = document.getElementById('outputContent');
    const text = outputContent.textContent;
    
    if (!text || text === '') {
        showToast('No summary to copy');
        return;
    }
    
    try {
        await navigator.clipboard.writeText(text);
        showToast('Summary copied to clipboard');
    } catch (err) {
        showToast('Failed to copy');
    }
}

function toggleDebugMode() {
    state.debugMode = document.getElementById('debugMode').checked;
    const debugPanel = document.getElementById('debugPanel');
    
    if (state.debugMode) {
        debugPanel.classList.add('visible');
    } else {
        debugPanel.classList.remove('visible');
    }
}

// ========================================
// Main Summarization Handler
// ========================================
async function handleSummarize() {
    const inputText = document.getElementById('inputText');
    const text = inputText.value.trim();
    
    if (!text) {
        showToast('Please enter some text to summarize');
        return;
    }
    
    if (text.length < 100) {
        showToast('Please enter at least 100 characters');
        return;
    }
    
    if (state.isProcessing) return;
    
    setProcessingState(true);
    const startTime = performance.now();
    
    try {
        // Try to call backend API
        const result = await callBackendAPI(text);
        const endTime = performance.now();
        
        displayResults(result, text, endTime - startTime);
    } catch (error) {
        console.warn('Backend unavailable, using local processing:', error.message);
        
        // Fallback to local processing
        const result = await processLocally(text);
        const endTime = performance.now();
        
        displayResults(result, text, endTime - startTime);
    }
    
    setProcessingState(false);
}

// ========================================
// Backend API Call
// ========================================
async function callBackendAPI(text) {
    const response = await fetch(`${state.backendUrl}/summarize`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            text: text,
            debug: state.debugMode
        })
    });
    
    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json();
}

// ========================================
// Local Processing (Fallback)
// ========================================
async function processLocally(text) {
    // Simulate processing delay
    await delay(500);
    
    // Input Processing
    const processed = processInput(text);
    
    // Run agents (simulated)
    const reasoningResult = runReasoningAgent(processed);
    await delay(200);
    
    const verificationResult = runVerificationAgent(processed, reasoningResult);
    await delay(150);
    
    const simplificationResult = runSimplificationAgent(processed, reasoningResult);
    await delay(150);
    
    const critiqueResult = runCritiqueAgent(processed, reasoningResult);
    await delay(100);
    
    // Debate and score
    const finalSummary = refineSummary(reasoningResult, verificationResult, simplificationResult, critiqueResult);
    
    return {
        summary: finalSummary,
        agents: {
            reasoning: reasoningResult,
            verification: verificationResult,
            simplification: simplificationResult,
            critique: critiqueResult
        }
    };
}

// ========================================
// Input Processor
// ========================================
function processInput(text) {
    // Normalize whitespace
    let processed = text.replace(/\s+/g, ' ').trim();
    
    // Remove URLs
    processed = processed.replace(/https?:\/\/[^\s]+/gi, '');
    
    // Remove email addresses
    processed = processed.replace(/[\w.-]+@[\w.-]+\.\w+/gi, '');
    
    // Split into sentences
    const sentences = processed.split(/(?<=[.!?])\s+/).filter(s => s.length > 10);
    
    return {
        original: text,
        normalized: processed,
        sentences: sentences,
        wordCount: countWords(processed)
    };
}

// ========================================
// Agent Implementations (Heuristic-based)
// ========================================

function runReasoningAgent(processed) {
    // Extract key sentences based on position and keywords
    const sentences = processed.sentences;
    const keyIndicators = ['key', 'important', 'main', 'essential', 'critical', 'significant', 'primary', 'focus', 'because', 'therefore', 'thus', 'result'];
    
    // Score sentences
    const scored = sentences.map((sentence, index) => {
        let score = 0;
        
        // Position weight (first and last sentences often important)
        if (index < 2) score += 3;
        if (index === sentences.length - 1) score += 2;
        
        // Keyword weight
        const lowerSentence = sentence.toLowerCase();
        keyIndicators.forEach(indicator => {
            if (lowerSentence.includes(indicator)) score += 2;
        });
        
        // Length weight (prefer medium-length sentences)
        const wordCount = countWords(sentence);
        if (wordCount >= 10 && wordCount <= 30) score += 1;
        
        return { sentence, score, index };
    });
    
    // Sort by score and take top sentences
    const topSentences = scored
        .sort((a, b) => b.score - a.score)
        .slice(0, Math.max(3, Math.ceil(sentences.length * 0.3)))
        .sort((a, b) => a.index - b.index)
        .map(item => item.sentence);
    
    return {
        summary: topSentences.join(' '),
        confidence: 0.75,
        keyPoints: topSentences.length
    };
}

function runVerificationAgent(processed, reasoningResult) {
    // Verify claims exist in original text
    const originalLower = processed.normalized.toLowerCase();
    const summaryWords = reasoningResult.summary.toLowerCase().split(/\s+/);
    
    // Check word overlap
    const significantWords = summaryWords.filter(w => w.length > 4);
    const matchedWords = significantWords.filter(w => originalLower.includes(w));
    const coverage = significantWords.length > 0 ? matchedWords.length / significantWords.length : 0;
    
    return {
        verified: coverage > 0.7,
        coverage: Math.round(coverage * 100),
        issues: coverage < 0.7 ? ['Some claims may not be directly from source'] : [],
        confidence: coverage
    };
}

function runSimplificationAgent(processed, reasoningResult) {
    let simplified = reasoningResult.summary;
    
    // Replace complex words with simpler alternatives
    const replacements = {
        'utilize': 'use',
        'implement': 'set up',
        'facilitate': 'help',
        'demonstrate': 'show',
        'significant': 'important',
        'approximately': 'about',
        'subsequently': 'then',
        'consequently': 'so',
        'nevertheless': 'but',
        'furthermore': 'also'
    };
    
    Object.entries(replacements).forEach(([complex, simple]) => {
        simplified = simplified.replace(new RegExp(complex, 'gi'), simple);
    });
    
    // Calculate readability improvement
    const originalWordLength = averageWordLength(reasoningResult.summary);
    const simplifiedWordLength = averageWordLength(simplified);
    
    return {
        summary: simplified,
        readabilityImproved: simplifiedWordLength < originalWordLength,
        avgWordLength: simplifiedWordLength.toFixed(1),
        confidence: 0.8
    };
}

function runCritiqueAgent(processed, reasoningResult) {
    const summary = reasoningResult.summary;
    const original = processed.normalized;
    const issues = [];
    
    // Check coverage
    const summaryWordCount = countWords(summary);
    const originalWordCount = countWords(original);
    const compressionRatio = 1 - (summaryWordCount / originalWordCount);
    
    if (compressionRatio > 0.9) {
        issues.push('Summary may be over-compressed');
    }
    if (compressionRatio < 0.3) {
        issues.push('Summary could be more concise');
    }
    
    // Check for potential missing info (simple heuristic)
    const importantTerms = extractImportantTerms(original);
    const missedTerms = importantTerms.filter(term => !summary.toLowerCase().includes(term.toLowerCase()));
    
    if (missedTerms.length > 3) {
        issues.push(`May be missing: ${missedTerms.slice(0, 3).join(', ')}`);
    }
    
    return {
        issues: issues,
        compressionRatio: Math.round(compressionRatio * 100),
        quality: issues.length === 0 ? 'Good' : issues.length < 2 ? 'Fair' : 'Needs improvement',
        confidence: 0.7
    };
}

// ========================================
// Output Refiner
// ========================================
function refineSummary(reasoning, verification, simplification, critique) {
    // Use simplified version if verification passed
    let finalSummary = verification.verified ? simplification.summary : reasoning.summary;
    
    // Clean up final text
    finalSummary = finalSummary
        .replace(/\s+/g, ' ')
        .replace(/\s+([.,!?])/g, '$1')
        .trim();
    
    // Ensure proper capitalization
    finalSummary = finalSummary.charAt(0).toUpperCase() + finalSummary.slice(1);
    
    // Ensure ends with period
    if (!finalSummary.endsWith('.') && !finalSummary.endsWith('!') && !finalSummary.endsWith('?')) {
        finalSummary += '.';
    }
    
    return finalSummary;
}

// ========================================
// Display Results
// ========================================
function displayResults(result, originalText, latency) {
    // Update output
    const outputPlaceholder = document.getElementById('outputPlaceholder');
    const outputContent = document.getElementById('outputContent');
    
    outputPlaceholder.classList.add('hidden');
    outputContent.classList.remove('hidden');
    outputContent.innerHTML = `<p>${result.summary}</p>`;
    
    // Update stats
    const statsBar = document.getElementById('statsBar');
    statsBar.classList.add('visible');
    
    document.getElementById('originalWords').textContent = countWords(originalText);
    document.getElementById('summaryWords').textContent = countWords(result.summary);
    
    const compression = Math.round((1 - countWords(result.summary) / countWords(originalText)) * 100);
    document.getElementById('compression').textContent = compression;
    document.getElementById('latency').textContent = Math.round(latency);
    
    // Update debug panel if enabled
    if (state.debugMode && result.agents) {
        updateDebugPanel(result.agents);
    }
}

function updateDebugPanel(agents) {
    // Reasoning
    const reasoningOutput = document.getElementById('reasoningOutput');
    reasoningOutput.innerHTML = `
        <strong>Key points extracted:</strong> ${agents.reasoning.keyPoints}<br>
        <strong>Confidence:</strong> ${Math.round(agents.reasoning.confidence * 100)}%
    `;
    
    // Verification
    const verificationOutput = document.getElementById('verificationOutput');
    verificationOutput.innerHTML = `
        <strong>Verified:</strong> ${agents.verification.verified ? '✓ Yes' : '✗ No'}<br>
        <strong>Coverage:</strong> ${agents.verification.coverage}%
        ${agents.verification.issues.length > 0 ? '<br><strong>Issues:</strong> ' + agents.verification.issues.join(', ') : ''}
    `;
    
    // Simplification
    const simplificationOutput = document.getElementById('simplificationOutput');
    simplificationOutput.innerHTML = `
        <strong>Readability improved:</strong> ${agents.simplification.readabilityImproved ? '✓ Yes' : 'No change'}<br>
        <strong>Avg word length:</strong> ${agents.simplification.avgWordLength} chars
    `;
    
    // Critique
    const critiqueOutput = document.getElementById('critiqueOutput');
    critiqueOutput.innerHTML = `
        <strong>Quality:</strong> ${agents.critique.quality}<br>
        <strong>Compression:</strong> ${agents.critique.compressionRatio}%
        ${agents.critique.issues.length > 0 ? '<br><strong>Suggestions:</strong> ' + agents.critique.issues.join(', ') : ''}
    `;
    
    // Animate cards
    document.querySelectorAll('.agent-card').forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('active');
        }, index * 100);
    });
}

// ========================================
// UI State Management
// ========================================
function setProcessingState(isProcessing) {
    state.isProcessing = isProcessing;
    const summarizeBtn = document.getElementById('summarizeBtn');
    
    if (isProcessing) {
        summarizeBtn.classList.add('loading');
        summarizeBtn.disabled = true;
    } else {
        summarizeBtn.classList.remove('loading');
        summarizeBtn.disabled = false;
    }
}

// ========================================
// Utility Functions
// ========================================
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function averageWordLength(text) {
    const words = text.split(/\s+/).filter(w => w.length > 0);
    if (words.length === 0) return 0;
    
    const totalLength = words.reduce((sum, word) => sum + word.length, 0);
    return totalLength / words.length;
}

function extractImportantTerms(text) {
    // Simple TF-based extraction
    const words = text.toLowerCase().split(/\s+/);
    const stopWords = new Set(['the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while', 'this', 'that', 'these', 'those', 'it', 'its']);
    
    const wordFreq = {};
    words.forEach(word => {
        const cleaned = word.replace(/[^a-z]/g, '');
        if (cleaned.length > 4 && !stopWords.has(cleaned)) {
            wordFreq[cleaned] = (wordFreq[cleaned] || 0) + 1;
        }
    });
    
    return Object.entries(wordFreq)
        .filter(([_, count]) => count >= 2)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([word]) => word);
}

function showToast(message) {
    // Remove existing toast
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Remove after delay
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

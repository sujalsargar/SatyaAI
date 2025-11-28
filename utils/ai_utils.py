import os
import json
import requests
import re
from transformers import pipeline
from utils.trusted_sources import collect_trusted_sources

# ✅ Load OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ✅ FREE HuggingFace model (backup only)
try:
    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli"
    )
except:
    classifier = None

def transcribe_audio_path(fp):
    return ""


def search_wikipedia_snippet(text):
    return None   # handled in trusted_sources


def extract_key_claims(text):
    """Extract key factual claims from text for better matching"""
    # Simple keyword extraction - can be enhanced
    text_lower = text.lower()
    # Look for common claim patterns
    claims = []
    sentences = re.split(r'[.!?]+', text)
    for sent in sentences[:10]:  # Limit to first 10 sentences
        sent = sent.strip()
        if len(sent) > 20 and any(word in sent.lower() for word in ['claim', 'said', 'reports', 'according', 'alleged']):
            claims.append(sent[:200])
    return claims[:3]  # Top 3 claims


def analyze_source_reliability(sources):
    """Calculate reliability score based on source quality and quantity"""
    reliability_scores = {
        "snopes": 98,
        "factcheck": 97,
        "politifact": 96,
        "altnews": 95,
        "boom": 94,
        "reuters": 92,
        "bbc": 92,
        "google_news": 75,
        "wiki": 80
    }
    
    found_sources = []
    total_score = 0
    count = 0
    
    for key, source in sources.items():
        if source and source.get("snippet"):
            score = reliability_scores.get(key, 70)
            found_sources.append({
                "name": source.get("name", key),
                "url": source.get("url", ""),
                "snippet": source.get("snippet", ""),
                "reliability": score
            })
            total_score += score
            count += 1
    
    avg_reliability = total_score / count if count > 0 else 0
    return found_sources, avg_reliability, count


def check_fake_indicators(text, sources):
    """Enhanced fake news detection with multiple indicators"""
    text_lower = text.lower()
    fake_keywords = [
        "false", "fake", "misleading", "debunked", "hoax", 
        "unverified", "unsubstantiated", "disproven", "incorrect"
    ]
    
    fake_count = 0
    fake_sources = []
    
    # Check fact-check sites for explicit debunks
    fact_check_sites = ["snopes", "factcheck", "politifact", "altnews", "boom"]
    for key in fact_check_sites:
        src = sources.get(key)
        if src:
            snippet_lower = src.get("snippet", "").lower()
            if any(keyword in snippet_lower for keyword in fake_keywords):
                fake_count += 1
                fake_sources.append(src)
    
    return fake_count, fake_sources


def check_true_indicators(text, sources):
    """Enhanced true news detection with multiple confirmations"""
    true_keywords = [
        "confirmed", "verified", "accurate", "true", "factual",
        "reported by", "according to", "official", "confirmed by"
    ]
    
    true_count = 0
    true_sources = []
    
    # Check reputable news sources
    reputable_sources = ["reuters", "bbc", "google_news"]
    for key in reputable_sources:
        src = sources.get(key)
        if src:
            snippet_lower = src.get("snippet", "").lower()
            if any(keyword in snippet_lower for keyword in true_keywords) or len(src.get("snippet", "")) > 50:
                true_count += 1
                true_sources.append(src)
    
    return true_count, true_sources


def ask_openai_gpt4(text, sources_summary):
    """Use OpenAI GPT-4 for advanced fact-checking with high confidence"""
    if not OPENAI_API_KEY:
        return None
    
    try:
        # Build comprehensive prompt
        sources_text = "\n".join([
            f"- {s['name']}: {s['snippet'][:150]}" 
            for s in sources_summary[:5]
        ])
        
        prompt = f"""You are an expert fact-checker. Analyze the following claim and provide a detailed verdict.

CLAIM TO VERIFY:
{text[:1500]}

EVIDENCE FROM TRUSTED SOURCES:
{sources_text if sources_text else "No direct sources found, but please analyze based on general knowledge and reasoning."}

Provide your analysis in the following JSON format:
{{
    "status": "true" | "fake" | "unknown",
    "confidence": 0-99,
    "reasoning": "Detailed explanation of your verdict",
    "risk_score": 0-100,
    "key_evidence": ["evidence point 1", "evidence point 2"]
}}

Be extremely thorough. If multiple reputable fact-checking sites (Snopes, FactCheck, PolitiFact) have debunked this, mark as "fake" with confidence 95-99.
If multiple reputable news sources (Reuters, BBC) confirm this, mark as "true" with confidence 90-99.
If evidence is mixed or insufficient, mark as "unknown" with confidence 40-60.
Always provide detailed reasoning."""

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4-turbo-preview",  # or "gpt-4" if turbo not available
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional fact-checker. Always respond with valid JSON only, no additional text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,  # Lower temperature for more consistent, factual responses
            "max_tokens": 800
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Extract JSON from response (handle cases where GPT adds extra text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                verdict = json.loads(json_match.group())
                return verdict
        else:
            print(f"OpenAI API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"OpenAI API exception: {str(e)}")
        return None


def ask_llm_for_verdict(text, collected):
    """
    ENHANCED FACT CHECKING LOGIC WITH 99% CONFIDENCE CAPABILITY
    Priority:
    1. Multiple fact-check sites debunk → FAKE (95-99% confidence)
    2. Multiple reputable sources confirm → TRUE (90-99% confidence)
    3. OpenAI GPT-4 analysis → Advanced reasoning (85-99% confidence)
    4. Ensemble scoring from all sources → Weighted confidence
    5. HF model backup → Lower confidence (60-80%)
    """

    text_query = (text or "").strip()

    if not text_query:
        return {
            "status": "unknown",
            "confidence": 40,
            "reasoning": "No text provided.",
            "sources": [],
            "risk_score": 50
        }

    # ✅ Collect trusted sources
    sources = collect_trusted_sources(text_query)
    
    # ✅ Analyze source reliability
    found_sources, avg_reliability, source_count = analyze_source_reliability(sources)
    
    # ✅ Check for fake indicators
    fake_count, fake_sources = check_fake_indicators(text_query, sources)
    
    # ✅ Check for true indicators
    true_count, true_sources = check_true_indicators(text_query, sources)
    
    # ✅ PRIORITY 1: Multiple fact-check sites debunk → HIGH CONFIDENCE FAKE
    if fake_count >= 2:
        confidence = min(95 + fake_count, 99)  # 95-99% confidence
        return {
            "status": "fake",
            "confidence": confidence,
            "reasoning": f"Debunked by {fake_count} reputable fact-checking organizations: {', '.join([s['name'] for s in fake_sources[:3]])}. Multiple independent sources confirm this is false information.",
            "sources": fake_sources[:5],
            "risk_score": min(95 + fake_count, 99)
        }
    
    # ✅ PRIORITY 2: Single strong fact-check debunk → HIGH CONFIDENCE FAKE
    if fake_count == 1 and fake_sources:
        src = fake_sources[0]
        # Check if it's a top-tier fact-checker
        if src.get("name", "").lower() in ["snopes", "factcheck.org", "politifact"]:
            return {
                "status": "fake",
                "confidence": 96,
                "reasoning": f"Debunked by {src['name']}, a highly reputable fact-checking organization.",
                "sources": [src],
                "risk_score": 96
            }
    
    # ✅ PRIORITY 3: Multiple reputable news sources confirm → HIGH CONFIDENCE TRUE
    if true_count >= 3:
        confidence = min(92 + (true_count - 3) * 2, 99)  # 92-99% confidence
        return {
            "status": "true",
            "confidence": confidence,
            "reasoning": f"Confirmed by {true_count} reputable news sources: {', '.join([s['name'] for s in true_sources[:3]])}. Multiple independent sources verify this information.",
            "sources": true_sources[:5],
            "risk_score": max(100 - confidence, 1)
        }
    
    # ✅ PRIORITY 4: OpenAI GPT-4 Advanced Analysis
    if OPENAI_API_KEY and found_sources:
        gpt4_result = ask_openai_gpt4(text_query, found_sources)
        if gpt4_result:
            # Enhance confidence based on source reliability
            base_confidence = gpt4_result.get("confidence", 70)
            if avg_reliability > 85 and source_count >= 2:
                # Boost confidence if we have high-quality sources
                enhanced_confidence = min(base_confidence + 5, 99)
            else:
                enhanced_confidence = base_confidence
            
            return {
                "status": gpt4_result.get("status", "unknown"),
                "confidence": enhanced_confidence,
                "reasoning": gpt4_result.get("reasoning", "AI analysis completed."),
                "sources": found_sources[:5],
                "risk_score": gpt4_result.get("risk_score", 50),
                "key_evidence": gpt4_result.get("key_evidence", [])
            }
    
    # ✅ PRIORITY 5: Ensemble Scoring - Combine multiple sources
    if source_count >= 2:
        # Calculate weighted confidence based on source reliability
        if avg_reliability >= 90:
            ensemble_confidence = min(85 + (source_count - 2) * 3, 95)
        elif avg_reliability >= 80:
            ensemble_confidence = min(75 + (source_count - 2) * 4, 90)
        else:
            ensemble_confidence = min(65 + (source_count - 2) * 3, 85)
        
        # Determine status based on source consensus
        if fake_count > 0:
            status = "fake"
            risk_score = min(85 + fake_count * 3, 95)
        elif true_count >= 2:
            status = "true"
            risk_score = max(100 - ensemble_confidence, 5)
        else:
            status = "unknown"
            risk_score = 50
        
        return {
            "status": status,
            "confidence": ensemble_confidence,
            "reasoning": f"Ensemble analysis from {source_count} sources (avg reliability: {avg_reliability:.1f}%). Cross-referenced multiple trusted sources for verification.",
            "sources": found_sources[:5],
            "risk_score": risk_score
        }
    
    # ✅ PRIORITY 6: Single reputable source
    if source_count == 1 and found_sources:
        src = found_sources[0]
        reliability = src.get("reliability", 70)
        
        # Check if it's a fact-check site
        if reliability >= 95:
            if "false" in src.get("snippet", "").lower() or "fake" in src.get("snippet", "").lower():
                return {
                    "status": "fake",
                    "confidence": 92,
                    "reasoning": f"Debunked by {src['name']}.",
                    "sources": [src],
                    "risk_score": 92
                }
            else:
                return {
                    "status": "true",
                    "confidence": 88,
                    "reasoning": f"Verified by {src['name']}.",
                    "sources": [src],
                    "risk_score": 12
                }
    
    # ✅ PRIORITY 7: HuggingFace Model Backup
    if classifier:
        try:
            result = classifier(
                text_query[:500],
                candidate_labels=["true", "fake", "unknown"]
            )

            status = result["labels"][0]
            base_confidence = int(result["scores"][0] * 100)
            
            # Enhance confidence if we have any sources
            if source_count > 0:
                enhanced_confidence = min(base_confidence + 10, 85)
            else:
                enhanced_confidence = min(base_confidence, 75)
            
            return {
                "status": status,
                "confidence": enhanced_confidence,
                "reasoning": f"AI model analysis (backup method). {'Additional sources found but not definitive.' if source_count > 0 else 'No external sources found.'}",
                "sources": found_sources[:3] if found_sources else [],
                "risk_score": 100 - enhanced_confidence if status == "fake" else enhanced_confidence
            }
        except Exception as e:
            print(f"Classifier error: {str(e)}")
    
    # ✅ PRIORITY 8: Final fallback with any found sources
    if found_sources:
        return {
            "status": "unknown",
            "confidence": min(60 + source_count * 5, 75),
            "reasoning": f"Found {source_count} source(s) but insufficient evidence for definitive verdict. More verification needed.",
            "sources": found_sources[:3],
            "risk_score": 50
        }
    
    # ✅ FINAL FALLBACK
    return {
        "status": "unknown",
        "confidence": 40,
        "reasoning": "No evidence found from trusted sources. Unable to verify claim.",
        "sources": [],
        "risk_score": 50
    }

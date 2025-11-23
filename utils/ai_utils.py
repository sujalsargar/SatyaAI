import os, json, requests
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")  # read runtime env
USE_OPENAI = bool(OPENAI_KEY)

if USE_OPENAI:
    import openai
    openai.api_key = OPENAI_KEY

def search_wikipedia_snippet(text):
    """Return short snippet from Wikipedia for quick evidence (best-effort)."""
    try:
        q = "+".join(text.split()[:20])
        url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro&explaintext&redirects=1&titles={q}"
        r = requests.get(url, timeout=8)
        j = r.json()
        pages = j.get("query", {}).get("pages", {})
        if pages:
            key = list(pages.keys())[0]
            snippet = pages[key].get("extract", "")
            return {"name": "Wikipedia", "url": f"https://en.wikipedia.org/?curid={key}", "snippet": snippet[:800]}
    except Exception:
        pass
    return None

def transcribe_audio_path(fp):
    """Use OpenAI Whisper if key present, else return empty string (or integrate other STT)."""
    if not USE_OPENAI:
        return ""
    try:
        with open(fp, "rb") as f:
            resp = openai.Audio.transcriptions.create(file=f, model="whisper-1")
            return resp.get("text", "")
    except Exception as e:
        print("Transcription error:", e)
        return ""

def ask_llm_for_verdict(text, collected):
    """
    Ask OpenAI to evaluate claims if available. If not available, run simple heuristic.
    Must return structured JSON:
    {
      status: "true"|"fake"|"unknown",
      confidence: number,
      reasoning: string,
      sources: [ { name, url, snippet } ],
      risk_score: number
    }
    """
    if USE_OPENAI:
        prompt = f"""
You are Satya AI, a precise fact-check assistant.

Input:
\"\"\"{(text or '')[:3000]}\"\"\"

Evidence summary (short): {collected.get('wiki') and collected['wiki']['snippet'][:1000] or 'N/A'}

Return exactly JSON with schema:
{{"status":"true"|"fake"|"unknown","confidence":number,"reasoning":string,"sources":[{{"name":"", "url":"", "snippet":""}}],"risk_score":number}}
Be concise and precise.
"""
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini" if "gpt-4o-mini" in openai.Model.list() else "gpt-4o",
                messages=[{"role":"system","content":"You are SATYA AI, a fact-check assistant."},{"role":"user","content":prompt}],
                max_tokens=700,
                temperature=0.0
            )
            txt = resp.choices[0].message.content
            start = txt.find("{")
            js = txt[start:]
            obj = json.loads(js)
            # basic sanitization
            obj['confidence'] = int(obj.get('confidence') or 40)
            obj['risk_score'] = int(obj.get('risk_score') or 50)
            return obj
        except Exception as e:
            print("LLM call error:", e)

    # fallback simple heuristic:
    text_l = (text or "").lower()
    fake_keywords = ["fake", "false", "not true", "hoax", "debunk"]
    true_keywords = ["official", "confirmed", "announced", "reported"]
    score = 40
    status = "unknown"
    for k in fake_keywords:
        if k in text_l:
            status = "fake"; score = 85; break
    if status == "unknown":
        for k in true_keywords:
            if k in text_l:
                status = "true"; score = 70; break
    if status == "unknown":
        status = "unknown"; score = 45

    reasoning = f"Simple heuristic: keywords matched. (OpenAI not configured.)"
    sources = []
    wiki = collected.get('wiki')
    if wiki:
        sources.append(wiki)
    return {"status": status, "confidence": score, "reasoning": reasoning, "sources": sources, "risk_score": int(score * 0.9)}

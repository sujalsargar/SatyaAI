# satya ai/flask_app/utils/trusted_sources.py
import json, time
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
from models import CacheEntry, db

CACHE_TTL = 60 * 60 * 24  # 24 hours

def _cache_get(key):
    entry = CacheEntry.query.filter_by(key=key).first()
    if not entry:
        return None
    age = (time.time() - entry.timestamp.timestamp())
    if age > CACHE_TTL:
        try:
            db.session.delete(entry)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return None
    try:
        return json.loads(entry.value)
    except Exception:
        return None

def _cache_set(key, value):
    text = json.dumps(value)
    entry = CacheEntry.query.filter_by(key=key).first()
    if entry:
        entry.value = text
        entry.timestamp = db.func.current_timestamp()
    else:
        entry = CacheEntry(key=key, value=text)
        db.session.add(entry)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

def wiki_summary(query):
    key = f"wiki:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        q = quote_plus(" ".join(query.split()[:20]))
        url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro&explaintext&redirects=1&titles={q}"
        r = requests.get(url, timeout=8)
        j = r.json()
        pages = j.get("query", {}).get("pages", {})
        if pages:
            pid = next(iter(pages))
            extract = pages[pid].get("extract", "")
            res = {"name": "Wikipedia", "url": f"https://en.wikipedia.org/?curid={pid}", "snippet": extract[:1200]}
            _cache_set(key, res)
            return res
    except Exception:
        pass
    return None

def snopes_search(query):
    key = f"snopes:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = f"https://www.snopes.com/?s={quote_plus(query)}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"satya-bot"})
        soup = BeautifulSoup(r.text, "html.parser")
        # find first result - site structure may change; best-effort
        first = soup.select_one(".search-results .card a") or soup.select_one(".article a")
        if first and first.get('href'):
            title = first.get_text(strip=True)[:200]
            href = first['href']
            res = {"name":"Snopes", "url": href, "snippet": title}
            _cache_set(key, res)
            return res
    except Exception:
        pass
    return None

def factcheck_search(query):
    key = f"factcheck:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = f"https://www.factcheck.org/?s={quote_plus(query)}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"satya-bot"})
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one(".entry-title a")
        if first and first.get('href'):
            title = first.get_text(strip=True)[:200]
            href = first['href']
            res = {"name":"FactCheck.org", "url": href, "snippet": title}
            _cache_set(key, res)
            return res
    except Exception:
        pass
    return None

def politifact_search(query):
    key = f"politifact:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = f"https://www.politifact.com/search/?q={quote_plus(query)}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"satya-bot"})
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one('.o-title a, .c-quote__title a')
        if first and first.get('href'):
            title = first.get_text(strip=True)[:200]
            href = first['href']
            if not href.startswith("http"):
                href = "https://www.politifact.com" + href
            res = {"name":"PolitiFact", "url": href, "snippet": title}
            _cache_set(key, res)
            return res
    except Exception:
        pass
    return None

def collect_trusted_sources(query):
    """
    Returns dict with keys 'wiki','snopes','factcheck','politifact' with best-effort results (or None).
    Results are cached for TTL in DB.
    """
    return {
        "wiki": wiki_summary(query),
        "snopes": snopes_search(query),
        "factcheck": factcheck_search(query),
        "politifact": politifact_search(query)
    }

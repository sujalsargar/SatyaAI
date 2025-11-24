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
        except:
            db.session.rollback()
        return None
    try:
        return json.loads(entry.value)
    except:
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
    except:
        db.session.rollback()


# ✅ GOOGLE NEWS
def google_news(query):
    key = f"gnews:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = f"https://news.google.com/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla"})
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one("article a")
        if first:
            title = first.get_text(strip=True)[:200]
            href = "https://news.google.com" + first['href'][1:]
            res = {"name":"Google News", "url": href, "snippet": title}
            _cache_set(key, res)
            return res
    except:
        pass
    return None


# ✅ ALT NEWS INDIA
def altnews_search(query):
    key = f"altnews:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = f"https://www.altnews.in/?s={quote_plus(query)}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla"})
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one(".td-module-title a")
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            res = {"name":"AltNews (India Fact Check)", "url": href, "snippet": title}
            _cache_set(key, res)
            return res
    except:
        pass
    return None


# ✅ BOOMLIVE INDIA
def boomlive_search(query):
    key = f"boom:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = f"https://www.boomlive.in/search?q={quote_plus(query)}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla"})
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one("a.card-title")
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            if not href.startswith("http"):
                href = "https://www.boomlive.in" + href
            res = {"name":"BoomLive (India Fact Check)", "url": href, "snippet": title}
            _cache_set(key, res)
            return res
    except:
        pass
    return None


# ✅ REUTERS
def reuters_search(query):
    key = f"reuters:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = f"https://www.reuters.com/site-search/?query={quote_plus(query)}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla"})
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one("a.search-result-title")
        if first:
            title = first.get_text(strip=True)[:200]
            href = "https://www.reuters.com" + first['href']
            res = {"name":"Reuters", "url": href, "snippet": title}
            _cache_set(key, res)
            return res
    except:
        pass
    return None


# ✅ BBC
def bbc_search(query):
    key = f"bbc:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = f"https://www.bbc.co.uk/search?q={quote_plus(query)}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla"})
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one(".ssrcss-6arcww-PromoHeadline a")
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            res = {"name":"BBC News", "url": href, "snippet": title}
            _cache_set(key, res)
            return res
    except:
        pass
    return None


# ✅ SNOPES
def snopes_search(query):
    key = f"snopes:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = f"https://www.snopes.com/?s={quote_plus(query)}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla"})
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one(".search-results .card a")
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            res = {"name":"Snopes", "url": href, "snippet": title}
            _cache_set(key, res)
            return res
    except:
        pass
    return None


# ✅ FACTCHECK.org
def factcheck_search(query):
    key = f"factcheck:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = f"https://www.factcheck.org/?s={quote_plus(query)}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla"})
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one(".entry-title a")
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            res = {"name":"FactCheck.org", "url": href, "snippet": title}
            _cache_set(key, res)
            return res
    except:
        pass
    return None


# ✅ POLITIFACT
def politifact_search(query):
    key = f"politifact:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = f"https://www.politifact.com/search/?q={quote_plus(query)}"
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla"})
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one('.o-title a, .c-quote__title a')
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            if not href.startswith("http"):
                href = "https://www.politifact.com" + href
            res = {"name":"PolitiFact", "url": href, "snippet": title}
            _cache_set(key, res)
            return res
    except:
        pass
    return None



def collect_trusted_sources(query):

    return {
        "google_news": google_news(query),
        "altnews": altnews_search(query),
        "boom": boomlive_search(query),
        "reuters": reuters_search(query),
        "bbc": bbc_search(query),
        "snopes": snopes_search(query),
        "factcheck": factcheck_search(query),
        "politifact": politifact_search(query),
    }

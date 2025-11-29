import json, time
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
from models import CacheEntry, db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info(f"Google News: Cache hit for query: {query[:50]}")
        return cached
    try:
        url = f"https://news.google.com/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        logger.info(f"Google News: Fetching {url}")
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one("article a")
        if first:
            title = first.get_text(strip=True)[:200]
            href = "https://news.google.com" + first['href'][1:]
            res = {"name":"Google News", "url": href, "snippet": title}
            _cache_set(key, res)
            logger.info(f"Google News: Found result - {title[:50]}")
            return res
        else:
            logger.warning(f"Google News: No results found for query: {query[:50]}")
    except requests.exceptions.Timeout:
        logger.error(f"Google News: Request timeout for query: {query[:50]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Google News: Connection error for query: {query[:50]} - {str(e)}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Google News: HTTP error {e.response.status_code} for query: {query[:50]}")
    except Exception as e:
        logger.error(f"Google News: Unexpected error for query: {query[:50]} - {str(e)}")
    return None


# ✅ ALT NEWS INDIA
def altnews_search(query):
    key = f"altnews:{query}"
    cached = _cache_get(key)
    if cached:
        logger.info(f"AltNews: Cache hit for query: {query[:50]}")
        return cached
    try:
        url = f"https://www.altnews.in/?s={quote_plus(query)}"
        logger.info(f"AltNews: Fetching {url}")
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one(".td-module-title a")
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            res = {"name":"AltNews (India Fact Check)", "url": href, "snippet": title}
            _cache_set(key, res)
            logger.info(f"AltNews: Found result - {title[:50]}")
            return res
        else:
            logger.warning(f"AltNews: No results found for query: {query[:50]}")
    except requests.exceptions.Timeout:
        logger.error(f"AltNews: Request timeout for query: {query[:50]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"AltNews: Connection error for query: {query[:50]} - {str(e)}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"AltNews: HTTP error {e.response.status_code} for query: {query[:50]}")
    except Exception as e:
        logger.error(f"AltNews: Unexpected error for query: {query[:50]} - {str(e)}")
    return None


# ✅ BOOMLIVE INDIA
def boomlive_search(query):
    key = f"boom:{query}"
    cached = _cache_get(key)
    if cached:
        logger.info(f"BoomLive: Cache hit for query: {query[:50]}")
        return cached
    try:
        url = f"https://www.boomlive.in/search?q={quote_plus(query)}"
        logger.info(f"BoomLive: Fetching {url}")
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one("a.card-title")
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            if not href.startswith("http"):
                href = "https://www.boomlive.in" + href
            res = {"name":"BoomLive (India Fact Check)", "url": href, "snippet": title}
            _cache_set(key, res)
            logger.info(f"BoomLive: Found result - {title[:50]}")
            return res
        else:
            logger.warning(f"BoomLive: No results found for query: {query[:50]}")
    except requests.exceptions.Timeout:
        logger.error(f"BoomLive: Request timeout for query: {query[:50]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"BoomLive: Connection error for query: {query[:50]} - {str(e)}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"BoomLive: HTTP error {e.response.status_code} for query: {query[:50]}")
    except Exception as e:
        logger.error(f"BoomLive: Unexpected error for query: {query[:50]} - {str(e)}")
    return None


# ✅ REUTERS
def reuters_search(query):
    key = f"reuters:{query}"
    cached = _cache_get(key)
    if cached:
        logger.info(f"Reuters: Cache hit for query: {query[:50]}")
        return cached
    try:
        url = f"https://www.reuters.com/site-search/?query={quote_plus(query)}"
        logger.info(f"Reuters: Fetching {url}")
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one("a.search-result-title")
        if first:
            title = first.get_text(strip=True)[:200]
            href = "https://www.reuters.com" + first['href']
            res = {"name":"Reuters", "url": href, "snippet": title}
            _cache_set(key, res)
            logger.info(f"Reuters: Found result - {title[:50]}")
            return res
        else:
            logger.warning(f"Reuters: No results found for query: {query[:50]}")
    except requests.exceptions.Timeout:
        logger.error(f"Reuters: Request timeout for query: {query[:50]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Reuters: Connection error for query: {query[:50]} - {str(e)}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Reuters: HTTP error {e.response.status_code} for query: {query[:50]}")
    except Exception as e:
        logger.error(f"Reuters: Unexpected error for query: {query[:50]} - {str(e)}")
    return None


# ✅ BBC
def bbc_search(query):
    key = f"bbc:{query}"
    cached = _cache_get(key)
    if cached:
        logger.info(f"BBC: Cache hit for query: {query[:50]}")
        return cached
    try:
        url = f"https://www.bbc.co.uk/search?q={quote_plus(query)}"
        logger.info(f"BBC: Fetching {url}")
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one(".ssrcss-6arcww-PromoHeadline a")
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            res = {"name":"BBC News", "url": href, "snippet": title}
            _cache_set(key, res)
            logger.info(f"BBC: Found result - {title[:50]}")
            return res
        else:
            logger.warning(f"BBC: No results found for query: {query[:50]}")
    except requests.exceptions.Timeout:
        logger.error(f"BBC: Request timeout for query: {query[:50]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"BBC: Connection error for query: {query[:50]} - {str(e)}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"BBC: HTTP error {e.response.status_code} for query: {query[:50]}")
    except Exception as e:
        logger.error(f"BBC: Unexpected error for query: {query[:50]} - {str(e)}")
    return None


# ✅ SNOPES
def snopes_search(query):
    key = f"snopes:{query}"
    cached = _cache_get(key)
    if cached:
        logger.info(f"Snopes: Cache hit for query: {query[:50]}")
        return cached
    try:
        url = f"https://www.snopes.com/?s={quote_plus(query)}"
        logger.info(f"Snopes: Fetching {url}")
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one(".search-results .card a")
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            res = {"name":"Snopes", "url": href, "snippet": title}
            _cache_set(key, res)
            logger.info(f"Snopes: Found result - {title[:50]}")
            return res
        else:
            logger.warning(f"Snopes: No results found for query: {query[:50]}")
    except requests.exceptions.Timeout:
        logger.error(f"Snopes: Request timeout for query: {query[:50]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Snopes: Connection error for query: {query[:50]} - {str(e)}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Snopes: HTTP error {e.response.status_code} for query: {query[:50]}")
    except Exception as e:
        logger.error(f"Snopes: Unexpected error for query: {query[:50]} - {str(e)}")
    return None


# ✅ FACTCHECK.org
def factcheck_search(query):
    key = f"factcheck:{query}"
    cached = _cache_get(key)
    if cached:
        logger.info(f"FactCheck: Cache hit for query: {query[:50]}")
        return cached
    try:
        url = f"https://www.factcheck.org/?s={quote_plus(query)}"
        logger.info(f"FactCheck: Fetching {url}")
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one(".entry-title a")
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            res = {"name":"FactCheck.org", "url": href, "snippet": title}
            _cache_set(key, res)
            logger.info(f"FactCheck: Found result - {title[:50]}")
            return res
        else:
            logger.warning(f"FactCheck: No results found for query: {query[:50]}")
    except requests.exceptions.Timeout:
        logger.error(f"FactCheck: Request timeout for query: {query[:50]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"FactCheck: Connection error for query: {query[:50]} - {str(e)}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"FactCheck: HTTP error {e.response.status_code} for query: {query[:50]}")
    except Exception as e:
        logger.error(f"FactCheck: Unexpected error for query: {query[:50]} - {str(e)}")
    return None


# ✅ POLITIFACT
def politifact_search(query):
    key = f"politifact:{query}"
    cached = _cache_get(key)
    if cached:
        logger.info(f"PolitiFact: Cache hit for query: {query[:50]}")
        return cached
    try:
        url = f"https://www.politifact.com/search/?q={quote_plus(query)}"
        logger.info(f"PolitiFact: Fetching {url}")
        r = requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        first = soup.select_one('.o-title a, .c-quote__title a')
        if first:
            title = first.get_text(strip=True)[:200]
            href = first['href']
            if not href.startswith("http"):
                href = "https://www.politifact.com" + href
            res = {"name":"PolitiFact", "url": href, "snippet": title}
            _cache_set(key, res)
            logger.info(f"PolitiFact: Found result - {title[:50]}")
            return res
        else:
            logger.warning(f"PolitiFact: No results found for query: {query[:50]}")
    except requests.exceptions.Timeout:
        logger.error(f"PolitiFact: Request timeout for query: {query[:50]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"PolitiFact: Connection error for query: {query[:50]} - {str(e)}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"PolitiFact: HTTP error {e.response.status_code} for query: {query[:50]}")
    except Exception as e:
        logger.error(f"PolitiFact: Unexpected error for query: {query[:50]} - {str(e)}")
    return None



# ✅ WIKIPEDIA API
def wikipedia_search(query):
    key = f"wiki:{query}"
    cached = _cache_get(key)
    if cached:
        logger.info(f"Wikipedia: Cache hit for query: {query[:50]}")
        return cached
    try:
        # Extract key terms for Wikipedia search
        search_terms = query[:100].split()[:5]  # First 5 words
        search_query = " ".join(search_terms)
        
        # Wikipedia API search
        search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote_plus(search_query)
        logger.info(f"Wikipedia: Fetching {search_url}")
        r = requests.get(search_url, timeout=8, headers={"User-Agent": "TruthMate/1.0"})
        
        if r.status_code == 200:
            data = r.json()
            if data.get("extract"):
                res = {
                    "name": "Wikipedia",
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "snippet": data.get("extract", "")[:300]
                }
                _cache_set(key, res)
                logger.info(f"Wikipedia: Found result - {data.get('title', 'Unknown')}")
                return res
            else:
                logger.warning(f"Wikipedia: No extract found for query: {query[:50]}")
        else:
            logger.warning(f"Wikipedia: HTTP {r.status_code} for query: {query[:50]}")
    except requests.exceptions.Timeout:
        logger.error(f"Wikipedia: Request timeout for query: {query[:50]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Wikipedia: Connection error for query: {query[:50]} - {str(e)}")
    except Exception as e:
        logger.error(f"Wikipedia: Error in summary API for query: {query[:50]} - {str(e)}")
    
    # Fallback: try Wikipedia search API
    try:
        search_url = f"https://en.wikipedia.org/api/rest_v1/page/search/{quote_plus(query[:50])}"
        logger.info(f"Wikipedia: Trying search API - {search_url}")
        r = requests.get(search_url, timeout=8, headers={"User-Agent": "TruthMate/1.0"})
        if r.status_code == 200:
            results = r.json()
            if results.get("pages") and len(results["pages"]) > 0:
                page = results["pages"][0]
                res = {
                    "name": "Wikipedia",
                    "url": f"https://en.wikipedia.org/wiki/{quote_plus(page.get('key', ''))}",
                    "snippet": page.get("snippet", "")[:300]
                }
                _cache_set(key, res)
                logger.info(f"Wikipedia: Found result via search API - {page.get('key', 'Unknown')}")
                return res
            else:
                logger.warning(f"Wikipedia: No pages found in search API for query: {query[:50]}")
        else:
            logger.warning(f"Wikipedia: HTTP {r.status_code} in search API for query: {query[:50]}")
    except requests.exceptions.Timeout:
        logger.error(f"Wikipedia: Search API timeout for query: {query[:50]}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Wikipedia: Search API connection error for query: {query[:50]} - {str(e)}")
    except Exception as e:
        logger.error(f"Wikipedia: Search API error for query: {query[:50]} - {str(e)}")
    
    return None


def collect_trusted_sources(query):
    """Collect all trusted sources in parallel for better performance"""
    logger.info(f"Collecting trusted sources for query: {query[:100]}")
    
    # Run all searches (they're cached, so safe to call all)
    sources = {
        "wiki": wikipedia_search(query),
        "google_news": google_news(query),
        "altnews": altnews_search(query),
        "boom": boomlive_search(query),
        "reuters": reuters_search(query),
        "bbc": bbc_search(query),
        "snopes": snopes_search(query),
        "factcheck": factcheck_search(query),
        "politifact": politifact_search(query),
    }
    
    # Count successful sources
    successful_sources = sum(1 for v in sources.values() if v is not None)
    logger.info(f"Source collection complete: {successful_sources}/{len(sources)} sources found")
    
    # Log which sources were found
    found_source_names = [k for k, v in sources.items() if v is not None]
    if found_source_names:
        logger.info(f"Found sources: {', '.join(found_source_names)}")
    else:
        logger.warning(f"No sources found for query: {query[:100]}")
    
    return sources

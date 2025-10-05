# src/fetch_parse_pmc.py (fetch portion)
import requests, time, os
from pathlib import Path

HEADERS = {"User-Agent": "SpaceApps/1.0 (email@you.org)"}

def fetch_and_cache(url, pmcid, outdir="models/raw_html", session=None):
    os.makedirs(outdir, exist_ok=True)
    path = Path(outdir) / f"{pmcid}.html"
    if path.exists():
        return path.read_text(encoding="utf8")
    sess = session or requests.Session()
    resp = sess.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    html = resp.text
    path.write_text(html, encoding="utf8")
    time.sleep(0.5)  # polite
    return html

# src/fetch_parse_pmc.py (parse portion)
from bs4 import BeautifulSoup
import re

def canonical_section(title):
    t = (title or "").lower()

    # common aliases mapped to canonical section tags
    SEC_ALIASES = [
        ("abstract", ["abstract", "summary"]),
        ("introduction", ["introduction", "background"]),
        ("methods", ["methods", "materials", "materials and methods", "methodology", "protocol", "procedures"]),
        ("results", ["results", "findings"]),
        ("discussion", ["discussion"]),
        ("results", ["results and discussion", "findings and discussion"]),  # normalize R&D to 'results'
        ("conclusion", ["conclusion", "conclusions", "general outcomes", "outcomes"]),
        ("acknowledgements", ["acknowledgements", "acknowledgments"]),
        ("funding", ["funding statement", "funding", "financial support", "funding sources", "grants", "sponsor"]),
        ("references", ["references", "bibliography", "reference list"]),
    ]
    for canon, keys in SEC_ALIASES:
        if any(k in t for k in keys):
            return canon

    # last resort
    return "other"

def parse_pmc_html(html):
    soup = BeautifulSoup(html, "lxml")
    parsed = {'abstract': '', 'sections': {}, 'funding': '', 'acknowledgements': '', 'references': []}
    # Abstract
    ab = soup.find(class_=re.compile("abstract", re.I)) or soup.find('abstract')
    if ab:
        parsed['abstract'] = " ".join(p.get_text(" ", strip=True) for p in ab.find_all(['p','div'])) or ab.get_text(" ", strip=True)
    # Body sections: capture h2/h3 headings and following paragraphs
    main = soup.find('article') or soup
    for header in main.find_all(['h2','h3']):
        title = header.get_text(" ", strip=True)
        texts = []
        for sib in header.next_siblings:
            if getattr(sib, "name", None) in ['h2','h3']:
                break
            if getattr(sib, "name", None) in ['p','div','section','ul','ol']:
                texts.append(sib.get_text(" ", strip=True))
        text = " ".join(t for t in texts if t).strip()
        if text:
            cname = canonical_section(title)
            parsed['sections'].setdefault(cname, "")
            parsed['sections'][cname] += " " + text
    # Fallback: if parser found no sections and no abstract, treat whole text as 'other'
    if not parsed['abstract'] and not parsed['sections']:
        full_text = soup.get_text(" ", strip=True)
        if full_text:
            parsed['sections']['other'] = full_text
    # heuristics for funding & acknowledgements from whole text
    full_text = soup.get_text(" ", strip=True)
    if not parsed['funding']:
        funding_sentences = [s for s in re.split(r'(?<=[.!?])\s+', full_text) if re.search(r'\b(fund|funding|supported by|grant|award)\b', s, re.I)]
        parsed['funding'] = " ".join(funding_sentences[:3])
    if not parsed['acknowledgements']:
        acks = [s for s in re.split(r'(?<=[.!?])\s+', full_text) if 'acknowledg' in s.lower()]
        parsed['acknowledgements'] = " ".join(acks[:3])
    # references quick scrape
    ref_block = soup.find(class_=re.compile("ref-list|references|bibliography", re.I)) or soup.find('ol', class_=re.compile('references', re.I))
    if ref_block:
        for li in ref_block.find_all(['li','div']):
            txt = li.get_text(" ", strip=True)
            if txt: parsed['references'].append(txt)
    return parsed


def parse_sections(html):
    """Backward-compatible wrapper expected by other modules.
    Returns the same structure as parse_pmc_html.
    """
    return parse_pmc_html(html)

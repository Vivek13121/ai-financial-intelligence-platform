"""
packages/pipeline/entity_service.py — Entity extraction using spaCy + alias normalization.

This service extracts structured entities (COMPANY, PERSON, ORGANIZATION, TOPIC)
from financial news article text using spaCy's NER pipeline, then normalizes
them through a curated alias dictionary.

Design decisions:
  - spaCy `en_core_web_sm` for lightweight, fast NER (~10ms per article on CPU).
  - Alias normalization resolves variants ("AAPL", "Apple Inc.") to canonical names.
  - No Gemini / LLM calls — zero API cost, runs entirely locally.
  - Returns a list of (entity_name, entity_type, relevance_score) tuples.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# spaCy model — module-level lazy loading
# ---------------------------------------------------------------------------
_NLP = None


def _get_nlp():
    """Load spaCy model on first call, cache for subsequent calls."""
    global _NLP
    if _NLP is None:
        import spacy
        try:
            _NLP = spacy.load("en_core_web_sm")
            logger.info("spaCy model 'en_core_web_sm' loaded successfully.")
        except OSError:
            logger.error(
                "spaCy model 'en_core_web_sm' not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
            raise
    return _NLP


# ---------------------------------------------------------------------------
# Alias normalization dictionary
# Maps lowercase alias → (canonical_name, entity_type, symbol)
# ---------------------------------------------------------------------------
COMPANY_ALIASES = {
    # Mega-cap tech
    "apple": ("Apple", "COMPANY", "AAPL"),
    "aapl": ("Apple", "COMPANY", "AAPL"),
    "apple inc": ("Apple", "COMPANY", "AAPL"),
    "apple inc.": ("Apple", "COMPANY", "AAPL"),
    "microsoft": ("Microsoft", "COMPANY", "MSFT"),
    "msft": ("Microsoft", "COMPANY", "MSFT"),
    "microsoft corp": ("Microsoft", "COMPANY", "MSFT"),
    "nvidia": ("Nvidia", "COMPANY", "NVDA"),
    "nvda": ("Nvidia", "COMPANY", "NVDA"),
    "nvidia corp": ("Nvidia", "COMPANY", "NVDA"),
    "nvidia corporation": ("Nvidia", "COMPANY", "NVDA"),
    "tesla": ("Tesla", "COMPANY", "TSLA"),
    "tsla": ("Tesla", "COMPANY", "TSLA"),
    "tesla inc": ("Tesla", "COMPANY", "TSLA"),
    "amazon": ("Amazon", "COMPANY", "AMZN"),
    "amzn": ("Amazon", "COMPANY", "AMZN"),
    "amazon.com": ("Amazon", "COMPANY", "AMZN"),
    "alphabet": ("Alphabet", "COMPANY", "GOOGL"),
    "google": ("Alphabet", "COMPANY", "GOOGL"),
    "googl": ("Alphabet", "COMPANY", "GOOGL"),
    "goog": ("Alphabet", "COMPANY", "GOOGL"),
    "alphabet inc": ("Alphabet", "COMPANY", "GOOGL"),
    "alphabet inc.": ("Alphabet", "COMPANY", "GOOGL"),
    "meta": ("Meta", "COMPANY", "META"),
    "meta platforms": ("Meta", "COMPANY", "META"),
    "facebook": ("Meta", "COMPANY", "META"),
    "netflix": ("Netflix", "COMPANY", "NFLX"),
    "nflx": ("Netflix", "COMPANY", "NFLX"),
    "netease": ("NetEase", "COMPANY", "NTES"),
    "ntes": ("NetEase", "COMPANY", "NTES"),
    "netease inc": ("NetEase", "COMPANY", "NTES"),
    "netease, inc.": ("NetEase", "COMPANY", "NTES"),

    # Semiconductors
    "intel": ("Intel", "COMPANY", "INTC"),
    "intc": ("Intel", "COMPANY", "INTC"),
    "amd": ("AMD", "COMPANY", "AMD"),
    "advanced micro devices": ("AMD", "COMPANY", "AMD"),
    "broadcom": ("Broadcom", "COMPANY", "AVGO"),
    "avgo": ("Broadcom", "COMPANY", "AVGO"),
    "qualcomm": ("Qualcomm", "COMPANY", "QCOM"),
    "qcom": ("Qualcomm", "COMPANY", "QCOM"),

    # Software / Cloud
    "oracle": ("Oracle", "COMPANY", "ORCL"),
    "orcl": ("Oracle", "COMPANY", "ORCL"),
    "salesforce": ("Salesforce", "COMPANY", "CRM"),
    "crm": ("Salesforce", "COMPANY", "CRM"),
    "adobe": ("Adobe", "COMPANY", "ADBE"),
    "adbe": ("Adobe", "COMPANY", "ADBE"),
    "ibm": ("IBM", "COMPANY", "IBM"),
    "palantir": ("Palantir", "COMPANY", "PLTR"),
    "pltr": ("Palantir", "COMPANY", "PLTR"),

    # Finance
    "jpmorgan": ("JPMorgan Chase", "COMPANY", "JPM"),
    "jpmorgan chase": ("JPMorgan Chase", "COMPANY", "JPM"),
    "jpm": ("JPMorgan Chase", "COMPANY", "JPM"),
    "bank of america": ("Bank of America", "COMPANY", "BAC"),
    "bac": ("Bank of America", "COMPANY", "BAC"),
    "goldman sachs": ("Goldman Sachs", "COMPANY", "GS"),
    "morgan stanley": ("Morgan Stanley", "COMPANY", "MS"),
    "citigroup": ("Citigroup", "COMPANY", "C"),
    "wells fargo": ("Wells Fargo", "COMPANY", "WFC"),

    # Retail / Consumer
    "walmart": ("Walmart", "COMPANY", "WMT"),
    "wmt": ("Walmart", "COMPANY", "WMT"),
    "target": ("Target", "COMPANY", "TGT"),
    "tgt": ("Target", "COMPANY", "TGT"),
    "costco": ("Costco", "COMPANY", "COST"),
    "cost": ("Costco", "COMPANY", "COST"),

    # Entertainment / Media
    "disney": ("Disney", "COMPANY", "DIS"),
    "walt disney": ("Disney", "COMPANY", "DIS"),
    "dis": ("Disney", "COMPANY", "DIS"),

    # Automotive / Industrials
    "boeing": ("Boeing", "COMPANY", "BA"),
    "ba": ("Boeing", "COMPANY", "BA"),
    "ford": ("Ford", "COMPANY", "F"),
    "general motors": ("General Motors", "COMPANY", "GM"),
    "gm": ("General Motors", "COMPANY", "GM"),
    "rivian": ("Rivian", "COMPANY", "RIVN"),

    # Energy
    "exxon": ("Exxon Mobil", "COMPANY", "XOM"),
    "exxon mobil": ("Exxon Mobil", "COMPANY", "XOM"),
    "xom": ("Exxon Mobil", "COMPANY", "XOM"),
    "chevron": ("Chevron", "COMPANY", "CVX"),
    "cvx": ("Chevron", "COMPANY", "CVX"),

    # Healthcare / Pharma
    "pfizer": ("Pfizer", "COMPANY", "PFE"),
    "pfe": ("Pfizer", "COMPANY", "PFE"),
    "moderna": ("Moderna", "COMPANY", "MRNA"),
    "mrna": ("Moderna", "COMPANY", "MRNA"),
    "eli lilly": ("Eli Lilly", "COMPANY", "LLY"),
    "lly": ("Eli Lilly", "COMPANY", "LLY"),
    "novo nordisk": ("Novo Nordisk", "COMPANY", "NVO"),
    "nvo": ("Novo Nordisk", "COMPANY", "NVO"),
    "johnson & johnson": ("Johnson & Johnson", "COMPANY", "JNJ"),
    "j&j": ("Johnson & Johnson", "COMPANY", "JNJ"),
    "unitedhealth": ("UnitedHealth", "COMPANY", "UNH"),

    # Fintech / Crypto
    "coinbase": ("Coinbase", "COMPANY", "COIN"),
    "coin": ("Coinbase", "COMPANY", "COIN"),
    "paypal": ("PayPal", "COMPANY", "PYPL"),
    "pypl": ("PayPal", "COMPANY", "PYPL"),
    "block": ("Block", "COMPANY", "SQ"),
    "square": ("Block", "COMPANY", "SQ"),
    "robinhood": ("Robinhood", "COMPANY", "HOOD"),

    # Telecom
    "at&t": ("AT&T", "COMPANY", "T"),
    "verizon": ("Verizon", "COMPANY", "VZ"),
    "t-mobile": ("T-Mobile", "COMPANY", "TMUS"),
}

# Organizations (non-company institutions)
ORGANIZATION_ALIASES = {
    "federal reserve": ("Federal Reserve", "ORGANIZATION", None),
    "the federal reserve": ("Federal Reserve", "ORGANIZATION", None),
    "the fed": ("Federal Reserve", "ORGANIZATION", None),
    "fed": ("Federal Reserve", "ORGANIZATION", None),
    "sec": ("SEC", "ORGANIZATION", None),
    "securities and exchange commission": ("SEC", "ORGANIZATION", None),
    "fda": ("FDA", "ORGANIZATION", None),
    "doj": ("DOJ", "ORGANIZATION", None),
    "department of justice": ("DOJ", "ORGANIZATION", None),
    "ftc": ("FTC", "ORGANIZATION", None),
    "european central bank": ("European Central Bank", "ORGANIZATION", None),
    "ecb": ("European Central Bank", "ORGANIZATION", None),
    "imf": ("IMF", "ORGANIZATION", None),
    "world bank": ("World Bank", "ORGANIZATION", None),
    "opec": ("OPEC", "ORGANIZATION", None),
    "congress": ("Congress", "ORGANIZATION", None),
    "white house": ("White House", "ORGANIZATION", None),
    "pentagon": ("Pentagon", "ORGANIZATION", None),
    "nato": ("NATO", "ORGANIZATION", None),
}

# spaCy entity label → our type mapping
SPACY_LABEL_MAP = {
    "ORG": "COMPANY",       # spaCy's ORG covers companies + orgs, we default to COMPANY
    "PERSON": "PERSON",
    "GPE": "ORGANIZATION",  # Geopolitical entities (countries, states)
}

# Words to skip even if spaCy identifies them as entities
ENTITY_STOP_WORDS = {
    "thestreet", "bloomberg", "cnbc", "yahoo", "associated press", "ap",
    "wall street", "nasdaq", "s&p", "dow jones", "nyse",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "the", "a", "an", "inc", "corp", "corporation", "ltd", "llc", "plc",
    "u.s.", "us", "uk", "eu", "china", "q1", "q2", "q3", "q4",
    "fy", "ceo", "cfo", "coo", "cto",
}


def _normalize_entity(text: str) -> Optional[tuple]:
    """
    Try to normalize an entity string through our alias dictionaries.
    Returns (canonical_name, entity_type, symbol) or None if not found.
    """
    key = text.lower().strip()

    # Check company aliases first (most common)
    if key in COMPANY_ALIASES:
        return COMPANY_ALIASES[key]

    # Check organization aliases
    if key in ORGANIZATION_ALIASES:
        return ORGANIZATION_ALIASES[key]

    return None


def _is_valid_entity(ent) -> bool:
    """
    Validate spaCy entities to reject action phrases and sentence fragments.
    """
    # Reject if any token is a verb (action phrase like "Bought Nvidia")
    if any(token.pos_ == "VERB" for token in ent):
        return False
        
    lower_text = ent.text.lower()
    # Reject contextual keywords that bleed into NER
    bad_keywords = {"stock", "shares", "options", "dividend", "earnings", "sell off", "optimism", "headlines", "news", "sinks", "surges", "jumps", "falls", "started"}
    for word in bad_keywords:
        if word in lower_text:
            return False
            
    return True


def extract_entities(title: str, content: str) -> list[dict]:
    """
    Extract entities from article title and content.

    Returns a list of dicts:
        [{"name": "Apple", "type": "COMPANY", "symbol": "AAPL", "relevance_score": 1.0}, ...]

    Strategy:
        1. Run spaCy NER on title and content separately.
        2. Normalize each entity through alias dictionary.
        3. For entities not in aliases, accept spaCy ORG/PERSON labels.
        4. Calculate relevance score: title mention = 1.0, body only = 0.5.
    """
    nlp = _get_nlp()

    # Track found entities: canonical_name → {type, symbol, in_title, in_body}
    found = {}

    def _process_doc(text: str, is_title: bool):
        if not text:
            return

        doc = nlp(text)
        all_aliases = {**COMPANY_ALIASES, **ORGANIZATION_ALIASES}

        for ent in doc.ents:
            ent_text = ent.text.strip()

            # Skip short or stop-word entities
            if len(ent_text) <= 1:
                continue
            if ent_text.lower() in ENTITY_STOP_WORDS:
                continue

            # Try alias normalization first
            normalized = _normalize_entity(ent_text)

            if normalized:
                canonical, etype, symbol = normalized
            elif ent.label_ in SPACY_LABEL_MAP:
                # If it doesn't match an alias perfectly, check if it contains an alias substring
                # This catches things like "Nvidia Blackwell" -> normalizes to "Nvidia"
                text_lower = ent_text.lower()
                found_alias = False
                for alias_key, (acanonical, aetype, asymbol) in all_aliases.items():
                    if len(alias_key) > 2 and re.search(r'\b' + re.escape(alias_key) + r'\b', text_lower):
                        canonical, etype, symbol = acanonical, aetype, asymbol
                        found_alias = True
                        break
                
                if not found_alias:
                    # Validate to reject action phrases and fragments
                    if not _is_valid_entity(ent):
                        continue
                        
                    # Accept spaCy's label if it's a type we care about
                    canonical = ent_text
                    etype = SPACY_LABEL_MAP[ent.label_]
                    symbol = None
                    # Skip very short unaliased entities (likely noise)
                    if len(canonical) <= 2:
                        continue
            else:
                continue

            if canonical not in found:
                found[canonical] = {
                    "type": etype,
                    "symbol": symbol,
                    "in_title": False,
                    "in_body": False,
                }

            if is_title:
                found[canonical]["in_title"] = True
            else:
                found[canonical]["in_body"] = True

        # Also do direct alias matching on the raw text (catches ticker symbols
        # and aliases that spaCy misses)
        text_lower = text.lower()
        for alias_key, (canonical, etype, symbol) in all_aliases.items():
            # Only match multi-word aliases or tickers (skip single common words)
            if len(alias_key) <= 2 and not alias_key.isupper():
                continue
            # Use word boundary matching
            pattern = r'\b' + re.escape(alias_key) + r'\b'
            if re.search(pattern, text_lower):
                if canonical not in found:
                    found[canonical] = {
                        "type": etype,
                        "symbol": symbol,
                        "in_title": False,
                        "in_body": False,
                    }
                if is_title:
                    found[canonical]["in_title"] = True
                else:
                    found[canonical]["in_body"] = True

    # Process title (high signal)
    _process_doc(title, is_title=True)

    # Process content (truncate to first 1000 chars for speed)
    content_truncated = content[:1000] if content else ""
    _process_doc(content_truncated, is_title=False)

    # Build result list with relevance scores
    results = []
    for canonical, info in found.items():
        if info["in_title"] and info["in_body"]:
            score = 1.0
        elif info["in_title"]:
            score = 0.9
        elif info["in_body"]:
            score = 0.5
        else:
            score = 0.3

        results.append({
            "name": canonical,
            "type": info["type"],
            "symbol": info["symbol"],
            "relevance_score": score,
        })

    # Sort by relevance (highest first)
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results

"""
Real-Time Web Search Service for EarthPulse AI Copilot
Combines Google News Live Article Search, Wikipedia Knowledge API,
and Web Scraper Fallbacks for zero-cost, keyless real-time external intelligence.
"""

import os
import re
import html
import json
import logging
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def clean_html(raw_html: str) -> str:
    """Strips HTML tags and unescapes entities."""
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


class WebSearchService:
    def __init__(self):
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        self.wiki_agent = "EarthPulse/1.0 (NASA Space Apps Challenge; contact@earthpulse.app)"

    def search_news(self, query: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """
        Fetches live breaking news, reports, and articles via Google News RSS.
        Keyless, highly available, and up-to-the-minute.
        """
        results = []
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            
            with urllib.request.urlopen(req, timeout=6.0) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                
                items = root.findall(".//item")
                for item in items[:max_results]:
                    t_el = item.find("title")
                    l_el = item.find("link")
                    d_el = item.find("description")
                    p_el = item.find("pubDate")
                    s_el = item.find("source")

                    title = t_el.text if t_el is not None and t_el.text else "News Article"
                    link = l_el.text if l_el is not None and l_el.text else ""
                    raw_desc = d_el.text if d_el is not None and d_el.text else ""
                    desc = clean_html(raw_desc)
                    pub_date = p_el.text if p_el is not None and p_el.text else ""
                    source_name = s_el.text if s_el is not None and s_el.text else "Live Web News"

                    # If title ends with "- Source Name", extract source cleanly
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        clean_title = parts[0].strip()
                        if source_name == "Live Web News":
                            source_name = parts[1].strip()
                    else:
                        clean_title = title.strip()

                    results.append({
                        "title": clean_title,
                        "url": link,
                        "snippet": desc[:280] if desc else clean_title,
                        "source": source_name,
                        "source_type": "web",
                        "date": pub_date,
                        "relevance": 0.92
                    })
        except Exception as e:
            logger.warning(f"Google News RSS search error: {e}")

        return results

    def search_wikipedia(self, query: str, max_results: int = 2) -> List[Dict[str, Any]]:
        """
        Fetches verified encyclopedia entries from Wikipedia API for scientific/geographic concepts.
        """
        results = []
        try:
            encoded_query = urllib.parse.quote(query)
            url = (
                f"https://en.wikipedia.org/w/api.php?action=query&list=search"
                f"&srsearch={encoded_query}&format=json&utf8="
            )
            req = urllib.request.Request(url, headers={"User-Agent": self.wiki_agent})
            
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                search_items = data.get("query", {}).get("search", [])
                
                for item in search_items[:max_results]:
                    title = item.get("title", "")
                    raw_snippet = item.get("snippet", "")
                    clean_snippet = clean_html(raw_snippet)
                    page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"

                    results.append({
                        "title": title,
                        "url": page_url,
                        "snippet": clean_snippet[:280] if clean_snippet else f"Wikipedia article on {title}",
                        "source": "Wikipedia Global Encyclopedia",
                        "source_type": "web",
                        "date": "",
                        "relevance": 0.88
                    })
        except Exception as e:
            logger.warning(f"Wikipedia search error: {e}")

        return results

    def normalize_query(self, query: str) -> str:
        """Translates Banglish/Bangla terms and strips prefixes for optimal search precision."""
        q = query.lower()
        q = re.sub(
            r"^(search web for|search the web for|web search|google search|search internet for|"
            r"search google for|online e khujo|web e search koro|khobor ki|news on|khobor dekhao|"
            r"খোঁজ করো|ওয়েব সার্চ করো)[:\s]*",
            "", q, flags=re.IGNORECASE
        ).strip()

        mappings = {
            r"\baguner\b": "wildfire",
            r"\bagun\b": "wildfire",
            r"\bআগুনের\b": "wildfire",
            r"\bআগুন\b": "wildfire",
            r"\bdabanol\b": "wildfire",
            r"\bদাবানল\b": "wildfire",
            r"\bkhobor\b": "news",
            r"\bখবর\b": "news",
            r"\bobostha\b": "status",
            r"\bঅবস্থা\b": "status",
        }
        for pat, rep in mappings.items():
            q = re.sub(pat, rep, q)

        stop_words = {
            "e", "te", "er", "ki", "kothay", "kemon", "ache", "koro", "korun",
            "bolo", "dekhao", "niye", "jeno", "paro", "tumi", "apni", "shuno", "eta"
        }
        tokens = [t for t in re.findall(r"[a-zA-Z0-9\u0980-\u09FF]+", q) if t.lower() not in stop_words]
        return " ".join(tokens).strip() or query

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Executes unified multi-provider web search.
        Deduplicates by title and URL, returning top ranked web sources.
        """
        clean_q = self.normalize_query(query)

        news_results = self.search_news(clean_q, max_results=4)
        if not news_results:
            raw_stripped = re.sub(r"^(search web for|web search koro|web search)[:\s]*", "", query, flags=re.IGNORECASE).strip()
            if raw_stripped and raw_stripped != clean_q:
                news_results = self.search_news(raw_stripped, max_results=4)

        wiki_results = self.search_wikipedia(clean_q, max_results=2) or []
        combined = (news_results or []) + wiki_results
        
        # Deduplicate
        seen_titles = set()
        deduped = []
        for item in combined:
            t_key = item["title"].lower().strip()
            if t_key not in seen_titles and item["url"]:
                seen_titles.add(t_key)
                deduped.append(item)

        return deduped[:max_results]

    def format_search_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Formats web search results into a clean text block for prompt grounding."""
        if not search_results:
            return ""

        context_lines = ["[REAL-TIME WEB SEARCH RESULTS]"]
        for i, item in enumerate(search_results, start=1):
            date_str = f" ({item['date']})" if item.get("date") else ""
            context_lines.append(
                f"{i}. Title: {item['title']}\n"
                f"   Publisher/Source: {item['source']}{date_str}\n"
                f"   URL: {item['url']}\n"
                f"   Summary: {item['snippet']}\n"
            )

        return "\n".join(context_lines)


# Global singleton
web_search_service = WebSearchService()

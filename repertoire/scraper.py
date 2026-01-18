"""Web scraping for musicalifeiten.nl."""
from __future__ import annotations

import random
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .parser import extract_text_from_html


class MusicaliefeitenScraper:
    """Scraper for musicalifeiten.nl content."""

    BASE_URL = "https://www.musicalifeiten.nl"
    
    # Available rubrics (categories)
    RUBRICS = {
        "portretten": "/composers/portraits",
        "discografieen": "/discographies",
        "mini_discografieen": "/mini-discographies",
        "vergelijkingen": "/comparisons",
        "mini_vergelijkingen": "/mini-comparisons",
    }

    def __init__(self, throttle: float = 1.0, timeout: int = 10):
        """Initialize scraper.
        
        Args:
            throttle: Seconds to wait between requests (respect rate limits)
            timeout: Request timeout in seconds
        """
        self.throttle = throttle
        self.timeout = timeout
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "User-Agent": "Repertoire/0.1.0 (Classical Music Manager)"
        })
        return session

    def scrape_random_page(self, rubric: str = "portretten") -> Optional[str]:
        """Scrape a random page from the specified rubric.
        
        Args:
            rubric: Which rubric to scrape from (portretten, discografieen, etc.)
            
        Returns:
            HTML content of the page, or None if scraping failed
        """
        if rubric not in self.RUBRICS:
            raise ValueError(f"Unknown rubric: {rubric}. Available: {list(self.RUBRICS.keys())}")

        try:
            # Get a random letter page
            letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            url = f"{self.BASE_URL}/composers/by-name/{letter.lower()}/"
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Wait before returning to respect rate limits
            time.sleep(self.throttle)
            
            return response.text
        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")
            return None

    def scrape_url(self, url: str) -> Optional[str]:
        """Scrape a specific URL.
        
        Args:
            url: Full URL to scrape
            
        Returns:
            HTML content, or None if scraping failed
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            time.sleep(self.throttle)
            return response.text
        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")
            return None

    def extract_content(self, html: str) -> list[str]:
        """Extract text paragraphs from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            List of text paragraphs
        """
        return extract_text_from_html(html)

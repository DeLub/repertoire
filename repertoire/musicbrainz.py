"""Integration with MusicBrainz for standardizing composer names and work titles."""
from __future__ import annotations

import os
from typing import Optional, Any
import requests
from functools import lru_cache


class MusicBrainzIntegration:
    """Interface for MusicBrainz API integration."""

    BASE_URL = "https://musicbrainz.org/ws/2"
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        """Initialize MusicBrainz integration.
        
        Args:
            api_key: MusicBrainz API key (optional)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("MUSICBRAINZ_API_KEY")
        self.timeout = timeout
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with proper headers."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Repertoire/0.1.0 (Classical Music Manager) "
                         "contact@example.com"
        })
        return session

    @lru_cache(maxsize=256)
    def search_artist(self, name: str, artist_type: str = "Person") -> Optional[dict[str, Any]]:
        """Search for an artist (composer) in MusicBrainz.
        
        Args:
            name: Artist name to search for
            artist_type: Type of artist ("Person", "Orchestra", "Choir", etc.)
            
        Returns:
            Dictionary with standardized artist info, or None if not found
        """
        try:
            query = f'artist:"{name}" AND type:"{artist_type}"'
            response = self.session.get(
                f"{self.BASE_URL}/artist",
                params={
                    "query": query,
                    "limit": 5,
                    "fmt": "json",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("artists"):
                # Return the best match (first result)
                artist = data["artists"][0]
                return {
                    "mb_id": artist.get("id"),
                    "name": artist.get("name"),
                    "sort_name": artist.get("sort-name"),
                    "type": artist.get("type"),
                    "country": artist.get("country"),
                    "life_span": artist.get("life-span", {}),
                }
            return None
        except requests.RequestException as e:
            print(f"Error searching MusicBrainz for '{name}': {e}")
            return None

    @lru_cache(maxsize=256)
    def search_work(self, title: str, composer_name: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Search for a musical work in MusicBrainz.
        
        Args:
            title: Work title to search for
            composer_name: Optional composer name for more precise search
            
        Returns:
            Dictionary with standardized work info, or None if not found
        """
        try:
            query = f'work:"{title}"'
            if composer_name:
                query += f' AND composer:"{composer_name}"'
            
            response = self.session.get(
                f"{self.BASE_URL}/work",
                params={
                    "query": query,
                    "limit": 5,
                    "fmt": "json",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("works"):
                work = data["works"][0]
                return {
                    "mb_id": work.get("id"),
                    "title": work.get("title"),
                    "type": work.get("type"),
                    "language": work.get("language"),
                    "composer": self._extract_composer_from_relations(work.get("relations", [])),
                }
            return None
        except requests.RequestException as e:
            print(f"Error searching MusicBrainz for work '{title}': {e}")
            return None

    def _extract_composer_from_relations(self, relations: list) -> Optional[dict[str, Any]]:
        """Extract composer info from work relations.
        
        Args:
            relations: List of relations from MusicBrainz work
            
        Returns:
            Composer info or None
        """
        for relation in relations:
            if relation.get("type-id") == "ea6f0698-6782-30d6-b16d-293081b66774":  # composer
                artist = relation.get("artist", {})
                return {
                    "mb_id": artist.get("id"),
                    "name": artist.get("name"),
                }
        return None

    @lru_cache(maxsize=128)
    def get_artist_info(self, mb_id: str) -> Optional[dict[str, Any]]:
        """Get detailed artist information from MusicBrainz.
        
        Args:
            mb_id: MusicBrainz artist ID
            
        Returns:
            Detailed artist information
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/artist/{mb_id}",
                params={
                    "inc": "recordings+works",
                    "fmt": "json",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            artist = response.json()
            return {
                "mb_id": artist.get("id"),
                "name": artist.get("name"),
                "sort_name": artist.get("sort-name"),
                "type": artist.get("type"),
                "country": artist.get("country"),
                "life_span": artist.get("life-span", {}),
                "begin_year": artist.get("life-span", {}).get("begin"),
                "end_year": artist.get("life-span", {}).get("end"),
            }
        except requests.RequestException as e:
            print(f"Error fetching artist {mb_id} from MusicBrainz: {e}")
            return None

    def standardize_composer_name(self, name: str) -> Optional[str]:
        """Get standardized composer name from MusicBrainz.
        
        Args:
            name: Composer name (possibly non-standard)
            
        Returns:
            Standardized name from MusicBrainz, or None if not found
        """
        result = self.search_artist(name)
        if result:
            return result.get("name")
        return None

    def standardize_work_title(self, title: str, composer_name: Optional[str] = None) -> Optional[str]:
        """Get standardized work title from MusicBrainz.
        
        Args:
            title: Work title (possibly non-standard)
            composer_name: Optional composer name for better matching
            
        Returns:
            Standardized title from MusicBrainz, or None if not found
        """
        result = self.search_work(title, composer_name)
        if result:
            return result.get("title")
        return None

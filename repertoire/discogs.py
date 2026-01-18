"""Integration with Discogs for cover art, catalog info, and EANs."""
from __future__ import annotations

import logging
import time
import re
from dataclasses import dataclass, field
from typing import Any, Optional
import requests

logger = logging.getLogger(__name__)


@dataclass
class DiscogsRelease:
    """Release information from Discogs."""
    release_id: str
    title: str
    country: Optional[str] = None
    year: Optional[str] = None
    ean: Optional[str] = None
    cover_url: Optional[str] = None
    label_name: Optional[str] = None
    catalog_number: Optional[str] = None
    artists: Optional[str] = None
    extra_artists: list[str] = field(default_factory=list)
    tracklist: list[dict[str, Optional[str]]] = field(default_factory=list)


class DiscogsClient:
    """Client for Discogs API."""
    
    API_BASE = "https://api.discogs.com"
    RELEASE_URL_RE = re.compile(
        r"(?:https?://)?(?:www\.)?discogs\.com/(?:[^/]+/)*release/(\d+)",
        re.IGNORECASE,
    )

    def __init__(
        self,
        token: str,
        user_agent: str = "Repertoire/0.1.0",
        throttle_seconds: float = 1.0,
        timeout: int = 30,
    ) -> None:
        """Initialize Discogs client.
        
        Args:
            token: Discogs API token
            user_agent: User agent string for requests
            throttle_seconds: Seconds to wait between requests (respect rate limits)
            timeout: Request timeout in seconds
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Authorization": f"Discogs token={token}",
        })
        self.timeout = timeout
        self.throttle_seconds = throttle_seconds
        self._last_request_time = 0.0

    def _throttle(self) -> None:
        """Respect rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.throttle_seconds:
            time.sleep(self.throttle_seconds - elapsed)
        self._last_request_time = time.time()

    def _get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Make a GET request to Discogs API."""
        self._throttle()
        url = f"{self.API_BASE}{endpoint}"
        try:
            response = self.session.get(url, params=params or {}, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Discogs API error on {endpoint}: {e}")
            raise

    def get_release(self, release_id: str) -> Optional[DiscogsRelease]:
        """Get release information by ID.
        
        Args:
            release_id: Discogs release ID
            
        Returns:
            DiscogsRelease with all metadata, or None if not found
        """
        try:
            details = self._get(f"/releases/{release_id}")
            return self._build_release(details)
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch release {release_id}: {e}")
            return None

    def find_release(
        self,
        catalog_number: Optional[str] = None,
        label: Optional[str] = None,
        artist: Optional[str] = None,
        query: Optional[str] = None,
    ) -> Optional[DiscogsRelease]:
        """Find a release in Discogs.
        
        Args:
            catalog_number: Catalog number (e.g., "DGG 439-947-2")
            label: Record label name
            artist: Artist/composer name
            query: Free-text search query
            
        Returns:
            Best matching DiscogsRelease, or None if not found
        """
        results = []

        # Try catalog number search first (most specific)
        if catalog_number:
            results = self._search_by_catalog(catalog_number, label, artist)

        # If no results, try query-based search
        if not results and query:
            results = self._search_by_query(query)

        if not results:
            logger.debug(f"No Discogs results for: catalog={catalog_number}, label={label}, query={query}")
            return None

        # Pick the best match
        best = self._choose_best_result(results, label, catalog_number)
        if not best:
            return None

        release_id = str(best.get("id"))
        return self.get_release(release_id)

    def _search_by_catalog(
        self,
        catalog_number: str,
        label: Optional[str],
        artist: Optional[str],
    ) -> list[dict[str, Any]]:
        """Search by catalog number."""
        # Normalize catalog number
        normalized = self._normalize_catalog(catalog_number)
        variants = [normalized]
        
        # Also try without spaces/dashes
        no_punctuation = catalog_number.replace(" ", "").replace("-", "").replace(".", "")
        if no_punctuation and no_punctuation not in variants:
            variants.append(self._normalize_catalog(no_punctuation))

        for variant in variants:
            try:
                params = {
                    "type": "release",
                    "per_page": 20,
                    "catno": variant,
                }
                if label:
                    params["label"] = label
                if artist:
                    params["artist"] = artist

                result = self._get("/database/search", params=params)
                results = result.get("results", [])
                if results:
                    return results
            except requests.RequestException as e:
                logger.debug(f"Catalog search failed for {variant}: {e}")
                continue

        return []

    def _search_by_query(self, query: str) -> list[dict[str, Any]]:
        """Search by free-text query."""
        try:
            result = self._get(
                "/database/search",
                {"type": "release", "per_page": 20, "q": query}
            )
            return result.get("results", [])
        except requests.RequestException as e:
            logger.warning(f"Query search failed for '{query}': {e}")
            return []

    @staticmethod
    def extract_release_id(url: str) -> Optional[str]:
        """Extract release ID from Discogs URL.
        
        Args:
            url: Discogs release URL
            
        Returns:
            Release ID or None if URL invalid
        """
        match = DiscogsClient.RELEASE_URL_RE.search(url)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _normalize_catalog(value: str) -> str:
        """Normalize catalog number for comparison."""
        return "".join(ch for ch in value.upper() if ch.isalnum())

    @staticmethod
    def _normalize_label(value: str) -> str:
        """Normalize label name for comparison."""
        return value.lower().strip()

    @staticmethod
    def _choose_best_result(
        results: list[dict[str, Any]],
        label: Optional[str],
        catalog_number: Optional[str],
    ) -> Optional[dict[str, Any]]:
        """Choose the best matching result from search results."""
        if not results:
            return None

        label_norm = DiscogsClient._normalize_label(label) if label else ""
        cat_norm = DiscogsClient._normalize_catalog(catalog_number) if catalog_number else ""

        def score_result(item: dict[str, Any]) -> tuple:
            """Score a result (lower is better)."""
            item_cat = DiscogsClient._normalize_catalog(item.get("catno", ""))
            item_labels = [
                DiscogsClient._normalize_label(lbl)
                for lbl in item.get("label", [])
            ]

            # Score: exact catalog match, country preference, label match
            cat_match = 0 if (cat_norm and item_cat == cat_norm) else 1
            label_match = 0 if (label_norm and label_norm in item_labels) else 1
            
            # Prefer releases from Europe/Netherlands
            country = item.get("country", "").lower()
            country_score = 0 if "netherlands" in country else (1 if "europe" in country else 2)

            return (cat_match, country_score, label_match)

        # Sort by score, return first (best)
        sorted_results = sorted(enumerate(results), key=lambda pair: (score_result(pair[1]), pair[0]))
        return sorted_results[0][1] if sorted_results else None

    @staticmethod
    def _build_release(details: dict[str, Any]) -> DiscogsRelease:
        """Build DiscogsRelease from API response."""
        return DiscogsRelease(
            release_id=str(details.get("id")),
            title=details.get("title", ""),
            country=details.get("country"),
            year=DiscogsClient._extract_year(details),
            ean=DiscogsClient._extract_ean(details),
            cover_url=DiscogsClient._extract_cover(details),
            label_name=DiscogsClient._extract_label(details)[0],
            catalog_number=DiscogsClient._extract_label(details)[1],
            artists=DiscogsClient._extract_artists(details)[0],
            extra_artists=DiscogsClient._extract_artists(details)[1],
            tracklist=DiscogsClient._extract_tracklist(details),
        )

    @staticmethod
    def _extract_year(release: dict[str, Any]) -> Optional[str]:
        """Extract year from release."""
        if release.get("released"):
            return release["released"][:4] if release["released"] else None
        year = release.get("year")
        return str(year) if year else None

    @staticmethod
    def _extract_cover(release: dict[str, Any]) -> Optional[str]:
        """Extract primary cover URL."""
        for image in release.get("images", []) or []:
            if image.get("type") == "primary" and image.get("uri"):
                return image.get("uri")
        for image in release.get("images", []) or []:
            if image.get("uri"):
                return image.get("uri")
        return None

    @staticmethod
    def _extract_ean(release: dict[str, Any]) -> Optional[str]:
        """Extract EAN/barcode."""
        identifiers = release.get("identifiers", []) or []
        for identifier in identifiers:
            value = identifier.get("value", "").strip()
            if not value:
                continue
            itype = (identifier.get("type") or "").lower()
            if itype in {"barcode", "ean", "upc"}:
                sanitized = DiscogsClient._sanitize_ean(value)
                if sanitized:
                    return sanitized

        for barcode in release.get("barcodes", []) or []:
            sanitized = DiscogsClient._sanitize_ean(barcode.strip())
            if sanitized:
                return sanitized
        
        return None

    @staticmethod
    def _sanitize_ean(value: str) -> Optional[str]:
        """Sanitize EAN/barcode (must be 12+ digits)."""
        cleaned = "".join(ch for ch in value if ch.isdigit())
        return cleaned if len(cleaned) >= 12 else None

    @staticmethod
    def _extract_label(release: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """Extract label name and catalog number."""
        labels = release.get("labels", []) or []
        if labels:
            primary = labels[0]
            return primary.get("name"), primary.get("catno")
        return None, None

    @staticmethod
    def _extract_artists(release: dict[str, Any]) -> tuple[Optional[str], list[str]]:
        """Extract primary and extra artists."""
        artists = release.get("artists", []) or []
        names = [artist.get("name") for artist in artists if artist.get("name")]
        
        extra = []
        for artist in release.get("extraartists", []) or []:
            name = artist.get("name")
            role = artist.get("role")
            if name:
                extra.append(f"{name} ({role})" if role else name)

        return ("; ".join(names) if names else None, extra)

    @staticmethod
    def _extract_tracklist(release: dict[str, Any]) -> list[dict[str, Optional[str]]]:
        """Extract tracklist."""
        tracks = []
        for track in release.get("tracklist", []) or []:
            title = track.get("title")
            if title:
                tracks.append({
                    "title": title,
                    "position": track.get("position"),
                    "duration": track.get("duration"),
                })
        return tracks

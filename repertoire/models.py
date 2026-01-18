"""Data models for Repertoire."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class RecordingType(str, Enum):
    """Types of recordings."""
    STUDIO = "studio"
    LIVE = "live"
    BROADCAST = "broadcast"
    OTHER = "other"


@dataclass
class Composer:
    """Classical composer."""
    id: Optional[int] = None
    name: str = ""
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    nationality: Optional[str] = None
    biography: Optional[str] = None
    musicbrainz_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __hash__(self) -> int:
        return hash((self.name, self.birth_year))


@dataclass
class Work:
    """Musical work by a composer."""
    id: Optional[int] = None
    composer_id: Optional[int] = None
    title: str = ""
    catalog_number: Optional[str] = None
    key: Optional[str] = None
    opus: Optional[str] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None
    musicbrainz_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __hash__(self) -> int:
        return hash((self.title, self.catalog_number))


@dataclass
class Performer:
    """Musical performer (soloist, conductor, ensemble, etc.)."""
    id: Optional[int] = None
    name: str = ""
    performer_type: str = ""  # soloist, conductor, ensemble, etc.
    instrument: Optional[str] = None
    biography: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class Label:
    """Record label."""
    id: Optional[int] = None
    name: str = ""
    country: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class Recording:
    """A recording of a musical work."""
    id: Optional[int] = None
    work_id: Optional[int] = None
    title: str = ""
    recording_type: RecordingType = RecordingType.STUDIO
    label_id: Optional[int] = None
    catalog_number: Optional[str] = None
    ean: Optional[str] = None
    release_year: Optional[int] = None
    recording_year: Optional[int] = None
    duration_seconds: Optional[int] = None
    cover_url: Optional[str] = None
    discogs_id: Optional[int] = None
    discogs_url: Optional[str] = None
    notes: Optional[str] = None
    in_library: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    # Relationships (denormalized for convenience)
    performers: list[Performer] = field(default_factory=list)
    work: Optional[Work] = None
    label: Optional[Label] = None

    def __hash__(self) -> int:
        return hash((self.title, self.catalog_number, self.release_year))


@dataclass
class ScrapePage:
    """Metadata about a scraped page from musicalifeiten.nl."""
    id: Optional[int] = None
    url: str = ""
    rubric: str = ""  # portretten, discografieen, mini_discografieen, etc.
    letter: Optional[str] = None
    page_number: Optional[int] = None
    scraped_at: datetime = field(default_factory=datetime.now)
    raw_html: Optional[str] = None
    notes: Optional[str] = None

"""SQLite database management for Repertoire."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import json

from .models import (
    Composer,
    Work,
    Performer,
    Label,
    Recording,
    RecordingType,
    ScrapePage,
)


class Database:
    """SQLite database for Repertoire."""

    def __init__(self, db_path: str | Path = "repertoire.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Composers table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS composers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                birth_year INTEGER,
                death_year INTEGER,
                nationality TEXT,
                biography TEXT,
                musicbrainz_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Works table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                composer_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                catalog_number TEXT,
                key TEXT,
                opus TEXT,
                duration_seconds INTEGER,
                notes TEXT,
                musicbrainz_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (composer_id) REFERENCES composers(id),
                UNIQUE(composer_id, title, catalog_number)
            )
            """
        )

        # Performers table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS performers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                performer_type TEXT,
                instrument TEXT,
                biography TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Labels table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                country TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Recordings table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                recording_type TEXT DEFAULT 'studio',
                label_id INTEGER,
                catalog_number TEXT,
                ean TEXT,
                release_year INTEGER,
                recording_year INTEGER,
                duration_seconds INTEGER,
                cover_url TEXT,
                discogs_id INTEGER UNIQUE,
                discogs_url TEXT,
                notes TEXT,
                in_library BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (label_id) REFERENCES labels(id),
                UNIQUE(title, catalog_number, label_id)
            )
            """
        )

        # Recording-Work junction table (supports multiple works per recording/album)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recording_works (
                recording_id INTEGER NOT NULL,
                work_id INTEGER NOT NULL,
                track_number INTEGER,
                PRIMARY KEY (recording_id, work_id),
                FOREIGN KEY (recording_id) REFERENCES recordings(id) ON DELETE CASCADE,
                FOREIGN KEY (work_id) REFERENCES works(id)
            )
            """
        )

        # Recording-Performer junction table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recording_performers (
                recording_id INTEGER NOT NULL,
                performer_id INTEGER NOT NULL,
                role TEXT,
                PRIMARY KEY (recording_id, performer_id),
                FOREIGN KEY (recording_id) REFERENCES recordings(id) ON DELETE CASCADE,
                FOREIGN KEY (performer_id) REFERENCES performers(id)
            )
            """
        )

        # Scraped pages table (for tracking progress)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraped_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                rubric TEXT,
                letter TEXT,
                page_number INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_html TEXT,
                notes TEXT
            )
            """
        )

        conn.commit()
        conn.close()

    def add_composer(self, composer: Composer) -> Composer:
        """Add or update a composer."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO composers (name, birth_year, death_year, nationality, biography)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    composer.name,
                    composer.birth_year,
                    composer.death_year,
                    composer.nationality,
                    composer.biography,
                ),
            )
            composer.id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            # Composer already exists, fetch it
            cursor.execute("SELECT id FROM composers WHERE name = ?", (composer.name,))
            row = cursor.fetchone()
            if row:
                composer.id = row[0]
        finally:
            conn.close()

        return composer

    def get_composer(self, name: str) -> Optional[Composer]:
        """Get a composer by name."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM composers WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return Composer(
                id=row["id"],
                name=row["name"],
                birth_year=row["birth_year"],
                death_year=row["death_year"],
                nationality=row["nationality"],
                biography=row["biography"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
        return None

    def add_recording(self, recording: Recording) -> Recording:
        """Add a new album/recording to the database.
        
        A recording is an album that can contain 0, 1, or more works.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Insert the recording (album)
            cursor.execute(
                """
                INSERT INTO recordings (
                    title, recording_type, label_id, catalog_number,
                    ean, release_year, recording_year, duration_seconds,
                    cover_url, discogs_id, discogs_url, notes, in_library
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recording.title,
                    recording.recording_type.value,
                    recording.label_id,
                    recording.catalog_number,
                    recording.ean,
                    recording.release_year,
                    recording.recording_year,
                    recording.duration_seconds,
                    recording.cover_url,
                    recording.discogs_id,
                    recording.discogs_url,
                    recording.notes,
                    recording.in_library,
                ),
            )
            recording.id = cursor.lastrowid

            # Add performers (album-level performers like conductor, orchestra)
            for performer in recording.performers:
                if performer.id is None:
                    performer = self.add_performer(performer)
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO recording_performers
                    (recording_id, performer_id)
                    VALUES (?, ?)
                    """,
                    (recording.id, performer.id),
                )

            # Add works (compositions on this album)
            for track_num, work in enumerate(recording.works, 1):
                if work.id is None:
                    work = self.add_work(work)
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO recording_works
                    (recording_id, work_id, track_number)
                    VALUES (?, ?, ?)
                    """,
                    (recording.id, work.id, track_num),
                )

            conn.commit()
        except sqlite3.IntegrityError as e:
            conn.close()
            raise ValueError(f"Database integrity error: {e}")
        finally:
            conn.close()

        return recording

    def add_work(self, work: Work) -> Work:
        """Add or get a work (composition)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO works (composer_id, title, catalog_number, key, opus, duration_seconds, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    work.composer_id,
                    work.title,
                    work.catalog_number,
                    work.key,
                    work.opus,
                    work.duration_seconds,
                    work.notes,
                ),
            )
            work.id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            # Work already exists, fetch it
            cursor.execute(
                "SELECT id FROM works WHERE composer_id = ? AND title = ? AND catalog_number = ?",
                (work.composer_id, work.title, work.catalog_number),
            )
            row = cursor.fetchone()
            if row:
                work.id = row[0]
        finally:
            conn.close()

        return work

    def add_performer(self, performer: Performer) -> Performer:
        """Add or update a performer."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO performers (name, performer_type, instrument, biography)
                VALUES (?, ?, ?, ?)
                """,
                (
                    performer.name,
                    performer.performer_type,
                    performer.instrument,
                    performer.biography,
                ),
            )
            performer.id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            # Performer already exists
            cursor.execute("SELECT id FROM performers WHERE name = ?", (performer.name,))
            row = cursor.fetchone()
            if row:
                performer.id = row[0]
        finally:
            conn.close()

        return performer

    def get_recordings(
        self,
        composer_name: Optional[str] = None,
        work_title: Optional[str] = None,
        label_name: Optional[str] = None,
        in_library: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Recording]:
        """Query recordings with filters."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM recordings WHERE 1=1"
        params = []

        if composer_name:
            query += """
                AND id IN (
                    SELECT rw.recording_id FROM recording_works rw
                    JOIN works w ON rw.work_id = w.id
                    JOIN composers c ON w.composer_id = c.id
                    WHERE c.name LIKE ?
                )
            """
            params.append(f"%{composer_name}%")

        if work_title:
            query += """
                AND id IN (
                    SELECT rw.recording_id FROM recording_works rw
                    JOIN works w ON rw.work_id = w.id
                    WHERE w.title LIKE ?
                )
            """
            params.append(f"%{work_title}%")

        if label_name:
            query += """
                AND label_id IN (
                    SELECT id FROM labels WHERE name LIKE ?
                )
            """
            params.append(f"%{label_name}%")

        if in_library is not None:
            query += " AND in_library = ?"
            params.append(int(in_library))

        query += " LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        recordings = []
        for row in rows:
            recording = Recording(
                id=row["id"],
                title=row["title"],
                recording_type=RecordingType(row["recording_type"]),
                label_id=row["label_id"],
                catalog_number=row["catalog_number"],
                ean=row["ean"],
                release_year=row["release_year"],
                recording_year=row["recording_year"],
                duration_seconds=row["duration_seconds"],
                cover_url=row["cover_url"],
                discogs_id=row["discogs_id"],
                discogs_url=row["discogs_url"],
                notes=row["notes"],
                in_library=bool(row["in_library"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

            # Fetch performers for this recording
            cursor.execute(
                """
                SELECT p.* FROM performers p
                JOIN recording_performers rp ON rp.performer_id = p.id
                WHERE rp.recording_id = ?
                """,
                (recording.id,),
            )
            for perf_row in cursor.fetchall():
                recording.performers.append(
                    Performer(
                        id=perf_row["id"],
                        name=perf_row["name"],
                        performer_type=perf_row["performer_type"],
                        instrument=perf_row["instrument"],
                        biography=perf_row["biography"],
                    )
                )

            # Fetch works for this recording
            cursor.execute(
                """
                SELECT w.* FROM works w
                JOIN recording_works rw ON rw.work_id = w.id
                WHERE rw.recording_id = ?
                ORDER BY rw.track_number
                """,
                (recording.id,),
            )
            for work_row in cursor.fetchall():
                recording.works.append(
                    Work(
                        id=work_row["id"],
                        composer_id=work_row["composer_id"],
                        title=work_row["title"],
                        catalog_number=work_row["catalog_number"],
                        key=work_row["key"],
                        opus=work_row["opus"],
                        duration_seconds=work_row["duration_seconds"],
                        notes=work_row["notes"],
                        musicbrainz_id=work_row.get("musicbrainz_id"),
                    )
                )

            recordings.append(recording)

        conn.close()
        return recordings

    def save_scraped_page(self, page: ScrapePage) -> ScrapePage:
        """Save a scraped page record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO scraped_pages (url, rubric, letter, page_number, raw_html, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (page.url, page.rubric, page.letter, page.page_number, page.raw_html, page.notes),
            )
            page.id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        return page

    def page_already_scraped(self, url: str) -> bool:
        """Check if a page has already been scraped."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM scraped_pages WHERE url = ?", (url,))
        result = cursor.fetchone() is not None
        conn.close()
        return result

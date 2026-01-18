"""Flask web application for Repertoire."""
from __future__ import annotations

from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from repertoire.database import Database
from repertoire.models import Recording, RecordingType, Composer, Work, Performer, Label
from repertoire.discogs import DiscogsClient
from repertoire.musicbrainz import MusicBrainzIntegration
import os


def create_app(db_path: str | Path = "repertoire.db") -> Flask:
    """Create and configure Flask app."""
    app = Flask(
        __name__,
        template_folder=Path(__file__).parent / "templates",
        static_folder=Path(__file__).parent / "static",
    )
    
    CORS(app)
    db = Database(db_path)
    
    # Initialize optional integrations
    discogs_token = os.getenv("DISCOGS_TOKEN")
    discogs_client = DiscogsClient(token=discogs_token) if discogs_token else None
    
    mb_client = MusicBrainzIntegration()

    @app.route("/")
    def index():
        """Serve main page."""
        return render_template("index.html")

    @app.route("/add")
    def add_recording_page():
        """Serve add recording page."""
        return render_template("add-recording.html")

    @app.route("/api/recordings", methods=["GET"])
    def api_recordings():
        """Get recordings with optional filters."""
        composer = request.args.get("composer")
        work = request.args.get("work")
        label = request.args.get("label")
        in_library = request.args.get("library")
        limit = int(request.args.get("limit", 100))

        in_lib = None
        if in_library == "true":
            in_lib = True
        elif in_library == "false":
            in_lib = False

        recordings = db.get_recordings(
            composer_name=composer,
            work_title=work,
            label_name=label,
            in_library=in_lib,
            limit=limit,
        )

        return jsonify([
            {
                "id": r.id,
                "title": r.title,
                "catalog_number": r.catalog_number,
                "release_year": r.release_year,
                "recording_type": r.recording_type.value,
                "in_library": r.in_library,
                "cover_url": r.cover_url,
            }
            for r in recordings
        ])

    @app.route("/api/recordings", methods=["POST"])
    def api_add_recordings():
        """Add new recordings from Raycast extension or manual entry.
        
        Expected JSON:
        {
            "recordings": [
                {
                    "composer": "Ludwig van Beethoven",
                    "work": "Symphony No. 5",
                    "performers": ["Berlin Philharmonic"],
                    "label": "Deutsche Grammophon",
                    "catalogNumber": "439-947-2",
                    "releaseYear": 1992,
                    "notes": "..."
                }
            ]
        }
        """
        try:
            data = request.get_json()
            if not data or "recordings" not in data:
                return jsonify({"error": "Missing 'recordings' field"}), 400

            recordings_data = data.get("recordings", [])
            added_count = 0

            for rec_data in recordings_data:
                # Get or create composer (with MusicBrainz standardization)
                composer_name = rec_data.get("composer", "Unknown")
                
                # Try to standardize with MusicBrainz
                standardized_name = mb_client.standardize_composer_name(composer_name)
                if standardized_name:
                    composer_name = standardized_name

                composer = db.get_composer(composer_name)
                if not composer:
                    composer = Composer(name=composer_name)
                    composer = db.add_composer(composer)

                # Get or create label
                label = None
                if rec_data.get("label"):
                    label = Label(name=rec_data["label"])
                    label = db.add_performer(label)  # Reuse performer method for labels

                # Create recording
                recording = Recording(
                    title=rec_data.get("work", "Unknown Work"),
                    catalog_number=rec_data.get("catalogNumber"),
                    release_year=rec_data.get("releaseYear"),
                    label_id=label.id if label else None,
                    notes=rec_data.get("notes"),
                    recording_type=RecordingType.STUDIO,
                    cover_url=rec_data.get("coverUrl"),
                    ean=rec_data.get("ean"),
                )

                # Add performers
                for performer_name in rec_data.get("performers", []):
                    performer = Performer(name=performer_name)
                    performer = db.add_performer(performer)
                    recording.performers.append(performer)

                # Save to database
                db.add_recording(recording)
                added_count += 1

            return jsonify({
                "success": True,
                "message": f"Added {added_count} recording(s)",
                "count": added_count,
            }), 201

        except Exception as e:
            return jsonify({
                "error": str(e),
                "message": "Error adding recordings"
            }), 500

    @app.route("/api/discogs/lookup", methods=["POST"])
    def api_discogs_lookup():
        """Lookup and enrich recording data from Discogs URL.
        
        Expected JSON:
        {
            "url": "https://www.discogs.com/release/123456"
        }
        """
        if not discogs_client:
            return jsonify({
                "error": "Discogs token not configured",
                "message": "Set DISCOGS_TOKEN environment variable"
            }), 400

        try:
            data = request.get_json()
            url = data.get("url", "").strip()

            if not url:
                return jsonify({"error": "Missing URL"}), 400

            # Extract release ID from URL
            release_id = DiscogsClient.extract_release_id(url)
            if not release_id:
                return jsonify({"error": "Invalid Discogs URL"}), 400

            # Fetch release data
            release = discogs_client.get_release(release_id)
            if not release:
                return jsonify({"error": "Release not found on Discogs"}), 404

            # Return enriched data
            return jsonify({
                "success": True,
                "release": {
                    "title": release.title,
                    "year": release.year,
                    "label": release.label_name,
                    "catalogNumber": release.catalog_number,
                    "ean": release.ean,
                    "coverUrl": release.cover_url,
                    "country": release.country,
                    "discogs_id": release.release_id,
                }
            }), 200

        except Exception as e:
            return jsonify({
                "error": str(e),
                "message": "Error looking up Discogs"
            }), 500

    @app.route("/api/discogs/search", methods=["POST"])
    def api_discogs_search():
        """Search Discogs for a recording.
        
        Expected JSON:
        {
            "catalog_number": "439-947-2",
            "label": "Deutsche Grammophon",
            "artist": "Ludwig van Beethoven"
        }
        """
        if not discogs_client:
            return jsonify({
                "error": "Discogs token not configured",
                "message": "Set DISCOGS_TOKEN environment variable"
            }), 400

        try:
            data = request.get_json()
            release = discogs_client.find_release(
                catalog_number=data.get("catalog_number"),
                label=data.get("label"),
                artist=data.get("artist"),
                query=data.get("query")
            )

            if not release:
                return jsonify({"error": "No matches found"}), 404

            return jsonify({
                "success": True,
                "release": {
                    "title": release.title,
                    "year": release.year,
                    "label": release.label_name,
                    "catalogNumber": release.catalog_number,
                    "ean": release.ean,
                    "coverUrl": release.cover_url,
                    "country": release.country,
                    "discogs_id": release.release_id,
                }
            }), 200

        except Exception as e:
            return jsonify({
                "error": str(e),
                "message": "Error searching Discogs"
            }), 500

    @app.route("/api/stats")
    def api_stats():
        """Get database statistics."""
        # Get basic counts
        recordings = db.get_recordings(limit=1000000)
        
        return jsonify({
            "total_recordings": len(recordings),
            "in_library": sum(1 for r in recordings if r.in_library),
            "unique_composers": len(set(r.work.composer_id for r in recordings if r.work)),
        })

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

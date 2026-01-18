"""Flask web application for Repertoire."""
from __future__ import annotations

from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from repertoire.database import Database
from repertoire.models import Recording, RecordingType, Composer, Work, Performer, Label


def create_app(db_path: str | Path = "repertoire.db") -> Flask:
    """Create and configure Flask app."""
    app = Flask(
        __name__,
        template_folder=Path(__file__).parent / "templates",
        static_folder=Path(__file__).parent / "static",
    )
    
    CORS(app)
    db = Database(db_path)

    @app.route("/")
    def index():
        """Serve main page."""
        return render_template("index.html")

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
        """Add new recordings from Raycast extension or API.
        
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
                # Get or create composer
                composer_name = rec_data.get("composer", "Unknown")
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

"""Flask web application for Repertoire."""
from __future__ import annotations

from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from repertoire.database import Database


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

    @app.route("/api/recordings")
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

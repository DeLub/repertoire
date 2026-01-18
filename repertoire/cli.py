"""Command-line interface for Repertoire."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from .database import Database
from .scraper import MusicaliefeitenScraper
from .models import Recording, Composer, Work, Performer, Label, RecordingType


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Repertoire - Classical music manager",
        prog="repertoire",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape musicalifeiten.nl")
    scrape_parser.add_argument(
        "--db",
        default="repertoire.db",
        help="Path to SQLite database (default: repertoire.db)",
    )
    scrape_parser.add_argument(
        "--rubric",
        default="portretten",
        choices=["portretten", "discografieen", "mini_discografieen", "vergelijkingen"],
        help="Which rubric to scrape",
    )
    scrape_parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Number of random pages to scrape",
    )
    scrape_parser.add_argument(
        "--throttle",
        type=float,
        default=2.0,
        help="Seconds to wait between requests",
    )

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument(
        "--db",
        default="repertoire.db",
        help="Path to SQLite database",
    )
    query_parser.add_argument(
        "--composer",
        help="Filter by composer name",
    )
    query_parser.add_argument(
        "--work",
        help="Filter by work title",
    )
    query_parser.add_argument(
        "--label",
        help="Filter by label name",
    )
    query_parser.add_argument(
        "--library",
        choices=["yes", "no"],
        help="Filter by library status",
    )
    query_parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of results",
    )

    # Server command
    server_parser = subparsers.add_parser("server", help="Start web server")
    server_parser.add_argument(
        "--db",
        default="repertoire.db",
        help="Path to SQLite database",
    )
    server_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host",
    )
    server_parser.add_argument(
        "--port",
        type=int,
        default=5173,
        help="Server port (default: 5173)",
    )
    server_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    return parser


def handle_scrape(args) -> None:
    """Handle scrape command."""
    db = Database(args.db)
    scraper = MusicaliefeitenScraper(throttle=args.throttle)

    print(f"Scraping {args.pages} page(s) from rubric: {args.rubric}")

    for i in range(args.pages):
        print(f"\nPage {i+1}/{args.pages}")
        html = scraper.scrape_random_page(rubric=args.rubric)
        
        if html:
            paragraphs = scraper.extract_content(html)
            print(f"Extracted {len(paragraphs)} paragraphs from page")
            
            # Print first few paragraphs as preview
            for j, para in enumerate(paragraphs[:3]):
                preview = para[:100] + "..." if len(para) > 100 else para
                print(f"  [{j+1}] {preview}")
        else:
            print("Failed to scrape page")


def handle_query(args) -> None:
    """Handle query command."""
    db = Database(args.db)
    
    in_library = None
    if args.library == "yes":
        in_library = True
    elif args.library == "no":
        in_library = False

    recordings = db.get_recordings(
        composer_name=args.composer,
        work_title=args.work,
        label_name=args.label,
        in_library=in_library,
        limit=args.limit,
    )

    print(f"Found {len(recordings)} recording(s):\n")
    for rec in recordings:
        print(f"Title: {rec.title}")
        if rec.catalog_number:
            print(f"Catalog: {rec.catalog_number}")
        if rec.release_year:
            print(f"Year: {rec.release_year}")
        print()


def handle_server(args) -> None:
    """Handle server command."""
    # Import Flask here to avoid dependency if not using server
    try:
        from webui.app import create_app
    except ImportError:
        print("Error: Flask is required to run the server.")
        print("Install it with: pip install flask flask-cors")
        return

    app = create_app(db_path=args.db)
    print(f"Starting Repertoire server on {args.host}:{args.port}")
    print(f"Open http://{args.host}:{args.port} in your browser")
    app.run(host=args.host, port=args.port, debug=args.debug)


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "scrape":
        handle_scrape(args)
    elif args.command == "query":
        handle_query(args)
    elif args.command == "server":
        handle_server(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

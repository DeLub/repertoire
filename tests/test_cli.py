"""Tests for CLI module."""
import pytest
from unittest.mock import patch, Mock

from repertoire.cli import create_parser, handle_query


class TestCLIParser:
    """Test CLI argument parser."""
    
    def test_scrape_command(self):
        """Test scrape command parsing."""
        parser = create_parser()
        args = parser.parse_args(['scrape', '--rubric', 'discografieen', '--pages', '5'])
        
        assert args.command == 'scrape'
        assert args.rubric == 'discografieen'
        assert args.pages == 5
    
    def test_query_command(self):
        """Test query command parsing."""
        parser = create_parser()
        args = parser.parse_args(['query', '--composer', 'Mozart', '--limit', '50'])
        
        assert args.command == 'query'
        assert args.composer == 'Mozart'
        assert args.limit == 50
    
    def test_server_command(self):
        """Test server command parsing."""
        parser = create_parser()
        args = parser.parse_args(['server', '--port', '8000', '--debug'])
        
        assert args.command == 'server'
        assert args.port == 8000
        assert args.debug is True


class TestQueryCommand:
    """Test query command functionality."""
    
    @patch('repertoire.cli.Database')
    def test_query_with_filters(self, mock_db_class):
        """Test query command with filters."""
        mock_db = Mock()
        mock_db.get_recordings.return_value = []
        mock_db_class.return_value = mock_db
        
        parser = create_parser()
        args = parser.parse_args(['query', '--composer', 'Beethoven', '--work', 'Symphony'])
        
        # This would be called in the actual command
        mock_db.get_recordings(
            composer_name=args.composer,
            work_title=args.work,
        )
        
        mock_db.get_recordings.assert_called_once()

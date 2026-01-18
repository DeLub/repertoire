"""Integration with Raycast AI for metadata enrichment."""
from __future__ import annotations

import os
from typing import Optional, Any
import json


class RaycastAIIntegration:
    """Interface for Raycast AI integration."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Raycast AI integration.
        
        Args:
            api_key: Raycast AI API key. If not provided, will attempt to read from environment.
        """
        self.api_key = api_key or os.getenv("RAYCAST_AI_KEY")
        if not self.api_key:
            raise ValueError(
                "RAYCAST_AI_KEY environment variable not set. "
                "Set it or pass api_key parameter."
            )

    def enrich_recording_metadata(self, text: str) -> dict[str, Any]:
        """Use Raycast AI to extract structured metadata from free text.
        
        This will be called from the Raycast extension when scraping a page.
        The extension has access to Raycast AI, so the actual enrichment
        happens there and returns the result to the backend.
        
        Args:
            text: Unstructured text about a recording
            
        Returns:
            Dictionary with structured metadata (composer, work, performers, label, etc.)
        """
        # This is a placeholder. In production, the Raycast extension will:
        # 1. Call Raycast AI directly
        # 2. Send the enriched data to the backend API
        # 3. The backend stores it
        
        return {
            "composer": None,
            "work": None,
            "performers": [],
            "label": None,
            "catalog_number": None,
            "recording_year": None,
            "notes": text,
        }

    def summarize_text(self, text: str) -> str:
        """Use Raycast AI to summarize text.
        
        Args:
            text: Text to summarize
            
        Returns:
            Summarized text
        """
        # Placeholder - actual implementation will be in Raycast extension
        return text[:200] + "..." if len(text) > 200 else text

    def extract_composers(self, text: str) -> list[str]:
        """Extract composer names from text using Raycast AI.
        
        Args:
            text: Text containing composer information
            
        Returns:
            List of composer names
        """
        # Placeholder - will be enhanced with actual AI
        # For now, return empty list
        return []

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AnkiConnect API wrapper for Anki integration."""

import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
import requests

from config import AppConfig

logger = logging.getLogger(__name__)


class AnkiConnectError(Exception):
    """Exception raised when AnkiConnect API call fails."""
    pass


class AnkiConnector:
    """Wrapper for AnkiConnect API."""

    def __init__(self, config: AppConfig):
        """Initialize AnkiConnect connector.

        Args:
            config: Application configuration
        """
        self.config = config
        self.base_url = f"http://{config.anki.url.split('://')[-1]}:{config.anki.port}"
        self.timeout = config.anki.timeout

    def test_connection(self) -> bool:
        """Test connection to AnkiConnect server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self._request("version")
            logger.info(f"Connected to AnkiConnect API version: {response}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to AnkiConnect: {e}")
            return False

    def create_deck(self, deck_name: str) -> bool:
        """Create a deck (or get existing deck if it already exists).

        Args:
            deck_name: Hierarchical deck name (e.g., "Japanese::NguPhap::Bai-1")

        Returns:
            True if deck created/exists, False otherwise
        """
        try:
            result = self._request("createDeck", {"deck": deck_name})
            logger.info(f"Deck created/fetched: {deck_name} (ID: {result})")
            return True
        except Exception as e:
            logger.error(f"Failed to create deck '{deck_name}': {e}")
            return False

    def add_card(
        self,
        deck_name: str,
        front: str,
        back: str,
        audio_field: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[int]:
        """Add a single card to a deck.

        Args:
            deck_name: Deck name
            front: Front field (Japanese pattern)
            back: Back field (Vietnamese meaning + explanation)
            audio_field: Optional audio HTML tag (e.g., "[sound:file.mp3]")
            tags: Optional list of tags

        Returns:
            Card ID if successful, None otherwise
        """
        if tags is None:
            tags = []

        # Combine back field with audio if provided
        back_content = back
        if audio_field:
            back_content = f"{back}<br/><br/>{audio_field}"

        note = {
            "deckName": deck_name,
            "modelName": self.config.card.note_type,
            "fields": {
                self.config.card.fields["front"]: front,
                self.config.card.fields["back"]: back_content,
            },
            "tags": tags,
        }

        try:
            card_id = self._request("addNote", {"note": note})
            logger.debug(f"Card added: {front} -> {back[:50]}...")
            return card_id
        except AnkiConnectError as e:
            if "duplicateCheck" in str(e) or "already exists" in str(e):
                logger.debug(f"Card already exists: {front}")
                return None
            logger.error(f"Failed to add card '{front}': {e}")
            return None

    def add_cards_batch(
        self,
        deck_name: str,
        cards: List[Dict[str, Any]],
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add multiple cards to a deck in batches.

        Args:
            deck_name: Deck name
            cards: List of card dicts with keys: front, back, audio (optional), tags (optional)
            batch_size: Cards per batch (default from config)

        Returns:
            Summary dict with counts: added, skipped, failed, total
        """
        if batch_size is None:
            batch_size = self.config.import_.batch_size

        summary = {"added": 0, "skipped": 0, "failed": 0, "total": len(cards)}

        for i, card in enumerate(cards):
            card_id = self.add_card(
                deck_name,
                card["front"],
                card["back"],
                card.get("audio"),
                card.get("tags", [])
            )

            if card_id is not None:
                summary["added"] += 1
            else:
                # Check if it was a duplicate (None return with no exception)
                summary["skipped"] += 1

            # Log progress
            if (i + 1) % batch_size == 0:
                logger.info(
                    f"Processed {i + 1}/{len(cards)} cards "
                    f"(added: {summary['added']}, skipped: {summary['skipped']})"
                )

        logger.info(
            f"Batch import complete: {summary['added']} added, "
            f"{summary['skipped']} skipped, {summary['failed']} failed"
        )
        return summary

    def find_cards(self, query: str) -> List[int]:
        """Find cards by query.

        Args:
            query: Anki search query (e.g., "deck:Japanese")

        Returns:
            List of card IDs
        """
        try:
            return self._request("findCards", {"query": query})
        except Exception as e:
            logger.error(f"Failed to find cards with query '{query}': {e}")
            return []

    def get_note(self, card_id: int) -> Optional[int]:
        """Get note ID from card ID.

        Args:
            card_id: Card ID

        Returns:
            Note ID if successful, None otherwise
        """
        try:
            # Use cardsInfo to get note ID
            logger.debug(f"Getting note for card {card_id} using cardsInfo")
            cards_info = self._request("cardsInfo", {"cards": [card_id]})
            logger.debug(f"cardsInfo response: {cards_info}")
            if cards_info and len(cards_info) > 0:
                # Note: cardsInfo returns 'note' field, not 'noteId'
                note_id = cards_info[0].get("note")
                logger.debug(f"Got note ID: {note_id}")
                return note_id
            logger.debug(f"cardsInfo returned empty or invalid response: {cards_info}")
            return None
        except Exception as e:
            logger.error(f"Failed to get note for card {card_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def update_note(self, card_id: int, back_content: str, audio_file: Optional[str] = None) -> bool:
        """Update a note with new back field content and optional audio.

        Args:
            card_id: Card ID
            back_content: New back field content
            audio_file: Optional audio filename

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get note ID from card ID
            note_id = self.get_note(card_id)
            if not note_id:
                logger.error(f"Could not get note ID for card {card_id}")
                return False

            logger.debug(f"Got note ID {note_id} for card {card_id}")

            # Add audio to back content if provided
            back_with_audio = back_content
            if audio_file:
                back_with_audio = f"{back_content}<br/><br/>[sound:{audio_file}]"

            # Update note fields
            fields = {
                self.config.card.fields["back"]: back_with_audio
            }

            logger.debug(f"Calling updateNote with note_id={note_id}, fields={fields}")
            
            result = self._request(
                "updateNote",
                {
                    "note": {
                        "id": note_id,
                        "fields": fields
                    }
                }
            )

            logger.debug(f"Note {note_id} updated with audio: {audio_file}, result={result}")
            return result is None  # updateNote returns None on success

        except Exception as e:
            logger.error(f"Failed to update note for card {card_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def add_audio_to_deck(self, deck_name: str, audio_files: Dict[str, Path]) -> Dict[str, bool]:
        """Add audio files to AnkiConnect media folder.

        Args:
            deck_name: Deck name (for reference)
            audio_files: Dict mapping audio name to file path

        Returns:
            Dict mapping audio name to success status
        """
        results = {}

        for audio_name, audio_path in audio_files.items():
            try:
                if not audio_path.exists():
                    logger.warning(f"Audio file not found: {audio_path}")
                    results[audio_name] = False
                    continue

                with open(audio_path, "rb") as f:
                    audio_data = f.read()

                result = self._request(
                    "storeMediaFile",
                    {
                        "filename": audio_name,
                        "data": audio_data.hex()
                    }
                )
                results[audio_name] = result is not None
                logger.debug(f"Audio file stored: {audio_name}")
            except Exception as e:
                logger.error(f"Failed to store audio file '{audio_name}': {e}")
                results[audio_name] = False

        return results

    def _request(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a request to AnkiConnect API.

        Args:
            action: API action to call
            params: Optional parameters for the action

        Returns:
            Response from API

        Raises:
            AnkiConnectError: If API call fails
        """
        if params is None:
            params = {}

        request_body = {
            "action": action,
            "version": 6,
            "params": params,
        }

        try:
            response = requests.post(
                f"{self.base_url}",
                json=request_body,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()

            if result.get("error") is not None:
                raise AnkiConnectError(result["error"])

            return result.get("result")

        except requests.exceptions.RequestException as e:
            raise AnkiConnectError(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            raise AnkiConnectError(f"Invalid JSON response: {e}")

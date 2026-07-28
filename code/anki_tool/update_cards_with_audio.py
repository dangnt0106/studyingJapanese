#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update existing Anki cards with audio files."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict

from config import AppConfig, load_config, get_default_config
from csv_processor import CSVProcessor, GrammarCard
from audio_matcher import AudioMatcher
from anki_connector import AnkiConnector
from anki_media_manager import copy_audio_files_for_csv

logger = logging.getLogger(__name__)


def update_cards_with_audio(
    anki_connector: AnkiConnector,
    cards: List[GrammarCard],
    deck_name: str
) -> Dict[str, bool]:
    """Update existing cards in Anki with audio.

    Args:
        anki_connector: AnkiConnector instance
        cards: List of grammar cards with audio info
        deck_name: Anki deck name

    Returns:
        Dict mapping pattern -> success status
    """
    results = {}

    for i, card in enumerate(cards, 1):
        if not card.audio_file:
            logger.warning(f"[{i}/{len(cards)}] No audio for: {card.pattern}")
            results[card.pattern] = False
            continue

        # Find card in Anki by front content (exact match)
        query = f'"{card.pattern}"'
        logger.debug(f"[{i}/{len(cards)}] Searching for: {query}")
        found_cards = anki_connector.find_cards(query)

        if not found_cards:
            logger.warning(f"[{i}/{len(cards)}] Card not found in Anki: {card.pattern}")
            results[card.pattern] = False
            continue

        logger.debug(f"[{i}/{len(cards)}] Found card IDs: {found_cards}")

        # Get the back content (without audio)
        back_content = card.to_dict()['meaning'] + '\n' + card.to_dict()['explanation']

        card_id = found_cards[0]

        try:
            logger.debug(f"[{i}/{len(cards)}] Updating card {card_id} with audio: {card.audio_file}")
            # Update note with audio
            success = anki_connector.update_note(card_id, back_content, card.audio_file)
            if success:
                logger.info(f"[{i}/{len(cards)}] [OK] Updated with audio: {card.pattern} ({card.audio_file})")
                results[card.pattern] = True
            else:
                logger.error(f"[{i}/{len(cards)}] Failed to update (update_note returned False): {card.pattern}")
                results[card.pattern] = False
        except Exception as e:
            logger.error(f"[{i}/{len(cards)}] Exception updating: {card.pattern} - {e}")
            import traceback
            traceback.print_exc()
            results[card.pattern] = False

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update existing Anki cards with audio files"
    )

    parser.add_argument(
        "--csv",
        type=Path,
        required=True,
        help="Grammar CSV file"
    )

    parser.add_argument(
        "--deck",
        type=str,
        required=False,
        help="Anki deck name (default: auto-extracted from CSV filename)"
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "config.yml",
        help="Path to configuration file"
    )

    args = parser.parse_args()

    # Setup logging
    # Configure logging with UTF-8 encoding
    import io
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)-8s %(name)s - %(message)s',
        handlers=[logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'))]
    )

    logger = logging.getLogger(__name__)

    # Load configuration
    try:
        if args.config.exists():
            config = load_config(args.config)
        else:
            logger.warning("Config file not found, using defaults")
            config = get_default_config()
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)

    # Resolve CSV path
    csv_path = args.csv
    if not csv_path.is_absolute():
        csv_dir = config.paths.get_grammar_csv_path(Path(__file__).parent)
        csv_path = csv_dir / csv_path

    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    # Setup Anki connection
    try:
        anki_connector = AnkiConnector(config)
        if not anki_connector.test_connection():
            logger.error("Failed to connect to Anki. Make sure Anki is running with AnkiConnect add-on.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error connecting to Anki: {e}")
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("Update Anki Cards with Audio")
    logger.info("=" * 70)
    logger.info(f"CSV file: {csv_path}")

    # Read CSV
    csv_processor = CSVProcessor(config)
    cards = csv_processor.read_grammar_csv(csv_path)
    logger.info(f"Loaded {len(cards)} cards from CSV")

    # Match audio files
    audio_matcher = AudioMatcher(config)
    audio_base_dir = config.paths.get_audio_base_path(Path(__file__).parent)

    for card in cards:
        audio_file, score = audio_matcher.find_audio_for_pattern(
            card.pattern,
            csv_path.stem,
            audio_base_dir
        )
        card.audio_file = audio_file
        card.audio_confidence = score

    # Get deck name
    if args.deck:
        deck_name = args.deck
    else:
        # Auto-extract from CSV filename
        csv_filename = csv_path.stem
        deck_template = config.deck.template
        deck_name = deck_template.format(lesson_name=csv_filename)

    logger.info(f"Deck: {deck_name}")
    logger.info(f"Audio directory: {audio_base_dir / csv_path.stem}")

    # Copy audio files to Anki media folder
    logger.info(f"\nCopying audio files to Anki media folder...")
    copy_success = copy_audio_files_for_csv(csv_path.name, audio_base_dir)
    if not copy_success:
        logger.warning("Could not copy audio files to Anki - they may not be accessible in Anki")

    # Update cards
    results = update_cards_with_audio(anki_connector, cards, deck_name)

    # Summary
    success_count = sum(1 for result in results.values() if result)
    logger.info(f"\n[OK] Update complete: {success_count}/{len(cards)} cards updated with audio")

    if success_count == 0:
        logger.error("No cards were updated. Check if cards exist in Anki and audio files are present.")
        sys.exit(1)


if __name__ == "__main__":
    main()

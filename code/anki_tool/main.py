#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Anki Integration Tool - Main CLI entry point."""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from config import AppConfig, load_config, get_default_config
from anki_connector import AnkiConnector, AnkiConnectError
from csv_processor import CSVProcessor
from audio_matcher import AudioMatcher


def setup_logging(config: AppConfig) -> None:
    """Setup logging based on configuration.

    Args:
        config: Application configuration
    """
    log_level = getattr(logging, config.logging.level, logging.INFO)

    # Create logs directory
    logs_dir = Path(config.logging.filename).parent
    if logs_dir == Path(config.logging.filename):
        logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Generate log filename with date
    log_filename = config.logging.filename.replace("{date}", datetime.now().strftime("%Y%m%d"))
    log_path = logs_dir / log_filename

    # Configure logging
    log_format = (
        "[%(asctime)s] %(levelname)-8s %(name)s - %(message)s"
        if config.logging.format == "detailed"
        else "%(levelname)s: %(message)s"
    )

    handlers = [logging.StreamHandler(sys.stdout)]
    if config.logging.file_logging:
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Level: {config.logging.level}")
    if config.logging.file_logging:
        logger.info(f"Log file: {log_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Anki Integration Tool - Import Japanese grammar CSV to Anki via AnkiConnect"
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "config.yml",
        help="Path to configuration file (default: config.yml in tool directory)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Test connection command
    test_parser = subparsers.add_parser("test", help="Test connection to AnkiConnect")

    # Generate intermediate CSV command
    csv_parser = subparsers.add_parser(
        "csv",
        help="Generate intermediate CSV from grammar CSV (for review before import)"
    )
    csv_parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input grammar CSV file"
    )
    csv_parser.add_argument(
        "--output",
        type=Path,
        required=False,
        help="Output intermediate CSV file (default: <input>_intermediate.csv)"
    )

    # Import command
    import_parser = subparsers.add_parser(
        "import",
        help="Import grammar CSV to Anki"
    )
    import_parser.add_argument(
        "--csv",
        type=Path,
        required=True,
        help="Input grammar CSV file"
    )
    import_parser.add_argument(
        "--deck",
        type=str,
        required=False,
        help="Deck name (default: extracted from CSV filename)"
    )
    import_parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation before import"
    )
    import_parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Skip audio matching (import without audio)"
    )

    # Parse arguments
    args = parser.parse_args()

    # Load configuration
    try:
        if args.config.exists():
            config = load_config(args.config)
        else:
            logger_temp = logging.getLogger(__name__)
            logger_temp.warning(f"Config file not found, using defaults: {args.config}")
            config = get_default_config()
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)

    # Resolve relative paths
    tool_dir = Path(__file__).parent
    csv_dir = config.paths.get_grammar_csv_path(tool_dir)
    audio_dir = config.paths.get_audio_base_path(tool_dir)
    output_dir = config.paths.get_output_path(tool_dir)

    logger.info(f"Tool directory: {tool_dir}")
    logger.info(f"CSV directory: {csv_dir}")
    logger.info(f"Audio directory: {audio_dir}")

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "test":
            handle_test_command(config, logger)

        elif args.command == "csv":
            handle_csv_command(args, config, csv_dir, audio_dir, output_dir, logger)

        elif args.command == "import":
            handle_import_command(args, config, csv_dir, audio_dir, logger)

    except Exception as e:
        logger.exception(f"Error executing command: {e}")
        sys.exit(1)


def handle_test_command(config: AppConfig, logger: logging.Logger) -> None:
    """Handle 'test' command.

    Args:
        config: Application configuration
        logger: Logger instance
    """
    logger.info("Testing AnkiConnect connection...")
    connector = AnkiConnector(config)

    if connector.test_connection():
        logger.info("✓ Connection test PASSED")
        sys.exit(0)
    else:
        logger.error("✗ Connection test FAILED")
        sys.exit(1)


def handle_csv_command(
    args,
    config: AppConfig,
    csv_dir: Path,
    audio_dir: Path,
    output_dir: Path,
    logger: logging.Logger
) -> None:
    """Handle 'csv' command to generate intermediate CSV.

    Args:
        args: Parsed arguments
        config: Application configuration
        csv_dir: CSV directory path
        audio_dir: Audio base directory path
        output_dir: Output directory path
        logger: Logger instance
    """
    csv_path = args.input
    if not csv_path.is_absolute():
        csv_path = csv_dir / csv_path

    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    logger.info(f"Processing CSV: {csv_path}")

    # Read CSV
    csv_processor = CSVProcessor(config)
    cards = csv_processor.read_grammar_csv(csv_path)

    # Match audio
    audio_matcher = AudioMatcher(config)
    csv_name = csv_path.stem
    audio_matches = audio_matcher.find_all_audio_for_csv(
        [card.pattern for card in cards],
        csv_name,
        audio_dir
    )

    # Update cards with audio matches
    for card in cards:
        audio_file, confidence = audio_matches.get(card.pattern, (None, 0.0))
        card.audio_file = audio_file
        card.audio_confidence = confidence

    # Write intermediate CSV
    output_path = args.output or csv_path.parent / f"{csv_path.stem}_intermediate.csv"
    csv_processor.write_intermediate_csv(cards, output_path)

    # Validate
    report = csv_processor.validate_cards(cards)
    logger.info(f"Validation: {report['valid']}/{report['total']} cards valid")

    logger.info(f"✓ Intermediate CSV saved to: {output_path}")


def handle_import_command(
    args,
    config: AppConfig,
    csv_dir: Path,
    audio_dir: Path,
    logger: logging.Logger
) -> None:
    """Handle 'import' command to import CSV to Anki.

    Args:
        args: Parsed arguments
        config: Application configuration
        csv_dir: CSV directory path
        audio_dir: Audio base directory path
        logger: Logger instance
    """
    csv_path = args.csv
    if not csv_path.is_absolute():
        csv_path = csv_dir / csv_path

    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    logger.info(f"Importing CSV to Anki: {csv_path}")

    # Initialize connector
    connector = AnkiConnector(config)
    if not connector.test_connection():
        logger.error("Failed to connect to AnkiConnect. Is Anki running with AnkiConnect add-on?")
        sys.exit(1)

    # Read CSV
    csv_processor = CSVProcessor(config)
    cards = csv_processor.read_grammar_csv(csv_path)

    # Match audio (unless --no-audio flag)
    if not args.no_audio:
        audio_matcher = AudioMatcher(config)
        csv_name = csv_path.stem
        audio_matches = audio_matcher.find_all_audio_for_csv(
            [card.pattern for card in cards],
            csv_name,
            audio_dir
        )

        for card in cards:
            audio_file, confidence = audio_matches.get(card.pattern, (None, 0.0))
            card.audio_file = audio_file
            card.audio_confidence = confidence

    # Validate (unless --no-validate flag)
    if not args.no_validate:
        report = csv_processor.validate_cards(cards)
        if report["total"] == 0:
            logger.error("No valid cards to import")
            sys.exit(1)

    # Determine deck name
    deck_name = args.deck
    if not deck_name:
        # Extract from CSV filename
        csv_name = csv_path.stem
        deck_name = config.deck.template.replace("{lesson_name}", csv_name)
        logger.info(f"Deck name auto-detected: {deck_name}")

    # Create deck
    if not connector.create_deck(deck_name):
        logger.error(f"Failed to create deck: {deck_name}")
        sys.exit(1)

    # Prepare cards for import
    anki_cards = []
    for card in cards:
        front, back, audio_html = card.to_anki_card()
        anki_cards.append({
            "front": front,
            "back": back,
            "audio": audio_html,
            "tags": ["grammar", csv_path.stem],
        })

    # Import cards
    summary = connector.add_cards_batch(deck_name, anki_cards)

    logger.info(f"✓ Import complete:")
    logger.info(f"  - Cards added: {summary['added']}")
    logger.info(f"  - Cards skipped (duplicates): {summary['skipped']}")
    logger.info(f"  - Cards failed: {summary['failed']}")
    logger.info(f"  - Total: {summary['total']}")


if __name__ == "__main__":
    main()

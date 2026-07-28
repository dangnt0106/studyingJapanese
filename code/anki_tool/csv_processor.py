#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CSV processor for grammar data."""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from config import AppConfig

logger = logging.getLogger(__name__)


@dataclass
class GrammarCard:
    """Represents a grammar card extracted from CSV."""
    pattern: str  # Japanese pattern (e.g., "〜一方だ")
    meaning: str  # Short Vietnamese translation
    explanation: str  # Full Vietnamese explanation
    audio_file: Optional[str] = None  # Audio filename if matched
    audio_confidence: float = 0.0  # Fuzzy match confidence (0-1)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for output CSV."""
        return {
            "pattern": self.pattern,
            "meaning": self.meaning,
            "explanation": self.explanation,
            "audio_file": self.audio_file or "",
            "audio_confidence": f"{self.audio_confidence:.2f}",
        }

    def to_anki_card(self) -> Tuple[str, str, Optional[str]]:
        """Convert to Anki card format.

        Returns:
            Tuple of (front, back, audio_html)
            - front: Japanese pattern
            - back: Vietnamese meaning + explanation
            - audio_html: Optional audio HTML tag or None
        """
        # Format back as: "Meaning\n\nExplanation"
        back = f"{self.meaning}\n\n{self.explanation}"

        # Audio HTML tag
        audio_html = None
        if self.audio_file:
            audio_html = f'[sound:{self.audio_file}]'

        return self.pattern, back, audio_html


class CSVProcessor:
    """Process grammar CSV files."""

    def __init__(self, config: AppConfig):
        """Initialize CSV processor.

        Args:
            config: Application configuration
        """
        self.config = config

    def read_grammar_csv(self, csv_path: Path) -> List[GrammarCard]:
        """Read grammar CSV file and extract cards.

        Expected CSV format:
        - Column 1: Japanese pattern
        - Column 2: Vietnamese meaning/explanation
        - Additional columns: ignored

        Args:
            csv_path: Path to CSV file

        Returns:
            List of GrammarCard objects
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        cards = []

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)

                for row_num, row in enumerate(reader, 1):
                    if not row or all(not cell.strip() for cell in row):
                        # Skip empty rows
                        continue

                    if len(row) < 2:
                        logger.warning(f"Row {row_num} has fewer than 2 columns, skipping")
                        continue

                    pattern = row[0].strip()
                    meaning_and_explanation = row[1].strip()

                    # Remove BOM if present
                    if pattern.startswith('\ufeff'):
                        pattern = pattern[1:]

                    if not pattern or not meaning_and_explanation:
                        logger.debug(f"Row {row_num} has empty pattern or meaning, skipping")
                        continue

                    # Extract meaning and explanation
                    meaning, explanation = self._parse_meaning_explanation(meaning_and_explanation)

                    card = GrammarCard(
                        pattern=pattern,
                        meaning=meaning,
                        explanation=explanation
                    )

                    cards.append(card)

            logger.info(f"Loaded {len(cards)} cards from {csv_path.name}")
            return cards

        except Exception as e:
            logger.error(f"Error reading CSV {csv_path}: {e}")
            raise

    def _parse_meaning_explanation(self, text: str) -> Tuple[str, str]:
        """Parse meaning and explanation from CSV cell.

        The CSV cell contains both meaning and explanation, separated by newlines
        or in some format. Try to extract the main meaning from the first line.

        Args:
            text: Text from CSV cell

        Returns:
            Tuple of (meaning, explanation)
        """
        lines = text.split("\n")

        # First non-empty line is usually the meaning/summary
        meaning = ""
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("★"):
                meaning = stripped
                break

        # Everything is explanation
        explanation = text.strip()

        # If meaning is same as full text, try to extract first line
        if meaning == explanation:
            first_line = lines[0].strip() if lines else ""
            if first_line:
                meaning = first_line
                # Remove first line from explanation
                remaining = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
                explanation = remaining if remaining else first_line

        return meaning, explanation

    def write_intermediate_csv(
        self,
        cards: List[GrammarCard],
        output_path: Path
    ) -> None:
        """Write cards to intermediate CSV for review.

        Args:
            cards: List of GrammarCard objects
            output_path: Output CSV path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = ["pattern", "meaning", "explanation", "audio_file", "audio_confidence"]

        try:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for card in cards:
                    writer.writerow(card.to_dict())

            logger.info(f"Intermediate CSV written to {output_path}")

        except Exception as e:
            logger.error(f"Error writing intermediate CSV {output_path}: {e}")
            raise

    def validate_cards(self, cards: List[GrammarCard]) -> Dict[str, any]:
        """Validate cards for issues.

        Args:
            cards: List of GrammarCard objects

        Returns:
            Validation report dict
        """
        report = {
            "total": len(cards),
            "valid": 0,
            "missing_audio": 0,
            "empty_meaning": 0,
            "empty_explanation": 0,
            "duplicates": 0,
            "issues": []
        }

        seen_patterns = set()

        for card in cards:
            is_valid = True

            if not card.audio_file:
                report["missing_audio"] += 1
                is_valid = False

            if not card.meaning:
                report["empty_meaning"] += 1
                is_valid = False

            if not card.explanation:
                report["empty_explanation"] += 1
                is_valid = False

            if card.pattern in seen_patterns:
                report["duplicates"] += 1
                is_valid = False
                report["issues"].append(f"Duplicate pattern: {card.pattern}")
            else:
                seen_patterns.add(card.pattern)

            if is_valid:
                report["valid"] += 1

        logger.info(f"Validation report: {report['valid']}/{report['total']} valid cards")
        if report["missing_audio"] > 0:
            logger.info(f"  - {report['missing_audio']} cards missing audio")
        if report["empty_meaning"] > 0:
            logger.warning(f"  - {report['empty_meaning']} cards with empty meaning")
        if report["empty_explanation"] > 0:
            logger.warning(f"  - {report['empty_explanation']} cards with empty explanation")
        if report["duplicates"] > 0:
            logger.warning(f"  - {report['duplicates']} duplicate patterns found")

        return report

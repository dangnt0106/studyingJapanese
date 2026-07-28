#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audio file matching using fuzzy matching on Japanese patterns."""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from difflib import SequenceMatcher

from config import AppConfig

logger = logging.getLogger(__name__)


class AudioMatcher:
    """Match audio files to Japanese grammar patterns using fuzzy matching."""

    # Romaji mapping for common N2 patterns
    ROMAJI_MAPPING = {
        '⼀⽅だ': 'ippouda',
        '上で': 'uede',
        'うえで': 'uede',
        'ようとする': 'youto-suru',
        '⽋かさず': 'kakazzu',
        '⽋かせない': 'kakasenai',
        '⽋かさず/⽋かせない': 'kakazzu-kakasenai',
        '⽋かさず_⽋かせない': 'kakazzu-kakasenai',
        'ことはない': 'kotohanal',
        'こともない': 'komonai',
        'ことはない・こともない': 'kotohanal-komonai',
        'さえ': 'sae',
        'すら': 'sura',
        'さえ・すら': 'sae-sura',
        '次第': 'jitai',
        'しだい': 'jitai',
    }

    def __init__(self, config: AppConfig):
        """Initialize audio matcher.

        Args:
            config: Application configuration
        """
        self.config = config
        self.threshold = config.audio.fuzzy_threshold / 100.0  # Convert to 0-1
        self.supported_formats = tuple(config.audio.supported_formats)
        
        # Build reverse mapping: all patterns that map to each romaji
        self._romaji_to_patterns = {}
        for pattern, romaji in self.ROMAJI_MAPPING.items():
            if romaji not in self._romaji_to_patterns:
                self._romaji_to_patterns[romaji] = []
            self._romaji_to_patterns[romaji].append(pattern)

    def find_audio_for_pattern(
        self,
        pattern: str,
        csv_name: str,
        audio_base_dir: Path
    ) -> Tuple[Optional[str], float]:
        """Find audio file for a Japanese pattern using fuzzy matching.

        Args:
            pattern: Japanese grammar pattern (e.g., "〜一方だ")
            csv_name: CSV filename without extension (e.g., "N2-Junbi-Nguphap-Bai-1")
            audio_base_dir: Base directory for audio files

        Returns:
            Tuple of (audio_filename, confidence_score)
            Returns (None, 0.0) if no suitable match found
        """
        # Try to find audio folder for this CSV
        audio_folder = audio_base_dir / csv_name
        if not audio_folder.exists():
            logger.debug(f"Audio folder not found: {audio_folder}")
            return None, 0.0

        # Get all audio files in folder
        audio_files = self._get_audio_files(audio_folder)
        if not audio_files:
            logger.debug(f"No audio files found in: {audio_folder}")
            return None, 0.0

        # Find best match using fuzzy matching
        best_match = None
        best_score = 0.0

        # Method 1: Try direct Romaji mapping first
        if pattern in self.ROMAJI_MAPPING:
            target_romaji = self.ROMAJI_MAPPING[pattern]
            for audio_file in audio_files:
                if audio_file.stem.lower() == target_romaji.lower():
                    logger.debug(
                        f"Audio match for '{pattern}': {audio_file.name} (direct mapping)"
                    )
                    return audio_file.name, 1.0

        # Method 2: Try fuzzy matching
        for audio_file in audio_files:
            # Try direct fuzzy match
            score1 = self._fuzzy_match_score(pattern, audio_file.stem)
            
            # Try matching with hiragana conversion
            score2 = self._fuzzy_match_with_conversion(pattern, audio_file.stem)
            
            # Use best score
            score = max(score1, score2)
            
            if score > best_score:
                best_score = score
                best_match = audio_file.name

        # Check if score meets threshold
        if best_score >= self.threshold:
            logger.debug(
                f"Audio match for '{pattern}': {best_match} (score: {best_score:.2f})"
            )
            return best_match, best_score
        else:
            if self.config.audio.log_unmatched:
                logger.debug(
                    f"No audio match for '{pattern}' in {audio_folder} "
                    f"(best score: {best_score:.2f}, threshold: {self.threshold:.2f})"
                )
            return None, best_score

    def find_all_audio_for_csv(
        self,
        patterns: List[str],
        csv_name: str,
        audio_base_dir: Path
    ) -> Dict[str, Tuple[Optional[str], float]]:
        """Find audio files for all patterns in a CSV.

        Args:
            patterns: List of Japanese patterns
            csv_name: CSV filename without extension
            audio_base_dir: Base directory for audio files

        Returns:
            Dict mapping pattern -> (audio_filename, confidence_score)
        """
        results = {}
        for pattern in patterns:
            audio_file, score = self.find_audio_for_pattern(pattern, csv_name, audio_base_dir)
            results[pattern] = (audio_file, score)

        # Log summary
        matched = sum(1 for af, _ in results.values() if af is not None)
        logger.info(
            f"Audio matching for {csv_name}: {matched}/{len(patterns)} patterns matched"
        )

        return results

    def _get_audio_files(self, folder: Path) -> List[Path]:
        """Get all audio files in folder.

        Args:
            folder: Directory to search

        Returns:
            List of audio file paths
        """
        if not folder.exists():
            return []

        audio_files = []
        for format_ in self.supported_formats:
            audio_files.extend(folder.glob(f"*.{format_}"))

        return sorted(audio_files)

    def _fuzzy_match_score(self, pattern: str, filename: str) -> float:
        """Calculate fuzzy match score between pattern and filename.

        Uses SequenceMatcher to find similarity ratio.

        Args:
            pattern: Japanese pattern
            filename: Audio filename (without extension)

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize: remove common separators and whitespace
        pattern_normalized = self._normalize(pattern)
        filename_normalized = self._normalize(filename)

        # Calculate similarity
        matcher = SequenceMatcher(None, pattern_normalized, filename_normalized)
        score = matcher.ratio()

        return score

    def _fuzzy_match_with_conversion(self, pattern: str, filename: str) -> float:
        """Try to match by converting hiragana to romaji format.

        Args:
            pattern: Japanese pattern
            filename: Audio filename (without extension)

        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            from pykakasi import kakasi
            kks = kakasi()
            
            # Convert pattern to hiragana
            result = kks.convert(pattern)
            pattern_hiragana = ''.join([r['hira'] for r in result if r['hira']])
            
            # Normalize both for comparison
            pattern_norm = self._normalize(pattern_hiragana)
            filename_norm = self._normalize(filename)
            
            # Try matching
            matcher = SequenceMatcher(None, pattern_norm, filename_norm)
            score = matcher.ratio()
            
            return score
        except Exception:
            return 0.0

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for matching.

        Removes separators and converts to lowercase.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Remove common separators
        text = text.replace("〜", "").replace("～", "").replace("-", "").replace("_", "")
        # Remove spaces
        text = text.replace(" ", "")
        # Convert to lowercase (for mixed text)
        text = text.lower()
        return text


def extract_pattern_from_csv_row(csv_row: Dict[str, str]) -> str:
    """Extract Japanese pattern from CSV row.

    Args:
        csv_row: Row from CSV (dict with column headers as keys)

    Returns:
        Japanese pattern
    """
    # First column typically contains the pattern
    first_value = next(iter(csv_row.values()))
    return first_value.strip()

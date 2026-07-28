#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate audio files offline using pyttsx3 - No internet needed!"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

from config import AppConfig, load_config, get_default_config
from csv_processor import CSVProcessor
from anki_media_manager import copy_audio_to_anki

logger = logging.getLogger(__name__)


class OfflineAudioGenerator:
    """Generate audio files offline using pyttsx3 (no internet required)."""

    def __init__(self, config: AppConfig, voice_index: int = 0):
        """Initialize offline audio generator.

        Args:
            config: Application configuration
            voice_index: Index of voice to use (0=default, or pass specific index)
        """
        if not HAS_PYTTSX3:
            raise ImportError(
                "pyttsx3 is not installed. "
                "Install with: pip install pyttsx3"
            )

        self.config = config
        self.voice_index = voice_index
        
        # Initialize engine temporarily to list voices
        temp_engine = pyttsx3.init()
        voices = temp_engine.getProperty('voices')
        logger.info(f"Available voices: {len(voices)}")
        for i, voice in enumerate(voices):
            logger.info(f"  [{i}] {voice.name} (lang: {voice.languages})")
        
        if len(voices) > voice_index:
            logger.info(f"Using voice: {voices[voice_index].name}")
        else:
            logger.warning(f"Voice index {voice_index} not available, using default")
        
        del temp_engine

    def generate_audio_for_patterns(
        self,
        patterns: List[str],
        output_dir: Path
    ) -> Dict[str, bool]:
        """Generate audio files for each pattern.

        Args:
            patterns: List of Japanese patterns
            output_dir: Directory to save audio files

        Returns:
            Dict mapping pattern -> success status
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results = {}

        for i, pattern in enumerate(patterns, 1):
            try:
                audio_file = self._generate_audio_file(pattern, output_dir)
                results[pattern] = audio_file is not None
                logger.info(f"[{i}/{len(patterns)}] Generated audio: {pattern} -> {audio_file}")
            except Exception as e:
                logger.error(f"Failed to generate audio for '{pattern}': {e}")
                results[pattern] = False

        return results

    def _generate_audio_file(self, pattern: str, output_dir: Path) -> Optional[str]:
        """Generate a single audio file for a pattern.

        Args:
            pattern: Japanese pattern (text to read)
            output_dir: Directory to save audio

        Returns:
            Audio filename if successful, None otherwise
        """
        try:
            audio_filename = self._pattern_to_filename(pattern)
            audio_path = output_dir / audio_filename

            # Create fresh engine for each file (avoids event loop issues)
            engine = pyttsx3.init()
            try:
                # Set properties
                engine.setProperty('rate', 100)  # Speed
                engine.setProperty('volume', 0.9)  # Volume
                
                # Set voice
                voices = engine.getProperty('voices')
                if len(voices) > self.voice_index:
                    engine.setProperty('voice', voices[self.voice_index].id)
                
                # Save to file
                engine.save_to_file(pattern, str(audio_path))
                engine.runAndWait()

                if audio_path.exists() and audio_path.stat().st_size > 0:
                    logger.debug(f"Audio saved: {audio_path} ({audio_path.stat().st_size} bytes)")
                    return audio_filename
                else:
                    logger.warning(f"Audio file was not created or empty: {audio_path}")
                    return None
            finally:
                # Clean up engine
                try:
                    engine.stop()
                except:
                    pass

        except Exception as e:
            logger.error(f"Error generating audio for '{pattern}': {e}")
            return None

    @staticmethod
    def _pattern_to_filename(pattern: str) -> str:
        """Convert pattern to safe filename.

        Args:
            pattern: Japanese pattern

        Returns:
            Filename with .mp3 extension
        """
        # Remove invalid filename characters
        filename = pattern.replace("〜", "").replace("～", "").strip()
        
        # Replace Windows-invalid characters with underscore
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length to 50 chars
        filename = filename[:50]
        # Add .mp3 extension
        return f"{filename}.mp3"


def list_voices():
    """List all available TTS voices."""
    if not HAS_PYTTSX3:
        print("pyttsx3 is not installed. Install with: pip install pyttsx3")
        return

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║              Available Text-to-Speech Voices                  ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")

    for i, voice in enumerate(voices):
        print(f"Index: {i}")
        print(f"  Name: {voice.name}")
        print(f"  ID: {voice.id}")
        print(f"  Languages: {voice.languages}")
        print(f"  Gender: {voice.gender}")
        print(f"  Age: {voice.age}")
        print()

    print("Usage in command:")
    print(f"  python generate_audio_offline.py --csv FILE --voice 0")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Japanese audio files OFFLINE using pyttsx3 (no internet needed!)"
    )

    parser.add_argument(
        "--csv",
        type=Path,
        required=False,
        help="Input grammar CSV file"
    )

    parser.add_argument(
        "--voice",
        type=int,
        default=0,
        help="Voice index to use (see --list-voices for options)"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=False,
        help="Output directory for audio files (default: code/audio/{csv_name})"
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "config.yml",
        help="Path to configuration file"
    )

    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List all available voices and exit"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)-8s %(name)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    logger = logging.getLogger(__name__)

    # Handle list-voices
    if args.list_voices:
        list_voices()
        return

    # CSV is required if not listing voices
    if not args.csv:
        parser.print_help()
        print("\n❌ Error: --csv is required (unless using --list-voices)")
        sys.exit(1)

    if not HAS_PYTTSX3:
        logger.error("pyttsx3 is not installed")
        logger.error("Install with: pip install pyttsx3")
        sys.exit(1)

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

    logger.info("╔════════════════════════════════════════════════════════════════╗")
    logger.info("║   Offline Audio Generation (No Internet Required!)             ║")
    logger.info("╚════════════════════════════════════════════════════════════════╝")
    logger.info(f"CSV file: {csv_path}")
    logger.info(f"Voice index: {args.voice}")

    # Read CSV
    csv_processor = CSVProcessor(config)
    cards = csv_processor.read_grammar_csv(csv_path)

    patterns = [card.pattern for card in cards]
    logger.info(f"Found {len(patterns)} patterns to generate audio for")

    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        audio_base_dir = config.paths.get_audio_base_path(Path(__file__).parent)
        output_dir = audio_base_dir / csv_path.stem

    logger.info(f"Output directory: {output_dir}")

    # Generate audio
    try:
        generator = OfflineAudioGenerator(config, voice_index=args.voice)
        results = generator.generate_audio_for_patterns(patterns, output_dir)

        # Summary
        success_count = sum(1 for result in results.values() if result)
        logger.info(f"\n✓ Audio generation complete: {success_count}/{len(patterns)} successful")

        if success_count > 0:
            logger.info(f"[OK] Audio files saved to: {output_dir}")
            
            # Copy to Anki media folder automatically
            logger.info("\nCopying audio files to Anki media folder...")
            if copy_audio_to_anki(output_dir):
                logger.info("[OK] Audio files copied to Anki successfully!")
            else:
                logger.warning("Could not copy audio files to Anki - they may need to be copied manually")
            
            logger.info("\nNext step: Run import command to add audio to Anki")
            logger.info(f"  python main.py import --csv {args.csv.name} --deck \"Japanese::NguPhap::NguPhap_N2\"")

    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        logger.error("\nTroubleshooting:")
        logger.error("1. Make sure pyttsx3 is installed: pip install pyttsx3")
        logger.error("2. Check available voices: python generate_audio_offline.py --list-voices")
        logger.error("3. Try a different voice: python generate_audio_offline.py --csv FILE --voice 1")
        sys.exit(1)


if __name__ == "__main__":
    main()

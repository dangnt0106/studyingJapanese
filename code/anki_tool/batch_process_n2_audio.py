#!/usr/bin/env python3
"""
Batch process all N2 grammar CSV files:
1. Import cards to Anki (if not already imported)
2. Generate offline audio (auto-copies to Anki media folder)
3. Update existing Anki cards with audio (auto-copies to Anki media folder)
"""

import logging
import sys
from pathlib import Path
from subprocess import run
import io

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-8s %(name)s - %(message)s',
    handlers=[logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'))]
)

logger = logging.getLogger(__name__)


def process_csv_file(csv_filename: str, base_dir: Path) -> bool:
    """Process a single CSV file through all steps.
    
    Args:
        csv_filename: CSV filename (e.g., "N2-Junbi-Nguphap-Bai-1.csv")
        base_dir: Base directory containing anki_tool and output folders
    
    Returns:
        True if successful, False otherwise
    """
    anki_tool_dir = base_dir / "anki_tool"
    output_dir = base_dir / "output"
    csv_path = output_dir / csv_filename
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return False
    
    logger.info(f"{'='*70}")
    logger.info(f"Processing: {csv_filename}")
    logger.info(f"{'='*70}")
    
    # Extract lesson name
    deck_name = "Japanese::NguPhap::NguPhap_N2"
    
    # Step 1: Import cards to Anki (skip if already imported)
    logger.info(f"\n[STEP 1/3] Importing cards to Anki...")
    try:
        result = run([
            sys.executable, str(anki_tool_dir / "main.py"),
            "import",
            "--csv", str(csv_path),
            "--deck", deck_name
        ], cwd=str(anki_tool_dir))
        # Don't fail if import returns non-zero (duplicates are OK)
        logger.info(f"Import step completed")
    except Exception as e:
        logger.error(f"Error importing cards: {e}")
        # Continue anyway - cards might already be imported
    
    # Step 2: Generate audio offline (auto-copies to Anki)
    logger.info(f"\n[STEP 2/3] Generating offline audio...")
    try:
        result = run([
            sys.executable, str(anki_tool_dir / "generate_audio_offline.py"),
            "--csv", str(csv_path),
            "--voice", "2"
        ], cwd=str(anki_tool_dir))
        if result.returncode != 0:
            logger.error("Failed to generate audio")
            return False
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return False
    
    # Step 3: Update Anki cards with audio (auto-copies to Anki)
    logger.info(f"\n[STEP 3/3] Updating Anki cards with audio...")
    try:
        result = run([
            sys.executable, str(anki_tool_dir / "update_cards_with_audio.py"),
            "--csv", str(csv_path),
            "--deck", deck_name
        ], cwd=str(anki_tool_dir))
        if result.returncode != 0:
            logger.error("Failed to update cards with audio")
            return False
    except Exception as e:
        logger.error(f"Error updating cards: {e}")
        return False
    
    logger.info(f"\n[SUCCESS] {csv_filename} processed successfully!")
    return True


def main():
    """Main batch processing loop."""
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "output"
    
    # Find all N2 CSV files
    csv_files = sorted([
        f.name for f in output_dir.glob("N2-Junbi-Nguphap-Bai-*.csv")
        if "_intermediate" not in f.name
    ])
    
    if not csv_files:
        logger.error(f"No N2 CSV files found in {output_dir}")
        return 1
    
    logger.info(f"Found {len(csv_files)} N2 CSV files to process")
    logger.info(f"Files: {', '.join([f.replace('N2-Junbi-Nguphap-', '').replace('.csv', '') for f in csv_files[:10]])}...")
    logger.info(f"\nStarting batch processing...")
    logger.info(f"Make sure Anki is running with AnkiConnect add-on!")
    
    # Process each CSV file
    successful = 0
    failed = 0
    
    for csv_file in csv_files:
        try:
            if process_csv_file(csv_file, base_dir):
                successful += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Unexpected error processing {csv_file}: {e}")
            failed += 1
    
    # Final summary
    logger.info(f"\n{'='*70}")
    logger.info(f"BATCH PROCESSING COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"Total files: {len(csv_files)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"\nAudio files are automatically copied to Anki media folder")
    logger.info(f"Close and reopen Anki to refresh the media cache")
    
    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

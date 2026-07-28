"""
Manage Anki media folder - copy audio files to Anki's collection.media directory.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


def get_anki_media_folder() -> Optional[Path]:
    r"""Get Anki media folder path.
    
    Anki stores media in:
    Windows: C:\Users\[User]\AppData\Roaming\Anki2\[Profile]\collection.media\
    macOS: ~/Library/Application Support/Anki2/[Profile]/collection.media/
    Linux: ~/.local/share/Anki2/[Profile]/collection.media/
    
    Returns:
        Path to Anki media folder if found, None otherwise
    """
    import sys
    from pathlib import Path
    
    if sys.platform == "win32":
        # Windows
        anki_base = Path.home() / "AppData" / "Roaming" / "Anki2"
    elif sys.platform == "darwin":
        # macOS
        anki_base = Path.home() / "Library" / "Application Support" / "Anki2"
    else:
        # Linux
        anki_base = Path.home() / ".local" / "share" / "Anki2"
    
    if not anki_base.exists():
        logger.warning(f"Anki2 folder not found: {anki_base}")
        return None
    
    # Find the first profile folder (usually "User 1" or similar)
    profile_folders = [f for f in anki_base.iterdir() if f.is_dir() and f.name != "addons21" and f.name != "logs"]
    
    if not profile_folders:
        logger.warning(f"No Anki profiles found in: {anki_base}")
        return None
    
    # Use the first profile found (usually the active one)
    profile_folder = profile_folders[0]
    media_folder = profile_folder / "collection.media"
    
    if not media_folder.exists():
        logger.warning(f"Anki media folder not found: {media_folder}")
        return None
    
    logger.debug(f"Found Anki media folder: {media_folder}")
    return media_folder


def copy_audio_to_anki(audio_dir: Path) -> bool:
    """Copy all MP3 files from audio directory to Anki media folder.
    
    Args:
        audio_dir: Directory containing MP3 files
    
    Returns:
        True if successful, False otherwise
    """
    media_folder = get_anki_media_folder()
    if not media_folder:
        logger.warning("Could not find Anki media folder. Audio files won't be accessible in Anki.")
        return False
    
    if not audio_dir.exists():
        logger.error(f"Audio directory not found: {audio_dir}")
        return False
    
    # Find all MP3 files
    mp3_files = list(audio_dir.glob("*.mp3"))
    
    if not mp3_files:
        logger.warning(f"No MP3 files found in: {audio_dir}")
        return False
    
    logger.info(f"Copying {len(mp3_files)} audio files to Anki media folder...")
    
    try:
        for mp3_file in mp3_files:
            dest_file = media_folder / mp3_file.name
            shutil.copy2(mp3_file, dest_file)
            logger.debug(f"Copied: {mp3_file.name}")
        
        logger.info(f"Successfully copied {len(mp3_files)} audio files to Anki")
        return True
    
    except Exception as e:
        logger.error(f"Failed to copy audio files to Anki: {e}")
        return False


def copy_audio_files_for_csv(csv_filename: str, audio_base_dir: Path) -> bool:
    """Copy audio files for a specific CSV to Anki media folder.
    
    Args:
        csv_filename: CSV filename (e.g., "N2-Junbi-Nguphap-Bai-1.csv")
        audio_base_dir: Base directory containing audio subdirectories
    
    Returns:
        True if successful, False otherwise
    """
    # Extract lesson name: "N2-Junbi-Nguphap-Bai-1.csv" -> "Bai-1" -> folder "N2-Junbi-Nguphap-Bai-1"
    lesson_name = csv_filename.replace("N2-Junbi-Nguphap-", "").replace(".csv", "")
    audio_dir = audio_base_dir / f"N2-Junbi-Nguphap-{lesson_name}"
    
    if not audio_dir.exists():
        logger.warning(f"Audio directory not found for {csv_filename}: {audio_dir}")
        return False
    
    return copy_audio_to_anki(audio_dir)

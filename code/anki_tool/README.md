# Anki Integration Tool - Usage Guide

A Python tool to import Japanese grammar CSV files into Anki with **automatic offline audio generation** using AnkiConnect API and fuzzy audio matching.

**Key Features:**
- ✅ Offline audio generation (pyttsx3) - no internet required
- ✅ Automatic copying to Anki media folder
- ✅ Batch processing for multiple CSV files
- ✅ Fuzzy audio pattern matching
- ✅ CSV import to Anki with AnkiConnect API

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Batch Processing](#batch-processing)
4. [Configuration](#configuration)
5. [Detailed Usage](#detailed-usage)
6. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.7+
- Anki with [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on installed
- Running Anki instance (for import commands)

### Setup

1. Navigate to the anki_tool directory:
```bash
cd code/anki_tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Create a symbolic link or add to PATH for easier access:
```bash
# Windows
python -m pip install -e .

# Or run directly:
python main.py --help
```

## Quick Start

### 1-Minute Setup

**Prerequisites:**
- Have Anki open with AnkiConnect add-on installed
- Have CSV files in `../output/` folder

**Run once to test:**
```bash
# Test AnkiConnect connection
python main.py test

# Generate audio and update one file (Bai-1)
python generate_audio_offline.py --csv ../output/N2-Junbi-Nguphap-Bai-1.csv --voice 2
python update_cards_with_audio.py --csv ../output/N2-Junbi-Nguphap-Bai-1.csv --deck "Japanese::NguPhap::NguPhap_N2"
```

**Or import without audio first:**
```bash
python main.py import --csv ../output/N2-Junbi-Nguphap-Bai-1.csv --deck "Japanese::NguPhap::NguPhap_N2" --no-audio
```

## Batch Processing

### Process All N2 Files (Bai-1 through Bai-19)

**What it does:**
1. Imports all CSV files to Anki
2. Generates offline audio (pyttsx3) - **automatically copies to Anki media folder**
3. Updates Anki cards with audio attachments

**Run:**
```bash
python batch_process_n2_audio.py
```

**Expected output:**
```
[STEP 1/3] Importing cards to Anki...
[STEP 2/3] Generating offline audio...
[OK] Audio files copied to Anki successfully!
[STEP 3/3] Updating Anki cards with audio...
Successfully copied 7 audio files to Anki
[SUCCESS] N2-Junbi-Nguphap-Bai-1.csv processed successfully!
...
[BATCH PROCESSING COMPLETE]
Total files: 19
Successful: 19
Failed: 0
```

**Important Notes:**
- Anki must be running and AnkiConnect add-on must be active
- Close Anki and reopen to see audio in cards
- Audio files are automatically copied to Anki media folder
- Script handles duplicate cards gracefully (skips if already imported)


The tool uses a `config.yml` file for configuration. A default configuration is provided.

### Key Configuration Options

```yaml
anki:
  url: "http://localhost"      # AnkiConnect server
  port: 8765                    # AnkiConnect port
  timeout: 10                   # Connection timeout in seconds

paths:
  grammar_csv_dir: "../output"  # Directory with grammar CSV files
  audio_base_dir: "../audio"    # Base directory for audio files
  output_dir: "./output"        # Output directory for intermediate CSVs
  logs_dir: "./logs"            # Logs directory

audio:
  fuzzy_threshold: 80           # Fuzzy matching threshold (0-100)
  supported_formats:
    - mp3
    - wav
    - ogg

deck:
  template: "Japanese::NguPhap::{lesson_name}"
  name_extraction_pattern: "N(?P<level>\\d+)-.*?(?P<lesson>Bai-\\d+)"
```

### Audio File Organization

Audio files should be organized as follows:

```
audio/
  N2-Junbi-Nguphap-Bai-1/
    ikou_da.mp3
    tame_ni.mp3
    ...
  N2-Junbi-Nguphap-Bai-2/
    ...
```

The tool uses fuzzy matching to connect grammar patterns in the CSV to audio filenames. For example:
- Pattern: `〜一方だ` might match audio file: `ikou_da.mp3`
- Pattern: `〜ため` might match audio file: `tame.mp3`

## Usage

### General Command Structure

```bash
python main.py [--config CONFIG_FILE] COMMAND [OPTIONS]
```

## Commands

### 1. Test Connection

Test if AnkiConnect is accessible:

```bash
python main.py test
```

**Expected Output:**
```
[INFO] Testing AnkiConnect connection...
[INFO] Connected to AnkiConnect API version: 6
✓ Connection test PASSED
```

### 2. Generate Offline Audio

Generate MP3 audio files for all patterns in a CSV using pyttsx3 (Microsoft Haruka voice):

```bash
python generate_audio_offline.py --csv INPUT_CSV [--voice VOICE_ID] [--output-dir OUTPUT_DIR]
```

**Options:**
- `--csv INPUT_CSV` (required): Path to input grammar CSV file
- `--voice VOICE_ID` (optional): Voice ID (default: 2 for Haruka)
- `--output-dir OUTPUT_DIR` (optional): Output folder for MP3s

**What happens:**
1. Reads all grammar patterns from CSV
2. Generates MP3 audio using pyttsx3
3. **Automatically copies all MP3s to Anki media folder**
4. Saves MP3s to folder named after CSV (e.g., `N2-Junbi-Nguphap-Bai-1/`)

**Example:**
```bash
python generate_audio_offline.py --csv ../output/N2-Junbi-Nguphap-Bai-1.csv --voice 2
```

### 3. Update Cards with Audio

Update existing Anki cards with audio attachments:

```bash
python update_cards_with_audio.py --csv INPUT_CSV [--deck DECK_NAME]
```

**Options:**
- `--csv INPUT_CSV` (required): Path to input grammar CSV file
- `--deck DECK_NAME` (optional): Anki deck name (default: auto-extracted)

**What happens:**
1. Reads audio files from folder matching CSV name
2. Finds all matching patterns in Anki
3. Adds `[sound:filename.mp3]` tags to card backs
4. **Automatically copies audio files to Anki media folder**

**Example:**
```bash
python update_cards_with_audio.py --csv ../output/N2-Junbi-Nguphap-Bai-1.csv --deck "Japanese::NguPhap::NguPhap_N2"
```

### 4. Import to Anki (without audio)

Import grammar CSV directly to Anki without audio:

```bash
python main.py import --csv INPUT_CSV [--deck DECK_NAME] [--no-validate]
```

**Options:**
- `--csv INPUT_CSV` (required): Path to input grammar CSV file
- `--deck DECK_NAME` (optional): Anki deck name (default: auto-extracted from CSV filename)
- `--no-validate`: Skip validation before import
- `--no-audio`: Skip audio matching

**Important:** Anki must be running with AnkiConnect add-on enabled.

### 5. Generate Intermediate CSV (for review)

Generate a CSV with audio matches for review before importing:

```bash
python main.py csv --input INPUT_CSV [--output OUTPUT_CSV]
```

**Options:**
- `--input INPUT_CSV` (required): Path to input grammar CSV file
- `--output OUTPUT_CSV` (optional): Path to output intermediate CSV

**Example:**
```
python main.py csv --input N2-Junbi-Nguphap-Bai-1.csv --output review.csv
```

## Examples

### Example 1: Complete Workflow for Single File

```bash
# Step 1: Generate audio (auto-copies to Anki)
python generate_audio_offline.py --csv ../output/N2-Junbi-Nguphap-Bai-1.csv --voice 2

# Step 2: Update existing cards with audio
python update_cards_with_audio.py --csv ../output/N2-Junbi-Nguphap-Bai-1.csv --deck "Japanese::NguPhap::NguPhap_N2"
```

### Example 2: Import New File (then add audio)

```bash
# Step 1: Import cards to Anki without audio
python main.py import --csv ../output/N2-Junbi-Nguphap-Bai-2.csv --deck "Japanese::NguPhap::NguPhap_N2" --no-audio

# Step 2: Generate audio (auto-copies to Anki)
python generate_audio_offline.py --csv ../output/N2-Junbi-Nguphap-Bai-2.csv --voice 2

# Step 3: Update cards with audio
python update_cards_with_audio.py --csv ../output/N2-Junbi-Nguphap-Bai-2.csv --deck "Japanese::NguPhap::NguPhap_N2"
```

### Example 3: Batch Process All Files

```bash
# Process all 19 N2 files automatically
python batch_process_n2_audio.py
```

This will:
- Import all CSV files (skip duplicates)
- Generate audio for each file
- Update all cards with audio
- Automatically copy all audio to Anki media folder

### Example 4: Test AnkiConnect Connection

```bash
python main.py test
```

## Configuration

Expected input CSV format:

| Column 1 | Column 2 |
|----------|----------|
| Japanese Pattern | Vietnamese Meaning + Explanation |
| `〜一方だ` | `Dần dần thay đổi...` |
| `〜ため` | `Để, vì mục đích...` |

**Notes:**
- Column 1: Japanese grammar pattern (e.g., `〜一方だ`)
- Column 2: Vietnamese translation/explanation (supports multi-line text)
- Additional columns are ignored
- Empty rows are skipped

## Audio Matching

The tool uses fuzzy matching (Python `difflib`) to match patterns to audio files:

1. For pattern `〜一方だ` in CSV for `N2-Junbi-Nguphap-Bai-1.csv`
2. Looks for audio files in `audio/N2-Junbi-Nguphap-Bai-1/`
3. Calculates similarity between pattern and each audio filename
4. Returns best match if confidence > `fuzzy_threshold` (default: 80%)

**Example Matches:**
- Pattern: `一方だ` ↔ Audio: `ikou_da.mp3` (match score: 0.85)
- Pattern: `ため` ↔ Audio: `tame_ni.mp3` (match score: 0.80)
- Pattern: `のに` ↔ No match found (below threshold)

## Troubleshooting

### Error: "Connection refused" or "Failed to connect to AnkiConnect"

**Solution:**
1. Ensure Anki is running
2. Verify AnkiConnect add-on is installed in Anki
3. Check that AnkiConnect is listening on localhost:8765
   - In Anki: Tools → Add-ons → AnkiConnect → Config
   - Should have `"apiBindAddress": "127.0.0.1"` and `"apiBindPort": 8765`

### Error: "CSV file not found"

**Solution:**
1. Verify CSV file path is correct
2. Use absolute paths if relative paths don't work
3. Check configuration `grammar_csv_dir` setting
4. Ensure file exists in `../output/` folder

### Audio Not Playing in Anki

**Solution:**
1. Close and reopen Anki to refresh media cache
2. Verify audio files are copied to Anki media folder
3. Check file exists: `C:\Users\[YourName]\AppData\Roaming\Anki2\[Profile]\collection.media\`
4. Look for `[sound:filename.mp3]` tags in card's Back field (in Anki browser)

### Audio Not Generated

**Solution:**
1. Verify pyttsx3 is installed: `pip install -r requirements.txt`
2. Verify Microsoft Haruka voice is available on Windows:
   - Settings → Speech → Speech recognition → Advanced options
   - Check if "Microsoft Haruka Desktop" voice is installed
3. Try alternative voice ID: `python generate_audio_offline.py --csv file.csv --voice 1` or `--voice 3`
4. Check logs in `logs/` directory for detailed errors

### No Audio Files Matched (when importing with main.py)

**Solution:**
1. Use `generate_audio_offline.py` instead - it creates audio files
2. Or provide pre-recorded audio files in `audio/{csv_name}/` folder
3. If using existing audio, check fuzzy matching confidence in intermediate CSV
4. Lower `fuzzy_threshold` in config if needed (e.g., 75% instead of 80%)

### Duplicate Cards in Anki After Batch Processing

**Solution:**
1. Script handles duplicates automatically - skip importing if cards already exist
2. If you want to re-import, manually delete old cards from Anki first
3. Or use `--no-audio` flag to import only new cards

### Windows Terminal Encoding Issues

**Solution:**
1. Run scripts with UTF-8 encoding: `chcp 65001` (in PowerShell)
2. Or use Git Bash instead of Windows PowerShell
3. Script automatically handles encoding internally

## Audio Generation Settings

### Available Voices (pyttsx3)

Windows includes several Japanese voices. Test which one sounds best:

```bash
# Voice 0
python generate_audio_offline.py --csv file.csv --voice 0

# Voice 1
python generate_audio_offline.py --csv file.csv --voice 1

# Voice 2 (Haruka - Recommended)
python generate_audio_offline.py --csv file.csv --voice 2

# Voice 3
python generate_audio_offline.py --csv file.csv --voice 3
```

### Speed and Rate Adjustment

Edit `generate_audio_offline.py` lines 125-130 to adjust:
- `engine.setProperty('rate', 120)` - speech speed (words per minute)
- `engine.setProperty('volume', 1.0)` - volume (0.0 to 1.0)

## Logs

Log files are created in the `logs/` directory (configurable) with format:
- `anki_import_YYYYMMDD.log`

Check logs for detailed operation information and debugging.

## Project Structure

```
anki_tool/
├── main.py                      # Main entry point for CLI commands
├── anki_connector.py            # AnkiConnect API wrapper
├── anki_media_manager.py        # Auto-copy audio to Anki media folder
├── csv_processor.py             # Parse grammar CSV files
├── audio_matcher.py             # Fuzzy match audio files to patterns
├── config.py                    # Configuration management
├── config.yml                   # Configuration file
├── generate_audio_offline.py    # Generate MP3 using pyttsx3 (RECOMMENDED)
├── update_cards_with_audio.py   # Update Anki cards with audio
├── batch_process_n2_audio.py    # Batch process all N2 files
├── requirements.txt             # Python dependencies
├── SETUP_GOOGLE_CREDENTIALS.py  # Guide for Google Cloud setup (optional)
├── README.md                    # This file
├── .gitignore                   # Git ignore rules
└── __init__.py

Core Modules:
- main.py: CLI entry point with test, csv, and import commands
- anki_connector.py: Wrapper for AnkiConnect API calls
- csv_processor.py: Parses grammar CSV files with UTF-8 BOM handling
- audio_matcher.py: Fuzzy matches audio filenames to patterns
- config.py: Loads and validates config.yml

Audio Generation:
- generate_audio_offline.py: Uses pyttsx3 for offline audio (RECOMMENDED)

Automation:
- anki_media_manager.py: Copies audio to Anki media folder (auto-integrated)
- batch_process_n2_audio.py: Processes all 19 N2 files in one command
- update_cards_with_audio.py: Updates existing cards with audio attachments

Configuration:
- config.yml: Settings for AnkiConnect, paths, audio, deck names
- SETUP_GOOGLE_CREDENTIALS.py: (Optional) If you want Google Cloud audio instead

Ignored (not tracked):
- output/: Generated output CSV files
- logs/: Generated log files
- audio/: Generated MP3 files
- __pycache__/: Python cache
- *.log: Log files
```

## Dependencies

See [requirements.txt](requirements.txt) for full list. Key dependencies:

```
pyttsx3==2.99          # Offline text-to-speech (RECOMMENDED for Japanese)
requests               # HTTP client for AnkiConnect
pydantic>=2.0          # Configuration validation
pyyaml                 # YAML config parsing
pykakasi>=2.3.0        # Japanese character conversion
difflib (built-in)     # Fuzzy string matching
```

## Note: Why Offline Audio?

**Why pyttsx3 (Offline) instead of Google Cloud?**
- ✅ Free (no costs or API limits)
- ✅ Works offline (no internet required)
- ✅ Microsoft Haruka voice sounds natural
- ✅ Instant generation (no API delays)
- ✅ Simple setup (no credentials needed)

**When to use Google Cloud instead:**
- Professional voice synthesis needed
- Multiple language support required
- Custom voice parameters needed
- See [SETUP_GOOGLE_CREDENTIALS.py](SETUP_GOOGLE_CREDENTIALS.py) for setup guide

---

**Last Updated:** 2026-07-28  
**Version:** 2.0 (Offline Audio + Batch Processing)

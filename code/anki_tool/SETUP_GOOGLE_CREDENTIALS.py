#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Setup guide for Google Cloud Text-to-Speech credentials."""

import sys
from pathlib import Path

def show_setup_guide():
    """Display setup guide for Google Cloud credentials."""
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║        Google Cloud Text-to-Speech Setup Guide                ║
╚════════════════════════════════════════════════════════════════╝

To generate audio using Google Text-to-Speech, you need to:

1. CREATE A GOOGLE CLOUD PROJECT
   - Go to: https://console.cloud.google.com
   - Sign in with your Google account (create one if needed)
   - Click "Select a Project" → "New Project"
   - Enter project name (e.g., "japanese-anki")
   - Click "Create"

2. ENABLE TEXT-TO-SPEECH API
   - In Google Cloud Console
   - Search for "Text-to-Speech API"
   - Click it and press "ENABLE"
   
3. CREATE A SERVICE ACCOUNT
   - Go to: IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Name: "anki-audio-generator"
   - Click "Create and Continue"
   - Grant role: "Editor" (or "Cloud Text-to-Speech Admin")
   - Click "Continue" → "Done"

4. CREATE AND DOWNLOAD JSON KEY
   - Click on the service account you created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Select "JSON"
   - Click "Create"
   - A JSON file will download automatically
   - Save it somewhere safe (e.g., ~/google-credentials.json)

5. USE THE CREDENTIALS FILE
   Run the generate_audio script with the credentials file:
   
   python generate_audio.py \\
     --csv N2-Junbi-Nguphap-Bai-1.csv \\
     --credentials /path/to/your-credentials.json

   Or set environment variable:
   
   $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\\path\\to\\credentials.json"
   python generate_audio.py --csv N2-Junbi-Nguphap-Bai-1.csv

═══════════════════════════════════════════════════════════════════

COST INFORMATION:
- Free tier: First 1 million characters per month
- After free tier: $16 per million characters
- Japanese text is typically 1 pattern = ~10-20 characters

ALTERNATIVE (If you prefer not to use Google Cloud):
- Use offline TTS library: pyttsx3 (but lower quality for Japanese)
- Record audio manually
- Use online resources for Japanese pronunciation

═══════════════════════════════════════════════════════════════════
""")

if __name__ == "__main__":
    show_setup_guide()

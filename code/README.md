# PDF Grammar Extraction Tool

A reusable batch-based tool to extract grammar content from PDF files and export them as structured CSV files.

## Quick Start

1. Place PDF files in the `input/` folder
2. Double-click `cmd.bat` to run the extraction
3. Check the `output/` folder for generated CSV files
4. Review `logs/run_YYYYMMDD.log` for execution details

## Folder Structure

```
code/
├── cmd.bat                          # Entry point (double-click to run)
├── input/                           # Place PDF files here
│   └── *.pdf
├── template/                        # Template reference files
│   ├── NguPhapN2_1.csv             # Sample CSV output format
│   └── N2-Junbi-Nguphap-Bai-1.pdf  # Reference PDF
├── output/                          # Generated CSV files
│   └── *.csv
├── logs/                            # Execution logs
│   └── run_YYYYMMDD.log            # Daily log file
└── core/                            # Source code
    ├── extract_grammar.py           # Main extraction script
    ├── pdf_grammar_extraction_requirements.md  # Requirements doc
    └── README.md                    # This file
```

## Features

- **Automatic PDF Processing**: Scans `input/` folder for all PDF files automatically
- **Mixed Layout Support**: Handles both lessons with a numbered TOC and lessons that only expose numbered grammar headings inside each `Bài ...` section
- **Structured CSV Output**: Generates 2-column CSV format matching the template
- **Template-Style Terms**: Normalizes grammar terms to match the template style by removing leading wave-dash markers and OCR spacing noise in the term only
- **UTF-8 Encoding**: Full support for Japanese and Vietnamese characters
- **Noise Filtering**: Removes lesson branding lines such as `Khoá học Online N2 Junbi – Ngữ pháp` from explanations
- **Error Handling**: Logs errors and continues processing if one PDF fails
- **Daily Logging**: Creates a log file for each day (run_YYYYMMDD.log)

## Usage

### Windows Explorer (Recommended)
1. Click and drag PDF files into the `input/` folder
2. Double-click `cmd.bat` to start extraction
3. The batch file will:
   - Check if Python is installed
   - Install dependencies (pdfplumber) if needed
   - Run the extraction
   - Display completion status

### Command Line
```bash
cd code
python core/extract_grammar.py
```

## Output Format

CSV files are generated with:
- **Column 1**: Grammar term (e.g., "末に")
- **Column 2**: Vietnamese explanation with:
  - Grammar point meaning
  - Key points (★ ポイント)
  - Example sentences (例⽂)
  - Connection rules (接続)

For lessons without a top-of-file TOC, the extractor groups grammar rows by `Bài ...` section boundaries and skips standalone `練習` sections.

**Encoding**: UTF-8 with BOM (utf-8-sig) for compatibility with Excel and Japanese/Vietnamese text

## Example Output

| Grammar Term | Explanation |
|---|---|
| 1. 末に | Sau một thời gian<br>★ ポイント<br>① Ở cuối một khoảng thời gian... |
| 2. だけ・だけ | Đến mức tối đa nhất có thể<br>★ ポイント<br>① Đến mức tối đa có thể... |

## Logging

All runs are logged to `logs/run_YYYYMMDD.log` with:
- **[INFO]** - Major execution steps
- **[ERROR]** - Errors encountered
- **[WARNING]** - Warnings (e.g., no content extracted)

Example log:
```
[INFO] Start processing
[INFO] Scan input folder: found 1 PDF files
[INFO] Processing PDF: sample.pdf
[INFO] Extract grammar content from sample.pdf
[INFO] Found 4 grammar items in sample.pdf
[INFO] Generate CSV: sample.csv
[INFO] Completed: processed 1/1 PDFs successfully
```

## Requirements

- Python 3.7+
- pdfplumber (automatically installed by cmd.bat)
- Windows 10/11 (for batch file execution)

## Troubleshooting

**"Python is not installed"**
- Install Python from https://www.python.org/
- Make sure to check "Add Python to PATH" during installation

**"Failed to read PDF"**
- Ensure the PDF file is not corrupted
- Check that the PDF is in UTF-8 or compatible encoding
- See logs/run_*.log for details

**CSV file is empty**
- The PDF might have a different structure than expected
- If the PDF has a valid numbered TOC block (starting at `1.`), the extractor uses it as the source of truth for grammar names and count
- If the PDF has no usable TOC, the extractor falls back to numbered grammar headings inside each `Bài ...` section
- The parser supports heading variants such as `1. ...`, `4 . ...`, and `1 〜...：` when the line looks like a grammar title rather than an example or dialogue line
- See logs/run_*.log for extraction details

**CSV row count is lower than the grammar list in the PDF**
- Compare the generated row count with the numbered grammar list shown at the top of the lesson PDF
- Check `logs/run_YYYYMMDD.log` for the `Found N grammar items` message
- If the counts do not match, inspect whether the PDF uses a different heading layout than the existing `N2 Junbi` lessons

**Input file count and output file count do not match**
- Some PDFs are processed without a TOC; in that case extraction is driven by grammar headings within each `Bài ...` section
- PDFs where extracted item count does not match a valid TOC count are skipped to avoid partial rows
- Standalone practice-only sections such as `練習` are intentionally skipped
- The run log now reports whether all expected CSVs were generated for the current input batch
- The run log also reports stale CSVs already present in `output/` but not backed by the current `input/` PDFs

## Technical Notes

- The tool dynamically processes all PDFs in the `input/` folder
- No file names are hardcoded
- If one PDF fails, the tool continues processing others
- CSV encoding uses utf-8-sig for Excel compatibility
- Multi-line explanations are properly quoted in CSV format
- Grammar names are stabilized from the numbered list at the top of the lesson when a valid TOC exists
- For no-TOC lessons, grammar items are segmented by numbered headings within each `Bài ...` section and the extractor stops the previous item when a new section starts
- Practice blocks (`問題`, `練習`) and branding metadata are not written into explanations
- Term normalization is applied only to the grammar term column; explanations keep their extracted content except for metadata cleanup

## Support

For issues or feature requests, check the logs (`logs/run_*.log`) for detailed error messages.

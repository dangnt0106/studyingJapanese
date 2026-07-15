 PDF Grammar Extraction Tool - Implementation Plan

 Context

 The goal is to create a reusable tool that extracts grammar content from PDF files and exports them as structured CSV files. Users will be able to place PDFs in the input/ folder and run a batch file to automatically extract grammar items into CSV format matching the existing template structure.

 Current State:
 - Template CSV exists: code/template/NguPhapN2_1.csv with 2-column format (Grammar term | Explanation)
Sample PDFs available in code/input/ and code/template/ folders
Folder structure is set up but Python script and batch file don't exist yet                                                                                            ↓

 Expected Outcome:
 - Working extraction pipeline that processes all PDFs dynamically
 - CSV outputs following the template format (2 columns with UTF-8-sig encoding)
 - Comprehensive logging for debugging and monitoring                                                                                                                     ↓

 ---                                                                                                                                                                      ↓
 Implementation Approach
↓
 1. Create code/extract_grammar.py

 Purpose: Main extraction script that processes PDFs and generates CSV output.                                                                                            ↓

 Key Components:
↓
 1. PDF Processing:
   - Use pdfplumber library for PDF text extraction (better at preserving layout than PyPDF2)
   - Read all .pdf files from code/input/ folder dynamically                                                                                                              ↓
   - Extract text while preserving structure and whitespace patterns
 2. Grammar Extraction Logic:
   - Identify grammar terms: typically on separate lines, followed by whitespace                                                                                          ↓
   - Extract explanation content following the grammar term
   - Handle multi-line explanations within quoted CSV cells
   - Preserve Japanese and Vietnamese text encoding                                                                                                                       ↓
 3. CSV Generation:
   - Output format: 2 columns (Grammar term | Explanation)
   - Match template structure in code/template/NguPhapN2_1.csv                                                                                                            ↓
   - Save to code/output/ folder with same naming as input (e.g., N2-Junbi-Nguphap-Bai-2.pdf → N2-Junbi-Nguphap-Bai-2.csv)
   - Use utf-8-sig encoding to support Japanese/Vietnamese characters
 4. Logging:
   - Create logs/ folder if it doesn't exist                                                                                                                              ↓
   - Log to file: logs/run_YYYYMMDD.log with timestamp
   - Include INFO logs for major steps (start, load template, scan input, processing each PDF, CSV generation, completion)
   - Include ERROR logs for failures (PDF read errors, extraction failures, CSV write errors)                                                                             ↓
   - Continue processing remaining PDFs even if one fails
 5. Error Handling:
   - Gracefully handle PDFs that can't be read                                                                                                                            ↓
   - Log errors with context for debugging
   - Don't stop entire process if one PDF fails                                                                                                                           ↓

 Dependencies:                                                                                                                                                            ↓
 - pdfplumber - for PDF text extraction
 - csv - standard library for CSV writing
 - logging - standard library for logging                                                                                                                                 ↓
 - pathlib - standard library for file path handling
 - datetime - standard library for date/time in log filenames

 ---                                                                                                                                                                      ↓
 2. Create cmd.bat
↓
 Purpose: Batch file entry point for users to run the extraction tool.
↓
 Flow:
 1. Check if Python is available                                                                                                                                          ↓
 2. Run code/extract_grammar.py
 3. Display completion status to user
 4. Keep window open so user can see results/errors                                                                                                                       ↓

 ---
 3. Create logs/ folder (if not exist)                                                                                                                                    ↓

 - Will be auto-created by Python script on first run
 - Stores log files with naming pattern run_YYYYMMDD.log                                                                                                                  ↓

 ---                                                                                                                                                                      ↓
 Critical Files to Modify/Create
                                                                                                                                                                          ↓
 ┌─────────────────────────┬────────────────┬───────────────────────────────────────────┐
 │          File           │     Status     │                  Purpose                  │
 ├─────────────────────────┼────────────────┼───────────────────────────────────────────┤                                                                                 ↓
 │ code/extract_grammar.py │ Create         │ Main extraction and CSV generation script │
 ├─────────────────────────┼────────────────┼───────────────────────────────────────────┤
 │ cmd.bat                 │ Create         │ Batch file entry point at root of code/   │
 ├─────────────────────────┼────────────────┼───────────────────────────────────────────┤
 │ code/logs/              │ Auto-create    │ Logging directory                         │                                                                                 ↓
 ├─────────────────────────┼────────────────┼───────────────────────────────────────────┤
 │ code/output/            │ Already exists │ Destination for CSV files                 │                                                                                 ↓
 └─────────────────────────┴────────────────┴───────────────────────────────────────────┘
 ---
 Reusable Components
 The script will leverage:
 - Template CSV structure from code/template/NguPhapN2_1.csv (read and analyze structure)
 - Existing folder structure (input/, output/, template/)

 ---                                                                                                                                                                      ↓
 Verification Plan
↓
 1. Test with sample PDF:
   - Run cmd.bat with the existing PDF in code/input/N2-Junbi-Nguphap-Bai-2.pdf                                                                                           ↓
   - Verify CSV is generated in code/output/ with correct filename
- Check CSV format matches template (2 columns, quoted cells for multi-line content)                                                                                    Verify output quality:                                                                                                                                                ↓
   - Open generated CSV in Excel/text editor
   - Verify grammar terms are extracted correctly
   - Verify explanations are complete and properly formatted
   - Check encoding is correct (Japanese/Vietnamese characters display properly)
 3. Check logging:                                                                                                                                                        ↓
   - Verify logs/run_YYYYMMDD.log is created
   - Check log contains expected INFO/ERROR messages                                                                                                                      ↓
- Verify timestamps are present                                                                                                                                         Test error handling:                                                                                                                                                  ↓
- Add a corrupt/invalid PDF to input/ folder                                                                                                                           - Run script and verify it logs error but continues processing other PDFs                                                                                              ↓

 ---
 Implementation Notes

 - No hardcoded file names: Script dynamically finds all PDFs in input/ folder                                                                                            ↓
Reusable design: Can process any number of PDFs without code changes                                                                                                   UTF-8-sig encoding: Required for proper Japanese/Vietnamese character support in CSV                                                                                   ↓
 - Graceful degradation: If one PDF fails, script logs error and continues with others
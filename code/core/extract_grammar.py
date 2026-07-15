#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import logging
import sys
from pathlib import Path
from datetime import datetime

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber is not installed.")
    print("Please install it using: pip install pdfplumber")
    sys.exit(1)


class GrammarExtractor:
    def __init__(self):
        self.script_dir = Path(__file__).parent  # This is the 'core' folder
        self.code_dir = self.script_dir.parent    # This is the 'code' folder
        self.input_dir = self.code_dir / "input"
        self.output_dir = self.code_dir / "output"
        self.logs_dir = self.code_dir / "logs"
        self.template_dir = self.code_dir / "template"

        self.logs_dir.mkdir(exist_ok=True)

        log_filename = f"run_{datetime.now().strftime('%Y%m%d')}.log"
        self.log_file = self.logs_dir / log_filename

        self.current_vietnamese_meaning = ""
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def extract_pdf_text(self, pdf_path):
        """Extract text from PDF while preserving structure."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_blocks = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_blocks.append(text)
                return "\n".join(text_blocks)
        except Exception as e:
            self.logger.error(f"Failed to read PDF: {pdf_path.name} - {str(e)}")
            return None

    def parse_grammar_items(self, text):
        """Parse grammar items from extracted text.

        Looks for numbered grammar patterns like "1. 〜XXX" as delimiters.
        These are the detailed lesson items in the PDF.
        Extracts up to the examples (例⽂) section only.
        """
        import re

        grammar_items = []
        lines = text.split('\n')

        current_term = None
        current_explanation = []

        for i, line in enumerate(lines):
            # Check if line starts with "N. 〜" pattern (detailed grammar item)
            stripped = line.strip()
            if re.match(r'^\d+\.\s+〜', stripped):
                if current_term and current_explanation:
                    explanation = self._clean_explanation(current_explanation, self.current_vietnamese_meaning)
                    if explanation:
                        grammar_items.append((current_term, explanation))

                # Extract grammar term and remove the numbering (N. )
                # Example: "1. 〜末に 6 回：Sau một thời gian" → term: "〜末に", meaning: "Sau một thời gian"
                term_with_num = stripped

                # Find Vietnamese meaning (after colon)
                colon_idx_full = max(term_with_num.find('：'), term_with_num.find(':'))
                vietnamese_meaning = ""

                if colon_idx_full > 0:
                    term_part = term_with_num[:colon_idx_full].strip()
                    vietnamese_meaning = term_with_num[colon_idx_full+1:].strip()
                else:
                    term_part = term_with_num

                # Remove the leading number and period: "1. 〜末に 6 回" → "〜末に"
                current_term = re.sub(r'^\d+\.\s+', '', term_part)
                # Also remove the occurrence count if present: "〜末に 6 回" → "〜末に"
                current_term = re.sub(r'\s+\d+\s+回$', '', current_term)

                # Store the Vietnamese meaning for this item
                self.current_vietnamese_meaning = vietnamese_meaning
                current_explanation = [line]
            elif current_term is not None:
                # Add this line to explanation unless it looks like a section marker
                if not re.match(r'^(RIKI\.EDU\.VN|Bài|問題|\d{4})', stripped):
                    current_explanation.append(line)

        # Don't forget the last item
        if current_term and current_explanation:
            explanation = self._clean_explanation(current_explanation, self.current_vietnamese_meaning)
            if explanation:
                grammar_items.append((current_term, explanation))

        return grammar_items

    def _clean_explanation(self, explanation_lines, vietnamese_meaning=""):
        """Clean explanation: keep key points and examples, stop after last example.

        Returns content from first line through last example sentence.
        Prepends Vietnamese meaning at the start if provided.
        """
        import re

        result = []
        last_example_line = -1

        for i, line in enumerate(explanation_lines):
            stripped = line.strip()

            # Skip the first line (which is the grammar term line)
            if i == 0:
                continue

            # Check if this is an example line (numbered or dialog)
            if re.match(r'^\d+[\.\。]\s+', stripped) or re.match(r'^[A-Z][\.\。]\s+', stripped):
                last_example_line = i
                result.append(line)
            # Check if this is example header
            elif stripped == '例⽂：' or stripped == '例文：':
                result.append(line)
            # For lines before we've seen any example, keep content
            elif last_example_line == -1:
                result.append(line)
            # For lines after examples, only keep a few lines then stop
            elif i <= last_example_line + 2:
                # Keep up to 2 lines after last example
                result.append(line)
            else:
                # Beyond 2 lines after last example - stop here
                break

        explanation = '\n'.join(result).strip()

        # Prepend Vietnamese meaning if available
        if vietnamese_meaning:
            explanation = vietnamese_meaning + '\n' + explanation

        return explanation

    def extract_grammar_from_pdf(self, pdf_path):
        """Extract grammar items from a PDF file."""
        self.logger.info(f"Processing PDF: {pdf_path.name}")

        text = self.extract_pdf_text(pdf_path)
        if text is None:
            return None

        self.logger.info(f"Extract grammar content from {pdf_path.name}")
        grammar_items = self.parse_grammar_items(text)

        if not grammar_items:
            self.logger.warning(f"No grammar items found in {pdf_path.name}")
            return []

        self.logger.info(f"Found {len(grammar_items)} grammar items in {pdf_path.name}")
        return grammar_items

    def save_to_csv(self, grammar_items, output_path):
        """Save grammar items to CSV file with utf-8-sig encoding."""
        try:
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                for term, explanation in grammar_items:
                    writer.writerow([term, explanation])
            self.logger.info(f"Generate CSV: {output_path.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to generate CSV output: {str(e)}")
            return False

    def process_pdf(self, pdf_path):
        """Process a single PDF file and generate CSV output."""
        output_filename = pdf_path.stem + '.csv'
        output_path = self.output_dir / output_filename

        grammar_items = self.extract_grammar_from_pdf(pdf_path)

        if grammar_items is None:
            return False

        if not grammar_items:
            self.logger.warning(f"Skipping {output_filename} - no content extracted")
            return True

        success = self.save_to_csv(grammar_items, output_path)
        return success

    def run(self):
        """Main execution method."""
        self.logger.info("Start processing")

        if not self.input_dir.exists():
            self.logger.error(f"Input folder not found: {self.input_dir}")
            return False

        pdf_files = list(self.input_dir.glob("*.pdf"))

        if not pdf_files:
            self.logger.warning("No PDF files found in input folder")
            return True

        self.logger.info(f"Scan input folder: found {len(pdf_files)} PDF files")

        success_count = 0
        for pdf_path in pdf_files:
            if self.process_pdf(pdf_path):
                success_count += 1

        self.logger.info(f"Completed: processed {success_count}/{len(pdf_files)} PDFs successfully")
        return success_count == len(pdf_files)


def main():
    extractor = GrammarExtractor()
    success = extractor.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

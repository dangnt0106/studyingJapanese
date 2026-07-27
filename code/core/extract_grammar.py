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

    def _is_noise_line(self, stripped):
        """Return True for metadata lines that should not be written to explanations."""
        if not stripped:
            return True

        lowered = stripped.lower()
        if 'junbi' in lowered and ('kho' in lowered or 'ngữ pháp' in lowered or 'ngu phap' in lowered):
            return True

        return False

    def _strip_wave_dash(self, value):
        """Legacy mode: keep original extracted text unchanged."""
        return value

    def _format_term(self, value):
        """Format grammar term to match template style."""
        import re

        if not value:
            return value

        formatted = value.replace('〜', '').replace('～', '')
        # Terms should be compact; OCR often injects stray spaces inside Japanese tokens.
        formatted = ''.join(formatted.split())
        formatted = formatted.replace('\u200b', '').replace('\ufeff', '')
        return formatted

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

        Uses the numbered index at the top of the PDF as the stable list of
        grammar names, then scans the lesson body for numbered headings such as
        "1. XXX: meaning" or "4 . XXX".
        """
        import re

        grammar_items = []
        lines = text.split('\n')
        toc_terms, body_start_index = self._extract_toc_terms(lines)

        if not toc_terms:
            return [], toc_terms

        body_lines = lines[body_start_index:]
        toc_size = len(toc_terms)

        current_term = None
        current_explanation = []
        body_started = False
        expected_item_number = 1

        def flush_current_item():
            if current_term and current_explanation:
                explanation = self._clean_explanation(current_explanation, self.current_vietnamese_meaning)
                if explanation:
                    grammar_items.append((self._format_term(current_term), explanation))

        for line in body_lines:
            stripped = line.strip()
            heading_match = re.match(r'^(\d+)\s*[\.．]\s*(.+)$', stripped)

            if not heading_match:
                # Some PDFs render grammar headings as "4 〜TERM" without a dot.
                loose_match = re.match(r'^(\d+)\s+(.+)$', stripped)
                if loose_match:
                    loose_item_number = int(loose_match.group(1))
                    loose_heading_body = loose_match.group(2).strip()
                    if (
                        loose_item_number == expected_item_number
                        and self._matches_toc_heading(loose_item_number, loose_heading_body, toc_terms)
                    ):
                        heading_match = loose_match

            if heading_match:
                item_number = int(heading_match.group(1))
                heading_body = heading_match.group(2).strip()
                has_heading_marker = any(marker in heading_body for marker in ('：', ':', '・', ','))
                is_dialogue_line = re.match(r'^[A-Z](?:[:：]|[\.。])', heading_body) is not None
                matches_expected_toc = self._matches_toc_heading(item_number, heading_body, toc_terms)

                if not body_started:
                    body_started = True

                if (
                    (has_heading_marker or matches_expected_toc)
                    and not is_dialogue_line
                    and len(heading_body) > 2
                    and item_number <= toc_size
                    and item_number == expected_item_number
                ):
                    flush_current_item()

                    colon_idx_full = max(heading_body.find('：'), heading_body.find(':'))
                    heading_term = heading_body
                    vietnamese_meaning = ""

                    if colon_idx_full > 0:
                        heading_term = heading_body[:colon_idx_full].strip()
                        vietnamese_meaning = heading_body[colon_idx_full + 1:].strip()

                    heading_term = re.sub(r'\s+\d+\s+回$', '', heading_term)
                    current_term = self._select_term(item_number, heading_term, toc_terms)
                    self.current_vietnamese_meaning = vietnamese_meaning
                    current_explanation = [line]
                    expected_item_number = item_number + 1
                    continue

            if current_term is not None:
                if self._is_noise_line(stripped):
                    continue

                if not re.match(r'^(RIKI\.EDU\.VN|Bài|問題|\d{4})', stripped):
                    current_explanation.append(line)

        flush_current_item()
        return grammar_items, toc_terms

    def _matches_toc_heading(self, item_number, heading_body, toc_terms):
        """Allow body headings without colons when they clearly start with the TOC term."""
        import re

        toc_term = toc_terms.get(item_number)
        if not toc_term:
            return False

        def normalize(value):
            normalized = value.replace('〜', '').replace('～', '')
            normalized = re.sub(r'[\s　]+', '', normalized)
            return normalized

        normalized_heading = normalize(heading_body)
        normalized_toc = normalize(toc_term)
        return normalized_heading.startswith(normalized_toc)

    def _select_term(self, item_number, heading_term, toc_terms):
        """Prefer the lesson index term unless it looks like a duplicated OCR artifact."""
        toc_term = toc_terms.get(item_number)
        if not toc_term:
            return self._format_term(heading_term)

        previous_toc_term = toc_terms.get(item_number - 1)
        if previous_toc_term and toc_term == previous_toc_term and heading_term != toc_term:
            return self._format_term(heading_term)

        return self._format_term(toc_term)

    def _extract_toc_terms(self, lines):
        """Read the consecutive numbered index block at the top of the PDF."""
        import re

        toc_terms = {}
        collecting = False
        expected_item_number = 1
        body_start_index = 0

        def extract_numbered_chunks(line_text):
            matches = list(re.finditer(r'(\d+)\s*\.\s*', line_text))
            chunks = []

            for idx, match in enumerate(matches):
                item_number = int(match.group(1))
                start = match.end()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(line_text)
                chunk = line_text[start:end].strip()
                chunks.append((item_number, chunk))

            return chunks

        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                if collecting:
                    body_start_index = index + 1
                    break
                continue

            line_chunks = extract_numbered_chunks(stripped)
            if not line_chunks:
                if collecting:
                    body_start_index = index
                    break
                continue

            first_item_number = line_chunks[0][0]
            if not collecting and first_item_number != 1:
                continue

            if collecting and first_item_number != expected_item_number:
                body_start_index = index
                break

            for item_number, heading_body in line_chunks:
                if item_number != expected_item_number:
                    body_start_index = index
                    collecting = True
                    break

                colon_idx_full = max(heading_body.find('：'), heading_body.find(':'))
                if colon_idx_full > 0:
                    # TOC lines can include short VN meanings after colon.
                    heading_body = heading_body[:colon_idx_full].strip()

                heading_body = re.sub(r'\s+\d+\s+回$', '', heading_body)

                collecting = True
                toc_terms[item_number] = self._strip_wave_dash(heading_body)
                expected_item_number += 1
                body_start_index = index + 1
            else:
                continue

            break

        return toc_terms, body_start_index

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

        # Final cleanup for OCR variants of the course branding line.
        cleaned_lines = []
        for line in explanation.split('\n'):
            if self._is_noise_line(line.strip()):
                continue
            cleaned_lines.append(line)
        explanation = '\n'.join(cleaned_lines).strip()

        # Prepend Vietnamese meaning if available
        if vietnamese_meaning:
            explanation = self._strip_wave_dash(vietnamese_meaning) + '\n' + explanation

        return explanation

    def _looks_like_grammar_heading_without_toc(self, heading_body):
        """Heuristic to detect grammar headings when a PDF has no numbered TOC."""
        import re

        body = heading_body.strip()
        if not body:
            return False

        # Dialogue lines should never be treated as grammar headings.
        if re.match(r'^[男女ＡＢA-Z][：:]', body):
            return False

        # Most grammar headings include wave-dash notation.
        if '〜' in body or '～' in body:
            return True

        # Also accept concise headings that end with a meaning marker.
        if ('：' in body or ':' in body) and len(body) <= 40:
            if not re.search(r'[\(（]\s*[\)）]', body):
                return True

        return False

    def _parse_grammar_items_without_toc(self, text):
        """Fallback parser for lessons that have numbered grammar headings but no TOC block."""
        import re

        grammar_items = []
        lines = text.split('\n')

        current_term = None
        current_explanation = []
        last_item_number = 0
        seen_subsection_header = False
        body_started = False
        in_exercise_block = False
        skip_current_subsection = False

        def flush_current_item():
            if current_term and current_explanation:
                explanation = self._clean_explanation(current_explanation, self.current_vietnamese_meaning)
                if explanation:
                    grammar_items.append((self._format_term(current_term), explanation))

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('Bài '):
                if current_term and current_explanation:
                    flush_current_item()
                    current_term = None
                    current_explanation = []
                last_item_number = 0
                seen_subsection_header = True
                in_exercise_block = False
                body_started = False
                skip_current_subsection = False
                continue

            if seen_subsection_header and stripped == '練習':
                skip_current_subsection = True
                continue

            if skip_current_subsection:
                continue

            if stripped.startswith('「') and '⾔い⽅' in stripped:
                if current_term and current_explanation:
                    flush_current_item()
                    current_term = None
                    current_explanation = []
                last_item_number = 0
                seen_subsection_header = True
                body_started = False
                in_exercise_block = False
                continue

            heading_match = re.match(r'^(\d+)\s*[\.．]\s*(.+)$', stripped)

            if not heading_match:
                loose_match = re.match(r'^(\d+)\s+(.+)$', stripped)
                if loose_match:
                    heading_match = loose_match

            if heading_match:
                item_number = int(heading_match.group(1))
                heading_body = heading_match.group(2).strip()

                if self._looks_like_grammar_heading_without_toc(heading_body):
                    has_meaning_marker = ('：' in heading_body or ':' in heading_body)
                    if not body_started and not has_meaning_marker:
                        continue

                    is_forward_number = item_number >= last_item_number
                    is_section_reset = item_number == 1 and seen_subsection_header

                    if is_forward_number or is_section_reset:
                        flush_current_item()

                        colon_idx_full = max(heading_body.find('：'), heading_body.find(':'))
                        heading_term = heading_body
                        vietnamese_meaning = ""

                        if colon_idx_full > 0:
                            heading_term = heading_body[:colon_idx_full].strip()
                            vietnamese_meaning = heading_body[colon_idx_full + 1:].strip()

                        heading_term = re.sub(r'\s+\d+\s+回$', '', heading_term)
                        current_term = self._format_term(heading_term)
                        self.current_vietnamese_meaning = vietnamese_meaning
                        current_explanation = [line]
                        last_item_number = item_number
                        seen_subsection_header = False
                        body_started = True
                        in_exercise_block = False
                        continue

            if current_term is not None:
                if stripped.startswith('問題') or stripped.startswith('練習'):
                    in_exercise_block = True
                    continue

                if in_exercise_block:
                    continue

                if self._is_noise_line(stripped):
                    continue

                if not re.match(r'^(RIKI\.EDU\.VN|Bài|問題|\d{4})', stripped):
                    current_explanation.append(line)

        flush_current_item()
        return grammar_items

    def build_fallback_items(self, text, pdf_stem):
        """Fallback for nonstandard lesson layouts: keep one row with the lesson title and full content."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        content_lines = [line for line in lines if line != 'Khoá học Online N2 Junbi – Ngữ pháp']

        if not content_lines:
            return []

        title = self._extract_fallback_title(content_lines, pdf_stem)
        explanation = '\n'.join(content_lines)
        return [(title, explanation)]

    def _extract_fallback_title(self, lines, pdf_stem):
        """Build a stable document title for fallback extraction."""
        title_parts = []
        seen_lesson_header = False

        for line in lines:
            if line.startswith('第 ') and '課' in line:
                seen_lesson_header = True
                continue

            if line.startswith('Bài '):
                break

            if not seen_lesson_header:
                continue

            title_parts.append(line)
            if len(title_parts) == 2:
                break

        if title_parts:
            return ' / '.join(title_parts)

        return pdf_stem

    def extract_grammar_from_pdf(self, pdf_path):
        """Extract grammar items from a PDF file."""
        self.logger.info(f"Processing PDF: {pdf_path.name}")

        text = self.extract_pdf_text(pdf_path)
        if text is None:
            return None

        self.logger.info(f"Extract grammar content from {pdf_path.name}")
        grammar_items, toc_terms = self.parse_grammar_items(text)

        # Avoid treating the first grammar heading as a fake TOC.
        if len(toc_terms) < 2:
            toc_terms = {}
            grammar_items = []

        if not toc_terms:
            grammar_items = self._parse_grammar_items_without_toc(text)
            if not grammar_items:
                self.logger.warning(
                    f"Skipping {pdf_path.name} - no valid numbered TOC found and no heading-based grammar items extracted"
                )
                return []

            self.logger.info(
                f"Found {len(grammar_items)} grammar items in {pdf_path.name} using heading-based extraction (no TOC)"
            )
            return grammar_items

        if not grammar_items:
            self.logger.warning(f"Skipping {pdf_path.name} - TOC found but no structured grammar items extracted")
            return []

        if len(grammar_items) != len(toc_terms):
            self.logger.warning(
                f"Skipping {pdf_path.name} - extracted {len(grammar_items)} items but TOC has {len(toc_terms)}"
            )
            return []

        self.logger.info(f"Found {len(grammar_items)} grammar items in {pdf_path.name} (TOC: {len(toc_terms)})")
        return grammar_items

    def save_to_csv(self, grammar_items, output_path):
        """Save grammar items to CSV file with utf-8-sig encoding."""
        try:
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
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

    def log_output_summary(self, pdf_files):
        """Report which outputs match the current input batch."""
        expected_outputs = {pdf_path.stem + '.csv' for pdf_path in pdf_files}
        actual_outputs = {csv_path.name for csv_path in self.output_dir.glob('*.csv')}

        missing_outputs = sorted(expected_outputs - actual_outputs)
        stale_outputs = sorted(actual_outputs - expected_outputs)

        if missing_outputs:
            self.logger.warning(f"Missing output CSVs: {', '.join(missing_outputs)}")
        else:
            self.logger.info("All expected output CSVs are present for the current input batch")

        if stale_outputs:
            self.logger.warning(f"Stale output CSVs not backed by current input PDFs: {', '.join(stale_outputs)}")

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

        self.log_output_summary(pdf_files)

        self.logger.info(f"Completed: processed {success_count}/{len(pdf_files)} PDFs successfully")
        return success_count == len(pdf_files)


def main():
    extractor = GrammarExtractor()
    success = extractor.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

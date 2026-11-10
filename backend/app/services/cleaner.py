import re
import unicodedata
from typing import List

class AgronomicTextCleaner:
    """
    Cleans raw document text while strictly preserving chemical formulations,
    scientific names, dosages, application rates, and tabular structures.
    """

    @staticmethod
    def clean_text(raw_text: str, document_title: str = "") -> str:
        if not raw_text:
            return ""

        # 1. Unicode Normalization (NFKC converts non-standard ligatures & symbols to standard form)
        text = unicodedata.normalize("NFKC", raw_text)

        # 2. Normalize line breaks
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 3. Clean running headers and footers (e.g., repeating document title or page numbers at margins)
        if document_title and len(document_title) > 8:
            # Escape for regex and remove if found as standalone line
            title_pat = re.escape(document_title.strip())
            text = re.sub(rf"(?im)^\s*{title_pat}\s*$", "", text)

        # Remove standalone page numbers at start or end of lines (e.g., "Page 14", "14 of 48", "- 14 -")
        text = re.sub(r"(?im)^\s*(?:page\s*)?[-–—]?\s*\d+\s*[-–—]?(?:\s*of\s*\d+)?\s*$", "", text)

        # 4. De-hyphenate words broken across line breaks (e.g. "insec-\nticide" -> "insecticide")
        # Ensure we do NOT strip hyphens in chemical names like "2,4-\nD" or "alpha-\ncypermethrin"
        def dehyphen_sub(match):
            prefix = match.group(1)
            suffix = match.group(2)
            # If prefix ends with letters and suffix starts with lowercase letters, join without hyphen
            if prefix.isalpha() and suffix.islower():
                return f"{prefix}{suffix}"
            return f"{prefix}-{suffix}"

        text = re.sub(r"([A-Za-z]{2,})-\s*\n\s*([A-Za-z]{2,})", dehyphen_sub, text)

        # 5. Reconstruct paragraphs while preserving intentional double newlines and lists
        lines = text.split("\n")
        cleaned_lines: List[str] = []
        for line in lines:
            line_stripped = line.strip()
            # Remove repeated dashes or underlines from page breaks
            if re.match(r"^[-=_*~]{4,}$", line_stripped):
                continue
            cleaned_lines.append(line.rstrip())

        # Group lines into logical paragraphs
        paragraphs: List[str] = []
        current_para: List[str] = []

        for line in cleaned_lines:
            if not line.strip():
                if current_para:
                    paragraphs.append(" ".join(current_para))
                    current_para = []
            else:
                # If line starts with a list bullet or numbering (e.g. 1., a), -, *), start new line
                if re.match(r"^(\d+[\.\)]|[a-zA-Z][\.\)]|[\*\-•])\s+", line.strip()):
                    if current_para:
                        paragraphs.append(" ".join(current_para))
                        current_para = []
                    current_para.append(line.strip())
                elif current_para and (
                    current_para[-1].endswith(":") or 
                    current_para[-1].endswith("|") or 
                    line.startswith("|") or
                    current_para[-1].startswith("|")
                ):
                    # Keep tabular lines or headers intact
                    paragraphs.append(" ".join(current_para))
                    current_para = [line.strip()]
                else:
                    current_para.append(line.strip())

        if current_para:
            paragraphs.append(" ".join(current_para))

        # Rejoin paragraphs with double newlines
        reconstructed = "\n\n".join(p for p in paragraphs if p.strip())

        # 6. Normalize multiple consecutive spaces within lines without touching newlines
        reconstructed = re.sub(r"[ \t]{2,}", " ", reconstructed)
        reconstructed = re.sub(r"\n{3,}", "\n\n", reconstructed)

        return reconstructed.strip()

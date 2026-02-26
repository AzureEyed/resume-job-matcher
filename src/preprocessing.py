"""Text preprocessing and PDF conversion utilities"""

import io
from functools import lru_cache
from typing import BinaryIO, Union

import pdfplumber
import spacy

PDFSource = Union[str, BinaryIO]
SPACY_MODEL_NAME = "en_core_web_sm"
SPACY_MODEL_ERROR_HELP = (
    "spaCy model failed to initialize.\n\n"
    "How to fix:\n"
    "1. In your virtualenv, run: python -m pip install -r requirements.txt\n"
    "2. Install the model: python -m spacy download en_core_web_sm\n"
    "3. Relaunch the app.\n"
    "4. If it still fails, recreate the virtualenv and retry."
)


class PreprocessingModelError(RuntimeError):
    """Raised when spaCy model setup or text processing fails."""
    pass


@lru_cache(maxsize=1)
def get_nlp():
    """Load the spaCy model once and reuse it."""
    try:
        return spacy.load(SPACY_MODEL_NAME)
    except Exception as exc:
        raise PreprocessingModelError(SPACY_MODEL_ERROR_HELP) from exc

def extract_text_from_pdf(
    pdf_source: PDFSource,
    page_separator: str = "\n\n",
    layout: bool = False,
) -> str:
    """Extract text from a PDF path or binary stream."""
    with pdfplumber.open(pdf_source) as pdf:
        pages = []
        for page in pdf.pages:
            text = page.extract_text(layout=layout)
            if text:
                pages.append(text)
    return page_separator.join(pages)

def extract_text_from_pdf_bytes(
    pdf_bytes: bytes,
    page_separator: str = "\n\n",
    layout: bool = False,
) -> str:
    """Extract text from in-memory PDF bytes."""
    return extract_text_from_pdf(
        io.BytesIO(pdf_bytes),
        page_separator=page_separator,
        layout=layout,
    )

def convert_resume(pdf_path, txt_path):
    """Convert a resume PDF into a plain-text file.

    Args:
        pdf_path: Path to the source PDF.
        txt_path: Path to the output text file.
    """
    full_text = extract_text_from_pdf(
        pdf_path,
        page_separator="\n\n--- Page Break ---\n\n",
        layout=False,
    )
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

# centralize replacements to normalize common tech tokens for matching.
REPLACEMENTS = {
    "c++": "cplusplus",
    "c#": "csharp",
    ".net": "dotnet",
    "node.js": "nodejs",
}

def clean_text(text: str) -> str:
    """Lowercase, normalize common tech tokens, lemmatize, and remove stopwords."""
    if not text:
        return ""

    text = text.lower()
    # normalize punctuation that blocks alpha-only tokens.
    text = text.replace("-", " ").replace("/", " ")

    for k, v in REPLACEMENTS.items():
        text = text.replace(k, v)

    try:
        doc = get_nlp()(text)
    except PreprocessingModelError:
        raise
    except Exception as exc:
        raise PreprocessingModelError(SPACY_MODEL_ERROR_HELP) from exc

    tokens = [
        token.lemma_
        for token in doc
        if not token.is_stop and token.is_alpha
    ]

    return " ".join(tokens)

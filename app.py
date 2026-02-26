"""Streamlit UI for resume/job matching.

This file intentionally contains full UI flow documentation because it is the
main entry point for non-CLI users.

Runtime flow:
1. Configure imports and Streamlit page settings.
2. Initialize session-state keys for text and uploaded PDF metadata.
3. Render two panels:
   - left: resume upload + editable resume text
   - right: job upload + editable job text
4. When a PDF is uploaded, extract text with preprocessing helpers.
   - Extraction is keyed by SHA-256 hash of file bytes, not filename.
   - This guarantees same-name files still refresh text when content changes.
5. On Analyze:
   - Validate both text boxes are non-empty.
   - Call matcher.match_texts(...)
   - Render scores, skill lists, and recommendations.
6. Show actionable runtime errors from model/preprocessing layers.
"""

import hashlib
import os
import sys

import streamlit as st

ROOT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

import matcher
import preprocessing

# Session-state keys are centralized to avoid typos and hidden coupling.
RESUME_TEXT_KEY = "resume_text"
JOB_TEXT_KEY = "job_text"
RESUME_PDF_NAME_KEY = "resume_pdf_name"
JOB_PDF_NAME_KEY = "job_pdf_name"
RESUME_PDF_HASH_KEY = "resume_pdf_hash"
JOB_PDF_HASH_KEY = "job_pdf_hash"


def _init_session_state() -> None:
    """Ensure all session keys used by the page exist."""
    st.session_state.setdefault(RESUME_TEXT_KEY, "")
    st.session_state.setdefault(JOB_TEXT_KEY, "")
    st.session_state.setdefault(RESUME_PDF_NAME_KEY, None)
    st.session_state.setdefault(JOB_PDF_NAME_KEY, None)
    st.session_state.setdefault(RESUME_PDF_HASH_KEY, None)
    st.session_state.setdefault(JOB_PDF_HASH_KEY, None)


def _hash_bytes(content: bytes) -> str:
    """Return a stable content hash for uploaded files."""
    return hashlib.sha256(content).hexdigest()


def _sync_uploaded_pdf_text(
    uploaded_file,
    text_key: str,
    name_key: str,
    hash_key: str,
) -> None:
    """Sync uploaded PDF content into a text area-backed session-state key.

    Rules:
    - No file: clear stored file metadata (name/hash) and return.
    - New content hash: extract text and update session-state text.
    - Same content hash: skip extraction to avoid redundant work.
    - Extraction failure: clear extracted text and leave hash unset so retry is
      possible on next rerun.
    """
    if uploaded_file is None:
        st.session_state[name_key] = None
        st.session_state[hash_key] = None
        return

    pdf_bytes = uploaded_file.getvalue()
    pdf_hash = _hash_bytes(pdf_bytes)
    if pdf_hash == st.session_state[hash_key]:
        return

    try:
        extracted = preprocessing.extract_text_from_pdf_bytes(pdf_bytes)
        st.session_state[text_key] = extracted
        st.session_state[name_key] = uploaded_file.name
        st.session_state[hash_key] = pdf_hash
    except Exception:
        st.session_state[text_key] = ""
        st.session_state[name_key] = uploaded_file.name
        st.session_state[hash_key] = None


def _render_upload_column(
    upload_label: str,
    upload_key: str,
    text_label: str,
    text_key: str,
    name_key: str,
    hash_key: str,
    empty_warning: str,
    placeholder: str,
) -> str:
    """Render one upload/text column and return current text value."""
    uploaded_pdf = st.file_uploader(upload_label, type=["pdf"], key=upload_key)
    _sync_uploaded_pdf_text(uploaded_pdf, text_key, name_key, hash_key)

    # Warn when a file exists but no extractable text was found.
    if uploaded_pdf is not None and not st.session_state[text_key].strip():
        st.warning(empty_warning)

    return st.text_area(
        text_label,
        height=300,
        placeholder=placeholder,
        key=text_key,
    )


def _analyze_and_render(resume_text: str, job_text: str) -> None:
    """Run matcher and render metrics/lists/recommendations."""
    try:
        with st.spinner("Analyzing..."):
            result = matcher.match_texts(resume_text, job_text)
    except RuntimeError as exc:
        # RuntimeError is used for actionable model/preprocessing failures.
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"Unexpected analysis error: {exc}")
        return

    st.subheader("Results")
    score_cols = st.columns(3)
    score_cols[0].metric("Final Match Score", f"{result['final_score']:.2f}%")
    score_cols[1].metric("Similarity", f"{result['similarity_score']:.2f}%")
    score_cols[2].metric("Skill Match", f"{result['skill_match_percentage']:.2f}%")

    list_cols = st.columns(3)
    list_cols[0].write("Matched skills")
    list_cols[0].write(result["matched_skills"])
    list_cols[1].write("Missing skills")
    list_cols[1].write(result["missing_skills"])
    list_cols[2].write("Extra skills")
    list_cols[2].write(result["extra_skills"])

    st.subheader("Recommendations")
    if result["recommendations"]:
        for rec in result["recommendations"]:
            st.write(f"- {rec}")
    else:
        st.write("No missing skills detected. You're aligned with the requirements.")


def main() -> None:
    """Render the full Streamlit page."""
    st.set_page_config(page_title="AI Resume Matcher", page_icon="AI", layout="wide")
    _init_session_state()

    st.title("AI Resume & Job Match Analyzer")
    st.caption("Paste a resume and job description to get a match score and skill gaps.")

    col_left, col_right = st.columns(2)

    with col_left:
        resume_text = _render_upload_column(
            upload_label="Resume PDF (optional)",
            upload_key="resume_pdf",
            text_label="Resume text",
            text_key=RESUME_TEXT_KEY,
            name_key=RESUME_PDF_NAME_KEY,
            hash_key=RESUME_PDF_HASH_KEY,
            empty_warning="No text extracted from the resume PDF. Paste text below or try another file.",
            placeholder="Paste resume text here...",
        )

    with col_right:
        job_text = _render_upload_column(
            upload_label="Job Description PDF (optional)",
            upload_key="job_pdf",
            text_label="Job description text",
            text_key=JOB_TEXT_KEY,
            name_key=JOB_PDF_NAME_KEY,
            hash_key=JOB_PDF_HASH_KEY,
            empty_warning="No text extracted from the job PDF. Paste text below or try another file.",
            placeholder="Paste job description here...",
        )

    if st.button("Analyze"):
        if not resume_text.strip() or not job_text.strip():
            st.warning("Please paste both resume and job description text before analyzing.")
            return
        _analyze_and_render(resume_text, job_text)


if __name__ == "__main__":
    main()

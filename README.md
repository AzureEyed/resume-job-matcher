AI Resume & Job Match Analyzer

An NLP-based system that analyzes resumes against job descriptions using transformer embeddings and cosine similarity. It extracts technical skills, computes match scores, and surfaces skill gaps with a simple Streamlit UI.

Features
- Clean and normalize text with spaCy
- Extract skills from a curated list
- Compute semantic similarity with SentenceTransformers
- Combine similarity and skill match into a final score
- Use a Streamlit UI for quick analysis
- Upload PDFs and auto-extract text with pdfplumber
- Generate simple recommendations for missing skills

Project Structure
- `app.py` Streamlit UI
- `src/preprocessing.py` text cleaning
- `src/skills.py` skill list and extraction
- `src/similarity.py` embedding similarity
- `src/matcher.py` end-to-end matching
- `run_app.bat` one click runner

Run (Windows Only)
Windows-specific one-click runner so users do not have to type commands.
1. Double-click `run_app.bat`
2. ctrl + c to end streamlit session from CLI when done in the browser.

What `run_app.bat` does:
1. Checks that Python is available in PATH.
2. Creates a virtual environment at `venv` if it does not already exist.
3. Uses `venv\Scripts\python.exe` for all following commands (installs stay inside the venv).
4. Installs/syncs packages from `requirements.txt`.
5. Checks whether `en_core_web_sm` is installed.
6. Downloads `en_core_web_sm` only if it is missing.
7. Launches the app with `streamlit run app.py`.


Cleanup

If you want to remove everything after you are done, you can do so by deleting the `venv` folder.

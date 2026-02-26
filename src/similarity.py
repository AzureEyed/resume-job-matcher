"""Semantic similarity utilities using SentenceTransformers."""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Put model loading behind a guard to avoid reloading in web apps:
_model = None
MODEL_NAME = "all-MiniLM-L6-v2"

MODEL_ERROR_HELP = (
    "SentenceTransformer failed to initialize or run.\n\n"
    "How to fix:\n"
    "1. Relaunch the app once (transient startup/download issues often clear).\n"
    "2. Ensure internet access on first run so the model can download.\n"
    "3. In your virtualenv, run: pip install -r requirements.txt\n"
    "4. If it still fails, clear Hugging Face cache and retry:\n"
    "   %USERPROFILE%\\.cache\\huggingface\\hub"
)


class SimilarityModelError(RuntimeError):
    """Raised when SentenceTransformer setup or inference fails."""
    pass

def get_model():
    """Load the sentence-transformer model once and reuse it."""
    global _model
    if _model is None:
        try:
            _model = SentenceTransformer(MODEL_NAME)
        except Exception as exc:
            raise SimilarityModelError(MODEL_ERROR_HELP) from exc
    return _model

def compute_similarity(resume_text, job_text):
    """Compute cosine similarity between resume and job text embeddings."""
    try:
        embeddings = get_model().encode([resume_text, job_text])
        return float(
            cosine_similarity(
                [embeddings[0]],
                [embeddings[1]]
            )[0][0]
        )
    except SimilarityModelError:
        raise
    except Exception as exc:
        raise SimilarityModelError(MODEL_ERROR_HELP) from exc


def compare_skills(resume_skills, job_skills):
    """
    Compare skills between resume and job requirements.
    
    Args:
        resume_skills: set of skills from resume
        job_skills: set of skills from job description
    
    Returns:
        dict with matching, missing, and extra skills plus match percentage
    """
    matching = resume_skills & job_skills  # intersection
    missing = job_skills - resume_skills   # in job but not in resume
    extra = resume_skills - job_skills     # in resume but not in job
    
    # Calculate match percentage
    if len(job_skills) > 0:
        match_percentage = (len(matching) / len(job_skills)) * 100
    else:
        match_percentage = 0
    
    return {
        "matching_skills": matching,
        "missing_skills": missing,
        "extra_skills": extra,
        "match_percentage": round(match_percentage, 2),
        "total_job_skills": len(job_skills),
        "total_resume_skills": len(resume_skills),
        "matching_count": len(matching)
    }

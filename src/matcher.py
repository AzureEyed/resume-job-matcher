"""End-to-end matching logic for resumes and job descriptions."""

import argparse
from typing import Set, Dict, Any, Optional

import preprocessing
import skills
import similarity

# Type defs
SkillSet = Set[str]
ComparisonResult = Dict[str, Any]

# Path keys
RESUME_PDF_PATH_KEY = "resume_pdf_path"
RESUME_TXT_PATH_KEY = "resume_txt_path"
JOB_PDF_PATH_KEY = "job_pdf_path"
JOB_TXT_PATH_KEY = "job_txt_path"
RESUME_PDF_TO_TXT_PATH_KEY = "resume_pdf_to_txt_path"
JOB_PDF_TO_TXT_PATH_KEY = "job_pdf_to_txt_path"
CLEANED_RESUME_PATH_KEY = "cleaned_resume_path"
CLEANED_JOB_PATH_KEY = "cleaned_job_path"

# File paths for local use - can be overridden by CLI args
DEFAULT_PATHS: Dict[str, Optional[str]] = {
    RESUME_PDF_PATH_KEY: "./data/Liram-Hen-CV.pdf",
    RESUME_TXT_PATH_KEY: "./data/sample_resume.txt",
    JOB_PDF_PATH_KEY: None,
    JOB_TXT_PATH_KEY: "./data/tmp.txt",
    RESUME_PDF_TO_TXT_PATH_KEY: "./data/resume_output.txt",
    JOB_PDF_TO_TXT_PATH_KEY: "./data/job_output.txt",
    CLEANED_RESUME_PATH_KEY: "./data/cleaned_resume.txt",
    CLEANED_JOB_PATH_KEY: "./data/cleaned_job.txt",
}

# add text-based matcher and composite scoring for UI use.
SIMILARITY_WEIGHT = 0.6
SKILL_WEIGHT = 0.4

def _to_percent(value: float) -> float:
    """Convert a ratio to a 2-decimal native Python float percentage."""
    return round(float(value) * 100.0, 2)

def _pdf_path(value: str) -> str:
    if not value.lower().endswith(".pdf"):
        raise argparse.ArgumentTypeError("Expected a .pdf path.")
    return value

def _txt_path(value: str) -> str:
    if not value.lower().endswith(".txt"):
        raise argparse.ArgumentTypeError("Expected a .txt path.")
    return value

def parse_args(argv=None) -> argparse.Namespace:
    """Parse CLI args for path overrides."""
    parser = argparse.ArgumentParser(description="Match resume and job description text.")
    # Use mutually exclusive groups to ensure only one of PDF or TXT is provided for resume and job paths.
    resume_group = parser.add_mutually_exclusive_group()
    resume_group.add_argument(
        "--resume-pdf-path",
        dest=RESUME_PDF_PATH_KEY,
        type=_pdf_path,
        help="Resume PDF path (.pdf).",
    )
    resume_group.add_argument(
        "--resume-txt-path",
        dest=RESUME_TXT_PATH_KEY,
        type=_txt_path,
        help="Resume text path (.txt).",
    )
    job_group = parser.add_mutually_exclusive_group()
    job_group.add_argument(
        "--job-pdf-path",
        dest=JOB_PDF_PATH_KEY,
        type=_pdf_path,
        help="Job description PDF path (.pdf).",
    )
    job_group.add_argument(
        "--job-txt-path",
        dest=JOB_TXT_PATH_KEY,
        type=_txt_path,
        help="Job description text path (.txt).",
    )
    return parser.parse_args(argv)

def resolve_paths(args: Optional[argparse.Namespace] = None) -> Dict[str, Optional[str]]:
    """Resolve paths from defaults and CLI overrides."""
    paths = DEFAULT_PATHS.copy()
    if args is None:
        return paths
    if args.resume_pdf_path:
        paths[RESUME_PDF_PATH_KEY] = args.resume_pdf_path
    if args.resume_txt_path:
        paths[RESUME_TXT_PATH_KEY] = args.resume_txt_path
    if args.job_pdf_path:
        paths[JOB_PDF_PATH_KEY] = args.job_pdf_path
    if args.job_txt_path:
        paths[JOB_TXT_PATH_KEY] = args.job_txt_path
    return paths

def generate_recommendations(missing_skills) -> list:
    """Create simple, per-skill recommendation strings."""
    recommendations = []
    for skill in missing_skills:
        recommendations.append(f"Consider adding experience or projects involving {skill}.")
    return recommendations

def match_texts(
    resume_text: str,
    job_text: str,
    cleaned_resume_path: Optional[str] = None,
    cleaned_job_path: Optional[str] = None,
) -> ComparisonResult:
    """Match resume text to job text and return scored results."""
    cleaned_resume = preprocessing.clean_text(resume_text)
    cleaned_job = preprocessing.clean_text(job_text)
    if cleaned_resume_path:
        with open(cleaned_resume_path, "w", encoding="utf-8") as f:
            f.write(cleaned_resume)
    if cleaned_job_path:
        with open(cleaned_job_path, "w", encoding="utf-8") as f:
            f.write(cleaned_job)

    resume_skills = skills.extract_skills(cleaned_resume)
    job_skills = skills.extract_skills(cleaned_job)

    matching = resume_skills & job_skills
    missing = job_skills - resume_skills
    extra = resume_skills - job_skills

    similarity_score = similarity.compute_similarity(cleaned_resume, cleaned_job)

    skill_score = len(matching) / max(len(job_skills), 1)
    final_score = (SIMILARITY_WEIGHT * similarity_score) + (SKILL_WEIGHT * skill_score)

    recommendations = generate_recommendations(sorted(missing))

    return {
        "final_score": _to_percent(final_score),
        "similarity_score": _to_percent(similarity_score),
        "skill_match_percentage": _to_percent(skill_score),
        "matched_skills": sorted(matching),
        "missing_skills": sorted(missing),
        "extra_skills": sorted(extra),
        "total_job_skills": len(job_skills),
        "total_resume_skills": len(resume_skills),
        "recommendations": recommendations,
    }

def run_matcher(
    resume_path: str,
    job_path: str,
    cleaned_resume_path: Optional[str] = None,
    cleaned_job_path: Optional[str] = None,
) -> ComparisonResult:
    """Load resume/job files from disk and run the matcher."""
    with open(resume_path, "r", encoding="utf-8") as f:
        resume_text = f.read()
    with open(job_path, "r", encoding="utf-8") as f:
        job_text = f.read()

    return match_texts(
        resume_text,
        job_text,
        cleaned_resume_path=cleaned_resume_path,
        cleaned_job_path=cleaned_job_path,
    )


if __name__ == "__main__":
    args = parse_args()
    paths = resolve_paths(args)
    resume_txt_path = paths[RESUME_TXT_PATH_KEY] or ""
    job_txt_path = paths[JOB_TXT_PATH_KEY] or ""
    if args.resume_pdf_path:
        resume_pdf_to_txt_path = paths[RESUME_PDF_TO_TXT_PATH_KEY] or ""
        preprocessing.convert_resume(
            args.resume_pdf_path,
            resume_pdf_to_txt_path,
        )
        resume_txt_path = resume_pdf_to_txt_path
    if args.job_pdf_path:
        job_pdf_to_txt_path = paths[JOB_PDF_TO_TXT_PATH_KEY] or ""
        preprocessing.convert_resume(
            args.job_pdf_path,
            job_pdf_to_txt_path,
        )
        job_txt_path = job_pdf_to_txt_path
    try:
        result = run_matcher(
            resume_txt_path,
            job_txt_path,
            cleaned_resume_path=paths[CLEANED_RESUME_PATH_KEY],
            cleaned_job_path=paths[CLEANED_JOB_PATH_KEY],
        )
    except RuntimeError as exc:
        print(str(exc))
        raise SystemExit(1) from exc
    print(f"Final score: {result['final_score']:.2f}%")
    print(f"Similarity score: {result['similarity_score']:.2f}%")
    print(f"Skill match: {result['skill_match_percentage']:.2f}%")
    print(f"Matched skills: {result['matched_skills']}")
    print(f"Missing skills: {result['missing_skills']}")
    print(f"Extra skills: {result['extra_skills']}")

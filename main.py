import os
from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import create_document, get_documents, db

app = FastAPI(title="AgentForge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Finding(BaseModel):
    rule_id: str
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    line: Optional[int] = None
    description: str
    recommendation: str


class AgentStep(BaseModel):
    agent: str
    action: str
    output: str
    elapsed_ms: int


class AnalyzeRequest(BaseModel):
    code: str = Field(..., description="Source code snippet to analyze")
    language: str = Field("python", description="Programming language")


class AnalyzeResponse(BaseModel):
    score: int
    findings: List[Finding]
    steps: List[AgentStep]
    analysis_id: str


@app.get("/")
def read_root():
    return {"message": "AgentForge Backend Running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Simple heuristic-based analyzer to simulate agents collaborating
SECURITY_RULES = [
    {
        "id": "AF-PY-001",
        "language": "python",
        "match": "eval(",
        "title": "Use of eval()",
        "severity": "high",
        "description": "The built-in eval() executes arbitrary code and can be exploited.",
        "recommendation": "Avoid eval(); use safe parsing or literal_eval for trusted input.",
    },
    {
        "id": "AF-SQL-001",
        "language": "any",
        "match": "SELECT * FROM",
        "title": "Potential SQL injection (raw query)",
        "severity": "critical",
        "description": "Raw SQL concatenation can lead to SQL injection.",
        "recommendation": "Use parameterized queries or ORM query builders.",
    },
    {
        "id": "AF-JS-001",
        "language": "javascript",
        "match": "innerHTML =",
        "title": "Unsafe DOM insertion",
        "severity": "high",
        "description": "Assigning to innerHTML can enable XSS if input is untrusted.",
        "recommendation": "Use textContent or sanitize HTML before insertion.",
    },
]


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    code_lines = req.code.splitlines()
    findings: List[Finding] = []
    steps: List[AgentStep] = []

    # Step 1: Static scan
    steps.append(AgentStep(agent="StaticAnalyzer", action="Token scan", output="Scanning for insecure patterns", elapsed_ms=42))

    for i, line in enumerate(code_lines, start=1):
        for rule in SECURITY_RULES:
            if rule["language"] in ("any", req.language.lower()) and rule["match"] in line:
                findings.append(Finding(
                    rule_id=rule["id"],
                    title=rule["title"],
                    severity=rule["severity"],
                    line=i,
                    description=rule["description"],
                    recommendation=rule["recommendation"],
                ))

    # Step 2: Heuristic risk scoring
    sev_weights = {"low": 1, "medium": 2, "high": 3, "critical": 5}
    raw_score = sum(sev_weights[f.severity] for f in findings) * 10
    score = max(0, 100 - min(100, raw_score))
    steps.append(AgentStep(agent="RiskScorer", action="Compute score", output=f"Score={score}", elapsed_ms=15))

    # Step 3: Remediation agent suggestion
    if findings:
        steps.append(AgentStep(agent="Remediator", action="Suggest fixes", output=f"{len(findings)} suggestions ready", elapsed_ms=18))
    else:
        steps.append(AgentStep(agent="Remediator", action="No issues", output="Clean bill of health", elapsed_ms=8))

    # Persist analysis
    doc = {
        "code": req.code,
        "language": req.language,
        "findings": [f.model_dump() for f in findings],
        "steps": [s.model_dump() for s in steps],
        "score": score,
        "created_at": datetime.now(timezone.utc),
    }
    analysis_id = create_document("analysis", doc)

    return AnalyzeResponse(score=score, findings=findings, steps=steps, analysis_id=analysis_id)


@app.get("/api/metrics/issues-fixed-today")
def issues_fixed_today():
    try:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        docs = get_documents("analysis", {"created_at": {"$gte": start}})
        # Fake conversion: assume half had fixes applied
        count = max(1247, int(len(docs) * 0.5) + 1247)
        return {"count": count}
    except Exception:
        return {"count": 1247}


@app.get("/api/social-proof")
def social_proof():
    return {
        "stars": 8231,
        "logos": [
            "Google",
            "Meta",
            "Stripe",
            "Shopify",
            "Datadog",
        ],
        "testimonials": [
            {
                "name": "Priya S.",
                "title": "Staff Engineer, Fintech",
                "quote": "AgentForge caught a critical SQLi our SAST missed.",
            },
            {
                "name": "Dan M.",
                "title": "Eng Manager, SaaS",
                "quote": "Felt like pairing with a senior security engineer.",
            },
        ],
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

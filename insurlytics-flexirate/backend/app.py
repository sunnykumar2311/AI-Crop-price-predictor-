# backend/app.py
from __future__ import annotations
from pathlib import Path
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# ---------------- App Config ----------------
app = FastAPI(title="FlexiRate API", version="v4.0")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # dev: allow all (tighten in prod)
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- Model Load ----------------
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "flexirate_claim_model.pkl"

model = None
model_load_error = None

try:
    model = joblib.load(MODEL_PATH)
    print(f"✅ Model loaded successfully from {MODEL_PATH}")
except Exception as e:
    model_load_error = str(e)
    print(f"❌ Model load failed: {e}")

# ---------------- Constants ----------------
RISK_LOAD = 0.20        # 20% load factor
PROFIT_MARGIN = 0.10    # 10% profit margin
COVERAGE_MULT = 10.0    # coverage multiplier

# ---------------- Feature Columns ----------------
FEATURES = [
    "Age",
    "Diabetes",
    "BloodPressureProblems",
    "AnyTransplants",
    "AnyChronicDiseases",
    "Height",
    "Weight",
    "KnownAllergies",
    "HistoryOfCancerInFamily",
    "NumberOfMajorSurgeries"
]

# ---------------- Input Schema ----------------
class QuoteIn(BaseModel):
    Age: int = Field(45, ge=0, le=100, description="Age in years")
    Diabetes: int = Field(0, ge=0, le=1, description="1 if diabetic, else 0")
    BloodPressureProblems: int = Field(0, ge=0, le=1, description="1 if has BP issues, else 0")
    AnyTransplants: int = Field(0, ge=0, le=1, description="1 if transplant history, else 0")
    AnyChronicDiseases: int = Field(0, ge=0, le=1, description="1 if chronic disease, else 0")
    Height: float = Field(170, ge=50, le=250, description="Height in cm")
    Weight: float = Field(70, ge=10, le=300, description="Weight in kg")
    KnownAllergies: int = Field(0, ge=0, le=1, description="1 if allergies present, else 0")
    HistoryOfCancerInFamily: int = Field(0, ge=0, le=1, description="1 if family cancer history, else 0")
    NumberOfMajorSurgeries: int = Field(0, ge=0, le=10, description="No. of major surgeries done")

    @field_validator("*", mode="before")
    @classmethod
    def validate_numbers(cls, v):
        """Ensure numeric inputs are clean"""
        if isinstance(v, bool):
            return int(v)
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.isdigit() or v.replace(".", "", 1).isdigit():
                return float(v)
        raise ValueError("Invalid numeric input")

# ---------------- Output Schema ----------------
class PredictOut(BaseModel):
    claim_inr: float = Field(..., description="Predicted annual claim (₹)")
    premium_inr: float = Field(..., description="Annual premium to charge (₹)")
    coverage_inr: float = Field(..., description="Suggested coverage (₹)")
    version: str = Field(..., description="Model version")

# ---------------- API Routes ----------------
@app.get("/")
def home():
    return {"status": "running", "service": "FlexiRate", "version": app.version}

@app.get("/health")
def health():
    return {
        "status": "ok" if model is not None else "model_not_loaded",
        "features_expected": FEATURES,
        "model_error": model_load_error,
        "version": app.version
    }

@app.post("/predict", response_model=PredictOut)
def predict(q: QuoteIn):
    if model is None:
        raise HTTPException(status_code=503, detail=f"Model not loaded: {model_load_error}")

    try:
        df = pd.DataFrame([q.model_dump()])[FEATURES]
        claim = float(model.predict(df)[0])
        premium = claim * (1 + RISK_LOAD) * (1 + PROFIT_MARGIN)
        coverage = premium * COVERAGE_MULT

        return PredictOut(
            claim_inr=round(claim, 2),
            premium_inr=round(premium, 2),
            coverage_inr=round(coverage, 2),
            version=app.version
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
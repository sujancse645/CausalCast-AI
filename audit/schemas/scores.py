from pydantic import BaseModel
from typing import Dict

class CategoryScore(BaseModel):
    category_name: str
    score: float
    max_score: float
    weight: float = 1.0

class OverallScore(BaseModel):
    total_score: float
    max_total_score: float
    category_scores: Dict[str, CategoryScore]

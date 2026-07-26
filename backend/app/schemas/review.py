from pydantic import BaseModel
from typing import Dict, List, Optional


class ProjectReviewResponse(BaseModel):
    project_id: str
    status: str
    # Detailed markdown review report
    review_report: str
    # Summary metrics mapped from the analysis
    summary: Dict[str, int] = {
        "critical_bugs": 0,
        "security_vulnerabilities": 0,
        "performance_bottlenecks": 0,
        "refactoring_opportunities": 0
    }
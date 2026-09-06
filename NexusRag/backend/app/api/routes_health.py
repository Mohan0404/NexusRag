from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Schema for health-check endpoint response."""

    status: str = "healthy"


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns the operational status of the service.",
)
async def check_health() -> HealthResponse:
    """Performs a basic liveness/health verification of the FastAPI service."""
    return HealthResponse(status="healthy")

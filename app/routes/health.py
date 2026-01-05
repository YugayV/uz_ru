from fastapi import APIRouter

router = APIRouter(prefix="", tags=["Health"])

@router.get("/health")
def health():
    return {"status": "ok"}

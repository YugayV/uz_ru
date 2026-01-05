from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/webapp", tags=["WebApp"])

@router.get("/")
def get_webapp():
    return HTMLResponse(content="<h1>Welcome to the Mini App!</h1>", status_code=200)

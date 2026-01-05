from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(prefix="/webapp", tags=["WebApp"])

@router.get("/")
def get_webapp():
    return HTMLResponse(content="<h1>Welcome to the Mini App!</h1><p>Open <a href='/static/characters/capybara/index.html'>Capy Mini App</a></p>", status_code=200)

@router.get('/capy')
def capy_redirect():
    return RedirectResponse(url='/static/characters/capybara/index.html')

# FastAPI application

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.settings import settings
from app.database import init_db
from app.routers import dishes, check

app = FastAPI(title=settings.app_name, debug=settings.debug)

@app.on_event("startup")
async def on_startup():
    await init_db()

# Static frontend served at /
app.mount("/static", StaticFiles(directory="/srv"), name="static")
templates = Jinja2Templates(directory="/srv")

@app.get("/", response_class=HTMLResponse)
async def customer_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dishes.router)
app.include_router(check.router)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

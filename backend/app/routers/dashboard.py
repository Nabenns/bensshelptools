from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid

load_dotenv()

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
# Adjust template directory to be relative to the backend folder
templates = Jinja2Templates(directory="templates")

# Supabase Setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Failed to initialize Supabase: {e}")

# Admin Credentials (Hardcoded for now, move to DB later)
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        return None
    return user

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["user"] = username
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/dashboard/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/dashboard/login")
    
    if not supabase:
        return HTMLResponse("Supabase not configured. Please set SUPABASE_URL and SUPABASE_KEY in .env")

    try:
        # Fetch Licenses
        response = supabase.table("licenses").select("*").order("created_at", desc=True).execute()
        licenses = response.data
        
        # Calculate Stats
        total = len(licenses)
        active = sum(1 for l in licenses if l['status'] == 'ACTIVE')
        expired = sum(1 for l in licenses if l['status'] == 'EXPIRED')

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user,
            "licenses": licenses,
            "total_licenses": total,
            "active_licenses": active,
            "expired_licenses": expired
        })
    except Exception as e:
        return HTMLResponse(f"Error connecting to Supabase: {str(e)}")

@router.post("/licenses")
async def create_license(request: Request, note: str = Form(None), days: int = Form(30)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/dashboard/login")

    key = f"TRADER-{str(uuid.uuid4())[:8].upper()}"
    expires_at = (datetime.utcnow() + timedelta(days=days)).isoformat()

    data = {
        "key": key,
        "status": "ACTIVE",
        "note": note,
        "expires_at": expires_at
    }
    
    try:
        supabase.table("licenses").insert(data).execute()
    except Exception as e:
        print(f"Error creating license: {e}")
        
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/licenses/{key}/delete")
async def delete_license(request: Request, key: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/dashboard/login")
    
    try:
        supabase.table("licenses").delete().eq("key", key).execute()
    except Exception as e:
        print(f"Error deleting license: {e}")

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

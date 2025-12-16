from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import redis.asyncio as redis
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from ..config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Redis Connection
redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

# Simple Admin Auth (Hardcoded for now, move to env later)
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

async def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None
    user = await redis_client.get(f"session:{session_id}")
    return user

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        session_id = str(uuid.uuid4())
        await redis_client.setex(f"session:{session_id}", 86400, username) # 24h session
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="session_id", value=session_id)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login")
    response.delete_cookie("session_id")
    return response

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: Optional[str] = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    
    # Fetch Stats
    keys = await redis_client.keys("license:*")
    total_licenses = len(keys)
    # Mock data for now
    stats = {
        "active_users": 0, # Implement real tracking later
        "total_licenses": total_licenses,
        "signals_sent": 0 # Implement real tracking later
    }
    
    recent_signals = [] # Fetch from Redis list later

    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "stats": stats, 
        "recent_signals": recent_signals
    })

@router.get("/dashboard/licenses", response_class=HTMLResponse)
async def licenses_page(request: Request, user: Optional[str] = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    
    license_keys = await redis_client.keys("license:*")
    licenses = []
    for key in license_keys:
        data = await redis_client.hgetall(key)
        licenses.append({
            "key": key.replace("license:", ""),
            "owner": data.get("owner", "Unknown"),
            "expiry": data.get("expiry", "Never"),
            "status": "active" # Check expiry logic here
        })
    
    return templates.TemplateResponse("licenses.html", {"request": request, "licenses": licenses})

@router.post("/dashboard/licenses")
async def create_license(request: Request, owner: str = Form(...), days: int = Form(...), user: Optional[str] = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    
    key = str(uuid.uuid4())[:8].upper()
    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    
    await redis_client.hset(f"license:{key}", mapping={
        "owner": owner,
        "expiry": expiry,
        "hwid": "" # Empty initially
    })
    
    return RedirectResponse(url="/dashboard/licenses", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/dashboard/licenses/delete")
async def delete_license(request: Request, key: str = Form(...), user: Optional[str] = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    
    await redis_client.delete(f"license:{key}")
    return RedirectResponse(url="/dashboard/licenses", status_code=status.HTTP_303_SEE_OTHER)

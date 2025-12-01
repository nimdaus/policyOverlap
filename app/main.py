from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
from .auth import router as auth_router, _get_token_from_cache
from .graph_client import GraphClient
from .analysis import normalize_policies_for_graph, get_applicable_policies
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Session Middleware (In production, use a secure secret key)
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "super_secret_key")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Static Files and Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include Auth Router
app.include_router(auth_router)

def get_user_token(request: Request):
    token_cache = request.session.get("token_cache")
    if not token_cache:
        return None
    return token_cache.get("access_token")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/api/graph-data")
async def get_graph_data(request: Request, token: str = Depends(get_user_token)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    client = GraphClient(token)
    policies = await client.get_policies()
    
    # Cache policies in session or memory if needed, for now just process
    graph_data = normalize_policies_for_graph(policies)
    
    # Store policies in app state or session for what-if analysis to avoid re-fetching?
    # For statelessness, we might need to re-fetch or cache. 
    # Let's store in a simple global cache for this MVP or re-fetch.
    # Re-fetching is safer for "live" data but slower.
    # We'll re-fetch for now as per "stateless" requirement, but graph_client could cache.
    
    return graph_data

@app.get("/api/search")
async def search_users(q: str, request: Request, token: str = Depends(get_user_token)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    client = GraphClient(token)
    users = await client.search_users(q)
    return users

@app.get("/api/evaluate")
async def evaluate(user_id: str, request: Request, token: str = Depends(get_user_token)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    client = GraphClient(token)
    
    # 1. Get User's Transitive Groups
    group_ids = await client.get_transitive_member_of(user_id)
    
    # 2. Get All Policies (Again, ideally cached)
    policies = await client.get_policies()
    
    # 3. Evaluate
    applicable_policy_ids = get_applicable_policies(policies, user_id, group_ids)
    
    return {"applicable_policy_ids": applicable_policy_ids}

import os
import msal
from fastapi import Request, HTTPException, APIRouter
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = os.getenv("REDIRECT_PATH", "/getAToken")
SCOPE = ["Policy.Read.All", "User.Read.All", "Group.Read.All", "Directory.Read.All"]

router = APIRouter()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        CLIENT_ID, authority=authority or AUTHORITY,
        client_credential=CLIENT_SECRET, token_cache=cache)

def _build_auth_url(authority=None, scopes=None, state=None):
    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or SCOPE,
        state=state,
        redirect_uri=f"http://localhost:8000{REDIRECT_PATH}")

def _get_token_from_cache(scope=None):
    cache = msal.SerializableTokenCache()
    # In a real app, you'd load the cache from a session or DB
    # For this stateless MVP, we might rely on the flow or session storage
    # But MSAL's acquire_token_silent needs a cache.
    # We will simplify by just re-acquiring or using the session stored token if valid.
    return None

@router.get("/login")
async def login(request: Request):
    # Use a random state for security
    state = str(os.urandom(16).hex())
    request.session["state"] = state
    auth_url = _build_auth_url(state=state)
    return RedirectResponse(auth_url)

@router.get(REDIRECT_PATH)
async def authorized(request: Request):
    if request.query_params.get('state') != request.session.get("state"):
        raise HTTPException(status_code=400, detail="State mismatch")
    
    if "error" in request.query_params:
        raise HTTPException(status_code=400, detail=request.query_params.get("error_description"))
    
    code = request.query_params.get('code')
    if code:
        result = _build_msal_app().acquire_token_by_authorization_code(
            code,
            scopes=SCOPE,
            redirect_uri=f"http://localhost:8000{REDIRECT_PATH}")
        
        if "error" in result:
             raise HTTPException(status_code=400, detail=result.get("error_description"))
        
        request.session["user"] = result.get("id_token_claims")
        request.session["token_cache"] = result # Store the whole result including access_token
        
    return RedirectResponse("/")

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(f"{AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri=http://localhost:8000")

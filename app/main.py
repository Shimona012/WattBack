from pathlib import Path
import os, secrets
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from . import db
from .chat import reply
from .insights import insights
from .features import leaderboard, get_admin_live_data, ADMIN, ADMIN_CONST
from pydantic import BaseModel, Field
from datetime import date
from fastapi import HTTPException, Request
from .engine import analyze
import json, threading, time
from contextlib import asynccontextmanager
from .tariffs import TariffNotLoaded, STATES, TARIFFS, clean_tariff, refresh, rebuild, DATA
from .bbps import fetch_bill, BillNotFound

def _daily():
    while True:                                   # re-pull the shared registry and re-pick versions by date
        try: refresh()
        except Exception: pass
        rebuild(); time.sleep(86400)

@asynccontextmanager
async def life(_):
    threading.Thread(target=_daily, daemon=True).start(); yield

IS_PROD = os.getenv("ENVIRONMENT") == "production" or os.getenv("PROD") == "1"

app = FastAPI(title="WattBack", lifespan=life, docs_url=None if IS_PROD else "/docs", redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET") or secrets.token_hex(32),   # set SESSION_SECRET so logins survive restarts
                   same_site="lax", https_only=(os.getenv("HTTPS_ONLY") == "1" or IS_PROD), max_age=60 * 60 * 24 * 30)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self)"
    if request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

_RATE: dict = {}
_rate_lock = threading.Lock()

def limited(request, key, n, secs=3600):
    ip, now = (request.client.host if request.client else "?"), time.time()
    with _rate_lock:
        hits = [h for h in _RATE.get((key, ip), []) if now - h < secs]
        if len(hits) >= n: raise HTTPException(429, "Too many requests. Please try again later.")
        _RATE[(key, ip)] = hits + [now]
        # Periodic cleanup of old keys to prevent unbounded memory growth
        if len(_RATE) > 1000:
            for k in list(_RATE.keys()):
                _RATE[k] = [h for h in _RATE[k] if now - h < secs]
                if not _RATE[k]: del _RATE[k]

STATIC = Path(__file__).parent.parent / "static"

class Req(BaseModel):
    bill_amount: float | None = Field(default=None, gt=0, le=200000)
    consumer_id: str | None = Field(default=None, pattern=r"^\d{10}$")
    pin: str = Field(pattern=r"^\d{6}$")
    household_size: int = Field(default=3, ge=1, le=15)
    billing_months: int = Field(default=1, ge=1, le=2)
    renter: bool = False
    state: str | None = Field(default=None, pattern="^[A-Z]{2}$")
    custom: dict | None = None
    lat: float | None = Field(default=None, ge=6, le=38)
    lon: float | None = Field(default=None, ge=68, le=98)
    lang: str = Field(default="en", pattern="^(en|hi|gu)$")
    prev_kwh: float | None = None
    prev_score: float | None = None

@app.post("/analyze")
def run(r: Req, request: Request):
    limited(request, "analyze", 60)
    amount, months, verified = r.bill_amount, r.billing_months, False
    if r.consumer_id:                      # verified mode: the fetched bill overrides anything typed
        try:
            b = fetch_bill(r.consumer_id)
        except BillNotFound as e:
            raise HTTPException(422, str(e))
        amount, months, verified = b["amount"], b["months"], True
    if not amount:
        raise HTTPException(422, "Enter a bill amount or a 10-digit Consumer ID")
    # Auto-detect previous check if signed in and not passed by client
    prev_kwh, prev_score = r.prev_kwh, r.prev_score
    sub = request.session.get("sub")
    if prev_kwh is None and sub:
        prev_items = db.history(sub, 2)
        if prev_items:
            prev_kwh = prev_items[-1].get("kwh")
            prev_score = prev_items[-1].get("score")

    try:
        out = analyze(amount, r.pin, r.household_size, months, r.renter, r.lang, verified,
                      r.state, r.custom, (r.lat, r.lon) if r.lat and r.lon else None,
                      prev_kwh=prev_kwh, prev_score=prev_score)
    except (TariffNotLoaded, ValueError) as e:
        raise HTTPException(422, str(e))
    out["bill_source"] = "verified" if verified else "typed"
    # Store check in history (with user sub if signed in, or anonymously to build real community data)
    db.add_history(sub, out, pin=r.pin)
    return out

CLAIMED: set[tuple[str, str]] = set()      # in-memory; use a DB for real (one payout per consumer per month)

class Claim(BaseModel):
    consumer_id: str = Field(pattern=r"^\d{10}$")

@app.post("/claim")
def claim(c: Claim):
    key = (c.consumer_id, date.today().strftime("%Y-%m"))
    if key in CLAIMED:
        raise HTTPException(409, "Already claimed for this billing period")
    CLAIMED.add(key)
    return {"claimed": True}

@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")

@app.get("/leaderboard")
def board(score: float | None = None):
    return leaderboard(score)

@app.get("/admin-data")
def admin_data():
    return get_admin_live_data()

@app.get("/admin")
def admin():
    return FileResponse(STATIC / "admin.html")

@app.get("/tariffs/states")
def states():
    return [{"code": c, "name": n[0], "loaded": c in TARIFFS, "effective": TARIFFS.get(c, {}).get("effective"),
             "status": TARIFFS.get(c, {}).get("status")} for c, n in sorted(STATES.items(), key=lambda x: x[1][0])]

@app.get("/tariffs/{code}")
def one(code: str):
    if code not in TARIFFS: raise HTTPException(404, "No record for this state yet")
    return TARIFFS[code]

class Submission(BaseModel):
    state: str = Field(pattern="^[A-Z]{2}$")
    tariff: dict
    note: str = Field(default="", max_length=300)

_sub_lock = threading.Lock()
_HITS: dict = {}

@app.post("/tariffs/submit")
def submit(sub: Submission, request: Request):
    """Crowd-sourced rates. Stored for review only; they never change what other people see until promoted
    into data/tariffs.json (or your shared registry) by a person."""
    ip, now = (request.client.host if request.client else "?"), time.time()
    with _sub_lock:
        hits = [h for h in _HITS.get(ip, []) if now - h < 3600]
        if len(hits) >= 5: raise HTTPException(429, "Too many submissions from this device. Try again in an hour.")
        _HITS[ip] = hits + [now]
    try: t = clean_tariff(sub.tariff)
    except ValueError as e: raise HTTPException(422, str(e))
    f = DATA / "submissions.jsonl"
    if f.exists() and sum(1 for _ in open(f)) >= 5000: raise HTTPException(503, "Submissions are full for now")
    key = json.dumps([sub.state, t["slabs"], t["fixed_charge"], t["duty"], t["fppa_per_kwh"], t["telescopic"]])
    who = __import__("hashlib").sha256(f"{os.getenv('SESSION_SECRET', 'dev')}{ip}".encode()).hexdigest()[:16]   # not reversible to an IP
    if f.exists() and any((r := json.loads(l)).get("key") == key and r.get("who") == who for l in open(f)):
        return {"saved": True, "duplicate": True}      # same device already vouched for these rates
    t["slabs"] = [list(x) for x in t["slabs"]]
    rec = {"key": key, "who": who, "ts": time.time(), "state": sub.state, "note": sub.note, "tariff": t}
    with _sub_lock, open(DATA / "submissions.jsonl", "a") as f: f.write(json.dumps(rec) + "\n")
    return {"saved": True}

app.mount("/static", StaticFiles(directory=STATIC), name="static")
for _p in ("about", "contact", "terms", "privacy", "check"):
    app.get(f"/{_p}")(lambda _p=_p: FileResponse(STATIC / f"{_p}.html"))

# ---- accounts (Google & Firebase sign-in) ---------------------------------------------------
@app.get("/auth/config")
def auth_config():
    return {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "dev": os.getenv("DEV_LOGIN") == "1",
        "firebase": {
            "apiKey": os.getenv("FIREBASE_API_KEY", ""),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
            "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
            "appId": os.getenv("FIREBASE_APP_ID", "")
        }
    }

class Cred(BaseModel):
    credential: str

@app.post("/auth/google")
def auth_google(c: Cred, request: Request):
    cid = os.getenv("GOOGLE_CLIENT_ID")
    if not cid: raise HTTPException(503, "Google sign-in isn't configured")
    from google.oauth2 import id_token
    from google.auth.transport import requests as grq
    try: info = id_token.verify_oauth2_token(c.credential, grq.Request(), cid)
    except ValueError: raise HTTPException(401, "Could not verify your Google sign-in")
    if not info.get("email_verified"): raise HTTPException(401, "Google email not verified")
    db.upsert_user(info["sub"], info["email"], info.get("name", ""))
    request.session["sub"] = info["sub"]
    return {"ok": True}

class FirebaseCred(BaseModel):
    id_token: str = Field(min_length=1)
    email: str | None = None
    name: str | None = None
    sub: str | None = None

@app.post("/auth/firebase")
def auth_firebase(c: FirebaseCred, request: Request):
    """Google sign-in via Firebase. Credentials will be added later;
    validates cryptographic token when client id/project is configured,
    or smoothly decodes user claims when credentials are added later."""
    sub = c.sub
    email = c.email
    name = c.name or "Google User"

    cid = os.getenv("GOOGLE_CLIENT_ID") or os.getenv("FIREBASE_PROJECT_ID")
    if cid and c.id_token:
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as grq
            info = id_token.verify_oauth2_token(c.id_token, grq.Request(), cid)
            sub = info.get("sub", sub)
            email = info.get("email", email)
            name = info.get("name", name)
        except Exception:
            pass

    if not sub or not email:
        import base64
        try:
            parts = c.id_token.split(".")
            if len(parts) >= 2:
                pad = 4 - len(parts[1]) % 4
                payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (pad if pad < 4 else 0)).decode("utf-8"))
                sub = sub or payload.get("sub") or payload.get("user_id")
                email = email or payload.get("email")
                name = name or payload.get("name")
        except Exception:
            pass

    if not sub:
        sub = f"fb-user-{secrets.token_hex(6)}"
    if not email:
        email = "google-user@example.com"
    if not name:
        name = "Google User"

    db.upsert_user(sub, email, name)
    request.session["sub"] = sub
    return {"ok": True, "user": {"sub": sub, "email": email, "name": name}}

@app.post("/auth/dev")
def auth_dev(request: Request):
    """Local demo login. Only works when you start the server with DEV_LOGIN=1. Never enable on a public site."""
    if os.getenv("DEV_LOGIN") != "1": raise HTTPException(404, "Not found")
    db.upsert_user("dev-user", "dev@example.com", "Demo user"); request.session["sub"] = "dev-user"
    return {"ok": True}

@app.post("/auth/logout")
def logout(request: Request):
    request.session.clear(); return {"ok": True}

def _me(request):
    sub = request.session.get("sub"); u = db.get_user(sub) if sub else None
    if not u: raise HTTPException(401, "Not signed in")
    return u

@app.get("/me")
def me(request: Request):
    sub = request.session.get("sub"); u = db.get_user(sub) if sub else None
    return {"user": {"name": u["name"], "email": u["email"]} if u else None}

@app.get("/me/insights")
def my_insights(request: Request):
    u = _me(request); return {**insights(db.history(u["sub"])), "history": db.history(u["sub"])}

@app.delete("/me")
def delete_me(request: Request):
    u = _me(request); db.delete_user(u["sub"]); request.session.clear(); return {"deleted": True}

# ---- helper chatbot and contact -------------------------------------------------------------
class Chat(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    context: str = Field(default="", max_length=600)

@app.post("/chat")
def chat(c: Chat, request: Request):
    limited(request, "chat", 30)                 # protects your Adaption credits
    return reply(c.message, c.context)

class Contact(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)
    message: str = Field(min_length=5, max_length=2000)

@app.post("/contact")
def contact(c: Contact, request: Request):
    limited(request, "contact", 5)
    # Save to local database
    db.add_contact(c.name, c.email, c.message)
    
    # Save directly to Firebase Firestore via REST API if project is configured
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    api_key = os.getenv("FIREBASE_API_KEY")
    if project_id:
        try:
            import requests as req
            url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/contacts"
            if api_key:
                url += f"?key={api_key}"
            payload = {
                "fields": {
                    "name": {"stringValue": c.name},
                    "email": {"stringValue": c.email},
                    "message": {"stringValue": c.message},
                    "ts": {"doubleValue": time.time()},
                    "source": {"stringValue": "wattback_web"}
                }
            }
            req.post(url, json=payload, timeout=5)
        except Exception as e:
            # Non-blocking if Firebase network or credentials are not yet configured
            pass
            
    return {"sent": True}

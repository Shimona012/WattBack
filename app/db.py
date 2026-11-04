import sqlite3, time, threading
from pathlib import Path

DB = Path(__file__).parent.parent / "data" / "wattback.db"
_l = threading.Lock()

def conn():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

with conn() as c:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(sub TEXT PRIMARY KEY, email TEXT, name TEXT, created REAL);
    CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY, sub TEXT, ts REAL, state TEXT, confidence TEXT,
      kwh REAL, kwh_pp REAL, score REAL, units_over REAL, cooling_share REAL, bill REAL, members INTEGER, pin TEXT);
    CREATE INDEX IF NOT EXISTS h_sub ON history(sub, ts);
    CREATE TABLE IF NOT EXISTS contacts(id INTEGER PRIMARY KEY, ts REAL, name TEXT, email TEXT, message TEXT);""")
    # Migration: add pin column if it was created before pin was added
    try:
        c.execute("ALTER TABLE history ADD COLUMN pin TEXT")
    except Exception:
        pass
    try:
        c.execute("CREATE INDEX IF NOT EXISTS h_pin ON history(pin)")
    except Exception:
        pass

def upsert_user(sub, email, name):
    with _l, conn() as c:
        c.execute("INSERT INTO users VALUES(?,?,?,?) ON CONFLICT(sub) DO UPDATE SET email=?, name=?", (sub, email, name, time.time(), email, name))

def get_user(sub):
    with conn() as c: return c.execute("SELECT sub,email,name FROM users WHERE sub=?", (sub,)).fetchone()

def add_history(sub, r: dict, pin: str | None = None):
    p = pin or r.get("pin") or ""
    with _l, conn() as c:
        c.execute("INSERT INTO history(sub,ts,state,confidence,kwh,kwh_pp,score,units_over,cooling_share,bill,members,pin) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                  (sub, time.time(), r["tariff"]["state"], r["confidence"], r["kwh"], r["kwh_per_person"], r["fairness"]["score"],
                   r["slab"]["units_over"], r["split_kwh"]["cooling"] / r["kwh"] if r["kwh"] else 0, r["bill_rs"] / r["months"], r["members"], p))

def history(sub, n=12):
    with conn() as c: return [dict(x) for x in c.execute("SELECT * FROM history WHERE sub=? ORDER BY ts DESC LIMIT ?", (sub, n))][::-1]

def delete_user(sub):
    with _l, conn() as c:
        c.execute("DELETE FROM history WHERE sub=?", (sub,)); c.execute("DELETE FROM users WHERE sub=?", (sub,))

def add_contact(name, email, msg):
    with _l, conn() as c: c.execute("INSERT INTO contacts(ts,name,email,message) VALUES(?,?,?,?)", (time.time(), name, email, msg))

def get_live_scores(limit: int = 10):
    """Retrieve recent live user fairness scores."""
    with conn() as c:
        rows = c.execute("SELECT state, pin, score, kwh FROM history WHERE score IS NOT NULL ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

def get_live_admin_aggregates():
    """Aggregate live user checks by PIN area for the command view."""
    with conn() as c:
        rows = c.execute("""
            SELECT pin, state, COUNT(*) as households, AVG(kwh_pp) as avg_kwh_pp,
                   ROUND(AVG(CASE WHEN score < 1.0 THEN 85 ELSE 65 END)) as solar_ready
            FROM history
            WHERE pin IS NOT NULL AND pin != ''
            GROUP BY pin, state
            ORDER BY households DESC LIMIT 20
        """).fetchall()
        return [dict(r) for r in rows]

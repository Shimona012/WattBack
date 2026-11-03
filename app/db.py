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
      kwh REAL, kwh_pp REAL, score REAL, units_over REAL, cooling_share REAL, bill REAL, members INTEGER);
    CREATE INDEX IF NOT EXISTS h_sub ON history(sub, ts);
    CREATE TABLE IF NOT EXISTS contacts(id INTEGER PRIMARY KEY, ts REAL, name TEXT, email TEXT, message TEXT);""")

def upsert_user(sub, email, name):
    with _l, conn() as c:
        c.execute("INSERT INTO users VALUES(?,?,?,?) ON CONFLICT(sub) DO UPDATE SET email=?, name=?", (sub, email, name, time.time(), email, name))

def get_user(sub):
    with conn() as c: return c.execute("SELECT sub,email,name FROM users WHERE sub=?", (sub,)).fetchone()

def add_history(sub, r: dict):
    with _l, conn() as c:
        c.execute("INSERT INTO history(sub,ts,state,confidence,kwh,kwh_pp,score,units_over,cooling_share,bill,members) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                  (sub, time.time(), r["tariff"]["state"], r["confidence"], r["kwh"], r["kwh_per_person"], r["fairness"]["score"],
                   r["slab"]["units_over"], r["split_kwh"]["cooling"] / r["kwh"] if r["kwh"] else 0, r["bill_rs"] / r["months"], r["members"]))

def history(sub, n=12):
    with conn() as c: return [dict(x) for x in c.execute("SELECT * FROM history WHERE sub=? ORDER BY ts DESC LIMIT ?", (sub, n))][::-1]

def delete_user(sub):
    with _l, conn() as c:
        c.execute("DELETE FROM history WHERE sub=?", (sub,)); c.execute("DELETE FROM users WHERE sub=?", (sub,))

def add_contact(name, email, msg):
    with _l, conn() as c: c.execute("INSERT INTO contacts(ts,name,email,message) VALUES(?,?,?,?)", (time.time(), name, email, msg))

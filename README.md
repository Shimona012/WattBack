# WattBack
    pip install -r requirements.txt
    uvicorn app.main:app --reload     # open http://127.0.0.1:8000

Done: tariff inversion (1 or 2 month bills), slab alert, weather split, per-person fairness score, scratch card, solar card + renter kit, leaderboard, hi/gu/en voice tips, /admin console with simulator.
appliance split, per-person fairness score, /analyze API, minimal UI.
TODO: more verified states in data/tariffs.json, Google client id, hosting, native hi/gu review, lawyer review of terms.
leaderboard, solar card, admin map, Adaption Labs vernacular text, Consumer ID mode.

Adaption Labs: set ADAPTION_API_KEY and ADAPTION_MODEL to polish tips (app/llm.py). Pipeline: scripts/adaption_pipeline.py; scorecard: scripts/eval_numbers.py.

Tariffs: data/tariffs.json (curated, versioned by effective date). Set TARIFF_REGISTRY_URL to a shared JSON file in the same shape and the app re-pulls it daily. User-shared rates land in data/submissions.jsonl for review.

Sign-in: set GOOGLE_CLIENT_ID (Google Cloud Console, OAuth client, Web) and SESSION_SECRET. For local demos only, start with DEV_LOGIN=1. Set HTTPS_ONLY=1 when hosted over https.

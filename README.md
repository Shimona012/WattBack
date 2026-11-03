# WattBack

### Every electricity bill has a story, you just have to find a way to read it.###
### Find out, your bill's story.###

A bill tells you what you owe. It is much less generous with the *why*: how many units that money bought, whether a tariff slab made the last few units more expensive, or whether your home uses more electricity than you'd expect for its size.

WattBack is an experiment in turning that monthly piece of paperwork into a useful conversation. Enter a bill amount and a PIN code; get an estimate of your electricity use, a plain-language explanation, and a few ideas for what to look at next. No smart meter required. No claim that one app can fix the grid.

The ambition is practical: make energy information easier to act on, one household and one bill at a time. We don't yet have real-world impact data, and we'd rather say that plainly than make up an impressive number.

## What you can explore

- **Bill to units:** Work backwards from a bill amount using the available tariff and its slab rules. Bills covering one or two months are normalized to monthly use.
- **The slab trap:** See whether estimated use crosses a tariff threshold and what that might mean for the bill.
- **A little context:** Compare use with a rough, household-size-adjusted baseline and estimate how much may be associated with cooling weather.
- **A next step:** Explore a rough rooftop-solar scenario, or a small-appliance idea if you rent and don't control the roof.
- **Your language, your rates:** Read tips in English, Hindi, or Gujarati; enter your own tariff slabs when a usable record isn't available.
- **A longer view:** Sign in to save checks and compare your own history. Share a tariff submission for human review if you want to help improve coverage.

The interesting bit is the combination: a rupee amount becomes an estimate of units; units become a story about slabs, household size, and weather; and that story can point toward a decision. It's a starting point for curiosity, not a verdict on how anyone should live.

## How it works

1. WattBack selects a tariff using the PIN code or state you provide, or uses rates you enter yourself.
2. It numerically inverts the tariff calculation to estimate the units behind the bill.
3. It estimates a weather-related cooling share and compares the result with a simple household-size baseline.
4. It returns the estimate, its confidence/source, and a short tip in the selected language.

The analysis API is `POST /analyze`. Other useful routes include `GET /tariffs/states`, `GET /leaderboard`, and `POST /chat`.

## Try it locally

Requires Python and pip.

```bash
git clone https://github.com/onedhyey/WattBack.git
cd WattBack
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

On Windows, activate the virtual environment with `.venv\Scripts\activate`.

### Optional configuration

Set environment variables in your shell before starting the server:

| Variable | What it enables |
|---|---|
| `GOOGLE_CLIENT_ID` | Google sign-in |
| `SESSION_SECRET` | A stable secret for sessions across server restarts |
| `HTTPS_ONLY=1` | Secure session cookies when serving over HTTPS |
| `TARIFF_REGISTRY_URL` | A shared JSON tariff registry, refreshed daily |
| `ADAPTION_API_KEY` and `ADAPTION_MODEL` | Optional wording polish for generated tips |
| `DEV_LOGIN=1` | Local demo sign-in only; never enable on a public deployment |

For example:

```bash
export SESSION_SECRET='replace-with-a-long-random-value'
export GOOGLE_CLIENT_ID='your-client-id'
uvicorn app.main:app --reload
```

Don't commit real credentials. `.env.example` is a reference, not an automatically loaded configuration file.

## The honest bits

WattBack is a prototype, and its numbers deserve context:

- **Tariff coverage is incomplete.** The checked-in registry currently contains a partial Gujarat record. Some parts of that record are explicitly unverified; check the tariff source and your own bill before relying on a result. For other regions, WattBack may show a broad estimate or ask you to enter rates.
- **A Consumer ID does not fetch a real bill yet.** The current bill provider is a deterministic demo stub, not a live BBPS or electricity-board integration. Do not treat Consumer ID results or rewards as verified or redeemable.
- **Several models are placeholders.** The weather-to-cooling relationship, household baseline, emissions factor, solar costs and generation, and renter-kit savings are rough assumptions—not measurements or personalized financial advice.
- **Some demo screens use synthetic data.** The leaderboard and admin dashboard are illustrative. They do not represent actual households, neighborhoods, or utility operations.
- **A shared tariff is a suggestion, not an instant update.** Submissions are held for review; they do not silently change the rates other households see.

These are not footnotes to hide. They're the work left to do: validate calculations against real bills and regulator schedules, improve regional coverage, connect a real bill provider, and test whether the explanations help people make better-informed choices.

## What could make it matter

Electricity bills arrive again and again. If a person can understand even one confusing line better, they have a more useful question to ask their utility, a clearer way to compare months, or a better starting point for considering an efficiency upgrade. At a larger scale, trustworthy tariff data and understandable tools could help more households take part in energy decisions.

That is a possibility, not a measured outcome. WattBack has not established savings, adoption, or emissions impact. The next meaningful milestone is evidence: compare estimates with real bills, validate assumptions with domain experts, and learn from households about which explanations actually help.

## Join the experiment

Try a bill with rates you can verify. Open an issue if a calculation looks off. If you know a regional tariff, share its source and effective date so it can be checked before being added.

Curiosity is welcome; corrections are even more welcome.

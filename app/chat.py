"""Helper chatbot. Uses an Adaption model/stack when ADAPTION_API_KEY and ADAPTION_MODEL are set, else a keyword FAQ
that costs nothing. The FAQ is also the fallback if the model call fails."""
import os

SYSTEM = ("You are WattBack's helper for Indian households. Answer briefly about using the app, understanding an electricity "
          "bill, slabs, solar, rewards, privacy and energy saving. Use only numbers that appear in the Context. If asked for a tariff rate you "
          "were not given, say to check the bill or the distribution company's tariff order. Reply in the user's language "
          "(English, Hindi or Gujarati). Never give legal or financial advice.")

FAQ = [
 (("how", "work", "calculate", "units", "algorithm"),
  "WattBack works backwards: we numerically invert your bill amount through your state's tariff slab equations to calculate exact units (kWh). Real-time degree-day weather data then separates base load from cooling."),

 (("accurate", "exact", "estimate", "wrong", "bracket"),
  "Where we hold official tariff records (like Gujarat), results are close to exact. For unlisted states, we bracket your usage between low and high tariffs. You can always enter the exact slabs printed on your bill via 'Use my own rates'."),

 (("problem", "target", "purpose", "why", "idea"),
  "People receive electricity bills but don't know the real reasons behind the number: how many units they bought, whether a tariff slab cliff caused a jump, or how weather affected AC load. WattBack turns that monthly number into clear insight, appliance splits, and real savings."),

 (("reward", "scratch", "cashback", "card", "prize", "voucher"),
  "Scratch cards are earned exclusively by homes that save electricity (score < 1.0) or show measurable improvement over their previous check. If usage is high, check the 'Why locked' card for guidance. Plus, analyzing 3 bills unlocks your permanent Profile Rewards Vault! Note: WattBack is an independent hackathon prototype; rewards are illustrative and not yet backed by official commercial partnerships."),

 (("milestone", "vault", "profile", "3 bills", "three bills", "saved checks"),
  "Analyze 3 electricity bills on WattBack to unlock the permanent Profile Rewards Vault! Once unlocked, all your earned vouchers, discount codes, and scratch card achievements are saved directly to your profile."),

 (("partner", "sponsored", "official", "discom", "geda", "team", "hackathon", "hackcult"),
  "WattBack is an independent citizen engagement prototype developed by Team Meteor for HackCult '26 at IIT Gandhinagar, based on GEDA's Mission LiFE problem statement. We are not yet officially partnered with or sponsored by any commercial appliance brand or utility DISCOM."),

 (("saving", "tip", "reduce", "cooling", "ac", "cut bill", "conserve"),
  "Top ways to reduce your bill: 1) Run AC at 24°C with ceiling fans (cuts cooling load by up to 20%). 2) Switch off standby devices at the plug (saves ~10% base load). 3) Keep units below your tariff slab cliff to avoid expensive penalty tiers."),

 (("solar", "roof", "subsidy", "surya", "pm surya"),
  "WattBack automatically sizes a rooftop solar setup based on your monthly units, estimates PM Surya Ghar central subsidies (up to ₹78,000), and shows net monthly loan EMI savings. Renters receive a portable efficiency kit recommendation instead."),

 (("slab", "cliff", "penalty", "tier"),
  "Tariff slabs charge steeply increasing rates once you cross set limits (e.g., 250 units). We detect whether you crossed a cliff, how many units went past, and the exact penalty surcharge you paid."),

 (("privacy", "data", "delete", "store", "account", "google"),
  "Without signing in, we store nothing about your bill. With Google sign-in, we save checks and history so you can track trends. You can delete your account and all saved checks anytime from the menu."),

 (("language", "hindi", "gujarati", "voice", "audio", "read aloud"),
  "WattBack is vernacular-first: tips and nudges are offered in English, Hindi, and Gujarati, with a one-click 'Read it aloud' voice synthesis button in your browser."),

 (("contact", "help", "support", "feedback"),
  "Have feedback, a question, or a tariff correction? Use the Contact page from the top navigation or slide-out menu to message the team."),
]

def reply(msg: str, context: str = "") -> dict:
    if os.getenv("ADAPTION_API_KEY") and os.getenv("ADAPTION_MODEL"):
        try:
            from adaption import Adaption
            out = Adaption().responses.create(model=os.getenv("ADAPTION_MODEL"), instructions=SYSTEM,
                                              input=f"Context: {context[:600]}\nUser: {msg[:500]}").output_text.strip()
            if out: return {"reply": out, "source": "ai"}
        except Exception:
            pass
    low = msg.lower()
    for keys, ans in FAQ:
        if any(k in low for k in keys): return {"reply": ans, "source": "faq"}
    return {"reply": "I can help with how WattBack works, tariff slabs, solar sizing, scratch card rewards, energy tips, and privacy. Ask any question or check the Contact page.", "source": "faq"}

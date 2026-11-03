"""Helper chatbot. Uses an Adaption model/stack when ADAPTION_API_KEY and ADAPTION_MODEL are set, else a keyword FAQ
that costs nothing. The FAQ is also the fallback if the model call fails."""
import os

SYSTEM = ("You are WattBack's helper for Indian households. Answer briefly about using the app, understanding an electricity "
          "bill, slabs, solar and saving energy. Use only numbers that appear in the Context. If asked for a tariff rate you "
          "were not given, say to check the bill or the distribution company's tariff order. Reply in the user's language "
          "(English, Hindi or Gujarati). Never give legal or financial advice.")

FAQ = [
 (("how", "work", "calculate", "units"), "Your bill amount is run backwards through your state's tariff slabs to find how many units you used. Weather data then helps split that into always-on use and cooling."),
 (("accurate", "exact", "estimate", "wrong"), "Where we have your state's rates the units are close to exact. Otherwise we show a range and mark it as an estimate. Use 'my own rates' with the slabs on your bill for an exact result."),
 (("privacy", "data", "delete", "store"), "Without signing in we store nothing about your bill. If you sign in we save your checks and your name and email so we can show trends. You can delete everything from the menu."),
 (("reward", "scratch", "cashback", "card"), "Scratch cards go to homes that use less than expected for their size and weather. Real rewards need a verified Consumer ID; typed bills are preview only."),
 (("solar", "roof", "subsidy", "surya"), "The solar card sizes a rooftop system from your units and shows the subsidy and a monthly payment. Renters get a portable savings kit instead. Check the current subsidy rules with GEDA."),
 (("slab", "cliff", "penalty"), "Tariffs charge a higher rate once you pass a monthly limit. We show how many units you went past it and roughly what that cost."),
 (("contact", "help", "support"), "Use the Contact page from the menu and we will get back to you."),
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
    return {"reply": "I can help with how WattBack works, slabs, solar, rewards and privacy. Try one of those, or use the Contact page.", "source": "faq"}

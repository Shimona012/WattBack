"""Optional tip polish via an Adaption model or stack (docs.adaptionlabs.ai Responses API).
Set ADAPTION_API_KEY and ADAPTION_MODEL (e.g. "stack:wattback" or a model id). The engine's numbers are
authoritative: if the model changes any number, we keep the template text."""
import os, re

LANGS = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}
_num = lambda s: sorted(re.findall(r"\d+(?:\.\d+)?", s))

def polish(template_text: str, lang: str) -> str:
    model = os.getenv("ADAPTION_MODEL")
    if not (os.getenv("ADAPTION_API_KEY") and model):
        return template_text
    try:
        from adaption import Adaption
        out = Adaption().responses.create(
            model=model,
            instructions=(f"Rewrite as a warm, jargon-free {LANGS[lang]} tip of at most two sentences. "
                          "Keep every number and rupee amount exactly as given. Add no new facts."),
            input=template_text).output_text.strip()
        return out if out and _num(out) == _num(template_text) else template_text
    except Exception:
        return template_text

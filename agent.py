"""
The FitFindr planning loop.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """A fresh session. Every tool result goes in here and is read back out."""
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


# ── query parsing (regex) ─────────────────────────────────────────────────────

_PRICE = re.compile(
    r"(?:under|below|less than|up to|at most|max(?:imum)?|<=?)\s*\$?\s*(\d+(?:\.\d+)?)",
    re.I,
)
_PRICE_BARE = re.compile(r"\$\s*(\d+(?:\.\d+)?)")
_SIZE = re.compile(r"\bsize\s+([A-Za-z0-9/.]+)", re.I)
_LEAD = re.compile(
    r"^\s*(?:i'?m\s+)?(?:looking for|find me|show me|i want|i need|get me)\s+", re.I
)


def _parse_query(query: str) -> dict:
    """Pull max_price and size out of the query; what's left is the description."""
    text = query
    max_price = None
    size = None

    match = _PRICE.search(text) or _PRICE_BARE.search(text)
    if match:
        max_price = float(match.group(1))
        text = text[: match.start()] + " " + text[match.end():]

    match = _SIZE.search(text)
    if match:
        size = match.group(1).strip(".,")
        text = text[: match.start()] + " " + text[match.end():]

    text = _LEAD.sub("", text)
    text = re.sub(r"[,.]", " ", text).strip()
    text = re.sub(r"\b(in|a|an)\s*$", "", text, flags=re.I)
    description = re.sub(r"\s+", " ", text).strip()

    return {"description": description, "size": size, "max_price": max_price}


# ── the message shown when a search comes back empty ──────────────────────────

def _empty_search_message(parsed: dict) -> str:
    desc, size, max_price = parsed["description"], parsed["size"], parsed["max_price"]

    filters = []
    if size:
        filters.append(f"size {size}")
    if max_price is not None:
        filters.append(f"under ${max_price:g}")
    searched = f"'{desc}'" + (f" ({', '.join(filters)})" if filters else "")

    tips = []
    if size:
        looser = search_listings(desc, None, max_price)
        if looser:
            tips.append(
                f"Try a different size or drop the size filter: {len(looser)} "
                f"listing(s) match without it (for example '{looser[0]['title']}' "
                f"in size {looser[0]['size']})."
            )
    if max_price is not None:
        looser = search_listings(desc, size, None)
        if looser:
            cheapest = min(item["price"] for item in looser)
            tips.append(
                f"Raise your price limit above ${max_price:g}: the cheapest "
                f"match costs ${cheapest:.2f}."
            )
    if not tips:
        tips.append(
            "Try different or broader keywords (for example the item type "
            "alone, like 'jacket' or 'tee')."
        )

    return f"No listings matched {searched}. " + " ".join(tips)


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session. Check session["error"]
    first: if it isn't None the run ended early.

    Branch rule: if search_listings returns [], put a message naming what to
    change in session["error"] and stop. Otherwise select the first result and
    continue to suggest_outfit, then create_fit_card.
    """
    session = new_session(query, wardrobe)
    session["parsed"] = _parse_query(query)

    step = "search"
    count = 0

    try:
        while step:
            count += 1
            trace.check_iterations(count)

            if step == "search":
                parsed = session["parsed"]
                results = search_listings(
                    parsed["description"], parsed["size"], parsed["max_price"]
                )
                session["search_results"] = results
                trace.step(
                    "search_listings",
                    inputs=parsed,
                    returned=[f"{r['id']} {r['title']} (${r['price']})" for r in results],
                )

                if not results:
                    # THE BRANCH: nothing came back, so stop here.
                    session["error"] = _empty_search_message(parsed)
                    step = None
                else:
                    session["selected_item"] = session["search_results"][0]
                    step = "outfit"

            elif step == "outfit":
                outfit = suggest_outfit(session["selected_item"], session["wardrobe"])
                session["outfit_suggestion"] = outfit
                trace.step(
                    "suggest_outfit",
                    inputs={
                        "id": session["selected_item"]["id"],
                        "title": session["selected_item"]["title"],
                    },
                    returned=outfit,
                )
                step = "card"

            elif step == "card":
                card = create_fit_card(
                    session["outfit_suggestion"], session["selected_item"]
                )
                session["fit_card"] = card
                trace.step(
                    "create_fit_card",
                    inputs={
                        "id": session["selected_item"]["id"],
                        "title": session["selected_item"]["title"],
                    },
                    returned=card,
                )
                step = None

    except ModelUnavailable:
        session["error"] = (
            "The model couldn't be reached. Check that GEMINI_API_KEY in .env "
            "is correct, wait a minute in case you hit the rate limit, then "
            "run the same query again."
        )

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )

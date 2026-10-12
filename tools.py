"""
The three FitFindr tools.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

Each is a standalone function; test them one at a time before the loop.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings

# Dollars over max_price that still count as a match.
PRICE_TOLERANCE = 2.0


# ── helpers ───────────────────────────────────────────────────────────────────

_STOPWORDS = {
    "a", "an", "the", "in", "for", "of", "with", "and", "or", "to", "me", "i",
    "want", "need", "looking", "find", "show", "please", "size", "under",
    "over", "below", "something", "some", "my", "on",
}


def _stem(word: str) -> str:
    """Crude plural handling so 'tees' matches 'tee' and 'jeans' matches 'jean'."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {_stem(w) for w in words if len(w) > 1 and w not in _STOPWORDS}


def _size_tokens(size: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", size.lower()))


def _size_matches(wanted: str, listing_size: str) -> bool:
    """Whole-token match: 'M' matches 'M' and 'S/M'; 'L' does not match 'XL'."""
    want = _size_tokens(wanted)
    return bool(want) and want <= _size_tokens(listing_size)


def _describe_item(item: dict) -> str:
    parts = [
        f"{item.get('title')}",
        f"category: {item.get('category')}",
        f"colors: {', '.join(item.get('colors') or [])}",
        f"style: {', '.join(item.get('style_tags') or [])}",
        f"condition: {item.get('condition')}",
        f"size: {item.get('size')}",
    ]
    return "; ".join(parts)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Filter by price and size, score by keyword overlap with the description,
    drop zero scores, return best first (at most config.SEARCH_RESULT_LIMIT).
    Returns [] when nothing matches.

    Price: an item passes if its price is at most max_price + PRICE_TOLERANCE.
    Size:  the requested size must be one of the listing's size tokens.
    Scoring per query word: 3 if it is in the title, else 2 if in the style
    tags, else 1 if in the description/category/colors/brand. Ties go to the
    cheaper item.
    """
    query_words = _keywords(description or "")
    scored = []

    for item in load_listings():
        if max_price is not None and item["price"] > max_price + PRICE_TOLERANCE:
            continue
        if size and not _size_matches(size, item["size"]):
            continue

        title_words = _keywords(item["title"])
        tag_words = _keywords(" ".join(item.get("style_tags") or []))
        other_words = _keywords(" ".join([
            item.get("description") or "",
            item.get("category") or "",
            item.get("brand") or "",
            " ".join(item.get("colors") or []),
        ]))

        score = 0
        for word in query_words:
            if word in title_words:
                score += 3
            elif word in tag_words:
                score += 2
            elif word in other_words:
                score += 1

        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [item for _, item in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    One or two outfits built around the item. With an empty wardrobe, general
    styling advice instead. Always returns a non-empty string.
    """
    items = (wardrobe or {}).get("items") or []

    if not items:
        prompt = (
            "You are a thrift-styling assistant. Someone is considering this "
            f"secondhand piece:\n{_describe_item(new_item)}\n\n"
            "They haven't told us what's in their wardrobe. Give two short, "
            "specific outfit ideas using common basics (name the types of "
            "pieces and colors). Keep it under 120 words."
        )
    else:
        lines = []
        for piece in items:
            lines.append(
                f"- {piece.get('name')} "
                f"({', '.join(piece.get('colors') or [])}; "
                f"{', '.join(piece.get('style_tags') or [])}) "
                f"{piece.get('notes') or ''}".strip()
            )
        prompt = (
            "You are a thrift-styling assistant. Someone is considering this "
            f"secondhand piece:\n{_describe_item(new_item)}\n\n"
            "Their wardrobe:\n" + "\n".join(lines) + "\n\n"
            "Suggest one or two outfits that combine the new piece with items "
            "they already own. Name the owned pieces exactly as listed. Keep "
            "it under 120 words."
        )

    response = generate(prompt)
    text = (response or "").strip()
    return text or "Try pairing it with simple basics in a neutral color."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    A two-to-four sentence caption that reads like a real post. Returns a
    descriptive message (without calling the model) if there's no outfit.
    """
    if not outfit or not outfit.strip():
        return "No outfit suggestion was available, so there's nothing to caption yet."

    price = new_item.get("price")
    price_text = f"${price:.2f}" if isinstance(price, (int, float)) else "an unlisted price"
    brand = new_item.get("brand")
    brand_line = f"Brand: {brand}\n" if brand else ""

    prompt = (
        "Write a short social media caption (two to four sentences) about a "
        "thrift find. It should sound like a real person posting, not a "
        "product description, and be specific about the vibe.\n"
        f"Item: {new_item.get('title')}\n"
        f"{brand_line}"
        f"Price: {price_text}\n"
        f"Platform: {new_item.get('platform')}\n"
        f"Outfit idea: {outfit}\n\n"
        f"Mention the item, the exact price {price_text}, and the platform "
        f"{new_item.get('platform')} once each. Do not mention any other "
        "dollar amounts. Don't invent a brand. Return only the caption."
    )

    response = generate(prompt)
    return (response or "").strip() or "Couldn't write a caption this time."
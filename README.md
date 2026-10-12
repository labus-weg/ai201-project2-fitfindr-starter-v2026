# FitFindr

Nafisa Nawrin Labonno

---

# Unit 3 — The Build

## What This Does

FitFindr takes a plain-English thrift request such as "a vintage graphic tee under $30" and searches a file of 40 secondhand listings, filtering by price and size and ranking by keyword match. For the best match it suggests one or two outfits built from the user's wardrobe, then writes a short social-media caption (a "fit card") naming the item, price and platform. If nothing matches, it stops and tells the user which filter to change instead of continuing with nothing.

---

## Tool Inventory

**search_listings(description: str, size: str | None, max_price: float | None) → list[dict]**
Filters listings to those priced at most max_price + $2 (a deliberate tolerance) and whose size has the requested size as a whole token, scores the rest by keyword overlap with the description, and returns the best matches first. Returns a list of listing dicts (id, title, description, category, style_tags, size, condition, price, colors, brand, platform), at most 10. Returns `[]` when nothing matches. Size match rule: the requested size must match a whole token of the listing's size, so "M" matches "S/M" but "L" does not match "XL".

**suggest_outfit(new_item: dict, wardrobe: dict) → str**
Asks the model for one or two outfits built around the item. Returns a non-empty string. With an empty wardrobe it returns general styling advice.

**create_fit_card(outfit: str, new_item: dict) → str**
Asks the model for a two-to-four sentence caption mentioning the item, price, and platform. Returns a string. With an empty outfit it returns a message instead of calling the model.

**Branch rule:** If search_listings returns `[]`, put a message naming what to change in session["error"] and stop, leaving fit_card as None. Otherwise set session["selected_item"] to the first result and go to suggest_outfit.

**Query parsing:** regex pulls the price (after "under", "$", etc.) and size (after "size"); the rest is the description.

## Planning Loop

**Branch rule:** If search_listings returns an empty list, put a message naming what to change in session["error"] and stop, so fit_card stays None. Otherwise take the first result, store it in session["selected_item"], and go to suggest_outfit, then create_fit_card.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** regex, in `agent.py::_parse_query`. It pulls out the price limit and size, and what's left becomes the description.

**What moves through the session:** query, then parsed (description, size, max_price), then search_results, then selected_item, then outfit_suggestion, then fit_card. error stays None unless the run stops early. Each tool's result is written into the session and read back out for the next call.

---

## Sample Run

**One full query** (from `python agent.py`)

```
=== A query the data can match ===
[1] search_listings
      in:  dict with keys: description, size, max_price
      out: 10 items: lst_033 Vintage Band Tee — Faded Grey ($19.0)…
[2] suggest_outfit
      in:  Vintage Band Tee — Faded Grey
      out: **Outfit 1: 90s Grunge Streetwear** Pair the vintage band tee with your **Baggy straight-leg jeans, dark wash**…
[3] create_fit_card
      in:  Vintage Band Tee — Faded Grey
      out: Found the ultimate faded grey vintage band tee on depop for just $19.00 and I am never taking it off…
  found:    Vintage Band Tee — Faded Grey — $19.0 on depop
  fit card: Found the ultimate faded grey vintage band tee on depop for just $19.00 and I am never taking it off. It has that perfectly worn-in, paper-thin 90s grunge feel that usually costs a fortune. Planning to style it with baggy dark wash denim and chunky boots for total off-duty cool.

=== A query it can't ===
[4] search_listings
      in:  dict with keys: description, size, max_price
      out: [] (empty)
  stopped: No listings matched 'designer ballgown' (size XXS, under $5). Try different or broader keywords (for example the item type alone, like 'jacket' or 'tee').
  fit_card is None — it should still be None here
```

**The three tools, tested one at a time**

```
$ python -c 'from tools import search_listings; print(search_listings("vintage graphic tee", "M", 30)[:1])'
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'brand': None, 'platform': 'depop', ...}]
```

```
$ python -c 'from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[1], get_example_wardrobe()))'
**Outfit 1: Y2K Streetwear**
Pair the butterfly baby tee with your **Baggy straight-leg jeans, dark wash** for a classic early-2000s contrast between fitted and loose. Cinch the waist with the **Brown leather belt**, and layer the **Black cropped zip hoodie** over top (left unzipped to show the print). Finish with the **Chunky white sneakers** and your **Black crossbody bag**.

**Outfit 2: Soft Contrast**
Tuck the baby tee into your **Wide-leg khaki trousers** for an easy earth-toned mix of Y2K and cottagecore aesthetics. Add the **Vintage black denim jacket** on top for structure, and ground the look with the **Black combat boots** to give the sweet butterfly print an edgy finish.
```

```
$ python -c 'from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card("Pair with baggy dark jeans and white sneakers.", load_listings()[1]))'
Found the absolute ultimate Y2K butterfly baby tee on depop for just $18.00 and I am never taking it off. It has the dreamiest nostalgic early 2000s energy. Just picturing it with some baggy dark jeans and fresh white sneakers for maximum mall-rat chic.
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* My environment check failed on the second project (missing `mcp` package), so I pasted the output into Claude and asked what was wrong.
- *What came back:* It said the terminal was still using the first project's virtual environment, and told me to run `pip install -r requirements.txt` and re-run `python test.py`.
- *What I changed:* I ran the install, and all 10 checks passed.

**Moment 2**

- *What I asked for:* I wanted the fit card to include a barcode as well as the price tag, name, and platform, and asked Claude whether that made sense as a criterion.
- *What came back:* It pointed out that the listings data has no barcode field, so a criterion requiring one could never pass.
- *What I changed:* I dropped the barcode and kept the criterion to item, exact price, and platform, with the listing id in the trace as the closest thing.

---

# Unit 4 — The Test

## Run Log — Before

## Verdicts and Diagnoses

## Loop Trace

## The Improvement

### Run Log — After

## What's Still Broken

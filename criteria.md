# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
Search is a keyword-overlap match that only handles plural endings, so a
phrasing that uses a different word than the listing (for example "t-shirt"
for a listing titled "tee") can score zero and return nothing. Two of the three
tools also call a model, which can fail on a rate limit or an outage. Both make
5 of 5 too strict.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path is a plain `if` on an empty list that runs before any model call, and
the message is built by code from the parsed query, not written by a model. No
step in it varies between runs, so a miss would be a bug and 5 of 5 is the
honest target.

---

## 3. The selected item is the same item all the way through

In 5 of 5 queries that match at least one listing, the id of the item passed to
`suggest_outfit` and to `create_fit_card` equals the id in
`session["selected_item"]`, which equals the id of `session["search_results"][0]`.

**Why this target:**
The item is chosen by code (the first search result) and handed between steps
through the session, with no model involved in passing it. A mismatch would mean
the state was dropped or overwritten, which is a bug, so I accept nothing less
than 5 of 5.

---

## 4. The fit card states the real price and platform

In at least 4 of 5 tries, the fit card contains the selected item's price
(written as "$24" or "$24.00") and its platform name, and contains no other
dollar amount.

**Why this target:**
The card is written by a model, so it chooses its own wording and may skip or
reformat the price; 5 of 5 would be too strict for that, and 4 of 5 leaves
room for one miss. The price matters most because search allows items up to
$2 over the user's stated limit, so the card is where the user sees what the
item really costs.

---

## 5. Search respects the price and size limits

Over 5 queries that each include a size and a price limit, every listing
`search_listings` returns costs at most the limit + $2 and has the requested
size as one of its size tokens (so "M" matches "M" or "S/M", but never "L"
or "XL"), in 5 of 5 queries.

**Why this target:**
Price and size are filtered by plain comparison code with no model involved,
so a miss would be a bug, not variation. I allow +$2 over the stated limit on
purpose, so the check is "limit + $2", not the limit itself.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->

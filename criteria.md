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
My planned design has two weak points. First, `search_listings` will score
listings by keyword overlap, not by meaning. Before scoring, it will take the
size out of the description (e.g. "M"), drop stop words ("under", "size",
"looking", "something") and strip punctuation. A query built mostly from those
words can be left with no keywords, or only with words no listing contains, so
every listing scores 0, the search returns `[]`, and the loop stops at the empty
branch even though the data has an item that fits — a vague query like
"size M" is the case I expect to miss. Second, `suggest_outfit` and
`create_fit_card` will both call the model. If `suggest_outfit` gets a blank
reply, my spec has it return a fallback message, and `create_fit_card` then
returns an error message instead of a caption, so no fit card is produced; a
rate limit that outlasts the retries in `generate.py` could also end a run.
I expect both to be uncommon, so 4 of 5 is realistic: 5 of 5 would assume
perfect parsing and a perfectly reliable model, while two or more misses would
point to a real bug, which a 3 of 5 target would excuse.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path will never call the model. `search_listings` will be plain Python
filtering a fixed file, with no randomness, so the same query will return the
same result on every run. For an impossible query like "designer ballgown size
XXS under $5", it should return `[]` for two independent reasons: no listing in
the data costs $5 or less (the cheapest is $12), so the price filter removes
everything, and no listing contains "designer" or "ballgown", so nothing would
score above 0 anyway. The branch in `run_agent` will be a single check on that
empty list: it will write a fixed message (not model-generated) into
`session["error"]` telling the user what to change, and return before
`suggest_outfit` is called. With nothing on this path depending on the model or
on chance, any failed try would be a bug in my code, so anything below 5 of 5
would excuse a real defect.

---

## 3. The item search found is the item the next two tools receive

Given a query that returns at least one listing, the selected item's id remains identical across session["selected_item"], session["outfit_input_id"], and session["fit_card_input_id"] (each recorded at the moment suggest_outfit and create_fit_card are called) — in 5 of 5 tries.

**Why this target:**
In my design the item will move from one tool to the next only through my code
reading `session["selected_item"]` and passing it on; the model will play no
part in the hand-off.

I will compare ids rather than titles or whole dicts because every listing has an
`id` field and all 40 ids in `data/listings.json` are distinct. Two listings
can share words in their titles, but no two share an id, so matching ids mean
the same listing, and a different id means a different listing reached the
tool. That makes it a single value anyone can read off the printed session and
compare by eye. `run_agent` will record each id from the same variable it
passes to the tool, so the recorded value shows what the tool actually received
rather than what the session claims.

Reading a value from a dict has no randomness, so the result should be
identical on every run. Any mismatch would be a bug in `run_agent` — passing a
different search result, a stale variable, or a re-searched item — not bad
luck. A target lower than 5 of 5 would let a run where the wrong item reached a
tool still count as passing, which would hide exactly the bug this criterion is
meant to catch.

---

## 4. Each fit card is a postable caption, and no two start the same way

 Given 5 different items whose queries return results, each fit-card states the item's price exactly once as $ digits (e.g. $24), names its platform exactly once, and contains 2 to 4 sentences under 80 words, with all three conditions met in at least 4 of 5 tries. Across the same 5 cards, each first sentence is unique.

**Why this target:**
A card passes only if several conditions hold at once — price once as `$`
digits, platform once, and 2–4 sentences under 80 words — and all of them
depend on the model following the prompt. The caption will be the only output
written entirely by the model, at temperature 0.9, so it can occasionally slip
(write the price in words, repeat it, or run past 80 words) however carefully
the prompt is worded. That is why I didn't pick 5 of 5. I didn't go lower than
4 of 5 because my design does part of the work in code before the model sees
anything: `create_fit_card` will format the price as `$` digits itself and
state every rule explicitly in the prompt, so more than one slip in five would
mean the prompt is broken, not unlucky. For the openings, the tool will pick a
random opening style for each call and each item gives the model different
details, so two identical first sentences across 5 different items would mean
the prompt is producing a template. I use 5 different items because the
starter's cache returns identical text for identical prompts, which would fail
that check for the wrong reason.

---

## 5. A non-empty wardrobe is actually used in the outfit suggestion

Given a query that matches at least one listing and a non-empty wardrobe, the agent returns an outfit suggestion that includes at least one existing wardrobe item (named exactly or by a close paraphrase — same type of piece and same colour) alongside the selected listing — in 5 of 5 tries.

**Why this target:**
The point of passing a wardrobe to `suggest_outfit` is to get an outfit built
around pieces the user already owns. If a non-empty wardrobe is passed and not
a single one of its items appears in the suggestion, the tool is behaving
exactly as it would with an empty wardrobe, and passing the wardrobe makes no
sense.

I ask for at least one wardrobe item rather than all of them because not every
piece the user owns will complement the selected item. Forcing the model to
use the whole wardrobe would push it into vague or random combinations that
make no sense in real life — orange trousers with a purple shirt, for example.
So my prompt will tell the model to pick only the wardrobe pieces that suit the
new item. Once at least one owned piece is in the outfit, the model is free to
use more of them if they fit, or to add general pieces from outside the
wardrobe to complete a good look. One item is the minimum that shows the
wardrobe was actually used.

I chose 5 of 5 because using the wardrobe is the feature this tool promises:
every query that comes with a non-empty wardrobe must get something out of it,
otherwise there is no point in having a wardrobe at all. Making sure that
happens is a design responsibility, not model variation — my prompt will
explicitly require at least one wardrobe piece in the outfit. Whatever the
wardrobe holds, it is the model's job to pick a piece and build the rest of the
look around it — with other wardrobe items or general pieces — so that the
combination makes sense. Missing on even one query would therefore be a bug in how the feature
is built, not bad luck, and a 4 of 5 target would excuse it.

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

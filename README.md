# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->
The user enters a query describing a piece of clothing, say a T-shirt or jeans, optionally with a size and a price limit. The system searches the one-of-a-kind second-hand listings and finds the best match. It additionally looks at the user's wardrobe, if one exists, and suggests outfits that pair the find with pieces they already own, and finally writes a short fit-card caption mentioning the item, its price, and the platform. If nothing matches, it stops and tells the user what to change in their search instead.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the listings by size and price, scores what's left by keyword overlap with the description, and returns the best matches.
- **Inputs:** `description` (`str`), `size` (`str` or `None`, default `None` = no size filter), `max_price` (`float` or `None`, inclusive: a listing priced exactly at `max_price` is kept; default `None` = no price filter; `0` is a real limit, not "no filter")
- **Size match:** case-insensitive, by whole size rather than substring. A listing's size is split on `/` and spaces, with notes in brackets dropped. It matches when it covers every size asked for. So `M` matches `M`, `S/M` and `M/L`; `W30` matches `W30 L30`; a bare number like `8.5` means `US 8.5`. But `S` never matches `US 9`, and `L` never matches `XL`.
- **Returns:** every listing that matches at least one query keyword (score ≥ 1), sorted by score descending, and on a tie, listings in a size written inside `description` (e.g. "graphic tee size M") come first; that size only reorders results, it doesn't filter them. At most 10. Score = one point per distinct query keyword found among the listing's words, where the listing's words are taken from `title`, `description` and `category` (lowercased, split on non-alphanumerics) plus each entry of `style_tags` and `colors`; stop words (filler like "the", "with", request words like "looking", and price/size words like "under", "size") are dropped from both sides first. The fields of the dict includes: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`
- **When it has nothing:** `[]` when the size or price filter leaves no listings, or when no remaining listing matches any keyword after stop words are removed (including an empty `description`), i.e, never `None`, never an exception.

### `suggest_outfit`

- **What it does:** Takes a thrifted listing the user is considering and asks the model to style it into complete outfits. If the user has a wardrobe, it first strips each wardrobe item's `id` and any `None` `notes` (via `_clean_wardrobe()`), then asks for looks built around the pieces the user already owns, choosing only the ones that suit the new item; if no wardrobe is given, it asks for general styling ideas instead.
- **Inputs:** `new_item` (`dict`): one listing, with `title`, `description`, `category`, `style_tags`, `colors`, `size`, `price`, `brand`. `wardrobe` (`dict`): the user's wardrobe, with an `'items'` key holding a `list[dict]`, where each item has `id`, `name`, `category`, `colors`, `style_tags`, `notes`; the list may be empty, and `'items'` may be missing or `None`.
- **Returns:** A non-empty `str` of outfit suggestions in plain language, usually two (sometimes three) labelled looks ("Look-1: …", "Look-2: …"). Each look names the new item, the pieces paired with it, and the overall vibe. When a wardrobe is given, the paired pieces come from that wardrobe and are referred to by name, never by ID; if the wardrobe can't complete an outfit (e.g. no shoes), the model fills the gap with general pieces.
- **When it has nothing:** If the wardrobe is empty, missing, or `None`, it does not raise or return `""`; it returns general styling advice for the item, using pieces the user may not own. If the model's response is blank (`""`, whitespace only, or `None`), it returns `"Couldn't generate an outfit suggestion — try again."`. It always returns a non-empty string, so the loop never needs to check for an empty result.

### `create_fit_card`

- **What it does:** Turns the chosen listing and its outfit suggestion into a short social-media caption, written as the buyer showing off their thrift find. Before calling the model it formats the price (`$75`, `$12.5`), strips the "Look-N:" labels from the outfit, and adds the brand only when the listing has one; a randomly chosen opening style keeps captions from starting the same way.
- **Inputs:** `outfit` (`str`): the suggestion text from `suggest_outfit()`. `new_item` (`dict`): the listing, using `title`, `category`, `colors`, `style_tags`, `price`, `platform`, `description`, and `brand` (may be `None`).
- **Returns:** A `str` caption of 2–4 sentences, under 80 words, on a single line. It names the item naturally rather than by its listing title, mentions the price (as `$` digits) and platform exactly once each but not in the first sentence, mentions the brand once only if there is one, and describes at most two looks from the outfit.
- **When it has nothing:** If `outfit` is empty, whitespace-only, or `suggest_outfit()`'s fallback message, it returns `"No outfit suggestion provided (The model FAILED to generate an outfit suggestion) — try again."` without calling the model. If the model's reply is blank, it returns `"Couldn't generate a caption — try again."`. It never returns `""` or `None`.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that names what the user could change (loosen or drop the size, raise the price ceiling, or use broader words), leave `selected_item`, `outfit_suggestion` and `fit_card` as `None`, and stop without calling `suggest_outfit`. Otherwise, take the first result as `session["selected_item"]`, pass it to `suggest_outfit`, store the result in `session["outfit_suggestion"]`, then pass both to `create_fit_card` and store its caption in `session["fit_card"]`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, with no model call, in `agent.py::_parse_request`. It pulls out three values and stores them in `session["parsed"]`:
- `max_price` (`float` or `None`): from a price phrase: "under", "below", "less than", "max", "up to" or "at most" followed by a number, or a bare `$N` (e.g. "under $30" → `30.0`). That phrase is then removed from the text. `None` when the query has no price, never `0`, because `0` is a real limit in my spec.
- `size` (`str` or `None`): taken from what's left by `_parse_query` in `tools.py`, the same size patterns the search uses ("M", "S/M", "W30", "US 8", "size 8.5", "one size").
- `description` (`str`): the remaining words, joined. Stop words are left in; `search_listings` drops them itself.

Example: `'vintage graphic tee under $30, size M'` → `{'description': 'vintage graphic tee', 'size': 'M', 'max_price': 30.0}`.

**What moves through the session:** each step writes its result into the session, and the next step reads its input back out of the session, never straight from the previous call. In order:
1. `query`: what the user typed (set by `new_session`).
2. `parsed`: `{description, size, max_price}` from `_parse_request(session["query"])`.
3. `search_results`: the list from `search_listings`, called with the three values read from `session["parsed"]`.
4. **Branch:** if `search_results` is empty, `error` gets a fixed message from `_no_results_message` naming what to change (size, price limit, or wording), and the run returns. `selected_item`, `outfit_input_id`, `outfit_suggestion`, `fit_card_input_id` and `fit_card` all stay `None`.
5. `selected_item`: `search_results[0]`.
6. `outfit_input_id` and `outfit_suggestion`: `_styled(session, session["selected_item"])` records the `id` of the item it actually passes to `suggest_outfit` (with `session["wardrobe"]`), then stores the suggestion.
7. `fit_card_input_id` and `fit_card`: `_captioned(session, session["outfit_suggestion"], session["selected_item"])` records the `id` of the item it actually passes to `create_fit_card`, then stores the caption.

`selected_item["id"] == outfit_input_id == fit_card_input_id` on every matching run is what criterion 3 checks.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

*A query that matches: all three tools run and values move through the session.*

Command:
```bash
python app.py ask 'tan leather shoulder bag under $40'
```

Output:
```text
  Found:    Mini Shoulder Bag — Tan Leather — $38.0 on poshmark

  Outfit:   Look-1: The mini tan leather shoulder bag paired with the white ribbed tank top, wide-leg khaki trousers, and chunky white sneakers for a fresh, minimal, and effortless daytime look that plays beautifully with earth tones.

Look-2: A chic, casual streetwear-inspired outfit featuring the mini tan leather shoulder bag layered with the oversized grey crewneck sweatshirt and baggy straight-leg jeans in dark wash, finished with chunky white sneakers.

Look-3: An edgy yet classic combination of the mini tan leather shoulder bag, the black cropped zip hoodie paired with the wide-leg khaki trousers, and black combat boots for a stylish contrast between grungy footwear and a polished vintage bag.

  Fit card: Pair this little tan leather bag with a white ribbed tank top and wide-leg khaki trousers for an effortless daytime look. It adds the right vintage touch to a casual street outfit with an oversized grey crewneck and dark wash jeans too. I managed to score it on Poshmark for $38, and it holds all my essentials while keeping things minimal.

2 model calls this session, 1555 prompt + 210 output tokens
```

**The three tools, tested one at a time**

### 1. `search_listings`

**Test 1a: a query that matches**

Command:
```bash
python -c "from tools import search_listings; r = search_listings('graphic tee', max_price=30); print(len(r), [(x['id'], x['title'], x['price']) for x in r])"
```

Output:
```text
6 [('lst_002', 'Y2K Baby Tee — Butterfly Print', 18.0), ('lst_006', 'Graphic Tee — 2003 Tour Bootleg Style', 24.0), ('lst_017', 'Mesh Long-Sleeve Top — Black', 15.0), ('lst_033', 'Vintage Band Tee — Faded Grey', 19.0), ('lst_011', 'Low-Rise Cargo Pants — Khaki', 27.0), ('lst_015', 'Vintage Graphic Hoodie — Faded Black', 26.0)]
```

**Test 1b: empty case (nothing matches)**

Command:
```bash
python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
```

Output:
```text
[]
```

### 2. `suggest_outfit`

**Test 2a: with the example wardrobe**

Command:
```bash
python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
```

Output:
```text
Look-1: Vintage Levi's 501 Jeans paired with the white ribbed tank top, layered with the vintage black denim jacket, chunky white sneakers, and the black crossbody bag for a classic, effortless streetwear look.

Look-2: Vintage Levi's 501 Jeans paired with the oversized grey crewneck sweatshirt, black combat boots, the brown leather belt, and the black crossbody bag for a cozy, vintage-inspired casual outfit.
```

**Test 2b: empty case (empty wardrobe)**

Command:
```bash
python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
```

Output:
```text
Look-1: A look consisting of the Vintage Levi's 501 Jeans paired with a crisp white button-down shirt tucked in, a classic brown leather belt, a pair of tan suede loafers, and a minimalist silver wristwatch for a timeless, smart-casual aesthetic.

Look-2: A cozy oatmeal-colored crewneck sweater layered over a white t-shirt (with the hem peeking out), worn with the medium wash Levi's, clean white leather sneakers, and a vintage brown leather messenger bag for an effortless, charming weekend look.

Look-3: A black fitted ribbed turtleneck paired with the vintage denim jeans, layered with a tailored camel trench coat, classic black leather ankle boots, and a matching black leather crossbody bag for a chic, sophisticated urban vibe.
```

### 3. `create_fit_card`

**Test 3a: with a real outfit**

Command:
```bash
python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
```

Output:
```text
The classic medium indigo wash on these vintage Levi's immediately caught my eye with its perfect, broken-in fade. I locked this pair down on Depop for $38 and wear them with crisp white sneakers for an effortless streetwear vibe. They also look great dressed down with the same sneakers for running errands.
```

**Test 3b: empty case (empty outfit)**

Command:
```bash
python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('', load_listings()[0]))"
```

Output:
```text
No outfit suggestion provided (The model FAILED to generate an outfit suggestion) — try again.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

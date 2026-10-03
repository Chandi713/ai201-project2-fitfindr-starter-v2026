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
The user enters a query describing clothing let's say a T-shirt or Jeans, optionally with size and price-limit. The system searches the one-of-a-kind second-hand listings and finds the best or most related match. It additinally looks into the user's wardrobe, if one exists, and suggest outfit that pair and suits with the one they already own, and finally writes a short fit-card caption mentioning the item, its price, and the platform. If nothing matches then it stops and asks the user to change their search instead.


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
- **Inputs:** `description` (`str`), `size` (`str` or `None`, default `None` = no size filter), `max_price` (`float` or `None`, inclusive — a listing priced exactly at `max_price` is kept; default `None` = no price filter; `0` is a real limit, not "no filter")
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

**How the query is parsed:** <!-- regex, string splitting, or asking the model — say which -->

**What moves through the session:** <!-- which fields, in what order -->

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```

```
$ python -c "from tools import suggest_outfit; ..."

```

```
$ python -c "from tools import create_fit_card; ..."

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

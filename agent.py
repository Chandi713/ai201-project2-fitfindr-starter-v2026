"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
        "outfit_input_id": None,     # id of the item actually passed to suggest_outfit
        "fit_card_input_id": None,   # id of the item actually passed to create_fit_card
    }


# ── query parsing ─────────────────────────────────────────────────────────────

def _parse_request(query: str) -> dict:
    """
    Split what the user typed into the three inputs search_listings takes.

    Regex, no model call:
      • max_price — "under $30", "below 40", "max $25.50", "less than $50",
                    "up to $20", or a bare "$30". None when there isn't one
                    (not 0 — 0 is a real limit in my spec).
      • size      — pulled out by _parse_query in tools.py ("M", "W30",
                    "US 8", "size 8.5", "S/M"…). None when there isn't one.
      • description — whatever words are left.

    'vintage graphic tee under $30, size M'
        → {'description': 'vintage graphic tee', 'size': 'M', 'max_price': 30.0}
    """
    import re
    from tools import _parse_query

    PRICE_RE = re.compile(
        r"(?:\b(?:under|below|less\s+than|max(?:imum)?|up\s+to|at\s+most)\s*\$?\s*"
        r"|\$\s*)(\d+(?:\.\d+)?)",
        re.IGNORECASE,
    )

    max_price = None
    text = query
    match = PRICE_RE.search(text)
    if match:
        max_price = float(match.group(1))
        text = text[:match.start()] + " " + text[match.end():]

    words, size = _parse_query(text)
    return {
        "description": " ".join(words),
        "size": size,
        "max_price": max_price,
    }


def _no_results_message(parsed: dict) -> str:
    """
    The fixed message for an empty search, built from what the user asked for.

    Written in code, not by the model, so it's there every time and always
    names something the user can change: the size, the price ceiling, or the
    words.
    """
    if not parsed["description"].strip():
        return ("Your search didn't say what kind of item you want, so there was "
                "nothing to match. Add the item, e.g. \"tee size M\" or "
                "\"denim jacket under $50\".")

    asked = parsed["description"]
    suggestions = []
    if parsed["size"]:
        suggestions.append(f"drop the size or try a different one (you asked for {parsed['size']})")
    if parsed["max_price"] is not None:
        suggestions.append(f"raise your price limit above ${parsed['max_price']:g}")
    suggestions.append("use fewer or more general words, e.g. the type of item "
                       "(\"dress\", \"jacket\", \"tee\") instead of a specific style")
    tips = "\n".join(f"  • {s}" for s in suggestions)
    return f"No listings matched \"{asked}\". To find something, try:\n{tips}"


# ── tool hand-offs ────────────────────────────────────────────────────────────
# Criterion 3 asks whether the item search found is the item each tool
# received. These two record the id from the very argument they pass on, so the
# recorded id and the tool's input can't drift apart: if run_agent ever passed
# the wrong item, the recorded id would stop matching session["selected_item"].

def _styled(session: dict, item: dict) -> str:
    """Call suggest_outfit with `item`, recording which item it received."""
    session["outfit_input_id"] = item["id"]
    return suggest_outfit(item, session["wardrobe"])


def _captioned(session: dict, outfit: str, item: dict) -> str:
    """Call create_fit_card with `item`, recording which item it received."""
    session["fit_card_input_id"] = item["id"]
    return create_fit_card(outfit, item)


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    import mcp_client
    session = new_session(query, wardrobe)
    steps = 0

    trace.start_trace()
    # Step 1 — parse the query into description / size / max_price
    steps += 1
    trace.check_iterations(steps)
    session["parsed"] = _parse_request(session["query"])
    trace.step("parse_request", inputs=session["query"], returned=str(session["parsed"]))

    # Step 2 — search, reading the inputs back out of the session
    steps += 1
    trace.check_iterations(steps)
    parsed = session["parsed"]
    # session["search_results"] = search_listings(
    #     parsed["description"],
    #     size=parsed["size"],
    #     max_price=parsed["max_price"],
    # )

    # The search runs on the MCP server; if the server can't start or refuses
    # the call, say so and stop rather than letting MCPError escape.
    try:
        session["search_results"] = mcp_client.call_tool("search_listings", {
            "description": parsed["description"],
            "size": parsed["size"],
            "max_price": parsed["max_price"],
        })
        trace.step("search_listings (via MCP)", inputs=str(parsed),
                   returned=session["search_results"])
    except mcp_client.MCPError as exc:
        session["error"] = (
            "Couldn't search the listings: the search server (mcp_server.py) "
            "didn't start or refused the call.\n"
            "Run `python mcp_server.py` on its own to see its error, fix that, "
            "then run the same search again."
        )
        trace.step("search_listings (via MCP)", inputs=str(parsed),
                   note=f"MCP call failed, stopping: {str(exc).splitlines()[0]}")
        return session

    # THE BRANCH — nothing found: say what to change and stop before suggest_outfit
    if not session["search_results"]:
        session["error"] = _no_results_message(parsed)
        trace.step("branch: no results", inputs=str(parsed), returned=session["error"],
                   note="search empty, stopping before suggest_outfit")
        return session

    # Step 3 — pick the best match
    steps += 1
    trace.check_iterations(steps)
    session["selected_item"] = session["search_results"][0]
    trace.step("select_item", inputs=session["search_results"],
               returned=session["selected_item"], note="first result")

    # Steps 4 and 5 call the model. If it can't be reached, keep what search
    # found, say what broke and what to do, and stop instead of raising.
    calling = "suggest_outfit"
    try:
        # Step 4 — style it. _styled records the id of the item it actually hands
        # to suggest_outfit (criterion 3).
        steps += 1
        trace.check_iterations(steps)
        session["outfit_suggestion"] = _styled(session, session["selected_item"])
        wardrobe_items = (session["wardrobe"] or {}).get("items") or []
        trace.step("suggest_outfit",
                   inputs=f"item {session['outfit_input_id']}: {session['selected_item']['title']}; "
                          f"wardrobe: {len(wardrobe_items)} items",
                   returned=session["outfit_suggestion"])

        # Step 5 — write the caption, reading both inputs back out of the session.
        # _captioned records the id of the item it actually hands to create_fit_card.
        calling = "create_fit_card"
        steps += 1
        trace.check_iterations(steps)
        session["fit_card"] = _captioned(
            session, session["outfit_suggestion"], session["selected_item"]
        )
        trace.step("create_fit_card",
                   inputs=f"item {session['fit_card_input_id']}: {session['selected_item']['title']}; "
                          f"outfit: {session['outfit_suggestion']}",
                   returned=session["fit_card"])
    except ModelUnavailable as exc:
        item = session["selected_item"]
        session["error"] = (
            f"Found \"{item['title']}\" (${item['price']:g} on {item['platform']}), "
            "but couldn't reach the styling model to build an outfit.\n"
            f"{exc}\n"
            "Then run the same search again."
        )
        trace.step(calling, inputs=item, note=f"model unavailable, stopping: {exc}")
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

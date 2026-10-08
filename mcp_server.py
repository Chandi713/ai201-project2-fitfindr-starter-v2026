"""
Your MCP server. ← UNIT 4, MILESTONE 1

Right now your tools only exist inside your own program. Nothing else can reach
them. MCP is an agreed shape you wrap a tool in so that anything speaking the
same protocol can call it — your agent today, a different agent tomorrow,
someone else's app after that.

**You're moving one tool. Not three.** The point is to see the seam.
`search_listings` is the one to move: it doesn't call the model, so nothing is
slow and nothing changes between runs while you're learning the shape.

    python mcp_server.py        starts the server (it will just sit there — that's right)
    python mcp_client.py        asks the server what it offers

─────────────────────────────────────────────────────────────────────────────
TODO — register one tool.

Uncomment the block below and fill it in. Three things matter:

  1. **The name.** Exactly what your agent will ask for.

  2. **The description.** This is the part that isn't code and matters most.
     Write it before you look at the example. You are not writing it for your
     agent — you're writing it for an agent someone else builds, that will
     never see your implementation. That isn't hypothetical; it's what every
     MCP server on the registry is.

     Two things to get right: name units and types ("price" is ambiguous,
     "max_price, in whole dollars" isn't), and state the empty case. Last unit
     the empty case was on your spec sheet for your loop's benefit. Here it's
     part of a published contract.

  3. **The typed inputs.** These come straight from your Tool Inventory. If the
     types here don't match your README, one of the two is wrong — fix it.

Then point your agent at it. In `run_agent()`, swap the direct call:

    results = search_listings(description, size, max_price)

for the MCP one:

    from mcp_client import call_tool
    results = call_tool("search_listings", {
        "description": description,
        "size": size,
        "max_price": max_price,
    })

**What comes back should not change.** If it does, that difference is your
first clue about what your tool was really returning before.

🛑 Stop rule: if this isn't connecting after 40 minutes, stop. Keep your direct
call, and write down in your README exactly where it broke — the error text and
the last thing that worked. Then carry on to Milestone 2. Everything after this
works with a direct call, and **a documented failure earns the point in full.**
─────────────────────────────────────────────────────────────────────────────
"""

from mcp.server.fastmcp import FastMCP

from tools import search_listings as _search_listings_impl  # noqa: F401 — you'll use this below

# log_level="WARNING" keeps the server from printing an INFO line for every
# request. Without it your terminal fills with "Processing request of type
# CallToolRequest" and the output you actually care about scrolls away.
mcp = FastMCP("fitfindr", log_level="WARNING")


# ── TODO: uncomment and fill this in ──────────────────────────────────────────
#
@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search 40 second-hand clothing listings from Depop, Poshmark and thredUP for items matching the user's keywords. Listings are tops, bottoms, outerwear, shoes and accessories.

    **Input:**
    * `description` (string, required): Keywords describing the desired item, e.g. "vintage graphic tee". Keywords are matched against each listing's title, description, category, style tags and colors. The `brand` field is not searched, though a brand that appears in the title still matches. A size written inside `description` (e.g. "tee size M") does not filter results; it only moves listings in that size ahead when scores tie.

    * `size` (string, optional): Keep only listings in this size. Matching is case-insensitive and by whole size, not substring: `"M"` matches `"M"`, `"S/M"` and `"M/L"`; `"W30"` matches `"W30 L30"`; a bare number such as `"8.5"` means US shoe size `"US 8.5"`. `"L"` does not match `"XL"`, and `"S"` does not match `"US 9"`. Omit or set to `null` for no size filter.

    * `max_price` (number, optional): Maximum listing price in US dollars, inclusive, so a listing priced exactly at `max_price` is kept. `0` is a real limit, not "no filter". Omit or set to `null` for no price filter.


    **Matching and filtering:**
    1. Apply the `size` filter and the `max_price` filter, each only when provided.
    2. Drop filler words (e.g. "the", "with", "looking", "under") from `description` and from each listing.
    3. Score each remaining listing by how many distinct keywords from `description` it contains.
    4. Keep every listing that shares at least one keyword (score of 1 or more).
    5. Sort by score, highest first; on a tie, listings in a size written inside `description` come first.
    6. Return at most 10.


    **Output:**
    A list of up to 10 listing objects, most keyword matches first. Each object has:

    * `id` (string)
    * `title` (string)
    * `description` (string)
    * `category` (string: tops, bottoms, outerwear, shoes or accessories)
    * `style_tags` (list of strings)
    * `size` (string, e.g. "M", "S/M", "W30 L30", "US 8.5", "One Size")
    * `condition` (string)
    * `price` (number, US dollars)
    * `colors` (list of strings)
    * `brand` (string or `null`; most listings have no brand)
    * `platform` (string: depop, poshmark or thredUp)


    **When nothing matches:**
    Returns an empty list `[]` when the size or price filter leaves no listings, or when no remaining listing shares a keyword with `description`. Never returns `null` and never raises an error.
    """
    return _search_listings_impl(description, size, max_price)
#
# ──────────────────────────────────────────────────────────────────────────────
#
# Two notes on the block above.
#
# The registered name is the *function* name — so the block above registers
# "search_listings", which is exactly what call_tool("search_listings", ...)
# asks for. That is also why the import at the top of this file brings the real
# implementation in under an alias: without it, the registered function and the
# one it calls would be the same name, and the tool would call itself.
#
# FastMCP builds the input schema from your type hints, which is why the hints
# are not optional here. `description: str` becomes a required string;
# `max_price: float | None = None` becomes an optional number. Getting these
# wrong is the most common reason a call is rejected.


if __name__ == "__main__":
    mcp.run()

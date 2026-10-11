"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
    {
        # A normal query. Criterion 3 — the same id in selected_item,
        # outfit_input_id and fit_card_input_id.
        "name": "item id carried through",
        "query": "black leather jacket under $80",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Five different items, one per scenario. Criterion 4 — price and
        # platform once each, 2–4 sentences under 80 words, unique openings.
        "name": "fit card: levi's jeans",
        "query": "vintage levis jeans",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # No brand on this listing.
        "name": "fit card: chelsea boots",
        "query": "suede chelsea boots",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # No brand on this listing.
        "name": "fit card: velvet blazer",
        "query": "velvet blazer",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        "name": "fit card: mary janes",
        "query": "platform mary janes",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # No brand on this listing.
        "name": "fit card: reversible bucket hat",
        "query": "reversible bucket hat",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # A non-empty wardrobe. Criterion 5 — at least one owned piece is
        # named in the outfit suggestion. A feminine floral dress against a
        # streetwear wardrobe, so the model is tempted to style it with
        # pieces the user doesn't own.
        "name": "wardrobe used in outfit",
        "query": "floral silk slip dress",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # Only a size, no item words. The weak point criterion 1's reason
        # predicted: the size is taken out and no keywords are left.
        "name": "size-only query",
        "query": "size M",
        "wardrobe": "example",
        "criterion": None,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems

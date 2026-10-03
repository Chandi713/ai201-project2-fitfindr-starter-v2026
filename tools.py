"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import config  # noqa: F401 — you'll use this in search_listings
import random
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────




def _parse_query(query: str) -> tuple[list[str], str | None]:
    import re

    LETTER = r"(?:xxs|xs|s|m|l|xl|xxl)"

    # Checked in this order; the first one that matches is
    SIZE_PATTERNS = [
        re.compile(r"\b(?:size\s+)?(w\d+(?:\s*l\d+)?)\b"),
        re.compile(r"\b(?:size\s+)?(us\s*\d+(?:\.\d+)?)(?!\.?\d)"),
        re.compile(r"\bsize\s+(\d+(?:\.\d+)?)(?!\.?\d)"),
        re.compile(r"\b(one\s+size)\b"),
        re.compile(rf"\b(?:size\s+)?({LETTER}/{LETTER})\b"),
        re.compile(r"\b(?:size\s+)?(xxs|xs|xl|xxl)\b"),
        re.compile(r"(?:^|(?<=\s))(?:size\s+)?([sml])(?=[\s,.;!?]|$)"),
    ]
    WORD_RE  = re.compile(r"[a-z0-9]+")

    text = query.lower()

    size = None
    for pattern in SIZE_PATTERNS:
        match = pattern.search(text)
        if match:
            size = match.group(1).upper()
            text = text[:match.start()] + " " + text[match.end():]
            break

    # 3. split what's left into words and drop stop words and one-letter leftovers
    words = [w for w in WORD_RE.findall(text) if len(w) > 1]

    return (words, size)


def _size_tokens(size: str) -> set[str]:
    """
    Break a size into the sizes it covers: "S/M" → {"s", "m"}, "W30 L30" →
    {"w30", "l30"}, "US 8.5" → {"us8.5"}, "XL (oversized)" → {"xl"}.

    A bare number is read as a US shoe size, so "8.5" → {"us8.5"}.
    """
    import re

    text = re.sub(r"\(.*?\)", " ", size.lower())   # drop notes like "(oversized)"
    text = re.sub(r"\bus\s+", "us", text)           # "us 8.5" → "us8.5"
    tokens = set(re.split(r"[/\s]+", text.strip())) - {""}
    return {"us" + t if re.fullmatch(r"\d+(?:\.\d+)?", t) else t for t in tokens}


def _size_matches(wanted: str, listing_size: str) -> bool:
    """
    True when every size in `wanted` is one the listing covers, so "M" matches
    "S/M" and "W30" matches "W30 L30", but "S" doesn't match "US 9" and "L"
    doesn't match "XL".
    """
    wanted_tokens = _size_tokens(wanted)
    return bool(wanted_tokens) and wanted_tokens <= _size_tokens(listing_size)


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    # TODO: replace this with your implementation
    import re
    import itertools
    STOPWORDS = {
        # filler found in the listings and in queries
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "for", "with",
        "to", "of", "from", "some", "no", "be", "can", "very", "like",
        "i", "me", "my", "is", "it", "that", "this", "any", "please",

        # request words
        "looking", "want", "need", "find", "show", "get", "something",

        # price and size words (the values are already saved separately)
        "under", "below", "less", "than", "max", "up", "around", "budget", "cheap",
        "size", "one", "fit", "fits",
    }
    listings = load_listings()
    if max_price is not None:
        listings = [listing for listing in listings if listing['price'] <= max_price]

    if size:
        listings = [listing for listing in listings if _size_matches(size, listing['size'])]

    

    words, found_size = _parse_query(description)
    words = set(w for w in words if w not in STOPWORDS)

    # score each listing without adding fields to it: (score, size_match, listing)
    scored = []
    for listing in listings:
        combined_text = listing['title'] + ' ' + listing['description'] + ' ' + listing['category']
        listing_words = re.findall(r"[a-z0-9]+", combined_text.lower())
        listing_words.extend(item.lower() for item in itertools.chain(listing["style_tags"], listing["colors"]))
        listing_words = set(w for w in listing_words if w not in STOPWORDS)
        score = len(words.intersection(listing_words))
        size_match = bool(found_size) and _size_matches(found_size, listing["size"])
        # keep every listing that scored at least one point
        if score > 0:
            scored.append((score, size_match, listing))

    # highest score first; on a tie, the listing in the size asked for comes first
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [listing for _, _, listing in scored[:config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def _clean_wardrobe(wardrobe: dict) -> dict:
    """
    Return a copy of the wardrobe with only the fields the model needs.

    Drops each item's 'id' (the model echoes it back to the user) and drops
    'notes' when it's None. The input wardrobe is left untouched.
    """
    cleaned_items = []
    for item in wardrobe['items']:
        cleaned = {k: v for k, v in item.items() if k != 'id'}
        if cleaned.get('notes') is None:
            cleaned.pop('notes', None)
        cleaned_items.append(cleaned)
    return {'items': cleaned_items}


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """

    if wardrobe.get('items'):
        cleaned_wardrobe = _clean_wardrobe(wardrobe)
        prompt = f"""
        Role: You are a fashion expert and have a good sense of styling. You very well understand what colors suit each other, what outfit gives a decent, subtle, and charming look. You can clearly pick which trouser or pant will suit a specific kind of shirt along with shoes and accessories.

        Task: You are given an item and its specifications listed in form of dictionary (contains fields like: category, style_tags, colors, etc.) from the listings on a thrift platform {new_item}, along with it you are given a set of items in the wardrobe {cleaned_wardrobe['items']}. Your task is to suggest an entire outfit (or a look) considering the new item and picking up the complementing item(s) from the user's wardrobe. **No need to consider the whole wardrobe in the suggestions, just pick up the items that are relevant to the new item.**
            Example: 
                New item: A white shirt with a green floral (leaves) print on it.
                User's wardrobe: A black t-shirt, a blue jeans, a pair of brown shoes, a black cap, a white shorts, a red t-shirt, a dark-green slides (flip-flops), an orange trouser, a pair of black sunglasses, a pair of brown boots, a blue baggy jeans, a pair of black sneakers.

        Output: A string output with your suggestions for the outfit(s) (No specific format, could be a paragraph, could be partitioned into multiple looks, etcetera):
            Look-1: A look consisting of a white shirt with a green floral (leaves) print on it, paired with white shorts, dark-green slides (flip-flops), and classic black sunglasses for a fresh, relaxed look.

            Look-2: A black t-shirt layered with the white shirt with a green floral (leaves) print on it, paired with blue baggy jeans, a pair of brown shoes, a black cap, and a pair of sunglasses for a casual, party vibe.

            Look-3: . . . and so on.
            .
            .
            .

        Note: Make sure to suggest at least one outfit, and return only the suggestion string, nothing else. Do not include any kind of instructions, irrelevant text, or comments.
        """
        response = generate(prompt)
    else:
        prompt = f"""
        Role: You are a fashion expert and have a good sense of styling. You very well understand what colors suit each other, what outfit gives a decent, subtle, and charming look. You can clearly pick which trouser or pant will suit a specific kind of shirt along with shoes and accessories.

        Task: You are given an item and its specifications listed in form of dictionary (contains fields like: category, style_tags, colors, etc.) from the listings on a thrift platform {new_item},  Your task is to suggest an entire outfit (or a look) considering the new item for a decent, classy, and elegant look.
            Example: New item: A white shirt with a green floral (leaves) print on it.

        Output: A string output with your suggestions for the outfit(s) (No specific format, could be a paragraph, could be partitioned into multiple looks, etcetera):
            Look-1: A look consisting of a white shirt with a green floral (leaves) print on it, paired with white shorts, dark-green slides (flip-flops), and classic black sunglasses for a fresh, relaxed look.

            Look-2: A black t-shirt layered with the white shirt with a green floral (leaves) print on it, paired with blue baggy jeans, a pair of brown shoes, a black cap, and a pair of sunglasses for a casual, party vibe.
            
            Look-3: . . . and so on.
            .
            .
            .
        
        Note: Make sure to suggest at least one outfit, and return only the suggestion string, nothing else. Do not include any kind of instructions, irrelevant text, or comments.
        """
        response = generate(prompt)
    return (response or "").strip() or "Couldn't generate an outfit suggestion — try again."



# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def _format_price(price) -> str:
    """
    Drop the decimals only when they're all zeros: 75.0 → "75", 12.5 → "12.5".
    """
    if isinstance(price, float) and price.is_integer():
        return str(int(price))
    return str(price)


def _combine_looks(outfit: str) -> str:
    """
    Turn "Look-1: abc\\nLook-2: def\\nLook-3: lds" into "abc. def. lds."

    If the outfit has no "Look-N:" labels, it comes back unchanged.
    """
    import re

    # matches "Look-1:", "Look 1:", and the bold "**Look-1:**"
    label = r"\**Look[-\s]?\d+\**:\**"
    if not re.search(label, outfit):
        return outfit.strip()

    looks = [look.strip().rstrip(".") for look in re.split(label, outfit)]
    return " ".join(look + "." for look in looks if look)


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    # TODO: replace this with your implementation
    if outfit.strip() == "Couldn't generate an outfit suggestion — try again." or outfit.strip() == "":
        return "No outfit suggestion provided (The model FAILED to generate an outfit suggestion) — try again."

    # "$24", not "24" — a bare number next to denim reads as a size
    price = "$" + _format_price(new_item['price'])
    outfit = _combine_looks(outfit)

    # most listings have no brand — only mention one when it's actually there
    brand = (new_item.get('brand') or "").strip()
    brand_detail = f"\n    - Brand: {brand}" if brand else ""
    brand_rule = "\n    - Mention the brand once." if brand else ""

    # a different opening each call, so the captions don't all start the same way
    opening = random.choice([
        "your first reaction to wearing it",
        "the vibe or mood of the outfit",
        "the occasion you'd wear it to",
        "a styling tip",
        "what caught your eye about the colour or texture",
        "a short question to your followers",
        "a short story about the item",
       "an incident related to the item"
    ])

    prompt = f"""
    Role: You are a fashion creator posting about a thrift find you just bought. Your captions are short, specific, and sound like a real person sharing an outfit, not a product listing or an ad.

    Task: Write a caption for the item below, styled with the outfit below.

    Item details:
    - Item: {new_item['title']}
    - Category: {new_item['category']}
    - Colors: {', '.join(new_item['colors'])}
    - Style: {', '.join(new_item['style_tags'])}
    - Price: {price} (price in $)
    - Platform: {new_item['platform']}{brand_detail}

    Outfit: {outfit}

    Rules:
    - Open with {opening}.
    - Do NOT start with "Scored", "Found", "Snagged", "Just got", "Obsessed", or any "I got this for $X on..." opener.
    - Mention the price and the platform once each, but not in the first sentence.
    - Write the price exactly as {price}, in digits with the $ sign, never in words.{brand_rule}
    - Call the item by a natural name (e.g. "this cream linen blazer"), never the listing title word for word.
    - Describe at most two looks from the outfit, without labels like "Look-1".
    - Don't invent details about the item's history or past owners.

    Output: 2-4 sentences, 60-70 words in total. Only use pieces from the item and the outfit above.

    Additional Context: Use it only if the details above aren't enough to make the caption specific.
        {new_item['description']}

    Note: Return only the caption, nothing else. No instructions, comments, or quotation marks around it.
    """
    response = generate(prompt)
    return (response or "").strip() or "Couldn't generate a caption — try again."
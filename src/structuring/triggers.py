"""
File description: Module for keyword synonym expansion
Purpose: Broadens intent detection accuracy by supplementing keywords with related terminology
How it works: Iterates through defined hard-coded sets of synonyms and attaches them to any matching base trigger
"""
def expand_triggers(triggers):
    # Expands base triggers matching explicit medical keywords
    synonyms = {
        "diagnosis": ["symptoms", "identify"],
        "treatment": ["therapy", "medication"],
        "referral": ["when to refer", "complications"]
    }

    expanded = set(triggers)

    # Extend the set with synonym mappings
    for t in triggers:
        for key, vals in synonyms.items():
            if key in t.lower():
                expanded.update(vals)

    return list(expanded)

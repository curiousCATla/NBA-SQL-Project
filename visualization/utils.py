"""
utils.py — Shared player name lookup utilities.

Used by analysis7.py and player_prog.py to resolve user-typed names
against the database, handling accented characters and typos.
"""

import unicodedata
import difflib


def normalize(name):
    """
    Strip accents and lowercase a name for comparison.
    Example: 'Luka Dončić' → 'luka doncic'
    """
    return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii').lower()


def build_name_map(players):
    """
    Build a lookup dict from a list of player names.
    Maps each normalized name back to its original form.
    Example: {'luka doncic': 'Luka Dončić', 'lebron james': 'LeBron James', ...}
    """
    return {normalize(p): p for p in players}


def lookup_player(raw_name, name_map):
    """
    Resolve a user-typed name to its canonical form in name_map.

    - Exact match (after normalization): returns immediately.
    - Close match found via fuzzy search: prompts yes/no/stop.
    - No match: asks the user to re-enter.

    Returns the canonical name string, or None if the user types 'stop'.
    """
    current_name = raw_name
    while True:
        match = name_map.get(normalize(current_name))
        if match:
            return match

        suggestions = difflib.get_close_matches(
            normalize(current_name), name_map.keys(), n=1, cutoff=0.6
        )
        if suggestions:
            closest = name_map[suggestions[0]]
            while True:
                answer = input(
                    f"'{current_name}' not found. Did you mean '{closest}'? (yes/no/stop): "
                ).strip().lower()
                if answer == 'yes':
                    return closest
                elif answer == 'no':
                    current_name = input("Re-enter player name: ").strip()
                    break
                elif answer == 'stop':
                    return None
                else:
                    print("Please type yes, no, or stop.")
        else:
            print(f"'{current_name}' not found and no close matches.")
            current_name = input("Re-enter player name (or type 'stop'): ").strip()
            if current_name.lower() == 'stop':
                return None

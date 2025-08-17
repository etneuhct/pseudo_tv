# -*- coding: utf-8 -*-
"""
Validator for TV catalog specification (Category A checks).
CLI usage:
  python validator_catalogue_tv.py <catalog.json>
"""

import json
import sys
from typing import Any, Dict, List

ALLOWED_SLOT_FORMATS = [
    {"show_min_duration": 22, "show_max_duration": 26, "slot_duration": 30},
    {"show_min_duration": 45, "show_max_duration": 52, "slot_duration": 60},
    {"show_min_duration": 70, "show_max_duration": 80, "slot_duration": 90},
    {"show_min_duration": 95, "show_max_duration": 110, "slot_duration": 120},
    {"show_min_duration": 12, "show_max_duration": 13, "slot_duration": 15},
]

ALLOWED_TYPES = {"series", "movie"}

ALLOWED_CRITERIA_CATEGORIES = {"genre", "type", "language", "duration"}

# Genres normalisés (clés seulement)
GENRES_NORMALISES = {
  "Podcast": ["Podcast"],
  "Animation": ["Animation", "Anime"],
  "Science-Fiction": ["Science-Fiction", "Science Fiction", "Science-Fiction & Fantastique"],
  "Fantastique": ["Fantastique", "Fantasy", "Science-Fiction & Fantastique"],
  "Family": ["Family", "Familial", "Children"],
  "Horror": ["Horror", "Horreur"],
  "Mini-Series": ["Mini-Series"],
  "Documentaire": ["Documentaire", "Vulgarisation"],
  "Histoire": ["Histoire", "History"],
  "Action": ["Action", "Action & Adventure"],
  "Aventure": ["Aventure", "Adventure", "Action & Adventure"],
  "Crime": ["Crime"],
  "War & Politics": ["War & Politics", "Guerre"],
  "Talk Show": ["Talk Show"],
  "Comédie": ["Comédie", "Comedy"],
  "Jeux télé": ["Jeux télé"],
  "Sport": ["Sport"],
  "Western": ["Western"],
  "Drame": ["Drame", "Drama"],
  "Martial Arts": ["Martial Arts"],
  "Suspense": ["Suspense", "Thriller"],
  "Mystery": ["Mystery", "Mystère"],
  "Romance": ["Romance"],
  "YouTube": ["YouTube"]
}

GENRE_KEYS = set(GENRES_NORMALISES.keys())

def almost_equal(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol

def is_allowed_slot_format(sf: Dict[str, Any]) -> bool:
    return any(
        sf.get("show_min_duration") == x["show_min_duration"]
        and sf.get("show_max_duration") == x["show_max_duration"]
        and sf.get("slot_duration") == x["slot_duration"]
        for x in ALLOWED_SLOT_FORMATS
    )

def validate_catalog_struct(catalog: Dict[str, Any]) -> List[str]:
    errs = []
    for key in ("name", "step", "channels"):
        if key not in catalog:
            errs.append(f"[catalog] clé manquante: {key}")
    if "channels" in catalog and not isinstance(catalog["channels"], list):
        errs.append("[catalog] 'channels' doit être une liste")
    return errs

def validate_channel(channel: Dict[str, Any], idx: int) -> List[str]:
    errs = []
    prefix = f"[channel#{idx}:{channel.get('name','?')}]"
    required = ("name", "description", "begin", "end", "fillers", "blocks")
    for k in required:
        if k not in channel:
            errs.append(f"{prefix} clé manquante: {k}")
    # types de base
    try:
        begin = float(channel.get("begin", 0))
        end = float(channel.get("end", 0))
        if not (begin < end):
            errs.append(f"{prefix} begin < end requis (begin={begin}, end={end})")
    except Exception:
        errs.append(f"{prefix} begin/end doivent être numériques")
        begin = None
        end = None

    # fillers
    fillers = channel.get("fillers", [])
    if not isinstance(fillers, list):
        errs.append(f"{prefix} 'fillers' doit être une liste")
    else:
        for g in fillers:
            if g not in GENRE_KEYS:
                errs.append(f"{prefix} filler genre inconnu (clé normalisée requise): {g}")

    # blocks
    blocks = channel.get("blocks", [])
    if not isinstance(blocks, list) or len(blocks) == 0:
        errs.append(f"{prefix} 'blocks' doit être une liste non vide")
        return errs  # can't continue

    # tri et continuité sans trous
    try:
        blocks_sorted = sorted(blocks, key=lambda b: float(b["begin"]))
    except Exception:
        errs.append(f"{prefix} impossible de trier les blocs par 'begin' (valeurs numériques requises)")
        return errs

    # vérif premier/dernier et chainage
    if begin is not None and end is not None:
        first_begin = float(blocks_sorted[0]["begin"])
        last_end = float(blocks_sorted[-1]["end"])
        if not almost_equal(first_begin, begin):
            errs.append(f"{prefix} le 1er bloc doit commencer à 'begin' (attendu {begin}, reçu {first_begin})")
        if not almost_equal(last_end, end):
            errs.append(f"{prefix} le dernier bloc doit finir à 'end' (attendu {end}, reçu {last_end})")

        for i in range(len(blocks_sorted) - 1):
            cur_end = float(blocks_sorted[i]["end"])
            nxt_begin = float(blocks_sorted[i+1]["begin"])
            if cur_end > nxt_begin + 1e-6:
                errs.append(f"{prefix} chevauchement blocs {i} et {i+1} (end {cur_end} > begin {nxt_begin})")
            if not almost_equal(cur_end, nxt_begin):
                errs.append(f"{prefix} trou entre blocs {i} et {i+1} (end {cur_end} != begin {nxt_begin})")

        # aucun bloc ne doit sortir de la plage globale
        for j, b in enumerate(blocks_sorted):
            b_begin = float(b["begin"])
            b_end = float(b["end"])
            if b_begin < begin - 1e-6 or b_end > end + 1e-6:
                errs.append(f"{prefix} bloc#{j} hors de la plage chaîne (block [{b_begin},{b_end}] vs [{begin},{end}])")

    # valider chaque bloc
    for j, b in enumerate(blocks_sorted):
        errs.extend(validate_block(b, f"{prefix}[block#{j}]"))
    return errs

def validate_block(block: Dict[str, Any], prefix: str) -> List[str]:
    errs = []
    for k in ("criteria", "begin", "end", "slot_count", "slot_format", "shows"):
        if k not in block:
            errs.append(f"{prefix} clé manquante: {k}")
    try:
        begin = float(block.get("begin", 0))
        end = float(block.get("end", 0))
        if not (begin < end):
            errs.append(f"{prefix} begin < end requis (begin={begin}, end={end})")
    except Exception:
        errs.append(f"{prefix} begin/end doivent être numériques")
        begin = None
        end = None

    # slot_count
    slot_count = block.get("slot_count")
    if slot_count not in (1, 2):
        errs.append(f"{prefix} slot_count doit être 1 ou 2 (reçu {slot_count})")

    # slot_format
    sf = block.get("slot_format", {})
    if not isinstance(sf, dict) or not is_allowed_slot_format(sf):
        errs.append(f"{prefix} slot_format non autorisé ou invalide: {sf}")

    # durée du bloc
    if isinstance(sf, dict) and begin is not None and end is not None and isinstance(slot_count, int):
        expected_hours = (sf.get("slot_duration", 0) * slot_count) / 60.0
        actual_hours = end - begin
        if not almost_equal(expected_hours, actual_hours):
            errs.append(f"{prefix} durée bloc {actual_hours}h ≠ {expected_hours}h attendu (slot_duration*slot_count)")

    # criteria
    criteria = block.get("criteria", [])
    if not isinstance(criteria, list) or len(criteria) == 0:
        errs.append(f"{prefix} criteria doit être une liste non vide")
    else:
        for k, crit in enumerate(criteria):
            errs.extend(validate_criterion(crit, f"{prefix}[criteria#{k}]"))

    # shows
    if "shows" not in block:
        errs.append(f"{prefix} 'shows' manquant")
    elif not isinstance(block["shows"], list):
        errs.append(f"{prefix} 'shows' doit être une liste")

    return errs

def validate_criterion(crit: Dict[str, Any], prefix: str) -> List[str]:
    errs = []
    cat = crit.get("category")
    if cat not in ALLOWED_CRITERIA_CATEGORIES:
        errs.append(f"{prefix} category invalide: {cat} (attendu {sorted(ALLOWED_CRITERIA_CATEGORIES)})")

    # forbidden bool
    forbidden = crit.get("forbidden")
    if not isinstance(forbidden, bool):
        errs.append(f"{prefix} 'forbidden' doit être booléen (True/False)")

    # values list checks
    values = crit.get("values")
    if not isinstance(values, list) or len(values) == 0:
        errs.append(f"{prefix} 'values' doit être une liste non vide")
    else:
        # validation par catégorie
        if cat == "genre":
            for v in values:
                if v not in GENRE_KEYS:
                    errs.append(f"{prefix} genre inconnu (clé normalisée requise): {v}")
        elif cat == "type":
            for v in values:
                if v not in ALLOWED_TYPES:
                    errs.append(f"{prefix} type invalide: {v} (attendu {sorted(ALLOWED_TYPES)})")
        elif cat == "language":
            for v in values:
                if not isinstance(v, str):
                    errs.append(f"{prefix} language doit être string (reçu {type(v).__name__})")
        elif cat == "duration":
            for v in values:
                if not isinstance(v, (int, float)):
                    errs.append(f"{prefix} duration doit être numérique en minutes (reçu {type(v).__name__})")
                elif v <= 0:
                    errs.append(f"{prefix} duration doit être > 0 (reçu {v})")
    return errs

def validate_catalog(catalog: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    errors.extend(validate_catalog_struct(catalog))
    channels = catalog.get("channels", []) if isinstance(catalog, dict) else []
    if isinstance(channels, list):
        for i, ch in enumerate(channels):
            errors.extend(validate_channel(ch, i))
    return errors

def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: python validator_catalogue_tv.py <catalog.json>", file=sys.stderr)
        return 2
    path = argv[1]
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    errs = validate_catalog(data)
    if not errs:
        print("✅ Catalogue valide (règles catégorie A).")
        return 0
    else:
        print("❌ Erreurs détectées :")
        for e in errs:
            print("-", e)
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
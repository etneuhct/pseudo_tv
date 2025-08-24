#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_catalog_rules.py
-------------------------

Ce module effectue une validation plus poussée qu'une simple vérification de
structure. Il s'appuie sur les définitions et les constantes décrites dans
le cahier des charges pour vérifier que le catalogue respecte l'ensemble des
règles métier : continuité horaire des blocs, formats de slots autorisés,
valeurs des critères, etc.

Pour l'utiliser en ligne de commande :

    python validate_catalog_rules.py <catalog.json>

Le script affichera « ✅ Catalogue valide » si aucune erreur n'est détectée,
sinon il listera toutes les erreurs relevées. Les fonctions de validation
sont également exportées pour être utilisées dans des tests unitaires ou
depuis un autre module.

"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List

from validate_json_structure import (
    validate_catalog_structure,
    GENRES_NORMALISES_KEYS,
)

# Définition des formats de slot autorisés. Chaque élément est un dict
# contenant la durée minimale et maximale d'un show et la durée du slot en
# minutes. Ces valeurs correspondent au cahier des charges (§5).
ALLOWED_SLOT_FORMATS = [
    {"show_min_duration": 22, "show_max_duration": 26, "slot_duration": 30},
    {"show_min_duration": 45, "show_max_duration": 52, "slot_duration": 60},
    {"show_min_duration": 70, "show_max_duration": 80, "slot_duration": 90},
    {"show_min_duration": 95, "show_max_duration": 110, "slot_duration": 120},
    {"show_min_duration": 12, "show_max_duration": 13, "slot_duration": 15},
]

# Types autorisés pour les shows (§6)
ALLOWED_TYPES = {"series", "movie"}

# Catégories autorisées pour les critères (§4)
ALLOWED_CRITERIA_CATEGORIES = {"genre", "type", "language", "duration"}


def almost_equal(a: float, b: float, tol: float = 1e-6) -> bool:
    """Compare deux nombres flottants en considérant une tolérance.

    Une tolérance est nécessaire afin de ne pas signaler des erreurs dues à
    l'arrondi lors des calculs de durée des blocs.

    Args:
        a: Premier nombre.
        b: Second nombre.
        tol: Tolérance absolue.

    Returns:
        True si |a - b| <= tol, False sinon.
    """
    return abs(a - b) <= tol


def is_allowed_slot_format(sf: Dict[str, Any]) -> bool:
    """Indique si un slot_format est parmi les formats autorisés.

    Args:
        sf: Dictionnaire contenant les clés show_min_duration, show_max_duration
            et slot_duration.

    Returns:
        True si un format identique est défini dans ALLOWED_SLOT_FORMATS.
    """
    return any(
        sf.get("show_min_duration") == x["show_min_duration"]
        and sf.get("show_max_duration") == x["show_max_duration"]
        and sf.get("slot_duration") == x["slot_duration"]
        for x in ALLOWED_SLOT_FORMATS
    )


def validate_catalog_rules(catalog: Dict[str, Any]) -> List[str]:
    """Valide les règles métier du catalogue.

    Cette fonction commence par valider la structure de l'objet via
    :func:`validate_catalog_structure`. Ensuite, pour chaque chaîne, elle
    valide la cohérence des horaires et des blocs et enfin vérifie les
    critères. Les erreurs de structure et de règles sont concatenées.

    Args:
        catalog: Dictionnaire représentant le catalogue.

    Returns:
        Une liste de messages d'erreurs. Vide si aucune erreur.
    """
    errors: List[str] = []
    # Première étape : valider la structure.
    errors.extend(validate_catalog_structure(catalog))
    channels = catalog.get("channels", []) if isinstance(catalog, dict) else []
    if isinstance(channels, list):
        for i, channel in enumerate(channels):
            if not isinstance(channel, dict):
                # Erreur de structure déjà signalée
                continue
            errors.extend(validate_channel_rules(channel, i))
    return errors


def validate_channel_rules(channel: Dict[str, Any], idx: int) -> List[str]:
    """Valide les règles métier propres à une chaîne.

    On vérifie les horaires globaux (begin < end), la continuité des blocs,
    l'absence de chevauchement et de trous, puis les règles de chaque bloc.

    Args:
        channel: Dictionnaire représentant la chaîne.
        idx: Indice de la chaîne dans la liste.

    Returns:
        Une liste de messages d'erreurs concernant cette chaîne.
    """
    errors: List[str] = []
    prefix = f"[channel#{idx}:{channel.get('name', '?')}]"
    # Valider begin < end
    try:
        begin = float(channel.get("begin", 0))
        end = float(channel.get("end", 0))
        if not (begin < end):
            errors.append(f"{prefix} begin < end requis (begin={begin}, end={end})")
    except Exception:
        # Type invalide déjà signalé par la validation de structure
        begin = None
        end = None
    # Vérification des fillers (genre normalisés déjà partiellement contrôlé dans la structure)
    fillers = channel.get("fillers", [])
    if isinstance(fillers, list):
        for g in fillers:
            if g not in GENRES_NORMALISES_KEYS:
                errors.append(f"{prefix} filler genre inconnu (clé normalisée requise) : {g}")
    # Vérification des blocs
    blocks = channel.get("blocks", [])
    if not isinstance(blocks, list) or len(blocks) == 0:
        # Structure invalide déjà signalée
        return errors
    # Trier les blocs par heure de début pour vérifier la continuité
    try:
        blocks_sorted = sorted(blocks, key=lambda b: float(b.get("begin", 0)))
    except Exception:
        errors.append(f"{prefix} impossible de trier les blocs par 'begin' (valeurs numériques requises)")
        return errors
    # Vérifier que les blocs couvrent la plage [begin, end] sans trous ni chevauchements
    if begin is not None and end is not None:
        first_begin = float(blocks_sorted[0].get("begin", 0))
        last_end = float(blocks_sorted[-1].get("end", 0))
        if not almost_equal(first_begin, begin):
            errors.append(
                f"{prefix} le 1er bloc doit commencer à 'begin' (attendu {begin}, reçu {first_begin})"
            )
        if not almost_equal(last_end, end):
            errors.append(
                f"{prefix} le dernier bloc doit finir à 'end' (attendu {end}, reçu {last_end})"
            )
        for i in range(len(blocks_sorted) - 1):
            cur_end = float(blocks_sorted[i].get("end", 0))
            nxt_begin = float(blocks_sorted[i + 1].get("begin", 0))
            if cur_end > nxt_begin + 1e-6:
                errors.append(
                    f"{prefix} chevauchement blocs {i} et {i+1} (end {cur_end} > begin {nxt_begin})"
                )
            if not almost_equal(cur_end, nxt_begin):
                errors.append(
                    f"{prefix} trou entre blocs {i} et {i+1} (end {cur_end} != begin {nxt_begin})"
                )
        # Vérifier qu'aucun bloc ne dépasse la plage globale
        for j, b in enumerate(blocks_sorted):
            try:
                b_begin = float(b.get("begin", 0))
                b_end = float(b.get("end", 0))
                if b_begin < begin - 1e-6 or b_end > end + 1e-6:
                    errors.append(
                        f"{prefix} bloc#{j} hors de la plage chaîne (block [{b_begin},{b_end}] vs [{begin},{end}])"
                    )
            except Exception:
                # Types invalides déjà signalés
                pass
    # Valider chaque bloc
    for j, block in enumerate(blocks_sorted):
        if isinstance(block, dict):
            errors.extend(validate_block_rules(block, f"{prefix}[block#{j}]"))
    return errors


def validate_block_rules(block: Dict[str, Any], prefix: str) -> List[str]:
    """Valide les règles métier propres à un bloc.

    On vérifie la cohérence des horaires (begin < end), la durée du bloc
    relativement aux slots, le nombre de slots autorisé, le format du slot
    ainsi que la validité des critères.

    Args:
        block: Dictionnaire représentant le bloc.
        prefix: Chaîne utilisée pour préfixer les messages d'erreurs.

    Returns:
        Liste des erreurs détectées pour ce bloc.
    """
    errors: List[str] = []
    # Vérifier begin < end
    try:
        begin = float(block.get("begin", 0))
        end = float(block.get("end", 0))
        if not (begin < end):
            errors.append(f"{prefix} begin < end requis (begin={begin}, end={end})")
    except Exception:
        # Type invalide déjà signalé dans la structure
        begin = None
        end = None
    # slot_count
    slot_count = block.get("slot_count")
    if slot_count not in (1, 2):
        errors.append(f"{prefix} slot_count doit être 1 ou 2 (reçu {slot_count})")
    # slot_format
    sf = block.get("slot_format", {})
    if not isinstance(sf, dict) or not is_allowed_slot_format(sf):
        errors.append(f"{prefix} slot_format non autorisé ou invalide : {sf}")
    # Durée du bloc (en heures) : (slot_duration * slot_count) / 60
    if (
        begin is not None
        and end is not None
        and isinstance(slot_count, int)
        and isinstance(sf, dict)
    ):
        try:
            slot_duration = float(sf.get("slot_duration", 0))
            expected_hours = (slot_duration * slot_count) / 60.0
            actual_hours = end - begin
            if not almost_equal(expected_hours, actual_hours):
                errors.append(
                    f"{prefix} durée bloc {actual_hours}h ≠ {expected_hours}h attendu (slot_duration*slot_count)"
                )
        except Exception:
            # Erreur de conversion, déjà signalée
            pass
    # criteria
    criteria = block.get("criteria", [])
    if not isinstance(criteria, list) or len(criteria) == 0:
        errors.append(f"{prefix} criteria doit être une liste non vide")
    else:
        for k, crit in enumerate(criteria):
            if not isinstance(crit, dict):
                errors.append(f"{prefix}[criteria#{k}] doit être un objet JSON")
                continue
            errors.extend(
                validate_criterion_rules(
                    crit,
                    f"{prefix}[criteria#{k}]",
                )
            )
    # shows : on vérifie seulement le type (liste). Contenu non testé ici.
    shows = block.get("shows")
    if shows is not None and not isinstance(shows, list):
        errors.append(f"{prefix} 'shows' doit être une liste")
    return errors


def validate_criterion_rules(crit: Dict[str, Any], prefix: str) -> List[str]:
    """Valide les règles métier pour un critère.

    Cette fonction vérifie que la catégorie est autorisée et que les valeurs
    fournies respectent le type attendu. Pour les genres, seules les clés
    normalisées sont acceptées. Pour les types, seules "series" ou
    "movie" sont autorisées. La durée doit être un nombre strictement
    positif.

    Args:
        crit: Dictionnaire représentant le critère.
        prefix: Préfixe pour les messages d'erreurs.

    Returns:
        Une liste d'erreurs pour ce critère.
    """
    errors: List[str] = []
    cat = crit.get("category")
    if cat not in ALLOWED_CRITERIA_CATEGORIES:
        errors.append(
            f"{prefix} category invalide : {cat} (attendu {sorted(ALLOWED_CRITERIA_CATEGORIES)})"
        )
    # forbidden doit être booléen
    forbidden = crit.get("forbidden")
    if not isinstance(forbidden, bool):
        errors.append(f"{prefix} 'forbidden' doit être booléen (True/False)")
    # values doit être une liste non vide
    values = crit.get("values")
    if not isinstance(values, list) or len(values) == 0:
        errors.append(f"{prefix} 'values' doit être une liste non vide")
    else:
        # Validation par catégorie
        if cat == "genre":
            for v in values:
                if v not in GENRES_NORMALISES_KEYS:
                    errors.append(
                        f"{prefix} genre inconnu (clé normalisée requise) : {v}"
                    )
        elif cat == "type":
            for v in values:
                if v not in ALLOWED_TYPES:
                    errors.append(
                        f"{prefix} type invalide : {v} (attendu {sorted(ALLOWED_TYPES)})"
                    )
        elif cat == "language":
            for v in values:
                if not isinstance(v, str):
                    errors.append(
                        f"{prefix} language doit être une chaîne (reçu {type(v).__name__})"
                    )
        elif cat == "duration":
            for v in values:
                if not isinstance(v, (int, float)):
                    errors.append(
                        f"{prefix} duration doit être numérique en minutes (reçu {type(v).__name__})"
                    )
                elif v <= 0:
                    errors.append(
                        f"{prefix} duration doit être > 0 (reçu {v})"
                    )
    return errors


def main(args: List[str]) -> int:
    """Point d'entrée CLI pour valider un catalogue.

    Charge le fichier JSON passé en argument, exécute la validation de
    structure puis de règles et affiche les erreurs éventuelles.

    Returns:
        0 si aucune erreur, 1 sinon (ou 2 en cas de mauvaise utilisation).
    """
    if len(args) < 2:
        print(
            "Usage : python validate_catalog_rules.py <catalog.json>",
            file=sys.stderr,
        )
        return 2
    path = args[1]
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"❌ Le fichier n'est pas un JSON valide : {exc}")
        return 1
    except FileNotFoundError:
        print(f"❌ Fichier introuvable : {path}")
        return 1
    errors = validate_catalog_rules(data)
    if not errors:
        print("✅ Catalogue valide (structure et règles).")
        return 0
    else:
        print("❌ Erreurs détectées :")
        for e in errors:
            print("-", e)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
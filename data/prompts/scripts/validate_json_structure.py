#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_json_structure.py
-------------------------

Ce module fournit des fonctions pour vérifier qu'un catalogue de chaînes télé
est bien structuré selon les types attendus. L'objectif principal de ce
script est de s'assurer que le JSON final produit par un agent de génération
respecte la forme imposée par les définitions de données décrites dans
`data_types.py`. Une validation stricte de la structure permet de détecter
rapidement les erreurs grossières avant de passer à la vérification des
règles métiers plus complexes.

Usage en ligne de commande :

    python validate_json_structure.py <catalog.json>

Le script charge le fichier JSON passé en argument et vérifie la présence
des clés obligatoires ainsi que le type de chacune. En cas d'erreur, une
liste de messages explicites est affichée.

Les fonctions de validation sont également disponibles pour un usage
programmatique (par exemple depuis des tests unitaires) : utilisez
``validate_catalog_structure(data)`` pour obtenir la liste des erreurs.

"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List

# Constantes pour les catégories et types autorisés
ALLOWED_CRITERIA_CATEGORIES = {"genre", "type", "language", "duration"}
ALLOWED_TYPES = {"series", "movie"}

# Genres normalisés – les clés attendues côté agent. Voir specification.
GENRES_NORMALISES_KEYS = {
    "Podcast",
    "Animation",
    "Science-Fiction",
    "Fantastique",
    "Family",
    "Horror",
    "Mini-Series",
    "Documentaire",
    "Histoire",
    "Action",
    "Aventure",
    "Crime",
    "War & Politics",
    "Talk Show",
    "Comédie",
    "Jeux télé",
    "Sport",
    "Western",
    "Drame",
    "Martial Arts",
    "Suspense",
    "Mystery",
    "Romance",
    "YouTube",
}


def validate_catalog_structure(catalog: Dict[str, Any]) -> List[str]:
    """Valide la structure de l'objet catalogue.

    Vérifie que le dictionnaire fourni contient les clés principales
    (`name`, `step`, `channels`) et que `channels` est une liste. Ensuite
    chaque chaîne est validée à son tour via :func:`validate_channel_structure`.

    Args:
        catalog: Dictionnaire représentant le catalogue.

    Returns:
        Une liste de messages d'erreurs. Vide si aucune erreur.
    """
    errors: List[str] = []
    # Clés obligatoires au niveau catalogue
    required_keys = ("name", "step", "channels")
    for key in required_keys:
        if key not in catalog:
            errors.append(f"[catalog] clé manquante : {key}")
    # Type de channels
    channels = catalog.get("channels")
    if channels is not None and not isinstance(channels, list):
        errors.append("[catalog] 'channels' doit être une liste")
    # Valider chaque chaîne
    if isinstance(channels, list):
        for i, channel in enumerate(channels):
            if not isinstance(channel, dict):
                errors.append(f"[catalog] channel#{i} doit être un objet JSON")
                continue
            errors.extend(validate_channel_structure(channel, i))
    return errors


def validate_channel_structure(channel: Dict[str, Any], idx: int) -> List[str]:
    """Valide la structure d'une chaîne (Channel).

    Vérifie que toutes les clés attendues sont présentes et que leurs types
    sont corrects. Ne vérifie pas les règles métiers (horaires continus,
    format de slot, etc.) – ces vérifications sont déléguées à un autre
    module.

    Args:
        channel: Dictionnaire représentant la chaîne.
        idx: Indice de la chaîne dans la liste, utilisé pour les messages.

    Returns:
        Une liste de messages d'erreurs. Vide si aucune erreur.
    """
    errors: List[str] = []
    prefix = f"[channel#{idx}:{channel.get('name', '?')}]"
    # Champs obligatoires pour la chaîne
    required = ("name", "description", "begin", "end", "fillers", "blocks")
    for key in required:
        if key not in channel:
            errors.append(f"{prefix} clé manquante : {key}")
    # Types élémentaires
    if "name" in channel and not isinstance(channel["name"], str):
        errors.append(f"{prefix} 'name' doit être une chaîne de caractères")
    if "description" in channel and not isinstance(channel["description"], str):
        errors.append(f"{prefix} 'description' doit être une chaîne de caractères")
    # Horaires début/fin : on laisse le type flottant ou int
    for time_key in ("begin", "end"):
        if time_key in channel:
            if not isinstance(channel[time_key], (int, float)):
                errors.append(f"{prefix} '{time_key}' doit être un nombre (int ou float)")
    # Fillers
    fillers = channel.get("fillers")
    if fillers is not None:
        if not isinstance(fillers, list):
            errors.append(f"{prefix} 'fillers' doit être une liste")
        else:
            for filler in fillers:
                if not isinstance(filler, str):
                    errors.append(f"{prefix} 'fillers' doit contenir uniquement des chaînes de caractères")
                elif filler not in GENRES_NORMALISES_KEYS:
                    errors.append(f"{prefix} filler genre inconnu (clé normalisée requise) : {filler}")
    # Blocks
    blocks = channel.get("blocks")
    if blocks is not None:
        if not isinstance(blocks, list) or len(blocks) == 0:
            errors.append(f"{prefix} 'blocks' doit être une liste non vide")
        else:
            for j, block in enumerate(blocks):
                if not isinstance(block, dict):
                    errors.append(f"{prefix}[block#{j}] doit être un objet JSON")
                    continue
                errors.extend(validate_block_structure(block, f"{prefix}[block#{j}]"))
    return errors


def validate_block_structure(block: Dict[str, Any], prefix: str) -> List[str]:
    """Valide la structure d'un bloc (ChannelBlock).

    Vérifie la présence des champs requis et le type de chacun. Cette
    fonction se concentre uniquement sur la structure, pas sur la cohérence
    temporelle ou les règles métiers.

    Args:
        block: Dictionnaire représentant le bloc.
        prefix: Préfixe à utiliser pour les messages d'erreurs.

    Returns:
        Une liste de messages d'erreurs. Vide si aucune erreur.
    """
    errors: List[str] = []
    required = ("criteria", "begin", "end", "slot_count", "slot_format", "shows")
    for key in required:
        if key not in block:
            errors.append(f"{prefix} clé manquante : {key}")
    # begin/end types
    for time_key in ("begin", "end"):
        if time_key in block and not isinstance(block[time_key], (int, float)):
            errors.append(f"{prefix} '{time_key}' doit être un nombre (int ou float)")
    # slot_count
    if "slot_count" in block and not isinstance(block["slot_count"], int):
        errors.append(f"{prefix} 'slot_count' doit être un entier")
    # slot_format
    sf = block.get("slot_format")
    if sf is not None:
        if not isinstance(sf, dict):
            errors.append(f"{prefix} 'slot_format' doit être un objet JSON")
        else:
            # Vérifier la présence des trois clés principales sans contrôler les valeurs ici
            for sf_key in ("show_min_duration", "show_max_duration", "slot_duration"):
                if sf_key not in sf:
                    errors.append(f"{prefix} 'slot_format' clé manquante : {sf_key}")
                else:
                    # Les durées doivent être des nombres (int ou float)
                    if not isinstance(sf[sf_key], (int, float)):
                        errors.append(
                            f"{prefix} 'slot_format.{sf_key}' doit être un nombre (int ou float)"
                        )
    # criteria
    criteria = block.get("criteria")
    if criteria is not None:
        if not isinstance(criteria, list) or len(criteria) == 0:
            errors.append(f"{prefix} 'criteria' doit être une liste non vide")
        else:
            for k, crit in enumerate(criteria):
                if not isinstance(crit, dict):
                    errors.append(f"{prefix}[criteria#{k}] doit être un objet JSON")
                    continue
                errors.extend(validate_criterion_structure(crit, f"{prefix}[criteria#{k}]") )
    # shows
    shows = block.get("shows")
    if shows is not None and not isinstance(shows, list):
        errors.append(f"{prefix} 'shows' doit être une liste")
    return errors


def validate_criterion_structure(crit: Dict[str, Any], prefix: str) -> List[str]:
    """Valide la structure d'un critère (Criteria).

    On s'assure de la présence des clés `category`, `values` et `forbidden`,
    puis du type attendu pour chacune. Les vérifications métier (valeurs
    autorisées) sont déléguées à un autre module.

    Args:
        crit: Dictionnaire représentant le critère.
        prefix: Préfixe pour les messages d'erreurs.

    Returns:
        Liste des erreurs de structure.
    """
    errors: List[str] = []
    for key in ("category", "values", "forbidden"):
        if key not in crit:
            errors.append(f"{prefix} clé manquante : {key}")
    # category
    if "category" in crit and not isinstance(crit["category"], str):
        errors.append(f"{prefix} 'category' doit être une chaîne de caractères")
    # values
    if "values" in crit:
        values = crit["values"]
        if not isinstance(values, list) or len(values) == 0:
            errors.append(f"{prefix} 'values' doit être une liste non vide")
    # forbidden
    if "forbidden" in crit and not isinstance(crit["forbidden"], bool):
        errors.append(f"{prefix} 'forbidden' doit être booléen (True/False)")
    return errors


def main(args: List[str]) -> int:
    """Point d'entrée pour le mode CLI.

    Charge le fichier JSON fourni, effectue la validation de structure et
    affiche les erreurs. Retourne 0 si aucune erreur n'est détectée, 1
    sinon.
    """
    if len(args) < 2:
        print(
            "Usage : python validate_json_structure.py <catalog.json>",
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
    errors = validate_catalog_structure(data)
    if not errors:
        print("✅ Structure JSON valide.")
        return 0
    else:
        print("❌ Erreurs de structure détectées :")
        for e in errors:
            print("-", e)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
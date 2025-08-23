#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_validation.py
------------------

Ce module contient quelques exemples simples de catalogues pour tester les
fonctions de validation fournies par `validate_json_structure` et
`validate_catalog_rules`. L'objectif de ces tests est de s'assurer que les
scripts de validation détectent correctement les erreurs et valident les
cas conformes.

Pour exécuter les tests manuellement, lancez :

    python test_validation.py

Les tests ne couvrent pas l'ensemble des cas possibles mais permettent de
vérifier que la logique principale fonctionne. Dans un cadre réel, il serait
préférable d'utiliser un framework de test unitaire tel que `pytest`.
"""

import json
from pprint import pprint

from validate_json_structure import validate_catalog_structure
from validate_catalog_rules import validate_catalog_rules


def example_valid_catalog() -> dict:
    """Construit un catalogue minimal valide pour les tests.

    Le catalogue contient une seule chaîne avec deux blocs qui se suivent
    parfaitement entre 6h et 9h.

    Returns:
        Un dictionnaire représentant un catalogue conforme.
    """
    return {
        "name": "Catalogue Test",
        "step": 0,
        "channels": [
            {
                "name": "Chaîne Exemple",
                "description": "Chaîne de test pour validation",
                # La chaîne diffuse de 6h à 10h (4 heures)
                "begin": 6.0,
                "end": 10.0,
                "fillers": ["Suspense"],
                "blocks": [
                    {
                        # Premier bloc : 2 slots de 60 minutes → 2 heures (de 6h à 8h)
                        "criteria": [
                            {"category": "genre", "values": ["Suspense"], "forbidden": False},
                            {"category": "type", "values": ["series"], "forbidden": False},
                        ],
                        "begin": 6.0,
                        "end": 8.0,
                        "slot_count": 2,
                        "slot_format": {
                            "show_min_duration": 45,
                            "show_max_duration": 52,
                            "slot_duration": 60,
                        },
                        "shows": [],
                    },
                    {
                        # Second bloc : 1 slot de 120 minutes → 2 heures (de 8h à 10h)
                        "criteria": [
                            {"category": "genre", "values": ["Suspense"], "forbidden": False},
                            {"category": "type", "values": ["movie"], "forbidden": False},
                        ],
                        "begin": 8.0,
                        "end": 10.0,
                        "slot_count": 1,
                        "slot_format": {
                            "show_min_duration": 95,
                            "show_max_duration": 110,
                            "slot_duration": 120,
                        },
                        "shows": [],
                    },
                ],
            }
        ],
    }


def example_invalid_catalog() -> dict:
    """Construit un catalogue volontairement erroné.

    Plusieurs erreurs sont introduites : bloc qui chevauche, bloc dont la
    durée ne correspond pas au nombre de slots, type invalide, genre
    inexistant et critères manquants.

    Returns:
        Un dictionnaire représentant un catalogue invalide.
    """
    return {
        "name": "Catalogue Erroné",
        "step": 0,
        "channels": [
            {
                "name": "Chaîne Mauvaise",
                "description": "Chaîne avec erreurs",
                "begin": 7.0,
                "end": 10.0,
                "fillers": ["Inexistant"],  # genre inconnu
                "blocks": [
                    {
                        # Critère manquant 'forbidden'
                        "criteria": [
                            {"category": "genre", "values": ["Action"]},
                            # Type invalide
                            {"category": "type", "values": ["documentary"], "forbidden": False},
                        ],
                        "begin": 7.0,
                        "end": 8.0,
                        "slot_count": 1,
                        "slot_format": {
                            "show_min_duration": 22,
                            "show_max_duration": 26,
                            "slot_duration": 30,
                        },
                        "shows": [],
                    },
                    {
                        # Ce bloc démarre avant la fin du précédent (chevauchement)
                        "criteria": [
                            {"category": "genre", "values": ["Action"], "forbidden": False},
                            {"category": "type", "values": ["series"], "forbidden": False},
                        ],
                        "begin": 7.5,
                        "end": 9.0,
                        "slot_count": 3,
                        "slot_format": {
                            "show_min_duration": 45,
                            "show_max_duration": 52,
                            "slot_duration": 60,
                        },
                        "shows": [],
                    },
                ],
            }
        ],
    }


def run_tests() -> None:
    """Exécute quelques validations simples et affiche les résultats."""
    print("Test 1 : catalogue valide")
    cat = example_valid_catalog()
    struct_errs = validate_catalog_structure(cat)
    rule_errs = validate_catalog_rules(cat)
    print("Erreurs de structure :")
    pprint(struct_errs)
    print("Erreurs de règles :")
    pprint(rule_errs)
    assert not struct_errs, "Le catalogue valide ne doit pas avoir d'erreur de structure"
    assert not rule_errs, "Le catalogue valide ne doit pas avoir d'erreur de règles"
    print("→ OK")
    print()
    print("Test 2 : catalogue invalide")
    cat_bad = example_invalid_catalog()
    struct_errs2 = validate_catalog_structure(cat_bad)
    rule_errs2 = validate_catalog_rules(cat_bad)
    print("Erreurs de structure :")
    pprint(struct_errs2)
    print("Erreurs de règles :")
    pprint(rule_errs2)
    assert struct_errs2 or rule_errs2, "Le catalogue invalide doit présenter des erreurs"
    print("→ OK")


if __name__ == "__main__":  # pragma: no cover
    run_tests()
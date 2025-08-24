import os

from data_types import CategoryCriteria, Channel
from settings import DATA_DIR
from utils import hour_float_to_hour_minute

"""
AI generated code
"""

def _is_genre_category(cat) -> bool:
    """Vrai si la catégorie correspond à GENRE (gère Enum ou str)."""
    if isinstance(cat, CategoryCriteria):
        return cat == CategoryCriteria.GENRE
    return str(cat).lower() == "genre"


def print_channel_full_description(channel: Channel):
    name = channel.get("name", "Sans nom")
    desc = channel.get("description", "Aucune")
    logo_file_path = os.path.join(DATA_DIR, "logo", channel['logo']) if "logo" in channel else os.path.join(
        DATA_DIR, "logo", f"{channel['name']}.png")

    logo = "Oui" if os.path.exists(logo_file_path)  else "Non"
    begin = channel.get("begin", 0)
    end = channel.get("end", 0)

    blocks = channel.get("blocks", []) or []
    fillers = channel.get("fillers", []) or []

    # ---- Stats sur les blocks / shows (ignore les available_*)
    block_count = len(blocks)
    total_block_duration = sum((b.get("end", 0) - b.get("begin", 0)) for b in blocks) if block_count else 0.0
    avg_block_duration = (total_block_duration / block_count) if block_count else 0.0

    blocks_without_shows = sum(1 for b in blocks if not b.get("shows"))
    total_shows = sum(len(b.get("shows", [])) for b in blocks)
    unique_show_names = {
        s.get("name") for b in blocks for s in (b.get("shows") or []) if s.get("name")
    }

    # Diversité des slot_duration rencontrées (côté blocks uniquement)
    slot_durations_seen = {
        b.get("slot_format", {}).get("slot_duration")
        for b in blocks
        if isinstance(b.get("slot_format", {}), dict) and b["slot_format"].get("slot_duration") is not None
    }
    slot_durations_seen.discard(None)
    slot_duration_min = min(slot_durations_seen) if slot_durations_seen else None
    slot_duration_max = max(slot_durations_seen) if slot_durations_seen else None

    # ---- Agrégation de tous les GENRE depuis les CRITERIA des blocks
    all_genres = set()
    for b in blocks:
        for crit in (b.get("criteria") or []):
            if _is_genre_category(crit.get("category")):
                for g in (crit.get("values") or []):
                    all_genres.add(str(g))

    # ---- Impression du résumé
    print(f"📺 Chaîne : {name}")
    print(f"Description : {desc}")
    print(f"Logo présent : {logo}")
    print(f"Période de diffusion : {hour_float_to_hour_minute(begin)} → {hour_float_to_hour_minute(end)}")
    print()

    print("🧱 Blocks")
    print(f" - Nombre de blocks : {block_count}")
    print(f" - Blocks sans shows : {blocks_without_shows}")
    print(f" - Durée totale des blocks : {total_block_duration:.2f} h")
    print(f" - Durée moyenne d’un block : {avg_block_duration:.2f} h")
    if slot_durations_seen:
        print(f" - Slot durations rencontrées : {sorted(slot_durations_seen)} "
              f"(min={slot_duration_min}, max={slot_duration_max})")
    else:
        print(" - Slot durations rencontrées : Aucune")
    print()

    print("🎭 Shows")
    print(f" - Nombre total d’émissions listées : {total_shows}")
    print(f" - Nombre d’émissions uniques : {len(unique_show_names)}")
    if unique_show_names:
        preview = sorted(unique_show_names)[:5]
        print(f" - Aperçu (5 max) : {', '.join(preview)}")
    print()

    print("🏷️ Genres")
    if all_genres:
        print(f" - {', '.join(sorted(all_genres))}")
    else:
        print(" - Aucun genre détecté dans les critères")
    print()

    print("🎬 Fillers :", ", ".join(fillers) if fillers else "Aucun")

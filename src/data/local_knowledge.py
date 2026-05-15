"""Local cultural knowledge per Spanish city/region.

Usage:
    from src.data.local_knowledge import get_local_knowledge
    lk = get_local_knowledge("Sevilla", birth_year=1945)
    print(lk.dishes, lk.football_team)

Two-layer lookup:
    1. Static DB  (data/local_knowledge_db.json) — ~25 cities, instant.
    2. LLM enrichment via Groq — for unknown cities, result cached to
       data/local_knowledge_cache/<city>.json.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent.parent
_DB_PATH = ROOT / "data" / "local_knowledge_db.json"
_CACHE_DIR = ROOT / "data" / "local_knowledge_cache"

_DB: dict | None = None


def _load_db() -> dict:
    global _DB
    if _DB is None:
        with open(_DB_PATH, encoding="utf-8") as f:
            _DB = json.load(f)
    return _DB


def _normalize_city(city: str) -> str:
    s = unicodedata.normalize("NFD", city.lower().strip())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


@dataclass
class LocalKnowledge:
    city: str
    region: str
    dishes: list[str] = field(default_factory=list)
    festivals: list[str] = field(default_factory=list)
    football_team: str = ""
    songs: list[str] = field(default_factory=list)
    famous_people: list[str] = field(default_factory=list)
    sayings: list[str] = field(default_factory=list)
    historical_facts: list[str] = field(default_factory=list)
    era_facts: dict[str, list[str]] = field(default_factory=dict)

    def era_content(self, birth_year: int) -> list[str]:
        """Return era_facts entries most relevant to a person born in birth_year."""
        youth_decade = f"{((birth_year + 15) // 10) * 10}s"   # when ~15 years old
        adult_decade = f"{((birth_year + 35) // 10) * 10}s"   # when ~35 years old
        out: list[str] = []
        for decade in (youth_decade, adult_decade):
            out.extend(self.era_facts.get(decade, []))
        return out

    def to_activity_items(self) -> list[str]:
        """Flat list of local items usable as activity hints."""
        items: list[str] = []
        items += [f"plato típico: {d}" for d in self.dishes[:3]]
        items += [f"fiesta: {f}" for f in self.festivals[:2]]
        if self.football_team:
            items.append(f"equipo de fútbol: {self.football_team}")
        items += [f"canción: {s}" for s in self.songs[:2]]
        items += [f"personaje famoso: {p}" for p in self.famous_people[:2]]
        return items


def get_local_knowledge(
    city: str,
    birth_year: int = 1945,
    *,
    use_llm: bool = True,
) -> LocalKnowledge:
    """Return LocalKnowledge for city. Falls back to LLM if not in static DB."""
    key = _normalize_city(city)
    db = _load_db()

    if key in db:
        return _from_dict(db[key])

    # Try partial match (e.g. "La Coruña" → "a_coruna")
    for db_key in db:
        if db_key in key or key in db_key:
            return _from_dict(db[db_key])

    # Try LLM enrichment
    cached = _load_cache(key)
    if cached:
        return _from_dict(cached)

    if use_llm:
        data = _enrich_with_llm(city, birth_year)
        if data:
            _save_cache(key, data)
            return _from_dict(data)

    return _generic_fallback(city)


def _from_dict(d: dict) -> LocalKnowledge:
    return LocalKnowledge(
        city=d.get("city", ""),
        region=d.get("region", ""),
        dishes=d.get("dishes", []),
        festivals=d.get("festivals", []),
        football_team=d.get("football_team", ""),
        songs=d.get("songs", []),
        famous_people=d.get("famous_people", []),
        sayings=d.get("sayings", []),
        historical_facts=d.get("historical_facts", []),
        era_facts=d.get("era_facts", {}),
    )


def _load_cache(key: str) -> dict | None:
    path = _CACHE_DIR / f"{key}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_cache(key: str, data: dict) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _CACHE_DIR / f"{key}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _enrich_with_llm(city: str, birth_year: int) -> Optional[dict]:
    try:
        import sys
        sys.path.insert(0, str(ROOT))
        from src.llm import get_default_client
        llm = get_default_client()
        if llm.backend == "echo":
            return None
    except Exception:
        return None

    prompt = f"""Para una persona mayor de unos {2025 - birth_year} años nacida en {city} (España),
dame en JSON con esta estructura exacta:
{{
  "city": "{city}",
  "region": "nombre de la región/comunidad autónoma",
  "dishes": ["plato1", "plato2", "plato3", "plato4", "plato5"],
  "festivals": ["fiesta1", "fiesta2", "fiesta3"],
  "football_team": "equipo local más popular",
  "songs": ["cancion1", "cancion2", "cancion3"],
  "famous_people": ["persona1", "persona2", "persona3"],
  "sayings": ["dicho1", "dicho2"],
  "historical_facts": ["hecho1", "hecho2", "hecho3"],
  "era_facts": {{
    "{((birth_year + 15) // 10) * 10}s": ["recuerdo1 de esa década", "recuerdo2"],
    "{((birth_year + 30) // 10) * 10}s": ["recuerdo1 de esa década", "recuerdo2"]
  }}
}}
Devuelve SOLO el JSON, sin texto adicional."""

    try:
        resp = llm.chat("Eres un experto en cultura local española.", prompt, max_tokens=600)
        text = resp.text.strip()
        # Extract JSON from response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return None


def _generic_fallback(city: str) -> LocalKnowledge:
    return LocalKnowledge(
        city=city,
        region="España",
        dishes=["tortilla de patatas", "cocido", "gazpacho", "paella", "jamón serrano"],
        festivals=["Semana Santa", "Fiestas patronales", "Carnaval"],
        football_team="equipo local",
        songs=["Copla española", "Bolero", "Jota"],
        famous_people=["Cervantes", "Velázquez", "Lorca"],
        sayings=["Más vale tarde que nunca", "A quien madruga Dios le ayuda"],
        historical_facts=["La historia de España", "La posguerra", "La Transición democrática"],
        era_facts={},
    )

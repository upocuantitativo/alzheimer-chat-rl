"""Filias (likes), fobias (dislikes / fears) and biographical interests.

The agent's first goal is to discover this profile through conversation;
the simulator privately holds it and reveals fragments according to its
mood / fatigue / cognitive stage.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# Domains that often appear in reminiscence therapy for AD patients.
TOPIC_BANK = {
    "es": {
        "musica": ["copla", "Joan Manuel Serrat", "Antonio Machín", "tunas universitarias",
                   "boleros", "Rocío Jurado", "Camilo Sesto"],
        "comida": ["paella", "tortilla de patatas", "gazpacho", "cocido madrileño",
                   "churros con chocolate"],
        "lugares": ["el pueblo de mi infancia", "la playa de Cádiz", "Sevilla",
                    "Madrid en los años 60", "Galicia"],
        "familia": ["mi madre", "mi marido", "mis hijos", "mis nietos", "mi hermana mayor"],
        "oficios": ["maestra", "ama de casa", "agricultor", "panadero", "modista",
                    "administrativo"],
        "aficiones": ["coser", "el huerto", "leer prensa", "el ganchillo", "cantar",
                      "el fútbol", "los toros"],
    },
    "en": {
        "music": ["Frank Sinatra", "Glenn Miller", "Elvis", "Sunday hymns",
                  "swing bands", "The Beatles"],
        "food": ["Sunday roast", "apple pie", "fish and chips", "cornbread", "pot roast"],
        "places": ["my hometown", "the lake house", "New York in the 60s", "Italy"],
        "family": ["my mother", "my husband", "my children", "my grandchildren"],
        "jobs": ["schoolteacher", "homemaker", "farmer", "baker", "nurse", "clerk"],
        "hobbies": ["knitting", "the garden", "reading the paper", "crochet", "singing",
                    "baseball"],
    },
}

# Topics that frequently trigger anxiety or sadness (fobias).
SENSITIVE_BANK = {
    "es": ["la muerte de mi marido", "la guerra", "estar sola", "perderse en la calle",
           "el médico", "los hospitales", "los ascensores"],
    "en": ["my late husband", "the war", "being alone", "getting lost", "doctors",
           "hospitals", "elevators"],
}


@dataclass
class InterestProfile:
    """Private profile the agent must discover through conversation."""
    name: str
    age: int
    likes: list[str] = field(default_factory=list)         # filias
    dislikes: list[str] = field(default_factory=list)      # fobias
    biographical: dict[str, str] = field(default_factory=dict)
    revealed_likes: set[str] = field(default_factory=set)  # discovered by agent
    revealed_dislikes: set[str] = field(default_factory=set)

    def reveal_like(self, topic: str) -> None:
        self.revealed_likes.add(topic)

    def reveal_dislike(self, topic: str) -> None:
        self.revealed_dislikes.add(topic)

    @property
    def discovery_rate(self) -> float:
        total = max(1, len(self.likes) + len(self.dislikes))
        return (len(self.revealed_likes) + len(self.revealed_dislikes)) / total

    def as_dict(self, hide_private: bool = False) -> dict:
        if hide_private:
            return {
                "name": self.name,
                "age": self.age,
                "revealed_likes": sorted(self.revealed_likes),
                "revealed_dislikes": sorted(self.revealed_dislikes),
                "discovery_rate": round(self.discovery_rate, 3),
            }
        return {
            "name": self.name,
            "age": self.age,
            "likes": self.likes,
            "dislikes": self.dislikes,
            "biographical": self.biographical,
            "revealed_likes": sorted(self.revealed_likes),
            "revealed_dislikes": sorted(self.revealed_dislikes),
        }


NAMES = {
    "es": ["Carmen", "María", "Antonio", "José", "Dolores", "Manuel", "Pilar",
           "Francisco", "Encarnación", "Joaquín"],
    "en": ["Margaret", "Robert", "Dorothy", "William", "Helen", "James",
           "Betty", "John", "Eleanor", "George"],
}


def build_random_profile(rng: random.Random | None = None, language: str = "es") -> InterestProfile:
    rng = rng or random.Random()
    name = rng.choice(NAMES[language])
    age = rng.randint(65, 92)

    bank = TOPIC_BANK[language]
    n_likes = rng.randint(3, 6)
    n_dislikes = rng.randint(1, 3)

    pool = [item for domain in bank.values() for item in domain]
    likes = rng.sample(pool, k=min(n_likes, len(pool)))
    dislikes = rng.sample(SENSITIVE_BANK[language], k=min(n_dislikes, len(SENSITIVE_BANK[language])))

    # One biographical anchor per domain to give the LLM material to work with.
    biographical = {
        domain: rng.choice(items) for domain, items in bank.items()
    }

    return InterestProfile(
        name=name,
        age=age,
        likes=likes,
        dislikes=dislikes,
        biographical=biographical,
    )

"""Rich bank of culturally-specific engagement activities for elderly Spanish patients.

Activities are organized by category:
    refrán          — complete the proverb (procedural memory, very preserved in AD)
    canción         — complete the song lyric (procedural memory)
    trivia_cultural — geography, history, gastronomy, traditions
    trivia_deportes — football, cycling, athletics, boxing
    adivinanza      — classic Spanish riddles

Each Activity maps to one of the four new AgentActions:
    REFRÁN          → category refrán
    CANCIÓN         → category canción
    TRIVIA_CULTURAL → category trivia_cultural
    TRIVIA_DEPORTES → category trivia_deportes

is_procedural=True items get a latency bonus (procedural memory survives longer in AD).
"""

from __future__ import annotations

import random
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower()).strip()


@dataclass
class Activity:
    category: str           # refrán | canción | trivia_cultural | trivia_deportes | adivinanza
    stimulus_es: str        # what the agent says
    completion_es: str      # canonical answer
    accepted_es: list[str]  # accepted answer variants (normalized during check)
    difficulty: float       # 0..1 (higher = harder for AD patient)
    interest_tags: list[str] = field(default_factory=list)  # match InterestProfile topics
    era: str = "general"    # general | 1940s | 1950s | 1960s | 1970s | 1980s
    is_procedural: bool = False   # True → big latency bonus + high success rate in AD


# ---------------------------------------------------------------------------
# Refranes (procedural / semantic memory — very preserved in early/mid AD)
# ---------------------------------------------------------------------------
REFRANES: list[Activity] = [
    Activity("refrán", "Más vale pájaro en mano...", "que ciento volando",
             ["ciento volando", "que cien volando"], 0.15, ["general"], "general", True),
    Activity("refrán", "En boca cerrada...", "no entran moscas",
             ["no entran moscas", "no entran"], 0.15, ["general"], "general", True),
    Activity("refrán", "A quien madruga...", "Dios le ayuda",
             ["dios le ayuda", "dios ayuda"], 0.15, ["general"], "general", True),
    Activity("refrán", "No hay mal...", "que por bien no venga",
             ["por bien no venga", "que por bien", "bien no venga"], 0.20, ["general"], "general", True),
    Activity("refrán", "Camarón que se duerme...", "se lo lleva la corriente",
             ["se lo lleva la corriente", "la corriente"], 0.25, ["general"], "general", True),
    Activity("refrán", "Ojos que no ven...", "corazón que no siente",
             ["corazon que no siente", "corazon no siente"], 0.20, ["general"], "general", True),
    Activity("refrán", "Más vale tarde...", "que nunca",
             ["que nunca", "nunca"], 0.10, ["general"], "general", True),
    Activity("refrán", "Al pan, pan...", "y al vino, vino",
             ["al vino vino", "y al vino", "vino vino"], 0.15, ["comida"], "general", True),
    Activity("refrán", "A caballo regalado...", "no le mires el diente",
             ["no le mires el diente", "no se le mira el diente", "no mires el diente"], 0.25, ["general"], "general", True),
    Activity("refrán", "El que la sigue...", "la consigue",
             ["la consigue", "consigue"], 0.15, ["general"], "general", True),
    Activity("refrán", "Dime con quién andas...", "y te diré quién eres",
             ["te dire quien eres", "y te dire quien eres"], 0.20, ["general"], "general", True),
    Activity("refrán", "No todo lo que reluce...", "es oro",
             ["es oro", "sera oro"], 0.15, ["general"], "general", True),
    Activity("refrán", "De tal palo...", "tal astilla",
             ["tal astilla", "tal la astilla"], 0.20, ["familia"], "general", True),
    Activity("refrán", "A mal tiempo...", "buena cara",
             ["buena cara", "hay que darle buena cara"], 0.15, ["general"], "general", True),
    Activity("refrán", "Perro que ladra...", "no muerde",
             ["no muerde", "no muerde nunca"], 0.20, ["general"], "general", True),
    Activity("refrán", "Quien mucho abarca...", "poco aprieta",
             ["poco aprieta", "poco aprieta poco"], 0.20, ["general"], "general", True),
    Activity("refrán", "Haz bien...", "y no mires a quién",
             ["no mires a quien", "y no mires a quien"], 0.25, ["general"], "general", True),
    Activity("refrán", "El hábito no hace...", "al monje",
             ["al monje", "al monje no"], 0.30, ["general"], "general", True),
    Activity("refrán", "Año de nieves...", "año de bienes",
             ["ano de bienes", "de bienes"], 0.25, ["general"], "1950s", True),
    Activity("refrán", "Agua que no has de beber...", "déjala correr",
             ["dejala correr", "deja correr"], 0.25, ["general"], "general", True),
    Activity("refrán", "Barriga llena...", "corazón contento",
             ["corazon contento", "corazon alegre"], 0.15, ["comida"], "general", True),
    Activity("refrán", "Cría cuervos...", "y te sacarán los ojos",
             ["te sacaran los ojos", "y te sacan los ojos", "los ojos"], 0.30, ["familia"], "general", True),
]

# ---------------------------------------------------------------------------
# Canciones (procedural memory — extremely preserved even in severe AD)
# ---------------------------------------------------------------------------
CANCIONES: list[Activity] = [
    Activity("canción", "Pena, penita, pena...", "pena de mi corazón",
             ["pena de mi corazon", "corazon", "de mi corazon"], 0.15, ["musica", "copla"], "1950s", True),
    Activity("canción", "Ay, ay, ay, canta y no...", "llores",
             ["llores", "no llores", "y no llores"], 0.15, ["musica"], "1950s", True),
    Activity("canción", "Suspiros de España, suspiros de...", "amor",
             ["amor", "de amor", "pena y amor"], 0.15, ["musica"], "1950s", True),
    Activity("canción", "La bien pagá, era la bien pagá...", "porque yo le di todo lo mío",
             ["porque yo le di todo lo mio", "todo lo mio", "le di todo"], 0.25, ["musica", "copla"], "1950s", True),
    Activity("canción", "Y viva España, cantemos todos juntos, viva...", "España",
             ["espana", "viva espana"], 0.15, ["musica"], "1960s", True),
    Activity("canción", "El emigrante, caminito de la...", "vera",
             ["vera", "vera del camino"], 0.20, ["musica", "copla"], "1960s", True),
    Activity("canción", "Ojos verdes, verdes como la albahaca...", "verdes como el verde trigo",
             ["verdes como el verde trigo", "verde trigo", "como el trigo"], 0.25, ["musica", "copla"], "1950s", True),
    Activity("canción", "Tatuaje, me lo hice en el puerto...", "una tarde de verano",
             ["una tarde de verano", "tarde de verano", "de verano"], 0.25, ["musica", "copla"], "1950s", True),
    Activity("canción", "Caminando, caminando, por la vida yo me...", "voy",
             ["voy", "voy caminando"], 0.20, ["musica"], "1960s", True),
    Activity("canción", "Al jardín de la alegría, dile que la quiero ver, que la...", "rosa de mi querer",
             ["rosa de mi querer", "la rosa", "mi querer"], 0.30, ["musica"], "1960s", True),
    Activity("canción", "Marinero de luces, tú me robaste el...", "corazón",
             ["corazon", "el corazon"], 0.20, ["musica", "copla"], "1950s", True),
    Activity("canción", "La Lola se va a los puertos, la Lola se va a...", "Cádiz",
             ["cadiz", "a cadiz", "los puertos"], 0.25, ["musica", "copla"], "1950s", True),
    Activity("canción", "Asturias, patria querida, Asturias de mis...", "amores",
             ["amores", "mis amores"], 0.15, ["musica"], "general", True),
    Activity("canción", "El río Guadalquivir, cuando va por...", "Sevilla",
             ["sevilla", "por sevilla"], 0.20, ["musica", "lugares"], "1950s", True),
    Activity("canción", "En el número cien de la calle mayor, vivía...", "Doña Dolores",
             ["dona dolores", "dolores", "una senora"], 0.30, ["musica"], "1960s", True),
    Activity("canción", "Un, dos, tres, respondón, que trece son...", "trece",
             ["trece", "son trece"], 0.20, ["musica"], "1970s", True),
    Activity("canción", "Uno de enero, dos de febrero, tres de marzo, cuatro de...", "abril",
             ["abril", "de abril"], 0.15, ["musica", "futbol"], "general", True),
]

# ---------------------------------------------------------------------------
# Trivia cultural (semantic memory — moderately preserved)
# ---------------------------------------------------------------------------
TRIVIA_CULTURAL: list[Activity] = [
    Activity("trivia_cultural", "¿Cuál es la capital de Francia?", "París",
             ["paris"], 0.10, ["general", "geografia"], "general", False),
    Activity("trivia_cultural", "¿En qué país está la Torre Eiffel?", "Francia",
             ["francia"], 0.10, ["general", "geografia"], "general", False),
    Activity("trivia_cultural", "¿Cuántas comunidades autónomas tiene España?", "17",
             ["17", "diecisiete"], 0.35, ["general", "geografia"], "general", False),
    Activity("trivia_cultural", "¿En qué año terminó la Guerra Civil Española?", "1939",
             ["1939", "treinta y nueve", "mil novecientos treinta y nueve"], 0.30, ["historia"], "general", False),
    Activity("trivia_cultural", "¿Quién pintó Las Meninas?", "Velázquez",
             ["velazquez", "diego velazquez"], 0.25, ["arte", "historia"], "general", False),
    Activity("trivia_cultural", "¿Quién escribió El Quijote?", "Cervantes",
             ["cervantes", "miguel de cervantes"], 0.20, ["literatura", "historia"], "general", False),
    Activity("trivia_cultural", "¿En qué ciudad está la Sagrada Familia?", "Barcelona",
             ["barcelona"], 0.15, ["general", "geografia"], "general", False),
    Activity("trivia_cultural", "¿Cómo se llama el río más largo de España?", "Ebro",
             ["ebro", "el ebro", "tajo"], 0.30, ["general", "geografia"], "general", False),
    Activity("trivia_cultural", "¿Cuántos días tiene el mes de febrero en un año normal?", "28",
             ["28", "veintiocho"], 0.20, ["general"], "general", False),
    Activity("trivia_cultural", "¿Cuál es la capital de Italia?", "Roma",
             ["roma"], 0.10, ["general", "geografia"], "general", False),
    Activity("trivia_cultural", "¿De qué país es el flamenco?", "España",
             ["espana", "de espana"], 0.10, ["musica", "general"], "general", False),
    Activity("trivia_cultural", "¿En qué mes se celebra la Semana Santa?", "marzo o abril",
             ["marzo", "abril", "semana santa"], 0.25, ["general", "fiestas"], "general", False),
    Activity("trivia_cultural", "¿Cómo se llama el rey de España que murió en 1975?", "Franco / Francisco Franco",
             ["franco", "francisco franco"], 0.30, ["historia"], "1970s", False),
    Activity("trivia_cultural", "¿Quién pintó el Guernica?", "Picasso",
             ["picasso", "pablo picasso"], 0.20, ["arte", "historia"], "general", False),
    Activity("trivia_cultural", "¿Cuántos meses tiene el año?", "12",
             ["12", "doce"], 0.05, ["general"], "general", False),
    Activity("trivia_cultural", "¿En qué continente está España?", "Europa",
             ["europa", "en europa"], 0.10, ["general", "geografia"], "general", False),
    Activity("trivia_cultural", "¿Cómo se llama el plato típico de Valencia con arroz?", "paella",
             ["paella", "la paella"], 0.15, ["comida", "gastronomia"], "general", False),
    Activity("trivia_cultural", "¿Cuál es la capital de Portugal?", "Lisboa",
             ["lisboa"], 0.20, ["general", "geografia"], "general", False),
    Activity("trivia_cultural", "¿Quién fue el primer hombre en pisar la luna?", "Neil Armstrong",
             ["neil armstrong", "armstrong"], 0.25, ["historia"], "1960s", False),
    Activity("trivia_cultural", "¿En qué año llegó el hombre a la luna?", "1969",
             ["1969", "sesenta y nueve", "mil novecientos sesenta y nueve"], 0.30, ["historia"], "1960s", False),
    Activity("trivia_cultural", "¿Cómo se llama el dulce típico de Toledo que se hace con almendra?", "mazapán",
             ["mazapan", "el mazapan"], 0.25, ["comida", "gastronomia"], "general", False),
    Activity("trivia_cultural", "¿Cuántos colores tiene el arcoíris?", "7",
             ["7", "siete"], 0.10, ["general"], "general", False),
    Activity("trivia_cultural", "¿Cómo se llaman los dulces típicos de Carnaval fritos en aceite?", "buñuelos o torrijas",
             ["bunuelos", "torrijas", "rosquillas"], 0.30, ["comida", "gastronomia", "fiestas"], "general", False),
    Activity("trivia_cultural", "¿En qué ciudad española hay una Alhambra famosa?", "Granada",
             ["granada"], 0.20, ["general", "historia"], "general", False),
]

# ---------------------------------------------------------------------------
# Trivia deportes (semantic memory + strong emotional resonance)
# ---------------------------------------------------------------------------
TRIVIA_DEPORTES: list[Activity] = [
    Activity("trivia_deportes", "¿En qué año ganó España su primer Campeonato del Mundo de fútbol?", "2010",
             ["2010", "dos mil diez", "en sudafrica"], 0.25, ["futbol"], "2010s", False),
    Activity("trivia_deportes", "¿Cómo se llama el estadio del Real Madrid?", "Santiago Bernabéu",
             ["bernabeu", "santiago bernabeu"], 0.15, ["futbol"], "general", False),
    Activity("trivia_deportes", "¿Cuántas Copas de Europa seguidas ganó el Real Madrid en los años 50 y 60?", "cinco",
             ["cinco", "5", "cinco copas"], 0.30, ["futbol"], "1960s", False),
    Activity("trivia_deportes", "¿Cómo se llama el estadio del Barça?", "Camp Nou",
             ["camp nou", "el camp nou", "nou camp"], 0.20, ["futbol"], "general", False),
    Activity("trivia_deportes", "¿En qué deporte se compite en el Tour de Francia?", "ciclismo",
             ["ciclismo", "en bicicleta", "bici"], 0.10, ["ciclismo", "deporte"], "general", False),
    Activity("trivia_deportes", "¿Quién fue el primer español en ganar el Tour de Francia?", "Federico Martín Bahamontes",
             ["bahamontes", "martin bahamontes", "federico"], 0.45, ["ciclismo"], "1950s", False),
    Activity("trivia_deportes", "¿Cuántos Tour de Francia seguidos ganó Miguel Induráin?", "cinco",
             ["cinco", "5"], 0.35, ["ciclismo"], "1990s", False),
    Activity("trivia_deportes", "¿De qué ciudad era el famoso torero Manolete?", "Córdoba",
             ["cordoba", "de cordoba"], 0.35, ["toros", "historia"], "1950s", False),
    Activity("trivia_deportes", "¿Cómo se llama el deporte que se practica en Pelota Vasca?", "pelota vasca o jai alai",
             ["pelota vasca", "pelota", "jai alai"], 0.30, ["deporte"], "general", False),
    Activity("trivia_deportes", "¿Quién fue Di Stéfano?", "El mejor jugador del Real Madrid de los años 50",
             ["real madrid", "di stefano", "jugador del real madrid", "estrella del madrid"], 0.35, ["futbol"], "1950s", False),
    Activity("trivia_deportes", "¿En qué año se celebraron los Juegos Olímpicos en Barcelona?", "1992",
             ["1992", "noventa y dos", "mil novecientos noventa y dos"], 0.25, ["deporte", "historia"], "1990s", False),
    Activity("trivia_deportes", "¿Cómo se llama el gol que España marcó en la final del Mundial 2010?", "El gol de Iniesta",
             ["iniesta", "andres iniesta", "gol de iniesta"], 0.30, ["futbol"], "2010s", False),
    Activity("trivia_deportes", "¿Qué número llevaba Butragueño en el Real Madrid?", "7",
             ["7", "siete"], 0.45, ["futbol"], "1980s", False),
    Activity("trivia_deportes", "¿En qué equipo jugó Emilio Butragueño?", "Real Madrid",
             ["real madrid", "el madrid"], 0.25, ["futbol"], "1980s", False),
    Activity("trivia_deportes", "¿Cuántas medallas de oro ganó España en los Juegos Olímpicos de Barcelona?", "13",
             ["13", "trece"], 0.45, ["deporte"], "1990s", False),
    Activity("trivia_deportes", "¿En qué deporte fue campeón del mundo Ángel Nieto 12+1 veces?", "motociclismo",
             ["motociclismo", "motos", "moto"], 0.30, ["deporte", "motos"], "1970s", False),
    Activity("trivia_deportes", "¿Cómo se llama el equipo de fútbol del País Vasco que solo ficha jugadores vascos?", "Athletic Club de Bilbao",
             ["athletic", "athletic club", "bilbao", "athletic bilbao"], 0.25, ["futbol"], "general", False),
    Activity("trivia_deportes", "¿Quién ganó el Balón de Oro en 1960?", "Luis Suárez (español)",
             ["luis suarez", "suarez", "luis suarez arconada"], 0.50, ["futbol"], "1960s", False),
    Activity("trivia_deportes", "¿En qué deporte es famoso el pelotón?", "ciclismo",
             ["ciclismo", "la bicicleta", "tour"], 0.20, ["ciclismo", "deporte"], "general", False),
    Activity("trivia_deportes", "¿Cómo se llama la competición de fútbol más importante de Europa entre clubes?", "Champions League / Copa de Europa",
             ["champions", "copa de europa", "champions league", "liga de campeones"], 0.20, ["futbol"], "general", False),
]

# ---------------------------------------------------------------------------
# Adivinanzas (semantic memory + fun, good mood lifter)
# ---------------------------------------------------------------------------
ADIVINANZAS: list[Activity] = [
    Activity("adivinanza", "Soy redonda como el sol, cuando me pelen no me duele, ¿qué soy?", "naranja",
             ["naranja", "una naranja"], 0.15, ["comida", "general"], "general", False),
    Activity("adivinanza", "Tengo hojas pero no soy árbol, tengo lomo pero no soy animal, ¿qué soy?", "libro",
             ["libro", "un libro"], 0.15, ["general"], "general", False),
    Activity("adivinanza", "Cuanto más me secas, más te mojo, ¿qué soy?", "toalla",
             ["toalla", "una toalla"], 0.20, ["general"], "general", False),
    Activity("adivinanza", "Soy de cristal pero no me rompes, te refresco pero no soy agua, ¿qué soy?", "aire / ventana",
             ["aire", "el aire", "ventana", "cristal"], 0.35, ["general"], "general", False),
    Activity("adivinanza", "Tengo cabeza y no pienso, tengo cola y no soy animal, ¿qué soy?", "moneda",
             ["moneda", "una moneda"], 0.25, ["general"], "general", False),
    Activity("adivinanza", "De día se pierde y de noche aparece, ¿qué es?", "las estrellas",
             ["estrellas", "la luna", "las estrellas", "la noche"], 0.20, ["general"], "general", False),
    Activity("adivinanza", "Tiene dientes y no come, tiene pelo y no es persona, ¿qué es?", "peine",
             ["peine", "el peine"], 0.20, ["general"], "general", False),
    Activity("adivinanza", "Soy blanco como la nieve, dulce como la miel, y no soy azúcar ni sal, ¿qué soy?", "leche",
             ["leche", "la leche"], 0.20, ["comida", "general"], "general", False),
]

# ---------------------------------------------------------------------------
# Unified bank
# ---------------------------------------------------------------------------
ALL_ACTIVITIES: list[Activity] = (
    REFRANES + CANCIONES + TRIVIA_CULTURAL + TRIVIA_DEPORTES + ADIVINANZAS
)

_BY_CATEGORY: dict[str, list[Activity]] = {}
for _a in ALL_ACTIVITIES:
    _BY_CATEGORY.setdefault(_a.category, []).append(_a)


class ActivityBank:
    """Stateful bank that tracks used activities and enables smart sampling."""

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)
        self._used: set[int] = set()   # indices into ALL_ACTIVITIES

    def sample(
        self,
        category: str,
        *,
        max_difficulty: float = 1.0,
        interest_tags: Optional[list[str]] = None,
        trending_tags: Optional[list[str]] = None,
        local_items: Optional[list[str]] = None,
        prefer_procedural: bool = False,
    ) -> Optional[Activity]:
        """Return an unused Activity from the category matching constraints."""
        pool = [a for a in _BY_CATEGORY.get(category, [])
                if id(a) not in self._used and a.difficulty <= max_difficulty]

        if not pool:
            # Reset if exhausted
            self._used = {uid for uid in self._used
                          if uid not in {id(a) for a in _BY_CATEGORY.get(category, [])}}
            pool = [a for a in _BY_CATEGORY.get(category, []) if a.difficulty <= max_difficulty]

        if not pool:
            return None

        # Score each activity: higher = more preferred
        def score(a: Activity) -> float:
            s = 1.0
            if interest_tags:
                matches = sum(1 for t in a.interest_tags if t in interest_tags)
                s += matches * 0.5
            if trending_tags:
                matches = sum(1 for t in a.interest_tags if t in trending_tags)
                s += matches * 0.3
            if prefer_procedural and a.is_procedural:
                s += 0.4
            return s + self.rng.random() * 0.2   # small tie-breaking noise

        pool.sort(key=score, reverse=True)
        # Sample from top-3 to keep some variety
        chosen = self.rng.choice(pool[:3])
        self._used.add(id(chosen))
        return chosen

    def verify(self, activity: Activity, answer: str) -> bool:
        """Return True if the answer matches the activity's accepted completions."""
        norm_ans = _norm(answer)
        return any(_norm(acc) in norm_ans or norm_ans in _norm(acc)
                   for acc in activity.accepted_es)

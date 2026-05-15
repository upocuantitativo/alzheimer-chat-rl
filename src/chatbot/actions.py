"""Discrete action space for the conversational RL agent.

Each action is a high-level "communicative move", inspired by the
clinical guides reviewed in the briefing document (Alzheimer's Association,
CEAFA, Ministerio de Sanidad). They aim to be small enough that the agent
must learn a meaningful policy, large enough to cover the moves a real
caregiver chatbot would make.

The RL agent emits an action index; an utterance is then materialised by
either a template or by the LLM under the constraint of the chosen action.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class AgentAction(IntEnum):
    OPEN_QUESTION = 0       # invita a hablar libremente (descubrir filias)
    PROBE_LIKE = 1          # profundiza en algo que el paciente disfruta
    VALIDATE_EMOTION = 2    # reconoce y valida el estado emocional
    COGNITIVE_TEST_EASY = 3 # propone una prueba sencilla (orientación)
    COGNITIVE_TEST_HARD = 4 # propone una prueba difícil (fluencia/atención)
    REMINISCE = 5           # reminiscencia biográfica
    CHANGE_TOPIC = 6        # cambia de tema (utilizar si ansiedad alta)
    SHORT_REASSURE = 7      # frase corta tranquilizadora, baja fatiga
    CLOSE_TURN = 8          # cierra educadamente (sale del entorno)
    # --- actividades motivadoras (memoria procedural y semántica) ---
    REFRÁN = 9              # completa el refrán (memoria procedural)
    CANCIÓN = 10            # completa la canción (memoria procedural)
    TRIVIA_CULTURAL = 11    # trivia de geografía, historia, gastronomía
    TRIVIA_DEPORTES = 12    # trivia de fútbol, ciclismo, deporte


ACTION_SPACE = list(AgentAction)


@dataclass
class ActionTemplate:
    es: list[str]
    en: list[str]


TEMPLATES: dict[AgentAction, ActionTemplate] = {
    AgentAction.OPEN_QUESTION: ActionTemplate(
        es=[
            "Cuénteme algo bonito de cuando era joven.",
            "¿De qué le gusta hablar?",
            "Hábleme de lo que más le gusta hacer en el día a día.",
        ],
        en=[
            "Tell me something nice from when you were young.",
            "What do you like to talk about?",
            "Tell me about what you most enjoy doing day to day.",
        ],
    ),
    AgentAction.PROBE_LIKE: ActionTemplate(
        es=[
            "Antes mencionó {topic}. ¿Qué le gustaba de eso?",
            "Cuénteme más sobre {topic}, parece que le hace ilusión.",
        ],
        en=[
            "Earlier you mentioned {topic}. What did you like about it?",
            "Tell me more about {topic}, it seems to bring you joy.",
        ],
    ),
    AgentAction.VALIDATE_EMOTION: ActionTemplate(
        es=[
            "Le entiendo, eso suena importante para usted.",
            "Tiene todo el sentido sentirse así. Estoy aquí escuchándole.",
        ],
        en=[
            "I understand, that sounds important to you.",
            "It makes sense to feel that way. I'm here listening.",
        ],
    ),
    AgentAction.COGNITIVE_TEST_EASY: ActionTemplate(
        es=["Le hago una preguntita fácil: {prompt}"],
        en=["Let me ask you an easy one: {prompt}"],
    ),
    AgentAction.COGNITIVE_TEST_HARD: ActionTemplate(
        es=["Vamos a jugar un poco con la memoria: {prompt}"],
        en=["Let's play a memory game: {prompt}"],
    ),
    AgentAction.REMINISCE: ActionTemplate(
        es=[
            "¿Cómo era el pueblo cuando usted era pequeño?",
            "¿Qué canciones se cantaban en su casa?",
            "Hábleme de su madre, ¿cómo era?",
        ],
        en=[
            "What was your town like when you were small?",
            "What songs were sung at home?",
            "Tell me about your mother, what was she like?",
        ],
    ),
    AgentAction.CHANGE_TOPIC: ActionTemplate(
        es=[
            "Dejemos eso. ¿Le apetece que hablemos de otra cosa más alegre?",
            "Mejor cambiemos un poco. ¿Sabe qué tiempo hace hoy?",
        ],
        en=[
            "Let's leave that. Shall we talk about something happier?",
            "Let's switch a little. Do you know what the weather is like today?",
        ],
    ),
    AgentAction.SHORT_REASSURE: ActionTemplate(
        es=[
            "Tranquila, no hay prisa. Tómese su tiempo.",
            "Está usted muy bien, no se preocupe.",
        ],
        en=[
            "It's all right, no rush. Take your time.",
            "You're doing very well, don't worry.",
        ],
    ),
    AgentAction.CLOSE_TURN: ActionTemplate(
        es=["Ha sido un placer hablar con usted. Hasta la próxima."],
        en=["It's been a pleasure talking with you. Until next time."],
    ),
    AgentAction.REFRÁN: ActionTemplate(
        es=[
            "Le voy a decir el principio de un refrán, a ver si me lo completa: «{stimulus}»",
            "¿Sabe usted cómo termina este refrán? «{stimulus}»",
            "Esto me lo enseñó mi abuela. ¿Cómo seguía? «{stimulus}»",
        ],
        en=[
            "I'll say the beginning of a proverb, see if you can complete it: «{stimulus}»",
            "Do you know how this saying ends? «{stimulus}»",
        ],
    ),
    AgentAction.CANCIÓN: ActionTemplate(
        es=[
            "¿Recuerda esta canción? Cante conmigo: «{stimulus}»",
            "Una canción que me gusta mucho empieza así: «{stimulus}» ¿Cómo sigue?",
            "Esto lo cantábamos todos de pequeños: «{stimulus}»",
        ],
        en=[
            "Do you remember this song? Sing with me: «{stimulus}»",
            "A song I love starts like this: «{stimulus}» How does it go?",
        ],
    ),
    AgentAction.TRIVIA_CULTURAL: ActionTemplate(
        es=[
            "Le hago una preguntilla de cultura general: {stimulus}",
            "A ver si lo sabe: {stimulus}",
            "Una cosita de cultura: {stimulus}",
        ],
        en=[
            "A little general knowledge question: {stimulus}",
            "Let's see if you know: {stimulus}",
        ],
    ),
    AgentAction.TRIVIA_DEPORTES: ActionTemplate(
        es=[
            "¿Sabe usted de deportes? {stimulus}",
            "Una pregunta deportiva: {stimulus}",
            "Hablando de deporte: {stimulus}",
        ],
        en=[
            "Are you a sports fan? {stimulus}",
            "A sports question: {stimulus}",
        ],
    ),
}

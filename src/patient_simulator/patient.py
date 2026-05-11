"""
PatientSimulator — produces utterances that mimic the linguistic and emotional
behavior of a person with Alzheimer's disease at a given cognitive stage.

Hybrid generation:
    1. The LLM (Groq / Ollama / HF) is prompted with a clinical persona derived
       from the cognitive state and interest profile.
    2. A post-processing layer injects stage-typical linguistic phenomena:
         - pausas ("eh...", "este...", "...")
         - repeticiones
         - sustituciones por hiperónimo ("esa cosa", "lo que se usa para...")
         - perseveración temática
         - cierre brusco si la fatiga es alta
    3. Internal state advances: fatiga sube por cada turno; cualquier topic
       coincidente con dislikes incrementa ansiedad; coincidencia con likes
       eleva mood y revela el interés.

If no LLM is available, a fully rule-based template still produces realistic
short utterances — enough to exercise the RL pipeline.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Optional

from ..llm import LLMClient, get_default_client
from .cognitive_state import CognitiveState, Stage
from .interests import InterestProfile, build_random_profile

# --------------------------------------------------------------------------
# Stage-conditioned linguistic phenomena
# --------------------------------------------------------------------------
FILLERS = {
    "es": ["eh...", "este...", "bueno...", "pues...", "a ver..."],
    "en": ["um...", "uh...", "well...", "you know...", "let me see..."],
}

ANOMIA_SUBS = {
    "es": ["esa cosa", "lo de siempre", "lo que se usa para eso", "como se llame",
           "esa que tú sabes"],
    "en": ["that thing", "the usual", "the one you use for that", "whatchamacallit",
           "you know which"],
}

STAGE_INTENSITY = {
    Stage.HEALTHY:     dict(filler=0.05, repeat=0.02, anomia=0.0,  truncation=0.0),
    Stage.MCI:         dict(filler=0.20, repeat=0.10, anomia=0.10, truncation=0.0),
    Stage.MILD_AD:     dict(filler=0.35, repeat=0.20, anomia=0.25, truncation=0.10),
    Stage.MODERATE_AD: dict(filler=0.55, repeat=0.35, anomia=0.45, truncation=0.30),
    Stage.SEVERE_AD:   dict(filler=0.70, repeat=0.50, anomia=0.65, truncation=0.55),
}


SYSTEM_PROMPT_ES = """Estás interpretando el papel de {name}, una persona de {age} años con
{stage_es}. Tu MMSE estimado es {mmse}/30. Responde SIEMPRE en primera persona como esa
persona, NUNCA como un asistente.

Filias (te alegran y te animan a hablar): {likes}
Fobias (te incomodan o entristecen): {dislikes}
Datos biográficos: {bio}

Reglas de habla:
- Frases cortas, vocabulario sencillo.
- Si te preguntan algo que recuerdas bien, contesta con detalle emocional.
- Si te preguntan algo difícil para tu fase, duda, repite, o di que no recuerdas.
- Nunca expliques que eres una IA ni rompas el personaje.
- Estado actual: fatiga={fatigue:.2f}, ansiedad={anxiety:.2f}, ánimo={mood:.2f}.
- Si la fatiga es alta (>0.7), responde con muy pocas palabras.
- Si la ansiedad es alta (>0.6), muestra inquietud o cambia de tema.
- Si el ánimo es positivo, sé cálido; si es negativo, sé reservado.

Devuelve SOLO la respuesta del paciente, en {language}, sin etiquetas ni guiones."""

SYSTEM_PROMPT_EN = """You are role-playing as {name}, a {age}-year-old person with {stage_en}.
Your estimated MMSE is {mmse}/30. Always respond in first person as that
person, NEVER as an assistant.

Likes (cheer you up and encourage talking): {likes}
Dislikes / fears (make you uncomfortable or sad): {dislikes}
Biographical facts: {bio}

Speech rules:
- Short sentences, plain vocabulary.
- If asked about something you remember well, answer with emotional detail.
- If asked something hard for your stage, hesitate, repeat, or say you don't remember.
- Never explain that you are an AI or break character.
- Current state: fatigue={fatigue:.2f}, anxiety={anxiety:.2f}, mood={mood:.2f}.
- If fatigue is high (>0.7), reply with very few words.
- If anxiety is high (>0.6), show unease or change the subject.
- If mood is positive, be warm; if negative, be reserved.

Return ONLY the patient's reply, in {language}, with no labels or dashes."""


STAGE_ES = {
    Stage.HEALTHY: "envejecimiento normal sin deterioro cognitivo",
    Stage.MCI: "deterioro cognitivo leve (DCL)",
    Stage.MILD_AD: "enfermedad de Alzheimer en fase leve",
    Stage.MODERATE_AD: "enfermedad de Alzheimer en fase moderada",
    Stage.SEVERE_AD: "enfermedad de Alzheimer en fase avanzada",
}
STAGE_EN = {
    Stage.HEALTHY: "no cognitive impairment",
    Stage.MCI: "mild cognitive impairment (MCI)",
    Stage.MILD_AD: "mild Alzheimer's disease",
    Stage.MODERATE_AD: "moderate Alzheimer's disease",
    Stage.SEVERE_AD: "severe Alzheimer's disease",
}


@dataclass
class PatientTurn:
    text: str
    state: dict
    triggered_like: Optional[str] = None
    triggered_dislike: Optional[str] = None
    used_llm: bool = False


class PatientSimulator:
    def __init__(
        self,
        profile: Optional[InterestProfile] = None,
        state: Optional[CognitiveState] = None,
        *,
        llm: Optional[LLMClient] = None,
        seed: Optional[int] = None,
        mode: str = "llm_hybrid",   # rules_only | llm_hybrid | llm_only
        language: str = "es",
    ):
        self.rng = random.Random(seed)
        self.language = language
        self.state = state or CognitiveState.sample(self.rng, language=language)
        self.profile = profile or build_random_profile(self.rng, language=language)
        self.mode = mode

        self.llm = llm
        if mode != "rules_only" and self.llm is None:
            self.llm = get_default_client()

        self.history: list[tuple[str, str]] = []  # (speaker, text)

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------
    def reply(self, agent_utterance: str) -> PatientTurn:
        """Receive an utterance from the agent and produce a patient reply."""
        self.history.append(("agent", agent_utterance))

        triggered_like = self._detect_topic(agent_utterance, self.profile.likes)
        triggered_dislike = self._detect_topic(agent_utterance, self.profile.dislikes)

        if triggered_like:
            self.profile.reveal_like(triggered_like)
            self.state.step_mood(+0.10)
            self.state.step_anxiety(-0.05)
        if triggered_dislike:
            self.profile.reveal_dislike(triggered_dislike)
            self.state.step_anxiety(+0.15)
            self.state.step_mood(-0.08)

        # Fatigue rises slowly each turn, faster in advanced stages.
        base = 0.02
        if self.state.stage in (Stage.MODERATE_AD, Stage.SEVERE_AD):
            base = 0.05
        self.state.step_fatigue(+base)
        self.state.history_length += 1

        # Generate reply
        used_llm = False
        if self.mode == "rules_only" or self.llm is None or self.llm.backend == "echo":
            text = self._rule_reply(agent_utterance, triggered_like, triggered_dislike)
        else:
            try:
                text = self._llm_reply(agent_utterance)
                used_llm = True
            except Exception:
                # Soft fallback: do not break the simulation on LLM outage.
                text = self._rule_reply(agent_utterance, triggered_like, triggered_dislike)

        if self.mode != "llm_only":
            text = self._inject_stage_phenomena(text)

        self.history.append(("patient", text))
        return PatientTurn(
            text=text,
            state=self.state.as_dict(),
            triggered_like=triggered_like,
            triggered_dislike=triggered_dislike,
            used_llm=used_llm,
        )

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------
    @staticmethod
    def _detect_topic(text: str, candidates: list[str]) -> Optional[str]:
        t = text.lower()
        for c in candidates:
            tokens = [w for w in re.split(r"\s+", c.lower()) if len(w) > 3]
            if any(tok in t for tok in tokens) or c.lower() in t:
                return c
        return None

    def _llm_reply(self, agent_utterance: str) -> str:
        tmpl = SYSTEM_PROMPT_ES if self.language == "es" else SYSTEM_PROMPT_EN
        stage = self.state.stage
        sys = tmpl.format(
            name=self.profile.name,
            age=self.profile.age,
            stage_es=STAGE_ES[stage],
            stage_en=STAGE_EN[stage],
            mmse=self.state.mmse,
            likes=", ".join(self.profile.likes),
            dislikes=", ".join(self.profile.dislikes),
            bio="; ".join(f"{k}: {v}" for k, v in self.profile.biographical.items()),
            fatigue=self.state.fatigue,
            anxiety=self.state.anxiety,
            mood=self.state.mood,
            language="español" if self.language == "es" else "English",
        )
        recent = self._format_recent_context(max_turns=4)
        prompt = f"{recent}\nInterlocutor: {agent_utterance}\n{self.profile.name}:"
        max_tokens = 120 if self.state.fatigue < 0.7 else 50
        resp = self.llm.chat(sys, prompt, max_tokens=max_tokens, temperature=0.8)
        return self._cleanup_llm_text(resp.text)

    @staticmethod
    def _cleanup_llm_text(text: str) -> str:
        text = text.strip().strip('"')
        # Strip role/name prefixes the model often emits.
        text = re.sub(r"^(paciente|patient|asistente|assistant)\s*:\s*", "", text, flags=re.I)
        text = re.sub(r"^[-—]\s*", "", text)
        return text

    def _format_recent_context(self, max_turns: int = 4) -> str:
        lines = []
        for speaker, text in self.history[-max_turns * 2 :]:
            who = "Interlocutor" if speaker == "agent" else self.profile.name
            lines.append(f"{who}: {text}")
        return "\n".join(lines)

    def _rule_reply(
        self,
        agent_utterance: str,
        triggered_like: Optional[str],
        triggered_dislike: Optional[str],
    ) -> str:
        L = self.language
        stage = self.state.stage

        if triggered_dislike and self.state.anxiety > 0.4:
            return self._template("evade", L)

        if triggered_like:
            return self._template("warm", L).format(topic=triggered_like)

        if "?" in agent_utterance:
            if stage in (Stage.MODERATE_AD, Stage.SEVERE_AD):
                return self.rng.choice(
                    self._templates("dont_remember", L)
                )
            return self.rng.choice(self._templates("doubtful_answer", L))

        return self.rng.choice(self._templates("neutral", L))

    @staticmethod
    def _templates(key: str, lang: str) -> list[str]:
        bank = {
            "es": {
                "evade": ["Ay, no... mejor hablamos de otra cosa.",
                          "Eso... no me gusta acordarme. ¿Y tú qué tal?",
                          "Prefiero no hablar de eso ahora."],
                "warm": ["Ay, {topic}... me alegra que lo digas. Me encanta.",
                         "Sí, {topic}, claro que lo recuerdo. ¡Qué buenos tiempos!",
                         "{topic}, qué bonito... cuéntame más."],
                "dont_remember": ["No me acuerdo... lo siento.",
                                  "Mmm... eso ya no me viene.",
                                  "Eh... no sé, no caigo."],
                "doubtful_answer": ["Pues... creo que sí, no estoy segura.",
                                    "A ver... me parece que...",
                                    "Sería... esa cosa, ¿no?"],
                "neutral": ["Vale.", "Ya.", "Mmm.", "Sí, sí.", "Entiendo."],
            },
            "en": {
                "evade": ["Oh... let's talk about something else.",
                          "I'd rather not... how have you been?",
                          "Not today, please."],
                "warm": ["Oh, {topic}... I love that.",
                         "Yes, {topic}, I remember. Good times!",
                         "{topic}, how lovely... tell me more."],
                "dont_remember": ["I don't remember... sorry.",
                                  "Hmm... it doesn't come to me.",
                                  "Uh... no, I can't."],
                "doubtful_answer": ["Well... I think so, not sure.",
                                    "Let me see... I'd say...",
                                    "It was... that thing, right?"],
                "neutral": ["Okay.", "Right.", "Mhm.", "Yes, yes.", "I see."],
            },
        }
        return bank[lang][key]

    def _template(self, key: str, lang: str) -> str:
        return self.rng.choice(self._templates(key, lang))

    # ----------------------------------------------------------------
    # Stage-typical noise injection
    # ----------------------------------------------------------------
    def _inject_stage_phenomena(self, text: str) -> str:
        cfg = STAGE_INTENSITY[self.state.stage]
        rng = self.rng

        # Filler at the beginning
        if rng.random() < cfg["filler"]:
            text = rng.choice(FILLERS[self.language]) + " " + text

        # Anomia: replace one mid-sentence content word
        if rng.random() < cfg["anomia"]:
            tokens = text.split()
            if len(tokens) > 4:
                idx = rng.randint(2, len(tokens) - 2)
                if len(tokens[idx]) > 4:
                    tokens[idx] = rng.choice(ANOMIA_SUBS[self.language])
                    text = " ".join(tokens)

        # Repetition: duplicate last fragment
        if rng.random() < cfg["repeat"]:
            tokens = text.split()
            if len(tokens) > 3:
                tail = " ".join(tokens[-2:])
                text = text + " ... " + tail

        # Truncation: cut the sentence short
        if rng.random() < cfg["truncation"]:
            tokens = text.split()
            if len(tokens) > 4:
                cutoff = rng.randint(3, len(tokens) - 1)
                text = " ".join(tokens[:cutoff]) + "..."

        return text

    # ----------------------------------------------------------------
    # Bookkeeping
    # ----------------------------------------------------------------
    def record_test_outcome(self, success: bool) -> None:
        if success:
            self.state.cognitive_successes += 1
            self.state.step_mood(+0.08)
            self.state.step_anxiety(-0.05)
        else:
            self.state.cognitive_failures += 1
            self.state.step_mood(-0.05)
            self.state.step_anxiety(+0.05)

    def reset(self) -> None:
        self.history.clear()
        self.state.history_length = 0
        self.state.cognitive_successes = 0
        self.state.cognitive_failures = 0
        self.state.fatigue = self.rng.uniform(0.0, 0.2)
        self.state.anxiety = self.rng.uniform(0.0, 0.3)
        self.state.mood = self.rng.uniform(-0.2, 0.3)
        self.profile.revealed_likes.clear()
        self.profile.revealed_dislikes.clear()

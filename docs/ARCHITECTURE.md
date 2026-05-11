# Arquitectura

## Visión de alto nivel

```
┌────────────────────────────────────────────────────────────────────┐
│                       Agente conversacional                         │
│                                                                     │
│   Política RL (PPO/REINFORCE/Scripted)                              │
│   ──> Action ∈ {OPEN_QUESTION, PROBE_LIKE, VALIDATE_EMOTION,        │
│                COGNITIVE_TEST_EASY/HARD, REMINISCE, CHANGE_TOPIC,   │
│                SHORT_REASSURE, CLOSE_TURN}                          │
│   ──> Renderer: convierte la acción en una frase concreta           │
└─────────────────────────┬──────────────────────────────────────────┘
                          │ utterance
                          ▼
┌────────────────────────────────────────────────────────────────────┐
│                       Entorno (Gymnasium)                           │
│                                                                     │
│   observation = [mmse_norm, fatigue, anxiety, mood, discovery_rate, │
│                  n_likes_revealed_norm, n_dislikes_revealed_norm,   │
│                  stage_one_hot(5)]                                  │
│                                                                     │
│   reward = α·descubrimiento + β·éxito_test + γ·Δmood                │
│            − δ·Δfatiga − ε·Δansiedad − ζ·inadecuación                │
└─────────────────────────┬──────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────────┐
│                  Simulador de paciente (clase central)              │
│                                                                     │
│   CognitiveState : MMSE, stage (CDR), fatigue, anxiety, mood        │
│   InterestProfile: name, age, likes (filias), dislikes (fobias),    │
│                    biographical, revealed_*                         │
│                                                                     │
│   reply(utterance) ──> PatientTurn                                  │
│       1. Detecta filias/fobias tocadas en la frase del agente       │
│       2. Actualiza estado (mood ↑/↓, anxiety ↑/↓, fatigue ↑)        │
│       3. Genera respuesta:                                          │
│             a) LLM (Groq llama-3.1) con persona condicionada, o     │
│             b) Plantillas de reglas si no hay LLM                   │
│       4. Inyecta fenómenos lingüísticos típicos de la fase:         │
│             fillers, repeticiones, anomia, truncaciones             │
└─────────────────────────┬──────────────────────────────────────────┘
                          │ transcript
                          ▼
┌────────────────────────────────────────────────────────────────────┐
│                Extractor de señales lingüísticas                    │
│                                                                     │
│   TTR, MATTR (w=20), longitud media, filler_ratio,                  │
│   repetition_ratio, anomia_ratio, truncation_ratio,                 │
│   idea_density_proxy                                                │
└─────────────────────────┬──────────────────────────────────────────┘
                          │ features
                          ▼
┌────────────────────────────────────────────────────────────────────┐
│                ProgressionDetector (heurístico)                     │
│                                                                     │
│   Compara features con baseline (sesión previa o normas).           │
│   ── score ∈ [-1, +1]   (+ → decline, - → mejora/reserva)           │
│   ── confidence ∈ [0,1] (sube con nº de elocuciones)                │
│   ── per_feature {ttr: -0.5, repetition: +0.8, ...}                 │
│   ── notes ["TTR bajo el baseline", ...]                            │
└────────────────────────────────────────────────────────────────────┘
```

## Modos de ejecución del simulador

| Modo | Latencia | Coste | Cuándo usar |
|---|---|---|---|
| `rules_only` | µs | $0 | Entrenamiento RL (millones de pasos) |
| `llm_hybrid` | 1-3 s | Groq free tier | Generación sintética rica, demo |
| `llm_only` | 1-3 s | Groq free tier | Inspección cualitativa |

## Diagrama de turno

```
agente.act(obs)
   │ AgentAction
   ▼
renderer.render_action(sim, action, bank)
   │ utterance, (test)
   ▼
sim.reply(utterance)
   │ - detecta filia/fobia
   │ - actualiza estado
   │ - genera texto (LLM o reglas)
   │ - inyecta fenómenos según fase
   ▼ patient_turn
test_bank.evaluate(test, patient_turn.text)  [opcional]
   │ success/fail
   ▼
compute_reward(state_before, sim_after, ...)
   │ reward + componentes
   ▼
obs' = env._observe()
```

## Datos y persistencia

- `data/public/` — guías y papers públicos, regenerable con `scripts/download_public_data.py`.
- `data/synthetic/*.jsonl` — generado por `scripts/generate_synthetic.py`. **No** se versionará por defecto (puede contener nombres simulados que parezcan reales).
- `data/clinical/` — DementiaBank y similares, una vez aprobado el acceso. Ignorada por git.
- `models/*.zip` — pesos de PPO. Ignorada por git.

## Extensión: añadir un dataset real al pipeline

1. Parsear los `.cha` (formato CHAT) con `pylangacq` o el parser propio.
2. Construir un `PatientProfile` y un `CognitiveState` a partir de los metadatos.
3. Inicializar el simulador con `PatientSimulator(profile=...)` y omitir `replay` cuando se quiera reproducir transcripciones reales.
4. Reajustar `NORMS_HEALTHY` y `NORMS_MILD_AD` en `signals/progression_detector.py` con estadísticas calculadas sobre el corpus.

# Roadmap

Estado del prototipo: **v0.1.0** subido en
`https://github.com/upocuantitativo/alzheimer-chat-rl`.

A continuación, el plan ordenado por bloques. Cada paso indica si depende de
una aprobación externa (📩) o se puede ejecutar localmente (💻).

---

## Bloque A — Acceso a datos clínicos

| # | Paso | Tipo | Estado |
|---|---|---|---|
| A1 | Enviar el email de solicitud a DementiaBank (`macw@cmu.edu`) usando la plantilla de `docs/DATA_ACCESS.md` | 📩 | pendiente |
| A2 | Firmar el `Data Use Agreement` y adjuntarlo en el email | 📩 | pendiente |
| A3 | Solicitar acceso adicional a **ADReSS 2020** y **ADReSSo 2021** | 📩 | pendiente |
| A4 | Solicitar acceso a **TAUKADIAL 2024** (`taukadial2024@ed.ac.uk`) | 📩 | pendiente |
| A5 | Al recibir los datos, colocar en `data/dementiabank/<corpus>/` y `data/adress/<año>/` (ambas ignoradas por git) | 💻 | bloqueado por A1–A4 |

Tiempo realista de espera: **2–4 semanas**.

---

## Bloque B — Recursos públicos (no bloqueado)

| # | Paso | Tipo |
|---|---|---|
| B1 | Ejecutar `python scripts/download_public_data.py` (descarga guías oficiales: CEAFA, Alzheimer's Association, paper MultiConAD) | 💻 |
| B2 | Construir un índice básico de buenas prácticas a partir de las guías para usar como sistema de RAG opcional del agente | 💻 |
| B3 | Buscar corpus conversacionales públicos generales (EmpatheticDialogues, DailyDialog, MELD) como datos proxy para preentrenar embeddings | 💻 |

---

## Bloque C — Calibración del simulador con datos reales

Una vez se tengan al menos un subcorpus de DementiaBank:

| # | Paso |
|---|---|
| C1 | Añadir parser CHAT (`pylangacq`) en `src/data/chat_parser.py` |
| C2 | Extraer features lingüísticas con `src/signals/linguistic_features.py` sobre **HC**, **MCI**, **mild AD**, **moderate AD** |
| C3 | Recalibrar `NORMS_HEALTHY` y `NORMS_MILD_AD` en `src/signals/progression_detector.py` con las medianas reales |
| C4 | Recalibrar las intensidades por fase (`STAGE_INTENSITY` en `patient.py`) ajustando filler/repetition/anomia/truncation a las observadas |
| C5 | Validar que el `ProgressionDetector` separa AD de HC con AUC ≥ 0.75 en hold-out |

---

## Bloque D — Mejoras del simulador y agente

| # | Paso |
|---|---|
| D1 | Añadir filias/fobias dinámicas: el simulador puede revelar más con el tiempo si el agente genera confianza |
| D2 | Añadir un estado de **memoria episódica** simulada (el paciente recuerda con probabilidad ↓ por fase lo que se dijo hace varios turnos) |
| D3 | Sustituir templates de acciones por generación constreñida del LLM (mantener la acción semánticamente, variar la superficie) |
| D4 | Soporte chino y catalán (datos TAUKADIAL y futuro SpeechDx) |
| D5 | Multimodal: prosodia simulada (latencia, longitud, signos de pausa) → señales adicionales |

---

## Bloque E — Entrenamiento RL

| # | Paso |
|---|---|
| E1 | Sweep de hiperparámetros PPO (`learning_rate`, `gamma`, `ent_coef`) con `optuna` |
| E2 | Comparar PPO vs **scripted** vs **random** en 1.000 episodios sintéticos. Métricas: recompensa, discovery_rate, anxiety media, fatigue final |
| E3 | Probar **REINFORCE** y **A2C** como alternativas más simples |
| E4 | Curriculum learning: empezar con pacientes en fase MCI, ir endureciendo a AD moderado |
| E5 | Exponer el LLM como oferta de acción adicional (acción discreta + slot textual generado) — pasa de Discrete a multi-discrete |

---

## Bloque F — Evaluación

| # | Paso |
|---|---|
| F1 | Diseñar un panel de **expertos** (geriatras, neuropsicólogos, terapeutas ocupacionales) para puntuar 50 conversaciones sintéticas en empatía, adecuación y seguridad |
| F2 | Comparar PPO entrenado contra scripted en el panel (estudio ciego) |
| F3 | Métricas automáticas: F1 en clasificación HC/MCI/AD sobre features del simulador vs reales |
| F4 | Test de robustez frente a prompts adversariales (preguntas que invitan a confabular, contenido sensible) |

---

## Bloque G — Producto/UI (opcional, post-prototipo)

| # | Paso |
|---|---|
| G1 | UI mínima Gradio sobre `chat_demo.py` |
| G2 | Persistencia por usuario: progresión longitudinal (sesión a sesión) con CSV cifrado |
| G3 | Panel para cuidador: ver score de progresión, filias descubiertas, alertas (ansiedad alta, fatiga alta) |
| G4 | Despliegue local on-premise (priorizar privacidad — no SaaS) |

---

## Bloque H — Cumplimiento

| # | Paso |
|---|---|
| H1 | Borrador de **DPIA** (Data Protection Impact Assessment) |
| H2 | Borrador de información al paciente y al representante legal (consentimiento) |
| H3 | Presentar al **CEI de la UPO** antes de cualquier piloto con personas |
| H4 | Evaluar si el sistema entra en `Annex III` del AI Act → clasificación de alto riesgo |

---

## Sugerencias de orden

1. **Esta semana**: B1, B2, A1, A2, A3, A4 (mandar los emails ya — la espera es larga).
2. **Mientras esperas (1–2 semanas)**: D1, D2, E1, E2, F1 (panel de evaluación con datos sintéticos).
3. **Cuando lleguen los datos (semana 3–5)**: C1–C5.
4. **Semana 6+**: E3–E5, F2–F4, G1.

---

## Glosario rápido

- **MMSE**: Mini-Mental State Examination (0–30; 24+ normal).
- **CDR**: Clinical Dementia Rating (0 / 0.5 / 1 / 2 / 3).
- **MCI**: Mild Cognitive Impairment / Deterioro Cognitivo Leve.
- **TTR / MATTR**: Type-Token Ratio / Moving-Average TTR — diversidad léxica.
- **PPO**: Proximal Policy Optimization (algoritmo de RL).
- **DementiaBank / ADReSS**: corpus clínicos restringidos.
- **CEAFA**: Confederación Española de Alzheimer.
- **DPIA**: Data Protection Impact Assessment (RGPD).

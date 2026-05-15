# Alzheimer Chat-RL

Prototipo de investigación para un sistema de chat dirigido a personas con enfermedad de Alzheimer (EA) y deterioro cognitivo leve (DCL). El sistema:

1. Mantiene una conversación adaptada a la fase cognitiva del usuario.
2. Detecta **filias, fobias e intereses** para personalizar el diálogo.
3. Propone **pruebas cognitivas graduadas** (memoria, fluencia, denominación, orientación) que refuerzan capacidades preservadas.
4. Extrae **señales lingüísticas** que sugieren progresión o estabilidad de la enfermedad.
5. Se entrena mediante **aprendizaje por refuerzo (RL)** sobre un **simulador de paciente** híbrido reglas+LLM, capaz de generar miles de escenarios sintéticos sin datos reales.

> ⚠️ **No es un dispositivo médico**. Este código es exclusivamente para investigación. No diagnostica, no sustituye a profesionales sanitarios y no debe usarse sin supervisión clínica y consentimiento informado. Ver [`docs/ETHICS.md`](docs/ETHICS.md).

## Estado del proyecto

| Componente | Estado |
|---|---|
| Simulador de paciente (reglas + LLM) | ✅ Funcional |
| Entorno RL (Gymnasium) | ✅ Funcional |
| Detector de señales lingüísticas | ✅ Funcional |
| Pruebas cognitivas adaptativas | ✅ Banco inicial |
| Generación sintética masiva | ✅ Script CLI |
| Entrenamiento PPO | ✅ Configurable (Stable-Baselines3) |
| Demo de chat CLI | ✅ Funcional |
| Aplicación web (FastAPI + SPA) | ✅ Funcional — `python scripts/run_api.py` |
| Datos clínicos reales (DementiaBank, ADReSS…) | ⏳ Requieren solicitud manual — ver [`docs/DATA_ACCESS.md`](docs/DATA_ACCESS.md) |

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                       Agente Conversacional                      │
│                (política RL: PPO / REINFORCE / scripted)         │
│      acciones: preguntar, validar, proponer reto, cambiar tema   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ acción
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Entorno (AlzheimerChatEnv)                    │
│   reward = empatía + adecuación cognitiva + utilidad terapéutica │
│            − fatiga inducida − ansiedad inducida                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │ respuesta + estado oculto
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│           Simulador de paciente (PatientSimulator)               │
│  Estado: MMSE, fase (CDR), fatiga, ansiedad, filias/fobias       │
│  Generación: reglas lingüísticas + LLM (Groq llama-3.1)          │
│  Inyecta: pausas, repeticiones, anomia, confabulación según fase │
└─────────────────────────────────────────────────────────────────┘
                            │ transcripción
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Extractor de señales lingüísticas                │
│  TTR, MATTR, longitud media, repeticiones, anomia, fillers,     │
│  coherencia temática → score de progresión                       │
└─────────────────────────────────────────────────────────────────┘
```

## Aplicación web

El prototipo incluye una interfaz completa accesible desde el navegador.

**Arrancar (Windows):** doble clic en `run_app.bat` — el navegador se abre solo.

**Arrancar (cualquier OS):**
```bash
pip install -r requirements.txt
python scripts/run_api.py
```

Una vez en marcha, abre **[http://localhost:8000](http://localhost:8000)** y elige entre las tres interfaces:

| Interfaz | Ruta | Para quién |
|---|---|---|
| Sesión de conversación | `/app` | Cuidador o investigador — interacción turno a turno |
| Dashboard clínico | `/dashboard` | Cuidador — seguimiento de sesiones, alarmas, gráficas |
| Panel científico | `/science` | Investigador — distribuciones, eficacia de acciones, arquitectura RL |

> La API REST está documentada automáticamente en [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Quick start (CLI)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. (Opcional) Configurar Groq para LLM gratuito
cp .env.example .env
# editar .env y poner tu GROQ_API_KEY (gratis en https://console.groq.com)

# 3. Probar el simulador interactivamente
python scripts/chat_demo.py --mode interactive

# 4. Generar 1000 conversaciones sintéticas
python scripts/generate_synthetic.py --n 1000 --out data/synthetic/run_001.jsonl

# 5. Entrenar agente RL (PPO)
python scripts/train_rl.py --timesteps 50000 --out models/ppo_v1.zip

# 6. Descargar recursos públicos (guías oficiales de comunicación)
python scripts/download_public_data.py
```

## Razonador gratuito (Groq)

Por defecto el simulador usa [Groq Cloud](https://console.groq.com) — inferencia gratuita con modelos `llama-3.1-8b-instant` y `llama-3.3-70b-versatile`. Si no se configura `GROQ_API_KEY`, el simulador cae en **modo reglas** (sin LLM), que sigue siendo funcional para entrenar RL — solo las respuestas son menos naturales.

Alternativas configurables: Ollama local (`OLLAMA_HOST`), HuggingFace Inference API (`HF_TOKEN`).

## Datos

El proyecto se diseñó para funcionar **sin datos clínicos reales** usando el simulador. Los datasets clínicos relevantes (DementiaBank, ADReSS, TAUKADIAL, SpeechDx) **requieren solicitud manual** con acuerdo institucional firmado — ver [`docs/DATA_ACCESS.md`](docs/DATA_ACCESS.md). El script `scripts/download_public_data.py` baja únicamente recursos públicos: guías oficiales de la Alzheimer's Association, CEAFA y el Ministerio de Sanidad.

## Estructura del repositorio

```
ALZAIMER/
├── README.md
├── requirements.txt
├── .env.example
├── LICENSE
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ETHICS.md
│   └── DATA_ACCESS.md
├── src/
│   ├── patient_simulator/
│   ├── chatbot/
│   ├── rl/
│   ├── llm/
│   ├── signals/
│   └── data/
├── scripts/
│   ├── chat_demo.py
│   ├── generate_synthetic.py
│   ├── train_rl.py
│   └── download_public_data.py
├── data/
│   ├── public/         (descargado por el script)
│   └── synthetic/      (generado por el RL)
├── notebooks/
└── tests/
```

## Citación y autoría

Universidad Pablo de Olavide — proyecto de investigación.
Contacto: mchaves@upo.es

## Licencia

MIT — ver [`LICENSE`](LICENSE).

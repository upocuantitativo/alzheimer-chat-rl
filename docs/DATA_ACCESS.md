# Acceso a datos clínicos

Los datasets relevantes para este proyecto **no se pueden descargar automáticamente**: requieren acuerdo institucional firmado y, en algunos casos, contacto directo con los equipos organizadores. Esta guía resume los pasos por dataset.

## Tabla resumen

| Dataset | Idioma | Tamaño | Cómo solicitar | Tiempo aprox. |
|---|---|---|---|---|
| **DementiaBank** (Pitt, Delaware, Baycrest…) | Inglés | ~500 audios | Email a TalkBank | 1–2 semanas |
| **DementiaBank Ivanova** | Español | 74 AD + 197 control + 90 MCI | Vía DementiaBank | 1–2 semanas |
| **DementiaBank PerLA** | Español | 21 AD (solo transcripciones) | Vía DementiaBank | 1–2 semanas |
| **ADReSS 2020** | Inglés | 156 sesiones | DementiaBank + email | 2–3 semanas |
| **ADReSSo 2021** | Inglés | Audio limpio + fluidez | DementiaBank + email | 2–3 semanas |
| **TAUKADIAL 2024** | Inglés + chino | 3 imágenes por sujeto | Email organizadores | 2–4 semanas |
| **SpeechDx** | Inglés/ES/CAT | ~2.650 sujetos (futuro) | Consorcio cerrado | No disponible |
| **MultiConAD** | Multilingüe | Derivado de 16 fuentes | Reutilizar tras citar | Inmediato |

## 1. DementiaBank (Pitt + Ivanova + PerLA + variantes)

1. Ir a https://talkbank.org/dementia/access/
2. Registrar una **TalkBank membership** (gratuita) — formulario web.
3. Descargar y firmar el acuerdo de uso (`Data Use Agreement`).
4. Enviar el acuerdo firmado a `macw@cmu.edu` con copia a la persona responsable del subcorpus que necesitas.
5. Al ser aprobado recibirás credenciales para descargar audio (WAV) y transcripciones (CHAT).
6. Citar obligatoriamente las referencias del subcorpus en cualquier publicación.

> Una vez aprobado, colocar los archivos descargados en `data/dementiabank/<corpus>/` (esta carpeta está ignorada por git).

## 2. ADReSS 2020 / ADReSSo 2021

1. Completar primero el paso de DementiaBank.
2. Solicitar acceso específico por email — direcciones publicadas en:
   - ADReSS 2020: https://luzs.gitlab.io/adress/
   - ADReSSo 2021: https://talkbank.org/dementia/ADReSSo-2021/
3. Los datos llegan como ZIPs con WAV preprocesado + transcripciones + CSV con metadatos (edad, sexo, MMSE).
4. Licencia: **CC-BY-NC-ND 4.0** — no se permite redistribuir ni derivar comercialmente.

Colocar en `data/adress/2020/` o `data/adress/2021/`.

## 3. TAUKADIAL 2024

1. Estar registrado en DementiaBank.
2. Contactar `taukadial2024@ed.ac.uk` describiendo el uso previsto.
3. Recibirás un enlace temporal con audio en inglés y chino + transcripciones automáticas + fondo demográfico.

## 4. MultiConAD

- Paper: https://arxiv.org/abs/2502.19208
- Recoge datos derivados de 16 fuentes públicas (incluyendo subcorpus de DementiaBank).
- El acceso a los datos individuales sigue requiriendo el permiso de la fuente original.
- Citar el paper de MultiConAD **y** cada fuente cuando publiques.

## 5. SpeechDx

- Consorcio BarcelonaBeta + ADDF — actualmente cerrado.
- Seguir noticias en: https://www.barcelonabeta.org

## ¿Y mientras tanto?

Mientras esperas a la aprobación de DementiaBank, este repositorio te permite:
- Entrenar el RL sobre el simulador `rules_only` (no requiere datos).
- Validar pipelines de extracción de features con `data/synthetic/`.
- Probar el chatbot con `chat_demo.py` (modo interactivo).

Cuando lleguen los datos reales, el flujo es:

```
data/dementiabank/Pitt/cha/*.cha   →   parser CHAT   →   data/processed/pitt.jsonl
                                                            │
                                                            ▼
                                         calibración del simulador (MMSE bins)
                                                            │
                                                            ▼
                                     reentrenamiento del agente RL
```

Hay un parser CHAT muy compacto en `tools/chat_parser.py` (a añadir cuando llegues a ese punto — la librería `pylangacq` también sirve).

## Plantilla de email para DementiaBank

```
To: macw@cmu.edu
Subject: Data Use Agreement — DementiaBank (Ivanova / Pitt / ADReSS)

Dear Prof. MacWhinney,

I am [name], affiliated with [institution], working on a research prototype
of a conversational AI to support communication with people with Alzheimer's
disease. We would like to request access to the following DementiaBank
subcorpora for non-commercial, academic research:

  - Pitt corpus
  - Ivanova (Spanish)
  - ADReSS 2020 / ADReSSo 2021

I have attached the signed Data Use Agreement. We will cite the required
references in any resulting publication.

Best regards,
[name, institution, email]
```

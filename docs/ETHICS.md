# Consideraciones éticas y de seguridad

> Este código es un prototipo de investigación. **No es un dispositivo médico** y no debe usarse para diagnóstico, triaje, terapia ni ninguna decisión clínica sin supervisión profesional y consentimiento informado conforme al RGPD/LOPDGDD y normativa local equivalente.

## 1. Marco legal aplicable

- **RGPD (UE 2016/679)** y **LOPDGDD (3/2018, España)**: los datos de salud son categoría especial (Art. 9). Requieren consentimiento explícito del paciente o de su representante legal.
- **Ley 41/2002 de Autonomía del Paciente** (España): derecho a la información clínica y al control de la historia clínica.
- **AI Act (UE)**: los sistemas de IA en salud para pacientes vulnerables están clasificados de alto riesgo — obligan a documentación de impactos, transparencia y supervisión humana.
- **MDR (UE 2017/745)**: si el sistema se promueve para evaluar o tratar Alzheimer, podría requerir marcado CE como dispositivo médico.
- **HIPAA** (si se despliega en EE. UU.) y equivalentes locales.

## 2. Consentimiento

Una persona con Alzheimer puede tener capacidad de consentimiento variable:
- **DCL / leve**: capacidad generalmente preservada → consentimiento informado directo.
- **Moderado**: capacidad parcial → consentimiento del representante legal + asentimiento del paciente.
- **Avanzado**: representante legal.

Cualquier despliegue del sistema debe:
1. Declarar que el interlocutor es una IA, no un médico.
2. Explicar qué datos se recogen, durante cuánto tiempo, y para qué.
3. Permitir revocación en cualquier momento (derecho al olvido).
4. Disponer de un canal de emergencia humano (familiar/cuidador) ante deterioro agudo, ideación suicida o crisis.

## 3. Riesgos identificados

| Riesgo | Mitigación implementada | Mitigación pendiente |
|---|---|---|
| El chatbot valida confabulaciones o delirios | No se entrena sobre datos reales sin supervisión; reward penaliza acciones que aumentan ansiedad | Filtros adicionales sobre la respuesta del LLM |
| Sesgo lingüístico (entrenamiento sesgado a inglés caucásico) | Soporte explícito ES/EN, simulador en español | Validación con hablantes mayores hispanohablantes |
| El sistema sugiere diagnóstico | El detector de progresión devuelve un score con `confidence` y `notes` aclarando que **no es diagnóstico** | Disclaimer obligatorio en UI |
| Información sensible registrada en logs | `.env` y `data/clinical/` están en `.gitignore`; los registros sintéticos no contienen PII | Cifrado en reposo si se despliega |
| El paciente se fatiga o angustia | Reward penaliza fatiga/ansiedad inducida; acción `SHORT_REASSURE` y `CLOSE_TURN` | Pruebas con cuidadores reales |

## 4. Datos sintéticos vs. reales

El simulador permite generar miles de conversaciones sin tocar datos reales. Esto:
- Acelera la iteración sobre el RL.
- Evita exponer datos clínicos durante el desarrollo.
- **No** sustituye a la validación con corpus reales (DementiaBank, ADReSS) ni a la evaluación con usuarios.

## 5. Buenas prácticas heredadas de las guías oficiales

Las acciones del agente (`src/chatbot/actions.py`) y las plantillas están alineadas con:
- Alzheimer's Association — *La comunicación* (folleto bilingüe).
- CEAFA — *Cómo comunicarse con una persona con Alzheimer*.
- Ministerio de Sanidad — *Manual para cuidadores de personas con demencia* (iSupport adaptado).

Principios incorporados:
- Frases cortas y vocabulario sencillo.
- Validar emociones antes de redirigir.
- No contradecir; cambiar de tema con cuidado.
- Permitir tiempo de respuesta (en una interfaz real esto debe traducirse en timeouts generosos).
- Reminiscencia como vehículo de identidad personal.

## 6. Lo que este sistema NO hace

- No emite diagnósticos de Alzheimer.
- No reemplaza a profesionales (geriatra, neuropsicólogo, terapeuta ocupacional).
- No realiza intervenciones médicas (fármacos, terapias).
- No registra audio sin consentimiento explícito por sesión.
- No conecta con redes sociales ni servicios externos sin aprobación.

## 7. Auditoría

Para preparar un despliegue piloto, antes de cualquier contacto con personas reales se requiere:
- Revisión por el **CEI (Comité de Ética de la Investigación)** correspondiente.
- DPIA (Data Protection Impact Assessment) bajo RGPD.
- Documento de información al paciente y a la familia.
- Plan de contingencia clínica.

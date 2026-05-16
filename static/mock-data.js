// Mock data shared by the three Alzheimer Chat-RL prototypes.
// Realistic Spanish-context names + clinically-plausible values.

window.MOCK = (() => {
  // ── Pacientes (para médicos) ─────────────────────────────────
  const patients = [
    {
      id: 'p001', name: 'María Dolores Ramírez', age: 78, city: 'Sevilla',
      stage: 'MILD_AD', stageLabel: 'EA leve', mmse: 22, mmseDelta: -1,
      alarms: 2, urgency: 'alta', lastSession: 'Hoy · 11:24',
      sessionsThisMonth: 12,
      mmseSeries: [27, 26, 26, 25, 25, 24, 23, 23, 22, 22],
      anxietySeries: [.2,.3,.25,.4,.5,.55,.4,.6,.7,.65],
      flags: ['Pico de ansiedad en 3 últimas sesiones', 'Anomia creciente en denominación'],
      caregiver: 'Lucía (hija)',
    },
    {
      id: 'p002', name: 'Antonio Heredia Núñez', age: 81, city: 'Córdoba',
      stage: 'MODERATE_AD', stageLabel: 'EA moderada', mmse: 16, mmseDelta: -3,
      alarms: 4, urgency: 'critica', lastSession: 'Hoy · 09:02',
      sessionsThisMonth: 18,
      mmseSeries: [22, 21, 21, 20, 19, 19, 18, 17, 17, 16],
      anxietySeries: [.35,.4,.5,.55,.6,.65,.7,.75,.8,.78],
      flags: ['Caída MMSE −3 en 4 sem.', '3 silencios consecutivos · 2 sesiones', 'Fatiga crítica recurrente'],
      caregiver: 'Carmen (esposa)',
    },
    {
      id: 'p003', name: 'Pilar Cebrián Vidal', age: 74, city: 'Valencia',
      stage: 'MCI', stageLabel: 'DCL', mmse: 26, mmseDelta: 0,
      alarms: 0, urgency: 'estable', lastSession: 'Ayer · 18:40',
      sessionsThisMonth: 8,
      mmseSeries: [26, 27, 26, 26, 26, 26, 27, 26, 26, 26],
      anxietySeries: [.15,.2,.18,.15,.22,.2,.18,.15,.2,.18],
      flags: ['Estable · sin alertas activas'],
      caregiver: 'José Luis (esposo)',
    },
    {
      id: 'p004', name: 'Juan Manuel Espinosa', age: 83, city: 'Granada',
      stage: 'MILD_AD', stageLabel: 'EA leve', mmse: 20, mmseDelta: -1,
      alarms: 1, urgency: 'media', lastSession: 'Ayer · 10:15',
      sessionsThisMonth: 10,
      mmseSeries: [24, 23, 23, 22, 22, 21, 21, 21, 20, 20],
      anxietySeries: [.3,.32,.3,.35,.4,.38,.42,.45,.48,.5],
      flags: ['Latencia media >9 s · subiendo'],
      caregiver: 'Marta (hija)',
    },
    {
      id: 'p005', name: 'Encarnación Ortiz Pino', age: 76, city: 'Málaga',
      stage: 'MCI', stageLabel: 'DCL', mmse: 25, mmseDelta: -1,
      alarms: 1, urgency: 'media', lastSession: 'Hace 2 días',
      sessionsThisMonth: 6,
      mmseSeries: [28, 27, 27, 26, 26, 26, 25, 26, 25, 25],
      anxietySeries: [.18,.2,.22,.25,.3,.28,.32,.35,.38,.4],
      flags: ['Engagement bajo en trivia cultural'],
      caregiver: 'Rocío (hija)',
    },
    {
      id: 'p006', name: 'Francisco Javier Lozano', age: 79, city: 'Sevilla',
      stage: 'HEALTHY', stageLabel: 'Sano', mmse: 29, mmseDelta: 0,
      alarms: 0, urgency: 'estable', lastSession: 'Hace 4 días',
      sessionsThisMonth: 4,
      mmseSeries: [29,29,30,29,29,29,30,29,29,29],
      anxietySeries: [.1,.12,.1,.1,.15,.12,.1,.12,.1,.1],
      flags: ['Línea base · referencia'],
      caregiver: 'Independiente',
    },
  ];

  // ── Conversación actual (vista mayor) ─────────────────────────
  const conversation = [
    { who: 'asistente', text: '¡Buenos días, María Dolores! ¿Cómo ha amanecido hoy?', time: '11:24' },
    { who: 'usuario',   text: 'Pues con un poquito de frío, pero bien.', time: '11:24' },
    { who: 'asistente', text: 'Me alegra oírla. ¿Le apetece que hablemos un rato? Puedo contarle un refrán o ponerle una canción de su época.', time: '11:25' },
    { who: 'usuario',   text: 'Mejor un refrán, que mi madre los sabía todos.', time: '11:25' },
    { who: 'asistente', text: '«A quien madruga, Dios le ayuda». ¿Lo conocía?', time: '11:26' },
  ];

  // ── Transcripción (vista médico) ──────────────────────────────
  const transcript = [
    { turn: 1, time: '11:24:02', action: 'GREETING', agent: '¡Buenos días, María Dolores! ¿Cómo ha amanecido?', patient: 'Pues con un poco de frío, pero bien.', lat: 2.1, test: null, flag: null },
    { turn: 2, time: '11:24:58', action: 'ASK_PREFERENCE', agent: '¿Le apetece un refrán o una canción?', patient: 'Mejor un refrán.', lat: 3.4, test: null, flag: null },
    { turn: 3, time: '11:25:44', action: 'REFRAN', agent: '«A quien madruga, Dios le ayuda». ¿Lo conocía?', patient: 'Claro, lo decía mi madre.', lat: 4.1, test: 'memoria_semantica', testOk: true, flag: null },
    { turn: 4, time: '11:26:51', action: 'ASK_MEMORY', agent: '¿Recuerda en qué año se casó?', patient: '... no, ahora mismo no caigo.', lat: 11.8, test: 'memoria_episodica', testOk: false, flag: 'latencia_alta' },
    { turn: 5, time: '11:28:12', action: 'VALIDATE', agent: 'No pasa nada, son recuerdos lejanos.', patient: 'Eso es, hace mucho.', lat: 5.2, test: null, flag: null },
    { turn: 6, time: '11:29:01', action: 'ASK_LANGUAGE', agent: '¿Cómo se llama el objeto con el que escribimos?', patient: '... lo que se usa para... para escribir...', lat: 14.2, test: 'denominacion', testOk: false, flag: 'anomia' },
    { turn: 7, time: '11:30:48', action: 'REASSURE', agent: 'Tranquila. Es un bolígrafo. Lo tendrá a mano.', patient: '(silencio)', lat: 22.0, test: null, flag: 'silencio' },
    { turn: 8, time: '11:32:15', action: 'OFFER_MUSIC', agent: '¿Quiere que pongamos una canción de Manolo Escobar?', patient: 'Ay sí, esa me gusta.', lat: 3.0, test: null, flag: 'engagement+' },
    { turn: 9, time: '11:33:02', action: 'TRIVIA_CULTURAL', agent: '¿En qué provincia está la Giralda?', patient: 'En Sevilla, claro.', lat: 2.4, test: 'orientacion', testOk: true, flag: null },
  ];

  // ── Acciones del agente (para vista mayor — panel cuidador) ──
  const actions = [
    { id: 0, label: 'Pregunta abierta', cat: 'conv' },
    { id: 1, label: 'Explorar interés', cat: 'conv' },
    { id: 2, label: 'Validar emoción', cat: 'conv' },
    { id: 5, label: 'Reminiscencia', cat: 'conv' },
    { id: 6, label: 'Cambiar tema', cat: 'conv' },
    { id: 7, label: 'Tranquilizar', cat: 'conv' },
    { id: 3, label: 'Test fácil', cat: 'test' },
    { id: 4, label: 'Test difícil', cat: 'test' },
    { id: 9, label: 'Refrán', cat: 'cult' },
    { id: 10, label: 'Canción', cat: 'cult' },
    { id: 11, label: 'Trivia cultural', cat: 'cult' },
    { id: 12, label: 'Trivia deportes', cat: 'cult' },
  ];

  // ── Datos panel científico ────────────────────────────────────
  const science = {
    kpis: {
      sessions: 1284, turns: 18472, mmseAvg: 22.3,
      silenceRate: 0.083, alarms: 412, domains: 6,
    },
    stageDist: { HEALTHY: 142, MCI: 318, MILD_AD: 462, MODERATE_AD: 287, SEVERE_AD: 75 },
    mmseHist: [
      { bin: '0–5', n: 18 }, { bin: '5–10', n: 64 }, { bin: '10–15', n: 168 },
      { bin: '15–20', n: 312 }, { bin: '20–25', n: 458 }, { bin: '25–30', n: 264 },
    ],
    actionStats: [
      { name: 'GREETING', fit: 0.82, n: 1284 },
      { name: 'ASK_PREFERENCE', fit: 0.78, n: 2104 },
      { name: 'TELL_STORY', fit: 0.74, n: 1672 },
      { name: 'REFRAN', fit: 0.71, n: 982 },
      { name: 'OFFER_MUSIC', fit: 0.69, n: 1148 },
      { name: 'TRIVIA_CULTURAL', fit: 0.66, n: 854 },
      { name: 'VALIDATE', fit: 0.64, n: 1742 },
      { name: 'PROPOSE_ACTIVITY', fit: 0.58, n: 1320 },
      { name: 'ASK_MEMORY', fit: 0.42, n: 1610 },
      { name: 'ASK_ORIENTATION', fit: 0.38, n: 1284 },
      { name: 'ASK_LANGUAGE', fit: 0.33, n: 1102 },
      { name: 'CLOSE_TURN', fit: 0.55, n: 1284 },
      { name: 'TRIVIA_DEPORTES', fit: 0.61, n: 506 },
    ],
    // policy heatmap: 13 actions × 5 stages — probability of selecting action
    policyHeatmap: [
      // rows = stages: HEALTHY, MCI, MILD_AD, MODERATE_AD, SEVERE_AD
      // cols = actions 0..12
      [0.04,0.12,0.10,0.14,0.06,0.10,0.12,0.06,0.04,0.08,0.06,0.04,0.04],
      [0.06,0.10,0.12,0.10,0.08,0.10,0.10,0.08,0.04,0.08,0.06,0.04,0.04],
      [0.08,0.06,0.08,0.06,0.12,0.10,0.10,0.10,0.04,0.10,0.08,0.04,0.04],
      [0.12,0.04,0.04,0.04,0.12,0.08,0.08,0.16,0.04,0.10,0.12,0.02,0.04],
      [0.18,0.02,0.02,0.02,0.06,0.04,0.04,0.22,0.06,0.06,0.20,0.02,0.06],
    ],
    runs: [
      { id: 'ppo_v3.2', date: '2026-05-14', steps: '500k', reward: 0.742, success: 0.68, alarms: 0.09, status: 'best' },
      { id: 'ppo_v3.1', date: '2026-05-12', steps: '500k', reward: 0.701, success: 0.64, alarms: 0.11, status: 'ok' },
      { id: 'ppo_v3.0', date: '2026-05-09', steps: '300k', reward: 0.678, success: 0.62, alarms: 0.12, status: 'ok' },
      { id: 'reinforce_v2', date: '2026-05-05', steps: '200k', reward: 0.521, success: 0.49, alarms: 0.21, status: 'old' },
      { id: 'scripted_baseline', date: '2026-04-28', steps: '—', reward: 0.412, success: 0.42, alarms: 0.18, status: 'baseline' },
      { id: 'ppo_v2.8', date: '2026-04-22', steps: '400k', reward: 0.643, success: 0.58, alarms: 0.14, status: 'old' },
    ],
    // training curve — reward per episode, 200 episodes
    trainingCurve: Array.from({ length: 100 }, (_, i) => {
      const noise = (Math.sin(i * 1.3) + Math.cos(i * 0.7)) * 0.04;
      return Math.min(0.78, 0.2 + Math.log10(i + 1) * 0.28 + noise);
    }),
    alarmCounts: {
      ANXIETY_SPIKE: 142, SILENCE_STREAK: 98, FATIGUE_CRITICAL: 87,
      PROGRESSION: 52, ANOMIA: 33,
    },
    topicScores: [
      ['Familia', 0.84], ['Música', 0.78], ['Comida regional', 0.71],
      ['Religión', 0.62], ['Fútbol', 0.58], ['Pueblo natal', 0.55],
      ['Refranes', 0.51], ['Cine clásico', 0.44], ['Trabajo', 0.38],
      ['Política', 0.12],
    ],
  };

  return { patients, conversation, transcript, actions, science };
})();

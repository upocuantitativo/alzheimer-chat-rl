// Vista SUPERVISIÓN — para familiares y cuidadores.
// Estilo clínico (mismo palette que medico.jsx) con lenguaje llano.

const SupervisionView = () => {
  const patient = window.MOCK.patients[0]; // María Dolores — hija Lucía
  const evolutionRef  = React.useRef(null);
  const engagementRef = React.useRef(null);
  const [selectedSession, setSelectedSession] = React.useState(null);

  React.useEffect(() => {
    if (!window.Chart) return;
    Chart.defaults.font.family = '"IBM Plex Sans", system-ui, sans-serif';
    Chart.defaults.color = '#7a8694';
    Chart.defaults.borderColor = '#e5e7eb';

    if (evolutionRef.current) {
      if (evolutionRef.current._chart) evolutionRef.current._chart.destroy();
      const scores = patient.mmseSeries.map(v => Math.round((v / 30) * 100));
      evolutionRef.current._chart = new Chart(evolutionRef.current.getContext('2d'), {
        type: 'line',
        data: {
          labels: scores.map((_, i) => `Sem. ${i + 1}`),
          datasets: [{
            label: 'Bienestar cognitivo',
            data: scores,
            borderColor: '#0d5b75',
            backgroundColor: 'rgba(13,91,117,.07)',
            borderWidth: 2, tension: .35,
            pointRadius: 3, pointBackgroundColor: '#0d5b75', fill: true,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { backgroundColor: '#1a2030', titleFont: { size: 11 }, bodyFont: { size: 11 },
              callbacks: { label: ctx => `Bienestar: ${ctx.raw}%` } },
          },
          scales: {
            x: { grid: { color: '#eef0f3' }, ticks: { font: { size: 10 }, color: '#7a8694' } },
            y: { min: 0, max: 100, grid: { color: '#eef0f3' },
              ticks: { font: { size: 10 }, color: '#7a8694', callback: v => `${v}%` } },
          },
        },
      });
    }

    if (engagementRef.current) {
      if (engagementRef.current._chart) engagementRef.current._chart.destroy();
      const topics = [['Familia',.84],['Música',.78],['Comida',.71],['Refranes',.51],['Cine',.44]];
      engagementRef.current._chart = new Chart(engagementRef.current.getContext('2d'), {
        type: 'bar',
        data: {
          labels: topics.map(([t]) => t),
          datasets: [{
            data: topics.map(([,v]) => Math.round(v * 100)),
            backgroundColor: 'rgba(13,91,117,.45)',
            borderColor: '#0d5b75', borderWidth: 1, borderRadius: 4,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false },
            tooltip: { backgroundColor: '#1a2030', callbacks: { label: ctx => `${ctx.raw}% participación` } } },
          scales: {
            x: { grid: { display: false }, ticks: { font: { size: 11 }, color: '#7a8694' } },
            y: { min: 0, max: 100, grid: { color: '#eef0f3' },
              ticks: { font: { size: 10 }, color: '#7a8694', callback: v => `${v}%` } },
          },
        },
      });
    }
  }, []);

  const alarmMap = {
    'Pico de ansiedad en 3 últimas sesiones':
      { msg: 'Se ha notado algo nerviosa en las últimas sesiones', sev: 'media' },
    'Anomia creciente en denominación':
      { msg: 'Le está costando más encontrar algunas palabras', sev: 'media' },
    'Caída MMSE −3 en 4 sem.':
      { msg: 'Ha habido cambios notables en su memoria reciente', sev: 'alta' },
    '3 silencios consecutivos · 2 sesiones':
      { msg: 'Tuvo momentos de silencio largo en las últimas sesiones', sev: 'media' },
    'Fatiga crítica recurrente':
      { msg: 'Se ha cansado mucho antes de terminar algunas sesiones', sev: 'alta' },
    'Latencia media >9 s · subiendo':
      { msg: 'Le lleva algo más de tiempo responder a las preguntas', sev: 'media' },
    'Engagement bajo en trivia cultural':
      { msg: 'Últimamente participa menos en preguntas de cultura', sev: 'baja' },
  };

  const activeAlarms = patient.flags.map(f =>
    alarmMap[f] || { msg: f, sev: 'media' }
  );

  const urgencyColor = u => ({
    critica: { bg: '#fef2f1', fg: '#c0362c', dot: '#c0362c', label: 'Necesita atención' },
    alta:    { bg: '#fef6ec', fg: '#b45309', dot: '#d97706', label: 'Pendiente de revisión' },
    media:   { bg: '#fffbed', fg: '#7c5800', dot: '#a87d00', label: 'Estable con seguimiento' },
    estable: { bg: '#eef7f5', fg: '#0d6e72', dot: '#0d7c80', label: 'Todo va bien' },
  }[u]);

  const uc = urgencyColor(patient.urgency);
  const bienestar = Math.round((patient.mmse / 30) * 100);
  const tendencia = patient.mmseDelta < 0 ? '↓ Ligero descenso'
    : patient.mmseDelta > 0 ? '↑ Mejorando' : '→ Estable';
  const tendenciaColor = patient.mmseDelta < 0 ? '#c0362c'
    : patient.mmseDelta > 0 ? '#0d7c80' : '#7a8694';

  const sessions = [
    { date: 'Hoy · 11:24', duration: '11 min', mood: 'Animada',
      summary: 'Estuvo muy participativa. Habló de su madre, dijo un refrán y recordó bien dónde vive.',
      topics: ['Familia', 'Refranes'], ok: true },
    { date: 'Ayer · 10:08', duration: '14 min', mood: 'Tranquila',
      summary: 'Hubo un momento de silencio largo, pero se animó enseguida con una canción.',
      topics: ['Música'], ok: true },
    { date: 'Hace 2 días', duration: '8 min', mood: 'Algo nerviosa',
      summary: 'Le costó recordar algunas palabras y se puso un poco nerviosa. Aurora la tranquilizó.',
      topics: ['Música', 'Palabras'], ok: false },
  ];

  const weekDays = [
    { day: 'L', ok: true,  had: true  },
    { day: 'M', ok: true,  had: true  },
    { day: 'X', ok: null,  had: false },
    { day: 'J', ok: false, had: true  },
    { day: 'V', ok: true,  had: true  },
    { day: 'S', ok: null,  had: false },
    { day: 'D', ok: true,  had: true  },
  ];

  return (
    <div style={ss.root}>
      {/* ── Top nav ── */}
      <div style={ss.topnav}>
        <div style={ss.brand}>
          <div style={ss.brandMark}>♥</div>
          <div>
            <div style={ss.brandTitle}>Alzheimer Chat-RL</div>
            <div style={ss.brandSub}>Supervisión familiar · {patient.caregiver}</div>
          </div>
        </div>
        <div style={{ flex: 1 }}/>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ ...ss.statusPill, background: uc.bg, color: uc.fg, borderColor: uc.dot + '55' }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: uc.dot, display: 'inline-block' }}/>
            {uc.label}
          </div>
          <button style={ss.btnGhost}>Historial completo</button>
          <button style={ss.btnPrimary}>Iniciar sesión con Aurora</button>
        </div>
      </div>

      <div style={ss.body}>
        {/* ── Patient header strip ── */}
        <div style={ss.patientStrip}>
          <div style={{ ...ss.avatar, background: uc.bg, color: uc.fg }}>
            {patient.name.split(' ').map(s => s[0]).slice(0,2).join('')}
          </div>
          <div>
            <div style={ss.patientName}>{patient.name}</div>
            <div style={ss.patientMeta}>
              {patient.age} años · {patient.city} · {patient.stageLabel} ·
              <span style={{ marginLeft: 8 }}>Última sesión: <b style={{ color: '#1f2937' }}>{patient.lastSession}</b></span>
              <span style={{ marginLeft: 12 }}>· Cuidadora: {patient.caregiver}</span>
            </div>
          </div>
          <div style={{ flex: 1 }}/>
          <div style={{ display: 'flex', gap: 20, alignItems: 'center', fontSize: 12 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: '#1f2937', fontVariantNumeric: 'tabular-nums' }}>{bienestar}%</div>
              <div style={{ color: '#7a8694' }}>Bienestar cognitivo</div>
            </div>
            <div style={{ width: 1, height: 36, background: '#e5e7eb' }}/>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: '#1f2937', fontVariantNumeric: 'tabular-nums' }}>{patient.sessionsThisMonth}</div>
              <div style={{ color: '#7a8694' }}>Sesiones este mes</div>
            </div>
            <div style={{ width: 1, height: 36, background: '#e5e7eb' }}/>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: tendenciaColor }}>{tendencia}</div>
              <div style={{ color: '#7a8694', fontSize: 11 }}>Tendencia</div>
            </div>
          </div>
        </div>

        {/* ── Alerts ── */}
        {activeAlarms.length > 0 && (
          <div style={ss.alertsRow}>
            <div style={{ fontSize: 11, fontWeight: 600, color: '#7a8694', textTransform: 'uppercase', letterSpacing: '.06em', marginRight: 12, whiteSpace: 'nowrap' }}>
              Avisos activos
            </div>
            {activeAlarms.map((a, i) => (
              <div key={i} style={{
                ...ss.alertChip,
                background: a.sev === 'alta' ? '#fef2f1' : '#fef6ec',
                color:      a.sev === 'alta' ? '#c0362c' : '#b45309',
                borderColor: a.sev === 'alta' ? '#f5c6c2' : '#f5d6a8',
              }}>
                {a.msg}
              </div>
            ))}
          </div>
        )}

        {/* ── Main grid ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 14 }}>

          {/* Left column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

            {/* Week calendar */}
            <div style={ss.card}>
              <div style={ss.cardHeader}>
                <div>
                  <div style={ss.cardTitle}>Esta semana</div>
                  <div style={ss.cardSub}>Cómo han ido las sesiones día a día</div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                {weekDays.map((d, i) => (
                  <div key={i} style={{ flex: 1, textAlign: 'center' }}>
                    <div style={{ fontSize: 10, color: '#7a8694', marginBottom: 5, fontWeight: 600 }}>{d.day}</div>
                    <div style={{
                      height: 38, borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 11, fontWeight: 600,
                      background: !d.had ? '#f7f7f5' : d.ok === true ? '#eef7f5' : d.ok === false ? '#fef2f1' : '#fef6ec',
                      border: `1px solid ${!d.had ? '#e5e7eb' : d.ok === true ? '#b3e0d8' : d.ok === false ? '#f5c6c2' : '#f5d6a8'}`,
                      color: !d.had ? '#cbd3da' : d.ok === true ? '#0d6e72' : d.ok === false ? '#c0362c' : '#b45309',
                    }}>
                      {!d.had ? '—' : d.ok === true ? 'Bien' : d.ok === false ? 'Rev.' : 'Ok'}
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 11, color: '#7a8694' }}>
                <span style={{ display:'flex', alignItems:'center', gap:5 }}><Dot color="#0d7c80"/> Sesión buena</span>
                <span style={{ display:'flex', alignItems:'center', gap:5 }}><Dot color="#c0362c"/> Con incidencias</span>
                <span style={{ display:'flex', alignItems:'center', gap:5 }}><Dot color="#cbd3da"/> Sin sesión</span>
              </div>
            </div>

            {/* Evolution chart */}
            <div style={ss.card}>
              <div style={ss.cardHeader}>
                <div>
                  <div style={ss.cardTitle}>Evolución del bienestar cognitivo</div>
                  <div style={ss.cardSub}>Puntuación relativa sobre el nivel máximo · últimas 10 semanas</div>
                </div>
              </div>
              <div style={{ height: 170, marginTop: 10 }}><canvas ref={evolutionRef}/></div>
              <div style={{ display: 'flex', gap: 24, marginTop: 12, paddingTop: 12, borderTop: '1px solid #eef0f3' }}>
                <MetaStat label="Nivel actual" value={`${bienestar}%`} accent="#0d5b75"/>
                <MetaStat label="Tendencia" value={tendencia} accent={tendenciaColor}/>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: '#7a8694', textTransform: 'uppercase', letterSpacing: '.05em', fontWeight: 600 }}>Recomendación</div>
                  <div style={{ fontSize: 12, color: '#4a5568', marginTop: 4, lineHeight: 1.5 }}>
                    {patient.mmseDelta < 0
                      ? 'Coméntaselo al médico en la próxima visita.'
                      : 'Las sesiones están siendo positivas, continúa así.'}
                  </div>
                </div>
              </div>
            </div>

            {/* Topics */}
            <div style={ss.card}>
              <div style={ss.cardHeader}>
                <div>
                  <div style={ss.cardTitle}>Temas que más la hacen participar</div>
                  <div style={ss.cardSub}>Porcentaje de engagement medio por categoría · último mes</div>
                </div>
              </div>
              <div style={{ height: 130, marginTop: 10 }}><canvas ref={engagementRef}/></div>
              <div style={{ marginTop: 12, padding: '10px 12px', background: '#eef7f5', borderRadius: 7, fontSize: 12, color: '#0d6e72', lineHeight: 1.6 }}>
                Consejo: si la llamas, empieza por la familia o ponle una canción — eso la anima enseguida.
              </div>
            </div>
          </div>

          {/* Right column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

            {/* Last sessions */}
            <div style={ss.card}>
              <div style={ss.cardTitle}>Últimas conversaciones</div>
              <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {sessions.map((s, i) => (
                  <div key={i}
                    onClick={() => setSelectedSession(selectedSession === i ? null : i)}
                    style={{
                      padding: '10px 12px', borderRadius: 7, cursor: 'pointer',
                      background: s.ok ? '#eef7f5' : '#fef6ec',
                      borderLeft: `3px solid ${s.ok ? '#0d7c80' : '#d97706'}`,
                      border: `1px solid ${s.ok ? '#b3e0d8' : '#f5d6a8'}`,
                      borderLeftWidth: 3,
                      transition: 'opacity .15s',
                    }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, alignItems: 'center' }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: '#1f2937', fontFamily: 'IBM Plex Mono, monospace' }}>{s.date}</div>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span style={{ fontSize: 11, fontWeight: 600, color: s.ok ? '#0d6e72' : '#b45309' }}>{s.mood}</span>
                        <span style={{ fontSize: 11, color: '#7a8694' }}>{s.duration}</span>
                      </div>
                    </div>
                    <div style={{ fontSize: 12, color: '#374151', lineHeight: 1.5 }}>{s.summary}</div>
                    {selectedSession === i && (
                      <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {s.topics.map(t => (
                          <span key={t} style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, background: '#fff', color: '#4a5568', border: '1px solid #d8dee5', fontWeight: 500 }}>{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Quick actions */}
            <div style={ss.card}>
              <div style={ss.cardTitle}>Acciones</div>
              <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 7 }}>
                {[
                  'Iniciar sesión con Aurora ahora',
                  'Dejar un mensaje para la próxima sesión',
                  'Contactar con el médico responsable',
                  'Descargar informe del mes',
                  'Ajustar recordatorios y notificaciones',
                ].map(label => (
                  <button key={label} style={ss.actionBtn}>{label}</button>
                ))}
              </div>
            </div>

            {/* Care team */}
            <div style={ss.card}>
              <div style={ss.cardTitle}>Equipo de seguimiento</div>
              <div style={{ marginTop: 10 }}>
                {[
                  ['DV', 'Dr. Vega', 'Neurólogo · H. Virgen del Rocío', '#0d5b75'],
                  ['AU', 'Aurora', 'Asistente de conversación', '#0d7c80'],
                ].map(([init, name, role, color]) => (
                  <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid #f1f3f5' }}>
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: color, color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{init}</div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#1f2937' }}>{name}</div>
                      <div style={{ fontSize: 11, color: '#7a8694', marginTop: 1 }}>{role}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

// ─── Helpers ────────────────────────────────────────────────────
const Dot = ({ color }) => (
  <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block' }}/>
);

const MetaStat = ({ label, value, accent }) => (
  <div>
    <div style={{ fontSize: 11, color: '#7a8694', textTransform: 'uppercase', letterSpacing: '.05em', fontWeight: 600 }}>{label}</div>
    <div style={{ fontSize: 18, fontWeight: 700, color: accent, marginTop: 3, fontVariantNumeric: 'tabular-nums' }}>{value}</div>
  </div>
);

// ─── Styles (clinical palette — mirrors medico.jsx) ──────────────
const ss = {
  root: {
    position: 'absolute', inset: 0,
    background: '#f7f7f5', color: '#1f2937',
    fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
    fontSize: 13, display: 'flex', flexDirection: 'column', overflow: 'hidden',
  },

  topnav: {
    height: 56, background: '#fff', borderBottom: '1px solid #e5e7eb',
    display: 'flex', alignItems: 'center', padding: '0 24px', gap: 16, flexShrink: 0,
  },
  brand: { display: 'flex', alignItems: 'center', gap: 12 },
  brandMark: {
    width: 32, height: 32, borderRadius: 8, background: '#0d5b75',
    color: '#fff', fontSize: 17, fontWeight: 700,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  brandTitle: { fontSize: 14, fontWeight: 600, lineHeight: 1.2, color: '#1f2937' },
  brandSub: { fontSize: 11, color: '#7a8694' },
  statusPill: {
    display: 'flex', alignItems: 'center', gap: 7,
    padding: '5px 12px', borderRadius: 99, fontSize: 12, fontWeight: 600, border: '1px solid',
  },
  btnPrimary: {
    background: '#0d5b75', color: '#fff', border: 'none',
    padding: '8px 14px', borderRadius: 7, fontSize: 12, fontWeight: 600,
    cursor: 'pointer', fontFamily: 'inherit',
  },
  btnGhost: {
    background: '#fff', color: '#4a5568', border: '1px solid #d8dee5',
    padding: '7px 12px', borderRadius: 7, fontSize: 12, fontWeight: 500,
    cursor: 'pointer', fontFamily: 'inherit',
  },

  body: { flex: 1, overflowY: 'auto', padding: 18 },

  patientStrip: {
    background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10,
    padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 16, marginBottom: 14,
  },
  avatar: {
    width: 48, height: 48, borderRadius: 10,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 16, fontWeight: 600, flexShrink: 0,
  },
  patientName: { fontSize: 18, fontWeight: 600, color: '#1f2937' },
  patientMeta: { fontSize: 12, color: '#4a5568', marginTop: 3 },

  alertsRow: {
    display: 'flex', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8,
    marginBottom: 14, padding: '10px 14px',
    background: '#fff', border: '1px solid #f5d6a8', borderRadius: 8,
  },
  alertChip: {
    padding: '5px 10px', borderRadius: 6, fontSize: 12,
    border: '1px solid', fontWeight: 500,
  },

  card: { background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: 16 },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' },
  cardTitle: { fontSize: 14, fontWeight: 600, color: '#1f2937' },
  cardSub: { fontSize: 11, color: '#7a8694', marginTop: 2 },

  actionBtn: {
    width: '100%', padding: '9px 12px', textAlign: 'left',
    background: '#f7f7f5', border: '1px solid #e5e7eb', borderRadius: 7,
    fontSize: 12, color: '#374151', fontWeight: 500, cursor: 'pointer',
    fontFamily: 'inherit',
  },
};

window.SupervisionView = SupervisionView;

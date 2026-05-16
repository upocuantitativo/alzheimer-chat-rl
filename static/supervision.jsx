// Vista SUPERVISIÓN — para familiares y cuidadores.
// Indicadores en lenguaje llano, alertas traducidas, evolución visual
// y resumen de las últimas conversaciones.

const SupervisionView = () => {
  const patient = window.MOCK.patients[0]; // María Dolores — hija Lucía
  const evolutionRef  = React.useRef(null);
  const engagementRef = React.useRef(null);
  const [selectedSession, setSelectedSession] = React.useState(null);

  React.useEffect(() => {
    if (!window.Chart) return;
    Chart.defaults.font.family = '"IBM Plex Sans", system-ui, sans-serif';

    // Evolución cognitiva (MMSE → % bienestar)
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
            borderColor: '#c4632b',
            backgroundColor: 'rgba(196,99,43,.09)',
            borderWidth: 2.5, tension: .35,
            pointRadius: 4, pointBackgroundColor: '#c4632b', fill: true,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: ctx => `Bienestar: ${ctx.raw}%` } },
          },
          scales: {
            x: { grid: { color: '#f0ece4' }, ticks: { font: { size: 10 }, color: '#8a7a5a' } },
            y: { min: 0, max: 100, grid: { color: '#f0ece4' },
              ticks: { font: { size: 10 }, color: '#8a7a5a', callback: v => `${v}%` } },
          },
        },
      });
    }

    // Temas favoritos
    if (engagementRef.current) {
      if (engagementRef.current._chart) engagementRef.current._chart.destroy();
      const topics = [['Familia',.84],['Música',.78],['Comida',.71],['Refranes',.51],['Cine',.44]];
      engagementRef.current._chart = new Chart(engagementRef.current.getContext('2d'), {
        type: 'bar',
        data: {
          labels: topics.map(([t]) => t),
          datasets: [{
            data: topics.map(([,v]) => Math.round(v * 100)),
            backgroundColor: 'rgba(196,99,43,.5)',
            borderColor: '#c4632b', borderWidth: 1, borderRadius: 5,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { font: { size: 11 }, color: '#8a7a5a' } },
            y: { min: 0, max: 100, grid: { color: '#f0ece4' },
              ticks: { font: { size: 10 }, color: '#8a7a5a', callback: v => `${v}%` } },
          },
        },
      });
    }
  }, []);

  // Alarmas traducidas a lenguaje llano
  const alarmMap = {
    'Pico de ansiedad en 3 últimas sesiones':
      { msg: 'Se ha notado algo nerviosa en las últimas sesiones', sev: 'media', icon: '⚠️' },
    'Anomia creciente en denominación':
      { msg: 'Le está costando más encontrar algunas palabras', sev: 'media', icon: '💬' },
    'Caída MMSE −3 en 4 sem.':
      { msg: 'Ha habido cambios notables en su memoria reciente', sev: 'alta', icon: '📉' },
    '3 silencios consecutivos · 2 sesiones':
      { msg: 'Tuvo momentos de silencio largo en las últimas sesiones', sev: 'media', icon: '🔇' },
    'Fatiga crítica recurrente':
      { msg: 'Se ha cansado mucho antes de terminar algunas sesiones', sev: 'alta', icon: '😔' },
    'Latencia media >9 s · subiendo':
      { msg: 'Le lleva algo más de tiempo responder a las preguntas', sev: 'media', icon: '⏱️' },
    'Engagement bajo en trivia cultural':
      { msg: 'Últimamente participa menos en preguntas de cultura', sev: 'baja', icon: '📚' },
  };

  const activeAlarms = patient.flags.map(f =>
    alarmMap[f] || { msg: f, sev: 'media', icon: '⚠️' }
  );

  const status = patient.urgency === 'critica'
    ? { label: 'Necesita atención', color: '#dc2626', bg: '#fff0f0', emoji: '🔴' }
    : patient.urgency === 'alta'
    ? { label: 'Pendiente de revisión', color: '#d97706', bg: '#fffbeb', emoji: '🟡' }
    : patient.urgency === 'media'
    ? { label: 'Estable con seguimiento', color: '#b45309', bg: '#fffbeb', emoji: '🟡' }
    : { label: 'Todo va bien', color: '#059669', bg: '#f0fdf4', emoji: '🟢' };

  const bienestar = Math.round((patient.mmse / 30) * 100);
  const tendencia = patient.mmseDelta < 0 ? '↘ Ligero descenso'
    : patient.mmseDelta > 0 ? '↗ Mejorando' : '→ Estable';
  const tendenciaColor = patient.mmseDelta < 0 ? '#d97706'
    : patient.mmseDelta > 0 ? '#059669' : '#6b5c45';

  const sessions = [
    { date: 'Hoy, 11:24', duration: '11 min', mood: '😊', moodLabel: 'Animada',
      summary: 'Estuvo muy participativa. Habló de su madre, cantó un refrán y recordó bien dónde vive.',
      topics: ['Familia', 'Refranes'], ok: true },
    { date: 'Ayer, 10:08', duration: '14 min', mood: '😐', moodLabel: 'Tranquila',
      summary: 'Hubo un momento de silencio largo, pero luego se animó con una canción de Manolo Escobar.',
      topics: ['Música'], ok: true },
    { date: 'Hace 2 días', duration: '8 min', mood: '😟', moodLabel: 'Algo nerviosa',
      summary: 'Le costó recordar algunas palabras y se puso un poco nerviosa. Aurora la tranquilizó con música.',
      topics: ['Música', 'Palabras'], ok: false },
  ];

  const weekDays = [
    { day: 'L', date: '12', ok: true, had: true },
    { day: 'M', date: '13', ok: true, had: true },
    { day: 'X', date: '14', ok: null, had: false },
    { day: 'J', date: '15', ok: false, had: true },
    { day: 'V', date: '16', ok: true, had: true },
    { day: 'S', date: '17', ok: null, had: false },
    { day: 'D', date: '18', ok: true, had: true },
  ];

  return (
    <div style={ss.root}>
      {/* ── Header ── */}
      <div style={ss.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={ss.avatar}>MD</div>
          <div>
            <div style={ss.headerName}>{patient.name}</div>
            <div style={ss.headerSub}>
              Tu madre · {patient.age} años · {patient.city} ·
              <span style={{ marginLeft: 8 }}>Última sesión: <b>{patient.lastSession}</b></span>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <div style={{ ...ss.statusChip, background: status.bg, color: status.color, borderColor: status.color + '44' }}>
            {status.emoji} {status.label}
          </div>
          <button style={ss.btnSecondary}>📋 Historial</button>
          <button style={ss.btnPrimary}>📞 Llamar a Aurora</button>
        </div>
      </div>

      <div style={ss.body}>
        {/* ── KPI row ── */}
        <div style={ss.kpiRow}>
          <KpiCard icon="🧠" value={`${bienestar}%`}
            label="Bienestar cognitivo"
            sub={<span style={{ color: tendenciaColor }}>{tendencia}</span>}
            accent="#c4632b"/>
          <KpiCard icon="🗓️" value={patient.sessionsThisMonth}
            label="Sesiones este mes"
            sub={<span style={{ color: '#059669' }}>✓ objetivo cumplido</span>}
            accent="#059669"/>
          <KpiCard icon="💬" value="Hoy, 11:24"
            label="Última conversación"
            sub="11 minutos · fue bien"
            accent="#0d5b75"/>
          <KpiCard icon="😊" value="Tranquila"
            label="Ánimo en la sesión"
            sub="Habló de su familia"
            accent="#d97706"/>
        </div>

        {/* ── Alerts ── */}
        {activeAlarms.length > 0 && (
          <div style={ss.alertsBox}>
            <div style={ss.alertsTitle}>Cosas que deberías saber</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
              {activeAlarms.map((a, i) => (
                <div key={i} style={{
                  ...ss.alertPill,
                  borderLeftColor: a.sev === 'alta' ? '#dc2626' : a.sev === 'media' ? '#d97706' : '#b45309',
                  background: a.sev === 'alta' ? '#fff0f0' : '#fffbeb',
                }}>
                  <span style={{ fontSize: 16 }}>{a.icon}</span>
                  <span style={{ fontSize: 12, color: '#2a2419', lineHeight: 1.4 }}>{a.msg}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Main grid ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 16 }}>

          {/* Left column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Week calendar */}
            <div style={ss.card}>
              <div style={ss.cardTitle}>Esta semana</div>
              <div style={{ fontSize: 12, color: '#8a7a5a', marginBottom: 12 }}>Cómo han ido las sesiones día a día</div>
              <div style={{ display: 'flex', gap: 8 }}>
                {weekDays.map((d, i) => (
                  <div key={i} style={{ flex: 1, textAlign: 'center' }}>
                    <div style={{ fontSize: 10, color: '#8a7a5a', marginBottom: 4 }}>{d.day}</div>
                    <div style={{
                      height: 40, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 16,
                      background: !d.had ? '#f5f0e8'
                        : d.ok === true ? '#d1fae5'
                        : d.ok === false ? '#fff0f0' : '#fef9ec',
                      border: `1px solid ${!d.had ? '#e8dfc8' : d.ok === true ? '#a7f3d0' : d.ok === false ? '#fca5a5' : '#fde68a'}`,
                    }}>
                      {!d.had ? '—' : d.ok === true ? '😊' : d.ok === false ? '😟' : '😐'}
                    </div>
                    <div style={{ fontSize: 9, color: '#8a7a5a', marginTop: 3 }}>{d.date}</div>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 11, color: '#8a7a5a' }}>
                <span style={{ display:'flex', alignItems:'center', gap: 4 }}><span style={{ width:10, height:10, borderRadius:3, background:'#d1fae5', border:'1px solid #a7f3d0', display:'inline-block' }}/> Sesión buena</span>
                <span style={{ display:'flex', alignItems:'center', gap: 4 }}><span style={{ width:10, height:10, borderRadius:3, background:'#fff0f0', border:'1px solid #fca5a5', display:'inline-block' }}/> Con incidencias</span>
                <span style={{ display:'flex', alignItems:'center', gap: 4 }}><span style={{ width:10, height:10, borderRadius:3, background:'#f5f0e8', border:'1px solid #e8dfc8', display:'inline-block' }}/> Sin sesión</span>
              </div>
            </div>

            {/* Evolution chart */}
            <div style={ss.card}>
              <div style={ss.cardTitle}>Evolución del bienestar cognitivo</div>
              <div style={{ fontSize: 12, color: '#8a7a5a', marginBottom: 12 }}>
                Cómo ha ido respondiendo en las últimas 10 semanas
              </div>
              <div style={{ height: 160 }}><canvas ref={evolutionRef}/></div>
              <div style={{ display: 'flex', gap: 24, marginTop: 12, paddingTop: 12, borderTop: '1px solid #f0ece4' }}>
                <div>
                  <div style={{ fontSize: 11, color: '#8a7a5a' }}>Nivel actual</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: '#c4632b', fontVariantNumeric: 'tabular-nums' }}>{bienestar}%</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: '#8a7a5a' }}>Tendencia</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: tendenciaColor, marginTop: 4 }}>{tendencia}</div>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: '#8a7a5a' }}>Qué hacer</div>
                  <div style={{ fontSize: 12, color: '#6b5c45', marginTop: 4, lineHeight: 1.5 }}>
                    {patient.mmseDelta < 0
                      ? 'Coméntaselo al médico en la próxima visita.'
                      : 'Sigue así, las sesiones están ayudando.'}
                  </div>
                </div>
              </div>
            </div>

            {/* Favorite topics */}
            <div style={ss.card}>
              <div style={ss.cardTitle}>Temas que más le gustan</div>
              <div style={{ fontSize: 12, color: '#8a7a5a', marginBottom: 12 }}>
                Qué temas la hacen participar más y con mejor ánimo
              </div>
              <div style={{ height: 130 }}><canvas ref={engagementRef}/></div>
              <div style={{ marginTop: 10, padding: '10px 12px', background: '#fdf8f1', borderRadius: 8, border: '1px solid #f0e8d8', fontSize: 12, color: '#6b5c45', lineHeight: 1.6 }}>
                💡 <b>Consejo:</b> si la llamas, empieza preguntando por la familia o ponle una canción — eso la anima enseguida.
              </div>
            </div>
          </div>

          {/* Right column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Last sessions */}
            <div style={ss.card}>
              <div style={ss.cardTitle}>Últimas conversaciones</div>
              <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
                {sessions.map((s, i) => (
                  <div key={i}
                    onClick={() => setSelectedSession(selectedSession === i ? null : i)}
                    style={{
                      padding: '10px 12px', borderRadius: 8, cursor: 'pointer',
                      borderTop: '1px solid #f0ece4', borderRight: '1px solid #f0ece4',
                      borderBottom: '1px solid #f0ece4',
                      borderLeft: `3px solid ${s.ok ? '#059669' : '#d97706'}`,
                      background: selectedSession === i ? '#fdf8f1' : '#fafaf8',
                      transition: 'background .15s',
                    }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: '#2a2419' }}>{s.date}</div>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                        <span style={{ fontSize: 15 }}>{s.mood}</span>
                        <span style={{ fontSize: 11, color: '#8a7a5a', fontWeight: 500 }}>{s.moodLabel}</span>
                        <span style={{ fontSize: 11, color: '#b0a090' }}>· {s.duration}</span>
                      </div>
                    </div>
                    <div style={{ fontSize: 12, color: '#5a4a36', lineHeight: 1.5 }}>{s.summary}</div>
                    {selectedSession === i && (
                      <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {s.topics.map(t => (
                          <span key={t} style={{ fontSize: 10, padding: '2px 8px', borderRadius: 99, background: '#f0e8d8', color: '#8a5a2a', fontWeight: 500 }}>{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Quick actions */}
            <div style={ss.card}>
              <div style={ss.cardTitle}>Acciones rápidas</div>
              <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  ['📞', 'Iniciar sesión con Aurora ahora'],
                  ['💌', 'Dejar un mensaje para la próxima sesión'],
                  ['👨‍⚕️', 'Contactar con el médico responsable'],
                  ['📊', 'Descargar informe del mes'],
                  ['⚙️',  'Ajustar recordatorios y notificaciones'],
                ].map(([icon, label]) => (
                  <button key={label} style={ss.actionBtn}>
                    <span style={{ fontSize: 16 }}>{icon}</span>
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Caregiver contact */}
            <div style={{ ...ss.card, background: '#eef7f5', border: '1px solid #a7dcd4' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#0d6e72', marginBottom: 8 }}>
                Equipo de seguimiento
              </div>
              {[
                ['🩺', 'Dr. Vega', 'Neurólogo · H. Virgen del Rocío'],
                ['🤝', 'Aurora', 'Asistente de conversación'],
              ].map(([icon, name, role]) => (
                <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid #cce6e0' }}>
                  <span style={{ fontSize: 20 }}>{icon}</span>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#1f2937' }}>{name}</div>
                    <div style={{ fontSize: 11, color: '#4a7c78' }}>{role}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── Sub-components ─────────────────────────────────────────────
const KpiCard = ({ icon, value, label, sub, accent }) => (
  <div style={{ ...ss.kpiCard, borderTop: `3px solid ${accent}` }}>
    <div style={{ fontSize: 26, marginBottom: 6 }}>{icon}</div>
    <div style={{ fontSize: 22, fontWeight: 700, color: '#2a2419', fontVariantNumeric: 'tabular-nums', lineHeight: 1.1 }}>{value}</div>
    <div style={{ fontSize: 11, color: '#8a7a5a', marginTop: 4, textTransform: 'uppercase', letterSpacing: '.05em', fontWeight: 600 }}>{label}</div>
    {sub && <div style={{ fontSize: 11, color: '#6b5c45', marginTop: 5 }}>{sub}</div>}
  </div>
);

// ─── Styles ─────────────────────────────────────────────────────
const ss = {
  root: {
    position: 'absolute', inset: 0, background: '#f8f5ef', color: '#2a2419',
    fontFamily: '"IBM Plex Sans", system-ui, sans-serif', fontSize: 13,
    display: 'flex', flexDirection: 'column', overflow: 'hidden',
  },
  header: {
    background: '#fff', borderBottom: '1px solid #e8dfc8',
    padding: '14px 24px', display: 'flex', justifyContent: 'space-between',
    alignItems: 'center', flexShrink: 0,
  },
  avatar: {
    width: 46, height: 46, borderRadius: '50%',
    background: 'linear-gradient(135deg, #c4632b, #a04a1c)',
    color: '#fff', fontSize: 15, fontWeight: 700,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  headerName: { fontSize: 17, fontWeight: 600, color: '#2a2419' },
  headerSub: { fontSize: 12, color: '#8a7a5a', marginTop: 2 },
  statusChip: {
    padding: '6px 14px', borderRadius: 99, fontSize: 12, fontWeight: 600,
    border: '1px solid',
  },
  btnPrimary: {
    background: '#c4632b', color: '#fff', border: 'none',
    padding: '9px 16px', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit',
  },
  btnSecondary: {
    background: '#fff', color: '#5a4a36', border: '1px solid #d8c9b1',
    padding: '9px 16px', borderRadius: 8, fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit',
  },
  body: { flex: 1, overflowY: 'auto', padding: 18 },
  kpiRow: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 16 },
  kpiCard: {
    background: '#fff', border: '1px solid #e8dfc8', borderRadius: 12,
    padding: '16px 14px', textAlign: 'center',
  },
  alertsBox: {
    background: '#fff', border: '1px solid #f0d090', borderRadius: 12,
    padding: '14px 18px', marginBottom: 16,
  },
  alertsTitle: { fontSize: 13, fontWeight: 600, color: '#8a5a00' },
  alertPill: {
    display: 'flex', alignItems: 'flex-start', gap: 10,
    padding: '9px 12px', borderRadius: 8, borderLeft: '3px solid',
    flex: '1 1 300px',
  },
  card: { background: '#fff', border: '1px solid #e8dfc8', borderRadius: 12, padding: 16 },
  cardTitle: { fontSize: 14, fontWeight: 600, color: '#2a2419', marginBottom: 0 },
  actionBtn: {
    width: '100%', padding: '10px 14px', textAlign: 'left',
    background: '#faf7f2', border: '1px solid #e8dfc8', borderRadius: 8,
    fontSize: 12, color: '#5a4a36', fontWeight: 500, cursor: 'pointer',
    fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 10,
  },
};

window.SupervisionView = SupervisionView;

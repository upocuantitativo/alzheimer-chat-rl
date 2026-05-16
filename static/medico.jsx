// Vista MÉDICO — clínica, sobria, longitudinal.
// Lista pacientes con triage + detalle paciente + transcripción revisable +
// evolución MMSE + notas clínicas + alertas configurables.
// 1440x900.

const MedicoView = () => {
  const patients = window.MOCK.patients;
  const [selectedId, setSelectedId] = React.useState('p002');
  const [tab, setTab] = React.useState('evolucion');
  const [showAlerts, setShowAlerts] = React.useState(false);
  const [thresholds, setThresholds] = React.useState({
    mmseDrop: 2, anxiety: 70, silenceStreak: 3, latency: 12,
  });
  const [noteDraft, setNoteDraft] = React.useState('');
  const [notes, setNotes] = React.useState([
    { date: '14 may', author: 'Dr. Vega', text: 'Cambio de pauta: introducir música pre-test para reducir ansiedad. Revisar en 2 semanas.' },
    { date: '07 may', author: 'Dr. Vega', text: 'Caída MMSE −2 confirmada. Solicitar valoración neurológica complementaria.' },
  ]);

  const p = patients.find(x => x.id === selectedId);
  const mmseRef = React.useRef(null);
  const sparkRefs = React.useRef({});

  // Draw MMSE longitudinal chart on patient change
  React.useEffect(() => {
    if (!p || !mmseRef.current || !window.Chart) return;
    const ctx = mmseRef.current.getContext('2d');
    if (mmseRef.current._chart) mmseRef.current._chart.destroy();
    const labels = ['Feb','Mar','','Abr','','May','','Jun','','Jul'].slice(0, p.mmseSeries.length);
    mmseRef.current._chart = new window.Chart(ctx, {
      type: 'line',
      data: {
        labels: p.mmseSeries.map((_, i) => `S${i+1}`),
        datasets: [
          { label: 'MMSE', data: p.mmseSeries, borderColor: '#0d5b75',
            backgroundColor: 'rgba(13,91,117,.08)', borderWidth: 2,
            tension: .3, pointRadius: 3, pointBackgroundColor: '#0d5b75', fill: true, yAxisID: 'y' },
          { label: 'Ansiedad', data: p.anxietySeries.map(v => v*30), borderColor: '#c0362c',
            borderWidth: 1.5, tension: .3, pointRadius: 2, borderDash: [4,4], fill: false, yAxisID: 'y' },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { font: { size: 11, family: '"IBM Plex Sans"' }, color: '#4a5568', boxWidth: 12 } },
          tooltip: { backgroundColor: '#1a2030', titleFont: { size: 11 }, bodyFont: { size: 11 } },
        },
        scales: {
          x: { grid: { color: '#eef0f3' }, ticks: { font: { size: 10, family: '"IBM Plex Sans"' }, color: '#7a8694' } },
          y: { min: 0, max: 30, grid: { color: '#eef0f3' }, ticks: { font: { size: 10 }, color: '#7a8694', stepSize: 5 } },
        },
      },
    });
  }, [selectedId]);

  // Draw mini sparklines for each patient row
  React.useEffect(() => {
    patients.forEach(pat => {
      const c = sparkRefs.current[pat.id];
      if (!c || !window.Chart) return;
      if (c._chart) c._chart.destroy();
      c._chart = new window.Chart(c.getContext('2d'), {
        type: 'line',
        data: { labels: pat.mmseSeries.map(()=>''), datasets: [{
          data: pat.mmseSeries,
          borderColor: pat.urgency === 'critica' ? '#c0362c' : pat.urgency === 'alta' ? '#d97706'
            : pat.urgency === 'media' ? '#8a6500' : '#0d7c80',
          borderWidth: 1.5, pointRadius: 0, tension: .35, fill: false,
        }] },
        options: { responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: { x: { display: false }, y: { display: false, min: 0, max: 30 } } },
      });
    });
  }, []);

  const urgencyColor = (u) => ({
    critica: { bg: '#fef2f1', fg: '#c0362c', dot: '#c0362c', label: 'CRÍTICA' },
    alta:    { bg: '#fef6ec', fg: '#b45309', dot: '#d97706', label: 'ALTA' },
    media:   { bg: '#fffbed', fg: '#7c5800', dot: '#a87d00', label: 'MEDIA' },
    estable: { bg: '#eef7f5', fg: '#0d6e72', dot: '#0d7c80', label: 'ESTABLE' },
  }[u]);

  const sortedPatients = [...patients].sort((a,b) => {
    const order = { critica: 0, alta: 1, media: 2, estable: 3 };
    return order[a.urgency] - order[b.urgency];
  });

  return (
    <div style={medicoStyles.root}>
      {/* ── Top nav ── */}
      <div style={medicoStyles.topnav}>
        <div style={medicoStyles.brand}>
          <div style={medicoStyles.brandMark}>+</div>
          <div>
            <div style={medicoStyles.brandTitle}>Alzheimer Chat-RL</div>
            <div style={medicoStyles.brandSub}>Panel clínico · Dr. Vega · Neurología</div>
          </div>
        </div>
        <div style={medicoStyles.navTabs}>
          <span style={{ ...medicoStyles.navTab, ...medicoStyles.navTabActive }}>Pacientes</span>
          <span style={medicoStyles.navTab}>Cohortes</span>
          <span style={medicoStyles.navTab}>Informes</span>
          <span style={medicoStyles.navTab}>Configuración</span>
        </div>
        <div style={medicoStyles.navRight}>
          <button style={medicoStyles.iconBtnGhost} onClick={() => setShowAlerts(true)} title="Umbrales de alerta">
            <SvgBell/>
            <span style={medicoStyles.bellDot}/>
          </button>
          <div style={medicoStyles.userChip}>DV</div>
        </div>
      </div>

      <div style={medicoStyles.body}>
        {/* ── Left rail: patient triage list ── */}
        <div style={medicoStyles.patientsRail}>
          <div style={medicoStyles.railHeader}>
            <div>
              <div style={medicoStyles.railTitle}>Pacientes</div>
              <div style={medicoStyles.railCount}>{patients.length} activos · ordenados por urgencia</div>
            </div>
            <button style={medicoStyles.smallBtn}>＋</button>
          </div>

          <div style={medicoStyles.searchWrap}>
            <SvgSearch/>
            <input style={medicoStyles.search} placeholder="Buscar por nombre o ciudad…"/>
          </div>

          <div style={medicoStyles.triageBar}>
            {['critica','alta','media','estable'].map(u => {
              const c = urgencyColor(u);
              const n = patients.filter(p => p.urgency === u).length;
              return (
                <div key={u} style={{ flex: 1, padding: '8px 6px', textAlign: 'center', background: c.bg }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: c.fg, fontVariantNumeric: 'tabular-nums' }}>{n}</div>
                  <div style={{ fontSize: 9, color: c.fg, letterSpacing: '.08em', fontWeight: 600 }}>{c.label}</div>
                </div>
              );
            })}
          </div>

          <div style={medicoStyles.patientList}>
            {sortedPatients.map(pat => {
              const c = urgencyColor(pat.urgency);
              const active = pat.id === selectedId;
              return (
                <div key={pat.id}
                  style={{ ...medicoStyles.patientRow,
                    ...(active ? medicoStyles.patientRowActive : {}),
                    borderLeftColor: c.dot,
                  }}
                  onClick={() => setSelectedId(pat.id)}>
                  <div style={medicoStyles.patientRowTop}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={medicoStyles.patientName}>{pat.name}</div>
                      <div style={medicoStyles.patientMeta}>
                        {pat.age} a · {pat.city} · {pat.stageLabel}
                      </div>
                    </div>
                    {pat.alarms > 0 && (
                      <div style={{ ...medicoStyles.alarmBadge, background: c.bg, color: c.fg }}>
                        {pat.alarms}
                      </div>
                    )}
                  </div>
                  <div style={medicoStyles.patientRowBot}>
                    <div style={medicoStyles.patientMmse}>
                      <span style={{ fontSize: 11, color:'#7a8694' }}>MMSE</span>
                      <span style={{ fontSize: 16, fontWeight: 700, color:'#1f2937', marginLeft: 4, fontVariantNumeric:'tabular-nums' }}>
                        {pat.mmse}
                      </span>
                      {pat.mmseDelta !== 0 && (
                        <span style={{ marginLeft: 6, fontSize: 11, fontWeight: 600,
                          color: pat.mmseDelta < 0 ? '#c0362c' : '#0d7c80' }}>
                          {pat.mmseDelta > 0 ? '+' : ''}{pat.mmseDelta}
                        </span>
                      )}
                    </div>
                    <div style={{ width: 80, height: 24 }}>
                      <canvas ref={el => sparkRefs.current[pat.id] = el}/>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Main detail ── */}
        <div style={medicoStyles.detail}>
          {/* Patient header */}
          <div style={medicoStyles.detailHeader}>
            <div style={{ display:'flex', alignItems:'center', gap: 18 }}>
              <div style={{ ...medicoStyles.patientAvatar,
                background: urgencyColor(p.urgency).bg,
                color: urgencyColor(p.urgency).fg }}>
                {p.name.split(' ').map(s=>s[0]).slice(0,2).join('')}
              </div>
              <div>
                <div style={medicoStyles.detailName}>{p.name}</div>
                <div style={medicoStyles.detailMeta}>
                  {p.age} años · {p.city} ·
                  <span style={{ ...medicoStyles.stagePill, marginLeft: 10,
                    background: urgencyColor(p.urgency).bg, color: urgencyColor(p.urgency).fg }}>
                    {p.stageLabel}
                  </span>
                  <span style={{ marginLeft: 14, color:'#7a8694' }}>· Cuidador: {p.caregiver}</span>
                </div>
              </div>
            </div>
            <div style={{ display:'flex', gap: 8 }}>
              <button style={medicoStyles.btnGhost}>
                <SvgDownload/> Exportar PDF
              </button>
              <button style={medicoStyles.btnPrimary}>Iniciar nueva sesión</button>
            </div>
          </div>

          {/* Flags row */}
          {p.flags.length > 0 && (
            <div style={medicoStyles.flagsRow}>
              {p.flags.map((f, i) => (
                <div key={i} style={{ ...medicoStyles.flagPill,
                  background: p.urgency === 'estable' ? '#eef7f5' : '#fef6ec',
                  color: p.urgency === 'estable' ? '#0d6e72' : '#b45309',
                  borderColor: p.urgency === 'estable' ? '#cce6e0' : '#f5d6a8',
                }}>
                  <SvgFlag/> {f}
                </div>
              ))}
            </div>
          )}

          {/* KPI grid */}
          <div style={medicoStyles.kpiGrid}>
            <Kpi label="MMSE actual" value={p.mmse} sub={`Línea base 28 · ${p.mmseDelta < 0 ? '↓' : '→'} ${Math.abs(p.mmseDelta)} en 4 sem.`} accent={p.mmseDelta < -1 ? '#c0362c' : '#0d5b75'}/>
            <Kpi label="Alarmas activas" value={p.alarms} sub={p.alarms === 0 ? 'ninguna en 7 días' : 'requieren revisión'} accent={p.alarms > 2 ? '#c0362c' : p.alarms > 0 ? '#d97706' : '#0d7c80'}/>
            <Kpi label="Sesiones (mes)" value={p.sessionsThisMonth} sub="objetivo: 12+" accent="#0d5b75"/>
            <Kpi label="Latencia media" value="6.4s" sub="dentro de norma para estadio" accent="#0d5b75"/>
            <Kpi label="Última sesión" value={p.lastSession.split(' · ')[0]} sub={p.lastSession.split(' · ')[1] || ''} accent="#0d5b75"/>
          </div>

          {/* Tabs */}
          <div style={medicoStyles.tabs}>
            {[
              ['evolucion', 'Evolución longitudinal'],
              ['transcripcion', 'Transcripción · 9 turnos'],
              ['notas', `Notas clínicas (${notes.length})`],
              ['sesiones', 'Historial de sesiones'],
            ].map(([k, l]) => (
              <button key={k} style={{ ...medicoStyles.tab,
                ...(tab === k ? medicoStyles.tabActive : {}) }}
                onClick={() => setTab(k)}>{l}</button>
            ))}
          </div>

          {/* Tab content */}
          <div style={medicoStyles.tabContent}>
            {tab === 'evolucion' && (
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
                <div style={medicoStyles.card}>
                  <div style={medicoStyles.cardHeader}>
                    <div>
                      <div style={medicoStyles.cardTitle}>MMSE longitudinal · 10 sesiones</div>
                      <div style={medicoStyles.cardSub}>Línea continua: MMSE · línea punteada: ansiedad media de sesión (escalada)</div>
                    </div>
                    <div style={{ display:'flex', gap: 4 }}>
                      <button style={medicoStyles.segBtn}>3m</button>
                      <button style={{ ...medicoStyles.segBtn, ...medicoStyles.segBtnActive }}>6m</button>
                      <button style={medicoStyles.segBtn}>12m</button>
                    </div>
                  </div>
                  <div style={{ height: 240 }}>
                    <canvas ref={mmseRef}/>
                  </div>
                </div>

                <div style={medicoStyles.card}>
                  <div style={medicoStyles.cardTitle}>Dominios cognitivos</div>
                  <div style={medicoStyles.cardSub}>Tasa de éxito últimos 30 días</div>
                  <div style={{ marginTop: 14 }}>
                    {[
                      ['Memoria episódica', 0.42, '−18%'],
                      ['Memoria semántica', 0.71, '−4%'],
                      ['Lenguaje · denominación', 0.55, '−12%'],
                      ['Orientación', 0.88, '+2%'],
                      ['Atención', 0.64, '−6%'],
                    ].map(([dom, val, delta]) => (
                      <div key={dom} style={{ marginBottom: 12 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                          <span style={{ color: '#374151' }}>{dom}</span>
                          <span style={{ fontVariantNumeric: 'tabular-nums', color:'#1f2937', fontWeight: 600 }}>
                            {Math.round(val*100)}%
                            <span style={{ marginLeft: 6, fontWeight: 500,
                              color: delta.startsWith('+') ? '#0d7c80' : '#c0362c' }}>{delta}</span>
                          </span>
                        </div>
                        <div style={{ height: 6, background: '#eef0f3', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${val*100}%`, height: '100%',
                            background: val > 0.6 ? '#0d7c80' : val > 0.4 ? '#a87d00' : '#c0362c',
                            borderRadius: 3 }}/>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {tab === 'transcripcion' && (
              <div style={medicoStyles.card}>
                <div style={medicoStyles.cardHeader}>
                  <div>
                    <div style={medicoStyles.cardTitle}>Sesión actual · 14 may 11:24 → 11:35</div>
                    <div style={medicoStyles.cardSub}>Filas marcadas en ámbar requieren revisión · 3 turnos con incidencia</div>
                  </div>
                  <button style={medicoStyles.btnGhost}><SvgDownload/> Exportar</button>
                </div>
                <table style={medicoStyles.table}>
                  <thead>
                    <tr>
                      <th style={medicoStyles.th}>#</th>
                      <th style={medicoStyles.th}>Hora</th>
                      <th style={medicoStyles.th}>Acción</th>
                      <th style={medicoStyles.th}>Agente</th>
                      <th style={medicoStyles.th}>Paciente</th>
                      <th style={medicoStyles.th}>Lat.</th>
                      <th style={medicoStyles.th}>Test</th>
                    </tr>
                  </thead>
                  <tbody>
                    {window.MOCK.transcript.map(t => (
                      <tr key={t.turn}
                        style={t.flag ? medicoStyles.trFlag : {}}>
                        <td style={medicoStyles.td}>{t.turn}</td>
                        <td style={{ ...medicoStyles.td, fontFamily: 'IBM Plex Mono, monospace', color:'#7a8694' }}>{t.time}</td>
                        <td style={medicoStyles.td}>
                          <span style={medicoStyles.actionTag}>{t.action}</span>
                        </td>
                        <td style={{ ...medicoStyles.td, color:'#374151' }}>{t.agent}</td>
                        <td style={{ ...medicoStyles.td, color:'#1f2937' }}>
                          {t.patient}
                          {t.flag === 'silencio' && <span style={medicoStyles.flagInline}>· silencio</span>}
                          {t.flag === 'anomia' && <span style={medicoStyles.flagInline}>· anomia</span>}
                          {t.flag === 'engagement+' && <span style={{ ...medicoStyles.flagInline, color:'#0d7c80' }}>· engagement+</span>}
                        </td>
                        <td style={{ ...medicoStyles.td, fontVariantNumeric: 'tabular-nums',
                          color: t.lat > 10 ? '#c0362c' : t.lat > 6 ? '#b45309' : '#0d7c80', fontWeight: 600 }}>
                          {t.lat.toFixed(1)}s
                        </td>
                        <td style={medicoStyles.td}>
                          {t.testOk === true && <span style={{ color:'#0d7c80' }}>✓ {t.test}</span>}
                          {t.testOk === false && <span style={{ color:'#c0362c' }}>✗ {t.test}</span>}
                          {t.testOk === null || t.testOk === undefined ? <span style={{ color:'#cdd3da' }}>—</span> : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {tab === 'notas' && (
              <div style={{ display:'grid', gridTemplateColumns: '1.4fr 1fr', gap: 16 }}>
                <div style={medicoStyles.card}>
                  <div style={medicoStyles.cardTitle}>Historial de observaciones</div>
                  <div style={{ marginTop: 14 }}>
                    {notes.map((n, i) => (
                      <div key={i} style={medicoStyles.noteCard}>
                        <div style={medicoStyles.noteHeader}>
                          <span style={medicoStyles.noteAuthor}>{n.author}</span>
                          <span style={medicoStyles.noteDate}>{n.date}</span>
                        </div>
                        <div style={medicoStyles.noteText}>{n.text}</div>
                      </div>
                    ))}
                  </div>
                </div>
                <div style={medicoStyles.card}>
                  <div style={medicoStyles.cardTitle}>Añadir nota</div>
                  <textarea style={medicoStyles.textarea} rows={6}
                    placeholder="Observaciones clínicas, pauta a aplicar, derivaciones…"
                    value={noteDraft} onChange={e => setNoteDraft(e.target.value)}/>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop: 10 }}>
                    <div style={{ fontSize: 11, color:'#7a8694' }}>Se asocia a la sesión actual y al historial del paciente.</div>
                    <button style={medicoStyles.btnPrimary} onClick={() => {
                      if (!noteDraft.trim()) return;
                      setNotes([{ date: 'hoy', author: 'Dr. Vega', text: noteDraft }, ...notes]);
                      setNoteDraft('');
                    }}>Guardar nota</button>
                  </div>
                </div>
              </div>
            )}

            {tab === 'sesiones' && (
              <div style={medicoStyles.card}>
                <table style={medicoStyles.table}>
                  <thead>
                    <tr>
                      <th style={medicoStyles.th}>Fecha</th>
                      <th style={medicoStyles.th}>Duración</th>
                      <th style={medicoStyles.th}>Turnos</th>
                      <th style={medicoStyles.th}>MMSE</th>
                      <th style={medicoStyles.th}>Alarmas</th>
                      <th style={medicoStyles.th}>Engagement</th>
                      <th style={medicoStyles.th}>Notas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ['14 may · 11:24', '11 min', 9, 22, 0, 'Alto', '—'],
                      ['12 may · 10:08', '14 min', 12, 22, 1, 'Medio', '✓'],
                      ['09 may · 16:42', '8 min', 7, 23, 2, 'Bajo', '✓'],
                      ['07 may · 11:30', '13 min', 11, 23, 1, 'Medio', '—'],
                      ['05 may · 10:11', '12 min', 10, 23, 0, 'Alto', '—'],
                      ['02 may · 17:05', '9 min', 8, 24, 2, 'Bajo', '✓'],
                      ['28 abr · 11:20', '15 min', 14, 25, 0, 'Alto', '—'],
                    ].map((row, i) => (
                      <tr key={i}>
                        {row.map((cell, j) => (
                          <td key={j} style={{ ...medicoStyles.td,
                            fontVariantNumeric: typeof cell === 'number' ? 'tabular-nums' : 'normal',
                            color: j === 4 && cell > 0 ? '#c0362c' : '#1f2937', fontWeight: j === 4 && cell > 0 ? 600 : 400 }}>
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Alert thresholds modal */}
      {showAlerts && (
        <>
          <div style={medicoStyles.overlay} onClick={() => setShowAlerts(false)}/>
          <div style={medicoStyles.modal}>
            <div style={medicoStyles.modalHeader}>
              <div>
                <div style={medicoStyles.modalTitle}>Umbrales de alerta personalizables</div>
                <div style={medicoStyles.cardSub}>Disparan alarmas en el panel y notifican al cuidador asignado.</div>
              </div>
              <button style={medicoStyles.modalClose} onClick={() => setShowAlerts(false)}>×</button>
            </div>
            <div style={{ display:'grid', gridTemplateColumns: '1fr 1fr', gap: 18, marginTop: 18 }}>
              <ThresholdField label="Caída MMSE en 4 sesiones" unit="puntos"
                value={thresholds.mmseDrop} min={1} max={8}
                onChange={v => setThresholds({...thresholds, mmseDrop: v})}/>
              <ThresholdField label="Ansiedad sostenida" unit="%"
                value={thresholds.anxiety} min={40} max={95}
                onChange={v => setThresholds({...thresholds, anxiety: v})}/>
              <ThresholdField label="Racha de silencio" unit="turnos seguidos"
                value={thresholds.silenceStreak} min={1} max={8}
                onChange={v => setThresholds({...thresholds, silenceStreak: v})}/>
              <ThresholdField label="Latencia media de sesión" unit="segundos"
                value={thresholds.latency} min={5} max={25}
                onChange={v => setThresholds({...thresholds, latency: v})}/>
            </div>
            <div style={{ display:'flex', justifyContent:'flex-end', gap: 10, marginTop: 22 }}>
              <button style={medicoStyles.btnGhost} onClick={() => setShowAlerts(false)}>Cancelar</button>
              <button style={medicoStyles.btnPrimary} onClick={() => setShowAlerts(false)}>Guardar cambios</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// ─── Helpers ────────────────────────────────────────────────────
const Kpi = ({ label, value, sub, accent }) => (
  <div style={medicoStyles.kpi}>
    <div style={{ position:'absolute', top: 0, left: 0, height: 3, width: '100%', background: accent }}/>
    <div style={medicoStyles.kpiLabel}>{label}</div>
    <div style={medicoStyles.kpiVal}>{value}</div>
    <div style={medicoStyles.kpiSub}>{sub}</div>
  </div>
);

const ThresholdField = ({ label, unit, value, min, max, onChange }) => (
  <div>
    <div style={{ fontSize: 12, color: '#4a5568', marginBottom: 6, fontWeight: 500 }}>{label}</div>
    <div style={{ display:'flex', alignItems:'center', gap: 12 }}>
      <input type="range" min={min} max={max} value={value}
        onChange={e => onChange(+e.target.value)}
        style={{ flex: 1, accentColor: '#0d5b75' }}/>
      <div style={{ width: 84, padding: '6px 10px', background: '#f7f7f5',
        borderRadius: 6, fontSize: 13, color: '#1f2937', fontWeight: 600,
        fontVariantNumeric: 'tabular-nums', textAlign:'center' }}>
        {value} <span style={{ fontSize: 10, color: '#7a8694', fontWeight: 400 }}>{unit.split(' ')[0]}</span>
      </div>
    </div>
    <div style={{ fontSize: 10, color: '#7a8694', marginTop: 4 }}>{unit}</div>
  </div>
);

// ─── SVG icons ──────────────────────────────────────────────────
const SvgIcon = ({ d, size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{d}</svg>
);
const SvgBell = () => <SvgIcon size={16} d={<><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></>}/>;
const SvgSearch = () => <SvgIcon size={14} d={<><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></>}/>;
const SvgDownload = () => <SvgIcon d={<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></>}/>;
const SvgFlag = () => <SvgIcon d={<><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1zM4 22V15"/></>}/>;

// ─── Styles ──────────────────────────────────────────────────────
const medicoStyles = {
  root: {
    position: 'absolute', inset: 0,
    background: '#f7f7f5', color: '#1f2937',
    fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
    fontSize: 13, display: 'flex', flexDirection: 'column', overflow: 'hidden',
  },

  topnav: {
    height: 56, background: '#fff', borderBottom: '1px solid #e5e7eb',
    display: 'flex', alignItems: 'center', padding: '0 24px', gap: 24, flexShrink: 0,
  },
  brand: { display:'flex', alignItems:'center', gap: 12, minWidth: 280 },
  brandMark: {
    width: 32, height: 32, borderRadius: 8, background:'#0d5b75',
    color:'#fff', fontSize: 20, fontWeight: 700,
    display:'flex', alignItems:'center', justifyContent:'center',
  },
  brandTitle: { fontSize: 14, fontWeight: 600, lineHeight: 1.2 },
  brandSub: { fontSize: 11, color: '#7a8694' },
  navTabs: { display:'flex', gap: 4, flex: 1 },
  navTab: { padding: '6px 12px', borderRadius: 6, fontSize: 13, color:'#7a8694', cursor:'pointer' },
  navTabActive: { background: '#eef7f5', color:'#0d5b75', fontWeight: 600 },
  navRight: { display:'flex', alignItems:'center', gap: 12 },
  iconBtnGhost: {
    position:'relative', width: 36, height: 36, borderRadius: 8,
    background:'#f7f7f5', border:'1px solid #e5e7eb', color:'#4a5568',
    display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer',
  },
  bellDot: { position:'absolute', top: 8, right: 9, width: 7, height: 7, borderRadius: '50%', background:'#c0362c', border:'1.5px solid #f7f7f5' },
  userChip: {
    width: 32, height: 32, borderRadius: '50%', background:'#0d5b75', color:'#fff',
    display:'flex', alignItems:'center', justifyContent:'center', fontSize: 12, fontWeight: 600,
  },

  body: { flex: 1, display: 'flex', minHeight: 0 },

  // Rail
  patientsRail: {
    width: 320, flexShrink: 0, background: '#fff', borderRight: '1px solid #e5e7eb',
    display: 'flex', flexDirection: 'column',
  },
  railHeader: { padding: '16px 18px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' },
  railTitle: { fontSize: 16, fontWeight: 600 },
  railCount: { fontSize: 11, color: '#7a8694', marginTop: 2 },
  smallBtn: { width: 28, height: 28, borderRadius: 6, border:'1px solid #e5e7eb', background:'#fff', color:'#7a8694', cursor:'pointer', fontSize: 16, fontWeight: 600 },
  searchWrap: { margin: '0 14px 14px', position:'relative', display:'flex', alignItems:'center', gap: 8,
    border:'1px solid #e5e7eb', borderRadius: 8, padding: '6px 10px', background:'#f7f7f5', color:'#7a8694' },
  search: { flex: 1, border: 'none', outline: 'none', background:'transparent', fontSize: 12, fontFamily:'inherit', color:'#1f2937' },
  triageBar: { display: 'flex', borderTop: '1px solid #e5e7eb', borderBottom: '1px solid #e5e7eb' },
  patientList: { flex: 1, overflowY: 'auto', padding: '6px 6px' },
  patientRow: {
    padding: '12px 12px', borderLeft: '3px solid transparent',
    borderBottom: '1px solid #f1f3f5', cursor:'pointer',
  },
  patientRowActive: { background: '#f0f6f6' },
  patientRowTop: { display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap: 10 },
  patientName: { fontSize: 13, fontWeight: 600, lineHeight: 1.2, color:'#1f2937' },
  patientMeta: { fontSize: 11, color: '#7a8694', marginTop: 3 },
  alarmBadge: { padding: '2px 7px', borderRadius: 10, fontSize: 11, fontWeight: 700, fontVariantNumeric: 'tabular-nums' },
  patientRowBot: { display:'flex', justifyContent:'space-between', alignItems:'center', marginTop: 8 },
  patientMmse: { display:'flex', alignItems:'baseline' },

  // Detail
  detail: { flex: 1, overflowY: 'auto', padding: 22 },
  detailHeader: { display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom: 14 },
  patientAvatar: {
    width: 56, height: 56, borderRadius: 12,
    display:'flex', alignItems:'center', justifyContent:'center',
    fontSize: 18, fontWeight: 600,
  },
  detailName: { fontSize: 22, fontWeight: 600, color: '#1f2937', letterSpacing: '-.01em' },
  detailMeta: { fontSize: 12, color: '#4a5568', marginTop: 4, display:'flex', alignItems:'center', flexWrap:'wrap' },
  stagePill: { padding: '2px 9px', borderRadius: 10, fontSize: 11, fontWeight: 600, letterSpacing: '.02em' },

  flagsRow: { display:'flex', gap: 8, marginBottom: 14, flexWrap:'wrap' },
  flagPill: {
    display:'flex', alignItems:'center', gap: 6,
    padding: '5px 10px', borderRadius: 6, fontSize: 12,
    border: '1px solid',
  },

  kpiGrid: { display:'grid', gridTemplateColumns:'repeat(5, 1fr)', gap: 12, marginBottom: 18 },
  kpi: { background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: '14px 16px', position:'relative', overflow:'hidden' },
  kpiLabel: { fontSize: 11, color: '#7a8694', textTransform:'uppercase', letterSpacing: '.06em', fontWeight: 600, marginBottom: 6 },
  kpiVal: { fontSize: 28, fontWeight: 700, color: '#1f2937', letterSpacing: '-.01em', fontVariantNumeric: 'tabular-nums', lineHeight: 1 },
  kpiSub: { fontSize: 11, color: '#7a8694', marginTop: 5 },

  tabs: { display:'flex', gap: 0, borderBottom: '1px solid #e5e7eb', marginBottom: 14 },
  tab: {
    padding: '10px 16px', background: 'transparent', border: 'none',
    fontSize: 12, color: '#7a8694', fontFamily: 'inherit', cursor: 'pointer',
    borderBottom: '2px solid transparent', marginBottom: -1, fontWeight: 500,
  },
  tabActive: { color: '#0d5b75', borderBottomColor: '#0d5b75', fontWeight: 600 },

  tabContent: {},
  card: { background:'#fff', border:'1px solid #e5e7eb', borderRadius: 10, padding: 18 },
  cardHeader: { display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom: 8 },
  cardTitle: { fontSize: 14, fontWeight: 600, color: '#1f2937' },
  cardSub: { fontSize: 11, color: '#7a8694', marginTop: 2 },
  segBtn: { padding: '4px 10px', background:'#f7f7f5', border:'1px solid #e5e7eb', borderRadius: 6, fontSize: 11, color:'#4a5568', cursor:'pointer', fontFamily:'inherit' },
  segBtnActive: { background:'#0d5b75', borderColor:'#0d5b75', color:'#fff', fontWeight: 600 },

  table: { width: '100%', borderCollapse: 'collapse', marginTop: 8 },
  th: { textAlign: 'left', padding: '8px 10px', fontSize: 11, fontWeight: 600, color:'#7a8694', textTransform: 'uppercase', letterSpacing: '.04em', borderBottom: '1px solid #e5e7eb' },
  td: { padding: '9px 10px', fontSize: 12, color:'#374151', borderBottom: '1px solid #f1f3f5', verticalAlign:'top' },
  trFlag: { background: '#fef6ec' },
  actionTag: { display:'inline-block', padding:'2px 7px', borderRadius: 4, background:'#eef0f3', fontSize: 10, color:'#4a5568', fontFamily:'"IBM Plex Mono", monospace', letterSpacing:'.04em' },
  flagInline: { marginLeft: 6, fontSize: 10, color: '#b45309', fontStyle: 'italic' },

  noteCard: { background:'#fafaf8', border:'1px solid #e5e7eb', borderRadius: 8, padding: 12, marginBottom: 10 },
  noteHeader: { display: 'flex', justifyContent: 'space-between', marginBottom: 6 },
  noteAuthor: { fontSize: 11, fontWeight: 600, color:'#0d5b75' },
  noteDate: { fontSize: 11, color: '#7a8694' },
  noteText: { fontSize: 13, color: '#1f2937', lineHeight: 1.5 },
  textarea: { width: '100%', marginTop: 10, padding: 10, border: '1px solid #e5e7eb', borderRadius: 8, fontFamily:'inherit', fontSize: 13, resize:'vertical', outline:'none' },

  btnPrimary: {
    background: '#0d5b75', color: '#fff', border: 'none',
    padding: '8px 14px', borderRadius: 7, fontSize: 12, fontWeight: 600,
    cursor: 'pointer', fontFamily: 'inherit',
  },
  btnGhost: {
    background: '#fff', color: '#4a5568', border: '1px solid #d8dee5',
    padding: '7px 12px', borderRadius: 7, fontSize: 12, fontWeight: 500,
    cursor: 'pointer', fontFamily: 'inherit',
    display:'inline-flex', alignItems:'center', gap: 6,
  },

  // Modal
  overlay: { position:'absolute', inset: 0, background:'rgba(15,23,42,.3)', zIndex: 40 },
  modal: {
    position:'absolute', top:'50%', left:'50%', transform:'translate(-50%,-50%)',
    background:'#fff', borderRadius: 14, padding: 26, width: 640, zIndex: 41,
    boxShadow: '0 30px 80px rgba(15,23,42,.25)',
  },
  modalHeader: { display:'flex', justifyContent:'space-between', alignItems:'flex-start' },
  modalTitle: { fontSize: 16, fontWeight: 600, color:'#1f2937' },
  modalClose: { width: 28, height: 28, border:'none', background:'#f7f7f5', borderRadius: 6, fontSize: 18, color:'#7a8694', cursor:'pointer' },
};

window.MedicoView = MedicoView;

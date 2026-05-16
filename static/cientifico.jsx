// Vista CIENTÍFICO — denso, oscuro, estilo Grafana.
// Filtros cruzados + heatmap política RL + curvas entrenamiento +
// tabla runs + inline docs.
// 1600x1000.

const CientificoView = () => {
  const D = window.MOCK.science;
  const [filters, setFilters] = React.useState({
    stage: 'all', mode: 'all', range: '7d', model: 'ppo_v3.2',
  });
  const [hoverCell, setHoverCell] = React.useState(null);
  const stageDistRef = React.useRef(null);
  const mmseHistRef = React.useRef(null);
  const actionFitRef = React.useRef(null);
  const trainCurveRef = React.useRef(null);
  const alarmsRef = React.useRef(null);
  const topicsRef = React.useRef(null);

  React.useEffect(() => {
    if (!window.Chart) return;

    Chart.defaults.color = '#7589a6';
    Chart.defaults.borderColor = '#1f2a3f';
    Chart.defaults.font.family = '"IBM Plex Sans", system-ui, sans-serif';

    const setup = (ref, type, data, opts) => {
      if (!ref.current) return;
      if (ref.current._chart) ref.current._chart.destroy();
      ref.current._chart = new Chart(ref.current.getContext('2d'), {
        type, data,
        options: { responsive: true, maintainAspectRatio: false, ...opts },
      });
    };

    // Stage distribution donut
    setup(stageDistRef, 'doughnut', {
      labels: Object.keys(D.stageDist).map(s => s.replace('_AD', ' AD')),
      datasets: [{
        data: Object.values(D.stageDist),
        backgroundColor: ['#22d3ee','#a78bfa','#fbbf24','#fb923c','#f87171'],
        borderWidth: 0,
      }],
    }, {
      cutout: '62%',
      plugins: { legend: { position: 'right', labels: { boxWidth: 8, font: { size: 10 } } } },
    });

    // MMSE histogram
    setup(mmseHistRef, 'bar', {
      labels: D.mmseHist.map(b => b.bin),
      datasets: [{
        data: D.mmseHist.map(b => b.n),
        backgroundColor: 'rgba(34,211,238,.4)',
        borderColor: '#22d3ee', borderWidth: 1,
      }],
    }, {
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color:'#15203a' }, ticks: { font: { size: 9 } } },
        y: { grid: { color:'#15203a' }, ticks: { font: { size: 9 } } },
      },
    });

    // Action fit
    const sorted = [...D.actionStats].sort((a,b) => b.fit - a.fit);
    setup(actionFitRef, 'bar', {
      labels: sorted.map(a => a.name),
      datasets: [{
        data: sorted.map(a => a.fit),
        backgroundColor: sorted.map(a => a.fit > 0.65 ? 'rgba(132,204,22,.7)'
          : a.fit > 0.45 ? 'rgba(251,191,36,.7)' : 'rgba(248,113,113,.7)'),
        borderWidth: 0,
      }],
    }, {
      indexAxis: 'y',
      plugins: { legend: { display: false },
        tooltip: { callbacks: { label: ctx => `fit=${ctx.raw.toFixed(2)}  n=${sorted[ctx.dataIndex].n}` } } },
      scales: {
        x: { min: 0, max: 1, grid: { color:'#15203a' }, ticks: { font: { size: 9 } } },
        y: { grid: { display: false }, ticks: { font: { size: 9, family: '"IBM Plex Mono"' } } },
      },
    });

    // Training curve
    setup(trainCurveRef, 'line', {
      labels: D.trainingCurve.map((_, i) => i * 10),
      datasets: [
        {
          label: 'reward',
          data: D.trainingCurve,
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6,182,212,.10)',
          tension: .25, pointRadius: 0, borderWidth: 1.5, fill: true,
        },
        {
          label: 'reward (smoothed)',
          data: D.trainingCurve.map((_, i, arr) => {
            const w = arr.slice(Math.max(0,i-5), i+1);
            return w.reduce((a,b)=>a+b,0) / w.length;
          }),
          borderColor: '#84cc16',
          borderWidth: 2, pointRadius: 0, tension: .25, fill: false,
        },
      ],
    }, {
      plugins: { legend: { position: 'bottom', labels: { font: { size: 10 }, boxWidth: 10 } } },
      scales: {
        x: { grid: { color:'#15203a' }, ticks: { font: { size: 9 }, callback: v => `${v}k` } },
        y: { grid: { color:'#15203a' }, ticks: { font: { size: 9 } }, min: 0, max: 1 },
      },
    });

    // Alarm counts
    const alarms = Object.entries(D.alarmCounts).sort((a,b) => b[1] - a[1]);
    setup(alarmsRef, 'bar', {
      labels: alarms.map(([k]) => k),
      datasets: [{
        data: alarms.map(([,v]) => v),
        backgroundColor: 'rgba(248,113,113,.6)', borderColor:'#f87171', borderWidth: 1,
      }],
    }, {
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color:'#15203a' }, ticks: { font: { size: 9 } } },
        y: { grid: { display: false }, ticks: { font: { size: 9 } } },
      },
    });

    // Topic scores
    setup(topicsRef, 'bar', {
      labels: D.topicScores.map(([k]) => k),
      datasets: [{
        data: D.topicScores.map(([,v]) => v),
        backgroundColor: 'rgba(167,139,250,.5)', borderColor:'#a78bfa', borderWidth: 1,
      }],
    }, {
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { min: 0, max: 1, grid: { color:'#15203a' }, ticks: { font: { size: 9 } } },
        y: { grid: { display: false }, ticks: { font: { size: 9 } } },
      },
    });
  }, []);

  const stages = ['HEALTHY','MCI','MILD_AD','MODERATE_AD','SEVERE_AD'];
  const actionLabels = window.MOCK.science.actionStats.map(a => a.name);

  // Heat color from value [0..0.25]
  const heat = (v) => {
    const t = Math.min(1, v / 0.22);
    const r = Math.round(15 + (6 - 15) * t * 0);
    // gradient from #131c2e (cold) to #06b6d4 (mid) to #fbbf24 (hot)
    if (t < 0.5) {
      const k = t * 2;
      return `rgb(${15 + (6-15)*k}, ${28 + (182-28)*k}, ${46 + (212-46)*k})`;
    } else {
      const k = (t - 0.5) * 2;
      return `rgb(${6 + (251-6)*k}, ${182 + (191-182)*k}, ${212 + (36-212)*k})`;
    }
  };

  return (
    <div style={ciStyles.root}>
      {/* ── Top bar ── */}
      <div style={ciStyles.topbar}>
        <div style={ciStyles.brand}>
          <div style={ciStyles.brandLogo}>⌬</div>
          <div>
            <div style={ciStyles.brandTitle}>Alzheimer Chat-RL <span style={ciStyles.brandVer}>v3.2.1</span></div>
            <div style={ciStyles.brandSub}>RESEARCH · METRICS · POLICY ANALYSIS</div>
          </div>
        </div>
        <div style={ciStyles.topbarSpacer}/>
        <div style={ciStyles.statusGroup}>
          <StatusDot label="API" ok={true}/>
          <StatusDot label="Worker" ok={true}/>
          <StatusDot label="Sim queue" ok={true} sub="3 jobs"/>
          <div style={ciStyles.lastUpdate}>updated 14:23:08 · auto-refresh 10s</div>
        </div>
      </div>

      {/* ── Filters ── */}
      <div style={ciStyles.filterBar}>
        <Filter label="STAGE" value={filters.stage}
          options={[['all','all (1284)'],['HEALTHY','HEALTHY (142)'],['MCI','MCI (318)'],['MILD_AD','MILD AD (462)'],['MODERATE_AD','MOD AD (287)'],['SEVERE_AD','SEV AD (75)']]}
          onChange={v => setFilters({...filters, stage: v})}/>
        <Filter label="SIM MODE" value={filters.mode}
          options={[['all','all'],['rules_only','rules_only'],['llm_hybrid','llm_hybrid'],['llm_only','llm_only']]}
          onChange={v => setFilters({...filters, mode: v})}/>
        <Filter label="RANGE" value={filters.range}
          options={[['24h','24h'],['7d','7d'],['30d','30d'],['90d','90d'],['all','all']]}
          onChange={v => setFilters({...filters, range: v})}/>
        <Filter label="MODEL" value={filters.model}
          options={D.runs.map(r => [r.id, r.id])}
          onChange={v => setFilters({...filters, model: v})}/>
        <div style={ciStyles.filterDivider}/>
        <div style={ciStyles.filterChip}>seed: random</div>
        <div style={ciStyles.filterChip}>language: es</div>
        <div style={{ flex: 1 }}/>
        <button style={ciStyles.iconBtn}>⤓ Export JSONL</button>
        <button style={ciStyles.iconBtn}>↻</button>
      </div>

      {/* ── Body ── */}
      <div style={ciStyles.body}>
        {/* KPI strip */}
        <div style={ciStyles.kpiStrip}>
          <KPI label="SESIONES" value={D.kpis.sessions.toLocaleString('es-ES')} delta="+12.4%" color="#22d3ee"/>
          <KPI label="TURNOS" value={D.kpis.turns.toLocaleString('es-ES')} delta="+8.1%" color="#a78bfa"/>
          <KPI label="MMSE MEDIO" value={D.kpis.mmseAvg.toFixed(1)} delta="−0.2" color="#84cc16"/>
          <KPI label="SILENCIO" value={`${(D.kpis.silenceRate*100).toFixed(1)}%`} delta="−1.1pp" color="#fbbf24"/>
          <KPI label="ALARMAS" value={D.kpis.alarms} delta="+18" color="#f87171"/>
          <KPI label="STRATEGY FIT" value="0.683" delta="+0.041" color="#06b6d4"/>
          <KPI label="DOMINIOS" value={D.kpis.domains} delta="±0" color="#a78bfa"/>
          <KPI label="EPISODE LEN" value="14.4" sub="turnos/ep" color="#22d3ee"/>
        </div>

        {/* Row 1: policy heatmap big + training curve */}
        <div style={{ display:'grid', gridTemplateColumns: '1.4fr 1fr', gap: 12, marginBottom: 12 }}>
          <Card title="POLÍTICA RL · π(a|s)" sub="Probabilidad de selección de acción por estadio · modelo ppo_v3.2">
            <div style={ciStyles.heatmapWrap}>
              <div style={ciStyles.heatmapColHeader}>
                <div style={{ width: 96 }}/>
                {actionLabels.map((a,i) => (
                  <div key={a} style={ciStyles.heatColLabel}>{a}</div>
                ))}
              </div>
              {stages.map((s, r) => (
                <div key={s} style={ciStyles.heatRow}>
                  <div style={ciStyles.heatRowLabel}>{s.replace('_AD',' AD')}</div>
                  {D.policyHeatmap[r].map((v, c) => (
                    <div key={c} style={{
                      ...ciStyles.heatCell, background: heat(v),
                      color: v > 0.12 ? '#0a0d12' : '#a7b6cb',
                      outline: hoverCell && hoverCell.r === r && hoverCell.c === c ? '1.5px solid #fff' : 'none',
                    }}
                      onMouseEnter={() => setHoverCell({ r, c, v })}
                      onMouseLeave={() => setHoverCell(null)}>
                      {v.toFixed(2).slice(1)}
                    </div>
                  ))}
                </div>
              ))}
              <div style={ciStyles.heatLegend}>
                <span style={{ fontSize: 9, color:'#7589a6', marginRight: 8 }}>P(a|s):</span>
                <div style={{ display: 'flex', alignItems:'center', gap: 0 }}>
                  {[0.02, 0.05, 0.08, 0.12, 0.16, 0.20].map(v => (
                    <div key={v} style={{ width: 24, height: 10, background: heat(v) }}/>
                  ))}
                </div>
                <span style={{ fontSize: 9, color:'#7589a6', marginLeft: 8, fontFamily: 'IBM Plex Mono, monospace' }}>0.02 → 0.20</span>
                {hoverCell && (
                  <div style={{ marginLeft: 'auto', fontSize: 10, color:'#22d3ee', fontFamily: 'IBM Plex Mono, monospace' }}>
                    π({actionLabels[hoverCell.c]}|{stages[hoverCell.r]}) = <b>{hoverCell.v.toFixed(3)}</b>
                  </div>
                )}
              </div>
            </div>
          </Card>

          <Card title="CURVA DE ENTRENAMIENTO · ppo_v3.2" sub="Recompensa media por episodio · 1000 episodes">
            <div style={{ height: 200 }}><canvas ref={trainCurveRef}/></div>
            <div style={ciStyles.miniGrid}>
              <Mini label="best reward" v="0.768"/>
              <Mini label="final reward" v="0.742"/>
              <Mini label="steps" v="500k"/>
              <Mini label="ep length μ" v="14.4"/>
              <Mini label="kl div μ" v="0.012"/>
              <Mini label="entropy" v="1.42"/>
            </div>
          </Card>
        </div>

        {/* Row 2: action fit + population dist + mmse hist */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: 12, marginBottom: 12 }}>
          <Card title="STRATEGY FIT · POR ACCIÓN" sub="μ fit  ·  n samples (verde > 0.65)">
            <div style={{ height: 280 }}><canvas ref={actionFitRef}/></div>
          </Card>
          <Card title="POBLACIÓN · ESTADIO" sub="distribución de pacientes simulados">
            <div style={{ height: 200 }}><canvas ref={stageDistRef}/></div>
            <div style={{ display:'flex', justifyContent:'space-between', marginTop: 12, fontFamily:'IBM Plex Mono, monospace', fontSize: 10 }}>
              <span style={{ color:'#7589a6' }}>χ² = 142.3</span>
              <span style={{ color:'#84cc16' }}>p &lt; 0.001 ✓</span>
              <span style={{ color:'#7589a6' }}>n=1284</span>
            </div>
          </Card>
          <Card title="HISTOGRAMA MMSE" sub="rango 0–30 · bin = 5">
            <div style={{ height: 200 }}><canvas ref={mmseHistRef}/></div>
            <div style={{ display:'flex', justifyContent:'space-between', marginTop: 12, fontFamily:'IBM Plex Mono, monospace', fontSize: 10 }}>
              <span style={{ color:'#7589a6' }}>μ = 22.3</span>
              <span style={{ color:'#7589a6' }}>σ = 6.1</span>
              <span style={{ color:'#7589a6' }}>med = 23</span>
            </div>
          </Card>
        </div>

        {/* Row 3: runs comparison + alarms + topics */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr 1fr', gap: 12, marginBottom: 12 }}>
          <Card title="RUNS · COMPARATIVA" sub="experimentos recientes · ▲ delta sobre baseline">
            <table style={ciStyles.runsTable}>
              <thead>
                <tr>
                  <th style={ciStyles.runsTh}>ID</th>
                  <th style={ciStyles.runsTh}>FECHA</th>
                  <th style={ciStyles.runsTh}>STEPS</th>
                  <th style={ciStyles.runsTh}>REWARD</th>
                  <th style={ciStyles.runsTh}>SUCCESS</th>
                  <th style={ciStyles.runsTh}>ALARMS</th>
                  <th style={ciStyles.runsTh}></th>
                </tr>
              </thead>
              <tbody>
                {D.runs.map(r => (
                  <tr key={r.id} style={{
                    background: r.status === 'best' ? 'rgba(132,204,22,.06)' : 'transparent',
                  }}>
                    <td style={ciStyles.runsTd}>
                      <div style={{ display:'flex', alignItems:'center', gap: 6 }}>
                        {r.status === 'best' && <span style={{ color:'#84cc16' }}>★</span>}
                        {r.status === 'baseline' && <span style={{ fontSize: 9, padding:'1px 5px', border:'1px solid #2a3a55', borderRadius:3, color:'#7589a6' }}>BL</span>}
                        <span style={{ fontFamily:'IBM Plex Mono, monospace', color: r.status === 'best' ? '#84cc16' : '#cad6e6' }}>{r.id}</span>
                      </div>
                    </td>
                    <td style={{ ...ciStyles.runsTd, color:'#7589a6' }}>{r.date}</td>
                    <td style={{ ...ciStyles.runsTd, fontFamily:'IBM Plex Mono, monospace' }}>{r.steps}</td>
                    <td style={{ ...ciStyles.runsTd, fontFamily:'IBM Plex Mono, monospace', fontWeight: 600, color: r.reward > 0.65 ? '#84cc16' : r.reward > 0.5 ? '#fbbf24' : '#f87171' }}>
                      {r.reward.toFixed(3)}
                    </td>
                    <td style={{ ...ciStyles.runsTd, fontFamily:'IBM Plex Mono, monospace' }}>{(r.success*100).toFixed(0)}%</td>
                    <td style={{ ...ciStyles.runsTd, fontFamily:'IBM Plex Mono, monospace', color: r.alarms > 0.15 ? '#f87171' : '#7589a6' }}>{(r.alarms*100).toFixed(0)}%</td>
                    <td style={ciStyles.runsTd}>
                      <button style={ciStyles.runsBtn}>diff</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <Card title="DISTRIBUCIÓN DE ALARMAS" sub="acumulado 30 días">
            <div style={{ height: 280 }}><canvas ref={alarmsRef}/></div>
          </Card>

          <Card title="TOPIC ENGAGEMENT" sub="score medio · top intereses revelados">
            <div style={{ height: 280 }}><canvas ref={topicsRef}/></div>
          </Card>
        </div>

        {/* Row 4: Arquitectura inline docs */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr 1fr', gap: 12 }}>
          <Card title="ESPACIO DE OBSERVACIÓN · obs_dim=16">
            <table style={ciStyles.docsTable}>
              <thead>
                <tr>
                  <th style={ciStyles.docsTh}>#</th>
                  <th style={ciStyles.docsTh}>FEATURE</th>
                  <th style={ciStyles.docsTh}>RANGO</th>
                  <th style={ciStyles.docsTh}>CATEGORÍA</th>
                </tr>
              </thead>
              <tbody>
                {[
                  [0,'mmse_norm','[0,1]','patient','#22d3ee'],
                  [1,'fatigue','[0,1]','patient','#22d3ee'],
                  [2,'anxiety','[0,1]','patient','#22d3ee'],
                  [3,'mood','[−1,1]','patient','#22d3ee'],
                  [4,'stage_norm','[0,1]','patient','#22d3ee'],
                  [5,'test_success_rate','[0,1]','history','#84cc16'],
                  [6,'last_latency_norm','[0,1]','signal','#a78bfa'],
                  [7,'last_silent','{0,1}','signal','#a78bfa'],
                  [8,'turn_norm','[0,1]','context','#fbbf24'],
                  [12,'strategy_fit','[0,1]','signal','#a78bfa'],
                  [13,'engagement_trend','[−1,1]','signal','#a78bfa'],
                  [15,'silence_streak_norm','[0,1]','signal','#f87171'],
                ].map(([i,n,r,cat,c]) => (
                  <tr key={i}>
                    <td style={{ ...ciStyles.docsTd, color:'#7589a6' }}>{i}</td>
                    <td style={{ ...ciStyles.docsTd, fontFamily:'IBM Plex Mono, monospace', color:'#cad6e6' }}>{n}</td>
                    <td style={{ ...ciStyles.docsTd, fontFamily:'IBM Plex Mono, monospace', color:'#7589a6', fontSize: 10 }}>{r}</td>
                    <td style={ciStyles.docsTd}>
                      <span style={{ fontSize: 9, padding: '1px 6px', borderRadius: 3, background: c+'18', color: c, fontWeight: 500, letterSpacing:'.04em', textTransform:'uppercase' }}>{cat}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <Card title="ESPACIO DE ACCIONES · n=13">
            <table style={ciStyles.docsTable}>
              <thead>
                <tr>
                  <th style={ciStyles.docsTh}>ID</th>
                  <th style={ciStyles.docsTh}>ACCIÓN</th>
                  <th style={ciStyles.docsTh}>CATEGORÍA</th>
                </tr>
              </thead>
              <tbody>
                {[
                  [0,'GREETING','social','#fbbf24'],
                  [1,'ASK_MEMORY','test','#a78bfa'],
                  [2,'ASK_ORIENTATION','test','#a78bfa'],
                  [3,'ASK_LANGUAGE','test','#a78bfa'],
                  [4,'TELL_STORY','narrativa','#22d3ee'],
                  [5,'ASK_PREFERENCE','preferencia','#fbbf24'],
                  [6,'PROPOSE_ACTIVITY','actividad','#84cc16'],
                  [7,'OFFER_MUSIC','actividad','#84cc16'],
                  [9,'REFRÁN','cultural','#84cc16'],
                  [10,'CANCIÓN','cultural','#84cc16'],
                  [11,'TRIVIA_CULTURAL','cultural','#84cc16'],
                  [12,'TRIVIA_DEPORTES','cultural','#84cc16'],
                ].map(([i,n,c,col]) => (
                  <tr key={i}>
                    <td style={{ ...ciStyles.docsTd, color:'#7589a6' }}>{i}</td>
                    <td style={{ ...ciStyles.docsTd, fontFamily:'IBM Plex Mono, monospace', color:'#cad6e6' }}>{n}</td>
                    <td style={ciStyles.docsTd}>
                      <span style={{ fontSize: 9, padding: '1px 6px', borderRadius: 3, background: col+'18', color: col, fontWeight: 500 }}>{c}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <Card title="REWARD WEIGHTS · r(s,a,s′)">
            <table style={ciStyles.docsTable}>
              <thead>
                <tr><th style={ciStyles.docsTh}>COMPONENTE</th><th style={ciStyles.docsTh}>w</th><th style={ciStyles.docsTh}>EFECTO</th></tr>
              </thead>
              <tbody>
                {[
                  ['mood_lift', '+1.0', 'incentiva ánimo', '#84cc16'],
                  ['strategy_fit', '+0.4', 'incentiva adecuación', '#84cc16'],
                  ['cultural_bonus', '+0.6', 'cultura local', '#84cc16'],
                  ['procedural_lift', '+0.3', 'lenguaje preservado', '#84cc16'],
                  ['latency_penalty', '−0.5', 'penaliza esfuerzo', '#f87171'],
                  ['silence_penalty', '−0.5', 'penaliza silencio', '#f87171'],
                  ['anxiety_penalty', '−0.4', 'penaliza ansiedad', '#f87171'],
                  ['fatigue_penalty', '−0.3', 'penaliza fatiga', '#f87171'],
                ].map(([c,w,e,col]) => (
                  <tr key={c}>
                    <td style={{ ...ciStyles.docsTd, fontFamily:'IBM Plex Mono, monospace', color:'#cad6e6' }}>{c}</td>
                    <td style={{ ...ciStyles.docsTd, fontFamily:'IBM Plex Mono, monospace', color:col, fontWeight: 600 }}>{w}</td>
                    <td style={{ ...ciStyles.docsTd, color:'#7589a6', fontSize: 10 }}>{e}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ marginTop: 12, padding: '10px 12px', background:'#0d1424', borderRadius: 6, fontFamily:'IBM Plex Mono, monospace', fontSize: 10, color:'#7589a6', lineHeight: 1.6 }}>
              <span style={{ color:'#84cc16' }}>def</span> <span style={{ color:'#22d3ee' }}>compute_reward</span>(s, a, s_next):<br/>
              &nbsp;&nbsp;<span style={{ color:'#a78bfa' }}>r</span> = 1.0·Δmood + 0.4·fit + 0.6·cult<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;− 0.5·lat_norm − 0.5·silent − 0.4·Δanx<br/>
              &nbsp;&nbsp;<span style={{ color:'#fbbf24' }}>return</span> clip(r, −2, +2)
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

// ─── Subcomponents ─────────────────────────────────────────────
const KPI = ({ label, value, delta, sub, color }) => (
  <div style={ciStyles.kpi}>
    <div style={{ position:'absolute', left: 0, top: 0, bottom: 0, width: 3, background: color }}/>
    <div style={ciStyles.kpiLabel}>{label}</div>
    <div style={ciStyles.kpiVal}>{value}</div>
    {delta && (
      <div style={{ fontSize: 10, color: delta.startsWith('+') ? '#84cc16' : delta.startsWith('−') ? '#f87171' : '#7589a6', fontFamily: 'IBM Plex Mono, monospace', marginTop: 3 }}>
        Δ {delta}
      </div>
    )}
    {sub && <div style={{ fontSize: 10, color: '#7589a6', fontFamily: 'IBM Plex Mono, monospace', marginTop: 3 }}>{sub}</div>}
  </div>
);

const Card = ({ title, sub, children }) => (
  <div style={ciStyles.card}>
    <div style={{ marginBottom: 10 }}>
      <div style={ciStyles.cardTitle}>{title}</div>
      {sub && <div style={ciStyles.cardSub}>{sub}</div>}
    </div>
    {children}
  </div>
);

const Filter = ({ label, value, options, onChange }) => (
  <div style={ciStyles.filter}>
    <div style={ciStyles.filterLabel}>{label}</div>
    <select style={ciStyles.filterSelect} value={value} onChange={e => onChange(e.target.value)}>
      {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
    </select>
  </div>
);

const Mini = ({ label, v }) => (
  <div>
    <div style={{ fontSize: 9, color:'#7589a6', letterSpacing:'.06em', textTransform:'uppercase' }}>{label}</div>
    <div style={{ fontSize: 13, color:'#cad6e6', fontFamily: 'IBM Plex Mono, monospace', fontWeight: 600, marginTop: 2 }}>{v}</div>
  </div>
);

const StatusDot = ({ label, ok, sub }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color:'#7589a6' }}>
    <span style={{ width: 7, height: 7, borderRadius: '50%', background: ok ? '#84cc16' : '#f87171', boxShadow: ok ? '0 0 6px #84cc16' : 'none' }}/>
    <span>{label}</span>
    {sub && <span style={{ color:'#465673' }}>· {sub}</span>}
  </div>
);

// ─── Styles ────────────────────────────────────────────────────
const ciStyles = {
  root: {
    position:'absolute', inset: 0, overflow:'hidden',
    background: '#080c14', color: '#cad6e6',
    fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
    fontSize: 12, display:'flex', flexDirection:'column',
  },

  // Top bar
  topbar: {
    height: 50, background: '#0c1322', borderBottom: '1px solid #1a2438',
    display:'flex', alignItems:'center', padding: '0 18px', gap: 16, flexShrink: 0,
  },
  brand: { display:'flex', alignItems:'center', gap: 10 },
  brandLogo: {
    width: 28, height: 28, borderRadius: 6,
    background:'linear-gradient(135deg, #06b6d4, #84cc16)',
    color:'#0a0d12', display:'flex', alignItems:'center', justifyContent:'center',
    fontSize: 18, fontWeight: 700,
  },
  brandTitle: { fontSize: 13, fontWeight: 600, color:'#cad6e6' },
  brandVer: { fontSize: 10, color:'#22d3ee', fontFamily: 'IBM Plex Mono, monospace', marginLeft: 6 },
  brandSub: { fontSize: 9, color:'#465673', letterSpacing:'.18em', fontWeight: 600 },
  topbarSpacer: { flex: 1 },
  statusGroup: { display:'flex', alignItems:'center', gap: 16 },
  lastUpdate: { fontSize: 10, color:'#465673', fontFamily: 'IBM Plex Mono, monospace' },

  // Filter
  filterBar: {
    background:'#0c1322', borderBottom:'1px solid #1a2438', padding:'8px 18px',
    display:'flex', alignItems:'center', gap: 10, flexShrink: 0,
  },
  filter: { display:'flex', alignItems:'center', gap: 6 },
  filterLabel: { fontSize: 9, color:'#465673', letterSpacing:'.14em', fontWeight: 600 },
  filterSelect: {
    background:'#131c2e', border:'1px solid #1f2a3f', color:'#cad6e6',
    fontSize: 11, fontFamily:'IBM Plex Mono, monospace', padding:'4px 8px', borderRadius: 4, outline:'none',
  },
  filterDivider: { width: 1, height: 22, background:'#1f2a3f' },
  filterChip: {
    fontSize: 10, color:'#7589a6', fontFamily: 'IBM Plex Mono, monospace',
    padding:'3px 8px', background:'#131c2e', border:'1px solid #1f2a3f', borderRadius: 3,
  },
  iconBtn: {
    fontSize: 10, color:'#22d3ee', fontFamily:'IBM Plex Mono, monospace',
    background:'transparent', border:'1px solid #22d3ee44', padding:'4px 10px', borderRadius: 4, cursor: 'pointer',
  },

  // Body
  body: { flex: 1, overflowY: 'auto', padding: 12 },

  // KPI strip
  kpiStrip: {
    display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: 8, marginBottom: 12,
  },
  kpi: {
    background:'#0f1828', border:'1px solid #1a2438', borderRadius: 6,
    padding: '10px 12px 10px 16px', position:'relative', overflow:'hidden',
  },
  kpiLabel: { fontSize: 9, color:'#7589a6', letterSpacing:'.1em', fontWeight: 600 },
  kpiVal: { fontSize: 22, fontWeight: 700, color:'#e8eef7', fontFamily: 'IBM Plex Mono, monospace', marginTop: 3, lineHeight: 1, fontVariantNumeric: 'tabular-nums' },

  // Card
  card: {
    background:'#0f1828', border:'1px solid #1a2438', borderRadius: 6, padding: 14,
  },
  cardTitle: { fontSize: 10, fontWeight: 700, letterSpacing:'.12em', color:'#cad6e6' },
  cardSub: { fontSize: 10, color:'#7589a6', marginTop: 2 },

  // Heatmap
  heatmapWrap: { padding: '4px 0 0' },
  heatmapColHeader: { display: 'grid', gridTemplateColumns: '96px repeat(13, 1fr)', marginBottom: 4 },
  heatColLabel: {
    fontSize: 9, color: '#7589a6', fontFamily: 'IBM Plex Mono, monospace',
    writingMode: 'vertical-rl', transform: 'rotate(180deg)',
    paddingBottom: 4, paddingTop: 6, alignSelf: 'end',
    textAlign: 'left',
  },
  heatRow: { display: 'grid', gridTemplateColumns: '96px repeat(13, 1fr)', alignItems: 'stretch' },
  heatRowLabel: {
    fontSize: 10, color: '#cad6e6', fontFamily: 'IBM Plex Mono, monospace',
    padding: '0 8px', display:'flex', alignItems:'center', borderRight:'1px solid #1a2438', justifyContent:'flex-end',
  },
  heatCell: {
    height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 10, fontFamily: 'IBM Plex Mono, monospace', fontWeight: 600,
    cursor: 'pointer', transition: 'outline .1s',
  },
  heatLegend: { display:'flex', alignItems:'center', marginTop: 10, paddingTop: 8, borderTop: '1px solid #1a2438' },

  // Mini stats
  miniGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginTop: 12, paddingTop: 12, borderTop: '1px solid #1a2438' },

  // Runs table
  runsTable: { width: '100%', borderCollapse: 'collapse', fontSize: 11 },
  runsTh: { textAlign: 'left', padding: '6px 8px', fontSize: 9, color:'#7589a6', letterSpacing:'.1em', fontWeight: 600, borderBottom:'1px solid #1a2438' },
  runsTd: { padding: '7px 8px', borderBottom: '1px solid #15203a', fontSize: 11 },
  runsBtn: { background:'transparent', border:'1px solid #22d3ee44', color:'#22d3ee', fontSize: 9, padding:'2px 8px', borderRadius: 3, cursor:'pointer', fontFamily:'IBM Plex Mono, monospace' },

  // Docs table
  docsTable: { width: '100%', borderCollapse: 'collapse', fontSize: 11 },
  docsTh: { textAlign: 'left', padding: '5px 8px', fontSize: 9, color:'#465673', letterSpacing:'.1em', fontWeight: 600, borderBottom:'1px solid #1a2438' },
  docsTd: { padding: '5px 8px', fontSize: 11, borderBottom:'1px solid #15203a' },
};

window.CientificoView = CientificoView;

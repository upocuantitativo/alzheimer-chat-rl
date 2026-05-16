// Vista MAYOR — cálida, voz-primero, accesible.
// Chat grande para la persona mayor + panel lateral plegable para el cuidador.
// 1024x768 (tablet landscape feel).

const MayorView = () => {
  const [conv, setConv] = React.useState(window.MOCK.conversation);
  const [listening, setListening] = React.useState(false);
  const [speaking, setSpeaking] = React.useState(false);
  const [caregiverOpen, setCaregiverOpen] = React.useState(false);
  const [showCall, setShowCall] = React.useState(false);
  const [showSize, setShowSize] = React.useState(false);
  const [textScale, setTextScale] = React.useState(1);
  const [now, setNow] = React.useState(new Date());
  const messagesRef = React.useRef(null);

  React.useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(t);
  }, []);

  React.useEffect(() => {
    if (messagesRef.current) messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
  }, [conv]);

  // Simulate voice flow: tap mic → listening 1.8s → user msg → assistant typing → speak
  const askVoice = () => {
    if (listening || speaking) return;
    setListening(true);
    setTimeout(() => {
      setListening(false);
      const userMsgs = [
        'Hoy he dormido bien, gracias.',
        'Me acuerdo de mi pueblo cuando era pequeña.',
        '¿Me pones una canción de Manolo Escobar?',
        'Mi hija viene esta tarde a verme.',
      ];
      const next = userMsgs[conv.length % userMsgs.length];
      const time = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
      setConv(c => [...c, { who: 'usuario', text: next, time }]);
      setTimeout(() => {
        setSpeaking(true);
        const replies = [
          'Me alegra mucho oír eso. ¿Le apetece que hablemos de su familia?',
          '¡Qué bonito recuerdo! ¿Cómo se llamaba ese pueblo?',
          'Por supuesto. Le pongo «Mi carro me lo robaron». Cierre los ojos y disfrute.',
          'Qué buena noticia. Cuando venga, dele un abrazo de mi parte.',
        ];
        const reply = replies[(conv.length) % replies.length];
        setConv(c => [...c, { who: 'asistente', text: reply, time }]);
        setTimeout(() => setSpeaking(false), 2400);
      }, 800);
    }, 1800);
  };

  const fontSize = (base) => `${base * textScale}px`;
  const HH = String(now.getHours()).padStart(2,'0');
  const MM = String(now.getMinutes()).padStart(2,'0');
  const weekday = now.toLocaleDateString('es-ES', { weekday: 'long' });
  const dateStr = now.toLocaleDateString('es-ES', { day: 'numeric', month: 'long' });

  return (
    <div style={mayorStyles.root}>
      {/* ────────── Top bar — minimal, no clinical noise ─────────── */}
      <div style={mayorStyles.topbar}>
        <div style={mayorStyles.greetingWrap}>
          <div style={mayorStyles.timeRow}>
            <span style={mayorStyles.bigTime}>{HH}:{MM}</span>
            <span style={mayorStyles.dateLabel}>
              {weekday.charAt(0).toUpperCase() + weekday.slice(1)} · {dateStr}
            </span>
          </div>
          <div style={mayorStyles.greeting}>Hola, María Dolores</div>
        </div>
        <div style={mayorStyles.topbarActions}>
          <button style={mayorStyles.iconBtn} onClick={() => setShowSize(s => !s)} title="Tamaño de letra">
            <IconText/>
          </button>
          <button style={mayorStyles.iconBtn} onClick={() => setCaregiverOpen(o => !o)} title="Panel cuidador">
            <IconShield/>
          </button>
        </div>
      </div>

      {/* Text-size popover */}
      {showSize && (
        <div style={mayorStyles.sizePopover}>
          <div style={{ fontSize: 16, color: '#5a4a36', marginBottom: 10 }}>Tamaño de letra</div>
          <div style={{ display: 'flex', gap: 8 }}>
            {[
              { v: 0.9, l: 'A', s: 18 },
              { v: 1.0, l: 'A', s: 22 },
              { v: 1.15, l: 'A', s: 26 },
              { v: 1.3, l: 'A', s: 30 },
            ].map((o,i) => (
              <button key={i}
                style={{ ...mayorStyles.sizeBtn, fontSize: o.s,
                  background: textScale === o.v ? '#c96442' : '#fff',
                  color: textScale === o.v ? '#fff' : '#3d2f22' }}
                onClick={() => { setTextScale(o.v); setShowSize(false); }}>
                {o.l}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ────────── Conversation area ─────────── */}
      <div style={mayorStyles.chatArea}>
        <div style={mayorStyles.messages} ref={messagesRef}>
          {conv.map((m, i) => (
            <div key={i} style={{ ...mayorStyles.bubbleRow,
              justifyContent: m.who === 'usuario' ? 'flex-end' : 'flex-start' }}>
              {m.who === 'asistente' && (
                <div style={mayorStyles.avatarAsistente}>
                  <IconHeart/>
                </div>
              )}
              <div style={{
                ...mayorStyles.bubble,
                ...(m.who === 'usuario' ? mayorStyles.bubbleUser : mayorStyles.bubbleAssist),
                fontSize: fontSize(m.who === 'usuario' ? 22 : 24),
              }}>
                <div style={{ ...mayorStyles.whoLabel,
                  color: m.who === 'usuario' ? '#b85d3f' : '#5d8a7a' }}>
                  {m.who === 'usuario' ? 'Yo' : 'Aurora'}
                </div>
                <div style={{ lineHeight: 1.45 }}>{m.text}</div>
              </div>
              {m.who === 'usuario' && (
                <div style={mayorStyles.avatarUser}>MD</div>
              )}
            </div>
          ))}
          {speaking && (
            <div style={mayorStyles.bubbleRow}>
              <div style={mayorStyles.avatarAsistente}><IconHeart/></div>
              <div style={{ ...mayorStyles.bubble, ...mayorStyles.bubbleAssist,
                display: 'flex', alignItems: 'center', gap: 4, padding: '20px 28px' }}>
                <div style={{ ...mayorStyles.typingDot, animationDelay: '0s' }}/>
                <div style={{ ...mayorStyles.typingDot, animationDelay: '.2s' }}/>
                <div style={{ ...mayorStyles.typingDot, animationDelay: '.4s' }}/>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ────────── Bottom action bar — voice-first ─────────── */}
      <div style={mayorStyles.bottomBar}>
        <button style={mayorStyles.actionBtn} onClick={() => setShowCall(true)}>
          <div style={{ ...mayorStyles.actionIcon, background: '#fef0ed', color: '#c96442' }}>
            <IconPhone/>
          </div>
          <span style={mayorStyles.actionLabel}>Llamar<br/>a mi familia</span>
        </button>

        <button style={mayorStyles.actionBtn}>
          <div style={{ ...mayorStyles.actionIcon, background: '#f0ede2', color: '#7d6a48' }}>
            <IconMusic/>
          </div>
          <span style={mayorStyles.actionLabel}>Poner<br/>música</span>
        </button>

        {/* Big mic button — center */}
        <button style={{ ...mayorStyles.micBtn,
          background: listening ? '#b85d3f' : '#c96442',
          boxShadow: listening
            ? '0 0 0 14px rgba(201,100,66,.22), 0 0 0 28px rgba(201,100,66,.10)'
            : '0 12px 32px rgba(201,100,66,.35)',
          transform: listening ? 'scale(1.04)' : 'scale(1)',
        }} onClick={askVoice}>
          {listening ? (
            <div style={mayorStyles.waveWrap}>
              <span style={{ ...mayorStyles.waveBar, animationDelay: '0s' }}/>
              <span style={{ ...mayorStyles.waveBar, animationDelay: '.12s' }}/>
              <span style={{ ...mayorStyles.waveBar, animationDelay: '.24s' }}/>
              <span style={{ ...mayorStyles.waveBar, animationDelay: '.36s' }}/>
              <span style={{ ...mayorStyles.waveBar, animationDelay: '.48s' }}/>
            </div>
          ) : (
            <IconMic/>
          )}
          <div style={mayorStyles.micLabel}>
            {listening ? 'Le escucho…' : 'Pulse y hable'}
          </div>
        </button>

        <button style={mayorStyles.actionBtn}>
          <div style={{ ...mayorStyles.actionIcon, background: '#e8ede6', color: '#5d8a7a' }}>
            <IconPhoto/>
          </div>
          <span style={mayorStyles.actionLabel}>Ver mis<br/>fotos</span>
        </button>

        <button style={mayorStyles.actionBtn}>
          <div style={{ ...mayorStyles.actionIcon, background: '#f4ebe0', color: '#a06942' }}>
            <IconBook/>
          </div>
          <span style={mayorStyles.actionLabel}>Refrán<br/>o historia</span>
        </button>
      </div>

      {/* ────────── Caregiver overlay panel ─────────── */}
      {caregiverOpen && (
        <>
          <div style={mayorStyles.overlay} onClick={() => setCaregiverOpen(false)}/>
          <div style={mayorStyles.caregiverPanel}>
            <div style={mayorStyles.cgHeader}>
              <div>
                <div style={mayorStyles.cgKicker}>PANEL CUIDADOR</div>
                <div style={mayorStyles.cgTitle}>María Dolores · sesión activa</div>
              </div>
              <button style={mayorStyles.cgClose} onClick={() => setCaregiverOpen(false)}>×</button>
            </div>

            <div style={mayorStyles.cgSection}>
              <div style={mayorStyles.cgLabel}>Estado cognitivo</div>
              <div style={mayorStyles.cgGrid}>
                <CGStat label="MMSE" value="22" sub="EA leve"/>
                <CGStat label="Turnos" value={String(conv.length)} sub="esta sesión"/>
                <CGStat label="Latencia" value="4.1s" sub="dentro de norma"/>
                <CGStat label="Alarmas" value="0" sub="ninguna activa"/>
              </div>
            </div>

            <div style={mayorStyles.cgSection}>
              <div style={mayorStyles.cgLabel}>Estado emocional</div>
              <CGBar label="Fatiga" value={0.28} color="#c96442"/>
              <CGBar label="Ansiedad" value={0.18} color="#a06942"/>
              <CGBar label="Ánimo" value={0.72} color="#5d8a7a"/>
            </div>

            <div style={mayorStyles.cgSection}>
              <div style={mayorStyles.cgLabel}>Sugerir al asistente</div>
              <div style={{ display:'flex', flexWrap:'wrap', gap: 6 }}>
                {window.MOCK.actions.slice(0,8).map(a => (
                  <button key={a.id} style={{
                    ...mayorStyles.cgChip,
                    background: a.cat==='cult' ? '#f4ebe0' : a.cat==='test' ? '#fef0ed' : '#e8ede6',
                    color: a.cat==='cult' ? '#7d4a1f' : a.cat==='test' ? '#a64020' : '#3a5d50',
                  }}>{a.label}</button>
                ))}
              </div>
            </div>

            <div style={mayorStyles.cgSection}>
              <div style={mayorStyles.cgLabel}>Intereses revelados</div>
              <div style={{ display:'flex', flexWrap:'wrap', gap: 6 }}>
                {['Familia','Música popular','Sevilla','Cocina','Refranes'].map(t => (
                  <span key={t} style={mayorStyles.cgTag}>{t}</span>
                ))}
              </div>
            </div>

            <button style={mayorStyles.cgEndBtn}>Terminar sesión y guardar</button>
          </div>
        </>
      )}

      {/* ────────── Call family modal ─────────── */}
      {showCall && (
        <>
          <div style={mayorStyles.overlay} onClick={() => setShowCall(false)}/>
          <div style={mayorStyles.callModal}>
            <div style={mayorStyles.callTitle}>¿A quién quiere llamar?</div>
            <div style={mayorStyles.callList}>
              {[
                { name: 'Lucía', rel: 'Mi hija', initials: 'L' },
                { name: 'Javier', rel: 'Mi hijo', initials: 'J' },
                { name: 'Carmen', rel: 'Mi hermana', initials: 'C' },
              ].map(c => (
                <button key={c.name} style={mayorStyles.callRow} onClick={() => setShowCall(false)}>
                  <div style={mayorStyles.callAvatar}>{c.initials}</div>
                  <div style={{ flex: 1, textAlign: 'left' }}>
                    <div style={{ fontSize: 24, color: '#2a1f15', fontWeight: 600 }}>{c.name}</div>
                    <div style={{ fontSize: 17, color: '#7d6a55' }}>{c.rel}</div>
                  </div>
                  <div style={mayorStyles.callGo}><IconPhone/></div>
                </button>
              ))}
            </div>
            <button style={mayorStyles.callCancel} onClick={() => setShowCall(false)}>Volver</button>
          </div>
        </>
      )}
    </div>
  );
};

// ─── Caregiver helpers ─────────────────────────────────────────
const CGStat = ({ label, value, sub }) => (
  <div style={mayorStyles.cgStat}>
    <div style={mayorStyles.cgStatVal}>{value}</div>
    <div style={mayorStyles.cgStatLabel}>{label}</div>
    <div style={mayorStyles.cgStatSub}>{sub}</div>
  </div>
);
const CGBar = ({ label, value, color }) => (
  <div style={{ marginBottom: 10 }}>
    <div style={{ display:'flex', justifyContent:'space-between', fontSize: 12, color:'#7d6a55', marginBottom: 4 }}>
      <span>{label}</span>
      <span style={{ fontVariantNumeric:'tabular-nums' }}>{Math.round(value*100)}%</span>
    </div>
    <div style={{ height: 5, background:'#efe6d8', borderRadius: 3, overflow:'hidden' }}>
      <div style={{ width: `${value*100}%`, height: '100%', background: color, borderRadius: 3 }}/>
    </div>
  </div>
);

// ─── Iconos (stroke, no emoji) ──────────────────────────────────
const Icon = ({ children, size = 32 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{children}</svg>
);
const IconMic = () => <Icon size={48}><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3"/></Icon>;
const IconPhone = () => <Icon><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.37 1.9.72 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.35 1.85.59 2.81.72A2 2 0 0 1 22 16.92z"/></Icon>;
const IconMusic = () => <Icon><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></Icon>;
const IconPhoto = () => <Icon><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></Icon>;
const IconBook = () => <Icon><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5v14z"/><path d="M4 19.5A2.5 2.5 0 0 1 6.5 22H20"/></Icon>;
const IconHeart = () => <Icon size={22}><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></Icon>;
const IconShield = () => <Icon size={22}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></Icon>;
const IconText = () => <Icon size={22}><path d="M4 7V4h16v3M9 20h6M12 4v16"/></Icon>;

// ─── Styles ──────────────────────────────────────────────────────
const mayorStyles = {
  root: {
    position: 'absolute', inset: 0,
    background: '#fbf4e8',
    display: 'flex', flexDirection: 'column',
    fontFamily: '"Lexend", system-ui, sans-serif',
    color: '#2a1f15',
    overflow: 'hidden',
  },
  topbar: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end',
    padding: '24px 36px 18px', borderBottom: '1px solid #e8ddc8',
    flexShrink: 0,
  },
  greetingWrap: {},
  timeRow: { display:'flex', alignItems:'baseline', gap: 14 },
  bigTime: { fontSize: 36, fontWeight: 600, color:'#2a1f15', fontVariantNumeric:'tabular-nums' },
  dateLabel: { fontSize: 18, color:'#7d6a55' },
  greeting: { fontSize: 26, fontWeight: 500, color:'#3d2f22', marginTop: 4 },
  topbarActions: { display:'flex', gap: 10 },
  iconBtn: {
    width: 52, height: 52, borderRadius: 14, border: '1.5px solid #d8c9b1',
    background: '#fff', color: '#7d6a55',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    cursor: 'pointer',
  },
  sizePopover: {
    position: 'absolute', top: 92, right: 36, zIndex: 20,
    background: '#fff', borderRadius: 16, padding: 16,
    boxShadow: '0 12px 40px rgba(60,40,20,.18)',
    border: '1px solid #e8ddc8',
  },
  sizeBtn: {
    width: 56, height: 56, borderRadius: 12, border:'1.5px solid #d8c9b1',
    fontFamily:'inherit', fontWeight:600, cursor:'pointer',
  },

  // Chat
  chatArea: {
    flex: 1, minHeight: 0, position:'relative',
    background: 'radial-gradient(circle at 50% 30%, #fff8eb 0%, #fbf4e8 70%)',
  },
  messages: {
    position:'absolute', inset: 0, padding: '28px 80px',
    overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 18,
  },
  bubbleRow: { display: 'flex', alignItems: 'flex-end', gap: 12 },
  avatarAsistente: {
    width: 44, height: 44, borderRadius: '50%',
    background: '#e8ede6', color: '#5d8a7a',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    flexShrink: 0, marginBottom: 4,
  },
  avatarUser: {
    width: 44, height: 44, borderRadius: '50%',
    background: '#f4d9c8', color: '#a64020',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    flexShrink: 0, marginBottom: 4, fontSize: 16, fontWeight: 600,
  },
  bubble: {
    maxWidth: '70%', padding: '16px 22px', borderRadius: 22,
    lineHeight: 1.45,
  },
  bubbleUser: { background: '#fff', color: '#2a1f15', border: '1.5px solid #e8ddc8', borderBottomRightRadius: 6 },
  bubbleAssist: { background: '#5d8a7a', color: '#fff', borderBottomLeftRadius: 6 },
  whoLabel: { fontSize: 12, fontWeight: 600, marginBottom: 4, letterSpacing: '.04em', textTransform: 'uppercase', opacity: .8 },
  typingDot: { width: 10, height: 10, borderRadius: '50%', background:'#fff', animation: 'mayorBlink 1.2s infinite ease-in-out' },

  // Bottom bar
  bottomBar: {
    flexShrink: 0,
    padding: '22px 36px 30px',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    background: '#fff8eb',
    borderTop: '1px solid #e8ddc8',
    gap: 16,
  },
  actionBtn: {
    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
    background: 'transparent', border: 'none', cursor: 'pointer',
    padding: 6, color: '#3d2f22',
    fontFamily: 'inherit',
  },
  actionIcon: {
    width: 72, height: 72, borderRadius: 22,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  actionLabel: { fontSize: 16, lineHeight: 1.25, textAlign: 'center', fontWeight: 500 },
  micBtn: {
    width: 144, height: 144, borderRadius: '50%',
    border: 'none', color: '#fff', cursor: 'pointer',
    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
    gap: 4, transition: 'all .25s ease', fontFamily: 'inherit',
    flexShrink: 0,
  },
  micLabel: { fontSize: 14, fontWeight: 500, opacity: .95 },
  waveWrap: { display: 'flex', alignItems: 'center', gap: 5, height: 48 },
  waveBar: {
    width: 6, height: 32, background: '#fff', borderRadius: 3,
    animation: 'mayorWave 1s infinite ease-in-out',
  },

  // Caregiver
  overlay: { position: 'absolute', inset: 0, background: 'rgba(40,30,20,.25)', zIndex: 30 },
  caregiverPanel: {
    position: 'absolute', top: 0, right: 0, bottom: 0, width: 360,
    background: '#fff', zIndex: 31, padding: '22px 22px 28px',
    overflowY: 'auto', borderLeft: '1px solid #e8ddc8',
    fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
    color: '#2a1f15', fontSize: 13,
  },
  cgHeader: { display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom: 18 },
  cgKicker: { fontSize: 10, letterSpacing: '.14em', color:'#a08a6e', fontWeight: 600 },
  cgTitle: { fontSize: 17, fontWeight: 600, marginTop: 4 },
  cgClose: { width: 32, height: 32, border:'none', background:'#f4ebe0', borderRadius: 8, fontSize: 22, color:'#7d6a55', cursor:'pointer' },
  cgSection: { marginBottom: 20 },
  cgLabel: { fontSize: 10, textTransform:'uppercase', letterSpacing:'.1em', color:'#a08a6e', marginBottom: 10, fontWeight: 600 },
  cgGrid: { display:'grid', gridTemplateColumns:'1fr 1fr', gap: 8 },
  cgStat: { background:'#fbf4e8', borderRadius: 10, padding: '10px 12px' },
  cgStatVal: { fontSize: 22, fontWeight: 700, color:'#2a1f15', lineHeight: 1, fontVariantNumeric:'tabular-nums' },
  cgStatLabel: { fontSize: 11, color:'#7d6a55', marginTop: 4, fontWeight: 600 },
  cgStatSub: { fontSize: 10, color:'#a08a6e', marginTop: 2 },
  cgChip: {
    padding: '6px 10px', borderRadius: 99, fontSize: 12, fontWeight: 500,
    border: 'none', cursor: 'pointer', fontFamily: 'inherit',
  },
  cgTag: { padding:'3px 9px', borderRadius: 99, fontSize: 11, background:'#f4ebe0', color:'#7d4a1f', fontWeight: 500 },
  cgEndBtn: {
    width: '100%', padding: '11px', marginTop: 8,
    background: '#fff', border: '1.5px solid #d8c9b1', borderRadius: 10,
    color: '#7d6a55', fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', fontSize: 13,
  },

  // Call modal
  callModal: {
    position:'absolute', top:'50%', left:'50%', transform:'translate(-50%,-50%)',
    background:'#fff', borderRadius: 24, padding: 32, width: 500, zIndex: 32,
    boxShadow: '0 30px 80px rgba(40,30,20,.3)',
  },
  callTitle: { fontSize: 28, fontWeight: 600, color:'#2a1f15', marginBottom: 22 },
  callList: { display:'flex', flexDirection:'column', gap: 10 },
  callRow: {
    display: 'flex', alignItems: 'center', gap: 16, padding: 16,
    background:'#fbf4e8', border:'1.5px solid #e8ddc8', borderRadius: 16,
    cursor:'pointer', fontFamily: 'inherit',
  },
  callAvatar: {
    width: 56, height: 56, borderRadius: '50%',
    background: '#5d8a7a', color:'#fff', fontSize: 24, fontWeight: 600,
    display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0,
  },
  callGo: {
    width: 56, height: 56, borderRadius: '50%',
    background: '#c96442', color: '#fff',
    display:'flex', alignItems:'center', justifyContent:'center',
  },
  callCancel: {
    width:'100%', marginTop: 20, padding: '16px',
    background: 'transparent', border: '1.5px solid #d8c9b1', borderRadius: 14,
    color:'#7d6a55', fontSize: 20, cursor: 'pointer', fontFamily:'inherit', fontWeight: 500,
  },
};

window.MayorView = MayorView;

// screens-loop.jsx — Feed, Sleep, Farewell→Dex, Empty states

const LOOP_CLOVER = {
  baby: 'img/clover_baby.png',
  mid_a: 'img/clover_mid_a.png',
  mid_b: 'img/clover_mid_b.png',
  final_a: 'img/clover_final_a.png',
  final_b: 'img/clover_final_b.png',
};

// ─── ⑨ FEED — interactive feeding flow ──────────────────────────────────
function FeedScreen({ stage='select', food='cake', mood='happy' }) {
  // stages: select | drag | result
  const foods = [
    {id:'cookie', e:'🍪', n:'Small Food', xp:50, p:20},
    {id:'cake',   e:'🍰', n:'Big Food',   xp:150, p:50},
    {id:'bento',  e:'🍱', n:'Special',    xp:300, p:90},
  ];
  const sel = foods.find(f=>f.id===food) || foods[1];

  return (
    <div className="gi-screen zone-forest">
      <div className="gi-topbar">
        <div className="gi-topbar-left">
          <button className="gi-iconbtn">←</button>
          <div className="gi-h2" style={{fontSize:18}}>Feed Clover</div>
        </div>
        <div className="gi-topbar-right">
          <span className="gi-stat"><span className="ico">💎</span> 240</span>
        </div>
      </div>

      <div style={{flex:1, position:'relative', display:'flex', flexDirection:'column'}}>

        {/* Character stage */}
        <div style={{flex:1, position:'relative', display:'flex', alignItems:'center', justifyContent:'center'}}>
          {/* Ground shadow */}
          <div style={{position:'absolute', bottom:'34%', width:160, height:18, background:'rgba(58,106,84,.18)', borderRadius:'50%', filter:'blur(6px)'}}/>

          {/* Clover */}
          <div style={{position:'relative', display:'flex', flexDirection:'column', alignItems:'center'}}>
            <img src={LOOP_CLOVER.mid_a} style={{width:200, height:200, objectFit:'contain'}} className="float"/>
            {stage==='result' && (
              <div style={{position:'absolute', top:-10, left:'50%', transform:'translateX(-50%)', display:'flex', gap:6}}>
                {['💖','✨','💖'].map((s,i)=>(
                  <span key={i} style={{fontSize:22, animation:`float 2s ease ${i*0.2}s infinite`}}>{s}</span>
                ))}
              </div>
            )}
          </div>

          {/* Drag indicator */}
          {stage==='drag' && (
            <div style={{position:'absolute', top:'30%', left:'30%', display:'flex', alignItems:'center', gap:10}}>
              <div style={{fontSize:48, filter:'drop-shadow(0 4px 8px rgba(0,0,0,.15))'}}>{sel.e}</div>
              <svg width="120" height="40" viewBox="0 0 120 40">
                <path d="M 5 20 Q 60 5 110 20" stroke="var(--diary)" strokeWidth="2.5" fill="none" strokeDasharray="4 4"/>
                <polygon points="110,20 102,15 102,25" fill="var(--diary)"/>
              </svg>
            </div>
          )}

          {/* Lumi tip */}
          {stage==='select' && (
            <div className="paper" style={{position:'absolute', top:24, right:24, maxWidth:220, padding:'14px 16px'}}>
              <div className="gi-hand" style={{fontSize:20, color:'var(--rewards-ink)'}}>Pick a treat & drag it to Clover ✨</div>
              <div style={{position:'absolute', bottom:-6, left:30, width:14, height:14, background:'var(--bg-card)', borderLeft:'1px solid var(--border-subtle)', borderBottom:'1px solid var(--border-subtle)', transform:'rotate(-45deg)'}}/>
            </div>
          )}

          {/* Result toast */}
          {stage==='result' && (
            <div style={{position:'absolute', top:'18%', background:'var(--bg-card)', border:'2px solid var(--math)', borderRadius:20, padding:'14px 22px', boxShadow:'var(--shadow-modal)', textAlign:'center'}}>
              <div className="gi-hand" style={{fontSize:24, color:'var(--math-ink)'}}>Yum! +{sel.xp} XP</div>
              <div style={{fontSize:12, fontWeight:700, color:'var(--text-secondary)', marginTop:2}}>Hunger 100% · Friendship +5</div>
            </div>
          )}
        </div>

        {/* Mini gauge HUD */}
        <div style={{position:'absolute', top:14, left:20, right:20, display:'flex', gap:10, pointerEvents:'none'}}>
          <div style={{flex:1, background:'rgba(255,255,255,.85)', borderRadius:10, padding:'8px 12px', backdropFilter:'blur(4px)'}}>
            <div style={{fontSize:10, fontWeight:800, color:'var(--text-secondary)', textTransform:'uppercase', letterSpacing:.5}}>Hunger</div>
            <div className="gauge-bar" style={{marginTop:4}}>
              <i style={{width: stage==='result'?'100%':'40%', background:'linear-gradient(90deg,#F4B27E,#EBA98C)'}}/>
            </div>
          </div>
          <div style={{flex:1, background:'rgba(255,255,255,.85)', borderRadius:10, padding:'8px 12px', backdropFilter:'blur(4px)'}}>
            <div style={{fontSize:10, fontWeight:800, color:'var(--text-secondary)', textTransform:'uppercase', letterSpacing:.5}}>Friendship</div>
            <div className="gauge-bar" style={{marginTop:4}}>
              <i style={{width: stage==='result'?'77%':'72%', background:'linear-gradient(90deg,#F8C8D5,#E09AAE)'}}/>
            </div>
          </div>
        </div>

        {/* Food tray */}
        <div style={{background:'var(--bg-card)', borderTop:'1px solid var(--border-subtle)', padding:'16px 20px'}}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12}}>
            <div className="gi-h2" style={{fontSize:14}}>Your Food</div>
            <span style={{fontSize:12, color:'var(--text-secondary)', fontWeight:700}}>3 items</span>
          </div>
          <div style={{display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:10}}>
            {foods.map(f=>(
              <div key={f.id} className="shop-item" style={{
                padding:'12px 10px',
                borderColor: f.id===food ? 'var(--diary)' : 'var(--border-subtle)',
                borderWidth: f.id===food ? 2 : 1,
                background: f.id===food ? 'var(--diary-light)' : 'var(--bg-card)',
              }}>
                <div className="em" style={{fontSize:30}}>{f.e}</div>
                <div className="nm" style={{fontSize:12}}>{f.n}</div>
                <div style={{fontSize:11, color:'var(--text-secondary)', fontWeight:700}}>+{f.xp} XP</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── ⑩ SLEEP — night rest state ─────────────────────────────────────────
function SleepScreen({ phase='sleeping' }) {
  // phase: sleeping | wake
  return (
    <div className="gi-screen night" style={{background:'linear-gradient(180deg, #1A1827 0%, #2A2147 60%, #1A1B3A 100%)'}}>
      <div className="stars"/>

      {/* Moon */}
      <div style={{position:'absolute', top:40, right:60, width:64, height:64, borderRadius:'50%', background:'radial-gradient(circle at 35% 35%, #FFF6D9, #F2E2A8)', boxShadow:'0 0 40px rgba(255,246,217,.4)'}}/>

      <div className="gi-topbar" style={{background:'transparent', borderBottom:'none'}}>
        <div className="gi-topbar-left">
          <button className="gi-iconbtn" style={{background:'rgba(255,255,255,.08)', borderColor:'rgba(255,255,255,.15)', color:'#F2EDE2'}}>←</button>
          <div className="gi-h2" style={{fontSize:18, color:'#F2EDE2'}}>Forest · Night</div>
        </div>
        <div className="gi-topbar-right">
          <span className="gi-stat" style={{background:'rgba(184,164,220,.2)', color:'#DCCFEE'}}>🌙 22:14</span>
        </div>
      </div>

      <div style={{flex:1, position:'relative', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:24}}>

        {/* Sleeping clover */}
        <div style={{position:'relative', display:'flex', flexDirection:'column', alignItems:'center'}}>
          {/* Z's */}
          {phase==='sleeping' && (
            <div style={{position:'absolute', top:-30, right:-30, display:'flex', flexDirection:'column', gap:2}}>
              <span style={{fontSize:28, opacity:.9, color:'#DCCFEE', fontFamily:'var(--font-display)', fontWeight:800, transform:'translateX(20px)'}}>z</span>
              <span style={{fontSize:22, opacity:.7, color:'#DCCFEE', fontFamily:'var(--font-display)', fontWeight:800, transform:'translateX(8px)'}}>z</span>
              <span style={{fontSize:16, opacity:.5, color:'#DCCFEE', fontFamily:'var(--font-display)', fontWeight:800}}>z</span>
            </div>
          )}

          {/* Bed */}
          <div style={{width:240, height:80, background:'linear-gradient(180deg, #3A3750 0%, #2E2C42 100%)', borderRadius:'50%/40%', position:'relative', border:'1px solid rgba(220,207,238,.2)'}}>
            {/* Pillow / leaf bed */}
            <div style={{position:'absolute', inset:'10% 15%', background:'rgba(220,207,238,.15)', borderRadius:'50%'}}/>
          </div>
          <img src={LOOP_CLOVER.mid_a} style={{
            position:'absolute',
            width:140, height:140,
            objectFit:'contain',
            top:-50,
            transform: phase==='sleeping' ? 'rotate(-12deg)' : 'rotate(0)',
            filter: phase==='sleeping' ? 'brightness(.85)' : 'none',
          }} className={phase==='wake' ? 'float' : ''}/>
        </div>

        {/* Status text */}
        <div style={{textAlign:'center', maxWidth:400, padding:'0 30px'}}>
          {phase==='sleeping' ? (
            <>
              <div className="gi-h1" style={{fontSize:24, color:'#F2EDE2'}}>Clover is sleeping</div>
              <div className="gi-hand" style={{fontSize:22, color:'#DCCFEE', marginTop:8}}>Energy recovers while you're away ✨</div>
            </>
          ) : (
            <>
              <div className="gi-h1" style={{fontSize:24, color:'#F2EDE2'}}>Good morning!</div>
              <div className="gi-hand" style={{fontSize:22, color:'#F8C8D5', marginTop:8}}>Energy fully restored 💕</div>
            </>
          )}
        </div>

        {/* Energy bar */}
        <div style={{width:300, background:'rgba(255,255,255,.08)', borderRadius:14, padding:'14px 18px', border:'1px solid rgba(220,207,238,.15)'}}>
          <div style={{display:'flex', justifyContent:'space-between', marginBottom:6}}>
            <span style={{fontSize:11, fontWeight:800, color:'#B5ADC4', textTransform:'uppercase', letterSpacing:.5}}>⚡ Energy</span>
            <span style={{fontSize:11, fontWeight:800, color:'#F2EDE2'}}>{phase==='sleeping'?'62%':'100%'}</span>
          </div>
          <div className="gauge-bar" style={{background:'rgba(255,255,255,.1)'}}>
            <i style={{width: phase==='sleeping'?'62%':'100%', background:'linear-gradient(90deg,#B8A4DC,#F8C8D5)'}}/>
          </div>
          {phase==='sleeping' && (
            <div style={{fontSize:11, color:'#7E7891', marginTop:8, textAlign:'center', fontWeight:600}}>
              Wakes in 4h 12m · or tap to wake early
            </div>
          )}
        </div>

        {/* Action */}
        <button className="btn" style={{
          background: phase==='wake' ? 'var(--diary)' : 'rgba(255,255,255,.08)',
          borderColor: phase==='wake' ? 'var(--diary)' : 'rgba(220,207,238,.3)',
          color: phase==='wake' ? '#fff' : '#DCCFEE',
          minWidth:180,
        }}>
          {phase==='sleeping' ? '🔔 Wake gently' : '☀️ Start the day'}
        </button>
      </div>
    </div>
  );
}

// ─── ⑪ FAREWELL — character departs to dex ───────────────────────────────
function FarewellScreen({ stage='goodbye' }) {
  // stage: goodbye | flying | dex
  return (
    <div className="gi-screen" style={{background:'linear-gradient(180deg, #FBEEF2 0%, #F2ECFA 50%, #EEF4FA 100%)'}}>

      {/* Petals */}
      <div style={{position:'absolute', inset:0, pointerEvents:'none', overflow:'hidden'}}>
        {[...Array(12)].map((_,i)=>(
          <span key={i} style={{
            position:'absolute',
            left: `${(i*73)%100}%`,
            top: `${(i*41)%100}%`,
            fontSize: 14 + (i%3)*4,
            opacity: .5,
            animation: `float 4s ease ${i*0.3}s infinite`,
          }}>🌸</span>
        ))}
      </div>

      <div className="gi-topbar" style={{background:'transparent', borderBottom:'none'}}>
        <div className="gi-topbar-left">
          <div className="gi-h2" style={{fontSize:18, color:'var(--diary-ink)'}}>A goodbye letter</div>
        </div>
      </div>

      <div style={{flex:1, position:'relative', display:'flex', alignItems:'center', justifyContent:'center', padding:'10px 40px 30px'}}>

        {stage==='goodbye' && (
          <div style={{display:'flex', gap:32, alignItems:'center', maxWidth:760}}>
            {/* Clover floating away */}
            <div style={{position:'relative', flexShrink:0}}>
              <img src={LOOP_CLOVER.final_a} style={{width:200, height:200, objectFit:'contain'}} className="float"/>
              <div style={{position:'absolute', top:-10, left:-20, fontSize:22, opacity:.7}}>✨</div>
              <div style={{position:'absolute', bottom:0, right:-10, fontSize:18, opacity:.6}}>💫</div>
            </div>

            {/* Letter */}
            <div className="paper" style={{flex:1, padding:'32px 28px', maxWidth:380, transform:'rotate(-1.2deg)', boxShadow:'var(--shadow-modal)'}}>
              <div className="gi-hand" style={{fontSize:28, color:'var(--diary-ink)', lineHeight:1.3}}>Dear Gia,</div>
              <div style={{fontFamily:'var(--font-hand)', fontSize:20, color:'var(--text-primary)', lineHeight:1.5, marginTop:14}}>
                Thank you for raising me. I'll fly to the legendary forest now — but I'll always be in your dokgam ✨
              </div>
              <div className="gi-hand" style={{fontSize:22, color:'var(--diary-ink)', textAlign:'right', marginTop:18}}>— Clover 🍀</div>
              <div style={{position:'absolute', top:14, right:18, fontSize:11, fontWeight:700, color:'var(--text-hint)'}}>raised 14 days</div>
            </div>
          </div>
        )}

        {stage==='dex' && (
          <div style={{textAlign:'center', maxWidth:480}}>
            <div style={{fontSize:14, fontWeight:800, color:'var(--diary-ink)', textTransform:'uppercase', letterSpacing:1}}>Added to Collection</div>
            <div className="gi-h1" style={{fontSize:32, marginTop:6}}>Clover · Forest 04/12</div>

            <div style={{position:'relative', display:'inline-block', margin:'24px 0'}}>
              <div style={{position:'absolute', inset:-20, borderRadius:'50%', background:'radial-gradient(circle, rgba(238,199,112,.4), transparent 70%)'}}/>
              <div className="dex-card" style={{width:160, height:200, position:'relative', borderColor:'var(--arcade)', borderWidth:2}}>
                <img src={LOOP_CLOVER.final_a} style={{width:120, height:120, objectFit:'contain'}}/>
                <div style={{fontSize:13, fontWeight:800, marginTop:6}}>Clover</div>
                <div style={{fontSize:10, color:'var(--text-secondary)', fontWeight:700}}>Final · Path A</div>
                <div style={{position:'absolute', top:8, right:8, background:'var(--arcade)', color:'var(--arcade-ink)', fontSize:10, fontWeight:800, padding:'2px 8px', borderRadius:999}}>NEW</div>
              </div>
            </div>

            <div className="paper" style={{padding:'14px 20px', display:'inline-block', textAlign:'left'}}>
              <div style={{display:'flex', gap:24}}>
                <div>
                  <div style={{fontSize:10, fontWeight:800, color:'var(--text-secondary)', textTransform:'uppercase'}}>Reward</div>
                  <div style={{fontSize:18, fontWeight:800, color:'var(--rewards-ink)', marginTop:4}}>+1 ✨ Lumi</div>
                </div>
                <div>
                  <div style={{fontSize:10, fontWeight:800, color:'var(--text-secondary)', textTransform:'uppercase'}}>Bonus</div>
                  <div style={{fontSize:18, fontWeight:800, color:'var(--diary-ink)', marginTop:4}}>+50 💎</div>
                </div>
                <div>
                  <div style={{fontSize:10, fontWeight:800, color:'var(--text-secondary)', textTransform:'uppercase'}}>Dex</div>
                  <div style={{fontSize:18, fontWeight:800, color:'var(--math-ink)', marginTop:4}}>4/12</div>
                </div>
              </div>
            </div>

            <div style={{marginTop:24, display:'flex', gap:10, justifyContent:'center'}}>
              <button className="btn">📖 View dokgam</button>
              <button className="btn btn-primary">🌱 Raise next</button>
            </div>
          </div>
        )}
      </div>

      {stage==='goodbye' && (
        <div style={{position:'absolute', bottom:24, left:0, right:0, display:'flex', justifyContent:'center', gap:10}}>
          <button className="btn">Save letter</button>
          <button className="btn btn-primary">Say goodbye →</button>
        </div>
      )}
    </div>
  );
}

// ─── ⑫ EMPTY STATES ─────────────────────────────────────────────────────
function EmptyState({ kind='zone' }) {
  const variants = {
    zone: {
      bg: 'zone-forest',
      icon: '🌱',
      title: 'No friend here yet',
      sub: 'Visit the shop to find a seed, then plant a friend in this zone.',
      cta: '🛍️ Open shop',
      hand: 'Every legend starts with one little seed ✨',
    },
    inv: {
      bg: '',
      icon: '🧺',
      title: 'Your basket is empty',
      sub: 'Buy food, decor, or evolution stones from the shop to fill it.',
      cta: '🛍️ Browse shop',
      hand: "It's quiet in here…",
    },
    dex: {
      bg: '',
      icon: '📖',
      title: 'No memories yet',
      sub: 'When a friend completes their journey, they\'ll appear in your dokgam forever.',
      cta: '🌱 Start raising',
      hand: 'The first page is always the sweetest',
    },
    friends: {
      bg: '',
      icon: '🏝️',
      title: 'No island visits yet',
      sub: "Friends' islands will show up here once they share an invite code.",
      cta: '＋ Add a friend',
      hand: 'Better with company',
    },
  };
  const v = variants[kind] || variants.zone;

  return (
    <div className={'gi-screen ' + v.bg}>
      <div className="gi-topbar">
        <div className="gi-topbar-left">
          <button className="gi-iconbtn">←</button>
          <div className="gi-h2" style={{fontSize:18}}>
            {kind==='zone' && 'Forest Zone'}
            {kind==='inv' && 'Inventory'}
            {kind==='dex' && 'Collection'}
            {kind==='friends' && 'Friends'}
          </div>
        </div>
        <div className="gi-topbar-right">
          <span className="gi-stat"><span className="ico">💎</span> 240</span>
        </div>
      </div>

      <div style={{flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'40px 30px', textAlign:'center', position:'relative'}}>

        {/* Big icon in dotted circle */}
        <div style={{
          width:140, height:140, borderRadius:'50%',
          border:'2px dashed var(--border-default)',
          display:'flex', alignItems:'center', justifyContent:'center',
          fontSize:64,
          background: kind==='zone' ? 'rgba(255,255,255,.5)' : 'var(--bg-card)',
          marginBottom: 22,
        }} className="float">
          {v.icon}
        </div>

        <div className="gi-h1" style={{fontSize:24, marginBottom:8}}>{v.title}</div>
        <div style={{fontSize:14, color:'var(--text-secondary)', maxWidth:340, lineHeight:1.5, marginBottom:8}}>
          {v.sub}
        </div>
        <div className="gi-hand" style={{fontSize:20, color:'var(--rewards-ink)', marginBottom:24}}>
          {v.hand}
        </div>

        <button className="btn btn-primary" style={{minWidth:180}}>{v.cta}</button>

        {/* Decorative slots for inv/dex */}
        {kind==='dex' && (
          <div style={{display:'grid', gridTemplateColumns:'repeat(6, 1fr)', gap:8, marginTop:32, opacity:.4}}>
            {[...Array(12)].map((_,i)=>(
              <div key={i} className="dex-card silhouette" style={{width:64, height:78}}>
                <div className="em" style={{fontSize:22}}>?</div>
                <div className="name" style={{fontSize:9}}>???</div>
              </div>
            ))}
          </div>
        )}
        {kind==='inv' && (
          <div style={{display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:10, marginTop:24, opacity:.35}}>
            {[...Array(8)].map((_,i)=>(
              <div key={i} style={{width:64, height:64, border:'1.5px dashed var(--border-default)', borderRadius:12, background:'var(--bg-card)'}}/>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { FeedScreen, SleepScreen, FarewellScreen, EmptyState });

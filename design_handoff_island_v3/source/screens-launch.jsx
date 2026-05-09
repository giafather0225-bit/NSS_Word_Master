// screens-launch.jsx — Loading, Error/Offline, Push notifications, Tutorial coachmarks

const LAUNCH_CLOVER = {
  baby: 'img/clover_baby.png',
  mid_a: 'img/clover_mid_a.png',
  final_a: 'img/clover_final_a.png',
};

// ─── ⑰ LOADING / SPLASH ─────────────────────────────────────────────────
function LoadingScreen({ kind='splash', progress=42 }) {
  // kind: splash | sync | reconnect

  if (kind === 'splash') {
    return (
      <div style={{
        width:'100%', height:'100%',
        background:'linear-gradient(180deg, #FBEEF2 0%, #F2ECFA 50%, #EEF4FA 100%)',
        position:'relative', overflow:'hidden',
        display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
      }}>
        {/* Floating petals */}
        {[...Array(14)].map((_,i)=>(
          <span key={i} style={{
            position:'absolute',
            left:`${(i*73)%100}%`, top:`${(i*41)%100}%`,
            fontSize: 12+(i%3)*4, opacity:.45,
            animation:`float 4s ease ${i*0.2}s infinite`,
          }}>{['🌸','✨','🌿','💕'][i%4]}</span>
        ))}

        {/* Logo island */}
        <div style={{position:'relative', marginBottom:30}}>
          <div style={{
            width:140, height:140, borderRadius:'50%',
            background:'radial-gradient(circle at 35% 30%, #FFFFFF, var(--diary-light) 60%, var(--rewards-light))',
            boxShadow:'0 12px 40px rgba(224,154,174,.3)',
            display:'flex', alignItems:'center', justifyContent:'center',
            fontSize:80,
          }} className="float">🏝️</div>
          <div style={{position:'absolute', top:-8, right:-12, fontSize:32}} className="float">✨</div>
        </div>

        <div className="gi-h1" style={{fontSize:32, color:'var(--diary-ink)'}}>Gia's Island</div>
        <div className="gi-hand" style={{fontSize:24, color:'var(--rewards-ink)', marginTop:6}}>welcome home 💕</div>

        {/* Subtle loader dots */}
        <div style={{display:'flex', gap:6, marginTop:40}}>
          {[0,1,2].map(i=>(
            <div key={i} style={{
              width:8, height:8, borderRadius:'50%',
              background:'var(--diary)',
              animation:`pulse-glow 1.4s ease ${i*.2}s infinite`,
            }}/>
          ))}
        </div>

        <div style={{position:'absolute', bottom:24, fontSize:11, color:'var(--text-hint)', fontWeight:600}}>v1.0.4</div>
      </div>
    );
  }

  if (kind === 'sync') {
    return (
      <div className="gi-screen" style={{justifyContent:'center', alignItems:'center'}}>
        <div style={{textAlign:'center', maxWidth:300, padding:30}}>
          <div style={{position:'relative', display:'inline-block', marginBottom:20}}>
            <img src={LAUNCH_CLOVER.baby} style={{width:120, height:120, objectFit:'contain'}} className="float"/>
            <div style={{position:'absolute', top:-10, right:-20, fontSize:22}}>💭</div>
          </div>
          <div className="gi-h2" style={{fontSize:18}}>Syncing your island…</div>

          {/* Progress bar */}
          <div style={{marginTop:20, background:'var(--bg-surface)', borderRadius:999, height:8, overflow:'hidden', position:'relative'}}>
            <div style={{
              width:progress+'%', height:'100%',
              background:'linear-gradient(90deg, var(--diary), var(--rewards-primary, #B8A4DC))',
              borderRadius:999,
              transition:'width .4s ease',
            }}/>
          </div>
          <div style={{display:'flex', justifyContent:'space-between', marginTop:8, fontSize:11, color:'var(--text-secondary)', fontWeight:700}}>
            <span>Restoring last visit</span>
            <span>{progress}%</span>
          </div>

          <div className="gi-hand" style={{fontSize:18, color:'var(--rewards-ink)', marginTop:24}}>Clover is waiting for you ✨</div>
        </div>
      </div>
    );
  }

  // reconnect
  return (
    <div className="gi-screen" style={{justifyContent:'center', alignItems:'center'}}>
      <div style={{
        background:'var(--bg-card)', border:'1px solid var(--border-subtle)',
        borderRadius:'var(--r-2xl)', padding:'24px 28px',
        boxShadow:'var(--shadow-modal)',
        display:'flex', alignItems:'center', gap:16,
      }}>
        <div style={{
          width:42, height:42, borderRadius:'50%',
          border:'3px solid var(--bg-surface)',
          borderTopColor:'var(--diary)',
          animation:'spin 1s linear infinite',
        }}/>
        <div>
          <div style={{fontSize:14, fontWeight:800}}>Reconnecting…</div>
          <div style={{fontSize:12, color:'var(--text-secondary)', fontWeight:600}}>Hang tight, we'll be back</div>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

// ─── ⑱ ERROR / OFFLINE ─────────────────────────────────────────────────
function ErrorScreen({ kind='offline' }) {
  const variants = {
    offline: {
      icon:'🌫️', title:'You\'re offline', sub:"We can't reach the island right now. Check your connection and try again.",
      hand:'The island will wait for you 💕', cta:'Try again', alt:'Continue offline',
    },
    server: {
      icon:'🛠️', title:'Something went wrong', sub:'Our servers had a hiccup. Give it a moment and try again — your progress is safe.',
      hand:'Not your fault, promise!', cta:'Try again', alt:'Report a bug',
    },
    update: {
      icon:'✨', title:'A new version is ready', sub:'Update to the latest version to keep playing. Your progress is saved.',
      hand:'New goodies inside!', cta:'Update now', alt:'Later',
    },
    maintenance: {
      icon:'🌙', title:'Under maintenance', sub:'We\'re tidying up the island. Back online around 03:00 KST.',
      hand:'See you soon ✨', cta:'Notify me', alt:null,
    },
  };
  const v = variants[kind];

  return (
    <div className="gi-screen" style={{background:'linear-gradient(180deg, var(--bg-page) 0%, var(--diary-light) 100%)'}}>
      <div style={{flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'40px 32px', textAlign:'center'}}>

        {/* Icon */}
        <div style={{
          width:140, height:140, borderRadius:'50%',
          background:'var(--bg-card)',
          border:'2px dashed var(--border-default)',
          display:'flex', alignItems:'center', justifyContent:'center',
          fontSize:64,
          marginBottom:24,
        }} className="float">{v.icon}</div>

        <div className="gi-h1" style={{fontSize:26, marginBottom:8}}>{v.title}</div>
        <div style={{fontSize:14, color:'var(--text-secondary)', maxWidth:340, lineHeight:1.5, marginBottom:8}}>{v.sub}</div>
        <div className="gi-hand" style={{fontSize:20, color:'var(--rewards-ink)', marginBottom:26}}>{v.hand}</div>

        <div style={{display:'flex', flexDirection:'column', gap:8, width:'100%', maxWidth:280}}>
          <button className="btn btn-primary" style={{minHeight:48}}>{v.cta}</button>
          {v.alt && <button className="btn btn-ghost">{v.alt}</button>}
        </div>

        {kind==='offline' && (
          <div style={{marginTop:30, padding:'12px 16px', background:'var(--bg-card)', borderRadius:'var(--r-md)', display:'flex', alignItems:'center', gap:10, border:'1px solid var(--border-subtle)'}}>
            <span style={{width:8, height:8, borderRadius:'50%', background:'#D97A7A', animation:'pulse-glow 2s ease infinite'}}/>
            <span style={{fontSize:12, fontWeight:700, color:'var(--text-secondary)'}}>No connection · last synced 12m ago</span>
          </div>
        )}

        {kind==='maintenance' && (
          <div style={{marginTop:24, padding:'10px 16px', background:'rgba(184,164,220,.18)', borderRadius:999, fontSize:12, fontWeight:800, color:'var(--rewards-ink)'}}>
            ⏰ Estimated 2h 14m
          </div>
        )}
      </div>
    </div>
  );
}

// ─── ⑲ PUSH NOTIFICATIONS — iPhone lock screen mock ─────────────────────
function PushNotifScreen({ scenario='hungry' }) {
  const notifs = {
    hungry: [
      {time:'now', title:'Lumi 🌙', body:'Clover hasn\'t eaten in a while and is feeling a bit hungry 🥺'},
    ],
    evolution: [
      {time:'now', title:'Lumi 🌙', body:'✨ Clover is ready to evolve! Come visit the Forest.'},
    ],
    streak: [
      {time:'9:00 PM', title:'Lumi 🌙', body:'Your 4-day streak ends in 3h — pop in for ✨ 1 Lumi'},
    ],
    multiple: [
      {time:'now', title:'Lumi 🌙', body:'Mina sent you a Mushroom Lantern 🍄'},
      {time:'5m ago', title:'Lumi 🌙', body:'Daily missions reset in 1h — claim your rewards!'},
      {time:'2h ago', title:'Lumi 🌙', body:'Clover wants to play 💕'},
    ],
  };
  const list = notifs[scenario];

  return (
    <IOSDevice width={390} height={780} dark={true} hideHomeIndicator={false}>
      {/* Lock screen wallpaper — soft gradient */}
      <div style={{
        position:'absolute', inset:0,
        background:'linear-gradient(180deg, #2A2147 0%, #1A1B3A 60%, #0F1029 100%)',
      }}>
        {/* Stars */}
        <div className="stars" style={{position:'absolute', inset:0}}/>

        {/* Time */}
        <div style={{position:'absolute', top:80, left:0, right:0, textAlign:'center', color:'#fff'}}>
          <div style={{fontSize:14, fontWeight:600, opacity:.85}}>Friday, May 1</div>
          <div style={{fontSize:88, fontWeight:200, lineHeight:1, marginTop:4, letterSpacing:'-2px', fontFamily:'-apple-system, "SF Pro Display", system-ui'}}>9:41</div>
        </div>

        {/* Notification stack */}
        <div style={{position:'absolute', top:260, left:14, right:14, display:'flex', flexDirection:'column', gap:8}}>
          {list.length > 1 && (
            <div style={{textAlign:'center', color:'rgba(255,255,255,.6)', fontSize:11, fontWeight:700, marginBottom:2}}>
              Notification Center · {list.length}
            </div>
          )}
          {list.map((n,i)=>(
            <div key={i} style={{
              background:'rgba(40,40,50,.55)',
              backdropFilter:'blur(20px)',
              WebkitBackdropFilter:'blur(20px)',
              borderRadius:18,
              padding:'12px 14px',
              display:'flex', gap:10,
              transform: list.length>1 ? `scale(${1 - i*0.04}) translateY(${i*-4}px)` : 'none',
              transformOrigin:'top center',
              opacity: list.length>1 ? 1 - i*0.15 : 1,
            }}>
              {/* App icon */}
              <div style={{
                width:38, height:38, borderRadius:9,
                background:'linear-gradient(135deg, #FBEEF2, #B8A4DC)',
                display:'flex', alignItems:'center', justifyContent:'center',
                fontSize:22, flexShrink:0,
              }}>🏝️</div>
              <div style={{flex:1, minWidth:0, color:'#fff'}}>
                <div style={{display:'flex', justifyContent:'space-between', alignItems:'baseline', gap:8}}>
                  <div style={{fontSize:13, fontWeight:700}}>Gia's Island</div>
                  <div style={{fontSize:11, opacity:.6, flexShrink:0}}>{n.time}</div>
                </div>
                <div style={{fontSize:13, fontWeight:600, marginTop:2}}>{n.title}</div>
                <div style={{fontSize:13, opacity:.85, marginTop:1, lineHeight:1.35}}>{n.body}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Flashlight + camera quick actions */}
        <div style={{position:'absolute', bottom:46, left:0, right:0, display:'flex', justifyContent:'space-between', padding:'0 36px'}}>
          <div style={{width:44, height:44, borderRadius:'50%', background:'rgba(255,255,255,.12)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:18}}>🔦</div>
          <div style={{width:44, height:44, borderRadius:'50%', background:'rgba(255,255,255,.12)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:18}}>📷</div>
        </div>
      </div>
    </IOSDevice>
  );
}

// ─── ⑳ TUTORIAL COACHMARKS — overlay tooltips on real UI ────────────────
function CoachmarkScreen({ step=1 }) {
  // Mocks the Map screen with a coachmark overlay highlighting one element

  const coachmarks = {
    1: {
      title:'Tap a zone to enter',
      body:'Each zone has its own friend. Forest is where Clover lives.',
      target: {left:'18%', top:'44%', size:160, shape:'circle'},
      arrow: {dir:'down-right', from:{left:'42%', top:'58%'}},
      tip: {left:'45%', top:'62%'},
      stepLabel:'1 of 4',
    },
    2: {
      title:'Your Lumi balance',
      body:'Earn Lumi by caring for friends. Spend them on food, evolution stones, and decor.',
      target: {left:'28px', top:'14px', width:90, height:32, shape:'pill'},
      arrow: {dir:'up-left', from:{left:'130px', top:'80px'}},
      tip: {left:'90px', top:'90px'},
      stepLabel:'2 of 4',
    },
    3: {
      title:'Daily streak',
      body:'Visit every day to keep your streak going. Day 7 has a big surprise!',
      target: {right:'24px', bottom:'24px', width:120, height:80, shape:'rect'},
      arrow: {dir:'down-right', from:{right:'160px', bottom:'130px'}},
      tip: {right:'180px', bottom:'140px'},
      stepLabel:'3 of 4',
    },
    4: {
      title:'You\'re all set!',
      body:'Tap anywhere to start raising Clover. Lumi will guide you along the way 🌙',
      target: null, // centered final
      tip: {left:'50%', top:'50%', center:true},
      stepLabel:'4 of 4',
      isFinal: true,
    },
  };
  const cm = coachmarks[step];

  // Fake map background
  const FakeMap = () => (
    <div style={{
      position:'absolute', inset:0,
      background:'linear-gradient(160deg, #CFE6D9 0%, #C7DDEF 60%, #F1DCA5 100%)',
    }}>
      {/* Top bar */}
      <div style={{position:'absolute', top:0, left:0, right:0, padding:'12px 18px', display:'flex', justifyContent:'space-between', alignItems:'center', background:'rgba(255,255,255,.85)', backdropFilter:'blur(8px)', borderBottom:'1px solid var(--border-subtle)'}}>
        <div style={{display:'flex', gap:8}}>
          <span className="gi-stat gi-stat--lumi">✨ 3</span>
          <span className="gi-stat"><span className="ico">💎</span> 240</span>
          <span className="gi-stat gi-stat--streak">🔥 4</span>
        </div>
        <div style={{display:'flex', gap:6}}>
          <button className="gi-iconbtn">🎒</button>
          <button className="gi-iconbtn">📖</button>
          <button className="gi-iconbtn">⚙️</button>
        </div>
      </div>

      {/* Fake zone hotspots */}
      <div style={{position:'absolute', left:'18%', top:'44%', transform:'translate(-50%,-50%)', width:140, height:140, borderRadius:'50%', border:'3px solid var(--math)', background:'radial-gradient(circle, rgba(255,255,255,.4), transparent 70%)', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center'}}>
          <span style={{fontSize:36}}>🌳</span>
          <span style={{fontSize:12, fontWeight:800, color:'var(--math-ink)', marginTop:4}}>Forest</span>
      </div>
      <div style={{position:'absolute', left:'58%', top:'30%', transform:'translate(-50%,-50%)', width:110, height:110, borderRadius:'50%', border:'3px solid var(--rewards-primary, #B8A4DC)', background:'radial-gradient(circle, rgba(255,255,255,.4), transparent 70%)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:32}}>🚀</div>
      <div style={{position:'absolute', left:'80%', top:'58%', transform:'translate(-50%,-50%)', width:120, height:120, borderRadius:'50%', border:'3px solid var(--english, #7FA8CC)', background:'radial-gradient(circle, rgba(255,255,255,.4), transparent 70%)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:32}}>🌊</div>

      {/* Bottom-right Today panel */}
      <div style={{position:'absolute', right:24, bottom:24, width:120, height:80, background:'rgba(255,255,255,.92)', backdropFilter:'blur(8px)', borderRadius:14, padding:'10px 12px', boxShadow:'var(--shadow-soft)'}}>
        <div style={{fontSize:10, fontWeight:800, color:'var(--text-secondary)', textTransform:'uppercase'}}>Streak</div>
        <div style={{display:'flex', gap:4, marginTop:6}}>
          {[1,1,1,1,0,0,0].map((on,i)=>(
            <div key={i} style={{width:10, height:10, borderRadius:'50%', background: on?'var(--arcade)':'var(--bg-surface)', border:'1.5px solid '+(on?'#D8AE55':'var(--border-default)')}}/>
          ))}
        </div>
        <div style={{fontSize:11, fontWeight:800, color:'var(--arcade-ink)', marginTop:4}}>🔥 4 days</div>
      </div>
    </div>
  );

  // Spotlight cutout
  const Spotlight = () => {
    if (!cm.target) {
      return <div style={{position:'absolute', inset:0, background:'rgba(43,39,34,.65)', backdropFilter:'blur(2px)'}}/>;
    }
    const t = cm.target;
    const isCircle = t.shape === 'circle';
    const isPill = t.shape === 'pill';
    const radius = isCircle ? '50%' : isPill ? '999px' : '14px';
    const w = isCircle ? t.size : t.width;
    const h = isCircle ? t.size : t.height;

    return (
      <>
        {/* Dark overlay */}
        <div style={{position:'absolute', inset:0, background:'rgba(43,39,34,.7)'}}/>
        {/* Cutout via mask — using box-shadow trick */}
        <div style={{
          position:'absolute',
          left: t.left, top: t.top, right: t.right, bottom: t.bottom,
          width: w, height: h,
          borderRadius: radius,
          transform: t.left==='18%' ? 'translate(-50%,-50%)' : 'none',
          boxShadow:'0 0 0 9999px rgba(43,39,34,.7)',
          border:'2px solid var(--diary)',
          animation:'pulse-glow 2s ease infinite',
          pointerEvents:'none',
        }}/>
      </>
    );
  };

  return (
    <div style={{width:'100%', height:'100%', position:'relative', overflow:'hidden', fontFamily:'var(--font-body)'}}>
      <FakeMap/>
      <Spotlight/>

      {/* Tip card */}
      <div style={{
        position:'absolute',
        left: cm.tip.left, top: cm.tip.top, right: cm.tip.right, bottom: cm.tip.bottom,
        transform: cm.tip.center ? 'translate(-50%,-50%)' : 'none',
        background:'var(--bg-card)',
        borderRadius:'var(--r-lg)',
        padding:'18px 20px',
        boxShadow:'var(--shadow-modal)',
        maxWidth:280,
        zIndex:10,
      }}>
        {!cm.isFinal && (
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:6}}>
            <span style={{fontSize:11, fontWeight:800, color:'var(--diary-ink)', textTransform:'uppercase', letterSpacing:.5}}>{cm.stepLabel}</span>
            <button style={{background:'none', border:'none', fontSize:11, fontWeight:700, color:'var(--text-hint)', cursor:'pointer'}}>Skip tour</button>
          </div>
        )}

        {cm.isFinal && (
          <div style={{fontSize:36, textAlign:'center', marginBottom:6}}>🌙</div>
        )}

        <div className="gi-h2" style={{fontSize:16, marginBottom:6, textAlign: cm.isFinal?'center':'left'}}>{cm.title}</div>
        <div style={{fontSize:13, color:'var(--text-secondary)', lineHeight:1.5, textAlign: cm.isFinal?'center':'left'}}>{cm.body}</div>

        {/* Step dots */}
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:14}}>
          <div style={{display:'flex', gap:4}}>
            {[1,2,3,4].map(i=>(
              <div key={i} style={{
                width: i===step?20:6, height:6, borderRadius:999,
                background: i===step?'var(--diary)': i<step?'var(--diary-soft)':'var(--bg-surface)',
                transition:'width .2s',
              }}/>
            ))}
          </div>
          <button className="btn btn-primary" style={{minHeight:32, padding:'6px 16px', fontSize:13}}>
            {cm.isFinal ? 'Start playing →' : 'Next'}
          </button>
        </div>
      </div>

      {/* Hand-drawn arrow (Caveat) */}
      {cm.arrow && (
        <div style={{
          position:'absolute',
          left: cm.arrow.from.left, top: cm.arrow.from.top,
          right: cm.arrow.from.right, bottom: cm.arrow.from.bottom,
          fontSize:20, color:'var(--diary)',
          fontFamily:'var(--font-hand)', fontWeight:700,
          pointerEvents:'none',
        }}>
          {cm.arrow.dir==='down-right' && '↘'}
          {cm.arrow.dir==='up-left' && '↖'}
        </div>
      )}
    </div>
  );
}

Object.assign(window, { LoadingScreen, ErrorScreen, PushNotifScreen, CoachmarkScreen });

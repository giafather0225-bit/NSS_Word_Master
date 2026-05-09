// screens-extra.jsx — Onboarding flow, Evolution sequence, Photo capture, Toast system

const EX_CLOVER = {
  baby: 'img/clover_baby.png',
  mid_a: 'img/clover_mid_a.png',
  final_a: 'img/clover_final_a.png',
};

// ─── ㉑ ONBOARDING FULL FLOW ──────────────────────────────────────────────
function OnboardingFlow({ step=1 }) {
  // step: 1 welcome | 2 nickname | 3 pick-friend | 4 first-feed | 5 done

  const Wrap = ({children, bg}) => (
    <div style={{
      width:'100%', height:'100%',
      background: bg || 'linear-gradient(180deg, #FBEEF2 0%, #F2ECFA 60%, #EEF4FA 100%)',
      position:'relative', overflow:'hidden',
      display:'flex', flexDirection:'column',
      fontFamily:'var(--font-body)',
    }}>
      {/* Step indicator */}
      <div style={{padding:'18px 22px', display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <button style={{background:'none', border:'none', fontSize:13, fontWeight:700, color:'var(--text-secondary)', cursor:'pointer', visibility: step>1?'visible':'hidden'}}>← Back</button>
        <div style={{display:'flex', gap:5}}>
          {[1,2,3,4,5].map(i=>(
            <div key={i} style={{
              width: i===step?22:6, height:6, borderRadius:999,
              background: i<=step ? 'var(--diary)' : 'var(--bg-surface)',
              transition:'width .25s',
            }}/>
          ))}
        </div>
        <button style={{background:'none', border:'none', fontSize:12, fontWeight:700, color:'var(--text-hint)', cursor:'pointer'}}>Skip</button>
      </div>
      {children}
    </div>
  );

  if (step === 1) return (
    <Wrap>
      <div style={{flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'0 32px', textAlign:'center'}}>
        <div style={{position:'relative', marginBottom:28}}>
          <div style={{width:160, height:160, borderRadius:'50%', background:'radial-gradient(circle at 35% 30%, #FFFFFF, var(--diary-light) 60%, var(--rewards-light))', boxShadow:'0 12px 40px rgba(224,154,174,.3)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:90}} className="float">🏝️</div>
          <div style={{position:'absolute', top:-10, right:-14, fontSize:36}} className="float">✨</div>
        </div>
        <div className="gi-h1" style={{fontSize:30, marginBottom:8}}>Welcome to Gia's Island</div>
        <div className="gi-hand" style={{fontSize:22, color:'var(--rewards-ink)', marginBottom:14}}>a quiet little place to come home to</div>
        <div style={{fontSize:14, color:'var(--text-secondary)', maxWidth:300, lineHeight:1.5, marginBottom:36}}>Raise tiny friends, write small diaries, and find a rhythm of your own.</div>
        <button className="btn btn-primary" style={{minHeight:50, padding:'0 36px', fontSize:15}}>Begin →</button>
      </div>
    </Wrap>
  );

  if (step === 2) return (
    <Wrap>
      <div style={{flex:1, padding:'20px 32px', display:'flex', flexDirection:'column'}}>
        <div className="gi-h1" style={{fontSize:24, marginBottom:6}}>What should we call you?</div>
        <div style={{fontSize:13, color:'var(--text-secondary)', marginBottom:24}}>Your friends will use this name in their diaries.</div>

        <div style={{display:'flex', gap:14, alignItems:'center', marginBottom:18}}>
          <div style={{width:64, height:64, borderRadius:'50%', background:'var(--bg-card)', border:'2px dashed var(--border-default)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:30}}>👤</div>
          <div style={{flex:1}}>
            <div style={{fontSize:11, fontWeight:800, color:'var(--text-secondary)', textTransform:'uppercase', letterSpacing:.5, marginBottom:4}}>Nickname</div>
            <div style={{background:'var(--bg-card)', border:'2px solid var(--diary)', borderRadius:12, padding:'12px 14px', fontSize:16, fontWeight:700}}>
              Mina<span style={{color:'var(--diary)', animation:'pulse-glow 1s ease infinite'}}>|</span>
            </div>
          </div>
        </div>

        <div style={{display:'flex', flexWrap:'wrap', gap:6, marginBottom:'auto'}}>
          {['Mina','Bori','Kirby','Tofu','Mochi'].map(n=>(
            <button key={n} style={{padding:'6px 12px', borderRadius:999, border:'1px solid var(--border-default)', background:'var(--bg-card)', fontSize:12, fontWeight:700, color:'var(--text-secondary)', cursor:'pointer'}}>{n}</button>
          ))}
          <button style={{padding:'6px 12px', borderRadius:999, border:'1px dashed var(--border-default)', background:'transparent', fontSize:12, fontWeight:700, color:'var(--text-hint)', cursor:'pointer'}}>🎲 random</button>
        </div>

        <div style={{padding:'10px 14px', background:'rgba(184,164,220,.15)', borderRadius:12, fontSize:12, color:'var(--rewards-ink)', fontWeight:600, marginBottom:18}}>
          ✨ You can change this anytime in Settings
        </div>
        <button className="btn btn-primary" style={{minHeight:48}}>Continue</button>
      </div>
    </Wrap>
  );

  if (step === 3) return (
    <Wrap>
      <div style={{flex:1, padding:'20px 24px', display:'flex', flexDirection:'column'}}>
        <div className="gi-h1" style={{fontSize:22, marginBottom:6}}>Choose your first friend</div>
        <div style={{fontSize:13, color:'var(--text-secondary)', marginBottom:20}}>You'll meet others as you explore. This one's just for now.</div>

        <div style={{display:'flex', flexDirection:'column', gap:12, marginBottom:'auto'}}>
          {[
            {name:'Clover', zone:'Forest', color:'#7BB17F', img:EX_CLOVER.baby, desc:'gentle · loves naps', selected:true},
            {name:'Pip',    zone:'Ocean',  color:'#7FA8CC', img:null, desc:'curious · always damp'},
            {name:'Nova',   zone:'Space',  color:'#B8A4DC', img:null, desc:'sparkly · easily dazzled'},
          ].map((f,i)=>(
            <div key={i} style={{
              display:'flex', gap:14, padding:14, borderRadius:16,
              background: f.selected?'var(--bg-card)':'transparent',
              border: f.selected?'2px solid '+f.color:'2px solid var(--border-subtle)',
              boxShadow: f.selected?'0 4px 16px rgba(0,0,0,.06)':'none',
              cursor:'pointer', position:'relative',
            }}>
              {f.selected && <div style={{position:'absolute', top:8, right:8, width:22, height:22, borderRadius:'50%', background:f.color, color:'#fff', display:'flex', alignItems:'center', justifyContent:'center', fontSize:13}}>✓</div>}
              <div style={{width:64, height:64, borderRadius:14, background:f.color+'30', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, overflow:'hidden'}}>
                {f.img ? <img src={f.img} style={{width:56, height:56, objectFit:'contain'}}/> : <span style={{fontSize:34, opacity:.4}}>?</span>}
              </div>
              <div style={{flex:1}}>
                <div style={{display:'flex', alignItems:'baseline', gap:8, marginBottom:2}}>
                  <div style={{fontSize:16, fontWeight:800}}>{f.name}</div>
                  <div style={{fontSize:11, fontWeight:800, color:f.color, padding:'2px 8px', borderRadius:999, background:f.color+'20'}}>{f.zone}</div>
                </div>
                <div className="gi-hand" style={{fontSize:16, color:'var(--text-secondary)'}}>{f.desc}</div>
              </div>
            </div>
          ))}
        </div>

        <button className="btn btn-primary" style={{minHeight:48, marginTop:14}}>Meet Clover →</button>
      </div>
    </Wrap>
  );

  if (step === 4) return (
    <Wrap bg="linear-gradient(180deg, #E8F2E8 0%, #CFE6D9 100%)">
      <div style={{flex:1, padding:'20px 28px', display:'flex', flexDirection:'column', alignItems:'center', textAlign:'center'}}>
        <div className="gi-h1" style={{fontSize:22, marginBottom:6}}>Try giving Clover a snack</div>
        <div className="gi-hand" style={{fontSize:18, color:'var(--rewards-ink)', marginBottom:24}}>tap the apple, then tap Clover 🌱</div>

        <div style={{flex:1, position:'relative', width:'100%', display:'flex', alignItems:'center', justifyContent:'center'}}>
          {/* Clover */}
          <img src={EX_CLOVER.baby} style={{width:160, height:160, objectFit:'contain'}} className="float"/>
          {/* Lumi */}
          <div style={{position:'absolute', top:'10%', right:'8%', width:60, height:60, borderRadius:'50%', background:'rgba(255,255,255,.8)', backdropFilter:'blur(6px)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:32}}>🌙</div>
          {/* Speech bubble */}
          <div style={{position:'absolute', top:'14%', left:'8%', maxWidth:180, background:'var(--bg-card)', borderRadius:14, padding:'10px 12px', fontSize:12, fontWeight:600, color:'var(--text-primary)', boxShadow:'var(--shadow-soft)'}}>
            <span className="gi-hand" style={{fontSize:14}}>This is Lumi — your guide ✨</span>
          </div>
          {/* Sparkles around apple */}
          <div style={{position:'absolute', bottom:30, left:'50%', transform:'translateX(-50%)', width:80, height:80, borderRadius:'50%', background:'radial-gradient(circle, rgba(255,200,100,.4), transparent 70%)', animation:'pulse-glow 1.5s ease infinite'}}/>
        </div>

        {/* Action tray */}
        <div style={{width:'100%', background:'var(--bg-card)', borderRadius:'var(--r-2xl)', padding:14, boxShadow:'var(--shadow-soft)'}}>
          <div style={{fontSize:11, fontWeight:800, color:'var(--text-secondary)', textTransform:'uppercase', letterSpacing:.5, marginBottom:8, textAlign:'left'}}>Inventory</div>
          <div style={{display:'flex', gap:10, justifyContent:'center'}}>
            <div style={{width:64, height:64, borderRadius:14, background:'#FFE5C2', border:'2px solid #D9A055', display:'flex', alignItems:'center', justifyContent:'center', fontSize:32, position:'relative', animation:'pulse-glow 1.5s ease infinite'}}>
              🍎
              <div style={{position:'absolute', bottom:-6, right:-6, background:'var(--diary)', color:'#fff', fontSize:10, fontWeight:800, padding:'2px 6px', borderRadius:999}}>×3</div>
            </div>
          </div>
        </div>
      </div>
    </Wrap>
  );

  // step 5 — done
  return (
    <Wrap bg="linear-gradient(180deg, #FFF7E8 0%, #FBEEF2 100%)">
      <div style={{flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:'0 32px', textAlign:'center'}}>
        {/* Burst */}
        <div style={{position:'relative', marginBottom:24}}>
          <div style={{position:'absolute', inset:-30, border:'2px dashed var(--diary)', borderRadius:'50%', opacity:.3, animation:'spin 8s linear infinite'}}/>
          <img src={EX_CLOVER.baby} style={{width:140, height:140, objectFit:'contain'}} className="float"/>
          {['✨','💕','🌱'].map((e,i)=>(
            <span key={i} style={{position:'absolute', fontSize:24, top:`${[10,20,80][i]}%`, left:`${[110,-10,90][i]}%`}}>{e}</span>
          ))}
        </div>

        <div className="gi-hand" style={{fontSize:28, color:'var(--diary-ink)', marginBottom:6}}>nice to meet you!</div>
        <div className="gi-h1" style={{fontSize:24, marginBottom:14}}>Clover joined your island</div>
        <div style={{fontSize:13, color:'var(--text-secondary)', maxWidth:280, lineHeight:1.5, marginBottom:30}}>Visit every day to keep them happy. They'll grow with your care.</div>

        <div style={{display:'flex', gap:8, marginBottom:24}}>
          <span className="gi-stat gi-stat--lumi">✨ +3 Lumi</span>
          <span className="gi-stat" style={{background:'#E8F2E8', color:'#3D6B47'}}>🌱 First friend</span>
        </div>

        <button className="btn btn-primary" style={{minHeight:50, padding:'0 36px'}}>Enter the island →</button>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </Wrap>
  );
}

// ─── ㉒ EVOLUTION SEQUENCE ───────────────────────────────────────────────
function EvolutionSequence({ phase='before' }) {
  // phase: before | during | after | choice

  if (phase === 'before') return (
    <div style={{
      width:'100%', height:'100%', position:'relative', overflow:'hidden',
      background:'radial-gradient(ellipse at center, #FFE8B0 0%, #F5C77E 40%, #C99B5C 100%)',
      display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
      fontFamily:'var(--font-body)',
    }}>
      <div style={{position:'absolute', inset:0, background:'radial-gradient(circle at 50% 50%, transparent 30%, rgba(0,0,0,.15) 100%)'}}/>

      <div className="gi-hand" style={{fontSize:24, color:'#7A4F1F', marginBottom:14, textShadow:'0 1px 0 rgba(255,255,255,.5)'}}>something feels different…</div>

      <div style={{position:'relative', marginBottom:30}}>
        {/* Glow */}
        <div style={{position:'absolute', inset:-40, borderRadius:'50%', background:'radial-gradient(circle, rgba(255,230,150,.8), transparent 70%)', animation:'pulse-glow 2s ease infinite'}}/>
        <img src={EX_CLOVER.baby} style={{width:180, height:180, objectFit:'contain', position:'relative', filter:'drop-shadow(0 0 24px #FFE8B0)'}} className="float"/>
        {[...Array(8)].map((_,i)=>(
          <span key={i} style={{
            position:'absolute', fontSize:20,
            top:`${50 + Math.sin(i)*40}%`, left:`${50 + Math.cos(i)*60}%`,
            animation:`float 3s ease ${i*.3}s infinite`,
          }}>✨</span>
        ))}
      </div>

      <div className="gi-h1" style={{fontSize:30, color:'#5C3A12', textShadow:'0 2px 0 rgba(255,255,255,.4)', marginBottom:8}}>Clover is ready to evolve</div>
      <div style={{fontSize:14, color:'#7A4F1F', maxWidth:300, textAlign:'center', lineHeight:1.5, marginBottom:30, padding:'0 20px'}}>You've cared for them so well. They want to grow into their next form.</div>

      <div style={{display:'flex', gap:10}}>
        <button className="btn btn-ghost" style={{minHeight:46, background:'rgba(255,255,255,.5)'}}>Not yet</button>
        <button className="btn btn-primary" style={{minHeight:46, padding:'0 28px', background:'linear-gradient(135deg, #E09AAE, #D9A055)'}}>Begin evolution ✨</button>
      </div>
    </div>
  );

  if (phase === 'during') return (
    <div style={{
      width:'100%', height:'100%', position:'relative', overflow:'hidden',
      background:'#0F0820',
      display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
    }}>
      {/* Radiating rays */}
      <div style={{position:'absolute', inset:0, background:'conic-gradient(from 0deg, transparent 0deg, rgba(255,230,150,.15) 10deg, transparent 20deg, transparent 40deg, rgba(255,230,150,.15) 50deg, transparent 60deg)', animation:'spin 6s linear infinite'}}/>

      {/* Stars */}
      {[...Array(30)].map((_,i)=>(
        <span key={i} style={{
          position:'absolute',
          left:`${(i*37)%100}%`, top:`${(i*53)%100}%`,
          width: 2+(i%3), height: 2+(i%3),
          background:'#fff', borderRadius:'50%',
          boxShadow:'0 0 8px #fff',
          animation:`pulse-glow 1.5s ease ${i*.05}s infinite`,
        }}/>
      ))}

      {/* Silhouette */}
      <div style={{position:'relative', zIndex:2}}>
        <div style={{position:'absolute', inset:-60, borderRadius:'50%', background:'radial-gradient(circle, rgba(255,255,255,.9), rgba(255,230,150,.4) 40%, transparent 70%)', animation:'pulse-glow 1.2s ease infinite'}}/>
        <div style={{
          width:200, height:200, borderRadius:'50%',
          background:'#FFFFFF',
          filter:'blur(2px)',
          maskImage:'radial-gradient(circle, #000 50%, transparent 70%)',
        }}/>
      </div>

      <div style={{position:'absolute', bottom:80, textAlign:'center', zIndex:3}}>
        <div className="gi-hand" style={{fontSize:32, color:'#FFE8B0', textShadow:'0 0 20px rgba(255,230,150,.8)'}}>✨ ✨ ✨</div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  if (phase === 'after') return (
    <div style={{
      width:'100%', height:'100%', position:'relative', overflow:'hidden',
      background:'linear-gradient(180deg, #E8F5E0 0%, #CFE6D9 100%)',
      display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
      fontFamily:'var(--font-body)',
    }}>
      {/* Confetti */}
      {[...Array(20)].map((_,i)=>(
        <span key={i} style={{
          position:'absolute',
          left:`${(i*37)%100}%`, top:`${(i*23)%80}%`,
          fontSize: 14+(i%3)*4,
          animation:`float 4s ease ${i*.15}s infinite`,
          opacity:.7,
        }}>{['✨','🌸','💕','🍃','⭐'][i%5]}</span>
      ))}

      <div className="gi-hand" style={{fontSize:24, color:'#3D6B47', marginBottom:8}}>look how you've grown!</div>

      <div style={{position:'relative', marginBottom:24}}>
        <div style={{position:'absolute', inset:-30, borderRadius:'50%', background:'radial-gradient(circle, rgba(255,255,255,.6), transparent 70%)'}}/>
        <img src={EX_CLOVER.mid_a} style={{width:200, height:200, objectFit:'contain', position:'relative', filter:'drop-shadow(0 8px 16px rgba(61,107,71,.3))'}} className="float"/>
      </div>

      <div className="gi-h1" style={{fontSize:30, color:'var(--diary-ink)', marginBottom:6}}>Clover evolved!</div>
      <div style={{fontSize:13, color:'var(--text-secondary)', marginBottom:4}}>Stage 1 → <strong style={{color:'var(--math-ink)'}}>Stage 2 · Sprout Form</strong></div>

      {/* Reward strip */}
      <div style={{display:'flex', gap:8, marginTop:20, marginBottom:28}}>
        <span className="gi-stat gi-stat--lumi">✨ +5 Lumi</span>
        <span className="gi-stat" style={{background:'rgba(184,164,220,.25)', color:'var(--rewards-ink)'}}>📔 New diary entry</span>
        <span className="gi-stat" style={{background:'#FFE5C2', color:'#7A4F1F'}}>📖 Dex updated</span>
      </div>

      {/* Before / After mini */}
      <div style={{display:'flex', alignItems:'center', gap:14, padding:'10px 18px', background:'rgba(255,255,255,.6)', backdropFilter:'blur(6px)', borderRadius:999, marginBottom:24}}>
        <img src={EX_CLOVER.baby} style={{width:32, height:32, objectFit:'contain', opacity:.6}}/>
        <span style={{fontSize:14, color:'var(--text-secondary)'}}>→</span>
        <img src={EX_CLOVER.mid_a} style={{width:38, height:38, objectFit:'contain'}}/>
      </div>

      <div style={{display:'flex', gap:10}}>
        <button className="btn btn-ghost" style={{minHeight:46}}>Share</button>
        <button className="btn btn-primary" style={{minHeight:46, padding:'0 28px'}}>Continue</button>
      </div>
    </div>
  );

  // choice (branching evolution)
  return (
    <div style={{
      width:'100%', height:'100%', position:'relative', overflow:'hidden',
      background:'linear-gradient(180deg, #1A1B3A 0%, #2A2147 100%)',
      display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
      color:'#fff', fontFamily:'var(--font-body)',
      padding:'40px 24px',
    }}>
      <div className="gi-hand" style={{fontSize:24, color:'#FFE8B0', marginBottom:6}}>two paths ahead…</div>
      <div className="gi-h1" style={{fontSize:24, color:'#fff', marginBottom:24}}>Choose Clover's path</div>

      <div style={{display:'flex', gap:14, width:'100%', maxWidth:400}}>
        {[
          {name:'Sprout', color:'#7BB17F', img:EX_CLOVER.mid_a, hint:'gentle · forest-bound', selected:true},
          {name:'Bloom',  color:'#E09AAE', img:EX_CLOVER.final_a, hint:'social · tea-loving'},
        ].map((p,i)=>(
          <div key={i} style={{
            flex:1, padding:18, borderRadius:18,
            background: p.selected?'rgba(255,255,255,.12)':'rgba(255,255,255,.04)',
            border: p.selected?'2px solid '+p.color:'2px solid rgba(255,255,255,.1)',
            backdropFilter:'blur(8px)',
            cursor:'pointer', textAlign:'center',
            position:'relative',
          }}>
            {p.selected && <div style={{position:'absolute', top:8, right:8, width:22, height:22, borderRadius:'50%', background:p.color, color:'#fff', display:'flex', alignItems:'center', justifyContent:'center', fontSize:13}}>✓</div>}
            <div style={{width:80, height:80, margin:'0 auto 10px', borderRadius:'50%', background:p.color+'30', display:'flex', alignItems:'center', justifyContent:'center'}}>
              <img src={p.img} style={{width:64, height:64, objectFit:'contain'}}/>
            </div>
            <div style={{fontSize:16, fontWeight:800, marginBottom:4}}>{p.name}</div>
            <div className="gi-hand" style={{fontSize:14, opacity:.8, color:p.color}}>{p.hint}</div>
          </div>
        ))}
      </div>

      <div style={{fontSize:11, opacity:.6, marginTop:18, textAlign:'center'}}>This choice is permanent.</div>

      <button className="btn btn-primary" style={{minHeight:46, padding:'0 32px', marginTop:24, background:'#7BB17F'}}>Choose Sprout →</button>
    </div>
  );
}

// ─── ㉓ PHOTO CAPTURE & SHARE ────────────────────────────────────────────
function PhotoCapture({ phase='compose' }) {
  // phase: compose | preview | shared

  if (phase === 'compose') return (
    <div style={{width:'100%', height:'100%', position:'relative', overflow:'hidden', background:'#000', fontFamily:'var(--font-body)'}}>
      {/* Viewfinder — fake forest scene */}
      <div style={{position:'absolute', inset:0, background:'linear-gradient(180deg, #CFE6D9 0%, #E8F5E0 70%, #F1DCA5 100%)'}}>
        <img src={EX_CLOVER.mid_a} style={{position:'absolute', bottom:'30%', left:'50%', transform:'translateX(-50%)', width:160, height:160, objectFit:'contain'}}/>
        {/* Sticker overlay */}
        <div style={{position:'absolute', top:'15%', right:'18%', fontSize:38, transform:'rotate(15deg)'}}>✨</div>
        <div style={{position:'absolute', top:'25%', left:'12%'}} className="gi-hand" >
          <span style={{background:'rgba(255,255,255,.85)', padding:'4px 12px', borderRadius:999, fontSize:18, color:'var(--diary-ink)', display:'inline-block', transform:'rotate(-5deg)'}}>day 12 ☀️</span>
        </div>
      </div>

      {/* Camera frame corners */}
      {[
        {top:60, left:20}, {top:60, right:20}, {bottom:200, left:20}, {bottom:200, right:20},
      ].map((s,i)=>(
        <div key={i} style={{position:'absolute', ...s, width:24, height:24, border:'2px solid #fff', borderTop: s.top?undefined:'none', borderBottom: s.bottom?undefined:'none', borderLeft: s.left?undefined:'none', borderRight: s.right?undefined:'none', opacity:.7}}/>
      ))}

      {/* Top bar */}
      <div style={{position:'absolute', top:0, left:0, right:0, padding:'14px 18px', display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <button style={{width:36, height:36, borderRadius:'50%', background:'rgba(0,0,0,.4)', backdropFilter:'blur(8px)', border:'none', color:'#fff', fontSize:20, cursor:'pointer'}}>✕</button>
        <div style={{padding:'6px 14px', background:'rgba(0,0,0,.4)', backdropFilter:'blur(8px)', borderRadius:999, fontSize:11, fontWeight:800, color:'#fff'}}>Forest · Clover</div>
        <button style={{width:36, height:36, borderRadius:'50%', background:'rgba(0,0,0,.4)', backdropFilter:'blur(8px)', border:'none', color:'#fff', fontSize:18, cursor:'pointer'}}>⚡</button>
      </div>

      {/* Sticker tray */}
      <div style={{position:'absolute', bottom:140, left:14, right:14, padding:'10px 14px', background:'rgba(255,255,255,.9)', backdropFilter:'blur(10px)', borderRadius:'var(--r-2xl)', display:'flex', gap:10, overflowX:'auto'}}>
        {['✨','🌸','💕','🍃','⭐','🌙','🌿','💫'].map((s,i)=>(
          <button key={i} style={{minWidth:44, height:44, borderRadius:12, background: i===0?'var(--diary-light)':'var(--bg-surface)', border:'none', fontSize:22, cursor:'pointer'}}>{s}</button>
        ))}
        <button style={{minWidth:44, height:44, borderRadius:12, background:'var(--bg-surface)', border:'1px dashed var(--border-default)', fontSize:18, color:'var(--text-secondary)', cursor:'pointer'}}>Aa</button>
      </div>

      {/* Shutter */}
      <div style={{position:'absolute', bottom:30, left:0, right:0, display:'flex', justifyContent:'space-between', alignItems:'center', padding:'0 36px'}}>
        <button style={{width:50, height:50, borderRadius:12, background:'rgba(255,255,255,.2)', backdropFilter:'blur(8px)', border:'none', display:'flex', alignItems:'center', justifyContent:'center', fontSize:22, cursor:'pointer'}}>🖼️</button>
        <button style={{width:78, height:78, borderRadius:'50%', background:'#fff', border:'4px solid rgba(255,255,255,.3)', boxShadow:'0 0 0 4px rgba(255,255,255,.5)', cursor:'pointer'}}/>
        <button style={{width:50, height:50, borderRadius:12, background:'rgba(255,255,255,.2)', backdropFilter:'blur(8px)', border:'none', display:'flex', alignItems:'center', justifyContent:'center', fontSize:22, cursor:'pointer'}}>🔄</button>
      </div>
    </div>
  );

  if (phase === 'preview') return (
    <div style={{width:'100%', height:'100%', background:'var(--bg-page)', display:'flex', flexDirection:'column', fontFamily:'var(--font-body)'}}>
      {/* Top bar */}
      <div style={{padding:'14px 18px', display:'flex', justifyContent:'space-between', alignItems:'center', borderBottom:'1px solid var(--border-subtle)'}}>
        <button style={{background:'none', border:'none', fontSize:14, fontWeight:700, color:'var(--text-secondary)', cursor:'pointer'}}>← Back</button>
        <div style={{fontSize:14, fontWeight:800}}>Save & Share</div>
        <button style={{background:'none', border:'none', fontSize:13, fontWeight:800, color:'var(--diary-ink)', cursor:'pointer'}}>Edit</button>
      </div>

      {/* Photo */}
      <div style={{padding:'16px 20px', flex:1, display:'flex', flexDirection:'column'}}>
        <div style={{position:'relative', borderRadius:'var(--r-lg)', overflow:'hidden', background:'linear-gradient(180deg, #CFE6D9, #F1DCA5)', aspectRatio:'4/5', maxHeight:340, marginBottom:14}}>
          <img src={EX_CLOVER.mid_a} style={{position:'absolute', bottom:'20%', left:'50%', transform:'translateX(-50%)', width:140, height:140, objectFit:'contain'}}/>
          <div style={{position:'absolute', top:14, right:18, fontSize:32, transform:'rotate(15deg)'}}>✨</div>
          <div style={{position:'absolute', top:'12%', left:14, background:'rgba(255,255,255,.9)', padding:'4px 12px', borderRadius:999, fontFamily:'var(--font-hand)', fontSize:18, color:'var(--diary-ink)', transform:'rotate(-5deg)'}}>day 12 ☀️</div>
        </div>

        {/* Caption */}
        <div style={{background:'var(--bg-card)', borderRadius:'var(--r-md)', padding:'10px 14px', marginBottom:14, border:'1px solid var(--border-subtle)'}}>
          <div className="gi-hand" style={{fontSize:18, color:'var(--text-primary)'}}>clover napped in the sun all afternoon ☀️</div>
        </div>

        {/* Save destinations */}
        <div style={{fontSize:11, fontWeight:800, color:'var(--text-secondary)', textTransform:'uppercase', letterSpacing:.5, marginBottom:8}}>Save to</div>
        <div style={{display:'flex', flexDirection:'column', gap:8, marginBottom:14}}>
          {[
            {icon:'📔', label:'Diary', sub:'today\'s entry', on:true},
            {icon:'📖', label:'Dex', sub:'Clover · Stage 2 page', on:true},
            {icon:'📷', label:'Camera roll', sub:'phone gallery', on:false},
          ].map((d,i)=>(
            <div key={i} style={{display:'flex', alignItems:'center', gap:12, padding:'10px 14px', background:'var(--bg-card)', borderRadius:'var(--r-md)', border:'1px solid var(--border-subtle)'}}>
              <div style={{width:36, height:36, borderRadius:10, background:'var(--bg-surface)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:20}}>{d.icon}</div>
              <div style={{flex:1}}>
                <div style={{fontSize:14, fontWeight:700}}>{d.label}</div>
                <div style={{fontSize:11, color:'var(--text-hint)'}}>{d.sub}</div>
              </div>
              <div style={{width:42, height:24, borderRadius:999, background: d.on?'var(--diary)':'var(--bg-surface)', position:'relative', transition:'background .2s'}}>
                <div style={{position:'absolute', top:2, left: d.on?20:2, width:20, height:20, borderRadius:'50%', background:'#fff', boxShadow:'0 1px 3px rgba(0,0,0,.2)', transition:'left .2s'}}/>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{padding:'14px 20px', background:'var(--bg-card)', borderTop:'1px solid var(--border-subtle)', display:'flex', gap:10}}>
        <button className="btn btn-ghost" style={{flex:1, minHeight:46}}>Save only</button>
        <button className="btn btn-primary" style={{flex:1.5, minHeight:46}}>Save & Share</button>
      </div>
    </div>
  );

  // shared
  return (
    <div style={{width:'100%', height:'100%', background:'var(--bg-page)', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', padding:30, textAlign:'center', fontFamily:'var(--font-body)'}}>
      <div style={{width:80, height:80, borderRadius:'50%', background:'#E8F5E0', display:'flex', alignItems:'center', justifyContent:'center', fontSize:40, marginBottom:18}}>✓</div>
      <div className="gi-h1" style={{fontSize:24, marginBottom:6}}>Saved!</div>
      <div className="gi-hand" style={{fontSize:20, color:'var(--rewards-ink)', marginBottom:20}}>added to today's diary 💕</div>

      <div style={{display:'flex', gap:8, marginBottom:30}}>
        <span className="gi-stat" style={{background:'rgba(184,164,220,.25)', color:'var(--rewards-ink)'}}>📔 Diary +1</span>
        <span className="gi-stat" style={{background:'#FFE5C2', color:'#7A4F1F'}}>📖 Dex updated</span>
      </div>

      <div style={{fontSize:12, fontWeight:800, color:'var(--text-secondary)', textTransform:'uppercase', letterSpacing:.5, marginBottom:12}}>Share to</div>
      <div style={{display:'flex', gap:10, marginBottom:24}}>
        {[
          {label:'Story', icon:'📸', color:'#E09AAE'},
          {label:'Link',  icon:'🔗', color:'#B8A4DC'},
          {label:'More',  icon:'⋯',  color:'var(--bg-surface)'},
        ].map((s,i)=>(
          <button key={i} style={{width:64, height:64, borderRadius:'var(--r-md)', background:s.color, border:'none', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:2, cursor:'pointer', color: i<2?'#fff':'var(--text-primary)'}}>
            <span style={{fontSize:22}}>{s.icon}</span>
            <span style={{fontSize:10, fontWeight:800}}>{s.label}</span>
          </button>
        ))}
      </div>

      <button className="btn btn-ghost" style={{minHeight:42}}>Done</button>
    </div>
  );
}

// ─── ㉔ TOAST / SNACKBAR SYSTEM ──────────────────────────────────────────
function ToastSystem({ variant='success' }) {
  const toasts = {
    success: [{kind:'success', icon:'✓', title:'Saved to diary', sub:null}],
    reward:  [{kind:'reward', icon:'✨', title:'+3 Lumi earned', sub:'daily mission complete'}],
    error:   [{kind:'error', icon:'!', title:'Couldn\'t save', sub:'tap to retry'}],
    info:    [{kind:'info', icon:'🌙', title:'Lumi has a message', sub:'tap to view'}],
    achieve: [{kind:'achieve', icon:'🏆', title:'New milestone!', sub:'7-day streak unlocked'}],
    stack:   [
      {kind:'success', icon:'✓', title:'Saved to diary'},
      {kind:'reward', icon:'✨', title:'+3 Lumi earned', sub:'daily mission complete'},
    ],
  };
  const list = toasts[variant];

  const styles = {
    success: {bg:'#E8F5E0', icon:'#3D6B47', text:'#2D4F33', border:'#7BB17F'},
    reward:  {bg:'#FFE5C2', icon:'#D9A055', text:'#7A4F1F', border:'#F0BD6B'},
    error:   {bg:'#FBEEF2', icon:'#C25770', text:'#8C4A5E', border:'#E09AAE'},
    info:    {bg:'#F2ECFA', icon:'#5C4A87', text:'#3D2F5E', border:'#B8A4DC'},
    achieve: {bg:'linear-gradient(135deg, #FFE5C2, #FBEEF2)', icon:'#D9A055', text:'#7A4F1F', border:'#F0BD6B'},
  };

  // Mock app behind
  return (
    <div style={{width:'100%', height:'100%', position:'relative', overflow:'hidden', fontFamily:'var(--font-body)'}}>
      {/* Faint app background */}
      <div style={{position:'absolute', inset:0, background:'linear-gradient(180deg, #CFE6D9, #C7DDEF)', opacity:.5}}/>
      <div style={{position:'absolute', top:0, left:0, right:0, padding:'12px 18px', background:'rgba(255,255,255,.7)', backdropFilter:'blur(8px)', borderBottom:'1px solid var(--border-subtle)'}}>
        <div style={{display:'flex', gap:8}}>
          <span className="gi-stat gi-stat--lumi">✨ 3</span>
          <span className="gi-stat"><span className="ico">💎</span> 240</span>
        </div>
      </div>
      <div style={{position:'absolute', left:'50%', top:'50%', transform:'translate(-50%,-50%)', opacity:.3}}>
        <img src={EX_CLOVER.mid_a} style={{width:140, height:140, objectFit:'contain'}}/>
      </div>

      {/* Toast stack — top of screen, below header */}
      <div style={{position:'absolute', top:60, left:14, right:14, display:'flex', flexDirection:'column', gap:8, alignItems:'center'}}>
        {list.map((t,i)=>{
          const s = styles[t.kind];
          return (
            <div key={i} style={{
              width:'100%', maxWidth:380,
              background: s.bg.includes('gradient') ? s.bg : s.bg,
              borderRadius:'var(--r-md)',
              border:'1px solid '+s.border,
              padding:'10px 14px',
              display:'flex', alignItems:'center', gap:12,
              boxShadow:'0 6px 20px rgba(0,0,0,.08)',
              transform: list.length>1 ? `scale(${1 - i*0.03}) translateY(${i*-3}px)` : 'none',
              animation:'slide-down .3s ease',
            }}>
              <div style={{
                width:32, height:32, borderRadius:'50%',
                background: s.icon, color:'#fff',
                display:'flex', alignItems:'center', justifyContent:'center',
                fontSize:16, fontWeight:800, flexShrink:0,
              }}>{t.icon}</div>
              <div style={{flex:1, minWidth:0}}>
                <div style={{fontSize:14, fontWeight:800, color:s.text}}>{t.title}</div>
                {t.sub && <div style={{fontSize:12, color:s.text, opacity:.75, marginTop:1}}>{t.sub}</div>}
              </div>
              {(t.kind==='error' || t.kind==='info') && (
                <button style={{background:'none', border:'none', fontSize:12, fontWeight:800, color:s.icon, cursor:'pointer', flexShrink:0}}>
                  {t.kind==='error'?'Retry':'View'}
                </button>
              )}
              <button style={{background:'none', border:'none', fontSize:14, color:s.text, opacity:.5, cursor:'pointer', flexShrink:0}}>✕</button>
            </div>
          );
        })}
      </div>

      {/* Variant label */}
      <div style={{position:'absolute', bottom:14, left:'50%', transform:'translateX(-50%)', padding:'4px 12px', background:'rgba(43,39,34,.7)', color:'#fff', fontSize:10, fontWeight:800, borderRadius:999, textTransform:'uppercase', letterSpacing:.5}}>
        {variant}
      </div>

      <style>{`@keyframes slide-down { from { transform: translateY(-20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }`}</style>
    </div>
  );
}

Object.assign(window, { OnboardingFlow, EvolutionSequence, PhotoCapture, ToastSystem });

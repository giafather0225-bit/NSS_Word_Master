// screens-meta.jsx — Daily Missions, Mailbox

// ─── ⑬ DAILY — attendance calendar + missions ──────────────────────────
function DailyScreen({ tab='missions' }) {
  const today = 4; // 1-indexed day this week
  const week = ['M','T','W','T','F','S','S'];
  const rewards = ['💎10','💎10','💎15','💎15','💎20','✨1','💎50'];
  const claimed = [true, true, true, false, false, false, false];

  const missions = [
    {id:1, ico:'🍖', title:'Feed Clover',          progress:1, total:1, done:true,  reward:'💎 10'},
    {id:2, ico:'💕', title:'Play 3 times',         progress:2, total:3, done:false, reward:'💎 15'},
    {id:3, ico:'🌱', title:'Visit every zone',     progress:3, total:5, done:false, reward:'💎 20'},
    {id:4, ico:'🛍️', title:'Buy something at shop', progress:0, total:1, done:false, reward:'✨ 1'},
    {id:5, ico:'🏝️', title:'Visit a friend\'s island', progress:0, total:1, done:false, reward:'💎 30', locked:true},
  ];

  const weekly = [
    {id:1, ico:'⭐', title:'Earn 5 Lumi this week',     progress:3, total:5, reward:'💎 100'},
    {id:2, ico:'🌸', title:'Evolve a friend twice',     progress:1, total:2, reward:'✨ 2'},
  ];

  return (
    <div className="gi-screen">
      <div className="gi-topbar">
        <div className="gi-topbar-left">
          <button className="gi-iconbtn">←</button>
          <div className="gi-h2" style={{fontSize:18}}>Daily</div>
        </div>
        <div className="gi-topbar-right">
          <span className="gi-stat"><span className="ico">💎</span> 240</span>
          <span className="gi-stat gi-stat--lumi"><span className="ico">✨</span> 3</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <div className={'tab ' + (tab==='attendance'?'active':'')}>📅 Attendance</div>
        <div className={'tab ' + (tab==='missions'?'active':'')}>🎯 Missions</div>
        <div className={'tab ' + (tab==='weekly'?'active':'')}>🗓️ Weekly</div>
      </div>

      <div style={{flex:1, overflow:'auto', padding:'20px 24px 24px'}}>

        {/* Streak banner — always visible */}
        <div style={{
          background:'linear-gradient(120deg, var(--arcade-light) 0%, var(--diary-light) 100%)',
          borderRadius:'var(--r-lg)', padding:'14px 18px',
          display:'flex', alignItems:'center', justifyContent:'space-between',
          border:'1px solid var(--arcade-soft)',
          marginBottom:20,
        }}>
          <div style={{display:'flex', alignItems:'center', gap:12}}>
            <div style={{fontSize:34}}>🔥</div>
            <div>
              <div className="gi-h2" style={{fontSize:18, color:'var(--arcade-ink)'}}>4-day streak</div>
              <div style={{fontSize:12, color:'var(--text-secondary)', fontWeight:600}}>Come back tomorrow for ✨ 1 Lumi</div>
            </div>
          </div>
          <div className="gi-hand" style={{fontSize:22, color:'var(--diary-ink)'}}>nice rhythm!</div>
        </div>

        {/* ATTENDANCE */}
        {tab==='attendance' && (
          <div className="card" style={{padding:24}}>
            <div className="gi-h2" style={{fontSize:16, marginBottom:14}}>This week</div>
            <div style={{display:'grid', gridTemplateColumns:'repeat(7, 1fr)', gap:10}}>
              {week.map((d,i)=>{
                const isClaimed = claimed[i];
                const isToday = i+1===today;
                return (
                  <div key={i} style={{
                    background: isClaimed ? 'var(--math-light)' : isToday ? 'var(--diary-light)' : 'var(--bg-card)',
                    border:'1.5px solid ' + (isToday ? 'var(--diary)' : isClaimed ? 'var(--math-soft)' : 'var(--border-subtle)'),
                    borderRadius:'var(--r-md)',
                    padding:'10px 6px',
                    textAlign:'center',
                    position:'relative',
                  }} className={isToday ? 'pulse' : ''}>
                    <div style={{fontSize:11, fontWeight:800, color:'var(--text-secondary)', textTransform:'uppercase', letterSpacing:.5}}>{d}</div>
                    <div style={{fontSize:18, fontWeight:800, marginTop:2, color: isClaimed ? 'var(--math-ink)' : 'var(--text-primary)'}}>
                      {isClaimed ? '✓' : i+1}
                    </div>
                    <div style={{fontSize:11, fontWeight:800, marginTop:6, color: isClaimed ? 'var(--math-ink)' : 'var(--text-secondary)'}}>
                      {rewards[i]}
                    </div>
                    {isToday && (
                      <div style={{position:'absolute', top:-8, left:'50%', transform:'translateX(-50%)', background:'var(--diary)', color:'#fff', fontSize:9, fontWeight:800, padding:'2px 8px', borderRadius:999, whiteSpace:'nowrap'}}>TODAY</div>
                    )}
                  </div>
                );
              })}
            </div>

            <button className="btn btn-primary" style={{width:'100%', marginTop:18, minHeight:48}}>
              ✨ Claim Day 4 · 💎 15
            </button>

            <div style={{marginTop:18, padding:'12px 14px', background:'var(--rewards-light)', borderRadius:'var(--r-md)', display:'flex', alignItems:'center', gap:10}}>
              <span style={{fontSize:22}}>🎁</span>
              <div style={{flex:1}}>
                <div style={{fontSize:13, fontWeight:800, color:'var(--rewards-ink)'}}>Day 7 mega reward</div>
                <div style={{fontSize:11, color:'var(--text-secondary)', fontWeight:600}}>3 days to go · 💎 50 + Lumi chest</div>
              </div>
            </div>
          </div>
        )}

        {/* MISSIONS */}
        {tab==='missions' && (
          <div>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'baseline', marginBottom:10}}>
              <div className="gi-h2" style={{fontSize:14}}>Today</div>
              <div style={{fontSize:11, color:'var(--text-secondary)', fontWeight:700}}>Resets in 6h 23m</div>
            </div>
            <div style={{display:'flex', flexDirection:'column', gap:8}}>
              {missions.map(m=>(
                <div key={m.id} className="card" style={{
                  padding:'14px 16px',
                  display:'flex', alignItems:'center', gap:14,
                  opacity: m.locked ? .5 : 1,
                  background: m.done ? 'var(--math-light)' : 'var(--bg-card)',
                  borderColor: m.done ? 'var(--math-soft)' : 'var(--border-subtle)',
                }}>
                  <div style={{
                    width:40, height:40, borderRadius:'50%',
                    background: m.done ? 'var(--math)' : 'var(--bg-surface)',
                    display:'flex', alignItems:'center', justifyContent:'center',
                    fontSize:20, flexShrink:0,
                  }}>{m.done ? '✓' : m.ico}</div>
                  <div style={{flex:1}}>
                    <div style={{fontSize:14, fontWeight:800, color:'var(--text-primary)', textDecoration: m.done?'line-through':'none'}}>{m.title}</div>
                    <div style={{display:'flex', alignItems:'center', gap:8, marginTop:4}}>
                      <div className="gauge-bar" style={{flex:1, height:6}}>
                        <i style={{width: (m.progress/m.total*100)+'%', background: m.done ? 'var(--math)' : 'linear-gradient(90deg,#F8C8D5,#E09AAE)'}}/>
                      </div>
                      <span style={{fontSize:11, fontWeight:700, color:'var(--text-secondary)'}}>{m.progress}/{m.total}</span>
                    </div>
                  </div>
                  {m.locked ? (
                    <span className="chip chip-locked">🔒</span>
                  ) : m.done ? (
                    <span style={{fontSize:13, fontWeight:800, color:'var(--math-ink)'}}>{m.reward}</span>
                  ) : (
                    <button className="btn" style={{minHeight:32, padding:'6px 14px', fontSize:12}}>{m.reward}</button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* WEEKLY */}
        {tab==='weekly' && (
          <div>
            <div style={{display:'flex', flexDirection:'column', gap:10}}>
              {weekly.map(m=>(
                <div key={m.id} className="card" style={{padding:'18px 20px', display:'flex', alignItems:'center', gap:16}}>
                  <div style={{
                    width:52, height:52, borderRadius:14,
                    background:'var(--rewards-light)',
                    display:'flex', alignItems:'center', justifyContent:'center',
                    fontSize:26,
                  }}>{m.ico}</div>
                  <div style={{flex:1}}>
                    <div style={{fontSize:15, fontWeight:800}}>{m.title}</div>
                    <div style={{display:'flex', alignItems:'center', gap:10, marginTop:6}}>
                      <div className="gauge-bar" style={{flex:1, height:8}}>
                        <i style={{width:(m.progress/m.total*100)+'%', background:'linear-gradient(90deg,#B8A4DC,#E09AAE)'}}/>
                      </div>
                      <span style={{fontSize:12, fontWeight:800, color:'var(--rewards-ink)'}}>{m.progress}/{m.total}</span>
                    </div>
                  </div>
                  <div style={{fontSize:14, fontWeight:800, color:'var(--rewards-ink)'}}>{m.reward}</div>
                </div>
              ))}
            </div>
            <div className="paper" style={{marginTop:18, padding:'16px 20px'}}>
              <div className="gi-hand" style={{fontSize:22, color:'var(--diary-ink)'}}>You're 2 missions away from a Lumi 💕</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── ⑭ MAILBOX — Lumi messages, friend gifts, events ─────────────────────
function MailboxScreen({ filter='all', open=null }) {
  const messages = [
    {id:1, type:'lumi', ico:'🌙', from:'Lumi', preview:'Clover misses you! Come feed them ✨', time:'2m', unread:true, gift:null},
    {id:2, type:'gift', ico:'🎁', from:'Mina', preview:'sent you a Mushroom Lantern',         time:'1h', unread:true, gift:'🍄'},
    {id:3, type:'lumi', ico:'🌙', from:'Lumi', preview:'Your weekly Lumi is ready to claim',  time:'3h', unread:true, gift:'✨'},
    {id:4, type:'event',ico:'🌸', from:'Spring Event', preview:'New decor in shop until Sunday', time:'1d', unread:false},
    {id:5, type:'gift', ico:'🎁', from:'Joon', preview:'sent you 💎 20',                       time:'2d', unread:false, gift:'💎'},
    {id:6, type:'lumi', ico:'🌙', from:'Lumi', preview:'Welcome to Gia\'s Island!',           time:'5d', unread:false},
  ];

  const shown = filter==='all' ? messages : messages.filter(m=>m.type===filter);
  const sel = open ? messages.find(m=>m.id===open) : null;

  return (
    <div className="gi-screen">
      <div className="gi-topbar">
        <div className="gi-topbar-left">
          <button className="gi-iconbtn">←</button>
          <div className="gi-h2" style={{fontSize:18}}>Mailbox</div>
          <span className="chip" style={{background:'var(--diary)', color:'#fff'}}>3 new</span>
        </div>
        <div className="gi-topbar-right">
          <button className="gi-iconbtn">⋯</button>
        </div>
      </div>

      {/* Filters */}
      <div style={{display:'flex', gap:6, padding:'12px 20px', borderBottom:'1px solid var(--border-subtle)', background:'var(--bg-card)'}}>
        {[
          {id:'all', lbl:'All', n:6},
          {id:'lumi', lbl:'🌙 Lumi', n:3},
          {id:'gift', lbl:'🎁 Gifts', n:2},
          {id:'event', lbl:'🌸 Events', n:1},
        ].map(f=>(
          <button key={f.id} style={{
            padding:'6px 14px', borderRadius:999,
            fontSize:13, fontWeight:700,
            border: '1px solid ' + (f.id===filter ? 'var(--diary)' : 'var(--border-subtle)'),
            background: f.id===filter ? 'var(--diary-light)' : 'transparent',
            color: f.id===filter ? 'var(--diary-ink)' : 'var(--text-secondary)',
            cursor:'pointer',
          }}>
            {f.lbl} <span style={{opacity:.6, fontWeight:600}}>{f.n}</span>
          </button>
        ))}
      </div>

      <div style={{flex:1, display:'flex', overflow:'hidden'}}>

        {/* List */}
        <div style={{flex: sel ? '0 0 260px' : 1, overflow:'auto', borderRight: sel ? '1px solid var(--border-subtle)' : 'none'}}>
          {shown.map(m=>(
            <div key={m.id} style={{
              padding:'14px 18px',
              borderBottom:'1px solid var(--border-subtle)',
              background: sel?.id===m.id ? 'var(--diary-light)' : m.unread ? 'var(--bg-card)' : 'transparent',
              display:'flex', gap:12, alignItems:'flex-start',
              cursor:'pointer',
              position:'relative',
            }}>
              {m.unread && (
                <div style={{position:'absolute', left:6, top:'50%', transform:'translateY(-50%)', width:6, height:6, borderRadius:'50%', background:'var(--diary)'}}/>
              )}
              <div style={{
                width:38, height:38, borderRadius:'50%',
                background: m.type==='lumi' ? 'var(--rewards-light)' : m.type==='gift' ? 'var(--arcade-light)' : 'var(--diary-light)',
                display:'flex', alignItems:'center', justifyContent:'center',
                fontSize:18, flexShrink:0,
              }}>{m.ico}</div>
              <div style={{flex:1, minWidth:0}}>
                <div style={{display:'flex', justifyContent:'space-between', alignItems:'baseline', gap:8}}>
                  <div style={{fontSize:14, fontWeight:m.unread?800:700, color:'var(--text-primary)'}}>{m.from}</div>
                  <div style={{fontSize:11, color:'var(--text-hint)', fontWeight:600, flexShrink:0}}>{m.time}</div>
                </div>
                <div style={{fontSize:13, color: m.unread ? 'var(--text-primary)' : 'var(--text-secondary)', marginTop:2, fontWeight:m.unread?600:400, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>
                  {m.preview}
                </div>
              </div>
              {m.gift && (
                <div style={{fontSize:18, alignSelf:'center'}}>{m.gift}</div>
              )}
            </div>
          ))}

          {shown.length===0 && (
            <div style={{padding:60, textAlign:'center', color:'var(--text-hint)'}}>
              <div style={{fontSize:40}}>📭</div>
              <div style={{marginTop:8, fontWeight:700}}>No messages</div>
            </div>
          )}
        </div>

        {/* Detail pane (when message open) */}
        {sel && (
          <div style={{flex:1, padding:'24px 28px', overflow:'auto', background:'var(--bg-page)'}}>
            <div style={{display:'flex', alignItems:'center', gap:12, marginBottom:18}}>
              <div style={{
                width:52, height:52, borderRadius:'50%',
                background:'var(--rewards-light)',
                display:'flex', alignItems:'center', justifyContent:'center',
                fontSize:26,
              }}>{sel.ico}</div>
              <div>
                <div className="gi-h2" style={{fontSize:18}}>{sel.from}</div>
                <div style={{fontSize:12, color:'var(--text-secondary)', fontWeight:600}}>{sel.time} ago</div>
              </div>
            </div>

            <div className="paper" style={{padding:'24px 22px'}}>
              <div className="gi-hand" style={{fontSize:24, color:'var(--diary-ink)', lineHeight:1.3}}>
                Hi Gia,
              </div>
              <div style={{fontFamily:'var(--font-hand)', fontSize:20, color:'var(--text-primary)', lineHeight:1.5, marginTop:12}}>
                Clover hasn't eaten in a while and is starting to feel a bit hungry 🥺 Can you visit the Forest when you have a moment?
              </div>
              <div className="gi-hand" style={{fontSize:22, color:'var(--diary-ink)', textAlign:'right', marginTop:18}}>— Lumi 🌙</div>
            </div>

            {sel.gift && (
              <div style={{marginTop:18, padding:'14px 18px', background:'var(--arcade-light)', borderRadius:'var(--r-md)', display:'flex', alignItems:'center', gap:14, border:'1px solid var(--arcade-soft)'}}>
                <span style={{fontSize:30}}>{sel.gift}</span>
                <div style={{flex:1}}>
                  <div style={{fontSize:13, fontWeight:800, color:'var(--arcade-ink)'}}>Attached gift</div>
                  <div style={{fontSize:12, color:'var(--text-secondary)', fontWeight:600}}>Tap claim to add to inventory</div>
                </div>
                <button className="btn btn-secondary">Claim</button>
              </div>
            )}

            <div style={{marginTop:20, display:'flex', gap:10}}>
              <button className="btn">→ Go to Forest</button>
              <button className="btn btn-ghost">Mark read</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { DailyScreen, MailboxScreen });

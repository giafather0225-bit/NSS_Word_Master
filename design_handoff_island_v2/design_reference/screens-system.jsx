// screens-system.jsx — Settings, Purchase confirm modal

// ─── ⑮ SETTINGS ─────────────────────────────────────────────────────────
function SettingsScreen({ section='account' }) {
  const Row = ({ico, label, sub, right, danger}) => (
    <div style={{
      display:'flex', alignItems:'center', gap:14,
      padding:'14px 18px',
      borderBottom:'1px solid var(--border-subtle)',
      cursor:'pointer',
    }}>
      {ico && (
        <div style={{
          width:34, height:34, borderRadius:10,
          background:'var(--bg-surface)',
          display:'flex', alignItems:'center', justifyContent:'center',
          fontSize:16, flexShrink:0,
        }}>{ico}</div>
      )}
      <div style={{flex:1, minWidth:0}}>
        <div style={{fontSize:14, fontWeight:700, color: danger ? '#B5443B' : 'var(--text-primary)'}}>{label}</div>
        {sub && <div style={{fontSize:12, color:'var(--text-secondary)', marginTop:2}}>{sub}</div>}
      </div>
      <div style={{flexShrink:0}}>{right}</div>
    </div>
  );

  const Toggle = ({on}) => (
    <div style={{
      width:42, height:24, borderRadius:999,
      background: on ? 'var(--diary)' : 'var(--bg-surface)',
      position:'relative', transition:'background .2s',
    }}>
      <div style={{
        width:20, height:20, borderRadius:'50%',
        background:'#fff', boxShadow:'0 1px 3px rgba(0,0,0,.2)',
        position:'absolute', top:2, left: on ? 20 : 2,
        transition:'left .2s',
      }}/>
    </div>
  );

  const Chevron = () => <span style={{color:'var(--text-hint)', fontSize:14}}>›</span>;

  return (
    <div className="gi-screen">
      <div className="gi-topbar">
        <div className="gi-topbar-left">
          <button className="gi-iconbtn">←</button>
          <div className="gi-h2" style={{fontSize:18}}>Settings</div>
        </div>
      </div>

      <div style={{flex:1, display:'flex', overflow:'hidden'}}>
        {/* Side nav */}
        <div style={{
          width:200, borderRight:'1px solid var(--border-subtle)',
          background:'var(--bg-card)', padding:'14px 10px',
          display:'flex', flexDirection:'column', gap:2,
        }}>
          {[
            {id:'account', ico:'👤', lbl:'Account'},
            {id:'sound',   ico:'🔊', lbl:'Sound'},
            {id:'notify',  ico:'🔔', lbl:'Notifications'},
            {id:'lang',    ico:'🌐', lbl:'Language'},
            {id:'support', ico:'💬', lbl:'Support'},
            {id:'about',   ico:'ℹ️', lbl:'About'},
          ].map(t=>(
            <div key={t.id} style={{
              display:'flex', alignItems:'center', gap:10,
              padding:'10px 12px', borderRadius:10,
              background: section===t.id ? 'var(--diary-light)' : 'transparent',
              color: section===t.id ? 'var(--diary-ink)' : 'var(--text-primary)',
              fontSize:13, fontWeight: section===t.id ? 800 : 600,
              cursor:'pointer',
            }}>
              <span style={{fontSize:15}}>{t.ico}</span> {t.lbl}
            </div>
          ))}
        </div>

        {/* Panel */}
        <div style={{flex:1, overflow:'auto'}}>
          {section==='account' && (
            <>
              {/* Profile card */}
              <div style={{padding:'24px 20px 18px', display:'flex', alignItems:'center', gap:14, background:'var(--bg-card)', borderBottom:'1px solid var(--border-subtle)'}}>
                <div style={{
                  width:64, height:64, borderRadius:'50%',
                  background:'linear-gradient(135deg, var(--diary-light), var(--rewards-light))',
                  border:'2px solid var(--bg-card)',
                  boxShadow:'var(--shadow-soft)',
                  display:'flex', alignItems:'center', justifyContent:'center',
                  fontSize:32,
                }}>🌿</div>
                <div style={{flex:1}}>
                  <div className="gi-h2" style={{fontSize:18}}>Gia</div>
                  <div style={{fontSize:12, color:'var(--text-secondary)', fontWeight:600}}>Island ID · GIA-204819</div>
                  <div className="gi-hand" style={{fontSize:18, color:'var(--diary-ink)', marginTop:2}}>since 12 days ago</div>
                </div>
                <button className="btn">Edit</button>
              </div>

              <Row ico="✉️" label="Email" sub="gia@example.com" right={<Chevron/>}/>
              <Row ico="🔗" label="Linked accounts" sub="Apple · Google" right={<Chevron/>}/>
              <Row ico="🎁" label="Invite code" sub="ISLAND-G7K2" right={<Chevron/>}/>
              <Row ico="💾" label="Cloud save" sub="Last synced 2m ago" right={<span style={{fontSize:12, fontWeight:800, color:'var(--math-ink)'}}>● ON</span>}/>

              <div style={{height:14}}/>
              <Row ico="🚪" label="Sign out" right={<Chevron/>}/>
              <Row ico="🗑️" label="Delete account" sub="Permanently erase your island" danger right={<Chevron/>}/>
            </>
          )}

          {section==='sound' && (
            <>
              <Row ico="🎵" label="Music" sub="Forest theme" right={<Toggle on={true}/>}/>
              <div style={{padding:'4px 18px 14px 66px'}}>
                <div style={{display:'flex', alignItems:'center', gap:10}}>
                  <span style={{fontSize:11, fontWeight:700, color:'var(--text-secondary)'}}>Vol</span>
                  <div style={{flex:1, height:4, background:'var(--bg-surface)', borderRadius:999, position:'relative'}}>
                    <div style={{position:'absolute', left:0, top:0, bottom:0, width:'70%', background:'var(--diary)', borderRadius:999}}/>
                    <div style={{position:'absolute', left:'70%', top:'50%', transform:'translate(-50%,-50%)', width:14, height:14, borderRadius:'50%', background:'#fff', boxShadow:'var(--shadow-soft)', border:'1.5px solid var(--diary)'}}/>
                  </div>
                  <span style={{fontSize:11, fontWeight:700, minWidth:30, textAlign:'right'}}>70</span>
                </div>
              </div>
              <Row ico="🔉" label="Sound effects" right={<Toggle on={true}/>}/>
              <Row ico="🐾" label="Character voices" sub="Cute chirps when you tap" right={<Toggle on={true}/>}/>
              <Row ico="🌧️" label="Ambient sounds" sub="Wind, water, leaves" right={<Toggle on={false}/>}/>
              <Row ico="📳" label="Haptics" right={<Toggle on={true}/>}/>
            </>
          )}

          {section==='notify' && (
            <>
              <div style={{padding:'14px 20px', background:'var(--rewards-light)', display:'flex', gap:10, alignItems:'center', borderBottom:'1px solid var(--border-subtle)'}}>
                <span style={{fontSize:18}}>🌙</span>
                <div style={{fontSize:12, color:'var(--rewards-ink)', fontWeight:700, lineHeight:1.4}}>Lumi will only send what you turn on below.</div>
              </div>
              <Row ico="🍖" label="Hunger reminders" sub="When a friend gets hungry" right={<Toggle on={true}/>}/>
              <Row ico="✨" label="Evolution ready" right={<Toggle on={true}/>}/>
              <Row ico="📅" label="Daily streak" sub="9pm reminder" right={<Toggle on={true}/>}/>
              <Row ico="🎁" label="Friend gifts" right={<Toggle on={true}/>}/>
              <Row ico="🌸" label="Events &amp; news" right={<Toggle on={false}/>}/>
              <Row ico="🌙" label="Quiet hours" sub="22:00 – 08:00" right={<Chevron/>}/>
            </>
          )}

          {section==='lang' && (
            <>
              {[
                {code:'ko', lbl:'한국어', sub:'Korean', sel:true},
                {code:'en', lbl:'English', sub:'English'},
                {code:'ja', lbl:'日本語', sub:'Japanese'},
                {code:'zh', lbl:'中文', sub:'Chinese (Simplified)'},
                {code:'es', lbl:'Español', sub:'Spanish'},
              ].map(l=>(
                <Row key={l.code} label={l.lbl} sub={l.sub} right={l.sel ? <span style={{color:'var(--diary)', fontSize:18, fontWeight:800}}>✓</span> : null}/>
              ))}
            </>
          )}

          {section==='support' && (
            <>
              <Row ico="❓" label="Help center" right={<Chevron/>}/>
              <Row ico="💌" label="Contact us" sub="We reply within 1–2 days" right={<Chevron/>}/>
              <Row ico="🐛" label="Report a bug" right={<Chevron/>}/>
              <Row ico="⭐" label="Rate the app" right={<Chevron/>}/>
            </>
          )}

          {section==='about' && (
            <>
              <Row label="Version" right={<span style={{fontSize:12, color:'var(--text-secondary)', fontWeight:700}}>1.0.4</span>}/>
              <Row label="Terms of service" right={<Chevron/>}/>
              <Row label="Privacy policy" right={<Chevron/>}/>
              <Row label="Open-source licenses" right={<Chevron/>}/>
              <Row label="Credits" sub="Made with care 💕" right={<Chevron/>}/>
              <div className="paper" style={{margin:24, padding:'18px 22px', textAlign:'center'}}>
                <div className="gi-hand" style={{fontSize:24, color:'var(--diary-ink)'}}>made with care 💕</div>
                <div style={{fontSize:11, color:'var(--text-hint)', fontWeight:600, marginTop:6}}>© 2026 Gia's Island</div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── ⑯ PURCHASE CONFIRM MODAL ──────────────────────────────────────────
function PurchaseModal({ kind='buy', state='confirm' }) {
  // kind: buy (gem item) | lumi (lumi item) | insufficient
  // state: confirm | success | insufficient
  const items = {
    buy:    {ico:'🍄', name:'Mushroom Lantern', desc:'Forest decor · adds cozy glow', price:30, currency:'💎', balance:240},
    lumi:   {ico:'⚡', name:'Legend 1st Stone A', desc:'Evolves Clover to legendary path', price:10, currency:'✨', balance:3},
    insufficient: {ico:'🌲', name:'Treehouse', desc:'Forest decor · large landmark', price:120, currency:'💎', balance:80},
  };
  const it = items[kind];
  const newBalance = it.balance - it.price;
  const isInsufficient = newBalance < 0;

  return (
    <div style={{width:'100%', height:'100%', position:'relative', background:'var(--bg-page)'}}>
      {/* Faint shop in background */}
      <div style={{position:'absolute', inset:0, padding:30, opacity:.35, pointerEvents:'none'}}>
        <div style={{display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:14}}>
          {[...Array(6)].map((_,i)=>(
            <div key={i} className="shop-item" style={{height:120}}>
              <div className="em">{['🍄','🪧','🍯','🏡','⛩️','🌲'][i]}</div>
              <div className="nm">Item</div>
            </div>
          ))}
        </div>
      </div>

      <div className="scrim" style={{background:'rgba(43,39,34,.5)'}}>
        <div className="card" style={{
          width:380, padding:'28px 26px',
          background:'var(--bg-card)',
          boxShadow:'var(--shadow-modal)',
          textAlign:'center',
          position:'relative',
        }}>

          {/* Close */}
          <button className="gi-iconbtn" style={{position:'absolute', top:14, right:14, width:30, height:30, fontSize:14}}>✕</button>

          {state==='confirm' && !isInsufficient && (
            <>
              <div style={{
                width:96, height:96, borderRadius:'50%',
                background: kind==='lumi' ? 'var(--rewards-light)' : 'var(--arcade-light)',
                margin:'0 auto 16px',
                display:'flex', alignItems:'center', justifyContent:'center',
                fontSize:54,
              }} className="float">{it.ico}</div>

              <div className="gi-h1" style={{fontSize:22}}>{it.name}</div>
              <div style={{fontSize:13, color:'var(--text-secondary)', marginTop:6, fontWeight:600}}>{it.desc}</div>

              {/* Price line */}
              <div style={{
                marginTop:20, padding:'14px 18px',
                background:'var(--bg-surface)',
                borderRadius:'var(--r-md)',
                display:'flex', flexDirection:'column', gap:8,
              }}>
                <div style={{display:'flex', justifyContent:'space-between', fontSize:13}}>
                  <span style={{fontWeight:600, color:'var(--text-secondary)'}}>Price</span>
                  <span style={{fontWeight:800, color: kind==='lumi' ? 'var(--rewards-ink)' : 'var(--arcade-ink)'}}>{it.currency} {it.price}</span>
                </div>
                <div style={{display:'flex', justifyContent:'space-between', fontSize:13}}>
                  <span style={{fontWeight:600, color:'var(--text-secondary)'}}>Balance</span>
                  <span style={{fontWeight:700}}>{it.currency} {it.balance}</span>
                </div>
                <div style={{height:1, background:'var(--border-default)'}}/>
                <div style={{display:'flex', justifyContent:'space-between', fontSize:13}}>
                  <span style={{fontWeight:600, color:'var(--text-secondary)'}}>After purchase</span>
                  <span style={{fontWeight:800, color:'var(--text-primary)'}}>{it.currency} {newBalance}</span>
                </div>
              </div>

              <div style={{display:'flex', gap:10, marginTop:20}}>
                <button className="btn" style={{flex:1}}>Cancel</button>
                <button className="btn btn-primary" style={{flex:2}}>Buy {it.currency} {it.price}</button>
              </div>

              <div style={{fontSize:11, color:'var(--text-hint)', marginTop:14, fontWeight:600}}>
                You can disable purchase confirmations in Settings
              </div>
            </>
          )}

          {state==='success' && (
            <>
              <div style={{
                width:96, height:96, borderRadius:'50%',
                background:'var(--math-light)',
                margin:'0 auto 16px',
                display:'flex', alignItems:'center', justifyContent:'center',
                fontSize:54,
                position:'relative',
              }}>
                {it.ico}
                <div style={{position:'absolute', top:-4, right:-4, width:32, height:32, borderRadius:'50%', background:'var(--math)', color:'#fff', display:'flex', alignItems:'center', justifyContent:'center', fontSize:16, fontWeight:800, border:'3px solid var(--bg-card)'}}>✓</div>
              </div>

              <div className="gi-h1" style={{fontSize:22}}>Got it!</div>
              <div className="gi-hand" style={{fontSize:22, color:'var(--diary-ink)', marginTop:6}}>{it.name} added to your basket ✨</div>

              <div style={{display:'flex', gap:10, marginTop:24}}>
                <button className="btn" style={{flex:1}}>Keep shopping</button>
                <button className="btn btn-primary" style={{flex:1}}>Use now →</button>
              </div>
            </>
          )}

          {kind==='insufficient' && (
            <>
              <div style={{
                width:96, height:96, borderRadius:'50%',
                background:'#FFE5E5',
                margin:'0 auto 16px',
                display:'flex', alignItems:'center', justifyContent:'center',
                fontSize:54,
              }}>{it.ico}</div>

              <div className="gi-h1" style={{fontSize:22}}>Not enough gems</div>
              <div style={{fontSize:13, color:'var(--text-secondary)', marginTop:6, fontWeight:600}}>You need <b style={{color:'var(--diary-ink)'}}>💎 {it.price - it.balance} more</b> to buy {it.name}.</div>

              <div style={{
                marginTop:20, padding:'14px 18px',
                background:'var(--bg-surface)',
                borderRadius:'var(--r-md)',
                display:'flex', justifyContent:'space-between', alignItems:'center',
              }}>
                <span style={{fontSize:13, fontWeight:700, color:'var(--text-secondary)'}}>Current balance</span>
                <span style={{fontSize:18, fontWeight:800}}>💎 {it.balance}</span>
              </div>

              {/* Earn-more options */}
              <div style={{marginTop:14, display:'flex', flexDirection:'column', gap:8}}>
                <div style={{display:'flex', alignItems:'center', gap:12, padding:'10px 14px', background:'var(--arcade-light)', borderRadius:'var(--r-md)', textAlign:'left'}}>
                  <span style={{fontSize:22}}>💱</span>
                  <div style={{flex:1}}>
                    <div style={{fontSize:13, fontWeight:800}}>Exchange Lumi</div>
                    <div style={{fontSize:11, color:'var(--text-secondary)', fontWeight:600}}>1 ✨ → 💎 50</div>
                  </div>
                  <span style={{color:'var(--text-hint)', fontSize:14}}>›</span>
                </div>
                <div style={{display:'flex', alignItems:'center', gap:12, padding:'10px 14px', background:'var(--diary-light)', borderRadius:'var(--r-md)', textAlign:'left'}}>
                  <span style={{fontSize:22}}>🎯</span>
                  <div style={{flex:1}}>
                    <div style={{fontSize:13, fontWeight:800}}>Complete missions</div>
                    <div style={{fontSize:11, color:'var(--text-secondary)', fontWeight:600}}>Earn up to 💎 60 today</div>
                  </div>
                  <span style={{color:'var(--text-hint)', fontSize:14}}>›</span>
                </div>
              </div>

              <button className="btn" style={{marginTop:18, width:'100%'}}>Maybe later</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { SettingsScreen, PurchaseModal });

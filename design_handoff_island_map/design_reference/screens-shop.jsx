// screens-shop.jsx — Shop, Inventory, Collection, Onboarding

// ─── 6) Shop ─────────────────────────────────────────────────────────────
function Shop({ tab='evolution' }) {
  const tabs = [
    { id:'rewards', lbl:'🎁 Rewards' },
    { id:'evolution', lbl:'🧬 Evolution' },
    { id:'food', lbl:'🍖 Food' },
    { id:'decor', lbl:'🌿 Decor' },
    { id:'exchange', lbl:'💱 Exchange' },
  ];

  const items = {
    evolution: [
      {n:'1st Stone A', e:'💎', p:50, c:'💎'},
      {n:'1st Stone B', e:'🔮', p:50, c:'💎'},
      {n:'2nd Stone', e:'💠', p:80, c:'💎'},
      {n:'Legend 1st A', e:'⚡', p:10, c:'✨'},
      {n:'Legend 1st B', e:'🌙', p:10, c:'✨'},
      {n:'Legend 2nd', e:'👑', p:20, c:'✨'},
    ],
    food: [
      {n:'Small Food', e:'🍪', p:20, c:'💎', desc:'+50 XP'},
      {n:'Big Food', e:'🍰', p:50, c:'💎', desc:'+150 XP'},
      {n:'Special Food', e:'🍱', p:90, c:'💎', desc:'+300 XP'},
    ],
    decor: [
      {n:'Mushroom Lantern', e:'🍄', p:30, c:'💎'},
      {n:'Signpost', e:'🪧', p:40, c:'💎'},
      {n:'Honey Jar', e:'🍯', p:50, c:'💎'},
      {n:'Cabin', e:'🏡', p:60, c:'💎', owned:true},
      {n:'Fairy Gate', e:'⛩️', p:80, c:'💎'},
      {n:'Treehouse', e:'🌲', p:120, c:'💎'},
      {n:'Firefly Effect', e:'🪰', p:100, c:'💎'},
      {n:'Flower Rain', e:'🌸', p:150, c:'💎'},
      {n:'Forest Mist', e:'🌫️', p:200, c:'💎'},
    ],
  };

  const showItems = items[tab] || items.evolution;

  return (
    <div className="gi-screen">
      <window.TopBar/>
      <div style={{padding:'18px 20px 8px'}}>
        <h1 className="gi-h1" style={{fontSize:26, margin:0}}>Shop</h1>
        <div style={{fontSize:13, color:'var(--text-secondary)'}}>Spend Lumi to grow your island</div>
      </div>
      <div className="tabs">
        {tabs.map(t => <div key={t.id} className={'tab ' + (t.id===tab?'active':'')}>{t.lbl}</div>)}
      </div>
      <div style={{flex:1, padding: 20, overflowY:'auto', background:'var(--bg-page)'}}>
        {tab === 'exchange' ? (
          <div style={{maxWidth: 460, margin: '20px auto', textAlign:'center'}}>
            <div className="card" style={{padding: 28}}>
              <div className="gi-h2" style={{fontSize:18,marginBottom: 10}}>Exchange Lumi → Legend Lumi</div>
              <div style={{fontSize:13, color:'var(--text-secondary)', marginBottom: 20}}>100 💎 = 1 ✨</div>
              <div style={{display:'flex',gap:12,alignItems:'center',justifyContent:'center'}}>
                <div style={{padding:16, background:'var(--rewards-light)', borderRadius:12, minWidth:120}}>
                  <div style={{fontSize:11,fontWeight:700,color:'var(--rewards-ink)'}}>FROM</div>
                  <div style={{fontSize:24,fontWeight:800,marginTop:4}}>💎 100</div>
                </div>
                <div style={{fontSize:24,color:'var(--text-hint)'}}>→</div>
                <div style={{padding:16, background:'var(--diary-light)', borderRadius:12, minWidth:120}}>
                  <div style={{fontSize:11,fontWeight:700,color:'var(--diary-ink)'}}>TO</div>
                  <div style={{fontSize:24,fontWeight:800,marginTop:4}}>✨ 1</div>
                </div>
              </div>
              <button className="btn btn-primary" style={{marginTop:20, width:'100%'}}>Exchange</button>
            </div>
          </div>
        ) : (
          <div style={{display:'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 12}}>
            {showItems.map((it,i) => (
              <div key={i} className="shop-item">
                {it.owned && <div className="badge-owned">Owned</div>}
                <div className="em">{it.e}</div>
                <div className="nm">{it.n}</div>
                {it.desc && <div style={{fontSize:11,color:'var(--text-secondary)'}}>{it.desc}</div>}
                <div className="pr" style={{color: it.c==='✨'?'var(--diary-ink)':'var(--rewards-ink)'}}>{it.c} {it.p}</div>
                <button className="btn btn-primary" style={{padding:'6px 14px',minHeight:32,fontSize:13,width:'100%'}} disabled={it.owned}>{it.owned?'Owned':'Buy'}</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── 7) Inventory + Collection ───────────────────────────────────────────
function InventoryCollection({ view='inventory' }) {
  const inv = [
    { n:'Small Food', e:'🍪', q:3, t:'Food'},
    { n:'Big Food', e:'🍰', q:1, t:'Food'},
    { n:'1st Stone A', e:'💎', q:2, t:'Evolution'},
    { n:'2nd Stone', e:'💠', q:1, t:'Evolution'},
    { n:'Mushroom Lantern', e:'🍄', q:1, t:'Decor'},
    { n:'Cabin', e:'🏡', q:1, t:'Decor'},
  ];
  const dexZones = ['forest','ocean','savanna','space'];
  const completion = { forest:[true,false,false,false,false], ocean:[false,false,false,false,false], savanna:[true,false,false,false,false], space:[false,false,false,false,false] };

  return (
    <div className="gi-screen">
      <window.TopBar/>
      <div style={{padding:'18px 20px'}}>
        <h1 className="gi-h1" style={{fontSize:26,margin:0}}>{view==='inventory'?'Inventory':'Collection'}</h1>
        <div style={{fontSize:13,color:'var(--text-secondary)'}}>{view==='inventory'?'Items you own':'Characters you\'ve raised'}</div>
      </div>
      <div className="tabs">
        <div className={'tab ' + (view==='inventory'?'active':'')}>🎒 Inventory</div>
        <div className={'tab ' + (view==='collection'?'active':'')}>📖 Collection</div>
      </div>
      <div style={{flex:1, padding: 20, overflowY:'auto', background:'var(--bg-page)'}}>
        {view === 'inventory' ? (
          <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(120px, 1fr))', gap: 10}}>
            {inv.map((i,k) => (
              <div key={k} className="shop-item" style={{padding:14}}>
                <div className="em">{i.e}</div>
                <div className="nm">{i.n}</div>
                <div style={{fontSize:11,color:'var(--text-hint)'}}>{i.t}</div>
                <div style={{position:'absolute', top:6, right:8, fontSize:13, fontWeight:800, background:'var(--diary)', color:'#fff', borderRadius:999, padding:'2px 8px'}}>×{i.q}</div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{display:'flex',flexDirection:'column',gap:18}}>
            {dexZones.map(z => {
              const Z = window.ZONES[z]; const chars = window.CHARS[z]; const comp = completion[z];
              return (
                <div key={z}>
                  <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:8}}>
                    <span style={{fontSize:18}}>{Z.emoji}</span>
                    <div className="gi-h2" style={{fontSize:16,margin:0,color:Z.ink}}>{Z.lbl}</div>
                    <div style={{fontSize:12,color:'var(--text-hint)'}}>{comp.filter(Boolean).length}/5 complete</div>
                  </div>
                  <div style={{display:'flex',gap:10,flexWrap:'wrap'}}>
                    {chars.map((c,i) => {
                      const done = comp[i];
                      const useImg = z==='forest' && c.n==='Sprout'; // demo
                      return (
                        <div key={c.n} className={'dex-card ' + (done?'':'silhouette')}>
                          <div className="em">{c.e}</div>
                          <div className="name" style={{marginTop:6}}>{done?c.n:'???'}</div>
                          {done && <div style={{fontSize:9,color:'var(--text-hint)',marginTop:2}}>Apr 28</div>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
            {/* Legend section */}
            <div>
              <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:8}}>
                <span style={{fontSize:18}}>✨</span>
                <div className="gi-h2" style={{fontSize:16,margin:0,color:'var(--diary-ink)'}}>Legend</div>
                <div className="chip chip-locked">🔒 Locked</div>
              </div>
              <div style={{display:'flex',gap:10,flexWrap:'wrap'}}>
                {window.CHARS.legend.map((c,i)=>(
                  <div key={c.n} className="dex-card silhouette">
                    <div className="em">{c.e}</div>
                    <div className="name" style={{marginTop:6}}>???</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── 8) Onboarding ───────────────────────────────────────────────────────
function Onboarding({ step='greet' }) {
  if (step === 'greet') return (
    <div className="gi-screen onb-card">
      <div style={{textAlign:'center', maxWidth: 420, padding: 24}}>
        <div className="float" style={{fontSize: 80, marginBottom: 12}}>🌟</div>
        <div className="gi-hand" style={{fontSize: 36, color:'var(--diary-ink)'}}>Hi! I'm Lumi</div>
        <div className="gi-h1" style={{fontSize: 32, margin: '8px 0 14px'}}>Welcome to Gia's Island</div>
        <div style={{fontSize:15, color:'var(--text-secondary)', lineHeight: 1.6, marginBottom: 22}}>
          Study to earn XP, turn it into Lumi 💎, and raise your very own island friends.
        </div>
        <button className="btn btn-primary" style={{padding:'12px 28px',fontSize:16}}>Let's go →</button>
        <div style={{display:'flex',gap:6,justifyContent:'center',marginTop:20}}>
          <span style={{width:8,height:8,borderRadius:'50%',background:'var(--diary)'}}></span>
          <span style={{width:8,height:8,borderRadius:'50%',background:'rgba(0,0,0,.1)'}}></span>
          <span style={{width:8,height:8,borderRadius:'50%',background:'rgba(0,0,0,.1)'}}></span>
        </div>
      </div>
    </div>
  );
  if (step === 'zone') return (
    <div className="gi-screen onb-card">
      <div style={{textAlign:'center', padding:24, width:'100%', maxWidth: 720}}>
        <div className="gi-hand" style={{fontSize:24, color:'var(--diary-ink)'}}>Pick your first home</div>
        <div className="gi-h1" style={{fontSize:28, margin:'4px 0 22px'}}>Where will your friend live?</div>
        <div style={{display:'grid', gridTemplateColumns:'repeat(2, 1fr)', gap:12}}>
          {['forest','ocean','savanna','space'].map(z => {
            const Z = window.ZONES[z];
            return (
              <div key={z} style={{background:Z.light, border:'2px solid '+Z.color, borderRadius:18, padding:18, cursor:'pointer', textAlign:'center'}}>
                <div style={{fontSize:48}}>{Z.emoji}</div>
                <div className="gi-h2" style={{fontSize:18, marginTop:6, color:Z.ink}}>{Z.lbl}</div>
                <div style={{fontSize:12, color:'var(--text-secondary)',marginTop:4}}>Earn here from <b>{Z.subject}</b></div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
  if (step === 'char') return (
    <div className="gi-screen onb-card">
      <div style={{textAlign:'center', padding:24, width:'100%', maxWidth:760}}>
        <div className="gi-hand" style={{fontSize:24, color:'var(--math-ink)'}}>🌳 Forest friends</div>
        <div className="gi-h1" style={{fontSize:28, margin:'4px 0 22px'}}>Pick your first friend</div>
        <div style={{display:'flex', gap: 10, justifyContent:'center'}}>
          {window.CHARS.forest.map((c,i) => (
            <div key={c.n} style={{background:'#fff', border:'2px solid ' + (i===1?'var(--math)':'var(--border-subtle)'), borderRadius:14, padding:14, width:120, textAlign:'center', cursor:'pointer'}}>
              <div style={{fontSize:48, filter: i===0||i===1?'none':'brightness(0) opacity(.18)'}}>{c.e}</div>
              <div style={{fontSize:13,fontWeight:800,marginTop:6}}>{i<=1?c.n:'???'}</div>
              {i>1 && <div style={{fontSize:10, color:'var(--text-hint)', marginTop:2}}>Complete prev</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
  // name step
  return (
    <div className="gi-screen onb-card">
      <div style={{textAlign:'center', padding:24, maxWidth:420}}>
        <div className="gi-hand" style={{fontSize:24, color:'var(--math-ink)'}}>almost there!</div>
        <div className="gi-h1" style={{fontSize:28, margin:'4px 0 18px'}}>Name your Clover 🍀</div>
        <img src="img/clover_baby.png" style={{width:180,height:180,objectFit:'contain'}} className="float"/>
        <input type="text" defaultValue="Clover" maxLength={8} style={{display:'block', margin:'14px auto', padding:'12px 18px', fontSize:18, fontFamily:'var(--font-display)', fontWeight:700, textAlign:'center', border:'2px solid var(--diary)', borderRadius:14, width:200, outline:'none'}}/>
        <div style={{fontSize:11, color:'var(--text-hint)', marginBottom:12}}>Up to 8 characters · can't be changed later</div>
        <button className="btn btn-primary" style={{padding:'12px 28px'}}>Confirm →</button>
      </div>
    </div>
  );
}

window.Shop = Shop;
window.InventoryCollection = InventoryCollection;
window.Onboarding = Onboarding;

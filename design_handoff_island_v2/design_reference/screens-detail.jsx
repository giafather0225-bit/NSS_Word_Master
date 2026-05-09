// screens-detail.jsx — Zone Detail, Character Detail, Evolution Modal, Complete Modal

const CLOVER_IMG = {
  baby: 'img/clover_baby.png',
  mid_a: 'img/clover_mid_a.png',
  mid_b: 'img/clover_mid_b.png',
  final_a: 'img/clover_final_a.png',
  final_b: 'img/clover_final_b.png',
};

// ─── Gauge styles ────────────────────────────────────────────────────────
function GaugeBar({ label, val, kind='h', icon }) {
  return (
    <div className="gauge-row">
      <span className="lbl">{icon} {label}</span>
      <div className="gauge-bar" style={{flex:1}}>
        <i className={kind} style={{width: val+'%', background: kind==='h'? 'linear-gradient(90deg,#F4B27E,#EBA98C)':'linear-gradient(90deg,#F8C8D5,#E09AAE)'}} />
      </div>
      <span className="val">{val}%</span>
    </div>
  );
}
function GaugeHearts({ val, kind='h' }) {
  const filled = Math.round(val/20);
  const ic = kind==='h' ? '🍖' : '💕';
  return (
    <div className="gauge-heart-row">
      {Array.from({length:5}).map((_,i)=>(
        <span key={i} className={'h ' + (i<filled?'full':'empty')}>{ic}</span>
      ))}
    </div>
  );
}
function GaugeDonut({ val, color='#EBA98C', label='' }) {
  const r = 22; const C = 2*Math.PI*r;
  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:4}}>
      <svg width="56" height="56" viewBox="0 0 56 56">
        <circle cx="28" cy="28" r={r} stroke="rgba(0,0,0,.08)" strokeWidth="6" fill="none"/>
        <circle cx="28" cy="28" r={r} stroke={color} strokeWidth="6" fill="none"
          strokeDasharray={C} strokeDashoffset={C*(1-val/100)} strokeLinecap="round"
          transform="rotate(-90 28 28)"/>
        <text x="28" y="33" textAnchor="middle" fontSize="13" fontWeight="800" fill="#2B2722">{val}</text>
      </svg>
      <div style={{fontSize:11, fontWeight:700, color:'var(--text-secondary)'}}>{label}</div>
    </div>
  );
}

// ─── 2) Zone Detail ──────────────────────────────────────────────────────
function ZoneDetail({ zone='forest', gaugeStyle='bar', mood='happy' }) {
  const z = window.ZONES[zone];
  const moods = {
    happy: { txt: 'Clover is so happy today! 🌟', hunger: 85, happy: 78 },
    sad: { txt: 'Clover seems a little down...', hunger: 38, happy: 18 },
    hungry: { txt: 'Clover is really hungry! 🍖', hunger: 12, happy: 60 },
  };
  const m = moods[mood] || moods.happy;
  const lowGauge = m.hunger < 20 || m.happy < 20;

  const renderGauges = () => {
    if (gaugeStyle === 'hearts') return (
      <div style={{display:'flex',flexDirection:'column',gap:14}}>
        <div><div style={{fontSize:13,fontWeight:700,color:'var(--text-secondary)',marginBottom:4}}>Hunger</div><GaugeHearts val={m.hunger} kind="h"/></div>
        <div><div style={{fontSize:13,fontWeight:700,color:'var(--text-secondary)',marginBottom:4}}>Happiness</div><GaugeHearts val={m.happy} kind="f"/></div>
      </div>
    );
    if (gaugeStyle === 'donut') return (
      <div style={{display:'flex',gap:18}}>
        <GaugeDonut val={m.hunger} color="#EBA98C" label="Hunger"/>
        <GaugeDonut val={m.happy} color="#E09AAE" label="Happy"/>
      </div>
    );
    return (
      <div>
        <GaugeBar label="Hunger" val={m.hunger} kind="h" icon="🍖"/>
        <GaugeBar label="Happiness" val={m.happy} kind="f" icon="💕"/>
      </div>
    );
  };

  return (
    <div className="gi-screen">
      <window.TopBar/>
      <div style={{flex:1, display:'flex', overflow:'hidden'}}>
        {/* LEFT — character area */}
        <div className={'zone-' + z.tint} style={{flex:1, position:'relative', display:'flex',alignItems:'center',justifyContent:'center'}}>
          <button className="btn btn-ghost" style={{position:'absolute',top:14,left:14}}>← Map</button>
          <div style={{textAlign:'center'}}>
            <div className="float" style={{display:'inline-block', filter:lowGauge?'saturate(.5)':'none'}}>
              <img src={CLOVER_IMG.baby} alt="Clover" style={{width:220,height:220,objectFit:'contain', filter:'drop-shadow(0 8px 16px rgba(0,0,0,.1))'}}/>
            </div>
            <div className="gi-hand" style={{fontSize:24, color: z.ink, marginTop:8}}>{m.txt}</div>
          </div>

          {/* Other completed/locked chars */}
          <div style={{position:'absolute',bottom:18,left:18,display:'flex',gap:10}}>
            {window.CHARS[zone].slice(1).map((c,i)=>(
              <div key={c.n} style={{width:48,height:48,borderRadius:'50%',background:'rgba(255,255,255,.6)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:24, filter:'grayscale(1) opacity(.4)'}}>{c.e}</div>
            ))}
          </div>
        </div>

        {/* RIGHT — info panel */}
        <div style={{width: 360, padding: 24, background:'var(--bg-card)', borderLeft:'1px solid var(--border-subtle)', overflowY:'auto'}}>
          <div style={{display:'flex',alignItems:'baseline',justifyContent:'space-between',marginBottom:14}}>
            <h2 className="gi-h1" style={{fontSize:30,margin:0}}>Clover</h2>
            <div className="chip" style={{background:z.light,color:z.ink}}>Lv.3</div>
          </div>

          {renderGauges()}

          <div style={{marginTop:18, padding:14, background:'var(--bg-page)', borderRadius:12}}>
            <div style={{fontSize:12,fontWeight:700,color:'var(--text-secondary)',marginBottom:6}}>XP TO EVOLVE</div>
            <div style={{display:'flex',justifyContent:'space-between',marginBottom:6,fontSize:13,fontWeight:700}}>
              <span>340 / 600</span>
              <span style={{color:z.ink}}>57%</span>
            </div>
            <div className="gauge-bar"><i style={{width:'57%',background:z.color}}/></div>
          </div>

          <div style={{display:'flex',justifyContent:'space-between',marginTop:14,fontSize:13,color:'var(--text-secondary)'}}>
            <div>Evolution stone <b style={{color:'var(--text-primary)'}}>None</b></div>
            <div>Lumi/day <b style={{color:'var(--text-primary)'}}>+0</b></div>
          </div>

          <div style={{display:'flex',gap:8,marginTop:20,flexDirection:'column'}}>
            <button className="btn btn-primary">🍖 Feed</button>
            <button className="btn" disabled>✨ Evolve (need stone)</button>
            <button className="btn btn-ghost">→ Open Shop</button>
          </div>

          {lowGauge && <div className="chip chip-warn" style={{marginTop:14, padding:'8px 12px'}}>❗ Gauges low — XP gain reduced 60%</div>}
        </div>
      </div>
    </div>
  );
}

// ─── 3) Character Detail with Evolution tree ─────────────────────────────
function CharacterDetail({ stage='baby' }) {
  const stages = [
    { id:'baby', img: CLOVER_IMG.baby, lbl:'Baby', sub:'Lv 1-5' },
    { id:'mid_a', img: CLOVER_IMG.mid_a, lbl:'Lucky Bloom', sub:'A · Lv 6-10' },
    { id:'mid_b', img: CLOVER_IMG.mid_b, lbl:'Moon Clover', sub:'B · Lv 6-10' },
    { id:'final_a', img: CLOVER_IMG.final_a, lbl:'Rainbow Royal', sub:'A · Final' },
    { id:'final_b', img: CLOVER_IMG.final_b, lbl:'Cosmic Clover', sub:'B · Final' },
  ];
  const unlocked = { baby:true, mid_a:false, mid_b:false, final_a:false, final_b:false };

  const StageImg = ({ s }) => (
    <div style={{width:90,height:90,borderRadius:18, background: unlocked[s.id]?'var(--math-light)':'var(--bg-surface)',display:'flex',alignItems:'center',justifyContent:'center',position:'relative',padding:8}}>
      <img src={s.img} alt={s.lbl} style={{width:'100%',height:'100%',objectFit:'contain', filter: unlocked[s.id]?'none':'grayscale(1) brightness(1.2) opacity(.55)'}}/>
      {!unlocked[s.id] && <div style={{position:'absolute',top:6,right:6,fontSize:14}}>🔒</div>}
    </div>
  );

  return (
    <div className="gi-screen">
      <window.TopBar/>
      <div style={{flex:1, padding: 24, overflowY:'auto', background: 'var(--math-light)'}}>
        <button className="btn btn-ghost" style={{marginBottom:14}}>← Forest</button>

        <div style={{display:'grid', gridTemplateColumns:'320px 1fr', gap:24}}>
          {/* Left - big character */}
          <div>
            <div className="card" style={{textAlign:'center', padding: 18}}>
              <img src={CLOVER_IMG.baby} alt="Clover" style={{width:240,height:240,objectFit:'contain'}} className="float"/>
              <div className="gi-h1" style={{fontSize:28, marginTop:6}}>Clover</div>
              <div className="chip" style={{background:'var(--math-light)',color:'var(--math-ink)',marginTop:6}}>🌳 Forest · Lv.3</div>
              <div className="gi-hand" style={{fontSize:18,color:'var(--math-ink)',marginTop:10}}>"A lucky three-leaf friend"</div>
            </div>
          </div>

          {/* Right - stats + evo tree */}
          <div style={{display:'flex',flexDirection:'column',gap:16}}>
            <div className="card">
              <div style={{display:'flex', gap: 18, alignItems:'center'}}>
                <GaugeDonut val={62} color="#EBA98C" label="Hunger"/>
                <GaugeDonut val={78} color="#E09AAE" label="Happy"/>
                <div style={{flex:1, paddingLeft: 18, borderLeft:'1px solid var(--border-subtle)'}}>
                  <div style={{fontSize:12,fontWeight:700,color:'var(--text-secondary)',marginBottom:4}}>XP THIS LEVEL</div>
                  <div style={{display:'flex',justifyContent:'space-between',fontSize:14,fontWeight:800,marginBottom:6}}>
                    <span>140 / 200</span>
                    <span style={{color:'var(--math-ink)'}}>70%</span>
                  </div>
                  <div className="gauge-bar"><i style={{width:'70%',background:'var(--math)'}}/></div>
                </div>
              </div>
            </div>

            {/* Evolution tree */}
            <div className="card">
              <div style={{fontSize:13,fontWeight:800,color:'var(--text-secondary)',marginBottom:14, letterSpacing:'.04em'}}>EVOLUTION PATH</div>
              <div style={{display:'flex',alignItems:'center',justifyContent:'center',gap:14,flexWrap:'wrap'}}>
                <div style={{textAlign:'center'}}>
                  <StageImg s={stages[0]}/>
                  <div style={{fontSize:11,fontWeight:700,marginTop:6}}>{stages[0].lbl}</div>
                  <div style={{fontSize:10,color:'var(--text-hint)'}}>{stages[0].sub}</div>
                </div>
                <div style={{color:'var(--text-hint)',fontSize:18}}>→</div>
                <div style={{display:'flex',flexDirection:'column',gap:8}}>
                  <div style={{textAlign:'center'}}>
                    <StageImg s={stages[1]}/>
                    <div style={{fontSize:11,fontWeight:700,marginTop:6}}>{stages[1].lbl}</div>
                    <div style={{fontSize:10,color:'var(--math-ink)'}}>+3% Eng XP</div>
                  </div>
                  <div style={{textAlign:'center'}}>
                    <StageImg s={stages[2]}/>
                    <div style={{fontSize:11,fontWeight:700,marginTop:6}}>{stages[2].lbl}</div>
                    <div style={{fontSize:10,color:'var(--rewards-ink)'}}>+3 Lumi/d</div>
                  </div>
                </div>
                <div style={{color:'var(--text-hint)',fontSize:18}}>→</div>
                <div style={{display:'flex',flexDirection:'column',gap:8}}>
                  <div style={{textAlign:'center'}}>
                    <StageImg s={stages[3]}/>
                    <div style={{fontSize:11,fontWeight:700,marginTop:6}}>{stages[3].lbl}</div>
                    <div style={{fontSize:10,color:'var(--math-ink)'}}>+5% Eng XP</div>
                  </div>
                  <div style={{textAlign:'center'}}>
                    <StageImg s={stages[4]}/>
                    <div style={{fontSize:11,fontWeight:700,marginTop:6}}>{stages[4].lbl}</div>
                    <div style={{fontSize:10,color:'var(--rewards-ink)'}}>+5 Lumi/d</div>
                  </div>
                </div>
              </div>
            </div>

            <div style={{display:'flex',gap:10}}>
              <button className="btn btn-primary" style={{flex:1}}>🍖 Feed Small Food (20💎)</button>
              <button className="btn" style={{flex:1}} disabled>✨ Evolve (Lv.5 required)</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── 4) Evolution Branch Modal (A vs B) ──────────────────────────────────
function EvolutionModal({ style='light' }) {
  return (
    <div className="gi-screen">
      <window.TopBar/>
      <div style={{flex:1, position:'relative', background:'var(--math-light)'}}>
        <div className="scrim" style={{padding:20}}>
          <div style={{background:'var(--bg-card)', borderRadius:24, padding:28, width:'92%', maxWidth: 720, boxShadow:'var(--shadow-modal)'}}>
            <div style={{textAlign:'center', marginBottom: 20}}>
              <div className="gi-hand" style={{fontSize: 22, color:'var(--diary-ink)'}}>Time to evolve!</div>
              <div className="gi-h1" style={{fontSize:26, margin:'4px 0 6px'}}>Choose Clover's path</div>
              <div style={{fontSize:13, color:'var(--text-secondary)'}}>This choice can't be undone.</div>
            </div>
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:14}}>
              <div style={{padding:20, border:'2px solid var(--math-soft)', borderRadius:18, background:'var(--math-light)', textAlign:'center', cursor:'pointer'}}>
                <img src={CLOVER_IMG.mid_a} style={{width:160,height:160,objectFit:'contain'}}/>
                <div className="gi-h2" style={{fontSize:18, marginTop:6}}>A · Lucky Bloom</div>
                <div style={{fontSize:12, color:'var(--math-ink)', marginTop:8, lineHeight:1.55}}>+3% English XP<br/>Hunger decays slower</div>
              </div>
              <div style={{padding:20, border:'2px solid var(--rewards-soft)', borderRadius:18, background:'var(--rewards-light)', textAlign:'center', cursor:'pointer'}}>
                <img src={CLOVER_IMG.mid_b} style={{width:160,height:160,objectFit:'contain'}}/>
                <div className="gi-h2" style={{fontSize:18, marginTop:6}}>B · Moon Clover</div>
                <div style={{fontSize:12, color:'var(--rewards-ink)', marginTop:8, lineHeight:1.55}}>+3 Lumi production / day<br/>Happiness decays slower</div>
              </div>
            </div>
            <div style={{display:'flex', gap:10, marginTop:22, justifyContent:'center'}}>
              <button className="btn">Cancel</button>
              <button className="btn btn-primary">Choose A · Lucky Bloom</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── 5) Character Complete celebration ───────────────────────────────────
function CompleteModal() {
  return (
    <div className="gi-screen">
      <window.TopBar/>
      <div style={{flex:1, position:'relative', background:'radial-gradient(circle at 50% 50%, #FFE8C9 0%, #FBEEF2 50%, #F2ECFA 100%)', overflow:'hidden'}}>
        {/* sparkle particles */}
        {Array.from({length: 24}).map((_,i)=>(
          <div key={i} style={{
            position:'absolute',
            left: (i*37 % 100) + '%', top: ((i*53)%100) + '%',
            fontSize: 12 + (i%4)*4, opacity:.7,
            transform: `rotate(${i*23}deg)`,
          }}>{['✨','⭐','💫','🌟'][i%4]}</div>
        ))}
        <div style={{position:'absolute', inset:0, display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',padding:24}}>
          <div className="gi-hand" style={{fontSize:32, color:'var(--diary-ink)', marginBottom: 8}}>congratulations!</div>
          <div className="gi-h1" style={{fontSize: 44, textAlign:'center'}}>Clover is complete! 🎉</div>
          <img src={CLOVER_IMG.final_a} style={{width:280,height:280,objectFit:'contain', filter:'drop-shadow(0 12px 24px rgba(0,0,0,.15))'}}/>
          <div style={{background:'var(--bg-card)', padding: 18, borderRadius:18, marginTop: 4, textAlign:'center', minWidth: 320, boxShadow:'var(--shadow-soft)'}}>
            <div className="gi-h2" style={{fontSize:18}}>Rainbow Royal · Final A</div>
            <div style={{fontSize:13, color:'var(--text-secondary)', marginTop:8, lineHeight:1.6}}>
              English XP <b style={{color:'var(--math-ink)'}}>+5%</b> forever<br/>
              Daily Lumi production <b style={{color:'var(--rewards-ink)'}}>+5</b>
            </div>
          </div>
          <button className="btn btn-primary" style={{marginTop: 18, padding:'12px 28px'}}>Return to Forest</button>
        </div>
      </div>
    </div>
  );
}

window.GaugeBar = GaugeBar;
window.GaugeHearts = GaugeHearts;
window.GaugeDonut = GaugeDonut;
window.ZoneDetail = ZoneDetail;
window.CharacterDetail = CharacterDetail;
window.EvolutionModal = EvolutionModal;
window.CompleteModal = CompleteModal;

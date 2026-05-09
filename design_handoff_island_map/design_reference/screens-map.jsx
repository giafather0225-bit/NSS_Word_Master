// screens-map.jsx — REAL island background version

const ZONES = {
  forest:  { lbl:'Forest',  emoji:'🌳', subject:'English', color:'#5BA37A', ink:'#2F5A3F', light:'#EEF7F2' },
  ocean:   { lbl:'Ocean',   emoji:'🌊', subject:'Math',    color:'#4F8FBF', ink:'#1F4870', light:'#EEF4FA' },
  savanna: { lbl:'Savanna', emoji:'🦁', subject:'Diary',   color:'#D4A33C', ink:'#5C3F0E', light:'#FBF3DE' },
  space:   { lbl:'Space',   emoji:'🚀', subject:'Review',  color:'#7C5FB8', ink:'#3D2A6E', light:'#F2ECFA' },
  legend:  { lbl:'Legend',  emoji:'✨', subject:'All',     color:'#E09AAE', ink:'#84425A', light:'#FBEEF2' },
};
const CHARS = {
  forest:  [{n:'Sprout',e:'🌱'},{n:'Clover',e:'🍀'},{n:'Mossy',e:'🪨'},{n:'Fernlie',e:'🌿'},{n:'Blossie',e:'🌸'}],
  ocean:   [{n:'Axie',e:'🐠'},{n:'Finn',e:'🐟'},{n:'Delphi',e:'🐬'},{n:'Bubbles',e:'🐡'},{n:'Starla',e:'⭐'}],
  savanna: [{n:'Mane',e:'🐴'},{n:'Ellie',e:'🐘'},{n:'Leo',e:'🦁'},{n:'Zuri',e:'🦒'},{n:'Rhino',e:'🦏'}],
  space:   [{n:'Lumie',e:'👽'},{n:'Twinkle',e:'⭐'},{n:'Orbee',e:'🪐'},{n:'Nova',e:'☄️'},{n:'Cosmo',e:'🤖'}],
  legend:  [{n:'Dragon',e:'🐉'},{n:'Unicorn',e:'🦄'},{n:'Phoenix',e:'🔥'},{n:'Gumiho',e:'🦊'},{n:'Qilin',e:'🐲'}],
};

function TopBar({ lumi=1250, legend=30, streak=5, dark=false }) {
  return (
    <div className="gi-topbar" style={dark?{background:'rgba(37,35,54,.92)',borderColor:'#3A3750',color:'#fff'}:{background:'rgba(255,255,255,.92)', backdropFilter:'blur(10px)'}}>
      <div className="gi-topbar-left">
        <span className="gi-stat gi-stat--lumi"><span className="ico">💎</span>{lumi.toLocaleString()}</span>
        <span className="gi-stat gi-stat--legend"><span className="ico">✨</span>{legend}</span>
        <span className="gi-stat gi-stat--streak"><span className="ico">🔥</span>{streak} days</span>
      </div>
      <div className="gi-topbar-right">
        <button className="gi-iconbtn" title="Inventory">🎒</button>
        <button className="gi-iconbtn" title="Collection">📖</button>
        <button className="gi-iconbtn" title="Settings">⚙️</button>
      </div>
    </div>
  );
}

function StreakDots({ count=5, total=7 }) {
  return (
    <div style={{display:'flex',gap:6,alignItems:'center'}}>
      {Array.from({length:total}).map((_,i) => (
        <span key={i} style={{
          width: 14, height: 14, borderRadius: '50%',
          background: i < count ? '#EEC770' : 'rgba(0,0,0,.12)',
          border: i < count ? '2px solid #D8AE55' : '2px solid transparent',
          display:'inline-block', position:'relative',
        }}>
          {i === count - 1 && <span style={{position:'absolute',top:-12,left:-3,fontSize:14}}>🔥</span>}
        </span>
      ))}
    </div>
  );
}

// Hotspot positions calibrated to island.png (1376×768)
// Approx fractional coordinates for the 5 zones in the artwork
// Calibrated to img/island_map.png (1376×768)
const HOTSPOTS = {
  forest:  { left:'17%',  top:'42%',  w: 150, h: 150 },   // wooded area + mushrooms
  space:   { left:'47%',  top:'22%',  w: 110, h: 110 },   // observatory dome (centered on dome)
  legend:  { left:'50%',  top:'50%',  w: 130, h: 130 },   // central crystals
  ocean:   { left:'88%',  top:'60%',  w: 130, h: 110 },   // coral reef + seaweed (below lighthouse)
  savanna: { left:'48%',  top:'80%',  w: 170, h: 110 },   // grassland bottom
};

function ZoneHotspot({ z, pos, locked=false, alert=null, ready=false, hideLabel=false }) {
  return (
    <div className="zone-hotspot" style={{
      position:'absolute',
      left: pos.left, top: pos.top,
      width: pos.w, height: pos.h,
      transform: 'translate(-50%, -50%)',
      cursor: locked ? 'help' : 'pointer',
    }}>
      {/* clickable circle ring */}
      <div style={{
        position:'absolute', inset:0,
        borderRadius:'50%',
        border: locked ? '2px dashed rgba(255,255,255,.7)' : '3px solid '+z.color,
        background: locked
          ? 'radial-gradient(circle, rgba(255,255,255,.5), rgba(243,210,220,.35))'
          : 'radial-gradient(circle, rgba(255,255,255,.18), transparent 70%)',
        boxShadow: locked ? 'inset 0 0 30px rgba(255,255,255,.6)' : '0 6px 20px rgba(0,0,0,.18), inset 0 0 0 6px rgba(255,255,255,.25)',
        backdropFilter: locked ? 'blur(3px)' : 'none',
      }}/>
      {/* label pill */}
      {!hideLabel && <div style={{
        position:'absolute', left:'50%', bottom: -10,
        transform:'translateX(-50%)',
        background: locked ? 'rgba(255,255,255,.85)' : '#fff',
        border: '2px solid '+z.color,
        color: z.ink,
        borderRadius: 999, padding:'4px 12px',
        fontFamily:"'Quicksand', sans-serif", fontWeight: 800, fontSize: 13,
        whiteSpace:'nowrap',
        boxShadow: '0 4px 10px rgba(0,0,0,.12)',
        display:'flex', alignItems:'center', gap:5,
      }}>
        {locked && '🔒 '}<span>{z.emoji} {z.lbl}</span>
      </div>}
      {/* badges */}
      {alert === 'warn' && <div style={{position:'absolute', top:-4, right:6, background:'#D97A7A', color:'#fff', borderRadius:'50%', width:26,height:26, display:'flex',alignItems:'center',justifyContent:'center', fontWeight:800, fontSize:14, boxShadow:'0 2px 6px rgba(0,0,0,.3)'}}>!</div>}
      {ready && <div className="pulse" style={{position:'absolute', top:-4, right:6, background:'#EEC770', color:'#7A5A1E', borderRadius:'50%', width:28,height:28, display:'flex',alignItems:'center',justifyContent:'center', fontWeight:800, fontSize:14, boxShadow:'0 2px 6px rgba(0,0,0,.3)'}}>✨</div>}
      {/* lock progress */}
      {locked && <div style={{position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', flexDirection:'column'}}>
        <div style={{fontSize: 26}}>🔒</div>
        <div style={{fontSize:10, fontWeight:800, color:z.ink, marginTop:2}}>1 / 4</div>
      </div>}
    </div>
  );
}

function IslandMap({ night=false, lumiToast=false, zoneProgress=4 }) {
  const isNight = night;
  const legendLocked = zoneProgress < 5;
  const zoneOrder = ['forest','ocean','savanna','space','legend'];

  return (
    <div className="gi-screen">
      <div style={{flex:1, position:'relative', overflow:'hidden', background:'#1a3a52'}}>
        {/* ISLAND BACKGROUND */}
        <img src="img/island_map.png" alt="Gia's Island"
          style={{
            position:'absolute', inset:0,
            width:'100%', height:'100%', objectFit:'cover',
            filter: isNight ? 'brightness(.5) saturate(.7) hue-rotate(-15deg)' : 'none',
            transition:'filter .4s ease',
          }}/>

        {/* Night overlay tint + stars */}
        {isNight && <>
          <div style={{position:'absolute', inset:0, background:'radial-gradient(ellipse at top, rgba(20,20,60,.2), rgba(10,10,40,.5))'}}/>
          <div className="stars"/>
          <div style={{position:'absolute', top:'5%', right:'6%', fontSize:48, filter:'drop-shadow(0 0 12px #FFE49A)'}}>🌙</div>
        </>}
        {!isNight && <div style={{position:'absolute', top:'4%', right:'6%', fontSize:42, filter:'drop-shadow(0 0 18px rgba(255,228,154,.7))'}}>☀️</div>}

        {/* TOP BAR — floating, glassy */}
        <div style={{position:'absolute', top:0, left:0, right:0, zIndex:5}}>
          <TopBar dark={isNight}/>
        </div>

        {/* ZONE HOTSPOTS */}
        {zoneOrder.map(key => {
          const z = ZONES[key]; const pos = HOTSPOTS[key];
          const locked = key === 'legend' && legendLocked;
          const alert = key === 'ocean' ? 'warn' : null;
          const ready = key === 'forest' ? true : false;
          return <ZoneHotspot key={key} z={z} pos={pos} locked={locked} alert={alert} ready={ready}/>;
        })}

        {/* Active character bubbles near each zone */}
        {[
          {emo:'🍀', left:'12%', top:'56%', delay:'0s'},      // near forest
          {emo:'🐠', left:'80%', top:'52%', delay:'.5s'},     // near ocean coral (below lighthouse)
          {emo:'🦁', left:'62%', top:'88%', delay:'.8s'},     // near savanna
          {emo:'👽', left:'58%', top:'24%', delay:'1.2s'},    // near space dome
        ].map((c,i) => (
          <div key={i} className="map-char float" style={{position:'absolute', left:c.left, top:c.top, transform:'translateX(-50%)', animationDelay:c.delay}}>
            <div style={{background:'rgba(255,255,255,.96)', borderRadius:'50%', width:40, height:40, display:'flex',alignItems:'center',justifyContent:'center', fontSize:22, boxShadow:'0 4px 10px rgba(0,0,0,.2)', border:'2px solid #fff'}}>{c.emo}</div>
          </div>
        ))}

        {/* STREAK PANEL bottom-left */}
        <div style={{position:'absolute', left: 16, bottom: 16, padding:'12px 16px', background:'rgba(255,255,255,.92)', borderRadius:14, boxShadow:'0 4px 14px rgba(0,0,0,.18)', display:'flex',gap:14,alignItems:'center', backdropFilter:'blur(8px)'}}>
          <div>
            <div style={{fontSize:10, fontWeight:800, color:'#706659', letterSpacing:'.06em'}}>STREAK</div>
            <div style={{marginTop:4}}><StreakDots count={5} total={7}/></div>
          </div>
        </div>

        {/* TODAY PANEL bottom-right */}
        <div style={{position:'absolute', right:16, bottom:16, width: 230, background:'rgba(255,255,255,.94)', borderRadius:14, padding:'12px 14px', boxShadow:'0 4px 14px rgba(0,0,0,.18)', backdropFilter:'blur(8px)'}}>
          <div style={{fontFamily:"'Quicksand'", fontWeight:800, fontSize:14, marginBottom:6}}>Today on the Island</div>
          <div style={{fontSize:12, lineHeight:1.7, color:'#706659'}}>
            <div>🌱 <b style={{color:'#2B2722'}}>Sprout</b> · ready to evolve ✨</div>
            <div>🐠 <b style={{color:'#2B2722'}}>Axie</b> · feeling hungry ❗</div>
            <div>🦁 <b style={{color:'#2B2722'}}>Leo</b> · happy &amp; full</div>
          </div>
        </div>

        {lumiToast && <div className="toast lumi">💎 +20 Lumi earned!</div>}
      </div>
    </div>
  );
}

window.IslandMap = IslandMap;
window.TopBar = TopBar;
window.StreakDots = StreakDots;
window.ZONES = ZONES;
window.CHARS = CHARS;

// Diary Screens — 4 views: Home / Write / Entry / Calendar
// Palette: Sweet Pink (--diary-*). Two style variants: Decorated ↔ Minimal
// Modes: Journal (prompted, mood-first), Free Write (open, AI feedback)

const { useState: useStateD, useEffect: useEffectD } = React;

/* Style variant — Diary uses DECORATED by default (section-level rule).
 * Preview-only hook: reads localStorage so Diary Preview.html can toggle Decorated ↔ Minimal
 * for comparison. In production app, this always resolves to 'decorated'.
 */
function useDiaryStyle() {
  const [style, setStyle] = useStateD(() => localStorage.getItem('nss.diary.style') || 'decorated');
  useEffectD(() => { localStorage.setItem('nss.diary.style', style); }, [style]);
  return [style, setStyle];
}

/* ═══════════════════════════════════════════════
   Shared primitives
   ═══════════════════════════════════════════════ */

const MOODS = [
  { id: 'great',   label: 'great',   tone: 'var(--diary-primary)',                    dot: '#E09AAE' },
  { id: 'happy',   label: 'happy',   tone: 'var(--arcade-primary)',                   dot: '#EEC770' },
  { id: 'calm',    label: 'calm',    tone: 'var(--math-primary)',                     dot: '#8AC4A8' },
  { id: 'curious', label: 'curious', tone: 'var(--english-primary)',                  dot: '#7FA8CC' },
  { id: 'tired',   label: 'tired',   tone: 'var(--rewards-primary)',                  dot: '#B8A4DC' },
  { id: 'sad',     label: 'sad',     tone: 'var(--review-primary)',                   dot: '#EBA98C' },
];

function DiaryPill({ children, tone = 'var(--diary-ink)', soft = 'var(--diary-soft)' }) {
  return (
    <span style={{
      padding: '4px 10px', borderRadius: 999,
      background: soft, color: tone,
      fontSize: 10.5, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase',
      display: 'inline-flex', alignItems: 'center', gap: 6,
    }}>{children}</span>
  );
}

function MoodDot({ mood, size = 10 }) {
  const m = MOODS.find(x => x.id === mood);
  if (!m) return <span style={{ width: size, height: size, borderRadius: 999, background: 'var(--border-subtle)', display: 'inline-block' }}/>;
  return <span style={{ width: size, height: size, borderRadius: 999, background: m.dot, display: 'inline-block' }}/>;
}

/* Top chrome: back + eyebrow + title + right slot */
function DiaryChrome({ eyebrow, title, subtitle, onNavigate, rightSlot, onBack }) {
  return (
    <header style={{
      padding: '20px 32px 16px',
      borderBottom: '1px solid var(--border-subtle)',
      background: 'var(--bg-page)',
      display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 24,
      flexShrink: 0,
    }}>
      <div>
        {/* Back button — icon-only, subtle, clearly separated from eyebrow */}
        <button
          onClick={() => onBack ? onBack() : onNavigate && onNavigate('home')}
          aria-label={onBack ? 'Back to Diary' : 'Back to Home'}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            fontSize: 12, color: 'var(--text-secondary)',
            marginBottom: 14,
            padding: '6px 10px 6px 6px',
            borderRadius: 999,
            background: 'transparent',
            border: 'none',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-card)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
        >
          <Icon name="chevron-left" size={14}/>
          {onBack ? 'Diary' : 'Home'}
        </button>
        <div><DiaryPill>{eyebrow}</DiaryPill></div>
        <div style={{
          fontFamily: 'var(--font-family-display)',
          fontSize: 32, fontWeight: 600, letterSpacing: '-0.02em',
          color: 'var(--diary-ink)', marginTop: 8, lineHeight: 1.1,
        }}>{title}</div>
        {subtitle && (
          <div style={{ marginTop: 4, fontSize: 13, color: 'var(--text-secondary)' }}>
            {subtitle}
          </div>
        )}
      </div>
      <div style={{ flexShrink: 0 }}>{rightSlot}</div>
    </header>
  );
}

/* Washi-tape corner decoration (decorated mode) */
function WashiTape({ color = 'var(--diary-soft)', rotate = -6, top = -8, left = 20, width = 90 }) {
  return (
    <div style={{
      position: 'absolute', top, left, width, height: 18,
      background: color, opacity: 0.85,
      transform: `rotate(${rotate}deg)`,
      boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
      backgroundImage: 'repeating-linear-gradient(90deg, rgba(255,255,255,0.3) 0 6px, transparent 6px 12px)',
      pointerEvents: 'none',
    }}/>
  );
}

/* ═══════════════════════════════════════════════
   Screen 1 — Diary Home
   ═══════════════════════════════════════════════ */
function DiaryHome({ onNavigate }) {
  const [style] = useDiaryStyle();
  const decorated = style === 'decorated';

  // Data
  const stats = {
    entries: 18,
    streak: 5,
    words: 642,
    dayOff: 2,
  };

  const weekMood = [
    { day: 'Mon', mood: 'happy' },
    { day: 'Tue', mood: 'calm' },
    { day: 'Wed', mood: 'great' },
    { day: 'Thu', mood: 'curious' },
    { day: 'Fri', mood: 'happy' },
    { day: 'Sat', mood: null },
    { day: 'Sun', mood: null },
  ];

  // Photos array: Journal entries may include 1-3 photos. Free Write has none.
  // `photos: []` = no photo → polaroid falls back to mood-gradient swatch.
  // Reduced from 4 to 3 for fit-in-viewport layout
  const recent = [
    { id: 'e1', date: 'Yesterday',   dateLong: 'APR 23',  mood: 'happy',   type: 'journal',  title: 'The yellow fish',
      text: 'We went to the aquarium. I saw a yellow fish that looked like butter.',
      photos: [{ tone: '#F6D98A' }, { tone: '#8AC4A8' }] },
    { id: 'e2', date: 'Wed',         dateLong: 'APR 22',  mood: 'great',   type: 'journal',  title: 'Brave day',
      text: 'My reading test was hard but I kept going. Mom said I was brave.',
      photos: [{ tone: '#E09AAE' }] },
    { id: 'e3', date: 'Tue',         dateLong: 'APR 21',  mood: 'curious', type: 'free',     title: 'Whisper',
      text: 'I wrote five sentences with new words. My favorite was whisper.',
      photos: [] },
  ];

  return (
    <div style={{ height: '100%', overflow: 'hidden', background: 'var(--bg-page)', display: 'flex', flexDirection: 'column' }}>
      <DiaryChrome
        eyebrow="Diary · Today"
        title="A little page for today"
        subtitle="Write what you feel, or free-write for fun."
        onNavigate={onNavigate}
        rightSlot={
          <button
            onClick={() => onNavigate('diary-write')}
            style={{
              padding: '10px 18px', borderRadius: 12,
              background: 'var(--diary-primary)', color: '#fff',
              fontSize: 13, fontWeight: 600,
              display: 'flex', alignItems: 'center', gap: 8,
              boxShadow: '0 4px 12px rgba(224,154,174,0.32)',
            }}
          >
            <Icon name="pen-tool" size={14}/>
            Start writing
          </button>
        }
      />

      {/* 2×2 grid — tuned for 1280×900 MacBook Air viewport, no scroll */}
      <div style={{
        flex: 1, minHeight: 0,
        padding: '20px 32px 24px',
        display: 'grid',
        gridTemplateColumns: '1.15fr 1fr',
        gridTemplateRows: 'auto 1fr',
        gap: 18,
      }}>
        {/* Top-left: Mode CTAs */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <ModeCTA
            mode="journal"
            title="Journal"
            copy="Pick your mood, answer a prompt, add photos."
            icon="book-open"
            decorated={decorated}
            onClick={() => onNavigate('diary-write')}
          />
          <ModeCTA
            mode="free"
            title="Free Write"
            copy="Write anything. AI gives gentle feedback."
            icon="sparkles"
            decorated={decorated}
            onClick={() => onNavigate('diary-write')}
          />
        </div>

        {/* Top-right: Prompt card */}
        <PromptCardV2 onStart={() => onNavigate('diary-write')} decorated={decorated}/>

        {/* Bottom-left: Week mood + Recent */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, minHeight: 0 }}>
          {/* Week mood strip */}
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
            borderRadius: 18, padding: '16px 18px', boxShadow: 'var(--shadow-soft)',
            position: 'relative', flexShrink: 0,
          }}>
            {decorated && <WashiTape color="var(--diary-soft)" rotate={-4} top={-9} left={28} width={90}/>}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12 }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>This week's mood</div>
                <div style={{ fontSize: 11, color: 'var(--text-hint)', marginTop: 1 }}>Tap a day to open that entry.</div>
              </div>
              <button
                onClick={() => onNavigate('diary-calendar')}
                style={{ fontSize: 11.5, color: 'var(--diary-primary)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 3 }}
              >
                Month view <Icon name="chevron-right" size={11}/>
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 8 }}>
              {weekMood.map(d => <WeekMoodCell key={d.day} d={d} decorated={decorated}/>)}
            </div>
          </div>

          {/* Recent — 3 polaroids with fixed aspect ratio so they never stretch */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1, minHeight: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Recent pages</div>
              <button
                onClick={() => onNavigate('diary-calendar')}
                style={{ fontSize: 11.5, color: 'var(--diary-primary)', fontWeight: 600 }}
              >See all</button>
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: 12,
              alignItems: 'start', // key — prevents polaroids from stretching to fill row
            }}>
              {recent.map((r, i) => decorated
                ? <PolaroidEntry key={r.id} entry={r} tilt={i === 1 ? 0 : (i === 0 ? -1.5 : 1.5)} onClick={() => onNavigate('diary-entry')}/>
                : <MinimalEntry key={r.id} entry={r} onClick={() => onNavigate('diary-entry')}/>
              )}
            </div>
          </div>
        </div>

        {/* Bottom-right: Stats + Streak combined */}
        <StatsWithStreak stats={stats} decorated={decorated}/>
      </div>
    </div>
  );
}

/* Stats — clean 2×2 tiles + Day off request CTA at bottom */
function StatsWithStreak({ stats, decorated }) {
  const [dayOffOpen, setDayOffOpen] = useStateD(false);
  const DAY_OFF_MAX = 2;
  const dayOffUsed = stats.dayOff || 0;
  const dayOffLeft = Math.max(DAY_OFF_MAX - dayOffUsed, 0);
  const canRequest = dayOffLeft > 0;

  return (
    <div style={{
      position: 'relative',
      background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
      borderRadius: 18, padding: 20,
      boxShadow: 'var(--shadow-soft)',
      display: 'flex', flexDirection: 'column', gap: 14,
      minHeight: 0,
    }}>
      {decorated && <WashiTape color="var(--math-soft)" rotate={5} top={-9} left={28} width={80}/>}

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexShrink: 0 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>This month</div>
          <div style={{ fontSize: 11, color: 'var(--text-hint)', marginTop: 1 }}>Your writing life so far.</div>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-hint)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          April
        </div>
      </div>

      {/* Stats grid — 2×2, fills available height */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 12,
        flex: 1, minHeight: 0,
      }}>
        <StatTile label="Entries" value={stats.entries}      sub="this month"   color="var(--diary-primary)"   icon="notebook"/>
        <StatTile label="Words"   value={stats.words}        sub="kept writing" color="var(--english-primary)" icon="edit"/>
        <StatTile label="Streak"  value={`${stats.streak}d`} sub="best: 11"     color="var(--arcade-primary)"  icon="flame"/>
        <StatTile label="Day off" value={`${dayOffUsed}/${DAY_OFF_MAX}`} sub={dayOffLeft > 0 ? `${dayOffLeft} left` : 'all used'} color="var(--rewards-primary)" icon="coffee"/>
      </div>

      {/* Day off request CTA */}
      <button
        onClick={() => canRequest && setDayOffOpen(true)}
        disabled={!canRequest}
        style={{
          padding: '10px 14px', borderRadius: 12,
          background: canRequest ? 'var(--arcade-light)' : 'var(--bg-page)',
          color: canRequest ? 'var(--arcade-ink)' : 'var(--text-hint)',
          border: `1px solid ${canRequest ? 'var(--arcade-soft)' : 'var(--border-subtle)'}`,
          fontSize: 12, fontWeight: 600,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          cursor: canRequest ? 'pointer' : 'not-allowed',
          transition: 'all 0.15s ease',
        }}
        onMouseEnter={(e) => { if (canRequest) e.currentTarget.style.background = 'var(--arcade-soft)'; }}
        onMouseLeave={(e) => { if (canRequest) e.currentTarget.style.background = 'var(--arcade-light)'; }}
      >
        <Icon name="coffee" size={13}/>
        {canRequest ? 'Request a day off' : 'No day offs left this month'}
      </button>

      {dayOffOpen && (
        <DayOffRequestModal
          onClose={() => setDayOffOpen(false)}
          dayOffLeft={dayOffLeft}
          max={DAY_OFF_MAX}
        />
      )}
    </div>
  );
}

/* Day off request modal — child requests, parent approves */
function DayOffRequestModal({ onClose, dayOffLeft, max }) {
  const [date, setDate] = useStateD('');
  const [reason, setReason] = useStateD('');

  // Min date = tomorrow (ISO yyyy-mm-dd)
  const minDate = (() => {
    const d = new Date(); d.setDate(d.getDate() + 1);
    return d.toISOString().slice(0, 10);
  })();

  const canSubmit = !!date;

  useEffectD(() => {
    const esc = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', esc);
    return () => document.removeEventListener('keydown', esc);
  }, [onClose]);

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 100,
        background: 'rgba(60, 40, 20, 0.28)',
        display: 'grid', placeItems: 'center',
        padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Request a day off"
        style={{
          width: 420, maxWidth: '100%',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 18, padding: 22,
          boxShadow: 'var(--shadow-modal)',
          display: 'flex', flexDirection: 'column', gap: 16,
          position: 'relative',
        }}
      >
        <WashiTape color="var(--arcade-soft)" rotate={-4} top={-9} left={32} width={90}/>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 38, height: 38, borderRadius: 11,
            background: 'var(--arcade-primary)', color: '#fff',
            display: 'grid', placeItems: 'center',
          }}>
            <Icon name="coffee" size={17}/>
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-family-display)', fontSize: 20, fontWeight: 600, color: 'var(--diary-ink)', lineHeight: 1.1 }}>
              Take a day off?
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--text-secondary)', marginTop: 2 }}>
              {dayOffLeft} / {max} left this month
            </div>
          </div>
        </div>

        {/* Date picker */}
        <div>
          <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-hint)', display: 'block', marginBottom: 6 }}>
            Which day?
          </label>
          <input
            type="date"
            value={date}
            min={minDate}
            onChange={(e) => setDate(e.target.value)}
            style={{
              width: '100%', padding: '10px 12px',
              borderRadius: 10, border: '1px solid var(--border-subtle)',
              background: 'var(--bg-page)',
              fontSize: 13, fontFamily: 'var(--font-family, "Nunito")',
              color: 'var(--text-primary)',
              outline: 'none',
            }}
          />
          <div style={{ fontSize: 10.5, color: 'var(--text-hint)', marginTop: 4 }}>Future days only.</div>
        </div>

        {/* Reason (optional) */}
        <div>
          <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-hint)', display: 'block', marginBottom: 6 }}>
            Why? <span style={{ textTransform: 'none', letterSpacing: 0, fontWeight: 500, color: 'var(--text-hint)' }}>(optional)</span>
          </label>
          <input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Family trip, feeling sick"
            maxLength={60}
            style={{
              width: '100%', padding: '10px 12px',
              borderRadius: 10, border: '1px solid var(--border-subtle)',
              background: 'var(--bg-page)',
              fontSize: 13, fontFamily: 'var(--font-family, "Nunito")',
              color: 'var(--text-primary)',
              outline: 'none',
            }}
          />
        </div>

        {/* Parent approval note */}
        <div style={{
          padding: '10px 12px', borderRadius: 12,
          background: 'var(--diary-light)', border: '1px solid var(--diary-soft)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <Icon name="heart" size={13} color="var(--diary-primary)"/>
          <div style={{ fontSize: 11.5, color: 'var(--diary-ink)', lineHeight: 1.4 }}>
            Mom or Dad will see your request and say OK.
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{
              padding: '9px 16px', borderRadius: 10,
              background: 'var(--bg-page)', color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              fontSize: 12.5, fontWeight: 600, cursor: 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            onClick={() => {
              // POST /api/v1/day-offs { date, reason } → status = 'pending'
              onClose();
            }}
            disabled={!canSubmit}
            style={{
              padding: '9px 18px', borderRadius: 10,
              background: canSubmit ? 'var(--arcade-primary)' : 'var(--border-subtle)',
              color: canSubmit ? '#fff' : 'var(--text-hint)',
              border: 'none',
              fontSize: 12.5, fontWeight: 600,
              display: 'inline-flex', alignItems: 'center', gap: 6,
              cursor: canSubmit ? 'pointer' : 'not-allowed',
              boxShadow: canSubmit ? '0 3px 10px rgba(238,199,112,0.32)' : 'none',
            }}
          >
            <Icon name="check" size={12}/> Send request
          </button>
        </div>
      </div>
    </div>
  );
}

function StatTile({ label, value, sub, color, icon }) {
  return (
    <div style={{
      padding: '16px 18px', borderRadius: 14,
      background: 'var(--bg-page)', border: '1px solid var(--border-subtle)',
      display: 'flex', flexDirection: 'column', gap: 10,
      minHeight: 0,
    }}>
      <div style={{
        width: 38, height: 38, borderRadius: 11,
        background: color, color: '#fff',
        display: 'grid', placeItems: 'center',
        flexShrink: 0,
      }}>
        <Icon name={icon} size={17}/>
      </div>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontFamily: 'var(--font-family-display)', fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1, letterSpacing: '-0.01em' }}>
          {value}
        </div>
        <div style={{ fontSize: 10.5, color: 'var(--text-hint)', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: 6 }}>
          {label}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>{sub}</div>
      </div>
    </div>
  );
}

function ModeCTA({ mode, title, copy, icon, decorated, onClick }) {
  const isJournal = mode === 'journal';
  return (
    <button
      onClick={onClick}
      style={{
        textAlign: 'left',
        padding: 20, borderRadius: 18,
        background: isJournal
          ? 'linear-gradient(160deg, var(--diary-light), #fff)'
          : 'linear-gradient(160deg, var(--english-light), #fff)',
        border: `1px solid ${isJournal ? 'var(--diary-soft)' : 'var(--english-soft)'}`,
        boxShadow: 'var(--shadow-soft)',
        position: 'relative', overflow: 'hidden',
        transition: 'transform 0.18s ease, box-shadow 0.18s ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; }}
    >
      {decorated && <WashiTape
        color={isJournal ? 'var(--diary-soft)' : 'var(--english-soft)'}
        rotate={isJournal ? -8 : 6}
        top={-8} left={isJournal ? 20 : 'auto'} width={70}
      />}
      <div style={{
        width: 38, height: 38, borderRadius: 12,
        background: isJournal ? 'var(--diary-primary)' : 'var(--english-primary)',
        color: '#fff', display: 'grid', placeItems: 'center',
        marginBottom: 12,
      }}>
        <Icon name={icon} size={17}/>
      </div>
      <div style={{
        fontFamily: 'var(--font-family-display)',
        fontSize: 20, fontWeight: 600, letterSpacing: '-0.01em',
        color: isJournal ? 'var(--diary-ink)' : 'var(--english-ink)',
      }}>{title}</div>
      <div style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.45 }}>
        {copy}
      </div>
      <div style={{
        marginTop: 10, fontSize: 11, fontWeight: 600,
        color: isJournal ? 'var(--diary-primary)' : 'var(--english-primary)',
        display: 'inline-flex', alignItems: 'center', gap: 4,
      }}>
        Begin <Icon name="chevron-right" size={11}/>
      </div>
    </button>
  );
}

function WeekMoodCell({ d, decorated }) {
  const m = MOODS.find(x => x.id === d.mood);
  const bg = m ? m.dot : 'var(--bg-surface)';
  return (
    <button style={{
      padding: '10px 6px', borderRadius: 12,
      background: d.mood ? 'var(--bg-card)' : 'var(--bg-surface)',
      border: '1px solid var(--border-subtle)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
    }}>
      <div style={{ fontSize: 10, color: 'var(--text-hint)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>{d.day}</div>
      <div style={{
        width: decorated ? 26 : 14, height: decorated ? 26 : 14,
        borderRadius: 999, background: bg,
        opacity: d.mood ? 1 : 0.4,
        border: d.mood ? '2px solid #fff' : '1.5px dashed var(--border-subtle)',
        boxShadow: d.mood ? '0 2px 4px rgba(120,90,60,0.08)' : 'none',
      }}/>
    </button>
  );
}

function PolaroidEntry({ entry, tilt = 0, onClick }) {
  const m = MOODS.find(x => x.id === entry.mood);
  return (
    <button
      onClick={onClick}
      style={{
        textAlign: 'left',
        background: '#fff',
        border: '1px solid var(--border-subtle)',
        borderRadius: 12, padding: 12,
        boxShadow: '0 8px 18px rgba(120,90,60,0.10), 0 1px 2px rgba(120,90,60,0.06)',
        transform: `rotate(${tilt}deg)`,
        transition: 'transform 0.2s ease',
        position: 'relative',
        display: 'flex', flexDirection: 'column',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.transform = `rotate(0deg) translateY(-2px)`; }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = `rotate(${tilt}deg)`; }}
    >
      {/* "Photo" area — fixed 4:3 aspect ratio so card never stretches vertically */}
      <div style={{
        aspectRatio: '4 / 3',
        borderRadius: 8,
        background: m ? `linear-gradient(135deg, ${m.dot}, var(--diary-light))` : 'var(--diary-light)',
        display: 'flex', alignItems: 'flex-end', padding: 8,
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Photo mosaic — up to 3 tiles. Tones are placeholders standing in for real images */}
        {entry.photos && entry.photos.length > 0 && (
          <div style={{
            position: 'absolute', inset: 0,
            display: 'grid',
            gridTemplateColumns: entry.photos.length === 1 ? '1fr'
              : entry.photos.length === 2 ? '1fr 1fr'
              : '2fr 1fr',
            gridTemplateRows: entry.photos.length <= 2 ? '1fr' : '1fr 1fr',
            gap: 2,
          }}>
            {entry.photos.slice(0, 3).map((p, i) => (
              <div key={i} style={{
                background: p.url
                  ? `center / cover no-repeat url("${p.url}")`
                  : `linear-gradient(135deg, ${p.tone || 'var(--diary-soft)'}, #fff)`,
                gridRow: entry.photos.length === 3 && i === 0 ? 'span 2' : undefined,
              }}/>
            ))}
          </div>
        )}
        {/* Pill overlay */}
        <div style={{ position: 'relative', zIndex: 1 }}>
          <DiaryPill tone="var(--diary-ink)" soft="rgba(255,255,255,0.85)">
            {entry.type === 'journal' ? 'Journal' : 'Free Write'}
          </DiaryPill>
        </div>
        {/* Multi-photo count badge */}
        {entry.photos && entry.photos.length > 1 && (
          <div style={{
            position: 'absolute', top: 8, right: 8, zIndex: 1,
            padding: '3px 8px', borderRadius: 999,
            background: 'rgba(0,0,0,0.45)', color: '#fff',
            fontSize: 10.5, fontWeight: 700, letterSpacing: '0.04em',
            display: 'inline-flex', alignItems: 'center', gap: 4,
          }}>
            <Icon name="grid" size={10}/> {entry.photos.length}
          </div>
        )}
      </div>
      <div style={{ padding: '10px 4px 4px' }}>
        <div style={{
          fontFamily: 'var(--font-family-handwritten, "Caveat"), cursive',
          fontSize: 22, fontWeight: 600, color: 'var(--diary-ink)', lineHeight: 1.1,
        }}>{entry.title}</div>
        <div style={{ fontSize: 11.5, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.4,
          display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {entry.text}
        </div>
        {/* Date only — mood already expressed by photo swatch color above */}
        <div style={{ marginTop: 8, fontSize: 10, color: 'var(--text-hint)', fontWeight: 700, letterSpacing: '0.08em' }}>
          {entry.dateLong}
        </div>
      </div>
    </button>
  );
}

function MinimalEntry({ entry, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        textAlign: 'left',
        display: 'grid', gridTemplateColumns: '56px 1fr auto', gap: 16, alignItems: 'center',
        padding: '14px 16px', borderRadius: 14,
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--diary-ink)' }}>{entry.title}</div>
        <div style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 3, lineHeight: 1.45,
          display: '-webkit-box', WebkitLineClamp: 1, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {entry.text}
        </div>
      </div>
      <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.08em', color: entry.type === 'journal' ? 'var(--diary-primary)' : 'var(--english-primary)' }}>
        {entry.type === 'journal' ? 'JOURNAL' : 'FREE'}
      </div>
    </button>
  );
}

function StatsMini({ stats }) {
  const rows = [
    { label: 'Entries', value: stats.entries, sub: 'this month', color: 'var(--diary-primary)' },
    { label: 'Streak',  value: `${stats.streak} days`, sub: 'best: 11', color: 'var(--arcade-primary)' },
    { label: 'Words',   value: stats.words, sub: 'kept writing', color: 'var(--english-primary)' },
  ];
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
      borderRadius: 18, padding: 18,
    }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-hint)', marginBottom: 12 }}>
        This month
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {rows.map(r => (
          <div key={r.label} style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{r.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-hint)' }}>{r.sub}</div>
            </div>
            <div style={{ fontFamily: 'var(--font-family-display)', fontSize: 22, fontWeight: 700, color: r.color, letterSpacing: '-0.01em' }}>
              {r.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PromptCardV2({ onStart, decorated }) {
  return (
    <div style={{
      position: 'relative',
      background: decorated
        ? 'linear-gradient(180deg, var(--diary-light), #fff)'
        : 'var(--bg-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 18, padding: 20,
      display: 'flex', flexDirection: 'column',
    }}>
      {decorated && <WashiTape color="var(--arcade-soft)" rotate={-4} top={-8} left={32} width={74}/>}
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--diary-ink)' }}>
        Today's prompt
      </div>
      <div style={{
        fontFamily: decorated ? 'var(--font-family-handwritten, "Caveat"), cursive' : 'var(--font-family-display)',
        fontSize: decorated ? 26 : 20,
        fontWeight: 600, color: 'var(--diary-ink)',
        marginTop: decorated ? 4 : 8, lineHeight: 1.2, letterSpacing: '-0.01em',
      }}>
        What made you smile today?
      </div>
      <div style={{ marginTop: 8, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, flex: 1 }}>
        Try using <i>three new words</i> from Lesson 07.
      </div>
      <button
        onClick={() => {
          localStorage.setItem('nss.diary.seed.mode', 'journal');
          localStorage.setItem('nss.diary.seed.prompt', 'What made you smile today?');
          onStart && onStart();
        }}
        style={{
          marginTop: 14, width: '100%', padding: '10px 14px', borderRadius: 12,
          background: 'var(--diary-primary)', color: '#fff',
          fontSize: 13, fontWeight: 600,
        }}
      >
        Start in Journal
      </button>
    </div>
  );
}

function StreakCard({ streak, decorated }) {
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
      borderRadius: 18, padding: 16,
      display: 'flex', alignItems: 'center', gap: 14,
    }}>
      <div style={{
        width: 44, height: 44, borderRadius: 12,
        background: 'var(--arcade-light)',
        color: 'var(--arcade-primary)',
        display: 'grid', placeItems: 'center',
      }}>
        <Icon name="flame" size={22}/>
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 12, color: 'var(--text-hint)', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Streak</div>
        <div style={{ fontFamily: 'var(--font-family-display)', fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>
          {streak} days
        </div>
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-hint)', textAlign: 'right' }}>
        best<br/><b style={{ color: 'var(--text-primary)', fontSize: 13 }}>11</b>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   Screen 2 — Diary Write
   ═══════════════════════════════════════════════ */
function DiaryWrite({ onNavigate }) {
  const [style] = useDiaryStyle();
  const decorated = style === 'decorated';

  // Read seed (mode + prompt) from localStorage, set e.g. by Home's "Start in Journal" button
  const seedMode   = typeof localStorage !== 'undefined' ? localStorage.getItem('nss.diary.seed.mode') : null;
  const seedPrompt = typeof localStorage !== 'undefined' ? localStorage.getItem('nss.diary.seed.prompt') : null;

  const [mode, setMode] = useStateD(seedMode === 'free' ? 'free' : 'journal'); // default journal
  const [mood, setMood] = useStateD('happy');
  const [title, setTitle] = useStateD('');
  const [body, setBody] = useStateD('');
  const [customPrompt, setCustomPrompt] = useStateD(seedPrompt || null);
  const [photos, setPhotos] = useStateD([]); // [{ id, url, name }] — both modes
  const [moodOpen, setMoodOpen] = useStateD(false);

  // Style controls
  const [font, setFont] = useStateD('caveat');  // 'nunito' | 'caveat' | 'patrick' | 'shadows' | 'indie' | 'kalam'
  const [textSize, setTextSize] = useStateD('m'); // 's' | 'm' | 'l'
  const [textColor, setTextColor] = useStateD('default'); // token key
  const [bgMood, setBgMood] = useStateD('default'); // token key
  const textareaRef = React.useRef(null);

  const insertAtCaret = (text) => {
    const el = textareaRef.current;
    if (!el) { setBody(body + text); return; }
    const start = el.selectionStart ?? body.length;
    const end = el.selectionEnd ?? body.length;
    const next = body.slice(0, start) + text + body.slice(end);
    setBody(next);
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(start + text.length, start + text.length);
    });
  };

  // Clear seed once consumed
  useEffectD(() => {
    if (seedMode)   localStorage.removeItem('nss.diary.seed.mode');
    if (seedPrompt) localStorage.removeItem('nss.diary.seed.prompt');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const defaultPrompt = mode === 'journal'
    ? 'What made you smile today, even a little?'
    : 'Write anything you want — a story, a wish, a memory.';
  const prompt = (mode === 'journal' && customPrompt) ? customPrompt : defaultPrompt;

  const wordCount = body.trim() ? body.trim().split(/\s+/).length : 0;
  const minWords = 15;
  const progress = Math.min(wordCount / minWords, 1);

  return (
    <div style={{ height: '100%', overflow: 'hidden', background: 'var(--bg-page)', display: 'flex', flexDirection: 'column' }}>
      <DiaryChrome
        eyebrow={mode === 'journal' ? 'Diary · Journal' : 'Diary · Free Write'}
        title={mode === 'journal' ? "Today's journal" : "Free write"}
        subtitle={mode === 'journal' ? 'Pick mood, add photos, answer the prompt.' : 'Write freely. AI gives gentle feedback.'}
        onBack={() => onNavigate('diary-home')}
        rightSlot={
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            {/* Mode segmented control — iOS style */}
            <div style={{
              display: 'inline-flex', gap: 2,
              background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
              borderRadius: 12, padding: 3,
            }}>
              {[
                { id: 'journal', label: 'Journal', icon: 'book-open' },
                { id: 'free',    label: 'Free Write', icon: 'sparkles' },
              ].map(t => {
                const active = mode === t.id;
                return (
                  <button
                    key={t.id}
                    onClick={() => setMode(t.id)}
                    style={{
                      padding: '8px 14px', borderRadius: 9,
                      fontSize: 12.5, fontWeight: active ? 600 : 500,
                      color: active ? 'var(--diary-ink)' : 'var(--text-secondary)',
                      background: active ? 'var(--bg-card)' : 'transparent',
                      boxShadow: active ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                      display: 'inline-flex', alignItems: 'center', gap: 6,
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <Icon name={t.icon} size={13}/> {t.label}
                  </button>
                );
              })}
            </div>

            {/* Overflow menu for Save draft + other utilities */}
            <WriteOverflowMenu/>

            <button
              disabled={wordCount < minWords}
              style={{
                padding: '10px 18px', borderRadius: 12,
                background: wordCount >= minWords ? 'var(--diary-primary)' : 'var(--border-subtle)',
                color: wordCount >= minWords ? '#fff' : 'var(--text-hint)',
                fontSize: 13, fontWeight: 600,
                display: 'inline-flex', alignItems: 'center', gap: 6,
                boxShadow: wordCount >= minWords ? '0 4px 12px rgba(224,154,174,0.32)' : 'none',
              }}
            >
              <Icon name="check" size={14}/> Save · +15 XP
            </button>
          </div>
        }
      />

      {/* Journal: 2-column (Paper / Prompts).  Free Write: full-width Paper (no aside). */}
      <div style={{
        flex: 1, minHeight: 0,
        padding: '20px 32px 24px',
        display: 'grid',
        gridTemplateColumns: '1fr 360px',
        gap: 20,
      }}>
        {/* CENTER — Paper (photos integrated inside, at top) */}
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          {/* Paper — single unified note card containing photos + title + prompt + body */}
          <div style={{
            position: 'relative', flex: 1, minHeight: 0,
            background: resolvePaperBackground(decorated, bgMood),
            border: '1px solid var(--border-subtle)',
            borderRadius: 16, padding: '18px 24px',
            boxShadow: 'var(--shadow-soft)',
            display: 'flex', flexDirection: 'column',
          }}>
            {decorated && <WashiTape color="var(--diary-soft)" rotate={-3} top={-9} left={30} width={90}/>}
            {decorated && <WashiTape color="var(--math-soft)" rotate={4} top={-9} left={'auto'} width={60}/>}

            {/* Photos — inline at top of note (both modes) */}
            <PhotoInlineStrip
              photos={photos}
              setPhotos={setPhotos}
              decorated={decorated}
            />

            {/* Title input — user-provided; AI suggest appears once body grows */}
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexShrink: 0 }}>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Give this page a title…"
                style={{
                  flex: 1, minWidth: 0,
                  background: 'transparent', border: 'none', outline: 'none',
                  fontFamily: decorated ? 'var(--font-family-handwritten, "Caveat"), cursive' : 'var(--font-family-display)',
                  fontSize: decorated ? 32 : 22,
                  fontWeight: 600,
                  color: 'var(--diary-ink)',
                  letterSpacing: '-0.01em',
                }}
              />
              {wordCount >= 20 && !title && (
                <button
                  title="Ask AI to suggest a title"
                  style={{
                    padding: '4px 10px', borderRadius: 999,
                    background: 'var(--english-light)', color: 'var(--english-ink)',
                    border: '1px solid var(--english-soft)',
                    fontSize: 10.5, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase',
                    display: 'inline-flex', alignItems: 'center', gap: 4,
                    flexShrink: 0,
                  }}
                >
                  <Icon name="sparkles" size={11}/> Suggest
                </button>
              )}
            </div>

            {/* Prompt — secondary line under title */}
            <div style={{
              marginTop: 6, fontSize: 12.5, color: 'var(--text-secondary)',
              fontStyle: 'italic', flexShrink: 0, lineHeight: 1.4,
            }}>
              {prompt}
            </div>

            {/* Textarea — responds to Style tools (font / size / color) */}
            <textarea
              ref={textareaRef}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder={mode === 'journal' ? 'Start with: "Today, I…"' : 'Once upon a time…'}
              style={{
                marginTop: 12, width: '100%', flex: 1,
                background: 'transparent', border: 'none', outline: 'none',
                resize: 'none',
                fontFamily: resolveFontFamily(font),
                fontSize: resolveFontSize(font, textSize),
                lineHeight: resolveLineHeight(font, textSize),
                color: resolveTextColor(textColor),
                minHeight: 0,
              }}
            />

            {/* Footer — mood popover (left) + counter + voice buttons (right) */}
            <div style={{
              marginTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              paddingTop: 12, borderTop: '1px dashed var(--border-subtle)',
              flexShrink: 0, gap: 10, position: 'relative',
            }}>
              {/* Mood pill + popover */}
              <MoodFooterPicker
                mood={mood} setMood={setMood}
                open={moodOpen} setOpen={setMoodOpen}
              />

              {/* Counter + voice */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{
                    width: 80, height: 5, borderRadius: 999,
                    background: 'var(--bg-surface)', overflow: 'hidden',
                  }}>
                    <div style={{
                      width: `${progress * 100}%`, height: '100%',
                      background: 'var(--diary-primary)', transition: 'width 0.3s ease',
                    }}/>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-hint)' }}>
                    <b style={{ color: progress >= 1 ? 'var(--math-primary)' : 'var(--text-primary)' }}>{wordCount}</b> / {minWords}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                  <button title="Voice to text" style={{
                    padding: '6px 10px', borderRadius: 8,
                    color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: 5,
                    fontSize: 11, fontWeight: 600,
                  }}>
                    <Icon name="mic" size={13}/> Speak
                  </button>
                  <button title="Read aloud" style={{
                    padding: '6px 10px', borderRadius: 8,
                    color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: 5,
                    fontSize: 11, fontWeight: 600,
                  }}>
                    <Icon name="volume" size={13}/> Listen
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT aside — both modes get Tips/Prompts + Style + Decor tools */}
        <aside style={{ display: 'flex', flexDirection: 'column', gap: 12, minHeight: 0, overflowY: 'auto' }}>
          {mode === 'journal' ? (
            <PromptBank onPick={(q) => setCustomPrompt(q)} current={prompt}/>
          ) : (
            <WritingTips/>
          )}
          <StyleTools
            font={font} setFont={setFont}
            textSize={textSize} setTextSize={setTextSize}
            textColor={textColor} setTextColor={setTextColor}
          />
          <DecorTools
            bgMood={bgMood} setBgMood={setBgMood}
            onInsertSticker={insertAtCaret}
          />
        </aside>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   Style resolvers — map state keys to CSS values
   ═══════════════════════════════════════════════ */

const FONT_OPTIONS = [
  { id: 'caveat',   label: 'Caveat',   css: '"Caveat", cursive',              sample: 'Aa' },
  { id: 'nunito',   label: 'Nunito',   css: '"Nunito", sans-serif',           sample: 'Aa' },
  { id: 'patrick',  label: 'Patrick',  css: '"Patrick Hand", cursive',        sample: 'Aa' },
  { id: 'shadows',  label: 'Shadows',  css: '"Shadows Into Light", cursive',  sample: 'Aa' },
  { id: 'indie',    label: 'Indie',    css: '"Indie Flower", cursive',        sample: 'Aa' },
  { id: 'kalam',    label: 'Kalam',    css: '"Kalam", cursive',               sample: 'Aa' },
];

function resolveFontFamily(font) {
  return FONT_OPTIONS.find(f => f.id === font)?.css || FONT_OPTIONS[0].css;
}

function resolveFontSize(font, size) {
  const scriptyFonts = ['caveat', 'shadows', 'indie'];
  const biggerBase = scriptyFonts.includes(font);
  const base = biggerBase ? 22 : 16;
  const bump = size === 's' ? -3 : size === 'l' ? 4 : 0;
  return base + bump;
}

function resolveLineHeight(font, size) {
  const fs = resolveFontSize(font, size);
  return Math.round(fs * 1.55) + 'px';
}

const TEXT_COLORS = [
  { id: 'default', label: 'Ink',     value: 'var(--text-primary)' },
  { id: 'diary',   label: 'Pink',    value: 'var(--diary-ink)' },
  { id: 'english', label: 'Blue',    value: 'var(--english-ink)' },
  { id: 'math',    label: 'Green',   value: 'var(--math-ink)' },
  { id: 'arcade',  label: 'Amber',   value: 'var(--arcade-ink)' },
  { id: 'rewards', label: 'Purple',  value: 'var(--rewards-ink)' },
  { id: 'review',  label: 'Peach',   value: 'var(--review-ink)' },
];

function resolveTextColor(key) {
  return TEXT_COLORS.find(c => c.id === key)?.value || 'var(--text-primary)';
}

const BG_MOODS = [
  { id: 'default',  label: 'Paper',    fill: '#FFFFFF',                lined: 'var(--diary-light)' },
  { id: 'pink',     label: 'Blossom',  fill: 'var(--diary-light)',     lined: 'var(--diary-soft)' },
  { id: 'mint',     label: 'Mint',     fill: 'var(--math-light)',      lined: 'var(--math-soft)' },
  { id: 'sky',      label: 'Sky',      fill: 'var(--english-light)',   lined: 'var(--english-soft)' },
  { id: 'butter',   label: 'Butter',   fill: 'var(--arcade-light)',    lined: 'var(--arcade-soft)' },
  { id: 'lavender', label: 'Lavender', fill: 'var(--rewards-light)',   lined: 'var(--rewards-soft)' },
  { id: 'peach',    label: 'Peach',    fill: 'var(--review-light)',    lined: 'var(--review-soft)' },
];

function resolvePaperBackground(decorated, bgKey) {
  const bg = BG_MOODS.find(b => b.id === bgKey) || BG_MOODS[0];
  if (decorated) {
    return `repeating-linear-gradient(180deg, ${bg.fill} 0 31px, ${bg.lined} 31px 32px)`;
  }
  return bg.fill;
}

/* ═══════════════════════════════════════════════
   Writing Tips card (Free Write only)
   ═══════════════════════════════════════════════ */
function WritingTips() {
  const tips = [
    { k: 'Start anywhere',     t: "You don't need to know the ending. Start with what you see or feel right now." },
    { k: "Show, don't tell",   t: "Instead of 'I was sad,' try 'My feet dragged like wet shoes.'" },
    { k: 'One small thing',    t: "Pick ONE moment from today. Don't try to cover the whole day." },
    { k: 'Use your senses',    t: "What did you hear, smell, or touch? Your story comes alive." },
  ];
  const [idx, setIdx] = useStateD(0);
  const tip = tips[idx];
  return (
    <div style={{
      background: 'linear-gradient(160deg, var(--english-light), #fff)',
      border: '1px solid var(--english-soft)',
      borderRadius: 14, padding: '12px 14px',
      display: 'flex', flexDirection: 'column', gap: 8,
      flexShrink: 0,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{
            width: 22, height: 22, borderRadius: 7,
            background: 'var(--english-primary)', color: '#fff',
            display: 'grid', placeItems: 'center',
          }}>
            <Icon name="sparkles" size={12}/>
          </div>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--english-ink)' }}>
            Writing tip
          </div>
        </div>
        <button
          onClick={() => setIdx((idx + 1) % tips.length)}
          aria-label="Next tip"
          style={{
            padding: '4px 8px', borderRadius: 8,
            background: 'var(--bg-card)', border: '1px solid var(--english-soft)',
            color: 'var(--english-ink)', fontSize: 10.5, fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Next →
        </button>
      </div>
      <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--english-ink)', lineHeight: 1.25 }}>
        {tip.k}
      </div>
      <div style={{ fontSize: 11.5, color: 'var(--text-primary)', lineHeight: 1.45 }}>
        {tip.t}
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        {tips.map((_, i) => (
          <div key={i} style={{
            width: i === idx ? 18 : 6, height: 4, borderRadius: 999,
            background: i === idx ? 'var(--english-primary)' : 'var(--english-soft)',
            transition: 'width 0.2s ease',
          }}/>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   StyleTools — Font · Size · Color
   ═══════════════════════════════════════════════ */
function StyleTools({ font, setFont, textSize, setTextSize, textColor, setTextColor }) {
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
      borderRadius: 14, padding: '12px 14px',
      display: 'flex', flexDirection: 'column', gap: 12,
      flexShrink: 0,
    }}>
      <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-hint)' }}>
        Style
      </div>

      {/* Font picker — 6 samples */}
      <div>
        <div style={{ fontSize: 10.5, color: 'var(--text-hint)', fontWeight: 600, marginBottom: 6 }}>Font</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
          {FONT_OPTIONS.map(f => {
            const active = f.id === font;
            return (
              <button
                key={f.id}
                onClick={() => setFont(f.id)}
                style={{
                  padding: '8px 6px', borderRadius: 10,
                  background: active ? 'var(--diary-light)' : 'var(--bg-page)',
                  border: active ? '1.5px solid var(--diary-primary)' : '1px solid var(--border-subtle)',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontFamily: f.css, fontSize: 20, color: 'var(--diary-ink)', lineHeight: 1 }}>
                  {f.sample}
                </div>
                <div style={{ fontSize: 9.5, color: active ? 'var(--diary-ink)' : 'var(--text-secondary)', fontWeight: active ? 600 : 500 }}>
                  {f.label}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Size */}
      <div>
        <div style={{ fontSize: 10.5, color: 'var(--text-hint)', fontWeight: 600, marginBottom: 6 }}>Size</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
          {[{ id: 's', label: 'S', size: 12 }, { id: 'm', label: 'M', size: 15 }, { id: 'l', label: 'L', size: 18 }].map(s => {
            const active = s.id === textSize;
            return (
              <button
                key={s.id}
                onClick={() => setTextSize(s.id)}
                style={{
                  padding: '8px 6px', borderRadius: 10,
                  background: active ? 'var(--diary-light)' : 'var(--bg-page)',
                  border: active ? '1.5px solid var(--diary-primary)' : '1px solid var(--border-subtle)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                  cursor: 'pointer',
                }}
              >
                <span style={{
                  fontFamily: 'var(--font-family-display)',
                  fontSize: s.size, fontWeight: 700, color: 'var(--diary-ink)',
                }}>Aa</span>
                <span style={{ fontSize: 10.5, color: active ? 'var(--diary-ink)' : 'var(--text-secondary)', fontWeight: active ? 600 : 500 }}>
                  {s.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Text color */}
      <div>
        <div style={{ fontSize: 10.5, color: 'var(--text-hint)', fontWeight: 600, marginBottom: 6 }}>Text color</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {TEXT_COLORS.map(c => {
            const active = c.id === textColor;
            return (
              <button
                key={c.id}
                onClick={() => setTextColor(c.id)}
                aria-label={c.label}
                title={c.label}
                style={{
                  width: 28, height: 28, borderRadius: 999,
                  background: c.value === 'var(--text-primary)' ? 'var(--text-primary)' : c.value,
                  border: active ? '2.5px solid #fff' : '1.5px solid var(--border-subtle)',
                  boxShadow: active ? `0 0 0 2px var(--diary-primary)` : 'none',
                  cursor: 'pointer',
                  padding: 0,
                }}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   DecorTools — Stickers · BG mood
   ═══════════════════════════════════════════════ */
const STICKER_CATEGORIES = [
  { id: 'nature',   label: 'Nature',   items: ['🌸','🌿','🌈','🌻','🍃','🌺','🌷','🌼'] },
  { id: 'sky',      label: 'Sky',      items: ['⭐','🌙','☀️','☁️','✨','🌤','🌟','☔'] },
  { id: 'hearts',   label: 'Hearts',   items: ['💕','❤️','💗','💖','💛','💚','💙','💜'] },
  { id: 'faces',    label: 'Faces',    items: ['😊','🥰','😌','🤗','🥺','😴','🤔','😍'] },
  { id: 'things',   label: 'Things',   items: ['📚','✏️','☕','🎀','🧸','🎈','🎁','📷'] },
  { id: 'food',     label: 'Food',     items: ['🍎','🍓','🍰','🍪','🍭','🍩','🥞','🍦'] },
  { id: 'animals',  label: 'Animals',  items: ['🐰','🐱','🐶','🐻','🐼','🦊','🐨','🐸'] },
];

function DecorTools({ bgMood, setBgMood, onInsertSticker }) {
  const [catIdx, setCatIdx] = useStateD(0);
  const cat = STICKER_CATEGORIES[catIdx];

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
      borderRadius: 14, padding: '12px 14px',
      display: 'flex', flexDirection: 'column', gap: 12,
      flexShrink: 0,
    }}>
      <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-hint)' }}>
        Decor
      </div>

      {/* Sticker tray */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
          <div style={{ fontSize: 10.5, color: 'var(--text-hint)', fontWeight: 600 }}>Stickers</div>
          <div style={{ fontSize: 10, color: 'var(--text-hint)' }}>Tap to add</div>
        </div>
        {/* Category tabs */}
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
          {STICKER_CATEGORIES.map((c, i) => {
            const active = i === catIdx;
            return (
              <button
                key={c.id}
                onClick={() => setCatIdx(i)}
                style={{
                  padding: '3px 9px', borderRadius: 999,
                  background: active ? 'var(--diary-primary)' : 'var(--bg-page)',
                  color: active ? '#fff' : 'var(--text-secondary)',
                  border: active ? '1px solid var(--diary-primary)' : '1px solid var(--border-subtle)',
                  fontSize: 10.5, fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {c.label}
              </button>
            );
          })}
        </div>
        {/* Sticker grid */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(8, 1fr)', gap: 4,
          background: 'var(--bg-page)', border: '1px solid var(--border-subtle)',
          borderRadius: 10, padding: 8,
        }}>
          {cat.items.map(s => (
            <button
              key={s}
              onClick={() => onInsertSticker(s + ' ')}
              style={{
                aspectRatio: '1 / 1',
                borderRadius: 8,
                background: 'transparent',
                border: '1px solid transparent',
                fontSize: 18,
                cursor: 'pointer',
                transition: 'transform 0.12s ease, background 0.12s ease',
                padding: 0,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'var(--bg-card)';
                e.currentTarget.style.transform = 'scale(1.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.transform = 'scale(1)';
              }}
            >{s}</button>
          ))}
        </div>
      </div>

      {/* BG mood */}
      <div>
        <div style={{ fontSize: 10.5, color: 'var(--text-hint)', fontWeight: 600, marginBottom: 6 }}>Page color</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {BG_MOODS.map(b => {
            const active = b.id === bgMood;
            return (
              <button
                key={b.id}
                onClick={() => setBgMood(b.id)}
                title={b.label}
                aria-label={`Page color ${b.label}`}
                style={{
                  width: 32, height: 32, borderRadius: 10,
                  background: b.fill,
                  border: active ? '2px solid var(--diary-primary)' : '1px solid var(--border-subtle)',
                  boxShadow: active ? '0 2px 6px rgba(120,90,60,0.15)' : 'none',
                  cursor: 'pointer',
                  padding: 0,
                  display: 'grid', placeItems: 'center',
                }}
              >
                {b.id === 'default' && (
                  <Icon name="x" size={10} color="var(--text-hint)"/>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* MoodFooterPicker — compact current-mood pill in Paper footer.
 * Click to open popover with 6 moods above the pill.
 */
function MoodFooterPicker({ mood, setMood, open, setOpen }) {
  const current = MOODS.find(m => m.id === mood);

  useEffectD(() => {
    if (!open) return;
    const close = (e) => { if (!e.target.closest?.('[data-mood-picker]')) setOpen(false); };
    const esc = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('click', close);
    document.addEventListener('keydown', esc);
    return () => {
      document.removeEventListener('click', close);
      document.removeEventListener('keydown', esc);
    };
  }, [open, setOpen]);

  return (
    <div data-mood-picker style={{ position: 'relative' }}>
      <button
        onClick={(e) => { e.stopPropagation(); setOpen(v => !v); }}
        style={{
          padding: '6px 12px 6px 8px', borderRadius: 999,
          background: `color-mix(in srgb, ${current.dot} 14%, #fff)`,
          border: `1.5px solid ${current.dot}`,
          display: 'inline-flex', alignItems: 'center', gap: 8,
          cursor: 'pointer',
        }}
      >
        <div style={{
          width: 16, height: 16, borderRadius: 999,
          background: current.dot, border: '2px solid #fff',
          boxShadow: `0 0 0 2px ${current.dot}55`,
        }}/>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
          {current.label}
        </span>
        <Icon name="chevron-down" size={11} color="var(--text-secondary)"/>
      </button>

      {open && (
        <div style={{
          position: 'absolute', bottom: 'calc(100% + 8px)', left: 0, zIndex: 50,
          background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
          borderRadius: 14, boxShadow: 'var(--shadow-modal)',
          padding: 8,
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 4,
          width: 260,
        }}>
          {MOODS.map(m => {
            const active = m.id === mood;
            return (
              <button
                key={m.id}
                onClick={() => { setMood(m.id); setOpen(false); }}
                style={{
                  padding: '8px 6px', borderRadius: 10,
                  background: active ? `color-mix(in srgb, ${m.dot} 14%, #fff)` : 'transparent',
                  border: active ? `1.5px solid ${m.dot}` : '1px solid transparent',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--bg-surface)'; }}
                onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent'; }}
              >
                <div style={{
                  width: 14, height: 14, borderRadius: 999,
                  background: m.dot, border: '2px solid #fff',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.08)',
                }}/>
                <span style={{ fontSize: 11.5, color: 'var(--text-primary)', textTransform: 'capitalize', fontWeight: active ? 600 : 500 }}>
                  {m.label}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* PhotoInlineStrip — photos that live INSIDE the note paper (no outer card).
 * Transparent background so the note-lined pattern shows through.
 * Paper-tape look: small photo tiles taped onto the top of the page.
 */
function PhotoInlineStrip({ photos, setPhotos, decorated }) {
  const MAX = 3;
  const fileRef = React.useRef(null);

  const onPick = (e) => {
    const files = Array.from(e.target.files || []);
    const room = MAX - photos.length;
    const next = files.slice(0, room).map((f) => ({
      id: `p-${Date.now()}-${Math.random().toString(36).slice(2,7)}`,
      url: URL.createObjectURL(f),
      name: f.name,
    }));
    setPhotos([...photos, ...next]);
    e.target.value = '';
  };

  const remove = (id) => {
    setPhotos(photos.filter((p) => p.id !== id));
  };

  const atLimit = photos.length >= MAX;

  // Empty state — single compact "Add photos" chip aligned right
  if (photos.length === 0) {
    return (
      <div style={{
        display: 'flex', justifyContent: 'flex-end',
        marginBottom: 10, flexShrink: 0,
      }}>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          multiple
          onChange={onPick}
          style={{ display: 'none' }}
        />
        <button
          onClick={() => fileRef.current?.click()}
          style={{
            padding: '6px 12px', borderRadius: 999,
            background: 'var(--bg-page)',
            color: 'var(--text-secondary)',
            border: '1.5px dashed var(--border-default)',
            fontSize: 11.5, fontWeight: 600,
            display: 'inline-flex', alignItems: 'center', gap: 6,
            cursor: 'pointer',
          }}
        >
          <Icon name="grid" size={13}/> Add photos
        </button>
      </div>
    );
  }

  // With photos — tiles laid horizontally at the top of the page
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      marginBottom: 14, flexShrink: 0,
    }}>
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        multiple
        onChange={onPick}
        style={{ display: 'none' }}
      />

      {photos.map((p, i) => (
        <div key={p.id} style={{
          position: 'relative',
          width: 96, height: 96,
          borderRadius: 10, overflow: 'hidden',
          background: `center / cover no-repeat url("${p.url}"), var(--bg-surface)`,
          transform: decorated ? `rotate(${i === 0 ? -2 : i === 1 ? 1.5 : -1}deg)` : 'none',
          boxShadow: decorated
            ? '0 6px 14px rgba(120,90,60,0.18), 0 0 0 5px #fff, 0 0 0 6px rgba(0,0,0,0.05)'
            : '0 0 0 1px var(--border-subtle), var(--shadow-soft)',
          flexShrink: 0,
        }}>
          <button
            onClick={() => remove(p.id)}
            aria-label="Remove photo"
            style={{
              position: 'absolute', top: 5, right: 5,
              width: 20, height: 20, borderRadius: 999,
              background: 'rgba(0,0,0,0.55)', color: '#fff',
              display: 'grid', placeItems: 'center',
              border: 'none', cursor: 'pointer',
            }}
          >
            <Icon name="x" size={10}/>
          </button>
        </div>
      ))}

      {!atLimit && (
        <button
          onClick={() => fileRef.current?.click()}
          style={{
            width: 96, height: 96,
            borderRadius: 10,
            border: '1.5px dashed var(--border-default)',
            background: 'transparent',
            color: 'var(--text-secondary)',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 4,
            fontSize: 11, fontWeight: 600,
            cursor: 'pointer',
            flexShrink: 0,
          }}
        >
          <Icon name="grid" size={18}/>
          Add
        </button>
      )}

      <div style={{ flex: 1 }}/>
      <div style={{
        fontSize: 10.5, fontWeight: 700, letterSpacing: '0.08em',
        textTransform: 'uppercase', color: 'var(--text-hint)',
        flexShrink: 0,
      }}>
        {photos.length} / {MAX}
      </div>
    </div>
  );
}

/* PhotoUploaderStrip — horizontal, compact version for top of Write.
 * 3 slots in a row, square tiles, dashed add tile inline.
 * Kept for reference; PhotoInlineStrip is now used inside Paper.
 */
function PhotoUploaderStrip({ photos, setPhotos, decorated }) {
  const MAX = 3;
  const fileRef = React.useRef(null);

  const onPick = (e) => {
    const files = Array.from(e.target.files || []);
    const room = MAX - photos.length;
    const next = files.slice(0, room).map((f) => ({
      id: `p-${Date.now()}-${Math.random().toString(36).slice(2,7)}`,
      url: URL.createObjectURL(f),
      name: f.name,
    }));
    setPhotos([...photos, ...next]);
    e.target.value = '';
  };

  const remove = (id) => {
    setPhotos(photos.filter((p) => p.id !== id));
  };

  const atLimit = photos.length >= MAX;

  return (
    <div style={{
      position: 'relative',
      background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
      borderRadius: 14, padding: '10px 14px', boxShadow: 'var(--shadow-soft)',
      display: 'flex', alignItems: 'center', gap: 14,
    }}>
      {decorated && <WashiTape color="var(--english-soft)" rotate={-4} top={-9} left={24} width={78}/>}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, flexShrink: 0 }}>
        <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-hint)' }}>
          Photos
        </div>
        <div style={{ fontSize: 10.5, color: 'var(--text-hint)' }}>{photos.length} / {MAX}</div>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        multiple
        onChange={onPick}
        style={{ display: 'none' }}
      />

      <div style={{ display: 'flex', gap: 12, flex: 1 }}>
        {photos.map((p, i) => (
          <div key={p.id} style={{
            position: 'relative',
            width: 110, height: 110,
            borderRadius: 12, overflow: 'hidden',
            border: '1px solid var(--border-subtle)',
            background: `center / cover no-repeat url("${p.url}"), var(--bg-surface)`,
            transform: decorated ? `rotate(${i % 2 === 0 ? -1.2 : 1.2}deg)` : 'none',
            boxShadow: decorated ? '0 5px 14px rgba(120,90,60,0.14)' : 'var(--shadow-soft)',
            flexShrink: 0,
          }}>
            <button
              onClick={() => remove(p.id)}
              aria-label="Remove photo"
              style={{
                position: 'absolute', top: 6, right: 6,
                width: 22, height: 22, borderRadius: 999,
                background: 'rgba(0,0,0,0.55)', color: '#fff',
                display: 'grid', placeItems: 'center',
                border: 'none', cursor: 'pointer',
              }}
            >
              <Icon name="x" size={11}/>
            </button>
          </div>
        ))}

        {!atLimit && (
          <button
            onClick={() => fileRef.current?.click()}
            style={{
              width: 110, height: 110,
              borderRadius: 12,
              border: '1.5px dashed var(--border-default)',
              background: 'var(--bg-page)',
              color: 'var(--text-secondary)',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 6,
              fontSize: 11.5, fontWeight: 600,
              cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            <Icon name="grid" size={22}/>
            {photos.length === 0 ? 'Add photos' : 'Add'}
          </button>
        )}
      </div>
    </div>
  );
}

/* Overflow menu for Write chrome — holds Save draft + future utilities */
function WriteOverflowMenu() {
  const [open, setOpen] = useStateD(false);
  useEffectD(() => {
    if (!open) return;
    const close = (e) => {
      if (!e.target.closest?.('[data-write-menu]')) setOpen(false);
    };
    const esc = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('click', close);
    document.addEventListener('keydown', esc);
    return () => {
      document.removeEventListener('click', close);
      document.removeEventListener('keydown', esc);
    };
  }, [open]);

  return (
    <div data-write-menu style={{ position: 'relative' }}>
      <button
        onClick={(e) => { e.stopPropagation(); setOpen(v => !v); }}
        aria-label="More actions"
        style={{
          width: 38, height: 38, borderRadius: 10,
          background: open ? 'var(--bg-surface)' : 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          color: 'var(--text-secondary)',
          display: 'grid', placeItems: 'center',
          cursor: 'pointer',
        }}
      >
        <div style={{ display: 'flex', gap: 3 }}>
          <span style={{ width: 3, height: 3, borderRadius: 999, background: 'currentColor' }}/>
          <span style={{ width: 3, height: 3, borderRadius: 999, background: 'currentColor' }}/>
          <span style={{ width: 3, height: 3, borderRadius: 999, background: 'currentColor' }}/>
        </div>
      </button>
      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 6px)', right: 0, zIndex: 50,
          background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
          borderRadius: 12, boxShadow: 'var(--shadow-modal)',
          padding: 6, minWidth: 180,
        }}>
          {[
            { label: 'Save draft',   icon: 'edit'  },
            { label: 'Clear all',    icon: 'x'     },
            { label: 'Export as PDF', icon: 'book-open' },
          ].map(item => (
            <button
              key={item.label}
              onClick={() => setOpen(false)}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                width: '100%', padding: '8px 10px', borderRadius: 8,
                textAlign: 'left', fontSize: 12.5, fontWeight: 500,
                color: 'var(--text-primary)',
                background: 'transparent', border: 'none', cursor: 'pointer',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-surface)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
            >
              <Icon name={item.icon} size={13}/>
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function PromptBank({ onPick, current }) {
  const prompts = [
    'What made you smile today?',
    'A small thing that surprised you.',
    'Something you felt proud of.',
    'A word you learned today.',
    'A question you asked in your head.',
  ];
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
      borderRadius: 14, padding: '12px 14px',
      display: 'flex', flexDirection: 'column', minHeight: 0,
    }}>
      <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-hint)', marginBottom: 8, flexShrink: 0 }}>
        More prompts
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 5, overflowY: 'auto', minHeight: 0 }}>
        {prompts.map((p, i) => {
          const active = current === p;
          return (
            <button
              key={i}
              onClick={() => onPick(p)}
              style={{
                textAlign: 'left',
                padding: '7px 10px', borderRadius: 10,
                background: active ? 'var(--diary-primary)' : 'var(--diary-light)',
                color: active ? '#fff' : 'var(--diary-ink)',
                border: active ? '1px solid var(--diary-primary)' : '1px solid var(--border-subtle)',
                fontSize: 11.5, lineHeight: 1.35,
                fontFamily: 'var(--font-family-display)',
                fontWeight: active ? 600 : 400,
              }}
            >
              {p}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   PhotoUploader — Journal only, max 3
   Prototype: reads File via URL.createObjectURL so the preview works offline.
   Production should POST to /api/v1/diary/:id/photos and store returned URLs.
   ═══════════════════════════════════════════════ */
function PhotoUploader({ photos, setPhotos, decorated }) {
  const MAX = 3;
  const fileRef = React.useRef(null);

  const onPick = (e) => {
    const files = Array.from(e.target.files || []);
    const room = MAX - photos.length;
    const next = files.slice(0, room).map((f) => ({
      id: `p-${Date.now()}-${Math.random().toString(36).slice(2,7)}`,
      url: URL.createObjectURL(f),
      name: f.name,
    }));
    setPhotos([...photos, ...next]);
    e.target.value = '';
  };

  const remove = (id) => {
    setPhotos(photos.filter((p) => p.id !== id));
  };

  const atLimit = photos.length >= MAX;

  return (
    <div style={{
      position: 'relative',
      background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
      borderRadius: 14, padding: '10px 12px', boxShadow: 'var(--shadow-soft)',
      flexShrink: 0,
    }}>
      {decorated && <WashiTape color="var(--english-soft)" rotate={-4} top={-9} left={20} width={70}/>}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
        <div style={{ fontSize: 10.5, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-hint)' }}>
          Photos
        </div>
        <div style={{ fontSize: 10.5, color: 'var(--text-hint)' }}>{photos.length} / {MAX}</div>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        multiple
        onChange={onPick}
        style={{ display: 'none' }}
      />

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 6,
      }}>
        {photos.map((p, i) => (
          <div key={p.id} style={{
            position: 'relative',
            aspectRatio: '1 / 1',
            borderRadius: 8, overflow: 'hidden',
            border: '1px solid var(--border-subtle)',
            background: `center / cover no-repeat url("${p.url}"), var(--bg-surface)`,
            transform: decorated ? `rotate(${i % 2 === 0 ? -1.2 : 1.2}deg)` : 'none',
            boxShadow: decorated ? '0 3px 8px rgba(120,90,60,0.12)' : 'var(--shadow-soft)',
          }}>
            <button
              onClick={() => remove(p.id)}
              aria-label="Remove photo"
              style={{
                position: 'absolute', top: 3, right: 3,
                width: 18, height: 18, borderRadius: 999,
                background: 'rgba(0,0,0,0.55)', color: '#fff',
                display: 'grid', placeItems: 'center',
                border: 'none', cursor: 'pointer',
              }}
            >
              <Icon name="x" size={10}/>
            </button>
          </div>
        ))}

        {/* Add button (dashed tile) */}
        {!atLimit && (
          <button
            onClick={() => fileRef.current?.click()}
            style={{
              aspectRatio: '1 / 1',
              borderRadius: 8,
              border: '1.5px dashed var(--border-default)',
              background: 'var(--bg-page)',
              color: 'var(--text-secondary)',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 3,
              fontSize: 10, fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <Icon name="grid" size={14}/>
            Add
          </button>
        )}
      </div>

      {atLimit && (
        <div style={{ marginTop: 10, fontSize: 11, color: 'var(--text-hint)' }}>
          Max {MAX} photos. Remove one to add another.
        </div>
      )}
    </div>
  );
}

function AIFeedbackCard({ body }) {
  const hasText = body.trim().length > 20;
  return (
    <div style={{
      background: 'linear-gradient(160deg, var(--english-light), #fff)',
      border: '1px solid var(--english-soft)',
      borderRadius: 14, padding: '12px 14px', position: 'relative',
      flex: 1, minHeight: 0, overflow: 'hidden',
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 8, flexShrink: 0 }}>
        <div style={{
          width: 22, height: 22, borderRadius: 7,
          background: 'var(--english-primary)', color: '#fff',
          display: 'grid', placeItems: 'center',
        }}>
          <Icon name="sparkles" size={12}/>
        </div>
        <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--english-ink)' }}>AI writing buddy</div>
      </div>

      {!hasText ? (
        <div style={{ fontSize: 11.5, color: 'var(--text-secondary)', lineHeight: 1.45 }}>
          Write a few sentences — I'll gently suggest words, grammar, and ideas.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, overflowY: 'auto', minHeight: 0 }}>
          <div style={{
            padding: '7px 10px', borderRadius: 10,
            background: 'var(--bg-card)', border: '1px solid var(--english-soft)',
          }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--math-primary)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 2 }}>
              ✓ Nice
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--text-primary)', lineHeight: 1.4 }}>
              "Kept going" is a strong phrase — keep using it!
            </div>
          </div>
          <div style={{
            padding: '7px 10px', borderRadius: 10,
            background: 'var(--bg-card)', border: '1px solid var(--english-soft)',
          }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--arcade-hover)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 2 }}>
              ✎ Try
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--text-primary)', lineHeight: 1.4 }}>
              "was hard <i>but</i>" → try "was hard, <b>yet</b>" for a grown-up feel.
            </div>
          </div>
          <div style={{
            padding: '7px 10px', borderRadius: 10,
            background: 'var(--bg-card)', border: '1px solid var(--english-soft)',
          }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--diary-primary)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 2 }}>
              ♡ Idea
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--text-primary)', lineHeight: 1.4 }}>
              Add one sensory detail — what did you <i>hear</i> or <i>smell</i>?
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* EntryGallery — photo viewer for saved entries.
 * First photo big, remaining as thumbnails. Click a thumb to swap the hero.
 */
function EntryGallery({ photos, decorated, layout = 'horizontal' }) {
  const [activeIdx, setActiveIdx] = useStateD(0);
  const active = photos[activeIdx] || photos[0];
  const bg = active.url
    ? `center / cover no-repeat url("${active.url}")`
    : `linear-gradient(135deg, ${active.tone || 'var(--diary-soft)'}, #fff)`;

  // Layout: 'horizontal' (default) — hero big, thumbs below
  // 'vertical' — hero fills, thumbs as right column; used in Entry side-by-side
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minHeight: 0 }}>
      {/* Hero photo */}
      <div style={{
        position: 'relative',
        flex: 1, minHeight: 0,
        aspectRatio: layout === 'vertical' ? undefined : '4 / 3',
        borderRadius: 12,
        background: bg,
        border: '1px solid var(--border-subtle)',
        boxShadow: decorated ? '0 4px 12px rgba(120,90,60,0.12)' : 'var(--shadow-soft)',
        overflow: 'hidden',
      }}>
        {decorated && <WashiTape color="var(--arcade-soft)" rotate={-4} top={-8} left={20} width={70}/>}
        <div style={{
          position: 'absolute', bottom: 8, right: 8,
          padding: '2px 8px', borderRadius: 999,
          background: 'rgba(0,0,0,0.45)', color: '#fff',
          fontSize: 10, fontWeight: 700, letterSpacing: '0.05em',
        }}>
          {activeIdx + 1} / {photos.length}
        </div>
      </div>

      {/* Thumbnails */}
      {photos.length > 1 && (
        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
          {photos.map((p, i) => {
            const thumbBg = p.url
              ? `center / cover no-repeat url("${p.url}")`
              : `linear-gradient(135deg, ${p.tone || 'var(--diary-soft)'}, #fff)`;
            const isActive = i === activeIdx;
            return (
              <button
                key={p.id || i}
                onClick={() => setActiveIdx(i)}
                aria-label={`View photo ${i + 1}`}
                style={{
                  width: 48, height: 48, borderRadius: 8,
                  background: thumbBg,
                  border: isActive ? '2px solid var(--diary-primary)' : '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  transform: isActive ? 'translateY(-1px)' : 'none',
                  transition: 'transform 0.15s ease',
                  flexShrink: 0,
                }}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

function WordBank({ mode }) {
  const words = ['whisper', 'gentle', 'curious', 'suddenly', 'wonder', 'quiet'];
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
      borderRadius: 14, padding: '10px 12px',
      flexShrink: 0,
    }}>
      <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-hint)', marginBottom: 6 }}>
        Word bank · L07
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        {words.map(w => (
          <button key={w} style={{
            padding: '4px 9px', borderRadius: 999,
            background: 'var(--english-light)', color: 'var(--english-ink)',
            border: '1px solid var(--english-soft)',
            fontSize: 11, fontWeight: 600,
          }}>{w}</button>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   Screen 3 — Diary Entry (detail view)
   ═══════════════════════════════════════════════ */
function DiaryEntry({ onNavigate }) {
  const [style] = useDiaryStyle();
  const decorated = style === 'decorated';

  const entry = {
    date: 'Wednesday, April 22',
    mood: 'great',
    type: 'journal',
    title: 'Brave day',
    prompt: 'What made you smile today, even a little?',
    body: `My reading test was hard, but I kept going. I didn't know the word "whisper" at first, but the picture in my head helped me guess.
Mom said I was brave. I felt warm — like sunshine on my shoulders. I want to try again tomorrow. 🌸`,
    words: ['whisper', 'brave'],
    xp: 15,
    // Journal photos — placeholder "tones" stand in for real images in prototype
    photos: [
      { id: 'ph1', tone: '#E09AAE' },
      { id: 'ph2', tone: '#EEC770' },
      { id: 'ph3', tone: '#8AC4A8' },
    ],
    // Style snapshot saved at write time — restored when viewing
    style: {
      font: 'caveat',       // 'nunito' | 'caveat' | 'patrick' | 'shadows' | 'indie' | 'kalam'
      textSize: 'm',        // 's' | 'm' | 'l'
      textColor: 'diary',   // token key
      bgMood: 'pink',       // token key
    },
  };

  const m = MOODS.find(x => x.id === entry.mood);

  const hasPhotos = entry.type === 'journal' && entry.photos && entry.photos.length > 0;

  return (
    <div style={{ height: '100%', overflow: 'hidden', background: 'var(--bg-page)', display: 'flex', flexDirection: 'column' }}>
      <DiaryChrome
        eyebrow="Diary · Entry"
        title={entry.title}
        subtitle={entry.date}
        onBack={() => onNavigate('diary-home')}
        rightSlot={
          <EntryDeleteButton onDelete={() => {/* delete action */}}/>
        }
      />

      {/* Full-width Paper — one unified page. Photos inline inside, like pasted into a diary. */}
      <div style={{
        flex: 1, minHeight: 0,
        padding: '20px 32px 24px',
        display: 'flex', flexDirection: 'column',
      }}>
        {/* Paper — restores saved bgMood; contains photos + body as one page */}
        <div style={{
          position: 'relative', flex: 1, minHeight: 0,
          background: resolvePaperBackground(decorated, entry.style?.bgMood || 'default'),
          border: '1px solid var(--border-subtle)',
          borderRadius: 16, padding: '16px 22px',
          boxShadow: 'var(--shadow-soft)',
          display: 'flex', flexDirection: 'column',
          overflow: 'hidden',
        }}>
          {decorated && <WashiTape color="var(--diary-soft)" rotate={-4} top={-9} left={28} width={90}/>}
          {decorated && <WashiTape color="var(--arcade-soft)" rotate={5} top={-9} left={'auto'} width={60}/>}

          {/* Photos pasted onto page (Journal only) — small tiles at top, same look as Write */}
          {hasPhotos && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              flexShrink: 0, marginBottom: 14,
              paddingBottom: 14, borderBottom: '1px dashed var(--border-subtle)',
            }}>
              {entry.photos.map((p, i) => {
                const tileBg = p.url
                  ? `center / cover no-repeat url("${p.url}"), var(--bg-surface)`
                  : `linear-gradient(135deg, ${p.tone || 'var(--diary-soft)'}, #fff)`;
                return (
                  <div key={p.id || i} style={{
                    width: 72, height: 72,
                    borderRadius: 10, overflow: 'hidden',
                    border: '1px solid var(--border-subtle)',
                    background: tileBg,
                    transform: decorated ? `rotate(${i % 2 === 0 ? -1.5 : 1.5}deg)` : 'none',
                    boxShadow: decorated ? '0 4px 10px rgba(120,90,60,0.14)' : 'var(--shadow-soft)',
                    flexShrink: 0,
                  }}/>
                );
              })}
              <div style={{ marginLeft: 'auto', fontSize: 10.5, color: 'var(--text-hint)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                {entry.photos.length} {entry.photos.length === 1 ? 'photo' : 'photos'}
              </div>
            </div>
          )}

          {/* Meta row */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12, flexShrink: 0 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 10,
              background: m?.dot || 'var(--diary-light)',
              border: '2.5px solid #fff',
              boxShadow: '0 2px 6px rgba(120,90,60,0.1)',
              flexShrink: 0,
            }}/>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--text-hint)', textTransform: 'uppercase' }}>
                {entry.type === 'journal' ? 'Journal' : 'Free write'}
              </div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--diary-ink)', textTransform: 'capitalize' }}>
                {entry.mood}
              </div>
            </div>
            <div style={{ flex: 1 }}/>
            <DiaryPill tone="var(--arcade-ink)" soft="var(--arcade-light)">
              +{entry.xp} XP
            </DiaryPill>
          </div>

          {/* Prompt (for journal) */}
          {entry.type === 'journal' && (
            <div style={{
              padding: '8px 12px', borderRadius: 10,
              background: 'var(--diary-light)',
              borderLeft: '3px solid var(--diary-primary)',
              marginBottom: 12,
              flexShrink: 0,
            }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--diary-primary)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 2 }}>
                Prompt
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--diary-ink)', fontFamily: 'var(--font-family-display)' }}>
                {entry.prompt}
              </div>
            </div>
          )}

          {/* Body — restores saved font / size / color */}
          <div style={{
            fontFamily: resolveFontFamily(entry.style?.font || 'caveat'),
            fontSize: resolveFontSize(entry.style?.font || 'caveat', entry.style?.textSize || 'm'),
            lineHeight: resolveLineHeight(entry.style?.font || 'caveat', entry.style?.textSize || 'm'),
            color: resolveTextColor(entry.style?.textColor || 'default'),
            whiteSpace: 'pre-wrap',
            flex: 1, minHeight: 0, overflowY: 'auto',
          }}>
            {entry.body}
          </div>

          {/* Words used row — inside paper */}
          <div style={{
            marginTop: 12, paddingTop: 12, borderTop: '1px dashed var(--border-subtle)',
            display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
            flexShrink: 0,
          }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-hint)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Words
            </div>
            {entry.words.map(w => (
              <span key={w} style={{
                padding: '3px 10px', borderRadius: 999,
                background: 'var(--english-light)', color: 'var(--english-ink)',
                border: '1px solid var(--english-soft)',
                fontSize: 11, fontWeight: 600,
              }}>{w}</span>
            ))}
            <div style={{ flex: 1 }}/>
            {/* Share stays in paper — it's about this page, not navigation */}
            <button style={{
              padding: '7px 12px', borderRadius: 10,
              background: 'var(--diary-primary)', color: '#fff',
              fontSize: 11.5, fontWeight: 600,
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 5,
              boxShadow: '0 3px 10px rgba(224,154,174,0.32)',
            }}>
              <Icon name="heart" size={12}/> Share with parent
            </button>
          </div>
        </div>

        {/* Page navigation — outside paper, like flipping through a diary */}
        <EntryPageNav entry={entry} onNavigate={onNavigate}/>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   Entry helpers
   ═══════════════════════════════════════════════ */

/* Delete button with confirm modal — prevents accidental taps by kids */
function EntryDeleteButton({ onDelete }) {
  const [confirming, setConfirming] = useStateD(false);

  useEffectD(() => {
    if (!confirming) return;
    const esc = (e) => { if (e.key === 'Escape') setConfirming(false); };
    const click = (e) => { if (!e.target.closest?.('[data-delete-confirm]')) setConfirming(false); };
    document.addEventListener('keydown', esc);
    document.addEventListener('click', click);
    return () => {
      document.removeEventListener('keydown', esc);
      document.removeEventListener('click', click);
    };
  }, [confirming]);

  return (
    <div data-delete-confirm style={{ position: 'relative' }}>
      <button
        onClick={(e) => { e.stopPropagation(); setConfirming(v => !v); }}
        style={{
          padding: '8px 12px', borderRadius: 10,
          background: 'var(--bg-card)', color: 'var(--color-error)',
          border: '1px solid var(--border-subtle)', fontSize: 12, fontWeight: 600,
          cursor: 'pointer',
        }}
      >
        Delete
      </button>
      {confirming && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 6px)', right: 0, zIndex: 60,
          background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
          borderRadius: 12, boxShadow: 'var(--shadow-modal)',
          padding: 14, width: 240,
        }}>
          <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
            Delete this page?
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--text-secondary)', marginBottom: 10, lineHeight: 1.4 }}>
            This page will be gone forever. You can't get it back.
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            <button
              onClick={() => setConfirming(false)}
              style={{
                flex: 1, padding: '7px 10px', borderRadius: 8,
                background: 'var(--bg-page)', color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                fontSize: 11.5, fontWeight: 600, cursor: 'pointer',
              }}
            >
              Keep it
            </button>
            <button
              onClick={() => { onDelete && onDelete(); setConfirming(false); }}
              style={{
                flex: 1, padding: '7px 10px', borderRadius: 8,
                background: 'var(--color-error)', color: '#fff',
                border: 'none',
                fontSize: 11.5, fontWeight: 600, cursor: 'pointer',
              }}
            >
              Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* Previous/next page navigation — below paper, like flipping a diary */
function EntryPageNav({ entry, onNavigate }) {
  // Sample neighbor pages (would come from real data)
  const prev = { dateLong: 'APR 21', title: 'Whisper' };
  const next = { dateLong: 'APR 23', title: 'The yellow fish' };

  const PageButton = ({ side, page }) => {
    if (!page) {
      return (
        <div style={{
          flex: 1, padding: '10px 14px', borderRadius: 12,
          background: 'transparent',
          display: 'flex', alignItems: 'center', gap: 10,
          opacity: 0.35,
          justifyContent: side === 'prev' ? 'flex-start' : 'flex-end',
        }}>
          <div style={{ fontSize: 11, color: 'var(--text-hint)' }}>
            {side === 'prev' ? 'No earlier pages' : 'No later pages'}
          </div>
        </div>
      );
    }
    return (
      <button
        onClick={() => onNavigate('diary-entry')}
        style={{
          flex: 1, padding: '10px 14px', borderRadius: 12,
          background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
          display: 'flex', alignItems: 'center', gap: 10,
          cursor: 'pointer',
          textAlign: side === 'prev' ? 'left' : 'right',
          transition: 'all 0.15s ease',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-surface)'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--bg-card)'; }}
      >
        {side === 'prev' && <Icon name="chevron-left" size={14} color="var(--text-secondary)"/>}
        <div style={{ flex: 1, minWidth: 0, textAlign: side === 'prev' ? 'left' : 'right' }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-hint)', letterSpacing: '0.08em' }}>
            {side === 'prev' ? 'Earlier' : 'Later'} · {page.dateLong}
          </div>
          <div style={{
            fontFamily: 'var(--font-family-handwritten, "Caveat"), cursive',
            fontSize: 18, fontWeight: 600, color: 'var(--diary-ink)', lineHeight: 1.1, marginTop: 2,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>
            {page.title}
          </div>
        </div>
        {side === 'next' && <Icon name="chevron-right" size={14} color="var(--text-secondary)"/>}
      </button>
    );
  };

  return (
    <div style={{
      marginTop: 14, display: 'flex', gap: 10, flexShrink: 0,
    }}>
      <PageButton side="prev" page={prev}/>
      <PageButton side="next" page={next}/>
    </div>
  );
}

/* ═══════════════════════════════════════════════
   Screen 4 — Diary Calendar (monthly)
   ═══════════════════════════════════════════════ */
function DiaryCalendar({ onNavigate }) {
  const [style] = useDiaryStyle();
  const decorated = style === 'decorated';

  // Static April 2026 data
  const month = 'April';
  const year = 2026;
  const firstDay = 3; // Wed (0=Sun)
  const daysInMonth = 30;
  const today = 24;

  // Pre-seeded moods
  const moodByDay = {
    1: 'happy', 2: 'calm', 3: 'great', 5: 'tired', 7: 'curious',
    8: 'happy', 10: 'great', 11: 'happy', 12: 'calm', 14: 'sad',
    15: 'curious', 16: 'happy', 18: 'great', 20: 'calm', 21: 'curious',
    22: 'great', 23: 'happy',
  };

  // Day off status per day — from DayOffRequest table (existing app feature).
  // 'approved' = parent approved, 'pending' = waiting for parent approval
  const dayOffByDay = {
    6: 'approved',   // family trip
    13: 'approved',  // sick day
    17: 'pending',   // waiting for parent
  };

  // Build grid
  const cells = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);

  const entriesCount = Object.keys(moodByDay).length;
  const moodCounts = Object.values(moodByDay).reduce((acc, m) => { acc[m] = (acc[m] || 0) + 1; return acc; }, {});

  return (
    <div style={{ height: '100%', overflow: 'hidden', background: 'var(--bg-page)', display: 'flex', flexDirection: 'column' }}>
      <DiaryChrome
        eyebrow="Diary · Month"
        title={`${month} ${year}`}
        subtitle={`${entriesCount} entries`}
        onBack={() => onNavigate('diary-home')}
        rightSlot={
          <div style={{ display: 'flex', gap: 4, background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 10, padding: 3 }}>
            <button style={{ padding: '6px 8px', color: 'var(--text-secondary)' }}><Icon name="chevron-left" size={13}/></button>
            <button style={{ padding: '6px 12px', color: 'var(--text-primary)', fontSize: 12, fontWeight: 600 }}>Apr</button>
            <button style={{ padding: '6px 8px', color: 'var(--text-secondary)' }}><Icon name="chevron-right" size={13}/></button>
          </div>
        }
      />

      <div style={{
        flex: 1, minHeight: 0,
        padding: '14px 28px 16px',
        display: 'grid',
        gridTemplateColumns: '1fr 260px',
        gap: 16,
      }}>
        {/* LEFT — calendar grid */}
        <div style={{
          position: 'relative',
          background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
          borderRadius: 16, padding: '14px 16px', boxShadow: 'var(--shadow-soft)',
          display: 'flex', flexDirection: 'column',
          minHeight: 0,
        }}>
          {decorated && <WashiTape color="var(--diary-soft)" rotate={-3} top={-9} left={30} width={100}/>}

          {/* Weekday labels */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 6, marginBottom: 6, flexShrink: 0 }}>
            {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => (
              <div key={d} style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-hint)', letterSpacing: '0.08em', textTransform: 'uppercase', textAlign: 'center', paddingBottom: 2 }}>
                {d}
              </div>
            ))}
          </div>

          {/* Day cells */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(7, 1fr)',
            gridAutoRows: '1fr',
            gap: 6,
            flex: 1, minHeight: 0,
          }}>
            {cells.map((d, i) => {
              if (d === null) return <div key={i}/>;
              const mood = moodByDay[d];
              const dayOff = dayOffByDay[d]; // 'approved' | 'pending' | undefined
              const m = mood ? MOODS.find(x => x.id === mood) : null;
              const isToday = d === today;
              const isFuture = d > today;
              const isDayOffApproved = dayOff === 'approved';
              const isDayOffPending  = dayOff === 'pending';
              const isMissed = !mood && !dayOff && !isFuture && !isToday;

              // Title for accessibility/tooltip
              let titleText;
              if (isDayOffApproved) titleText = 'Day off · approved';
              else if (isDayOffPending) titleText = 'Day off · waiting for parent';
              else if (isMissed) titleText = 'No entry this day';

              // Cell style branching by state
              const cellBg =
                isDayOffApproved ? 'var(--arcade-light)'
                : mood ? 'var(--bg-card)'
                : isFuture ? 'transparent'
                : 'var(--bg-page)';

              const cellBorder =
                isToday ? '2px solid var(--diary-primary)'
                : isDayOffApproved ? '1px solid var(--arcade-soft)'
                : isDayOffPending ? '1px dashed var(--arcade-primary)'
                : isMissed ? '1px dashed var(--border-subtle)'
                : '1px solid var(--border-subtle)';

              const cellOpacity =
                isFuture ? 0.4
                : isDayOffPending ? 0.75
                : isMissed ? 0.65
                : 1;

              return (
                <button
                  key={i}
                  onClick={() => mood && onNavigate('diary-entry')}
                  disabled={isFuture}
                  title={titleText}
                  style={{
                    borderRadius: 10,
                    background: cellBg,
                    border: cellBorder,
                    padding: 5,
                    display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
                    opacity: cellOpacity,
                    cursor: mood ? 'pointer' : 'default',
                    transition: 'transform 0.15s ease',
                    position: 'relative',
                    minHeight: 0,
                  }}
                  onMouseEnter={(e) => { if (mood) e.currentTarget.style.transform = 'translateY(-1px)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; }}
                >
                  <div style={{
                    fontSize: 11, fontWeight: isToday ? 700 : 600,
                    color: isToday ? 'var(--diary-primary)'
                      : isDayOffApproved ? 'var(--arcade-ink)'
                      : (isMissed || isDayOffPending) ? 'var(--text-hint)'
                      : 'var(--text-primary)',
                    textAlign: 'left', lineHeight: 1,
                  }}>
                    {d}
                  </div>
                  {/* Mood dot — only if entry exists */}
                  {m && (
                    <div style={{
                      alignSelf: 'flex-end',
                      width: 12, height: 12, borderRadius: 999,
                      background: m.dot,
                      border: '1.5px solid #fff',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.08)',
                    }}/>
                  )}
                  {/* Day off — approved: solid coffee icon, pending: faded */}
                  {dayOff && (
                    <div style={{
                      alignSelf: 'flex-end',
                      color: isDayOffApproved ? 'var(--arcade-primary)' : 'var(--text-hint)',
                      opacity: isDayOffPending ? 0.6 : 1,
                      display: 'grid', placeItems: 'center',
                    }}>
                      <Icon name="coffee" size={12}/>
                    </div>
                  )}
                  {/* Missed day — tiny gray dot */}
                  {isMissed && (
                    <div style={{
                      alignSelf: 'flex-end',
                      width: 4, height: 4, borderRadius: 999,
                      background: 'var(--text-hint)',
                      opacity: 0.5,
                    }}/>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* RIGHT — mood legend + summary + CTA */}
        <aside style={{ display: 'flex', flexDirection: 'column', gap: 10, minHeight: 0 }}>
          {/* Legend */}
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
            borderRadius: 14, padding: '10px 12px',
          }}>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-hint)', marginBottom: 8 }}>
              Mood legend
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px 10px' }}>
              {MOODS.map(m => (
                <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 999, background: m.dot, border: '1.5px solid #fff', boxShadow: '0 1px 2px rgba(0,0,0,0.08)' }}/>
                  <div style={{ fontSize: 11.5, color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{m.label}</div>
                  <div style={{ marginLeft: 'auto', fontSize: 10.5, color: 'var(--text-hint)', fontWeight: 600 }}>
                    {moodCounts[m.id] || 0}
                  </div>
                </div>
              ))}
            </div>
            {/* Day off legend row */}
            <div style={{
              marginTop: 10, paddingTop: 8, borderTop: '1px dashed var(--border-subtle)',
              display: 'flex', flexDirection: 'column', gap: 6,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 14, height: 14, borderRadius: 4, background: 'var(--arcade-light)', border: '1px solid var(--arcade-soft)', display: 'grid', placeItems: 'center', color: 'var(--arcade-primary)' }}>
                  <Icon name="coffee" size={9}/>
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--text-secondary)' }}>Day off</div>
                <div style={{ marginLeft: 'auto', fontSize: 10.5, color: 'var(--text-hint)', fontWeight: 600 }}>2</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ width: 14, height: 14, borderRadius: 4, background: 'var(--bg-page)', border: '1px dashed var(--arcade-primary)', display: 'grid', placeItems: 'center', color: 'var(--text-hint)', opacity: 0.7 }}>
                  <Icon name="coffee" size={9}/>
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--text-secondary)' }}>Waiting</div>
                <div style={{ marginLeft: 'auto', fontSize: 10.5, color: 'var(--text-hint)', fontWeight: 600 }}>1</div>
              </div>
            </div>
          </div>

          {/* Summary */}
          <div style={{
            background: 'linear-gradient(160deg, var(--diary-light), #fff)',
            border: '1px solid var(--diary-soft)',
            borderRadius: 14, padding: '12px 14px', position: 'relative',
            flex: 1, minHeight: 0,
            display: 'flex', flexDirection: 'column',
          }}>
            {decorated && <WashiTape color="var(--arcade-soft)" rotate={-5} top={-9} left={18} width={70}/>}
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--diary-ink)' }}>
              April summary
            </div>
            <div style={{
              fontFamily: decorated ? 'var(--font-family-handwritten, "Caveat"), cursive' : 'var(--font-family-display)',
              fontSize: decorated ? 22 : 17,
              fontWeight: 600, color: 'var(--diary-ink)', marginTop: 4, lineHeight: 1.2,
            }}>
              Mostly happy.<br/>A brave month.
            </div>
            <div style={{ marginTop: 'auto', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6 }}>
              <MiniStat label="Entries" value={entriesCount}/>
              <MiniStat label="Streak"  value="5"/>
              <MiniStat label="Words"   value="642"/>
            </div>
          </div>

          {/* CTA removed — Calendar is a map/explorer, not a writing trigger */}
        </aside>
      </div>
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 10, padding: '6px 4px',
      border: '1px solid var(--border-subtle)', textAlign: 'center',
    }}>
      <div style={{ fontFamily: 'var(--font-family-display)', fontSize: 16, fontWeight: 700, color: 'var(--diary-ink)', lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 9.5, color: 'var(--text-hint)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginTop: 3 }}>{label}</div>
    </div>
  );
}

// DiaryTweaks removed — Diary is fixed to Decorated style per design rules.
// Diary Preview.html has its own in-page toggle for reference comparison.

Object.assign(window, { DiaryHome, DiaryWrite, DiaryEntry, DiaryCalendar });

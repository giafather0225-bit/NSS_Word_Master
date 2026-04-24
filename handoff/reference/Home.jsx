// Dashboard Hub — entry point to English / Math / Diary apps
// B palette (Pinterest Schoolgirl Diary): Baby Blue, Mint, Sweet Pink, Butter, Lavender
// Layout reference: user's real app screenshot
//   Left  — Today checklist with XP badges
//   Center— Section cards (English / Math / Diary / Arcade / Shop)
//   Right — Profile + stats + Ocean World placeholder
//   Bottom-right — GIA mascot (circular placeholder)

const { useState: useStateH } = React;

function Home({ onNavigate }) {
  const today = new Date();
  const dateStr = today.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  return (
    <div style={{
      height: '100%', overflowY: 'auto',
      background: 'var(--bg-page)',
      position: 'relative',
    }}>
      {/* Top-right overflow menu — hidden entry to Parent Dashboard */}
      <TopRightMenu onNavigate={onNavigate}/>

      {/* Bottom-right mascot placeholder */}
      <MascotPlaceholder/>

      <div style={{
        maxWidth: 1280, margin: '0 auto', padding: '28px 36px 56px',
        display: 'grid', gridTemplateColumns: '260px 1fr 280px', gap: 28,
      }}>
        {/* ═══ LEFT — Today Checklist ═══ */}
        <aside style={{ display: 'flex', flexDirection: 'column', gap: 16, maxHeight: 'calc(100vh - 56px)' }}>
          <GreetingBlock dateStr={dateStr}/>
          <TodayChecklist/>
        </aside>

        {/* ═══ CENTER — Section Cards ═══ */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <HeaderBar/>
          <SectionGrid onNavigate={onNavigate}/>
          <WeeklyStrip/>
        </section>

        {/* ═══ RIGHT — Stats + Ocean World ═══ */}
        <aside style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <StatsStack/>
          <OceanWorldCard/>
        </aside>
      </div>

    </div>
  );
}

function TopRightMenu({ onNavigate }) {
  const [open, setOpen] = useStateH(false);
  return (
    <div style={{ position: 'fixed', top: 14, right: 14, zIndex: 50 }}>
      <button
        onClick={() => setOpen(o => !o)}
        aria-label="More options"
        style={{
          width: 40, height: 40, borderRadius: '50%',
          background: open ? 'var(--bg-card)' : 'transparent',
          border: open ? '1px solid var(--border-subtle)' : '1px solid transparent',
          display: 'grid', placeItems: 'center',
          color: 'var(--text-secondary)',
          boxShadow: open ? 'var(--shadow-soft)' : 'none',
          transition: 'all 0.15s ease',
        }}
        onMouseEnter={(e) => { if (!open) e.currentTarget.style.background = 'var(--bg-surface)'; }}
        onMouseLeave={(e) => { if (!open) e.currentTarget.style.background = 'transparent'; }}
      >
        {/* Horizontal 3-dot icon */}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="5" cy="12" r="2"/>
          <circle cx="12" cy="12" r="2"/>
          <circle cx="19" cy="12" r="2"/>
        </svg>
      </button>

      {open && (
        <>
          <div
            onClick={() => setOpen(false)}
            style={{ position: 'fixed', inset: 0, zIndex: 1 }}
          />
          <div style={{
            position: 'absolute', right: 0, top: 48,
            minWidth: 200, padding: 6,
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 14,
            boxShadow: '0 12px 30px rgba(90,65,40,0.16)',
            zIndex: 2,
          }}>
            <MenuRow
              icon="users" label="Parent Dashboard"
              onClick={() => { setOpen(false); onNavigate('parent'); }}
            />
            <MenuRow
              icon="settings" label="Settings"
              onClick={() => { setOpen(false); }}
            />
          </div>
        </>
      )}
    </div>
  );
}

function MenuRow({ icon, label, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        width: '100%', padding: '9px 10px', borderRadius: 10,
        display: 'flex', alignItems: 'center', gap: 10,
        fontSize: 13, color: 'var(--text-primary)',
        textAlign: 'left',
      }}
      onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-surface)'}
      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
    >
      <span style={{ color: 'var(--text-secondary)', display: 'flex' }}>
        <Icon name={icon} size={15}/>
      </span>
      {label}
    </button>
  );
}

/* ═══════════════ LEFT COLUMN ═══════════════ */

function GreetingBlock({ dateStr }) {
  return (
    <div style={{ padding: '4px 4px 0' }}>
      <div style={{ fontSize: 12, color: 'var(--text-hint)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 6 }}>
        {dateStr}
      </div>
      <div style={{
        fontFamily: 'var(--font-family-display)',
        fontSize: 30, fontWeight: 600, color: 'var(--text-primary)',
        letterSpacing: '-0.02em', lineHeight: 1.1,
      }}>
        Good morning,<br/>
        <span style={{ color: 'var(--diary-primary)' }}>Gia</span>
      </div>
    </div>
  );
}

function TodayChecklist() {
  // Parent Dashboard에서 선택한 모든 작업이 여기로 내려옴.
  // 섹션별로 그룹핑해서 시각적으로 정리.
  const groups = [
    {
      section: 'english',
      label: 'English',
      items: [
        { id: 'e1', label: 'Voca · Lesson 07 Preview',      xp: 10, done: true  },
        { id: 'e2', label: 'Voca · Word Match (3 rounds)',  xp: 15, done: true  },
        { id: 'e3', label: 'Voca · Fill the Blank',         xp: 15, done: false, due: 'now' },
        { id: 'e4', label: 'Voca · Spelling Master',        xp: 20, done: false },
        { id: 'e5', label: 'Voca · Make a Sentence (×3)',   xp: 20, done: false },
      ],
    },
    {
      section: 'math',
      label: 'Math',
      items: [
        { id: 'm1', label: 'Multiply by 6 · Learn',         xp: 10, done: false },
        { id: 'm2', label: 'Multiply by 6 · Practice 1',    xp: 15, done: false },
        { id: 'm3', label: 'Fact Fluency · 60 sec',         xp: 10, done: false },
        { id: 'm4', label: 'Kangaroo · 3 problems',         xp: 15, done: false },
      ],
    },
    {
      section: 'diary',
      label: 'Diary',
      items: [
        { id: 'd1', label: '3 sentences with new words',    xp: 15, done: false },
        { id: 'd2', label: 'Today\'s mood check-in',        xp: 5,  done: false },
      ],
    },
    {
      section: 'review',
      label: 'Review',
      items: [
        { id: 'r1', label: 'Yesterday\'s wrong problems',   xp: 15, done: false },
      ],
    },
  ];

  const all = groups.flatMap(g => g.items);
  const doneCount = all.filter(i => i.done).length;
  const totalCount = all.length;
  const totalXP = all.reduce((s, i) => s + i.xp, 0);
  const earnedXP = all.filter(i => i.done).reduce((s, i) => s + i.xp, 0);
  const progressPct = totalCount ? (doneCount / totalCount) * 100 : 0;

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 20, padding: 18,
      boxShadow: 'var(--shadow-soft)',
      display: 'flex', flexDirection: 'column',
      minHeight: 0,
      flex: 1,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 4 }}>
        <div style={{ fontSize: 14, fontWeight: 700 }}>Today's tasks</div>
        <div style={{ fontSize: 11, color: 'var(--text-hint)' }}>{doneCount} / {totalCount} done</div>
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-hint)', marginBottom: 10 }}>
        Set by parent · {earnedXP} / {totalXP} XP earned
      </div>

      {/* Overall progress bar */}
      <div style={{ height: 4, background: 'var(--bg-surface)', borderRadius: 4, overflow: 'hidden', marginBottom: 12 }}>
        <div style={{ width: `${progressPct}%`, height: '100%', background: 'var(--diary-primary)', borderRadius: 4, transition: 'width 0.3s ease' }}/>
      </div>

      {/* Grouped scrollable list */}
      <div style={{
        display: 'flex', flexDirection: 'column', gap: 14,
        overflowY: 'auto', paddingRight: 4,
        flex: 1, minHeight: 0,
      }}>
        {groups.map(g => <ChecklistGroup key={g.section} group={g}/>)}
      </div>
    </div>
  );
}

function ChecklistGroup({ group }) {
  const secColor = `var(--section-${group.section}-color)`;
  const doneInGroup = group.items.filter(i => i.done).length;
  return (
    <div>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 4px', marginBottom: 6,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: secColor }}/>
          <span style={{
            fontSize: 10.5, fontWeight: 700, letterSpacing: '0.08em',
            textTransform: 'uppercase', color: secColor,
          }}>
            {group.label}
          </span>
        </div>
        <span style={{ fontSize: 10, color: 'var(--text-hint)' }}>
          {doneInGroup}/{group.items.length}
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {group.items.map(item => <ChecklistRow key={item.id} {...item} section={group.section}/>)}
      </div>
    </div>
  );
}

function ChecklistRow({ label, xp, section, done, due }) {
  const secColor = `var(--section-${section}-color)`;
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '7px 10px', borderRadius: 10,
      background: done ? 'var(--bg-surface)' : due === 'now' ? `color-mix(in srgb, ${secColor} 8%, transparent)` : 'transparent',
      opacity: done ? 0.55 : 1,
      border: due === 'now' ? `1px solid color-mix(in srgb, ${secColor} 30%, transparent)` : '1px solid transparent',
    }}>
      <span style={{
        width: 18, height: 18, borderRadius: '50%',
        border: `1.5px solid ${done ? secColor : 'var(--border-default)'}`,
        background: done ? secColor : 'transparent',
        display: 'grid', placeItems: 'center',
        flexShrink: 0,
      }}>
        {done && <Icon name="check" size={11} color="#fff" strokeWidth={3}/>}
      </span>
      <div style={{
        flex: 1, fontSize: 12.5,
        textDecoration: done ? 'line-through' : 'none',
        color: 'var(--text-primary)',
        lineHeight: 1.3,
      }}>
        {label}
        {due === 'now' && !done && (
          <span style={{
            marginLeft: 6, fontSize: 9.5, fontWeight: 700,
            padding: '1px 6px', borderRadius: 999,
            background: secColor, color: '#fff',
            letterSpacing: '0.04em',
          }}>NOW</span>
        )}
      </div>
      <div style={{
        fontSize: 10, fontWeight: 700, letterSpacing: '0.03em',
        padding: '2px 7px', borderRadius: 20,
        background: `color-mix(in srgb, ${secColor} 14%, transparent)`,
        color: secColor,
        flexShrink: 0,
      }}>+{xp}</div>
    </div>
  );
}

/* ═══════════════ CENTER COLUMN ═══════════════ */

function HeaderBar() {
  return (
    <div style={{ padding: '2px 2px' }}>
      <div style={{ fontSize: 11, color: 'var(--text-hint)', letterSpacing: '0.09em', textTransform: 'uppercase' }}>
        Pick a room
      </div>
      <div style={{
        fontFamily: 'var(--font-family-display)',
        fontSize: 22, fontWeight: 600, color: 'var(--text-primary)',
        letterSpacing: '-0.015em', marginTop: 2,
      }}>
        What do you feel like today?
      </div>
    </div>
  );
}

function SectionGrid({ onNavigate }) {
  // 6 cards in one uniform grid — all same size
  const all = [
    { id: 'english-home', title: 'English', color: 'var(--english-primary)', soft: 'var(--english-light)', ink: 'var(--english-ink)' },
    { id: 'math-home',    title: 'Math',    color: 'var(--math-primary)',    soft: 'var(--math-light)',    ink: 'var(--math-ink)'    },
    { id: 'diary-home',   title: 'Diary',   color: 'var(--diary-primary)',   soft: 'var(--diary-light)',   ink: 'var(--diary-ink)'   },
    { id: 'arcade',       title: 'Arcade',  color: 'var(--arcade-primary)',  soft: 'var(--arcade-light)',  ink: 'var(--arcade-ink)'  },
    { id: 'rewards',      title: 'Shop',    color: 'var(--rewards-primary)', soft: 'var(--rewards-light)', ink: 'var(--rewards-ink)' },
    { id: 'review',       title: 'Review',  color: 'var(--review-primary)',  soft: 'var(--review-light)',  ink: 'var(--review-ink)'  },
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gridAutoRows: '1fr',
      gap: 14,
    }}>
      {all.map(c => <SmallSectionCard key={c.id} card={c} onClick={() => onNavigate(c.id)}/>)}
    </div>
  );
}

function SmallSectionCard({ card, onClick }) {
  const [hover, setHover] = useStateH(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: 'relative',
        padding: '20px 14px',
        borderRadius: 20,
        background: card.soft,
        border: '1px solid var(--border-subtle)',
        aspectRatio: '1 / 1',
        minHeight: 140,
        textAlign: 'center',
        overflow: 'hidden',
        transform: hover ? 'translateY(-2px)' : 'none',
        boxShadow: hover ? '0 8px 20px rgba(120,90,60,0.08)' : 'var(--shadow-soft)',
        transition: 'all 0.18s ease',
        display: 'grid', placeItems: 'center',
        width: '100%',
      }}
    >
      <div style={{
        fontFamily: 'var(--font-family-display)',
        fontSize: 28, fontWeight: 600,
        letterSpacing: '-0.02em', lineHeight: 1.25,
        color: card.ink || card.color,
        maxWidth: '100%',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        padding: '0 4px',
      }}>
        {card.title}
      </div>
    </button>
  );
}

function WeeklyStrip() {
  const days = ['S','M','T','W','T','F','S'];
  const values = [0.3, 0.8, 0.6, 1.0, 0.4, 0.9, 0.0]; // sunday..saturday
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 16, padding: '16px 18px',
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 600 }}>This week</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--text-hint)' }}>
          5-day streak
          <span style={{ color: 'var(--arcade-primary)', display: 'inline-flex' }}>
            <Icon name="flame" size={12}/>
          </span>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 8, alignItems: 'end', height: 64 }}>
        {days.map((d, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <div style={{
              width: '100%', height: `${Math.max(values[i]*56, 4)}px`,
              background: values[i] >= 0.9 ? 'var(--diary-primary)'
                        : values[i] >= 0.5 ? 'var(--diary-soft)'
                        : values[i] > 0    ? 'var(--bg-surface)'
                                           : 'var(--border-subtle)',
              borderRadius: 6, transition: 'all 0.2s ease',
            }}/>
            <div style={{ fontSize: 10, color: 'var(--text-hint)' }}>{d}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════ RIGHT COLUMN ═══════════════ */

function ProfileCard() {
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 20, padding: 18,
      boxShadow: 'var(--shadow-soft)',
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
        <div style={{
          fontFamily: 'var(--font-family-display)',
          fontSize: 18, fontWeight: 600, letterSpacing: '-0.01em',
          color: 'var(--text-primary)',
        }}>
          Gia
        </div>
        <div style={{
          fontSize: 10.5, fontWeight: 700, letterSpacing: '0.06em',
          color: 'var(--arcade-ink)',
        }}>
          LV.1
        </div>
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-hint)', marginTop: 2 }}>
        Grade 3 · Ocean crew
      </div>

      {/* XP bar */}
      <div style={{ marginTop: 16, position: 'relative' }}>
        <div style={{ height: 8, borderRadius: 8, background: 'var(--bg-surface)', overflow: 'hidden' }}>
          <div style={{ width: '31%', height: '100%', background: 'var(--diary-primary)', borderRadius: 8 }}/>
        </div>
        <div style={{
          position: 'absolute', right: 0, top: -18,
          fontSize: 10.5, color: 'var(--text-hint)', letterSpacing: '0.02em',
        }}>
          31 / 100 XP
        </div>
      </div>
    </div>
  );
}

function StatsStack() {
  const stats = [
    { label: 'Words learned', value: '342', sub: 'all-time',   color: 'var(--english-primary)', icon: 'book-open' },
    { label: 'Total XP',      value: '1,250', sub: '+45 today', color: 'var(--diary-primary)',   icon: 'sparkles' },
    { label: 'Streak',        value: '5 days', sub: 'best: 12',  color: 'var(--arcade-primary)',  icon: 'flame' },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {stats.map((s) => (
        <div key={s.label} style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '12px 14px', borderRadius: 16,
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
        }}>
          <span style={{
            width: 32, height: 32, borderRadius: 10,
            background: `color-mix(in srgb, ${s.color} 14%, transparent)`,
            color: s.color,
            display: 'grid', placeItems: 'center',
          }}>
            <Icon name={s.icon} size={15}/>
          </span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 11, color: 'var(--text-hint)' }}>{s.label}</div>
            <div style={{ fontSize: 16, fontWeight: 700, letterSpacing: '-0.01em', fontFamily: 'var(--font-family-display)' }}>{s.value}</div>
          </div>
          <div style={{ fontSize: 10.5, color: 'var(--text-hint)' }}>{s.sub}</div>
        </div>
      ))}
    </div>
  );
}

function OceanWorldCard() {
  return (
    <div style={{
      position: 'relative',
      background: 'linear-gradient(180deg, var(--english-light), var(--english-soft))',
      border: '1px solid var(--border-subtle)',
      borderRadius: 20, padding: '16px 16px 14px',
      minHeight: 160,
      overflow: 'hidden',
    }}>
      <div style={{ fontSize: 11, color: 'var(--english-ink)', letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 700 }}>
        World
      </div>
      <div style={{
        fontFamily: 'var(--font-family-display)',
        fontSize: 20, fontWeight: 600, color: 'var(--english-ink)',
        letterSpacing: '-0.01em', marginTop: 2,
      }}>
        Ocean World
      </div>
      <div style={{ fontSize: 11, color: 'var(--english-ink)', opacity: 0.7, marginTop: 2 }}>
        Illustration placeholder
      </div>

      {/* Placeholder illustration */}
      <svg viewBox="0 0 200 90" style={{ width: '100%', marginTop: 10, display: 'block' }}>
        <defs>
          <pattern id="dash" patternUnits="userSpaceOnUse" width="6" height="6">
            <path d="M0,3 L6,3" stroke="var(--english-ink)" strokeWidth="0.5" opacity="0.3"/>
          </pattern>
        </defs>
        <rect x="0" y="0" width="200" height="90" fill="url(#dash)" opacity="0.5"/>
        <text x="100" y="48" fill="var(--english-ink)" opacity="0.55" fontSize="10" textAnchor="middle" fontStyle="italic">
          ocean illustration
        </text>
      </svg>

      <div style={{ marginTop: 8, fontSize: 11, color: 'var(--english-ink)', opacity: 0.75 }}>
        3 / 10 sea creatures collected
      </div>
    </div>
  );
}

function MascotPlaceholder() {
  return (
    <div style={{
      position: 'fixed', right: 24, bottom: 24,
      width: 92, height: 92, borderRadius: '50%',
      background: '#fff',
      border: '1px solid var(--border-subtle)',
      boxShadow: '0 8px 24px rgba(120,90,60,0.12)',
      display: 'grid', placeItems: 'center',
      zIndex: 10,
    }}>
      <div style={{
        width: 72, height: 72, borderRadius: '50%',
        background: 'var(--bg-surface)',
        display: 'grid', placeItems: 'center',
        color: 'var(--text-hint)', fontSize: 10, fontWeight: 600,
        letterSpacing: '0.03em',
      }}>
        GIA
      </div>
    </div>
  );
}

Object.assign(window, { Home });

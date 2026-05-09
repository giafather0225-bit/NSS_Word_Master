# Gia's Island — Complete Design Index

총 24개 화면, 4개 phase로 핸드오프 완료.

| Phase | 화면 # | 패키지 |
|-------|--------|--------|
| 1 | ① Splash · ② Map · ③ Zone Detail · ④ Forest · ⑤ Inventory · ⑥ Shop · ⑦ Dex · ⑧ Diary | `design_handoff_island_map` |
| 2 | ⑨ Feed · ⑩ Sleep · ⑪ Farewell→Dex · ⑫ Empty States · ⑬ Daily/Missions · ⑭ Mailbox · ⑮ Settings · ⑯ Purchase | `design_handoff_island_v2` |
| 3 | ⑰ Loading · ⑱ Error · ⑲ Push · ⑳ Coachmarks | `design_handoff_island_v3` |
| 4 | ㉑ Onboarding · ㉒ Evolution · ㉓ Photo · ㉔ Toast | `design_handoff_island_v4` ← 본 패키지 |

전체 디자인 원본: `Gia's Island.html`

---

## 통합 구현 우선순위 (제안)

**Sprint 1 — 코어 루프:**
④ Forest → ⑨ Feed → ⑩ Sleep → ㉔ Toast → ⑫ Empty States

**Sprint 2 — 진입/이탈:**
① Splash → ⑰ Loading → ⑱ Error → ㉑ Onboarding → ⑳ Coachmarks

**Sprint 3 — 메타/진행:**
② Map → ⑤ Inventory → ⑥ Shop → ⑯ Purchase → ⑬ Daily → ⑦ Dex

**Sprint 4 — 정서/바이럴:**
㉒ Evolution → ⑧ Diary → ㉓ Photo → ⑪ Farewell

**Sprint 5 — 라이브옵스:**
⑮ Settings → ⑭ Mailbox → ⑲ Push

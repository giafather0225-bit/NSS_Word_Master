# G3 Misconception Library

Grade 3 (3학년) 학습자가 자주 보이는 수학 오개념(misconception)을 표준별로 정리한
참조 라이브러리. 각 파일은 단일 CCSS 표준에 대응하며, 7개 misconception 항목을
학술 인용과 함께 수록.

## 파일 명세

| 파일 | 표준 | 영역 |
|---|---|---|
| `3.NBT.1.json` | 3.NBT.A.1 | 반올림 |
| `3.NBT.2.json` | 3.NBT.A.2 | 1,000 이내 덧셈/뺄셈 |
| `3.NBT.A.3.json` | 3.NBT.A.3 | 10의 배수 곱셈 |
| `3.OA.A.1.json` | 3.OA.A.1 | 곱셈의 의미 |
| `3.OA.A.2.json` | 3.OA.A.2 | 나눗셈의 의미 |
| `3.OA.A.3.json` | 3.OA.A.3 | 곱·나눗셈 문장제 |
| `3.OA.A.4.json` | 3.OA.A.4 | 미지수 찾기 |
| `3.OA.B.5.json` | 3.OA.B.5 | 곱셈 성질 |
| `3.OA.C.7.json` | 3.OA.C.7 | 곱·나눗셈 fluency |
| `3.OA.D.8.json` | 3.OA.D.8 | 2단계 문제, 연산 순서 |
| `3.OA.D.9.json` | 3.OA.D.9 | 산술 패턴 |
| `3.NF.A.1.json` | 3.NF.A.1 | 분수의 의미 |
| `3.MD.A.1.json` | 3.MD.A.1 | 시간 측정 |
| `3.MD.A.2.json` | 3.MD.A.2 | 질량·부피 측정 |
| `3.MD.B.3.json` | 3.MD.B.3 | 그림·막대 그래프 |
| `3.MD.B.4.json` | 3.MD.B.4 | 라인 플롯 |
| `3.MD.C.5.json` | 3.MD.C.5 | 넓이 개념 |
| `3.MD.C.6.json` | 3.MD.C.6 | 넓이 세기 측정 |
| `3.MD.C.7.json` | 3.MD.C.7 | 넓이와 곱셈 |
| `3.MD.D.8.json` | 3.MD.D.8 | 둘레 |
| `3.G.A.1.json` | 3.G.A.1 | 다각형 분류 |
| `3.G.A.2.json` | 3.G.A.2 | 도형 분할과 분수 |

총 22개 표준 × 7개 misconception × 학술 인용 ≈ **154개 항목**.

## JSON 스키마

```json
{
  "standard": "3.NF.A.1",
  "standard_description": "Common Core 공식 정의 원문",
  "sources": ["참고문헌 1", "참고문헌 2", ...],
  "misconceptions": [
    {
      "misconception_id": "3.NF.A.1.M01",
      "error_type": "denominator_size_confusion",
      "short_label": "한 줄 요약",
      "description": "상세 설명",
      "example": "구체적 학습자 응답 예시",
      "citation": "학술 인용 원문 (NCTM, Van de Walle 등)",
      "source": "출처",
      "remediation": "치료 전략",
      "bloom_level": 1
    },
    ...
  ],
  "metadata": {
    "created": "2026-05-XX",
    "version": "1.0",
    "lesson_uses": ["G3_U8_L3", ...],
    "total_misconceptions": 7
  }
}
```

## 활용

레슨 JSON의 각 문항 `expected_errors` 필드에 misconception_id를 등록하면,
학습자가 오답을 낼 때 적절한 치료 자료를 자동 제시할 수 있음.

```json
{
  "id": "PT_03",
  "question": "...",
  "expected_errors": ["3.NF.A.1.M02", "3.NF.A.1.M03"]
}
```

Stage 7 학습자 파일럿(2026-06-13~19) 후, 실제 학습자 오답과 매칭률을 측정하여
보강 필요 항목을 식별.

## 참고문헌

- NCTM Progressions for the Common Core State Standards (K-6)
- Van de Walle, J.A., Karp, K.S., & Bay-Williams, J.M. (2013). *Elementary and Middle School Mathematics* (8th ed.). Pearson.
- Van Hiele, P.M. (1986). *Structure and Insight*. Academic Press.
- Battista, M.T. (2007). *The Development of Geometric and Spatial Thinking* (NCTM Handbook).
- EngageNY Grade 3 Modules 1-7 Teacher Editions
- Smarter Balanced Assessment Consortium — Grade 3 Math Item Specifications (2015)
- Friel, S.N., Curcio, F.R., & Bright, G.W. (2001). *Making sense of graphs*. JRME 32(2).
- Outhred, L. & Mitchelmore, M. (2000). *Young children's intuitive understanding of rectangular area*. JRME 31(2).

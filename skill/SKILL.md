---
name: repo-ontology
description: 코드베이스 도메인 온톨로지 역색인(onto trace) 및 정합성 검증(onto lint) 워크플로우
---

# repo-ontology SKILL

코드 레포지토리에 구축된 `.ontology/` 명세를 활용하여, 기억상실증 상태의 에이전트가 요구사항을 10초 만에 분석하고 안전하게 변경을 수행하기 위한 가이드입니다.

---

## 1. 워크플로우 4단계

```
[1. 요구사항 인입]
       ↓
[2. onto trace <keyword> 실행] ──> 도메인 객체, 불변식 가드(Preconditions), 수정 파일 목록 즉시 확보
       ↓
[3. TDD 사이클 실행] ────────────> Preconditions를 테스트의 Given으로 설정하여 기능 개발
       ↓
[4. onto lint 실행] ─────────────> 코드 바인딩 경로 및 심볼 불일치(Drift) 0건 검증
```

---

## 2. 세부 지침

### Step 1: 컨텍스트 역추적 (`onto trace`)
사용자로부터 기능 추가/수정 요구사항이 들어오면, 전체 소스 트리를 탐색하기 전에 가장 먼저 `onto trace`를 실행합니다.

```bash
onto trace <keyword>
# 예: onto trace attendance
# 예: onto trace grading
```

- 추출되는 정보:
  1. **관련 Objects**: 모델 속성과 PK
  2. **관련 Actions**: 상태 전이 로직 및 **Preconditions(절대 깨뜨리면 안 되는 비즈니스 불변식)**
  3. **Direct Code Touchpoints**: 수정 대상 백엔드/프론트엔드/모바일 파일들의 고유 목록

### Step 2: 불변식 기반 TDD 테스트 작성
- 온톨로지의 `preconditions` 목록은 반드시 테스트 케이스(Given - When - Then)로 구현되어야 합니다.
- 예: `target.status != 'CANCELLED'` 불변식이 있다면, 취소된 세션에 출석 기록 시도 시 400 Bad Request 또는 예외가 발생하는지 검증하는 테스트를 먼저 작성합니다.

### Step 3: 지정된 파일만 안전하게 수정
- `Direct Code Touchpoints`에 명시된 파일 이외의 엉뚱한 레이어를 임의로 수정하지 않습니다.
- 백엔드 서비스 계층과 프론트엔드 피처 컴포넌트 간의 계약을 준수합니다.

### Step 4: 정적 검증 (`onto lint`)
수정이 완료된 후, 온톨로지와 코드 간의 어긋남이 없는지 최종 검증합니다.

```bash
onto lint
```
- 모든 검증이 통과(`0 violations`)되어야 작업을 완료할 수 있습니다.

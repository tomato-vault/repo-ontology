# repo-ontology (onto)

> **코드 레포지토리 전용 팔란티어급 실행형 온톨로지 템플릿 & CLI**  
> "기억상실증 에이전트에게 10초 만에 도메인 불변식과 코드 지도를 복원해준다."

---

## 1. 개요

`repo-ontology`는 엔터프라이즈 데이터 운영 체계인 **팔란티어(Palantir Foundry / AIP)**의 온톨로지 철학을 코드베이스 레포지토리에 이식한 시스템입니다.

현대 AI 에이전트(Claude Code, Antigravity, Cursor 등) 기반 개발에서 가장 큰 병목은 **"에이전트의 세션 초기화(기억상실증)"**와 **"도메인 비즈니스 불변식(Invariants)의 누락"**입니다. 
- 수기 마크다운 명세(`docs/features/`)는 코드가 수정되면 drift(어긋남)가 발생합니다.
- 데이터베이스 ERD는 명사(테이블 형태)만 보여줄 뿐, 시스템에서 허용되는 상태 변경(동사, Action)과 권한을 통제하지 못합니다.

`repo-ontology`는 프로젝트 루트에 기계 가독형 `.ontology/` 명세를 구축하고, 정적 검증(`onto lint`)과 요구사항 초고속 역색인(`onto trace`)을 통해 문서와 코드의 정합성을 100%로 유지합니다.

---

## 2. 4대 프리미티브 (Palantir Primitives)

| 프리미티브 | 파일 위치 | 역할 및 설명 |
|:---|:---|:---|
| **Objects** (명사) | `.ontology/objects/*.yml` | 도메인 엔티티, 속성, Primary Key, 실제 소스코드 Model/Schema 바인딩 |
| **Links** (관계) | `.ontology/links/*.yml` | 엔티티 간 연관 관계, 카디널리티(1:1, 1:N, N:M), 외래키 매핑 |
| **Actions** (동사) | `.ontology/actions/*.yml` | 상태를 변경하는 **원자적 트랜잭션**, 실행 전 불변식(`preconditions`), 부수효과, 서비스 코드 바인딩 |
| **Functions** (계산) | `.ontology/functions/*.yml` | 상태 변경 없는 순수 계산 로직 및 파생 속성 도출, AIP LLM 체인 |

---

## 3. 핵심 명령어 (CLI)

```bash
# 1. 새 프로젝트에 .ontology 스켈레톤 안착
onto init [target-path]

# 2. 온톨로지 무결성 및 코드 바인딩 정적 검증
onto lint [target-path]

# 3. 요구사항 인입 시 관련 도메인/코드 즉시 역추적
onto trace <query> [target-path]
# 예: onto trace attendance

# 4. 온톨로지 등록 현황 요약
onto info [target-path]

# 5. 새 객체/액션 스켈레톤 생성
onto scaffold object <name>
onto scaffold action <name>
```

---

## 4. 디렉터리 레이아웃 표준안

```text
<project-root>/
├── .ontology/
│   ├── config.yml              # 프로젝트 메타데이터 및 스택 설정
│   ├── objects/                # 도메인 엔티티 (User, Course, Session)
│   ├── links/                  # 엔티티 간 관계도
│   ├── actions/                # 상태 전이 액션 (GradeSubmission, RecordAttendance)
│   ├── functions/              # 순수 계산 및 도출 함수 (CalculateAttendanceRate)
│   └── rules/                  # 전역 비즈니스 불변식
├── docs/                       # 기존 4대 운영 대장 (adr, tech-debt, watchlist)
└── backend/ frontend/ mobile/  # 실제 소스 코드
```

---

## 5. 설치 방법

```bash
# 로컬 개발 환경 설치
cd ~/Desktop/Code/repo-ontology
uv pip install -e .

# 또는 전역 설치
pip install -e ~/Desktop/Code/repo-ontology
```

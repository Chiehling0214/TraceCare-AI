# TraceCare AI — Sprint 0 UI Reference

## 1. Purpose

This document defines the user-interface scope and information architecture for **Sprint 0** of TraceCare AI.

The Sprint 0 UI is a competition prototype used to demonstrate:

- synthetic patient data
- deterministic laboratory trend analysis
- traceable clinical events
- evidence display
- event acknowledgement and resolution
- simulated device state

This document does **not** define a production medical interface.

---

## 2. Safety and Scope

### 2.1 Required Safety Notice

The application must display a visible notice:

> This project is a competition prototype and is not a medical device.  
> It must not be used for diagnosis or treatment decisions.  
> All included patient data is synthetic.

The notice should appear:

- on the patient overview page
- on the patient detail page
- in the README

### 2.2 Sprint 0 Scope

The UI must support:

- viewing synthetic patients
- viewing Creatinine laboratory history
- viewing deterministic rule results
- viewing clinical events and evidence
- acknowledging an event
- resolving an event
- viewing simulated device state
- manually running prototype analysis

### 2.3 Out of Scope

Do not implement the following in Sprint 0:

- login or role-based access control
- real patient data
- document upload
- PDF parsing
- FHIR import
- local LLM output
- RAG chat
- vector search
- graphical clinical evidence graph
- medical diagnosis
- treatment recommendations
- real ESP32 communication
- ECG or PPG visualization
- mobile-first layout

---

## 3. Global UI Requirements

### 3.1 Language

- Primary interface language: **Traditional Chinese**
- Technical identifiers such as `RAPID_INCREASE`, `OPEN`, or `ACKNOWLEDGED` may remain in English
- All visible labels should be understandable without reading source code

### 3.2 Visual Style

Use a clean, restrained hospital-dashboard style.

Recommended characteristics:

- light background
- dark navy or charcoal text
- clear card hierarchy
- moderate spacing
- minimal animation
- no decorative gradients that reduce readability
- no flashing effects in Sprint 0
- status colors must always be accompanied by text

### 3.3 Status Colors

| Status | Suggested Color | Required Text Label |
|---|---|---|
| NORMAL | Green | 正常 |
| REVIEW_REQUIRED | Amber / Yellow | 待確認 |
| HIGH_RISK | Red | 高風險 |
| ACKNOWLEDGED | Amber / Orange | 已確認未結案 |
| DEFERRED | Amber / Orange | 已延後 |
| RESOLVED | Gray / Green | 已處理／結案 |

Color alone must not be the only indicator.

### 3.4 Layout

- Desktop-first
- Minimum supported width: approximately 1024 px
- Main content centered with a reasonable maximum width
- Header remains consistent across pages
- Tables should remain readable without excessive horizontal scrolling

### 3.5 Loading, Empty, and Error States

Every data-dependent section must support:

- loading state
- empty state
- error state

Examples:

- `正在載入病人資料…`
- `目前沒有檢驗資料。`
- `目前沒有臨床事件。`
- `資料載入失敗，請稍後再試。`

Do not leave blank areas when data is missing.

---

## 4. Application Navigation

Sprint 0 requires two primary pages:

1. Patient Overview Page
2. Patient Detail Page

Recommended routes:

```text
/
/patients/:patientId
```

Optional redirect:

```text
/patients → /
```

---

## 5. Global Header

The global header should contain:

- application name: `TraceCare AI`
- subtitle: `可追溯臨床證據與實體警示決策支援系統`
- badge: `Synthetic Data`
- prototype safety notice or link to the notice
- optional navigation link back to patient overview

Recommended compact header structure:

```text
TraceCare AI
可追溯臨床證據與實體警示決策支援系統
[Synthetic Data] [Competition Prototype]
```

---

## 6. Patient Overview Page

### 6.1 Page Goal

Allow users to quickly identify which synthetic patient requires attention and open the patient detail page.

### 6.2 Required Sections

The page should contain:

1. Page title and prototype notice
2. Global simulated device state card
3. Run Analysis control
4. Summary statistics
5. Patient table

---

### 6.3 Page Header

Display:

- title: `病人總覽`
- description: `依目前風險狀態與未處理事件排序`
- button: `執行原型分析`

The analysis button should:

- call `POST /api/prototype/run-analysis`
- display a loading state while running
- prevent repeated clicks during execution
- refresh patient and device-state data after completion
- display a success or failure message

Suggested messages:

- success: `原型分析已完成。`
- failure: `分析執行失敗，請檢查後端服務。`

---

### 6.4 Summary Cards

Show compact cards for:

- total synthetic patients
- patients requiring review
- open events
- current device state

Example:

| Card | Example Value |
|---|---:|
| 合成病人 | 3 |
| 待確認病人 | 1 |
| 未處理事件 | 1 |
| 設備狀態 | WARNING |

These values must come from API data when possible.

---

### 6.5 Device State Card

Display:

- State
- LED
- Buzzer
- Connection

Example:

```text
Device State
State: WARNING
LED: Yellow Blinking
Buzzer: Short Beep
Connection: SIMULATED
```

Traditional Chinese labels are preferred:

```text
模擬設備狀態
狀態：待確認
LED：黃燈閃爍
蜂鳴器：短音提示
連線：模擬模式
```

The card must clearly show that no real hardware is connected.

---

### 6.6 Patient Table

Required columns:

| Column | Description |
|---|---|
| 病人代碼 | Synthetic patient identifier |
| 顯示名稱 | Synthetic display name |
| 風險狀態 | NORMAL / REVIEW_REQUIRED / HIGH_RISK |
| 未處理事件 | Count of OPEN or ACKNOWLEDGED events |
| 最新檢驗時間 | Latest laboratory observation time |
| 操作 | Link or button to detail page |

Recommended action label:

```text
查看詳情
```

### 6.7 Sorting

Patients must be sorted by:

1. `HIGH_RISK`
2. `REVIEW_REQUIRED`
3. `NORMAL`

Within the same severity, sort by latest event or laboratory time descending.

### 6.8 Patient Row Behavior

A patient row may be clickable, but there must still be a visible action control.

The risk badge should display both color and text.

Example:

```text
P001 | Synthetic Patient A | 待確認 | 1 | 2026/06/21 08:00 | 查看詳情
```

---

## 7. Patient Detail Page

### 7.1 Page Goal

Allow users to inspect a patient's laboratory history, event reason, source evidence, and event lifecycle.

### 7.2 Required Sections

The page must contain:

1. Back navigation
2. Patient summary
3. Current risk state
4. Creatinine laboratory history
5. Clinical event list
6. Event evidence detail
7. Event action controls
8. Simulated device state
9. Safety notice

---

### 7.3 Back Navigation

Display a clear link:

```text
← 返回病人總覽
```

---

### 7.4 Patient Summary Card

Display:

- patient code
- synthetic display name
- latest laboratory time
- current risk state
- number of unresolved events

Example:

```text
病人代碼：P001
顯示名稱：Synthetic Patient A
目前狀態：待確認
未處理事件：1
最新檢驗：2026/06/21 08:00
```

The UI must mark the patient as synthetic.

---

### 7.5 Creatinine History Section

Sprint 0 uses a table rather than a chart.

Required columns:

| Column | Description |
|---|---|
| 檢驗時間 | `observed_at` |
| 檢驗項目 | Creatinine |
| 數值 | Numeric value |
| 單位 | mg/dL |
| 參考區間 | reference_min – reference_max |
| 資料來源 | source_document |

Recommended value presentation:

```text
0.8 mg/dL
Reference: 0.6–1.2 mg/dL
```

Sort oldest to newest so the time sequence is easy to understand.

---

## 8. Clinical Event List

### 8.1 Event Card Required Fields

Each event card must display:

- severity
- status
- event type
- title
- description
- Rule ID
- created time
- acknowledged time, when available
- resolved time, when available

Example:

```text
待確認 | OPEN
檢驗值快速變化
Rule ID: RAPID_INCREASE

Creatinine changed from 0.8 mg/dL to 1.3 mg/dL within 24 hours.
Prototype rule triggered. Human review is required.
```

### 8.2 Prototype Rule Badge

Every rule-based event must display:

```text
Prototype Rule
```

This prevents the rule from being mistaken for a validated clinical standard.

### 8.3 Status Labels

| API Status | UI Label |
|---|---|
| OPEN | 待處理 |
| ACKNOWLEDGED | 已確認未結案 |
| DEFERRED | 已延後 |
| RESOLVED | 已處理／結案 |

---

## 9. Evidence Detail

### 9.1 Goal

Show exactly which laboratory records support the event.

### 9.2 Required Evidence Fields

Display:

- relation type
- test name
- value
- unit
- observed time
- source document

For `RAPID_INCREASE`, show at least:

```text
PREVIOUS_VALUE
Creatinine: 0.8 mg/dL
Observed at: 2026/06/20 08:00
Source: synthetic_lab_report_20260620.csv

CURRENT_VALUE
Creatinine: 1.3 mg/dL
Observed at: 2026/06/21 08:00
Source: synthetic_lab_report_20260621.csv
```

### 9.3 Evidence Presentation

Evidence may be shown as:

- stacked evidence cards
- a two-column before/after comparison
- a compact table

Recommended Sprint 0 presentation:

| Previous Value | Current Value |
|---|---|
| 0.8 mg/dL | 1.3 mg/dL |
| 2026/06/20 08:00 | 2026/06/21 08:00 |
| synthetic_lab_report_20260620.csv | synthetic_lab_report_20260621.csv |

Do not implement a graphical evidence graph in Sprint 0.

---

## 10. Event Actions

### 10.1 Acknowledge Action

Show the acknowledge button only when event status is `OPEN`.

Button label:

```text
確認事件
```

On click:

- ask for confirmation or show clear button intent
- call `POST /api/events/{event_id}/acknowledge`
- disable the button while loading
- refresh event and device-state data
- show success or error feedback

Success message:

```text
事件已確認，仍需後續處理。
```

### 10.2 Resolve Action

Show the resolve button when event status is:

- `OPEN`, if backend allows direct resolution
- `ACKNOWLEDGED`

Recommended Sprint 0 flow:

- acknowledge first
- resolve second

Button label:

```text
標示為已處理
```

Success message:

```text
事件已結案。
```

### 10.3 Button State Rules

| Event Status | Confirm Button | Resolve Button |
|---|---|---|
| OPEN | Enabled | Disabled or hidden |
| ACKNOWLEDGED | Hidden or disabled | Enabled |
| RESOLVED | Hidden | Hidden |

Do not leave clickable buttons after an event is resolved.

---

## 11. Simulated Device State

### 11.1 Required Fields

Display:

- state
- LED output
- buzzer output
- connection mode

### 11.2 State Mapping

| Event Condition | Device State | LED | Buzzer |
|---|---|---|---|
| No open event | NORMAL | Green solid | Off |
| Open REVIEW_REQUIRED event | WARNING | Yellow blinking | Short beep |
| Open HIGH_RISK event | CRITICAL | Red blinking | Intermittent |
| Acknowledged but unresolved event | ACKNOWLEDGED | Yellow solid | Off |

### 11.3 Visual Treatment

The simulated device should look like a status panel, not like a real hardware control screen.

It must display:

```text
Connection: SIMULATED
```

Do not add fake connection controls.

---

## 12. Notifications and Feedback

Use a simple toast, inline alert, or status message for:

- analysis success
- analysis failure
- event acknowledgement success
- event acknowledgement failure
- event resolution success
- event resolution failure

Messages must disappear only after enough time to be read, or be manually dismissible.

Do not use browser `alert()` for normal workflow if a simple UI message component can be implemented.

---

## 13. Accessibility and Readability

Required:

- buttons have visible focus styles
- all buttons use descriptive labels
- tables use semantic headers
- status is not represented by color alone
- text contrast is sufficient
- loading states are announced visually
- disabled buttons look disabled
- timestamps use one consistent format

Recommended timestamp format:

```text
YYYY/MM/DD HH:mm
```

---

## 14. Responsive Behavior

Sprint 0 is desktop-first, but the interface should not completely break on smaller screens.

At narrower widths:

- summary cards may wrap
- tables may use horizontal scrolling
- patient detail sections may stack vertically
- action buttons may wrap onto separate lines

Do not spend significant Sprint 0 time on mobile-specific optimization.

---

## 15. Recommended Component Structure

The exact implementation may vary, but a reasonable React structure is:

```text
src/
├─ api/
│  ├─ client.ts
│  ├─ patients.ts
│  ├─ events.ts
│  └─ analysis.ts
├─ components/
│  ├─ AppHeader.tsx
│  ├─ PrototypeNotice.tsx
│  ├─ RiskBadge.tsx
│  ├─ EventStatusBadge.tsx
│  ├─ DeviceStateCard.tsx
│  ├─ PatientTable.tsx
│  ├─ LabResultsTable.tsx
│  ├─ ClinicalEventCard.tsx
│  ├─ EvidenceComparison.tsx
│  ├─ LoadingState.tsx
│  ├─ EmptyState.tsx
│  └─ ErrorState.tsx
├─ pages/
│  ├─ PatientOverviewPage.tsx
│  └─ PatientDetailPage.tsx
├─ types/
│  ├─ patient.ts
│  ├─ lab.ts
│  ├─ event.ts
│  └─ device.ts
└─ App.tsx
```

Avoid creating a component for every small text element.

---

## 16. API Integration Expectations

The UI should use the endpoints defined in `docs/API_SPEC.md`.

At minimum:

```text
GET  /api/patients
GET  /api/patients/{patient_id}
GET  /api/patients/{patient_id}/labs
GET  /api/patients/{patient_id}/events
GET  /api/events/{event_id}
POST /api/events/{event_id}/acknowledge
POST /api/events/{event_id}/resolve
POST /api/prototype/run-analysis
GET  /api/device-state
```

Do not hard-code event results in React.

Synthetic seed values may be known in advance, but all displayed data must come from backend responses.

---

## 17. Reference Images

Optional reference images may be stored in:

```text
docs/reference/
├─ architecture.png
├─ evidence-graph.png
└─ event-lifecycle.png
```

These images are used only to understand:

- information hierarchy
- event relationships
- state transitions
- overall visual tone

Sprint 0 does not need to reproduce these figures exactly.

The implementation scope in `docs/SPRINT_00.md` takes precedence over visual references.

---

## 18. UI Acceptance Criteria

Sprint 0 UI is accepted when all conditions below are met.

### 18.1 Patient Overview

- Patient overview loads from backend data.
- P001, P002, and P003 are visible.
- Patients are sorted by current severity.
- Current device state is visible.
- Run Analysis triggers backend analysis.
- User can open a patient detail page.

### 18.2 Patient Detail

- Patient information is displayed.
- Creatinine history is displayed in chronological order.
- Event Rule ID and status are visible.
- Previous and current evidence records are visible.
- Source document names are visible.
- Acknowledge action updates the UI and backend.
- Resolve action updates the UI and backend.
- Device state updates after event actions.

### 18.3 Safety

- Synthetic-data badge is visible.
- Prototype disclaimer is visible.
- Prototype rule is clearly labeled.
- No diagnostic or treatment language is generated.
- No external AI service is called.

### 18.4 Quality

- Loading, empty, and error states exist.
- Buttons cannot be repeatedly submitted while loading.
- No primary workflow uses fake buttons.
- No primary displayed data is hard-coded in the frontend.
- The UI remains usable at desktop widths.

---

## 19. Known Limitations

Sprint 0 intentionally does not include:

- a production clinical design review
- formal usability testing with hospital staff
- a graphical evidence graph
- laboratory trend charts
- authentication
- permissions
- local LLM output
- document ingestion
- real hardware integration

These limitations should be documented rather than hidden.

---

# 20. Sprint 2 UI Addendum

Sprint 2 extends the existing UI without removing Sprint 0 or Sprint 1 workflows.

## 20.1 Patient Overview

The `執行原型分析` button runs:

```text
POST /api/prototype/run-analysis
POST /api/prototype/run-contradiction-analysis
POST /api/prototype/run-risk-evaluation
```

The patient table displays additive risk context:

- risk reason codes
- unresolved event count
- oldest unresolved event time
- latest lab time

Patients are ordered by deterministic risk priority, unresolved event age, unresolved event count, then latest lab time.

## 20.2 Event Cards

Event cards show Sprint 2 lifecycle metadata:

- deferred-until time
- escalation time
- escalation reason
- action history

Allowed buttons:

| Event Status | Confirm | Defer | Resolve |
|---|---|---|---|
| OPEN | enabled | enabled | hidden |
| DEFERRED | enabled | enabled | enabled |
| ACKNOWLEDGED | hidden | enabled | enabled |
| RESOLVED | hidden | hidden | hidden |

Action history is loaded from backend event detail and must not be hard-coded in React.

## 20.3 Safety

Risk reason text must stay in prototype workflow language. The UI must not display diagnosis, treatment advice, real alert-policy language, or AI-generated risk claims.

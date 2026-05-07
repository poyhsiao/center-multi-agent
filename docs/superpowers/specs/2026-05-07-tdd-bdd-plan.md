# TDD + BDD 混合驅動開發規劃

> **版本：** v0.1
> **日期：** 2026-05-07
> **狀態：** 已確認

---

## 1. 測試策略架構

### 測試金字塔

```
        ▲ BDD E2E (Playwright)           ← 4 個 Feature 覆蓋
       ╱  ╲  ╱  ╲
      ╱ BDD ╲╱ BDD
     ╱ Integration ╲ ───────────────────  pytest (mock PostgreSQL/Redis)
    ╱   Tests      ╲
   ╱───────────────╲ ───────────────────  pytest (pure unit, no mocks)
   │   Unit Tests  │
   └───────────────┘
```

### 測試類型對應

| 類型 | 框架 | 目標 |
|------|------|------|
| **Unit Tests** | pytest | Pure functions, Token Service, 無外部依賴 |
| **Integration Tests** | pytest + mock | Auth Service, Tenant Service, 需要 mock DB/Redis |
| **BDD Acceptance Tests** | Behave + Playwright | 4 大核心流程行為驗收 |
| **E2E Tests** | Playwright | 真實環境完整流程 |

---

## 2. TDD 開發順序（Phase 1-4）

### Phase 1：Token Service（TDD）
- **負責人**：Auth Service
- **範圍**：
  - RS256 JWT 簽發與驗證
  - Refresh Token 旋轉（Sliding Window）
  - Redis 黑名單（RT 撤銷）
  - 設備指紋綁定 claims

### Phase 2：Auth Service（TDD）
- **負責人**：Auth Service
- **範圍**：
  - 密碼驗證（bcrypt）
  - TOTP 驗證（可選）
  - 登入整合 Token Service

### Phase 3：Tenant Service（TDD）
- **負責人**：Tenant Service
- **範圍**：
  - Org/Dept/User CRUD
  - RBAC Engine

### Phase 4：LLM Gateway + Knowledge Service（TDD）
- **負責人**：Gateway / Knowledge Service
- **範圍**：
  - Model Router + Failover
  - RAG Pipeline + 審核流程

---

## 3. BDD 驗收順序

### Feature A：登入流程
- 成功登入（密碼）
- 登入失敗（錯誤密碼）
- Token 刷新流程
- 設備指紋驗證
- Refresh Token 旋轉驗證

### Feature B：Agent 操作完整流程
- 正常操作流程
- 連線失敗佇列機制
- 離線 RAG 查詢

### Feature C：知識貢獻流程
- 提交知識
- 審核通知（SSE）
- Admin 核准/拒絕
- 知識發布

### Feature D：Client 同步流程
- MCP/Skills 差異同步
- 本地設定更新

---

## 4. 技術棧

### 後端
- **語言**：Python FastAPI
- **測試**：pytest
- **BDD**：Behave

### 前端（Client Agent）
- **框架**：Tauri
- **E2E**：Playwright

### 資料庫
- **主要**：PostgreSQL + RLS
- **向量**：PGVector
- **快取**：Redis

---

## 5. 輸出產物

| 階段 | 文件 |
|------|------|
| 設計 | `docs/superpowers/specs/YYYY-MM-DD-tdd-bdd-plan.md` |
| 實作計畫 | 將由 `writing-plans` skill 生成 |
| BDD Features | `features/A-login.feature`, `B-agent-operation.feature`, etc. |
| TDD Tests | `tests/unit/`, `tests/integration/` |

---

*狀態：設計確認完成，等待實作計畫生成*

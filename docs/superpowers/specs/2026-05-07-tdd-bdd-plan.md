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

#### 1.1 JWT 規格

| Token 類型 | 演算法 | 簽發者 | 過期時間 |
|------------|--------|--------|----------|
| Access Token (AT) | RS256 | `auth-service` | 15 min |
| Refresh Token (RT) | RS256 | `auth-service` | 7 days |

**Access Token Claims：**
```json
{
  "sub": "<user_id>",
  "tid": "<tenant_id>",
  "did": "<device_id>",
  "fp": "<fingerprint_hash>",
  "type": "access",
  "iat": 1715145600,
  "exp": 1715146500
}
```

**Refresh Token Claims：**
```json
{
  "sub": "<user_id>",
  "tid": "<tenant_id>",
  "did": "<device_id>",
  "fp": "<fingerprint_hash>",
  "jti": "<unique_token_id>",
  "type": "refresh",
  "iat": 1715145600,
  "exp": 1715750400
}
```

#### 1.2 Redis Schema

```
# RT 存儲（Sliding Window）
rt:<user_id>:<device_id> -> Hash
  - jti:<jti> := <rt_payload_json>
  - current := <current_jti>
  - created_at := <timestamp>

# RT 撤銷黑名單（用於登出/強制撤銷）
blacklist:rt:<jti> := 1
  - TTL = RT 剩餘過期時間

# 設備註冊
device:<user_id>:<device_id> -> Hash
  - fingerprint := <hash>
  - trusted := <boolean>
  - last_active := <timestamp>
```

#### 1.3 設備指紋

指紋組成因素：
- `User-Agent` 雜湊
- 客戶端版本
- 客戶端類型（web/desktop/mobile）

指紋格式：
```
fp = SHA256(agent_hash + client_version + client_type + salt)
```

#### 1.4 Sliding Window RT 旋轉

```
流程：
1. 收到 RT，驗證簽名與Expiry
2. 檢查 fingerprint 是否匹配
3. 檢查 jti 是否在黑名單 → 否 → 繼續
4. 產生新的 RT（new_jti），更新 Redis current
5. 舊 RT 加入黑名單（TTL = 舊 RT 剩餘時間）
6. 回傳新 AT + 新 RT
```

#### 1.5 TDD 測試案例

**Unit Tests：**
- `test_jwt_sign_and_verify()` - 簽發與驗證
- `test_jwt_claims_extraction()` - Claims 解析
- `test_fingerprint_generation()` - 指紋生成一致性
- `test_token_expiry_validation()` - 過期檢查

**Integration Tests：**
- `test_rt_rotation_flow()` - 完整旋轉流程
- `test_fingerprint_mismatch_reject()` - 指紋不符拒絕
- `test_blacklist_check()` - 黑名單檢查
- `test_concurrent_refresh_handling()` - 並發刷新防範

#### Phase 2：Auth Service（TDD）
- **負責人**：Auth Service
- **範圍**：
  - 密碼驗證（bcrypt）
  - TOTP 驗證（可選）
  - 登入整合 Token Service

##### 2.1 密碼雜湊

| 項目 | 規格 |
|------|------|
| 演算法 | bcrypt |
| 工作因子 | 12（cost = 2^12 = 4096 迭代） |
| 鹽值 | 每密碼隨機生成 22 字元 |
| 雜湊長度 | 60 字元 |

密碼驗證流程：
```
1. 收到明文密碼
2. 取出 stored_hash 中的 salt
3. bcrypt.verify(plain, stored_hash)
4. 回傳布林結果
```

##### 2.2 TOTP（可選）

| 項目 | 規格 |
|------|------|
| 演算法 | SHA1（預設）/ SHA256 / SHA512 |
| 一次性密碼長度 | 6 位數 |
| 時間步進 | 30 秒 |
| 容許時間窗口 | ±1 步進（60 秒） |
| 金鑰格式 | Base32 |
| 金鑰儲存 | 加密後存入 DB（金鑰以 KDF 保護） |

##### 2.3 登入流程

```
┌─────────────────────────────────────────────────────────┐
│  登入流程                                                  │
│                                                           │
│  1. POST /auth/login                                     │
│     - 输入: email, password, device_fingerprint           │
│  2. 驗證密碼（bcrypt）                                     │
│  3. 若啟用 TOTP → 驗證 TOTP code                          │
│  4. 產生 AT + RT（調用 Token Service）                     │
│  5. 註冊設備指紋（更新 Redis）                            │
│  6. 回傳 { access_token, refresh_token, expires_in }     │
└─────────────────────────────────────────────────────────┘
```

##### 2.4 測試案例

**Unit Tests：**
- `test_password_hash_verify()` - bcrypt 雜湊驗證
- `test_password_hash_uniqueness()` - 不同鹽值產生不同雜湊
- `test_totp_code_generation()` - TOTP 產生一致性
- `test_totp_window_validation()` - ±1 步進容許

**Integration Tests：**
- `test_login_success_flow()` - 成功登入
- `test_login_wrong_password()` - 錯誤密碼拒絕
- `test_login_totp_required()` - 需要 TOTP 驗證
- `test_login_totp_invalid()` - 無效 TOTP 拒絕

#### Phase 3：Tenant Service（TDD）
- **負責人**：Tenant Service
- **範圍**：
  - Org/Dept/User CRUD
  - RBAC Engine

##### 3.1 資料模型

**Organization：**
```json
{
  "id": "uuid",
  "name": "string",
  "slug": "string",
  "plan": "free|pro|enterprise",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

**Department：**
```json
{
  "id": "uuid",
  "org_id": "uuid",
  "name": "string",
  "parent_id": "uuid|null",
  "created_at": "timestamp"
}
```

**User：**
```json
{
  "id": "uuid",
  "org_id": "uuid",
  "dept_id": "uuid|null",
  "email": "string",
  "password_hash": "string",
  "role": "admin|manager|member",
  "totp_secret": "string|null",
  "totp_enabled": "boolean",
  "status": "active|suspended|inactive",
  "created_at": "timestamp"
}
```

##### 3.2 RBAC Engine

**角色權限矩陣：**

| 動作 | Admin | Manager | Member |
|------|-------|---------|--------|
| 管理組織設定 | ✓ | ✗ | ✗ |
| 管理部門 | ✓ | ✓ | ✗ |
| 管理成員 | ✓ | ✓ | ✗ |
| 邀請成員 | ✓ | ✓ | ✗ |
| 提交知識 | ✓ | ✓ | ✓ |
| 審核知識 | ✓ | ✓ | ✗ |
| 發布知識 | ✓ | ✗ | ✗ |

**權限檢查流程：**
```
1. 取得 user.role
2. 查詢 action_resource 的權限矩陣
3. 若為管理員角色 → 直接放行
4. 否則查詢具體權限 → 回傳布林
```

##### 3.3 PostgreSQL Schema

```sql
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL,
  plan VARCHAR(20) DEFAULT 'free',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE departments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  parent_id UUID REFERENCES departments(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  dept_id UUID REFERENCES departments(id) ON DELETE SET NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'member',
  totp_secret VARCHAR(255),
  totp_enabled BOOLEAN DEFAULT FALSE,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

##### 3.4 測試案例

**Unit Tests：**
- `test_org_crud_operations()` - Org 增刪查改
- `test_dept_tree_operations()` - 部門樹狀結構
- `test_user_crud_operations()` - User 增刪查改
- `test_rbac_permission_check()` - 權限檢查邏輯

**Integration Tests：**
- `test_create_user_with_org()` - 創建用戶關聯組織
- `test_dept_hierarchy_delete()` - 刪除部門保持階層
- `test_rbac_admin_bypass()` - Admin 繞過權限檢查
- `test_rbac_member_restricted()` - Member 角色受限

#### Phase 4：LLM Gateway + Knowledge Service（TDD）
- **負責人**：Gateway / Knowledge Service
- **範圍**：
  - Model Router + Failover
  - RAG Pipeline + 審核流程

##### 4.1 Model Router

**支援模型：**

| 模型 | Provider | 用途 | 成本等級 |
|------|----------|------|----------|
| GPT-4o | OpenAI | 複雜推理 | 高 |
| GPT-4o-mini | OpenAI | 一般任務 | 中 |
| Claude 3.5 Sonnet | Anthropic | 創意寫作 | 高 |
| Claude 3 Haiku | Anthropic | 快速任務 | 低 |
| Gemini 2.0 Flash | Google | 批量處理 | 低 |

**路由策略：**
```
1. 任務分類：complex_reasoning | general | creative | batch
2. 根據任務類型選擇最低成本候選
3. 若 primary 模型失敗 → failover 到 backup
4. 記錄 cost 與 latency
```

**Failover 鏈：**
```
complex_reasoning: GPT-4o → Claude 3.5 Sonnet
general: GPT-4o-mini → Gemini 2.0 Flash
creative: Claude 3.5 Sonnet → GPT-4o
batch: Gemini 2.0 Flash → Claude 3 Haiku
```

##### 4.2 RAG Pipeline

```
┌─────────────────────────────────────────────────────────┐
│  RAG Pipeline                                           │
│                                                         │
│  1. Query Input                                         │
│  2. Embedding（text-embedding-3-small）                │
│  3. Vector Search（PGVector）                            │
│  4. Context Assembly（top-k chunks）                    │
│  5. LLM Generation（with context）                      │
│  6. Response Output                                     │
└─────────────────────────────────────────────────────────┘
```

**PGVector Schema：**
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  knowledge_id UUID REFERENCES knowledge(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding vector(1536),
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

##### 4.3 審核流程

**知識狀態機：**
```
[draft] → [pending_review] → [approved] → [published]
                         ↘ [rejected] → [draft]
```

**SSE 通知事件：**
| 事件 | 內容 |
|------|------|
| `knowledge.submitted` | 新知識提交，等待審核 |
| `knowledge.approved` | 管理員核准 |
| `knowledge.rejected` | 管理員拒絕（含原因） |
| `knowledge.published` | 知識已發布 |

##### 4.4 測試案例

**Unit Tests：**
- `test_model_router_selection()` - 路由選擇邏輯
- `test_model_failover_chain()` - 備援鏈順序
- `test_embedding_generation()` - 向量生成一致性
- `test_knowledge_state_machine()` - 狀態轉換

**Integration Tests：**
- `test_rag_query_with_context()` - RAG 查詢流程
- `test_failover_on_model_error()` - 模型失敗備援
- `test_approval_workflow()` - 審核工作流
- `test_sse_notification_events()` - SSE 事件觸發

---

## 3. BDD 驗收順序

### Feature A：登入流程

```gherkin
# features/A-login.feature
Feature: 使用者登入流程

  Scenario: 成功登入（密碼正確）
    Given 使用者註冊於系統中，郵箱為 "user@example.com"，密碼為 "ValidPassword123"
    And 設備指紋為 "fp_abc123"
    When 使用者提交登入請求，郵箱為 "user@example.com"，密碼為 "ValidPassword123"
    Then 系統回傳 Access Token（過期時間 15 分鐘）
    And 系統回傳 Refresh Token（過期時間 7 天）
    And Redis 中存在設備註冊記錄

  Scenario: 登入失敗（密碼錯誤）
    Given 使用者註冊於系統中，郵箱為 "user@example.com"，密碼為 "CorrectPassword"
    When 使用者提交登入請求，郵箱為 "user@example.com"，密碼為 "WrongPassword"
    Then 系統回傳 401 錯誤
    And 錯誤訊息為 "Invalid credentials"

  Scenario: 帳號不存在
    Given 系統中不存在郵箱為 "nonexistent@example.com" 的使用者
    When 使用者提交登入請求，郵箱為 "nonexistent@example.com"，密碼為 "AnyPassword"
    Then 系統回傳 401 錯誤

  Scenario: Token 刷新成功
    Given 使用者已完成登入，持有有效的 Refresh Token
    When 使用者提交 Token 刷新請求，攜帶有效的 Refresh Token
    Then 系統回傳新的 Access Token
    And 系統回傳新的 Refresh Token（RT 旋轉）
    And 舊 Refresh Token 已加入黑名單

  Scenario: 設備指紋驗證失敗
    Given 使用者上次登入設備指紋為 "fp_original"
    When 使用者使用不同的設備指紋 "fp_different" 提交刷新請求
    Then 系統回傳 401 錯誤
    And 錯誤訊息為 "Device fingerprint mismatch"

  Scenario: Refresh Token 已被撤銷
    Given 使用者的 Refresh Token 已被撤銷（用戶登出）
    When 使用者提交 Token 刷新請求，攜帶已被撤銷的 Refresh Token
    Then 系統回傳 401 錯誤
    And 錯誤訊息為 "Token has been revoked"

  Scenario: 首次登入新設備需要指紋註冊
    Given 使用者從新設備嘗試登入
    When 使用者成功完成登入
    Then 系統創建新的設備指紋記錄
    And 設備標記為 trusted = false（可選升級）
```

### Feature B：Agent 操作完整流程

```gherkin
# features/B-agent-operation.feature
Feature: Client Agent 操作流程

  Scenario: 正常操作流程
    Given 使用者已登入系統，持有有效 Access Token
    And Agent 客戶端已初始化
    When 使用者發起 Agent 任務請求
    Then 任務進入處理佇列
    And 系統回傳任務 ID
    And 任務完成後通知用戶（可選 SSE）

  Scenario: 連線失敗佇列機制
    Given 使用者已登入系統，持有有效 Access Token
    And Agent 客戶端已初始化
    And 外部服務目前無法連線
    When 使用者發起 Agent 任務請求
    Then 任務進入重試佇列
    And 系統回傳任務 ID 與狀態 "queued"
    And 任務在服務恢復後自動處理
    And 完成後通知用戶

  Scenario: 離線 RAG 查詢
    Given 使用者已登入系統
    And 本地快取中存在相關知識
    And 網路連線中斷
    When 使用者發起 RAG 查詢請求
    Then 系統從本地快取返回知識
    And 標記結果為 "cached"

  Scenario: 多個任務並發處理
    Given 使用者已登入系統，持有有效 Access Token
    When 使用者同時發起多個 Agent 任務（3 個）
    Then 每個任務獲得獨立任務 ID
    And 任務並行處理
    And 所有任務完成後通知用戶

  Scenario: 任務超時處理
    Given 使用者已登入系統，持有有效 Access Token
    And 任務處理超時設定為 30 秒
    When 使用者發起需要超時的任務
    Then 系統回傳超時錯誤
    And 任務標記為 "timeout"
```

### Feature C：知識貢獻流程

```gherkin
# features/C-knowledge-contribution.feature
Feature: 知識貢獻與審核流程

  Scenario: 成員提交知識
    Given 使用者角色為 "member"
    And 使用者已登入系統
    When 使用者提交新知識，標題為 "新技術文章"，內容為 "文章內容..."
    Then 知識狀態為 "draft"
    And 系統回傳知識 ID

  Scenario: 成員提交知識進入審核
    Given 使用者角色為 "member"
    And 使用者已登入系統
    And 知識處於 "draft" 狀態
    When 使用者提交知識進入審核
    Then 知識狀態變更為 "pending_review"
    And Admin 收到審核通知（SSE 事件 `knowledge.submitted`）

  Scenario: Manager 審核知識（核准）
    Given 使用者角色為 "manager"
    And 有知識處於 "pending_review" 狀態
    When Manager 核准該知識
    Then 知識狀態變更為 "approved"
    And 提交者收到通知（SSE 事件 `knowledge.approved`）

  Scenario: Manager 審核知識（拒絕）
    Given 使用者角色為 "manager"
    And 有知識處於 "pending_review" 狀態
    When Manager 拒絕該知識，理由為 "內容需要補充"
    Then 知識狀態變更為 "rejected"
    And 提交者收到通知（SSE 事件 `knowledge.rejected`），包含拒絕原因

  Scenario: Admin 發布知識
    Given 使用者角色為 "admin"
    And 有知識處於 "approved" 狀態
    When Admin 發布該知識
    Then 知識狀態變更為 "published"
    And 知識進入 RAG 向量資料庫
    And 所有相關用戶收到通知（SSE 事件 `knowledge.published`）

  Scenario: 成員編輯自己草稿
    Given 使用者角色為 "member"
    And 使用者擁有一個 "draft" 狀態的知識
    When 使用者編輯該知識的內容
    Then 知識內容更新成功
    And 狀態保持為 "draft"

  Scenario: 成員無法刪除他人知識
    Given 使用者角色為 "member"
    And 系統中存在其他成員的知識
    When 使用者嘗試刪除該知識
    Then 系統回傳 403 錯誤
    And 知識未被刪除
```

### Feature D：Client 同步流程

```gherkin
# features/D-client-sync.feature
Feature: Client Agent 同步流程

  Scenario: MCP 技能差異同步
    Given Client Agent 已連線至 Server
    When Client 發起同步請求，查詢本地 MCP 版本為 "1.2.0"
    And Server 端的 MCP 版本為 "1.3.0"
    Then 系統回傳需要更新的技能清單
    And 差異內容下載至 Client

  Scenario: 無新版本時同步完成
    Given Client Agent 已連線至 Server
    When Client 發起同步請求，查詢本地 MCP 版本為 "1.3.0"
    And Server 端的 MCP 版本為 "1.3.0"
    Then 系統回傳 "no_update_required"

  Scenario: 本地設定更新
    Given 使用者修改了 Client 設定（如主題、語言）
    When Client 提交設定更新至 Server
    Then 設定儲存至 Server
    And 其他已登入的 Client 實例同步更新

  Scenario: 離線設定變更
    Given 使用者在離線狀態修改了 Client 設定
    When 網路恢復後 Client 重新連線
    Then Client 同步本地變更至 Server
    And Server 回傳衝突解決策略（如有）

  Scenario: 首次安裝同步
    Given 新 Client Agent 首次啟動
    When Client 發起首次同步請求
    Then 系統回傳完整配置
    And 技能定義、设定檔案全部同步
```

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

### 5.1 專案目錄結構

```
center-multi-agent/
├── backend/                          # FastAPI 後端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── config.py                 # 設定管理
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── auth.py           # 認證端點
│   │   │   │   ├── agent.py          # Agent 操作端點
│   │   │   │   ├── knowledge.py      # 知識管理端點
│   │   │   │   └── sync.py           # 同步端點
│   │   │   └── deps.py               # 依賴注入
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py           # JWT、bcrypt、TOTP
│   │   │   └── exceptions.py         # 自訂例外
│   │   ├── models/                   # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── organization.py
│   │   │   ├── department.py
│   │   │   └── knowledge.py
│   │   ├── schemas/                 # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── agent.py
│   │   │   └── knowledge.py
│   │   ├── services/                 # 商業邏輯
│   │   │   ├── __init__.py
│   │   │   ├── token_service.py      # Phase 1
│   │   │   ├── auth_service.py       # Phase 2
│   │   │   ├── tenant_service.py     # Phase 3
│   │   │   └── llm_gateway.py        # Phase 4
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── database.py           # SQLAlchemy 連線
│   │       └── redis.py              # Redis 客戶端
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── __init__.py
│   │   │   ├── test_token_service.py
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_tenant_service.py
│   │   │   └── test_llm_gateway.py
│   │   ├── integration/
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py           # pytest fixtures
│   │   │   ├── test_auth_flows.py
│   │   │   └── test_knowledge_flows.py
│   │   └── conftest.py
│   ├── features/                     # BDD Behave
│   │   ├── __init__.py
│   │   ├── A-login.feature
│   │   ├── B-agent-operation.feature
│   │   ├── C-knowledge-contribution.feature
│   │   ├── D-client-sync.feature
│   │   └── steps/                   # Step definitions
│   │       ├── __init__.py
│   │       ├── auth_steps.py
│   │       ├── agent_steps.py
│   │       └── knowledge_steps.py
│   ├── pyproject.toml
│   ├── poetry.lock
│   └── README.md
│
├── client/                           # Tauri 前端
│   ├── src/
│   │   ├── main.ts                  # 入口
│   │   ├── App.tsx                 # 主元件
│   │   ├── lib/
│   │   │   ├── api.ts              # API 客戶端
│   │   │   ├── auth.ts             # 認證邏輯
│   │   │   └── sync.ts            # 同步邏輯
│   │   ├── components/
│   │   │   └── ...
│   │   └── styles/
│   │       └── ...
│   ├── e2e/                         # Playwright E2E
│   │   ├── login.spec.ts
│   │   └── ...
│   ├── src-tauri/
│   │   ├── src/
│   │   │   └── main.rs
│   │   ├── Cargo.toml
│   │   └── tauri.conf.json
│   ├── package.json
│   └── playwright.config.ts
│
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-05-07-tdd-bdd-plan.md
│
└── README.md
```

### 5.2 系統架構圖

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Client (Tauri)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │
│  │   UI Layer  │  │  Auth Store │  │ Sync Engine │                   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                   │
└─────────┼────────────────┼────────────────┼─────────────────────────┘
          │                 │                │
          │    HTTPS + JWT  │   WebSocket    │
          ▼                 ▼                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         API Gateway (FastAPI)                        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      /api/v1/* Routes                          │ │
│  │  ┌─────────┐  ┌─────────┐  ┌────────────┐  ┌────────────────┐  │ │
│  │  │  Auth   │  │  Agent  │  │  Knowledge  │  │     Sync       │  │ │
│  │  │ Router  │  │ Router  │  │   Router    │  │    Router      │  │ │
│  │  └───┬─────┘  └────┬────┘  └──────┬─────┘  └───────┬────────┘  │ │
│  └──────┼─────────────┼──────────────┼───────────────┼────────────┘ │
│         │             │              │               │              │
└─────────┼─────────────┼──────────────┼───────────────┼──────────────┘
          │             │              │               │
          ▼             ▼              ▼               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Service Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │Token Service │  │Auth Service  │  │Tenant Svc    │  │LLM Gateway│ │
│  │ (Phase 1)    │  │ (Phase 2)    │  │ (Phase 3)    │  │ (Phase 4) │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘  └─────┬─────┘ │
│         │                 │                 │                │      │
└─────────┼─────────────────┼─────────────────┼────────────────┼──────┘
          │                 │                 │                │
          ▼                 ▼                 ▼                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │
│  │     Redis       │  │   PostgreSQL    │  │      PGVector       │   │
│  │  (RT/黑名單)     │  │  (User/Org)     │  │   (Knowledge Embed) │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.3 初始化步驟

**Phase 1 初始化流程：**

```bash
# 1. 建立專案結構
mkdir -p backend/app/{api/v1,core,models,schemas,services,db}
mkdir -p backend/tests/{unit,integration}
mkdir -p backend/features/steps
mkdir -p client/src/{lib,components,styles}
mkdir -p client/e2e

# 2. 後端依賴安裝
cd backend
poetry init --name center-multi-agent-backend
poetry add fastapi uvicorn[standard] sqlalchemy asyncpg
poetry add python-jose[cryptography] passlib[bcrypt] python-multipart
poetry add redis aioredis pydantic-settings
poetry add pytest pytest-asyncio httpx
poetry add behave playwright

# 3. 前端依賴安裝
cd client
npm create tauri-app@latest .
npm install @tauri-apps/api
npm install -D @playwright/test

# 4. 環境變數設定
cp backend/.env.example backend/.env
# 編輯 backend/.env 填入必要的環境變數
```

---

*狀態：設計確認完成，輸出產物已細化*
*下一步：使用 `writing-plans` skill 生成 Phase 1 實作計畫*

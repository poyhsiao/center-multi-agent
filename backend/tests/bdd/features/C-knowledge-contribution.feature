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
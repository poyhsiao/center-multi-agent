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
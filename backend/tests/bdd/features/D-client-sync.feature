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
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

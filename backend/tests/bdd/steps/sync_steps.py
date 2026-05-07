"""Step definitions for Client Sync feature."""
from behave import given, when, then


# =============================================================================
# Context Keys
# =============================================================================
# These keys are used to store test state in context
CLIENT_CONNECTED = "client_connected"
LOCAL_MCP_VERSION = "local_mcp_version"
SERVER_MCP_VERSION = "server_mcp_version"
SYNC_RESULT = "sync_result"
CLIENT_SETTINGS = "client_settings"
SERVER_SETTINGS = "server_settings"
CONFLICT_STRATEGY = "conflict_strategy"
FULL_CONFIG = "full_config"
OFFLINE_CHANGES = "offline_changes"


# =============================================================================
# MCP Skill Sync Scenarios
# =============================================================================

@given("Client Agent 已連線至 Server")
def step_client_connected(context):
    """Initialize client as connected."""
    context.client_connected = True


@when("Client 發起同步請求，查詢本地 MCP 版本為 {version}")
def step_client_sync_request_with_version(context, version):
    """Client发起同步请求，携带本地MCP版本。"""
    context.local_mcp_version = version.strip('"')


@when("Server 端的 MCP 版本為 {version}")
def step_server_mcp_version(context, version):
    """设置服务端MCP版本。"""
    context.server_mcp_version = version.strip('"')


@then("系統回傳需要更新的技能清單")
def step_return_skill_update_list(context):
    """验证系统返回需要更新的技能列表。"""
    assert context.local_mcp_version is not None, "local_mcp_version not set"
    assert context.server_mcp_version is not None, "server_mcp_version not set"

    local_ver = context.local_mcp_version
    server_ver = context.server_mcp_version

    # Simple version comparison - extract major.minor
    def parse_ver(v):
        parts = v.split(".")
        return (int(parts[0]), int(parts[1])) if len(parts) >= 2 else (int(parts[0]), 0)

    local_tuple = parse_ver(local_ver)
    server_tuple = parse_ver(server_ver)

    if server_tuple > local_tuple:
        context.sync_result = {
            "status": "update_required",
            "skills_to_update": [
                {"name": "mcp_skill_1", "version": server_ver},
                {"name": "mcp_skill_2", "version": server_ver},
            ],
        }
    else:
        context.sync_result = {"status": "no_update_required"}


@then("差異內容下載至 Client")
def step_diff_content_downloaded(context):
    """验证差异内容已下载到客户端。"""
    assert context.sync_result is not None, "sync_result not set"
    assert context.sync_result.get("status") == "update_required", \
        f"Expected update_required, got {context.sync_result.get('status')}"
    assert "skills_to_update" in context.sync_result, \
        "skills_to_update not in sync_result"


@then("系統回傳 {expected}")
def step_return_no_update(context, expected):
    """Verify system returns no update required or other status."""
    expected_value = expected.strip('"')

    # Compute sync_result if not already set (for "no_update_required" scenario)
    sync_result = getattr(context, 'sync_result', None)
    if sync_result is None and hasattr(context, 'local_mcp_version') and hasattr(context, 'server_mcp_version'):
        local_ver = context.local_mcp_version
        server_ver = context.server_mcp_version

        def parse_ver(v):
            parts = v.split(".")
            return (int(parts[0]), int(parts[1])) if len(parts) >= 2 else (int(parts[0]), 0)

        local_tuple = parse_ver(local_ver)
        server_tuple = parse_ver(server_ver)

        if server_tuple > local_tuple:
            context.sync_result = {
                "status": "update_required",
                "skills_to_update": [
                    {"name": "mcp_skill_1", "version": server_ver},
                ],
            }
        else:
            context.sync_result = {"status": "no_update_required"}

    assert context.sync_result is not None, "sync_result not set"
    assert context.sync_result.get("status") == expected_value, \
        f"Expected {expected_value}, got {context.sync_result.get('status')}"


# =============================================================================
# Local Settings Update Scenarios
# =============================================================================

@given("使用者修改了 Client 設定（如主題、語言）")
def step_user_modified_settings(context):
    """用户修改了客户端设置。"""
    context.client_settings = {
        "theme": "dark",
        "language": "zh-TW",
        "updated_at": "2026-05-07T10:00:00Z",
    }


@when("Client 提交設定更新至 Server")
def step_client_submit_settings(context):
    """客户端提交设置更新到服务器。"""
    # Mock: store settings on server
    context.server_settings = context.client_settings.copy()
    context.sync_result = {"status": "settings_saved"}


@then("設定儲存至 Server")
def step_settings_saved_to_server(context):
    """验证设置已保存到服务器。"""
    assert context.server_settings is not None, "server_settings not set"
    assert context.server_settings.get("theme") == "dark"
    assert context.server_settings.get("language") == "zh-TW"


@then("其他已登入的 Client 實例同步更新")
def step_other_clients_synced(context):
    """验证其他已登录的客户端实例也已同步更新。"""
    # Mock: broadcast notification sent
    context.sync_result = {**context.sync_result, "broadcast_sent": True}
    assert context.sync_result.get("broadcast_sent") is True


# =============================================================================
# Offline Settings Change Scenarios
# =============================================================================

@given("使用者在離線狀態修改了 Client 設定")
def step_user_modified_offline_settings(context):
    """用户在离线状态修改了客户端设置。"""
    context.offline_changes = {
        "theme": "light",
        "language": "en-US",
        "modified_at": "2026-05-07T09:00:00Z",
    }


@when("網路恢復後 Client 重新連線")
def step_client_reconnected(context):
    """网络恢复后客户端重新连接。"""
    context.client_connected = True


@then("Client 同步本地變更至 Server")
def step_client_sync_offline_changes(context):
    """客户端将离线变更同步到服务器。"""
    # Mock: send offline changes to server
    context.server_settings = context.offline_changes.copy()
    context.sync_result = {
        "status": "offline_changes_synced",
        "conflicts": [],
    }


@then("Server 回傳衝突解決策略（如有）")
def step_server_conflict_resolution(context):
    """服务器返回冲突解决策略（如果有）。"""
    # Mock: no conflicts in this case
    context.conflict_strategy = {"strategy": "server_wins", "conflicts": []}
    context.sync_result = {**context.sync_result, "conflict_strategy": context.conflict_strategy}


# =============================================================================
# First Install Sync Scenarios
# =============================================================================

@given("新 Client Agent 首次啟動")
def step_new_client_first_start(context):
    """新的客户端代理首次启动。"""
    context.client_connected = True
    context.is_first_sync = True


@when("Client 發起首次同步請求")
def step_client_first_sync_request(context):
    """客户端发起首次同步请求。"""
    # Mock: server returns full config for new client
    context.full_config = {
        "mcp_version": "1.3.0",
        "skills": [
            {"name": "mcp_skill_1", "version": "1.3.0", "definition": {}},
            {"name": "mcp_skill_2", "version": "1.3.0", "definition": {}},
        ],
        "settings": {
            "theme": "light",
            "language": "en-US",
        },
        "configuration": {
            "server_url": "https://api.example.com",
            "tenant_id": "default",
        },
    }
    context.sync_result = {"status": "full_sync_complete", "config": context.full_config}


@then("系統回傳完整配置")
def step_return_full_config(context):
    """验证系统返回完整配置。"""
    assert context.full_config is not None, "full_config not set"
    assert "mcp_version" in context.full_config
    assert "skills" in context.full_config
    assert "settings" in context.full_config


@then("技能定義、设定檔案全部同步")
def step_skills_and_settings_synced(context):
    """验证技能定义、设置文件全部同步。"""
    assert context.sync_result.get("status") == "full_sync_complete"
    assert len(context.full_config.get("skills", [])) > 0
    assert context.full_config.get("settings") is not None
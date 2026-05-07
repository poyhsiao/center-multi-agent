# 系統規格文件索引

> **專案：** 混合式多租戶 AI SaaS 平台  
> **版本：** v0.1  
> **日期：** 2026-05-07  
> **狀態：** 架構確認完成

---

## 文件結構

```
docs/
├── README.md              ← 本文件（索引）
└── spec/
    ├── 00_架構總覽.md      ← 系統定位、整體架構、技術選型、RBAC 模型、安全模型
    ├── 01_系統元件圖.md    ← Component Diagram（完整 Server/Client 部署架構）
    └── 02_資料流向圖.md    ← Data Flow（5 大核心流程 + 生命週期 + SSE 事件）
```

---

## 文件版本追蹤

| 文件 | 版本 | 更新日期 | 狀態 |
|------|------|----------|------|
| 00_架構總覽.md | v0.1 | 2026-05-07 | ✅ 架構確認完成 |
| 01_系統元件圖.md | v0.1 | 2026-05-07 | ✅ 架構確認完成 |
| 02_資料流向圖.md | v0.1 | 2026-05-07 | ✅ 架構確認完成 |

---

## 下一步

下一步應展開的實作規格文件：

| 優先級 | 文件 | 內容 |
|--------|------|------|
| P1 | 03_API_設計規範.md | OpenAPI / REST API endpoints, 認證流程, Rate Limit |
| P1 | 04_資料庫設計.md | Schema 設計, RLS Policy, 遷移策略 |
| P1 | 05_安全設計.md | JWT/Refresh Token, 裝置指紋, 加密方式 |
| P2 | 06_Client_Agent_設計.md | Tauri 架構, LanceDB, CUA Driver, OS 整合 |
| P2 | 07_MCP_協議設計.md | MCP Server/Client 協議, OpenAPI 格式定義 |
| P2 | 08_知識庫設計.md | RAG Pipeline, 審核流程, PGVector Schema |
| P3 | 09_部署架構.md | Docker Compose, Kubernetes, 一鍵部署腳本 |
| P3 | 10_測試策略.md | E2E 測試, 多租戶隔離測試, Failover 測試 |

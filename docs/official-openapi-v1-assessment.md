# 教育部校園食材登錄平臺 OpenAPI v1 研究紀錄

研究日期：2026-11-05

## 核心結論

使用者提供的
`https://fatraceschool.k12ea.gov.tw/cateringservice/web/openapi_doc/v1/index.html`
是**月度開放資料（Open Data）介接文件**，與 Tad Lunch3 依學校、日期擷取即時供餐的端點**不同**。
正式 OpenAPI 可望用於**歷史菜色、食材及供應商資料**，但**不能直接視為隔日預告或每日早晨即時菜單 API**。

### 可公開確認的項目

- 政府開放資料平台正式收錄：
  `https://data.gov.tw/dataset/98339`。
- 文件根網址索引資訊：
  `https://fatraceschool.k12ea.gov.tw/cateringservice/openapi`，版本 `v1`。
- Swagger UI：
  `https://fatraceschool.k12ea.gov.tw/cateringservice/web/openapi_doc/v1/index.html`。
- OpenAPI 定義：
  `https://fatraceschool.k12ea.gov.tw/cateringservice/web/openapi_doc/v1/openapi.json`。
- **已找到索引摘錄，但未能直接下載完整 Swagger 規格**：
  - `POST /accountReg/`：輸入電子郵件登錄，OpenAPI 存取碼透過郵件寄送。
  - `POST /opendatadataset/`：使用存取碼與年、月、縣市查詢資料集，依歷年政府回覆取得可下載資源的連結。
  - 查縣市列表的模型名稱可見 `countyReq`、`countyResp`，但未取得完整定義，**不應臆測確切端點、JSON 欄位或方法**。
- 官方資料集描述：提供每月全國高級中等以下學校午餐菜色、食材及供應商、調味料、團膳業者等資料；更新頻率標記「不定期」，且資訊屬檔案型。
- 授權：**政府資料開放授權條款—第 1 版**（適用於該開放資料集，不等於授權任意抓取網站全部圖片或繞過網站存取限制）。
- 2020 年政府資料開放諮詢小組會議附件回覆：先下載 OPENAPI 定義檔，再選「年月、縣市、資料集種類」取得資料集下載連結；菜色名稱在「午餐菜色及食材資料集」，並不保證每一種資料集都包含菜色名稱。

### 存取狀況與重要限制

- 本專案的 GitHub Actions 之前以普通 HTTP 請求測試中央查詢頁與 API 相關路徑，皆獲得 HTTP 403；目前用來研究的環境存取 `index.html`、`openapi.json` 也得到 403。
- **無法驗證完整 OpenAPI Schema**，包括 request 的 JSON 欄位、回傳的結構、是否有 CORS、是否須資格審核、存取碼有效期限、頻率限制、現行 2.0／3.0 相容性等。
- Swagger 文件中定義的 `openapi.json` 是**API 規格文件**，不是當日午餐菜色 JSON。
- 外部索引顯示有 email 註冊存取碼流程，**尚未替使用者申請、收到或使用任何金鑰**；沒有用真實帳號測試授權 API。
- 2026 年曾有校園食材平台靜態 JS 外洩授權金鑰的公開資安通報。**不可使用外洩金鑰、複製不當存取方法或繞過伺服器權限**；只以官方正式提供的方式申請。
- 另有 2026 年教育單位公告提及食登 3.0 架構升級及轉換排程。因此 `v1` 文件是否仍可供新系統正式使用，必須由官方確認，不能直接假設。

## 與本專案每日供餐資料的差異

| 面向 | OpenAPI v1 開放資料集 | Tad Lunch3 的歷史每日接口 | 現有學校公開頁面同步 |
|---|---|---|---|
| 資料目的 | 年月／縣市批次資料、歷史分析 | 指定學校／日期／供餐批次 | 指定試點學校的公開菜單 |
| 最早可見時間 | 月度下載，不能推論當天預告時點 | 理論上有日資料，但中央目前 HTTP 403 | 已實測部分學校可提前一天取得 |
| 需要授權 | 文件含電子郵件存取碼流程 | 舊程式未呈現相同授權流程，現在不能視為開放 | 只讀各校已公開顯示的頁面 |
| 現況 | 官方規格待確認及申請 | 不能直接串接 | 10 所左右小範圍試點，仍需驗證穩定性 |
| 推薦用途 | 歷史菜色、食材分析、未來食譜資料庫 | 正式授權後可評估每日同步 | 目前的今天／明日家長預告功能 |

## 下一步建議

1. 保留學校公開午餐網頁的既有同步，持續追蹤今天／明天首次可見及變更時間。
2. 將官方 OpenAPI 當成**歷史資料補充來源**，不要讓網站實時服務依賴它。
3. 向國教署確認：
   - OpenAPI v1／3.0 現行網址和支援狀態；
   - 申請正式 access code 的資格、程序、配額、商業加值利用條件；
   - OpenAPI 是否只提供年月批次資料，或可授權取得每日或未來預告菜單；
   - 學校的 `SchoolId` 與教育部統計名錄 `code` 的公開對照方式；
   - 菜色類型、附餐、供餐者、照片權利與更新時間欄位。
4. 如官方允許且取得正式憑證，使用 GitHub Actions 的 Secret 或其他**伺服器端**安全憑證儲存方案，絕不寫進公開的 `index.html`、`data/*.json` 或 GitHub Pages。
5. 使用者若能下載官方 `openapi.json` 原始檔，再按其確切 schema 寫可測試的客戶端，不從搜尋索引猜 payload。

## 可核對的公開來源

- 官方資料集：https://data.gov.tw/dataset/98339
- 官方 OpenAPI Swagger UI：https://fatraceschool.k12ea.gov.tw/cateringservice/web/openapi_doc/v1/index.html
- 官方 OpenAPI JSON：https://fatraceschool.k12ea.gov.tw/cateringservice/web/openapi_doc/v1/openapi.json
- 教育部 2020 開放資料諮詢會議附件：https://ws.moe.edu.tw/001/Upload/9/relfile/7959/77946/61c4502d-6949-440c-a933-1dfae94e7245.pdf
- Tad Lunch3 程式碼：https://github.com/tad0616/tad_lunch3/blob/master/index.php
- 2026/08 食登 3.0 轉換公告：https://xc.hlc.edu.tw/~xc_bulletin/index.php?cate_id=10&id=131560&page=department
- 資安公開通報：https://zeroday.hitcon.org/vulnerability/ZD-2026-01109

以上結論以截至 2026-11-05 可核對的資料為限，不代表 API 一定向第三方公開可用。

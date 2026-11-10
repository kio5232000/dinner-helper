# 🍚 今晚煮什麼？臺南版

手機友善的學校午餐查詢＋家庭晚餐靈感網站。

**網站：** https://kio5232000.github.io/dinner-helper/

## V1.7 穩定性改善（2026-11-10）

### 最新實測（11 月 10 日下午，臺北時間）

- **今日菜單：10/10 試點學校成功同步**。
- **11 月 11 日菜單預告：8/10 成功同步**；尚未驗證新嘉與新南國小明日菜單，不以今天菜單充數。
- 修復東區勝利、新生、崇明國小的 Tad Lunch3 解析：模組在 h3 中使用圖片 alt 顯示校名、`input[name=period]` 儲存日期。新解析依同一區塊確認校名、日期、菜色，不再假設日期一定是一般文字。
- **12 項解析測試通過**，包括錯日期、錯學校、附幼菜單隔離、重複菜色及更新指紋。
- 修正 GitHub Actions 在程式碼與資料同步提交互相競爭時，使用 `fetch / rebase / retry` 的非強制推送，避免非 fast-forward 錯誤。

以上是單次的實測成功率，不代表每天保證 100%。學校來源可能改版、停餐或晚於我們的排程公開。

### 目前串接的學校

| 行政區 | 國小／國中 |
|---|---|
| 柳營區 | 柳營國小 |
| 東區 | 勝利國小、崇明國小、崇明國中 |
| 後壁區 | 新嘉國小 |
| 新營區 | 新生國小 |
| 中西區 | 進學國小 |
| 佳里區 | 佳興國小 |
| 歸仁區 | 紅瓦厝國小 |
| 安平區 | 新南國小 |

本階段只維持**10 所白名單試點學校**。其他臺南國中小在學校選單中仍可選，但未串接的學校不會顯示假資料。

## 家長端功能

- 首次選擇 **行政區 → 國小／國中 → 學校**，記住學校。
- **今天／明天**午餐切換。試點學校有資料時標示 `✓`；來源檔案必須符合所選學校與日期。
- 顯示主食、主菜、副菜、蔬菜、湯品、附餐；圖像可能連來源網站，若跨站失敗用明確示意插畫取代。
- 顯示學校來源網站連結及**本站最早觀測時間**，不把它宣稱為校方首次上傳時間。明日菜單註明預告，可能臨時更改。
- 若沒有菜單，可手動輸入或選明確標示的示範菜單。
- 晚餐推薦**目前只用本地規則**，不是串接 ChatGPT 或其他 AI，尚不提供精確營養、熱量或過敏原判斷。

## 資料同步及監測

```
臺南學校公開網站（Tad Lunch3 全頁／學校首頁午餐區）
  ↓ GitHub Actions 公開頁面同步
scripts/import_tainan_pilot.py
  ├─ 校名＋行政區＋學制對照教育部學校名錄
  ├─ 日期及同校菜單驗證（含附幼隔離）
  ├─ 資料變更指紋與首次觀測時間
  ├─ data/lunch/{school_code}/{YYYY-MM-DD}.json
  ├─ data/lunch-monitor.json
  └─ data/tainan-pilot-status.json
  ↓ GitHub Pages
index.html（今天／明天，沒有資料就明確標示）
```

**排程：臺北時間週一至週五** 06:45、08:45、11:15、13:35；週日至週四 19:15 查隔日預告。GitHub Actions 排程有執行延遲，**上述是設定的時間，不是每次實際取得菜單的時間**。監測結果以檔案中的 `checked_at`、`first_seen_at`、`last_changed_at` 為準。

- 正式同步：`.github/workflows/import-tainan-pilot.yml`
- 解析回歸測試：`tests/test_lunch_import.py`
- 限定公開學校頁面結構診斷：`scripts/diagnose_lunch_pages.py`，工作流程 `.github/workflows/diagnose-lunch-headings.yml`，只用於排錯，不保存來源完整 HTML
- 名錄定期同步：`scripts/sync_schools.py`、`.github/workflows/sync-schools.yml`
- 可在 GitHub Actions 查看原始執行紀錄，或查看 `data/tainan-pilot-status.json` 的每一校來源和驗證狀態

## 官方 API 研究

- Tad Lunch3 開源程式：https://github.com/tad0616/tad_lunch3
- 公開平台的歷史單校每日接口在自動化執行環境先前回傳 HTTP 403 / Cloudflare 驗證，不能視為已授權的第三方 API。
- 官方 OpenAPI v1 的 `/accountReg/`、`/county/`、`/opendatadataset/`、`/opendatadownload/` 是**月度開放資料集**用途，**不是**即時單校午餐 API；第三方申請與正式授權方式仍需官方確認。
- 已根據完整 Swagger v1 規格撰寫 `docs/official-openapi-v1-assessment.md`，並有不送出網路請求的安全預覽工具 `scripts/official_monthly_openapi.py`。不得使用外洩金鑰或繞過 Cloudflare。
- 詳細研究：`docs/lunch-data-research.md`、`data/source-diagnostics.json`。

## 下一步與限制

1. 持續追蹤至少一個上課週，確認**首次觀測時間**、菜單臨時修改與各校未公布情況。
2. 對目前明日預告失敗的兩所學校確認是否為資料尚未發布或來源格式不同。
3. 確認資料及圖片使用權、更新頻率和多供餐批次後，再逐批擴展臺南學校。
4. 建立來源可靠的家庭食譜資料，再於安全的後端實作真正 AI 推薦。

學校午餐菜單只是供餐資訊，不代表每位孩子實際吃下的菜色或份量。網站為試點工具，並非全臺南市所有學校皆已串接的即時服務。

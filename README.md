# 🍚 今晚煮什麼？ Dinner Helper

## V1.5 臺南市先行（2026-11-05）

介面只顯示「行政區 → 國小／國中 → 學校」，移除縣市選單。網站標示「臺南版」，**GitHub 專案名稱與 Pages 網址暫不變**。

### 實際午餐資料路線

中央 [校園食材登錄平臺](https://fatraceschool.k12ea.gov.tw/frontend/search.html) 的搜尋頁／舊版 API 在 GitHub runner 回應 HTTP 403，尚無可行的直接公開 API 介接。

但是部分臺南學校透過 [Tad Lunch3](https://github.com/tad0616/tad_lunch3) 模組公開學校當日午餐。2026-11-05 的 GitHub Runner 小規模測試，柳營國小、東區勝利國小、昭明國中三校公開頁面皆回 HTTP 200，並讀到當日實際菜名，詳見 `data/tainan-source-probe.json`。

- 試點抓取器：`scripts/import_tainan_pilot.py`
- 每週一至週五 14:35 台北時間同步：`.github/workflows/import-tainan-pilot.yml`
- 使用**學校網站**作為菜單來源（`source: school_website`），而不是假稱直接取得中央 API
- 只支援三所已核對校名、地址／行政區及網址的試點學校。其他學校不顯示假的當日菜單。
- 成功後：`data/lunch/{school_code}/{YYYY-MM-DD}.json`；失敗時有 `data/tainan-pilot-status.json` 提示；網站只讀同校、同日的檔案。
- 若圖片的原始網站拒絕跨站載入，介面會回退 SVG 菜色示意圖。
- 資料與圖片使用權、更新頻率、批次供餐及多供應商異常處理尚待正式確認，試點不代表已取得所有臺南學校的午餐資料。

## V1.4：依行政區及學制篩選學校

首次設定按順序選：
1. 縣市
2. 行政區（縣市下的區／鄉／鎮／市）
3. 國小或國中
4. 學校

教育部官方名錄來源：
- 國小：https://stats.moe.gov.tw/files/school/114/e1_new.json
- 國中：https://stats.moe.gov.tw/files/opendata/j1_new.json

資料同步腳本：`scripts/sync_schools.py`；工作流程：`.github/workflows/sync-schools.yml`。
同步會產生 `data/schools.json`（新增 `district`、`level` 欄位），以及 `data/school-stats.json`（學校數量摘要）。

原本使用者已儲存的學校仍會保留，系統會嘗試補上行政區與學制。正式午餐 API 仍尚未取得，選擇學校並不代表已連接到該校午餐。



孩子中午在學校吃了什麼，晚上就換個口味。手機優先、無須註冊。

## V1.3：學校下拉選單（已更新）

- 首次設定：先選縣市，再從該縣市的學校下拉選單挑選；不再輸入校名或搜尋。
- 學校名錄載入前下拉選單鎖定，載入失敗時顯示提示（不猜測學校）。
- 延續既有 localStorage 儲存格式，已選學校會自動嘗試對應到官方統計名錄代碼。
- 其他首頁結構、午餐資料狀態、晚餐示範推薦維持不變。

### 熱量資訊（規劃中，未實作）

可使用食藥署食品營養成分資料集（https://data.gov.tw/dataset/8543）的每 100 公克熱量，搭配已驗證食譜的食材克數及每份份量計算。AI 可輔助判定食材，但不應在沒有份量與調味油資訊時輸出假精準熱量。學校午餐菜名、插畫或照片不足以判定孩子實際攝入熱量；預計僅以「示意區間／每份約值」標示並註明估計依據。

## V1.2 已完成

1. 第一次選擇縣市與學校，**記住學校**；下次進站直接顯示選定學校的今日午餐區。
2. 真實國小搜尋：教育部統計處的 **114 學年度國民小學名錄**，目前共 2,608 筆，以 GitHub Actions 自動同步為 `data/schools.json`。
3. 午餐展示有**資料狀態**：沒有正式當日菜單時清楚顯示「尚未取得」，不再冒充學校真實供餐。
4. 有官方午餐網站入口，供家長自行核對。
5. 若家長已知道菜色，可在折疊區貼上午餐名稱，進行示範規則推薦；也可明確選擇示範菜單預覽介面。
6. 午餐卡片使用 SVG 餐點插畫（標示示意圖）；晚餐推薦仍是本地規則，不是 AI。

## ⚠️ 重要：學校名錄代碼 ≠ 校園食材登錄平臺學校代碼

`data/schools.json` 內的 `code` 是教育部統計資料的「國小名錄代碼」，**不是**官方午餐平臺舊 API 的 `SchoolId`。

因此目前 **無法**把學校名錄代碼直接拿去呼叫官方午餐 API。正式介接需先確認新版 API、授權/存取方式、學校 ID 對照、CORS、供餐批次與菜單結構。

**2026-11-05 實測結果：** GitHub Actions 以一般 HTTP 請求測試官方查詢頁、OpenAPI 文件與歷史 offered/meal 介面，三者均回傳 HTTP 403，且未提供允許 GitHub Pages 的 CORS 標頭。結果記錄於 `data/source-diagnostics.json`，程式為 `scripts/check_lunch_access.py`，可由 `.github/workflows/check-lunch-source.yml` 手動重新測試。這不表示所有用戶在官方網站都會遇到 403，但我們尚無可確認的網站直接讀取方式。

請勿將此版本視為即時午餐資料服務。正式介接需要向官方確認 API 允許的使用方式或改用具有授權的其他來源。

## 學校名錄同步

官方來源：https://stats.moe.gov.tw/files/school/114/e1_new.json

- 程式：`scripts/sync_schools.py`
- 工作流程：`.github/workflows/sync-schools.yml`
- 本地資料：`data/schools.json`
- GitHub Actions 在工作流程首次提交、每週排程或手動執行時更新
- `contents: write` 權限用於將名錄變更提交回主分支

## 未來午餐資料交換格式

預留本地檔案 `data/lunch/{school_code}/{YYYY-MM-DD}.json`，供後端同步模組填入，格式：

```json
{
  "source": "official",
  "date": "2026-11-05",
  "school_code": "學校名錄 code",
  "dishes": [
    {"name": "真實菜名", "photo_url": null}
  ]
}
```

**注意：** 此交換格式只是網站內部介面，不代表來源 API 的回傳格式或已完成對接。正式後端必須核對原始來源、所選學校與日期，防止錯誤資料混入。

## 部署

GitHub Pages：https://kio5232000.github.io/dinner-helper/

若未啟用：Settings → Pages → Deploy from a branch → main → /(root) → Save。

## 待做

- 取得或核准可用的官方午餐 API，驗證各校對應的供餐服務 ID。
- 透過後端或排程同步每日午餐，處理供餐批次、停餐與資料不存在。
- 自動辨識食材、已審核食譜庫及過敏原審查。
- 於後端整合 OpenAI API，勿將金鑰放在公開 GitHub Pages 程式裡。

資料使用：教育部統計處公開資料（政府資料開放授權條款第 1 版），需保留來源與署名。
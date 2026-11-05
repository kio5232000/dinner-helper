# 臺南市午餐資料來源研究（2026-11-05）

## 1. 現況（務必分清）

- 本站的國小／國中名錄來自教育部統計處公開 JSON，**其學校代碼不等於**教育部午餐系統的 `SchoolId`。
- 教育部校園食材登錄平臺的公開查詢頁、OpenAPI 文件及歷史菜單網址，在 GitHub Actions 伺服器的存取測試皆回 `403`，亦未提供允許 GitHub Pages 網站直接跨站存取的 CORS 標頭。詳 `data/source-diagnostics.json`。
- 臺南市部分學校網站透過 Tad Lunch3 顯示校園食材登錄平臺的菜色。GitHub Actions 已從數所學校的公開網頁讀取並解析當日菜單，存為 `data/lunch/{統計學校代碼}/{YYYY-MM-DD}.json`。這是**學校網站公開菜單的同步**，**不是**中央 API 已開放的證明。
- 臺南市學校午餐教育資訊網 `https://lunch.tn.edu.tw/` 以營養教育、食譜及午餐行政資訊為主，暫未證實有通用的全校每日供餐 API。

## 2. 依據 Tad Lunch3 開放程式碼，確認的資料接口

原始程式：`https://github.com/tad0616/tad_lunch3/blob/master/index.php`。

程式依序呼叫（歷史介面，可能已變動，不保證現在可直接使用）：

1. `https://fatraceschool.k12ea.gov.tw/school/{SchoolId}` 取得校園食材平台學校 ID 與學校資訊；
2. `https://fatraceschool.k12ea.gov.tw/offered/meal?SchoolId={SchoolId}&period={YYYY-MM-DD}&KitchenId=all` 取得供餐批次；
3. `https://fatraceschool.k12ea.gov.tw/dish?BatchDataId={BatchDataId}` 取得該批次菜色。

開放原始碼顯示資料於學校網站端快取，故「學校網站仍可顯示」不代表「我們的網域可以直接存取中央平台」。任何正式直接介接，需確認現行服務條款、官方 API、存取授權及資料欄位。**不得繞過 403、登入權限或網路防護。**

## 3. 目前實作與驗證

- 小範圍白名單：`scripts/import_tainan_pilot.py` 的 `PILOTS`。
- 每次只請求每所白名單學校當日的公開頁面，一次限定大小、逾時與筆數。
- 使用教育部統計名錄的 **行政區 + 學制 + 校名** 確認資料歸屬，避免重名學校混淆。
- 必須同時檢查頁面學校／日期、至少三道菜、含主菜，驗證通過才發布當日 JSON。
- 菜單來源標示 `source: school_website` 和 `source_url`，網站不會把他校、舊日、示範菜單冒充當日官方資料。
- 對供應商／附幼等額外菜單仍需更可靠的結構化解析，現階段僅採試點校第一份完整午餐；不應宣稱涵蓋多餐別。
- 每日同步由 `.github/workflows/import-tainan-pilot.yml` 執行（平日臺北時間下午 2:35）；GitHub Pages 靜態讀取同步檔案。排程可能延遲，若當日缺資料則顯示「尚未取得」。
- 圖片僅保留來源網址，不重新上傳。跨站圖片可能失效，也必須先核對授權；未成功載入時以 SVG 示意圖取代。

## 4. 進一步擴展條件

先選擇同意公開使用、具有可穩定讀取頁面的學校，觀察一週工作日是否每天順利同步，再擴增至更多區域。後續如可申請正式午餐 API，應改用具資料授權且可靠的單一後端，對接 `SchoolId`、供應商、餐別、資料校驗、快取與異常回報；之後再串接已驗證食譜和 AI 推薦。

> 請勿把相似日期、圖片或學校名稱當成學校午餐資料已經完整查證。

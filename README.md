# 🍚 今晚煮什麼？ Dinner Helper

孩子中午在學校吃了什麼，晚上就換個口味。手機優先、無須註冊。

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

目前尚未驗證每日午餐 API 回傳，請勿將此版本視為即時午餐資料服務。

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
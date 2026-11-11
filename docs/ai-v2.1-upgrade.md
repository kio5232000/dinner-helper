# V2.1 快取升級與驗收

## 已完成的程式修改

V2.1 沿用原本的 Cloudflare Worker、D1 資料庫及兩個秘密，不新增任何服務。前端與後端部署是分開的：GitHub Pages 更新後仍相容 V2.0 Worker，但只有部署 V2.1 Worker 並完成 D1 遷移，才有快取與 Token 紀錄。

- 公開學校菜單：後端核對 GitHub Pages 原始 JSON 的校碼、日期、菜名與分類。核對通過後以排序後的菜單與模型/提示詞版本建立 SHA-256 快取鍵。
- 相同菜單可跨學校、跨使用者共用七天內的 AI 推薦；菜單內容改變就使用新鍵。自行輸入菜單或核對失敗不進入共用快取。
- 讀取快取不消耗每日新生成額度。新生成仍使用既有的每 IP 2 次、全站 35 次限制。相同菜單並行查詢時，利用 D1 原子寫入取得 90 秒生成權；其他請求收到稍後重試提示。
- 每日記錄 OpenAI 成功 HTTP 回應中的實際 usage：輸入、快取輸入、輸出 Token 及回應數。若上游未回傳 usage 或 D1 紀錄失敗，可能不完整；以 OpenAI Usage/帳務為準。
- 生成後的食譜是建議，不代表孩子實際攝取量或營養診斷。

## 1. 先更新既有 D1（不要刪除原表）

1. 登入 [Cloudflare Dashboard](https://dash.cloudflare.com/)。
2. 選擇儲存空間和資料庫 → D1 SQLite 資料庫 → `dinner-helper-quota` → 主控台。
3. 開啟 [0002_cache_usage.sql](../worker/migrations/0002_cache_usage.sql)，複製整份 SQL 貼入主控台，按執行。指令都是 CREATE IF NOT EXISTS，可安全重複執行，不會清除原有 quota 資料。
4. 在主控台執行以下查詢確認：

```sql
SELECT name FROM sqlite_master
WHERE type = 'table'
AND name IN ('quota','ai_cache','ai_usage_daily')
ORDER BY name;
```

三張表都出現才繼續。若 SQL 執行失敗，先不要更新 Worker。

## 2. 更新既有 Worker

1. 運算 → Workers 和 Pages → `dinner-helper-ai`。
2. 點「編輯代碼」。從 [index.js](../worker/src/index.js) 複製完整程式碼，取代 Cloudflare 編輯器中的主要 `worker.js`，再按部署。
3. 原本 `QUOTA_DB`、`IP_HASH_PEPPER`、`OPENAI_API_KEY` 繫結與秘密保持不變，無須重建或貼到 GitHub。
4. 不要因直接造訪 Worker 根路徑回傳 403 而修改程式；本服務仍只接受正式網站來源的 /recommend 請求。

## 3. 實際驗收

- 在 [今晚煮什麼？網站](https://kio5232000.github.io/dinner-helper/) 重新整理，選擇已同步的學校與同一天菜單。
- 點 AI 分析一次；若尚未有快取，應顯示「AI 生成」且扣一次生成額度。這次可能產生 OpenAI API 費用。
- 不改變學校、日期、午餐內容，再點一次。應顯示「AI 共用推薦」與不消耗新生成額度。若第二次仍顯示新生成，請先停止重複測試並排查後端、資料驗證與 D1。
- 查看 D1 主控台的每日用量：

```sql
SELECT day, model, responses, input_tokens,
       cached_input_tokens, output_tokens
FROM ai_usage_daily
ORDER BY day DESC, model;
```

同一個新菜單的兩次請求，正常只增加一筆模型回應計數；若第一次已命中，兩次都不新增。可另外查快取筆數：

```sql
SELECT COUNT(*) AS active_cache_count FROM ai_cache
WHERE result_json IS NOT NULL
AND expires_at > unixepoch()*1000;
```

快取使用七天效期（過期資料不再回傳，未自動清除舊列）。D1 的 token 紀錄是本版本部署之後的觀測用量，不會補回 V2.0 歷史資料。官方實際扣費以 [OpenAI Usage](https://platform.openai.com/usage) 為準。

## 回復方式

若 V2.1 Worker 部署後出錯，可在 Cloudflare 的部署紀錄回復 V2.0 Worker；新資料表保留不影響舊版。若需要完全停止新的 API 支出，停用 Worker 或撤銷專用 API Key；僅關閉前端按鈕並不會阻止直接呼叫公開後端。

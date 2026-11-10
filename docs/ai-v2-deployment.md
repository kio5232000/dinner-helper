# V2.0 AI 晚餐助手：安全上線說明（2026-11-10）

## 目前狀態

- 已完成前端 AI 分析 UI、三道晚餐食譜卡片、食材、步驟、時間，以及原本的免費規則式料理推薦。
- 後端 `worker/src/index.js` 已完成並通過模擬測試，但**尚未連線真實 OpenAI API、也尚未部署到你的 Cloudflare 帳號**。不能把測試通過解讀成真實 API 已可使用。
- `ai-config.js` 預設是空網址，因此前端**不會**呼叫 OpenAI，也不會產生 API 費用。你完成下面四步才會啟用 AI。

## 架構與安全

```text
GitHub Pages (index.html, ai-config.js, 公開學校午餐 JSON)
      │ 只傳送菜名、分類（不送姓名、帳號或 API Key）
      ↓ HTTPS
Cloudflare Worker (/recommend)
      ├─ CORS: 只回應 https://kio5232000.github.io
      ├─ 入參/大小檢查及拒絕跨站 Origin
      ├─ Cloudflare IP + 私有 Pepper → SHA-256 派生每日計數鍵
      ├─ D1 原子計數：單一 IP 每臺灣日 2 次，全球每日 35 次
      └─ OpenAI Responses API (gpt-5-mini, JSON schema, max_output_tokens=2300)
                 ↓
      午餐食材分析、恰好 3 道晚餐、食材、步驟、預估時間
```

**重要限制：** `Origin` 與 CORS 是瀏覽器限制，不是登入身分驗證；自動化客戶端可以偽造 Origin。D1 依 Cloudflare 提供的來源 IP 配額作保護，但多 IP 可共用全站 35 次額度。每個請求**先占額度再呼叫模型**，就算回應失敗也可能扣次數。這是保守的防費用暴衝設計，而不是帳務級「絕對硬上限」；請另外在 OpenAI 專案設定使用量預算警示，並定期查帳。Cloudflare Worker/D1 也可能有平台費用，依帳戶方案與實際使用量為準。

## 步驟 1：建立 Cloudflare Worker/D1

需先註冊或登入自己的 Cloudflare 帳號，安裝 Node.js（建議 20+）。**以下命令由你在自己的終端機執行，不要把密鑰貼到 GitHub 或聊天中。**

```bash
git clone https://github.com/kio5232000/dinner-helper.git
cd dinner-helper/worker
npm install
npx wrangler login
npx wrangler d1 create dinner-helper-quota
```

最後會回傳 `database_id`。請把它填進 `worker/wrangler.toml` 的：

```toml
database_id = "REPLACE_WITH_YOUR_D1_DATABASE_ID"
```

將佔位文字換成真正 D1 ID。接著執行：

```bash
npx wrangler d1 migrations apply dinner-helper-quota --remote
```

資料庫建立 `quota(day, key, used)` 及索引。

## 步驟 2：設定私密金鑰

到 [OpenAI API 平台](https://platform.openai.com/api-keys) 建立**專用於此網站的 Project API key**。ChatGPT Plus 訂閱不會自動提供 API 額度。建議在該專案設定小額預算警示、查看實際成本，勿和其他應用共用金鑰。

在 `worker/` 目錄執行：

```bash
npx wrangler secret put OPENAI_API_KEY
npx wrangler secret put IP_HASH_PEPPER
```

第一個輸入 OpenAI API key；第二個輸入你自行產生、不可預測的長字串（建議 32 字元以上），專門用來雜湊用量識別碼。**不要**放到 `wrangler.toml`、`ai-config.js` 或 GitHub。

## 步驟 3：部署 Worker

```bash
npx wrangler deploy
```

取得 `https://dinner-helper-ai.<你的子網域>.workers.dev` 類似網址。這個網址是**公開端點**，可以放入前端；它**不是** API Key。

本 Worker 預期：
- `OPTIONS /recommend` 提供 CORS 預檢。
- `POST /recommend` 僅接受 JSON，要求含兩至二十道菜 `{ "dishes": [{"name":"三杯雞","category":"主菜"},...] }`。
- 只允許正式 GitHub Pages 的 Origin；無 Cloudflare 來源 IP、資料庫或 secrets 時會拒絕請求，不會直接把付費金鑰曝光。

## 步驟 4：在 GitHub Pages 啟用 AI

確認 Worker 可正常用自己的網站 Origin 測試後，編輯根目錄 `ai-config.js`：

```js
// 這裡只有 Worker 公開網址，不是 API Key。
window.DINNER_AI_ENDPOINT = "https://dinner-helper-ai.你的子網域.workers.dev";
```

將檔案提交並等 GitHub Pages 部署；之後首頁 AI 按鈕才會啟用。**未完成前不必修改此檔**，免費基本晚餐推薦照常可用。

## 費用估算與保護

目前預設模型 `gpt-5-mini`，官方標準文字單價約 **US$0.25／百萬輸入 token、US$2.00／百萬輸出 token**（2026-11-10 查核；之後須以官方定價為準）。

假設每次約 1,500 輸入＋2,000 輸出 token，則預估：
- 輸入：1500 × 0.25 / 1,000,000 = US$0.000375
- 輸出：2000 × 2 / 1,000,000 = US$0.004
- **每次約 US$0.0044**
- 每日 35 次全部用完，30 天約 US$4.60；這是**示例估算**，非固定月費或保證上限。模型可能含額外推理/格式 token；Worker、D1、其他平台費用另計。

內建控制：
- 單一 Cloudflare 來源 IP／臺灣日期最多 2 次。
- 全站同一臺灣日期最多 35 次。
- 每次請求最多 20 道菜、限制文字長度；`max_output_tokens=2300`。
- 資料庫失效直接 503（拒絕消耗 API 額度）。
- API 失敗時不自動重試花費，前端仍能使用本地免費推薦。

**額度是保守的 API 請求限制，不是保證不會超出任何帳單金額的財務硬限制。**若公開流量升高，建議接 Turnstile、防濫用監控、登入驗證或實作更嚴謹的全站預算控制。

## 測試與驗收

```bash
cd worker
npm test
```

GitHub Actions `V2 AI backend tests` 自動執行 Worker 模擬測試與前端語法檢查，包含：
1. 有效資料回傳 3 道料理，API key 不出現在回傳值。
2. 同來源 IP 連續第三次請求被拒絕。
3. 跨站 Origin、不正確菜單、缺少 secrets 都會拒絕。
4. OpenAI 上游錯誤時不產生虛構菜單。
5. `index.html` 與 Worker 腳本語法檢查。

**尚缺實際付費 API E2E 驗收**：待你部署 Worker、設定 secrets 後，才能用真實菜單跑一次並確認 OpenAI 專案計費、D1 計數與 UI，之後才算完整上線。

## 內容與隱私限制

輸入只有午餐菜名與分類；**不要輸入兒童姓名、健康狀況、過敏病史或其他敏感資訊**。生成內容只依菜名推估可能食材，不能診斷營養缺乏、過敏原安全，也不代表學生吃下多少份量。確認肉類完全熟透、魚刺、食物過敏與家人飲食需求應由家長自行把關。

如要停用 AI，將 `ai-config.js` 的端點改回空字串並部署；如需立即阻止後端繼續產生費用，應同時停用 Cloudflare Worker 或撤銷 OpenAI 專案 API key。

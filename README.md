# 🍚 今晚煮什麼？ Dinner Helper

以學校午餐為起點的家庭晚餐靈感網站。

## V1 體驗
開啟 GitHub Pages： https://kio5232000.github.io/dinner-helper/ （須先在 GitHub 啟用 Pages）

- 第一次輸入縣市與學校名稱，使用瀏覽器 localStorage 儲存設定
- 下次進站直接看到今日午餐示範菜單
- 午餐以 emoji 插圖搭配菜名呈現
- 按下「推薦今晚晚餐」後，透過本地規則從示範食譜推薦 3 道料理
- 料理時間、預算、排除食材及換一批

## ⚠️ V1 是原型，非正式資料服務
- 學校名稱是使用者自行輸入的**顯示標籤**，並未連線教育部學校名冊或即時午餐資料。
- 每日午餐內容是**示範資料**，**不是**該校真實菜單。
- 並未串接 OpenAI API。推薦使用本地規則。
- 食譜、預算與料理步驟僅為示範，**尚未人工驗證**。
- 排除食材使用字串比對，**不能**作為過敏原安全控管。
- 不需要帳號，設定儲存在當前瀏覽器，清除瀏覽資料會消失。

## 開啟 GitHub Pages
1. Repository → **Settings** → **Pages**。
2. **Build and deployment** → **Source** 選 **Deploy from a branch**。
3. **Branch** 選 **main**，資料夾選 **/(root)**，按 **Save**。
4. 待部署完成後，造訪 https://kio5232000.github.io/dinner-helper/ 。

此版本為單檔 index.html，不需要 npm、build 指令或任何 API 金鑰。

## 下一階段
- 教育部午餐資料 API（透過後端代理、快取、錯誤處理）
- 官方食材分類及學校供餐組合
- 人工審核的食譜資料庫、可靠過敏原排除
- 後端 OpenAI API 依候選食譜編排晚餐
- 已授權料理圖片與真實/示意圖片標示

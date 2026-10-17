# 🎬 StreamProject 影音串流平台系統（資料庫管理系統 第十組專題）

本專案為中山大學資料庫管理系統**第十組**期末專題，使用 **Python Flask + PostgreSQL** 實作影音串流平台帳號、訂閱方案、子使用者（Profile 弱實體）、兒童模式分級過濾、觀看紀錄與多值觀看時間點（`Watch_Time`）及後台 ECharts 數據分析儀表板。

---

## 🚀 組員快速安裝與啟動步驟

### 1. 下載專案 (`git clone`)
打開終端機（Mac Terminal 或 Windows PowerShell），執行：
```bash
git clone <此 GitHub Repository 的網址>
cd stream_project
```

### 2. 建立虛擬環境並安裝套件
- **Mac / Linux**：
  ```bash
  python3 -m venv venv
  ./venv/bin/pip install -r requirements.txt
  ```
- **Windows (PowerShell)**：
  ```powershell
  python -m venv venv
  .\venv\Scripts\pip install -r requirements.txt
  ```

### 3. 新增資料庫連線設定檔 `.env`
在 `stream_project` 資料夾根目錄建立一個名為 **`.env`** 的檔案，貼上我們第十組的 PostgreSQL 連線資訊（請向組長索取密碼填入）：
```env
DB_USER=project_10
DB_PASSWORD=<請填入第十組資料庫密碼>
DB_NAME=project_10
DB_HOST=140.117.68.35
DB_PORT=5432
```
> 💡 **注意**：我們第十組的 9 張資料表（`Account`, `Plan`, `Subscription`, `Profile`, `Movie`, `Genre`, `Belong`, `Watch`, `Watch_Time`）與初始資料**已經建立在學校伺服器 `project_10` 資料庫中**，組員**不需要**再次執行 `schema.sql` 或 `seed.sql`！

### 4. 啟動網站
- **Mac / Linux**：
  ```bash
  ./venv/bin/python app.py
  ```
- **Windows**：
  ```powershell
  .\venv\Scripts\python app.py
  ```
啟動後打開瀏覽器前往：**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 測試帳號一覽

| 身份 | 帳號 (Email) | 密碼 | 說明 |
| :--- | :--- | :--- | :--- |
| **一般家庭會員** | `family@example.com` | `1234` | 內含「爸爸」、「媽媽」、「小明（兒童模式）」3 個 Profile |
| **一般會員** | `linda@example.com` | `1234` | 標準方案（上限 2 人） |
| **後台管理員** | `admin@example.com` | `admin` | 可管理電影與類別、檢視全站訂閱/觀看紀錄與數據分析儀表板 |

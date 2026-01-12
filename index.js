const express = require('express');
const { Pool } = require('pg');
const { createClient } = require('redis');
const swaggerUi = require('swagger-ui-express');
const YAML = require('yamljs');
const { tenantMiddleware, getTenantId } = require('./context');

const app = express();
const port = 3000;

// 文檔
const swaggerDocument = YAML.load('./swagger.yaml');
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

// --- 1. Admin Pool (上帝視角) ---
// 只有在啟動時用它來建表、設權限
const adminPool = new Pool({
  connectionString: process.env.DATABASE_URL, // 使用 docker-compose 裡的 admin 帳號
});

// --- 2. App Pool (凡人視角) ---
// 這是給程式跑業務邏輯用的，稍後會初始化
let appPool = null;

const redisClient = createClient({
  url: process.env.REDIS_URL
});
redisClient.on('error', (err) => console.log('Redis Client Error', err));

app.use(tenantMiddleware);

// --- 核心工具：安全查詢包裝器 (Safe Query Wrapper) ---
// 這就是「橋接模型」的關鍵實作
async function safeQuery(text, params = []) {
  // 1. 從隱形口袋拿到租戶 ID
  const tenantId = getTenantId();
  
  // 2. 從凡人池借一個連線
  const client = await appPool.connect();
  
  try {
    // 3. 【關鍵】設定 Session 變數
    // 告訴資料庫：「這次操作是屬於 tenantId 的，請用 RLS 幫我過濾」
    // set_config(key, value, is_local) -> is_local=true 代表只在這次 transaction 有效
    //await client.query(`SELECT set_config('app.current_tenant', $1, false)`, [tenantId]);
    
    // 4. 執行真正的查詢
    const res = await client.query(text, params);
    return res;
    
  } finally {
    // 5. 歸還連線 (很重要！不然連線池會乾掉)
    client.release();
  }
}

async function initDatabase() {
  const client = await adminPool.connect();
  try {
    console.log("正在執行資料庫初始化 (Admin)...");

    // 1. 建立業務用的受限帳號 (app_user)
    // 如果已經存在就忽略錯誤
    try {
      await client.query(`CREATE ROLE app_user WITH LOGIN PASSWORD 'app_pass';`);
    } catch (e) { /* ignore if exists */ }

    // 2. 建表
    await client.query(`
      CREATE TABLE IF NOT EXISTS access_logs (
        id SERIAL PRIMARY KEY,
        tenant_id VARCHAR(50),
        payload TEXT, -- 增加一個欄位讓我們寫些測試資料
        created_at TIMESTAMP DEFAULT NOW()
      );
    `);

    // 3. 【開啟 RLS】
    await client.query(`ALTER TABLE access_logs ENABLE ROW LEVEL SECURITY;`);

    // 4. 【設定政策】(最重要的一行！)
    // 翻譯：只有當 tenant_id 等於 app.current_tenant 這個變數時，才允許看見或修改
    // DROP POLICY 為了避免重複建立報錯
    await client.query(`DROP POLICY IF EXISTS tenant_isolation_policy ON access_logs;`);
    await client.query(`
      CREATE POLICY tenant_isolation_policy ON access_logs
      USING (tenant_id = current_setting('app.current_tenant')::varchar);
    `);

    // 5. 賦予 app_user 權限
    await client.query(`GRANT ALL ON access_logs TO app_user;`);
    await client.query(`GRANT USAGE, SELECT ON SEQUENCE access_logs_id_seq TO app_user;`);

    console.log("資料庫 RLS 安全機制已部署完成。");

  } finally {
    client.release();
  }
}

async function startServer() {
  await redisClient.connect();
  
  // 先用 Admin 設好規則
  await initDatabase();

  // 初始化 App Pool (用受限帳號連線)
  // 注意：這裡的密碼 'app_pass' 對應上面 CREATE ROLE 的密碼
  appPool = new Pool({
    connectionString: 'postgres://app_user:app_pass@db:5432/saas_db' 
  });

    app.get('/', async (req, res) => {
      try { 
        const tenantId = getTenantId();
        
        // 寫入日誌
        // 注意：我們改用 safeQuery，它會自動帶入 tenant_id 上下文
        await safeQuery(
          'INSERT INTO access_logs (tenant_id, payload) VALUES ($1, $2)',
          [tenantId, `User from ${tenantId} visited`]
        );

        // --- 驗證 RLS 的時刻 ---
        // 我們故意下一個「全表掃描」的指令 (SELECT * FROM access_logs)
        // 如果沒有 RLS，這裡會撈出所有人的資料 (包含 Google, Apple...)
        // 如果有 RLS，這裡應該只會吐出「我自己」的資料
        const result = await safeQuery('SELECT * FROM access_logs');

        res.json({
          message: `歡迎光臨 (RLS版)，${tenantId}`,
          your_data: result.rows, // 這裡顯示撈到了什麼
          security_level: "High (Database RLS Enforced)"
        });

      } catch (err) {
        console.error(err);
        res.status(500).json({ error: err.message });
      }
  });

  app.listen(port, () => {
    console.log(`SaaS App listening at port ${port}`);
  });
}

startServer();
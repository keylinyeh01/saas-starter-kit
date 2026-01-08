const express = require('express');
const { Pool } = require('pg');
const { createClient } = require('redis');

const app = express();
const port = 3000;

// 設定限制：每個租戶，每 10 秒鐘，只能訪問 5 次
// (為了讓你方便測試，我設得很嚴格)
const TIME_WINDOW = 10; // 秒
const MAX_REQUESTS = 5; // 次數

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

const redisClient = createClient({
  url: process.env.REDIS_URL
});

redisClient.on('error', (err) => console.log('Redis Client Error', err));

// 這是我們的「保全」函數
async function isRateLimited(tenantId) {
  const key = `rate_limit:${tenantId}`;
  
  // 1. 幫這個租戶的計數器 +1
  const currentCount = await redisClient.incr(key);

  // 2. 如果他是第一次來，設定這個計數器 10 秒後自動歸零 (過期)
  if (currentCount === 1) {
    await redisClient.expire(key, TIME_WINDOW);
  }

  // 3. 檢查有沒有超過限制
  if (currentCount > MAX_REQUESTS) {
    return true; // 擋下！
  }
  return false; // 放行
}

async function startServer() {
  await redisClient.connect();

  // 初始化資料庫表
  await pool.query(`
    CREATE TABLE IF NOT EXISTS access_logs (
      id SERIAL PRIMARY KEY,
      tenant_id VARCHAR(50),
      created_at TIMESTAMP DEFAULT NOW()
    );
  `);

  app.get('/', async (req, res) => {
    try {
      const tenantId = req.query.tenant || 'anonymous';

      // --- 保全檢查站 Start ---
      const limited = await isRateLimited(tenantId);
      if (limited) {
        // 如果被擋下，回傳 429 (Too Many Requests) 錯誤代碼
        return res.status(429).json({
          error: "太頻繁了！",
          message: `親愛的 ${tenantId}，你說話太快了，請休息一下。`,
          limit: `每 ${TIME_WINDOW} 秒只能 ${MAX_REQUESTS} 次`
        });
      }
      // --- 保全檢查站 End ---


      // 下面是原本的商業邏輯 (記帳 + 回應)
      const redisKey = `visits:${tenantId}`;
      const visitCount = await redisClient.incr(redisKey);
      
      await pool.query(
        'INSERT INTO access_logs (tenant_id) VALUES ($1)',
        [tenantId]
      );

      res.json({
        message: `歡迎光臨，${tenantId}`,
        count: visitCount,
        status: "正常通行"
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
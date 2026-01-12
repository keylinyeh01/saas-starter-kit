const { AsyncLocalStorage } = require('async_hooks');

// 這是 Node.js 內建的神奇儲存空間
// 它能確保這份資料只屬於「目前的請求」，不會跟別人的請求搞混
const asyncLocalStorage = new AsyncLocalStorage();

module.exports = {
  // 1. 中間件 (Middleware)：負責在門口把 tenant_id 塞進口袋
  tenantMiddleware: (req, res, next) => {
    // 從網址參數 (?tenant=google) 讀取，預設為 anonymous
    const tenantId = req.query.tenant || 'anonymous';
    
    // 建立一個儲存區 (Store)，把 tenantId 放進去
    const store = new Map();
    store.set('tenantId', tenantId);

    // 這裡是最神奇的地方：
    // 使用 .run()，接下來所有的 next() 流程，都「看得到」這個 store
    asyncLocalStorage.run(store, () => {
      next(); // 繼續往後執行 (進入原本的 app.get 等等)
    });
  },

  // 2. 取用工具 (Getter)：負責隨時從口袋拿資料
  getTenantId: () => {
    const store = asyncLocalStorage.getStore();
    return store ? store.get('tenantId') : 'anonymous';
  }
};
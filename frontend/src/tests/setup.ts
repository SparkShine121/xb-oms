// node 环境（非 jsdom）下提供 localStorage / sessionStorage 轻量实现，
// 供不依赖 DOM 的纯逻辑测试（如 user store）使用。
function makeStorage(): Storage {
  const store = new Map<string, string>()
  return {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => { store.set(k, String(v)) },
    removeItem: (k: string) => { store.delete(k) },
    clear: () => { store.clear() },
    key: (i: number) => [...store.keys()][i] ?? null,
    get length() { return store.size },
  } as Storage
}
if (typeof globalThis.localStorage === 'undefined') globalThis.localStorage = makeStorage()
if (typeof globalThis.sessionStorage === 'undefined') globalThis.sessionStorage = makeStorage()

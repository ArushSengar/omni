# OmniRoute Optimization Guide: Tips, Tricks & Best Practices

Optimized specifically for edge devices, ARM64 hardware (Raspberry Pi 4 / 5), and self-hosted environments.

---

## 1. Raspberry Pi 4 Resource Tuning

### Memory Cap (`OMNIROUTE_MEMORY_MB`)
By default, Node.js applications attempt to allocate up to 50-70% of total host RAM. On a 4GB Raspberry Pi sharing memory with OS, Hermes Agent, and Chromium browser automation, set:
```env
OMNIROUTE_MEMORY_MB=1024
```
This restricts the Node V8 heap to 1GB, preventing out-of-memory (OOM) kernel kills while providing ample room for routing tables and SQLite caches.

### Cold Start Readiness (`OMNIROUTE_READY_TIMEOUT_MS`)
On SD card storage or busy multi-core ARM systems, Next.js / Node route registration may take 40-70 seconds on initial boot.
```env
OMNIROUTE_READY_TIMEOUT_MS=120000
```
This prevents systemd or supervisor watchdogs from terminating the service during initial cold startup.

### Compression Worker Pool (`OMNI_COMPRESSION_WORKERS`)
OmniRoute features token compression engines (`caveman`, `omniglyph`, and `rtk`) that trim redundant conversational fluff from tool output loops.
On 4-core SBCs:
```env
OMNI_COMPRESSION_WORKERS=1
OMNI_COMPRESSION_WORKER_TIMEOUT_MS=60000
OMNI_COMPRESSION_WORKER_IDLE_MS=30000
```
Setting 1 worker thread prevents CPU core starvation, keeping Hermes agent tasks responsive.

---

## 2. Security Hardening

### The Public Exposure Golden Rule
Never bind to `0.0.0.0` or open a public tunnel without:
```env
REQUIRE_API_KEY=true
```
When `REQUIRE_API_KEY=true`:
- Every incoming request to `/v1/models`, `/v1/chat/completions`, etc., MUST supply `Authorization: Bearer <valid-omnikey>`.
- Unauthenticated requests are immediately halted with `HTTP 401 Unauthorized` without consuming upstream provider quota.

### HTTPS Cookie Enforcement
When accessing the OmniRoute dashboard over Cloudflare tunnels:
```env
AUTH_COOKIE_SECURE=true
```
Guarantees session cookies are transmitted exclusively over encrypted TLS connections.

---

## 3. High-Performance Combos & Fallback Chains

OmniRoute Combos let you define cascading model tiers. If a premium model hits a rate limit or network error, OmniRoute automatically falls back to the next tier without failing the client request.

### `hermes-brain` (Primary Reasoning Chain)
1. **Tier 1**: `antigravity/claude-sonnet-4-6` (Deep reasoning, code execution)
2. **Tier 2**: `no-think/antigravity/claude-opus-4-6-thinking` (Ultra-heavy tasks)
3. **Tier 3**: `antigravity/gemini-3.8-flash-high` (High-speed large context)
4. **Tier 4**: `gh/gpt-4.1` (Backup provider)
5. **Tier 5**: `codestral/codestral-2508` (Mistral code engine)

### `hermes-fast` (High-Throughput Chain)
1. `antigravity/gemini-3-flash`
2. `gh/gpt-4.1`
3. `codestral/codestral-2508`
4. `antigravity/claude-sonnet-4-6`

---

## 4. Semantic & Reasoning Caches

OmniRoute embeds an in-memory & SQLite vector/semantic cache:
- `SEMANTIC_CACHE_TTL_MS=1800000` (30 minutes): Repeated queries with identical semantic intent return instant cached responses with zero upstream latency and zero cost.
- `PROMPT_CACHE_TTL_MS=300000` (5 minutes): Hot prompt prefixes remain in memory for instant reuse across turns.

---

## 5. Tunnel Persistence with Systemd

Instead of manually running terminal background processes that die upon logout:
Use the provided `omniroute-tunnel.service` unit:
- Automatically starts on boot.
- Auto-restarts on network dropouts.
- Dynamically discovers and writes the active trycloudflare URL to `/home/arush/.omniroute/public_url.txt`.

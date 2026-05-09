import fs from 'fs/promises';

// ─── Config ──────────────────────────────────────────────────────────────────

const BATCH_SIZE        = 100;
const RETRY_LIMIT       = 5;    // low — fall back to single-IP endpoint quickly
const REQUEST_WINDOW  = 60_000; // ip-api: 30 req/min on the free tier
const REQUEST_LIMIT   = 28;     // stay 2 under the hard cap as a safety margin
const FETCH_TIMEOUT   = 10_000;

const REPO          = 'https://raw.githubusercontent.com/doodad-labs/tor-node-tracker/refs/heads/main/';
const IP_API_BATCH  = 'http://ip-api.com/batch?fields=8386';
const IP_API_SINGLE = 'http://ip-api.com/json';

// ─── Types ───────────────────────────────────────────────────────────────────

interface GeoEntry {
    ip:        string;
    country:   string;
    latitude:  number;
    longitude: number;
}

interface IpApiItem {
    query:       string;
    countryCode: string;
    lat:         number;
    lon:         number;
}

interface IpApiSingleResponse {
    status:      string;
    countryCode: string;
    lat:         number;
    lon:         number;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Fetch with an automatic abort timeout. Returns null on any error. */
async function fetchWithTimeout(
    url:     string,
    options: RequestInit = {},
    ms      = FETCH_TIMEOUT,
): Promise<Response | null> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), ms);
    try {
        return await fetch(url, { ...options, signal: controller.signal });
    } catch {
        return null;
    } finally {
        clearTimeout(timer);
    }
}

/** Fetch a plain-text file from the repo and split into non-empty lines. */
async function fetchLines(path: string): Promise<string[]> {
    const res = await fetchWithTimeout(`${REPO}${path}`);
    if (!res?.ok) return [];
    const text = await res.text().catch(() => '');
    return text.split('\n').map(l => l.trim()).filter(Boolean);
}

/** Sleep for `ms` milliseconds. */
const sleep = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms));

/** Chunk an array into pages of `size`. */
function chunks<T>(arr: T[], size: number): T[][] {
    const out: T[][] = [];
    for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
    return out;
}

// ─── Rate-limiter ────────────────────────────────────────────────────────────

/**
 * Simple sliding-window rate limiter.
 * Call `acquire()` before each request; it blocks until a slot is free.
 */
class RateLimiter {
    private timestamps: number[] = [];

    constructor(
        private readonly maxRequests: number,
        private readonly windowMs:    number,
    ) {}

    async acquire(): Promise<void> {
        while (true) {
            const now = Date.now();
            this.timestamps = this.timestamps.filter(t => now - t < this.windowMs);

            if (this.timestamps.length < this.maxRequests) {
                this.timestamps.push(now);
                return;
            }

            const oldest  = this.timestamps[0];
            const waitMs  = this.windowMs - (now - oldest) + 10;
            console.log(`  [rate-limit] window full — waiting ${Math.ceil(waitMs / 1000)}s`);
            await sleep(waitMs);
        }
    }
}

const rateLimiter = new RateLimiter(REQUEST_LIMIT, REQUEST_WINDOW);

// ─── Geolocation ─────────────────────────────────────────────────────────────

/** Returns true if an entry is missing usable geo data. */
const isIncomplete = (e: GeoEntry) =>
    e.country === 'Unknown' || (e.latitude === 0 && e.longitude === 0);

async function fallbackGeoLocation(ip: string): Promise<GeoEntry | null> {
    const res = await fetchWithTimeout(`${IP_API_SINGLE}/${ip}?fields=8386`);

    if (!res?.ok) {
        console.warn(`  [fallback] failed for ${ip} — HTTP ${res?.status ?? 'timeout'}`);
        return null;
    }

    const data: IpApiSingleResponse = await res.json();

    if (data.status !== 'success') {
        console.warn(`  [fallback] ip-api rejected ${ip} — status: ${data.status}`);
        return null;
    }

    return {
        ip,
        country:   data.countryCode || 'Unknown',
        latitude:  data.lat ?? 0,
        longitude: data.lon ?? 0,
    };
}

async function processBatch(batch: string[], batchIndex: number, total: number): Promise<GeoEntry[]> {
    for (let attempt = 1; attempt <= RETRY_LIMIT; attempt++) {
        await rateLimiter.acquire();

        const res = await fetchWithTimeout(IP_API_BATCH, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(batch),
        });

        if (res?.ok) {
            const data: IpApiItem[] = await res.json();
            const entries: GeoEntry[] = data.map(item => ({
                ip:        item.query,
                country:   item.countryCode || 'Unknown',
                latitude:  item.lat ?? 0,
                longitude: item.lon ?? 0,
            }));

            // Enrich any entries ip-api couldn't fully resolve
            const incomplete = entries.filter(isIncomplete);
            if (incomplete.length > 0) {
                console.log(`  [batch ${batchIndex}/${total}] enriching ${incomplete.length} incomplete entries via fallback`);
                const enriched = await Promise.all(incomplete.map(e => fallbackGeoLocation(e.ip)));
                const enrichMap = new Map(enriched.filter((r): r is GeoEntry => r !== null).map(r => [r.ip, r]));
                const resolved = entries.map(e => enrichMap.get(e.ip) ?? e);
                console.log(`  [batch ${batchIndex}/${total}] ✓ ${resolved.length} IPs (${enrichMap.size} enriched via fallback)`);
                return resolved;
            }

            console.log(`  [batch ${batchIndex}/${total}] ✓ ${entries.length} IPs via ip-api`);
            return entries;
        }

        const status = res?.status;

        if (status === 429) {
            const backoff = attempt * 15_000;
            console.warn(`  [batch ${batchIndex}/${total}] rate-limited (attempt ${attempt}/${RETRY_LIMIT}) — backing off ${backoff / 1000}s`);
            await sleep(backoff);
            continue;
        }

        if (status === 422) {
            console.error(`  [batch ${batchIndex}/${total}] unprocessable (422) — skipping`);
            break;
        }

        // Network error / timeout / unexpected status → fall through to fallback
        console.warn(`  [batch ${batchIndex}/${total}] unexpected status ${status ?? 'timeout'} — using fallback`);
        break;
    }

    // ip-api exhausted — fall back to ipwho.is per-IP
    console.log(`  [batch ${batchIndex}/${total}] falling back to ipwho.is for ${batch.length} IPs`);
    const fallbacks = await Promise.all(batch.map(ip => fallbackGeoLocation(ip)));
    const succeeded = fallbacks.filter((r): r is GeoEntry => r !== null);
    console.log(`  [batch ${batchIndex}/${total}] fallback: ${succeeded.length}/${batch.length} resolved`);
    return succeeded;
}

async function geoLocationBatch(ips: string[]): Promise<GeoEntry[]> {
    const batches = chunks(ips, BATCH_SIZE);
    console.log(`Processing ${ips.length} IPs across ${batches.length} batches`);

    const results: GeoEntry[] = [];
    for (let i = 0; i < batches.length; i++) {
        const entries = await processBatch(batches[i], i + 1, batches.length);
        results.push(...entries);
    }
    return results;
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
    const now   = new Date();
    const year  = now.getUTCFullYear().toString();
    const month = String(now.getUTCMonth() + 1).padStart(2, '0');
    const today = `${year}-${month}-${String(now.getUTCDate()).padStart(2, '0')}`;

    await fs.mkdir('out/active',                          { recursive: true });
    await fs.mkdir(`out/history/${year}/${month}/${today}`, { recursive: true });

    console.log('Fetching node lists…');
    const [relays, exits, guards] = await Promise.all([
        fetchLines('active/relay-nodes.txt'),
        fetchLines('active/exit-nodes.txt'),
        fetchLines('active/guard-nodes.txt'),
    ]);

    const uniqueIPs = [...new Set([...relays, ...exits, ...guards])];
    console.log(`Unique IPs to geolocate: ${uniqueIPs.length}`);

    const geoResults = await geoLocationBatch(uniqueIPs);
    console.log(`Done — ${geoResults.length} entries resolved`);

    const json = JSON.stringify(geoResults);
    await Promise.all([
        fs.writeFile('out/active/geo-location.json',                          json),
        fs.writeFile(`out/history/${year}/${month}/${today}/geo-location.json`, json),
    ]);

    console.log('Output written.');
}

void main().catch(err => {
    console.error('Fatal:', err);
    process.exit(1);
});
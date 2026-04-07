/**
 * Bunny Edge Script — Mooindagcounter
 *
 * Features:
 *  - Rate limiting on POST /increment (max 5 requests per IP per minute)
 *  - www → apex redirect
 *  - Cache-Control headers for dynamic routes
 *  - No-cache enforcement for POST requests
 */

import * as BunnySDK from "https://esm.sh/@bunny.net/edgescript-sdk@0.10.0";

const RATE_LIMIT_WINDOW_MS = 60_000; // 1 minute
const RATE_LIMIT_MAX = 5;            // max requests per window per IP

// In-memory store for rate limiting (per isolate, resets on cold start)
const rateLimitStore = new Map();

function getRateLimitKey(ip) {
    return `rl:${ip}`;
}

function isRateLimited(ip) {
    const now = Date.now();
    const key = getRateLimitKey(ip);
    const entry = rateLimitStore.get(key);

    if (!entry || now - entry.windowStart > RATE_LIMIT_WINDOW_MS) {
        rateLimitStore.set(key, { windowStart: now, count: 1 });
        return false;
    }

    if (entry.count >= RATE_LIMIT_MAX) {
        return true;
    }

    entry.count++;
    return false;
}

BunnySDK.serve({
    async fetch(request) {
        const url = new URL(request.url);

        // 1. www → apex redirect
        if (url.hostname.startsWith("www.")) {
            url.hostname = url.hostname.replace(/^www\./, "");
            return Response.redirect(url.toString(), 301);
        }

        // 2. Rate limiting on POST /increment
        if (request.method === "POST" && url.pathname === "/increment") {
            const clientIp =
                request.headers.get("CF-Connecting-IP") ||
                request.headers.get("X-Forwarded-For")?.split(",")[0].trim() ||
                "unknown";

            if (isRateLimited(clientIp)) {
                return new Response("Too Many Requests", {
                    status: 429,
                    headers: { "Retry-After": "60" },
                });
            }
        }

        // 3. Forward request to origin
        const response = await fetch(request);

        // 4. Force no-cache for dynamic routes
        const dynamicRoutes = ["/increment", "/overview", "/api/"];
        const isDynamic = dynamicRoutes.some((r) => url.pathname.startsWith(r));

        if (isDynamic || request.method === "POST") {
            const headers = new Headers(response.headers);
            headers.set("Cache-Control", "no-store, no-cache, must-revalidate");
            return new Response(response.body, {
                status: response.status,
                headers,
            });
        }

        return response;
    },
});

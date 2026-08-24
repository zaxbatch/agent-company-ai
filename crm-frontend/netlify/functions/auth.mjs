// ============================================================================
// /api/auth/* — login, logout, session check
// ============================================================================
import { createSession, cookieHeader, clearCookieHeader, verifyPassphrase, verifySession, readCookie } from "./lib/auth.mjs";

const JSON_HEADERS = { "Content-Type": "application/json", "Cache-Control": "no-store" };

function ok(body, headers = {}) {
  return { statusCode: 200, headers: { ...JSON_HEADERS, ...headers }, body: JSON.stringify(body) };
}
function fail(message, status = 400) {
  return { statusCode: status, headers: JSON_HEADERS, body: JSON.stringify({ error: message }) };
}

function parseBody(event) {
  try { return JSON.parse(event.body || "{}"); } catch { return {}; }
}

export async function handler(event) {
  if (event.httpMethod === "OPTIONS") return { statusCode: 204, headers: { "Access-Control-Allow-Methods": "POST,GET,OPTIONS" }, body: "" };

  const url = new URL(event.rawUrl || `https://x${event.path}`);
  const path = url.pathname.replace(/\/+$/, "");

  try {
    if (path === "/api/auth/login" && event.httpMethod === "POST") {
      const { email, passphrase } = parseBody(event);
      if (!email || !String(email).includes("@")) return fail("A valid email is required", 400);
      if (!verifyPassphrase(passphrase)) return fail("Invalid email or passphrase", 401);
      const token = createSession(String(email).toLowerCase().trim());
      return ok({ ok: true, email: String(email).toLowerCase().trim() }, { "Set-Cookie": cookieHeader(token) });
    }

    if (path === "/api/auth/logout" && (event.httpMethod === "POST" || event.httpMethod === "GET")) {
      return ok({ ok: true }, { "Set-Cookie": clearCookieHeader() });
    }

    if (path === "/api/auth/me" && event.httpMethod === "GET") {
      const payload = verifySession(readCookie(event));
      if (!payload) return fail("Unauthorized", 401);
      return ok({ ok: true, email: payload.email });
    }

    return fail("Not found", 404);
  } catch (e) {
    return fail(e.message || "Server error", e.status || 500);
  }
}

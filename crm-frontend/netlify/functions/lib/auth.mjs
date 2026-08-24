// ============================================================================
// Internal session auth — HMAC-signed cookie (same pattern as the Z-Dot
// dashboard server). The passphrase lives in CRM_PASSPHRASE (Netlify env).
// No secrets ever reach the browser; the cookie only carries {email, exp}.
// ============================================================================
import crypto from "crypto";

export const COOKIE_NAME = "crm_session";
export const SESSION_TTL_SECONDS = 12 * 60 * 60; // 12h

function secret() {
  const s = process.env.CRM_SESSION_SECRET;
  if (!s) throw Object.assign(new Error("CRM_SESSION_SECRET not configured"), { status: 500 });
  return s;
}

export function signSession(payload) {
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  const sig = crypto.createHmac("sha256", secret()).update(body).digest("base64url");
  return `${body}.${sig}`;
}

export function verifySession(token) {
  if (!token) return null;
  const [body, sig] = token.split(".");
  if (!body || !sig) return null;
  const expected = crypto.createHmac("sha256", secret()).update(body).digest("base64url");
  if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(expected))) return null;
  try {
    const payload = JSON.parse(Buffer.from(body, "base64url").toString("utf8"));
    if (!payload.exp || Date.now() > payload.exp * 1000) return null;
    return payload;
  } catch {
    return null;
  }
}

export function createSession(email) {
  const payload = { email, exp: Math.floor(Date.now() / 1000) + SESSION_TTL_SECONDS };
  return signSession(payload);
}

export function cookieHeader(token) {
  return `${COOKIE_NAME}=${token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${SESSION_TTL_SECONDS}; Secure`;
}

export function clearCookieHeader() {
  return `${COOKIE_NAME}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0`;
}

export function readCookie(event) {
  const h = event.headers?.cookie || event.headers?.Cookie || "";
  const m = h.match(new RegExp(`(?:^|;\\s*)${COOKIE_NAME}=([^;]+)`));
  return m ? decodeURIComponent(m[1]) : null;
}

export function verifyPassphrase(given) {
  const expected = process.env.CRM_PASSPHRASE || "";
  if (!expected) throw Object.assign(new Error("CRM_PASSPHRASE not configured"), { status: 500 });
  if (!given) return false;
  const a = Buffer.from(String(given));
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

export function requireSession(event) {
  const payload = verifySession(readCookie(event));
  if (!payload) {
    const e = new Error("Unauthorized");
    e.status = 401;
    throw e;
  }
  return payload;
}

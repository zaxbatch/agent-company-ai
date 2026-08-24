// ============================================================================
// /api/* — CRM data API (contacts, kpis, queue). Every route requires a valid
// session cookie (SC-5). All HubSpot traffic goes through lib/hubspot.mjs with
// the token server-side only.
// ============================================================================
import {
  searchAllContacts, getContact, updateContact, computeKpis, computeQueue, isStale,
} from "./lib/hubspot.mjs";
import { requireSession } from "./lib/auth.mjs";

const JSON_HEADERS = { "Content-Type": "application/json", "Cache-Control": "no-store" };

function ok(body, status = 200) {
  return { statusCode: status, headers: JSON_HEADERS, body: JSON.stringify(body) };
}
function fail(message, status = 400) {
  return { statusCode: status, headers: JSON_HEADERS, body: JSON.stringify({ error: message }) };
}

function parseBody(event) {
  try { return JSON.parse(event.body || "{}"); } catch { return {}; }
}

export async function handler(event) {
  if (event.httpMethod === "OPTIONS") return { statusCode: 204, body: "" };

  let session;
  try {
    session = requireSession(event);
  } catch (e) {
    return fail("Unauthorized", 401);
  }

  const url = new URL(event.rawUrl || `https://x${event.path}`);
  const path = url.pathname.replace(/\/+$/, "");
  const q = url.searchParams;
  const actor = session.email || "team";

  try {
    // ---- GET /api/contacts?id= — detail -------------------------------------
    if (path === "/api/contacts" && event.httpMethod === "GET" && q.get("id")) {
      const c = await getContact(q.get("id"));
      return ok({ ...c, stale: isStale(c) });
    }
        if (path === "/api/contacts" && event.httpMethod === "GET") {
      const search = q.get("q") || "";
      const status = q.get("status") || "";
      const tag = q.get("tag") || "";
      const page = Math.max(1, Number(q.get("page") || 1));
      const per = Math.min(100, Math.max(1, Number(q.get("limit") || 50)));
      const includeChurned = q.get("includeChurned") === "1";

      let all = await searchAllContacts({ q: search });
      if (status) all = all.filter((c) => c.stage === status);
      if (tag) all = all.filter((c) => c.tags.includes(tag));
      if (!includeChurned) all = all.filter((c) => c.stage !== "churned");

      all.sort((a, b) => (b.createdAt || "").localeCompare(a.createdAt || ""));
      const total = all.length;
      const start = (page - 1) * per;
      const results = all.slice(start, start + per).map((c) => ({ ...c, stale: isStale(c) }));
      return ok({ total, page, per, results });
    }

    // ---- GET /api/contacts?id= — detail -------------------------------------
    if (path === "/api/contacts" && event.httpMethod === "GET" && q.get("id")) {
      const c = await getContact(q.get("id"));
      return ok({ ...c, stale: isStale(c) });
    }

    // ---- PATCH /api/contacts?id= — update (stage, tags, next, prio, src, notes)
    if (path === "/api/contacts" && event.httpMethod === "PATCH") {
      const id = q.get("id");
      if (!id) return fail("id required", 400);
      const patch = parseBody(event);
      const allowed = ["stage", "tags", "next", "prio", "src", "notes"];
      for (const k of Object.keys(patch)) {
        if (!allowed.includes(k)) return fail(`Field not writable: ${k}`, 400);
      }
      const c = await updateContact(id, patch, actor);
      return ok({ ...c, stale: isStale(c) });
    }

    // ---- POST /api/contacts?id=&action=note — append note --------------------
    // ---- POST /api/contacts?id=&action=followup — clear next touch ----------
    if (path === "/api/contacts" && event.httpMethod === "POST") {
      const id = q.get("id");
      const action = q.get("action");
      if (!id || !action) return fail("id and action required", 400);
      const body = parseBody(event);
      if (action === "note") {
        if (!body.text || !String(body.text).trim()) return fail("text required", 400);
        const c = await updateContact(id, { notes: String(body.text).trim() }, actor);
        return ok({ ...c, stale: isStale(c) });
      }
      if (action === "followup") {
        // mark follow-up done: clear next touch + log it
        const c = await updateContact(id, { next: null, notes: `Follow-up completed.` }, actor);
        return ok({ ...c, stale: isStale(c) });
      }
      return fail("Unknown action", 400);
    }

    // ---- GET /api/kpis — dashboard aggregates ---------------------------------
    if (path === "/api/kpis" && event.httpMethod === "GET") {
      const all = await searchAllContacts();
      return ok(computeKpis(all));
    }

    // ---- GET /api/queue — follow-up queue --------------------------------------
    if (path === "/api/queue" && event.httpMethod === "GET") {
      const all = await searchAllContacts();
      const queue = computeQueue(all);
      return ok({ total: queue.length, overdue: queue.filter((c) => c.overdue).length, results: queue.slice(0, 200) });
    }

    return fail("Not found", 404);
  } catch (e) {
    return fail(e.message || "Server error", e.status || 500);
  }
}

// ============================================================================
// HubSpot REST client — SERVER-SIDE ONLY.
// The HUBSPOT_ACCESS_TOKEN lives in Netlify env vars and is NEVER exposed to
// the browser. All CRM reads/writes flow through this module.
//
// Verified against our account 2026-08-24:
//   - GET /search, GET by email, POST, PATCH, DELETE on contacts: OK
//   - Batch upsert endpoint: 400 VALIDATION_ERROR -> use per-contact flow
//   - Deals/pipelines/owners endpoints: 403 (token lacks those scopes)
//   - Creating custom properties: 403 (token lacks crm.schemas.contacts.write)
//     => DATA MODEL DECISION: the CRM model maps onto STANDARD writable
//        properties (see ENVELOPE below). No custom properties required.
//
// Rate-limit strategy (HubSpot limits, free tier):
//   - Burst: ~100 req / 10s (all endpoints)
//   - Search API: 4 req/s, max ~200 records/response, 10k result cap
//   - Daily: ~250k req/day (free tier) — trivially above our usage
//   - On 429: exponential backoff + jitter, retry up to 4 times
//   - Search calls are serialized through a promise queue so the UI never
//     fires parallel search requests that trip the 4 req/s burst.
// ============================================================================

const HUBSPOT_API = "https://api.hubapi.com";
const MAX_RETRIES = 4;
const BASE_BACKOFF_MS = 250;

// ---- 429 retry with exponential backoff + jitter ---------------------------
export function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

export async function hsRequest(path, { method = "GET", body, retries = MAX_RETRIES } = {}) {
  const token = process.env.HUBSPOT_ACCESS_TOKEN;
  if (!token) throw Object.assign(new Error("HUBSPOT_ACCESS_TOKEN not configured"), { status: 500 });

  let url = path.startsWith("http") ? path : `${HUBSPOT_API}${path}`;
  let lastErr = null;
  for (let attempt = 0; attempt <= retries; attempt++) {
    const res = await fetch(url, {
      method,
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });

    if (res.status === 429) {
      const retryAfter = Number(res.headers.get("Retry-After") || 0);
      const wait = retryAfter > 0 ? retryAfter * 1000 : BASE_BACKOFF_MS * 2 ** attempt + Math.random() * 200;
      await sleep(wait);
      lastErr = new Error(`RATE_LIMIT after ${attempt + 1} attempts`);
      continue;
    }
    if (res.status >= 500) {
      await sleep(BASE_BACKOFF_MS * 2 ** attempt + Math.random() * 200);
      lastErr = new Error(`HubSpot ${res.status}`);
      continue;
    }
    const text = await res.text();
    const data = text ? JSON.parse(text) : {};
    if (!res.ok) {
      const msg = data?.message || `HubSpot ${res.status}`;
      const err = new Error(msg);
      err.status = res.status;
      err.category = data?.category;
      err.correlationId = data?.correlationId;
      throw err;
    }
    return data;
  }
  const err = new Error(`HubSpot request failed after retries: ${lastErr?.message}`);
  err.status = 502;
  throw err;
}

// ---- Search serialization (protect the 4 req/s search burst) ---------------
let searchQueue = Promise.resolve();
export function enqueueSearch(fn) {
  const run = searchQueue.then(fn, fn);
  searchQueue = run.catch(() => {});
  return run;
}

// ============================================================================
// DATA MODEL — ZDot envelope
// ----------------------------------------------------------------------------
// The token cannot create custom properties (403), so the CRM model lives in
// TWO standard, writable contact properties:
//
//   hs_cross_account_note        -> JSON envelope with the CRM fields:
//        { stage, tags[], next, prio, src, history[] }
//   hs_content_membership_notes  -> notes timeline (append-only plain text)
//
// HubSpot stays the system of record: everything persists via the Contacts API.
// The envelope keeps the kanban/funnel state on the contact object itself, so
// HubSpot search/list can still surface it and no sidecar DB is needed.
// ============================================================================

export const STAGES = ["lead", "prospect", "customer", "churned"];
export const PRIORITIES = ["High", "Medium", "Low"];
export const TAGS = ["zdot", "lpt", "both", "snowsnakes", "spread-da-word", "snitch", "outreach"];
export const SOURCES = ["website", "referral", "cold outreach", "prospect campaign", "snowsnakes", "event", "other"];

const ENVELOPE_PROP = "hs_cross_account_note";
const NOTES_PROP = "hs_content_membership_notes";

export function normalizeTags(raw) {
  if (!raw) return [];
  const arr = Array.isArray(raw) ? raw : String(raw).split(",");
  return [...new Set(
    arr.map((t) => String(t).trim().toLowerCase().replace(/^#/, ""))
       .filter((t) => t.length > 0)
  )];
}

export function decodeEnvelope(raw) {
  const empty = { stage: "lead", tags: [], next: null, prio: "Medium", src: null, history: [] };
  if (!raw) return empty;
  try {
    const o = JSON.parse(String(raw));
    return {
      stage: STAGES.includes(o.stage) ? o.stage : "lead",
      tags: normalizeTags(o.tags),
      next: /^\d{4}-\d{2}-\d{2}$/.test(o.next || "") ? o.next : null,
      prio: PRIORITIES.includes(o.prio) ? o.prio : "Medium",
      src: typeof o.src === "string" && o.src ? o.src : null,
      history: Array.isArray(o.history) ? o.history.slice(-50) : [],
    };
  } catch {
    return empty;
  }
}

export function encodeEnvelope(e) {
  const env = decodeEnvelope(e); // sanitize
  return JSON.stringify(env);
}

export function parseNotes(raw) {
  // notes timeline: "[YYYY-MM-DD HH:MM] Author: text" lines
  if (!raw) return [];
  return String(raw).split("\n").map((l) => l.trim()).filter((l) => l.length > 0)
    .map((line) => {
      const m = line.match(/^\[([^\]]+)\]\s*(.*)$/);
      return m ? { at: m[1], text: m[2] } : { at: null, text: line };
    });
}

export function appendNote(existingRaw, text, author) {
  const stamp = new Date().toISOString().slice(0, 16).replace("T", " ");
  const who = (author || "team").trim() || "team";
  const line = `[${stamp}] ${who}: ${String(text).trim()}`;
  const prev = existingRaw ? String(existingRaw).trim() : "";
  return prev ? `${prev}\n${line}` : line;
}

// ---- Contact search --------------------------------------------------------
export const CONTACT_PROPERTIES = [
  "email", "firstname", "lastname", "phone", "company", "jobtitle", "website",
  "createdate", "hs_lastmodifieddate", "hs_lead_status", "hs_analytics_source",
  "hs_analytics_source_data_1", "hubspot_owner_id", "notes_last_updated",
  ENVELOPE_PROP, NOTES_PROP,
];

export function mapContact(c) {
  const p = c.properties || {};
  const env = decodeEnvelope(p[ENVELOPE_PROP]);
  const first = p.firstname || "";
  const last = p.lastname || "";
  const name = [first, last].filter(Boolean).join(" ") || p.company || p.email || "(no name)";
  const src = env.src || p.hs_analytics_source || p.hs_analytics_source_data_1 || null;
  const lastTouch = p.notes_last_updated || p.hs_lastmodifieddate || null;
  return {
    id: p.hs_object_id || c.id,
    email: p.email || null,
    name,
    firstname: first,
    lastname: last,
    company: p.company || null,
    phone: p.phone || null,
    jobtitle: p.jobtitle || null,
    website: p.website || null,
    stage: env.stage,
    tags: env.tags,
    notes: p[NOTES_PROP] || "",
    notesParsed: parseNotes(p[NOTES_PROP]),
    nextFollowUp: env.next,
    priority: env.prio,
    source: src,
    ownerId: p.hubspot_owner_id || null,
    createdAt: p.createdate || null,
    updatedAt: p.hs_lastmodifieddate || null,
    lastTouch,
    history: env.history,
  };
}

function searchBody({ q, limit = 200, after }) {
  const filterGroups = [];
  if (q && q.trim()) {
    filterGroups.push(
      { filters: [{ propertyName: "email", operator: "CONTAINS_TOKEN", value: q.trim() }] },
      { filters: [{ propertyName: "firstname", operator: "CONTAINS_TOKEN", value: q.trim() }] },
      { filters: [{ propertyName: "lastname", operator: "CONTAINS_TOKEN", value: q.trim() }] },
      { filters: [{ propertyName: "company", operator: "CONTAINS_TOKEN", value: q.trim() }] }
    );
  }
  const body = { limit: Math.min(limit, 200), properties: CONTACT_PROPERTIES, filterGroups };
  if (after) body.after = String(after);
  return body;
}

export async function searchAllContacts({ q } = {}) {
  // Fetch all pages (cap 10k like HubSpot). App-level filters (status/tag)
  // run in memory — with our volume (<1k) this is one or two search calls and
  // keeps the custom-envelope filters exact.
  let all = [];
  let after = null;
  do {
    const body = searchBody({ q, after });
    const data = await enqueueSearch(() =>
      hsRequest("/crm/v3/objects/contacts/search", { method: "POST", body })
    );
    all = all.concat((data.results || []).map(mapContact));
    after = data.paging?.next?.after || null;
    if (all.length >= 10000) break;
  } while (after);
  return all;
}

export async function getContact(id) {
  const data = await hsRequest(`/crm/v3/objects/contacts/${id}?properties=${CONTACT_PROPERTIES.join(",")}`);
  return mapContact(data);
}

export async function getContactByEmail(email) {
  const data = await hsRequest(`/crm/v3/objects/contacts/${encodeURIComponent(email)}?idProperty=email&properties=${CONTACT_PROPERTIES.join(",")}`);
  return mapContact(data);
}

// ---- Contact update (whitelist enforced server-side) -----------------------
// Accepts UI-model keys and encodes them into HubSpot standard properties.
const STAGE_HISTORY_MAX = 50;

export async function updateContact(id, patch, actor = "team") {
  const props = {};
  const current = await getContact(id);

  if (patch.stage !== undefined) {
    const stage = String(patch.stage).toLowerCase();
    if (!STAGES.includes(stage)) throw Object.assign(new Error(`Invalid stage: ${stage}`), { status: 400 });
    const env = { ...current, stage };
    if (stage !== current.stage) {
      env.history = (current.history || []).concat([{
        s: stage, at: new Date().toISOString(), by: actor,
      }]).slice(-STAGE_HISTORY_MAX);
    }
    props[ENVELOPE_PROP] = encodeEnvelope(env);
  }

  if (patch.tags !== undefined) {
    const env = { ...current, tags: normalizeTags(patch.tags) };
    props[ENVELOPE_PROP] = encodeEnvelope(env);
  }
  if (patch.next !== undefined) {
    const v = patch.next ? String(patch.next) : null;
    const env = { ...current, next: v };
    props[ENVELOPE_PROP] = encodeEnvelope(env);
  }
  if (patch.prio !== undefined) {
    const v = String(patch.prio);
    if (!PRIORITIES.includes(v)) throw Object.assign(new Error(`Invalid priority: ${v}`), { status: 400 });
    const env = { ...current, prio: v };
    props[ENVELOPE_PROP] = encodeEnvelope(env);
  }
  if (patch.src !== undefined) {
    const env = { ...current, src: patch.src ? String(patch.src) : null };
    props[ENVELOPE_PROP] = encodeEnvelope(env);
  }
  if (patch.notes !== undefined) {
    props[NOTES_PROP] = appendNote(current.notes, patch.notes, actor);
  }

  if (Object.keys(props).length === 0) return current;
  const data = await hsRequest(`/crm/v3/objects/contacts/${id}`, { method: "PATCH", body: { properties: props } });
  return mapContact(data);
}

export async function createContact(contact) {
  const data = await hsRequest("/crm/v3/objects/contacts", { method: "POST", body: { properties: contact } });
  return mapContact(data);
}

export async function deleteContact(id) {
  await hsRequest(`/crm/v3/objects/contacts/${id}`, { method: "DELETE" });
  return { deleted: true, id };
}

// ---- Stale definition (>=7 days since last touch) --------------------------
export function isStale(contact, now = new Date()) {
  const t = contact.lastTouch ? new Date(contact.lastTouch) : null;
  if (!t) return true; // never touched = stale
  return (now - t) > 7 * 24 * 60 * 60 * 1000;
}

// ---- Dashboard / queue aggregation (in-memory over the fetched set) --------
export function daysAgoIso(n, now = new Date()) {
  const d = new Date(now.getTime() - n * 24 * 60 * 60 * 1000);
  return d.toISOString();
}

export function computeKpis(contacts, now = new Date()) {
  const total = contacts.length;
  const weekAgo = daysAgoIso(7, now);
  const leadsThisWeek = contacts.filter((c) => c.createdAt && c.createdAt >= weekAgo).length;
  const byStage = { lead: 0, prospect: 0, customer: 0, churned: 0 };
  for (const c of contacts) byStage[c.stage] = (byStage[c.stage] || 0) + 1;

  const tagCounts = {};
  for (const c of contacts) for (const t of c.tags) tagCounts[t] = (tagCounts[t] || 0) + 1;

  const stale = contacts.filter((c) => isStale(c, now)).length;
  const funnel = {
    lead: byStage.lead,
    prospect: byStage.prospect,
    customer: byStage.customer,
    churned: byStage.churned,
    leadToProspectPct: total ? Math.round((byStage.prospect / total) * 100) : 0,
    leadToCustomerPct: total ? Math.round((byStage.customer / total) * 100) : 0,
  };
  return { total, leadsThisWeek, byStage, byTag: tagCounts, stale, funnel };
}

export function computeQueue(contacts, now = new Date()) {
  const today = now.toISOString().slice(0, 10);
  return contacts
    .filter((c) => c.stage !== "churned" && c.nextFollowUp)
    .map((c) => ({ ...c, overdue: c.nextFollowUp < today, dueToday: c.nextFollowUp === today }))
    .sort((a, b) => {
      // overdue first, then date asc, then priority High > Medium > Low
      if (a.overdue !== b.overdue) return a.overdue ? -1 : 1;
      if (a.nextFollowUp !== b.nextFollowUp) return a.nextFollowUp < b.nextFollowUp ? -1 : 1;
      const p = { High: 0, Medium: 1, Low: 2 };
      return (p[a.priority] ?? 1) - (p[b.priority] ?? 1);
    });
}

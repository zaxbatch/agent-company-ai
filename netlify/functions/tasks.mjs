// Z-Dot Team Checklist API - Netlify Function backed by Netlify Blobs.
import { getStore } from "@netlify/blobs";
import { SEED } from "./seed.js";

const KEY = "tasks";
const VALID_STATUSES = new Set(["pending","assigned","in_progress","review","done","failed","cancelled"]);
const PRIO = {0:0,1:1,2:2,3:3};

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function ok(body, status = 200) {
  return { statusCode: status, headers: { "Content-Type": "application/json", ...CORS }, body: JSON.stringify(body) };
}
function err(msg, status = 400) {
  return { statusCode: status, headers: { "Content-Type": "application/json", ...CORS }, body: JSON.stringify({ error: msg }) };
}
function now() { return new Date().toISOString(); }

async function load(store) {
  const existing = await store.get(KEY);
  if (existing) {
    try { return JSON.parse(existing); } catch { return null; }
  }
  return null;
}

async function save(store, tasks) {
  await store.set(KEY, JSON.stringify(tasks));
}

export async function handler(event) {
  if (event.httpMethod === "OPTIONS") return { statusCode: 204, headers: CORS, body: "" };

  const store = getStore({ name: "checklist" });
  let tasks = await load(store);
  if (tasks === null) {
    tasks = SEED;
    await save(store, tasks);
  }

  const url = new URL(event.rawUrl || `https://x${event.path}`);
  const path = url.pathname;
  const m = path.match(/^\/api\/tasks(?:\/([^/]+))?$/);
  if (!m) return err("not found", 404);

  const id = m[1];
  const method = event.httpMethod;

  if (method === "GET" && !id) return ok(tasks);

  if (method === "POST" && !id) {
    let body;
    try { body = JSON.parse(event.body || "{}"); } catch { return err("invalid JSON"); }
    const desc = (body.description || "").trim();
    if (!desc) return err("description is required");
    const task = {
      id: Math.random().toString(16).slice(2, 14),
      description: desc,
      assignee: body.assignee || null,
      priority: PRIO[body.priority] ?? 0,
      status: body.assignee ? "assigned" : "pending",
      result: null,
      blocker: body.blocker || null,
      created_at: now(),
      updated_at: now(),
      last_checked_at: null,
    };
    tasks.push(task);
    await save(store, tasks);
    return ok(task, 201);
  }

  if ((method === "PATCH" || method === "DELETE") && id) {
    const idx = tasks.findIndex(t => t.id === id);
    if (idx === -1) return err("no task with id " + id, 404);
    if (method === "DELETE") {
      tasks.splice(idx, 1);
      await save(store, tasks);
      return { statusCode: 204, headers: CORS, body: "" };
    }
    let body;
    try { body = JSON.parse(event.body || "{}"); } catch { return err("invalid JSON"); }
    const t = tasks[idx];
    if (body.status !== undefined) {
      if (!VALID_STATUSES.has(body.status)) return err("invalid status: " + body.status);
      t.status = body.status;
    }
    if (body.assignee !== undefined) t.assignee = body.assignee;
    if (body.description !== undefined) {
      const d = (body.description || "").trim();
      if (!d) return err("description cannot be empty");
      t.description = d;
    }
    if (body.result !== undefined) t.result = body.result;
    if (body.blocker !== undefined) t.blocker = body.blocker;
    if (body.last_checked_at !== undefined) t.last_checked_at = body.last_checked_at;
    t.updated_at = now();
    tasks[idx] = t;
    await save(store, tasks);
    return ok(t);
  }

  return err("not found", 404);
}

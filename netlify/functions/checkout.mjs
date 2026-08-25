// Z-Dot Checkout — Stripe Checkout Session (Option 2, prebuilt form)
// POST /api/checkout  {price_id, mode, contact_id?, source?}
// Returns {url} — redirect the browser there. Secret key stays server-side.
import Stripe from "stripe";

export async function handler(event) {
  if (event.httpMethod === "OPTIONS") return { statusCode: 204, headers: cors() };
  if (event.httpMethod !== "POST") return err("POST only", 405);
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) return err("STRIPE_SECRET_KEY not set", 500);

  let body;
  try { body = JSON.parse(event.body || "{}"); } catch { return err("bad json", 400); }
  const priceId = body.price_id;
  if (!priceId) return err("price_id required", 400);

  const stripe = new Stripe(key);
  try {
    const session = await stripe.checkout.sessions.create({
      mode: body.mode === "subscription" ? "subscription" : "payment",
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: (body.success_url || "https://tasks.zdotllc.com/progress") + "?paid=1",
      cancel_url: body.cancel_url || "https://tasks.zdotllc.com/progress",
      metadata: {
        contact_id: body.contact_id || "",
        source: body.source || "checkout",
      },
    });
    return ok({ url: session.url, id: session.id });
  } catch (e) {
    return err("stripe: " + (e.message || e), 500);
  }
}

const cors = () => ({
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
});
const ok = (d) => ({ statusCode: 200, headers: { "Content-Type": "application/json", ...cors() }, body: JSON.stringify(d) });
const err = (m, s = 400) => ({ statusCode: s, headers: { "Content-Type": "application/json", ...cors() }, body: JSON.stringify({ error: m }) });

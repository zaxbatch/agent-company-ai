#!/usr/bin/env python3
"""Inject the MilkUps/play email-capture block into the play pages.

Idempotent: re-running replaces the existing block rather than duplicating it.
The block posts to /lead.php (same origin) which stores to our own list AND
creates a HubSpot contact.

Usage: python3 scripts/inject_lead_capture.py [--dry-run]
"""
from __future__ import annotations
import argparse, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BLOCK = """
<!-- ZDOT-LEAD-CAPTURE:start -->
<section class="zdlc" id="get-tracks">
  <h2>Get the new tracks first</h2>
  <p>Drop your email and we&rsquo;ll send new MilkUps tracks, drops and free downloads
     before they go anywhere else. No spam, unsubscribe any time.</p>
  <form class="zdlc-form" novalidate>
    <input type="email" name="email" placeholder="you@email.com" required
           autocomplete="email" aria-label="Your email address">
    <input type="text" name="website" tabindex="-1" autocomplete="off"
           aria-hidden="true" class="zdlc-hp">
    <button type="submit">Send me tracks</button>
  </form>
  <div class="zdlc-msg" role="status" aria-live="polite"></div>
</section>
<style>
  .zdlc{max-width:620px;margin:34px auto 0;padding:22px;border-radius:14px;
        background:linear-gradient(135deg,#1a0d1a,#12081a);border:1px solid #e040fb44;
        font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}
  .zdlc h2{margin:0 0 8px;font-size:19px;letter-spacing:.5px;color:#ea80fc}
  .zdlc p{margin:0 0 14px;font-size:13px;line-height:1.65;color:#b08cc8}
  .zdlc-form{display:flex;gap:9px;flex-wrap:wrap}
  .zdlc-form input[type=email]{flex:1 1 220px;min-width:0;padding:13px 14px;border-radius:9px;
        border:1px solid #e040fb55;background:#0d050d;color:#f3e8ff;font:inherit;font-size:14px}
  .zdlc-form input[type=email]:focus{outline:2px solid #ea80fc;outline-offset:1px}
  .zdlc-form button{flex:0 0 auto;padding:13px 22px;border:0;border-radius:9px;cursor:pointer;
        background:#ea80fc;color:#180019;font:inherit;font-weight:700;font-size:14px;
        letter-spacing:.4px}
  .zdlc-form button:hover{filter:brightness(1.1)}
  .zdlc-form button[disabled]{opacity:.6;cursor:default}
  .zdlc-hp{position:absolute!important;left:-9999px!important;width:1px;height:1px;
        opacity:0;pointer-events:none}
  .zdlc-msg{margin-top:11px;font-size:13px;min-height:18px;color:#8fe8c8}
  .zdlc-msg.err{color:#ff8f8f}
</style>
<script>
(function(){
  var f = document.currentScript.previousElementSibling.querySelector('.zdlc-form');
  if (!f) return;
  f.addEventListener('submit', function(e){
    e.preventDefault();
    var btn = f.querySelector('button'), msg = f.parentNode.querySelector('.zdlc-msg');
    var email = f.email.value.trim();
    if (!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(email)) {
      msg.className = 'zdlc-msg err'; msg.textContent = 'Please enter a valid email.'; return;
    }
    btn.disabled = true; btn.textContent = 'Sending...';
    msg.className = 'zdlc-msg'; msg.textContent = '';
    fetch('/lead.php', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({email:email, name:'', source:'play', page:location.pathname,
                            website: f.website.value})
    }).then(function(r){ return r.json(); }).then(function(d){
      if (d && d.ok) {
        f.style.display='none';
        msg.className='zdlc-msg';
        msg.textContent = 'You\\u2019re in. Check your inbox \\u2014 new tracks land there first.';
      } else {
        throw new Error((d && d.error) || 'failed');
      }
    }).catch(function(){
      btn.disabled=false; btn.textContent='Send me tracks';
      msg.className='zdlc-msg err'; msg.textContent='That didn\\u2019t go through. Try again?';
    });
  });
})();
</script>
<!-- ZDOT-LEAD-CAPTURE:end -->
"""

MARK_START = "<!-- ZDOT-LEAD-CAPTURE:start -->"
MARK_END   = "<!-- ZDOT-LEAD-CAPTURE:end -->"

TARGETS = [
    ROOT / "content" / "milkups" / "index.html",
    ROOT / "content" / "milkups" / "album.html",
    ROOT / "content" / "milkups" / "tracker" / "index.html",
    ROOT / "content" / "milkups" / "v2-index.html",
]


def inject(path: Path, dry: bool) -> str:
    if not path.exists():
        return f"  SKIP  {path.name} (not found)"
    html = path.read_text(encoding="utf-8")
    if MARK_START in html:                      # replace existing block
        html = re.sub(re.escape(MARK_START) + ".*?" + re.escape(MARK_END), "", html,
                      flags=re.S).rstrip()
        action = "replaced"
    else:
        action = "added"
    if "</body>" in html:
        html = html.replace("</body>", BLOCK + "\n</body>", 1)
    else:
        html = html + BLOCK
    if not dry:
        path.write_text(html, encoding="utf-8")
    return f"  {action.upper():<9} {path.relative_to(ROOT)}  ({len(html)} bytes)"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    for t in TARGETS:
        print(inject(t, a.dry_run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

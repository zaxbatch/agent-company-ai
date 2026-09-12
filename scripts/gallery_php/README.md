# Approval gallery (live PHP app)

Live at **https://zerric.xyz/review/**

## Why PHP, not a static page
A static page can't share state — decisions would live in one browser. This is
server-backed so everyone sees the same decisions, and content can refresh itself.

## Files
| File | Role |
|---|---|
| `index.php` | UI. Loads items + decisions from the API, posts decisions back. |
| `api.php` | JSON API. Reads/writes `data/*.json`. |
| `htaccess.txt` | Upload as `.htaccess` (noindex + no-store on JSON). |

## API
| Call | Does |
|---|---|
| `GET  api.php?action=items` | the review manifest |
| `GET  api.php?action=decisions` | all decisions (object keyed by item id) |
| `POST api.php?action=decide` | `{id, decision, note, by}` — `decision:null` clears |
| `GET  api.php?action=refresh` | pulls new songs/doodles from the SnowSnakes API server-side |

`refresh` works server-side, so the SnowSnakes CORS restriction (which blocks a
static page from reading the API) does not apply. It dedupes on `source`
(e.g. `ss:doodle:12`), so curated items are never duplicated by a refresh.

## Deploy
FTP `151.106.97.104` as `u281804670` -> `domains/zerric.xyz/public_html/review/`
plus `data/items.json`. **Note:** subdomains do NOT serve from
`domains/<sub>/public_html/` — see TEAM-STATE docroot correction.

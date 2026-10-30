# Launch guide (step by step)

## 0. Before anything is public
- [ ] Run everything once on your own machine: `python -m pytest -q`, `cd web && npm test && npm run dev`, click through every tab on desktop and on your phone (same Wi-Fi: `npm run dev -- --host`).
- [ ] Fill every `TODO` URL in `docs/RELATED_WORK.md` after opening each link yourself. Put your real name in `CITATION.cff`.
- [ ] Record a short screen capture of the app (ScreenToGif on Windows, Kap on Mac) and add it to the README.

## 1. Put it on GitHub (you become the author)
The zip carries commits authored as "bluff-lab dev". To make the history yours and clean:
```bash
cd bluff-lab
rm -rf .git                      # Windows PowerShell: Remove-Item -Recurse -Force .git
git init -b main
git config user.name  "Your Name"
git config user.email "you@example.com"     # the email tied to your GitHub account
git add -A && git commit -m "Bluff Lab: exact Kuhn poker lab"
```
On github.com click New repository, name it `bluff-lab`, leave "Add a README" unticked, then:
```bash
git remote add origin https://github.com/<your-username>/bluff-lab.git
git push -u origin main
```
Then regenerate the numbers so FACTS.md cites YOUR commit (about 12 minutes; use Mac/Linux or WSL):
`python scripts/experiments.py && python scripts/field_demo.py && python scripts/make_figures.py && python scripts/make_facts.py`, commit, push.

## 2. Deploy the website (static)
On Cloudflare Pages, Netlify or Vercel: connect the repo, root directory `web`, build command `npm run build`, output directory `dist`, environment variable `VITE_API` = your API's URL (step 3). Without step 3 the site works but the Arena tab shows "server not running".

## 3. Deploy the arena API
Any host that runs a Dockerfile (Render, Fly.io, Railway). Use the `Dockerfile` in the repo root and set:
- `ADMIN_TOKEN` : a long random string (needed to delete entries). Never commit it.
- `ALLOWED_ORIGINS` : your site's URL, e.g. `https://bluff-lab.pages.dev`
- `FORWARDED_ALLOW_IPS` : `*` (only because the host's proxy sits in front; without it every visitor shares one IP and the rate limit hits everyone)
Free tiers often wipe the disk on restart, so the leaderboard may reset; check your host's current terms before relying on it.

## 4. Test it live
Submit an entry from the site, reload, check it appears. Delete it: `curl -X DELETE -H "X-Admin-Token: <token>" https://<api-host>/api/admin/<id>`. Try 11 submissions in a minute and expect a refusal.

## 5. Posting
Link the live site and the repo. Quote only numbers from `docs/FACTS.md`. Say "to my knowledge" before any claim about what exists elsewhere.

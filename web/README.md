# Bluff Lab web app (Milestones 3-4)
```bash
cd web
npm install
npm test        # Python<->TypeScript parity at 1e-9 (regenerate vectors: python ../scripts/golden.py)
npm run dev     # http://localhost:5173
npm run build   # static site in web/dist
```
Sections: Exploit me (12 sliders, exact exploitability, exact counter-strategy, share card), Solver lab (CFR+ in the browser), Play (opponents at 10/100/1,000/10,000 CFR+ iterations).

## Arena (Milestone 5)
```bash
# terminal 1, from the repo root (venv active)
pip install -e .[arena]
uvicorn server.app:app --port 8000
# terminal 2
cd web && npm run dev      # /api is proxied to port 8000
```
Delete an entry: `curl -X DELETE -H "X-Admin-Token: $ADMIN_TOKEN" http://localhost:8000/api/admin/<id>` (start the server with `ADMIN_TOKEN=...` set; with no token set, deletion is disabled).
Docker: `docker build -t bluff-arena . && docker run -p 8000:8000 -v arena:/data -e ADMIN_TOKEN=change-me bluff-arena`.

BASE_CSS = """
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#f1f5f9; color:#0f172a; margin:0; display:flex; height:100vh; }
.sidebar { width:220px; background:#ffffff; border-right:1px solid #cbd5f5; display:flex; flex-direction:column; }
.sidebar h2 { font-size:1.1rem; padding:1rem; margin:0; border-bottom:1px solid #cbd5f5; }
.sidebar .nav { flex:1; display:flex; flex-direction:column; }
.sidebar .nav a { padding:0.8rem 1rem; text-decoration:none; color:#0f172a; border-bottom:1px solid #e5e7eb; }
.sidebar .nav a:hover { background:#e0f2fe; }
main { flex:1; display:flex; padding:1rem; gap:1rem; overflow:auto; }
.column { flex:1; display:flex; flex-direction:column; gap:1rem; }
.card { background:#ffffff; border:1px solid #cbd5f5; border-radius:14px; padding:1rem 1.25rem; box-shadow:0 8px 20px rgba(0,0,0,0.08); }
.card h2 { margin-top:0; font-size:1.05rem; color:#1d4ed8; }
.actions { display:flex; gap:0.75rem; flex-wrap:wrap; align-items:center; }
button { border:none; border-radius:10px; padding:0.55rem 1.1rem; font-size:0.9rem; font-weight:600; cursor:pointer; color:white; background:linear-gradient(135deg,#60a5fa,#2563eb); box-shadow:0 6px 16px rgba(37,99,235,0.25); }
button.secondary { background:#e5e7eb; color:#0f172a; box-shadow:none; }
select { padding:0.45rem; border-radius:8px; border:1px solid #cbd5f5; font-size:0.9rem; }
.nic { padding:0.6rem 0.8rem; border-radius:10px; border:1px solid #cbd5f5; margin-bottom:0.6rem; display:flex; justify-content:space-between; align-items:center; background:#f8fafc; }
.badge { padding:0.2rem 0.6rem; border-radius:999px; font-size:0.7rem; font-weight:700; text-transform:uppercase; }
.managed { background:#dbeafe; color:#1e40af; }
.monitor { background:#fee2e2; color:#991b1b; }
.muted { color:#64748b; font-size:0.85em; }
.alert { background:#fee2e2; color:#991b1b; padding:0.3rem 0.6rem; border-radius:6px; font-weight:600; }

/* Table tuning */
table { width:100%; border-collapse:collapse; margin-top:0.5rem; font-size:0.95rem; }
th, td { border-bottom:1px solid #e5e7eb; padding:0.45rem 0.6rem; text-align:left; vertical-align:middle; }
th { background:#f8fafc; }

/* Terminal */
.terminal { background:#1e1e1e; color:#c0c0c0; font-family: monospace; padding:0.8rem; height:400px; overflow:auto; border-radius:10px; }
</style>
"""

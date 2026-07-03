"""HTML-шаблон дашборда.

Одна самодостаточная страница без внешних зависимостей: подтягивает статистику
из `/dashboard/stats` и отрисовывает карточки. Такой подход держит фронтенд
простым и не требует сборщика.
"""

from __future__ import annotations

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Smart Moderator — Dashboard</title>
  <style>
    :root { color-scheme: light dark; }
    body { font-family: system-ui, sans-serif; margin: 0; padding: 2rem;
           background: #0f172a; color: #e2e8f0; }
    h1 { font-weight: 600; margin-bottom: 0.25rem; }
    .sub { color: #94a3b8; margin-top: 0; }
    .grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit,
            minmax(160px, 1fr)); margin-top: 2rem; }
    .card { background: #1e293b; border-radius: 12px; padding: 1.25rem; }
    .card .value { font-size: 2rem; font-weight: 700; }
    .card .label { color: #94a3b8; text-transform: uppercase;
                   font-size: 0.75rem; letter-spacing: 0.05em; }
    footer { margin-top: 2rem; color: #64748b; font-size: 0.85rem; }
  </style>
</head>
<body>
  <h1>Smart Telegram Moderator</h1>
  <p class="sub">Moderation activity overview</p>
  <div class="grid" id="cards"></div>
  <footer>Data refreshes from <code>/dashboard/stats</code></footer>
  <script>
    const LABELS = {
      total: "Total actions", warns: "Warnings", mutes: "Mutes",
      bans: "Bans", unbans: "Unbans", deleted_messages: "Deleted"
    };
    async function load() {
      const res = await fetch("/dashboard/stats");
      const data = await res.json();
      const cards = document.getElementById("cards");
      cards.innerHTML = "";
      for (const [key, label] of Object.entries(LABELS)) {
        const div = document.createElement("div");
        div.className = "card";
        div.innerHTML =
          '<div class="value">' + (data[key] ?? 0) + '</div>' +
          '<div class="label">' + label + '</div>';
        cards.appendChild(div);
      }
    }
    load();
  </script>
</body>
</html>
"""

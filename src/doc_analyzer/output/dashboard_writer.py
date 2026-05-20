"""Interactive HTML dashboard for migration readiness results."""

from __future__ import annotations

import json
from pathlib import Path

from doc_analyzer.models import CorpusReport
from doc_analyzer.output.json_writer import _serialize_result


def write_dashboard(report: CorpusReport, output_path: Path) -> Path:
    documents = [_serialize_result(r) for r in report.documents]
    summary = report.summary

    dashboard_data = {
        "generated_at": report.generated_at,
        "document_count": len(documents),
        "stats": {
            "ready": summary.get("ready_count", 0),
            "partial": summary.get("partial_count", 0),
            "restructure": summary.get("restructure_count", 0),
            "not_ready": summary.get("not_ready_count", 0),
        },
        "pairs": report.pairs,
        "documents": [
            {
                "id": i,
                "file_name": d["file_info"]["file_name"],
                "file_type": d["file_info"]["file_type"],
                "pair_name": d["file_info"].get("pair_name"),
                "readiness": d["migration_readiness"]["rating"],
                "score": d["migration_readiness"]["score"],
                "ready": d["migration_readiness"]["ready_for_migration"],
                "verdict": d["migration_question"]["answer"],
                "improvements": d["migration_question"]["improvements_needed"],
                "issues": d["issues_detected"],
                "recommendations": d["recommendations"],
                "metrics": {
                    "pages": d["metrics"]["page_count"],
                    "words": d["metrics"]["word_count"],
                    "paragraphs": d["metrics"]["paragraph_count"],
                    "headings": d["metrics"]["heading_count"],
                    "tables": d["metrics"]["table_count"],
                    "images": d["metrics"]["image_count"],
                },
                "quality": d["quality_scores"],
            }
            for i, d in enumerate(documents)
        ],
    }

    data_json = json.dumps(dashboard_data, ensure_ascii=False)
    # Prevent accidental </script> breakage inside embedded JSON
    data_json = data_json.replace("</", "<\\/")
    html = _HTML_TEMPLATE.replace("__DATA__", data_json)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Migration Readiness Dashboard</title>
  <style>
    :root {
      --bg: #0f1419;
      --surface: #1a2332;
      --surface2: #243044;
      --text: #e7ecf3;
      --muted: #8b9cb3;
      --border: #2d3d52;
      --ready: #22c55e;
      --partial: #eab308;
      --restructure: #f97316;
      --notready: #ef4444;
      --accent: #3b82f6;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      min-height: 100vh;
    }
    .wrap { max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }
    header { margin-bottom: 2rem; }
    header h1 { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; }
    header p { color: var(--muted); margin-top: 0.35rem; font-size: 0.95rem; }
    .key-question {
      background: linear-gradient(135deg, #1e3a5f 0%, #1a2332 100%);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 2rem;
    }
    .key-question strong { color: #93c5fd; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; }
    .key-question p { margin-top: 0.5rem; font-size: 1.1rem; }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }
    .stat {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem 1.25rem;
    }
    .stat .num { font-size: 2rem; font-weight: 700; }
    .stat .label { font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem; }
    .stat.ready .num { color: var(--ready); }
    .stat.partial .num { color: var(--partial); }
    .stat.restructure .num { color: var(--restructure); }
    .stat.notready .num { color: var(--notready); }
    .toolbar {
      display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center;
      margin-bottom: 1.5rem;
    }
    .toolbar label { color: var(--muted); font-size: 0.85rem; }
    .toolbar input[type="search"] {
      flex: 1; min-width: 200px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.6rem 1rem;
      color: var(--text);
      font-size: 0.95rem;
    }
    .filter-btn {
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.45rem 0.9rem;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.85rem;
    }
    .filter-btn:hover, .filter-btn.active { background: var(--accent); border-color: var(--accent); }
    .cards { display: flex; flex-direction: column; gap: 1rem; }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
    }
    .card-header {
      display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between;
      gap: 1rem; padding: 1.25rem 1.5rem; cursor: pointer;
    }
    .card-header:hover { background: var(--surface2); }
    .card-title { font-weight: 600; font-size: 1.05rem; }
    .card-meta { font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem; }
    .badge {
      display: inline-block;
      padding: 0.25rem 0.65rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 600;
      white-space: nowrap;
    }
    .badge.ready { background: rgba(34,197,94,0.2); color: var(--ready); }
    .badge.partial { background: rgba(234,179,8,0.2); color: var(--partial); }
    .badge.restructure { background: rgba(249,115,22,0.2); color: var(--restructure); }
    .badge.notready { background: rgba(239,68,68,0.2); color: var(--notready); }
    .score-pill {
      font-size: 0.85rem; color: var(--muted);
      background: var(--bg); padding: 0.2rem 0.5rem; border-radius: 6px;
    }
    .card-body {
      display: none;
      padding: 0 1.5rem 1.5rem;
      border-top: 1px solid var(--border);
    }
    .card.open .card-body { display: block; padding-top: 1.25rem; }
    .verdict-box {
      background: var(--bg);
      border-radius: 8px;
      padding: 1rem 1.25rem;
      margin-bottom: 1.25rem;
      border-left: 4px solid var(--accent);
    }
    .verdict-box h4 { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; margin-bottom: 0.35rem; }
    .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.25rem; }
    .section h4 { font-size: 0.8rem; color: var(--muted); text-transform: uppercase; margin-bottom: 0.6rem; }
    .metric-chips { display: flex; flex-wrap: wrap; gap: 0.5rem; }
    .chip {
      background: var(--surface2);
      padding: 0.35rem 0.7rem;
      border-radius: 6px;
      font-size: 0.8rem;
    }
    .chip span { color: var(--muted); }
    ul.clean { list-style: none; }
    ul.clean li {
      padding: 0.4rem 0;
      padding-left: 1.1rem;
      position: relative;
      font-size: 0.9rem;
    }
    ul.clean li::before { content: "-"; position: absolute; left: 0; color: var(--accent); }
    .pairs-section { margin-top: 2.5rem; }
    .pairs-section h2 { font-size: 1.2rem; margin-bottom: 1rem; }
    table {
      width: 100%; border-collapse: collapse;
      background: var(--surface); border-radius: 10px; overflow: hidden;
      border: 1px solid var(--border);
    }
    th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { background: var(--surface2); font-size: 0.75rem; text-transform: uppercase; color: var(--muted); }
    footer { margin-top: 3rem; text-align: center; color: var(--muted); font-size: 0.8rem; }
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Migration Readiness Dashboard</h1>
      <p id="meta-line">Document Analysis Tool</p>
    </header>

    <div class="key-question">
      <strong>Key question</strong>
      <p>Is this document ready for migration? If not, what needs improvement?</p>
    </div>

    <div class="stats" id="stats"></div>

    <div class="toolbar">
      <input type="search" id="search" placeholder="Search by file name..." />
      <button class="filter-btn active" data-filter="all">All</button>
      <button class="filter-btn" data-filter="Ready">Ready</button>
      <button class="filter-btn" data-filter="Partially Ready">Partially Ready</button>
      <button class="filter-btn" data-filter="Requires Restructuring">Restructuring</button>
      <button class="filter-btn" data-filter="Not Ready">Not Ready</button>
    </div>

    <div class="cards" id="cards"></div>

    <section class="pairs-section" id="pairs-section" style="display:none">
      <h2>DOCX / PDF Pairs</h2>
      <table><thead><tr><th>Topic</th><th>DOCX Words</th><th>PDF Words</th><th>Parity</th></tr></thead><tbody id="pairs-body"></tbody></table>
    </section>

    <footer>Generated by Document Analysis &amp; Migration Readiness Tool</footer>
  </div>

  <script id="report-data" type="application/json">__DATA__</script>
  <script>
    const DATA = JSON.parse(document.getElementById("report-data").textContent);

    const badgeClass = (r) => {
      if (r === "Ready") return "ready";
      if (r === "Partially Ready") return "partial";
      if (r === "Requires Restructuring") return "restructure";
      return "notready";
    };

    document.getElementById("meta-line").textContent =
      `${DATA.document_count} documents | ${new Date(DATA.generated_at).toLocaleString()}`;

    const statsEl = document.getElementById("stats");
    const statDefs = [
      ["ready", "Ready", DATA.stats.ready],
      ["partial", "Partially Ready", DATA.stats.partial],
      ["restructure", "Requires Restructuring", DATA.stats.restructure],
      ["notready", "Not Ready", DATA.stats.not_ready],
    ];
    statDefs.forEach(([cls, label, n]) => {
      const box = document.createElement("div"); box.className = "stat " + cls; box.innerHTML = '<div class="num">' + n + '</div><div class="label">' + label + '</div>'; statsEl.appendChild(box);
    });

    let activeFilter = "all";

    function renderCards() {
      const q = document.getElementById("search").value.toLowerCase();
      const el = document.getElementById("cards");
      el.innerHTML = "";
      DATA.documents
        .filter(d => activeFilter === "all" || d.readiness === activeFilter)
        .filter(d => d.file_name.toLowerCase().includes(q))
        .forEach(d => {
          const bc = badgeClass(d.readiness);
          const card = document.createElement("div");
          card.className = "card";
          card.innerHTML = `
            <div class="card-header">
              <div>
                <div class="card-title">${d.file_name}</div>
                <div class="card-meta">${d.file_type} | ${d.pair_name || "-"}</div>
              </div>
              <div style="display:flex;align-items:center;gap:0.75rem">
                <span class="score-pill">Score ${d.score}/100</span>
                <span class="badge ${bc}">${d.readiness}</span>
              </div>
            </div>
            <div class="card-body">
              <div class="verdict-box">
                <h4>Migration verdict</h4>
                <p>${d.verdict}</p>
              </div>
              <div class="grid-2">
                <div class="section">
                  <h4>Document metrics</h4>
                  <div class="metric-chips">
                    <span class="chip"><span>Words</span> ${d.metrics.words}</span>
                    <span class="chip"><span>Headings</span> ${d.metrics.headings}</span>
                    <span class="chip"><span>Paragraphs</span> ${d.metrics.paragraphs}</span>
                    <span class="chip"><span>Tables</span> ${d.metrics.tables}</span>
                    <span class="chip"><span>Images</span> ${d.metrics.images}</span>
                    ${d.metrics.pages != null ? `<span class="chip"><span>Pages</span> ${d.metrics.pages}</span>` : ""}
                  </div>
                </div>
                <div class="section">
                  <h4>Quality scores</h4>
                  <div class="metric-chips">
                    <span class="chip"><span>Readability</span> ${d.quality.readability}</span>
                    <span class="chip"><span>Clarity</span> ${d.quality.clarity}</span>
                    <span class="chip"><span>Consistency</span> ${d.quality.consistency}</span>
                    <span class="chip"><span>Structure</span> ${d.quality.structural_quality}</span>
                  </div>
                </div>
              </div>
              ${d.issues.length ? `<div class="section" style="margin-top:1rem"><h4>Issues detected</h4><ul class="clean">${d.issues.map(i=>`<li>${i}</li>`).join("")}</ul></div>` : ""}
              ${d.improvements.length ? `<div class="section" style="margin-top:1rem"><h4>What needs improvement</h4><ul class="clean">${d.improvements.map(i=>`<li>${i}</li>`).join("")}</ul></div>` :
                (d.ready ? `<div class="section" style="margin-top:1rem"><p style="color:var(--ready);font-size:0.9rem">No critical improvements required.</p></div>` : `<div class="section" style="margin-top:1rem"><ul class="clean">${d.recommendations.map(i=>`<li>${i}</li>`).join("")}</ul></div>`)}
            </div>
          `;
          card.querySelector(".card-header").addEventListener("click", () => card.classList.toggle("open"));
          el.appendChild(card);
        });
    }

    document.querySelectorAll(".filter-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        activeFilter = btn.dataset.filter;
        renderCards();
      });
    });
    document.getElementById("search").addEventListener("input", renderCards);

    if (DATA.pairs && DATA.pairs.length) {
      document.getElementById("pairs-section").style.display = "block";
      const tbody = document.getElementById("pairs-body");
      DATA.pairs.forEach(p => {
        tbody.innerHTML += `<tr><td>${p.name}</td><td>${p.docx_words ?? '-'}</td><td>${p.pdf_words ?? '-'}</td><td>${p.parity_ratio != null ? (p.parity_ratio * 100).toFixed(1) + '%' : '-'}</td></tr>`;
      });
    }

    renderCards();
  </script>
</body>
</html>
"""

#!/usr/bin/env python3
import csv, hashlib, statistics, sys
from pathlib import Path

root, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
rows = list(csv.DictReader((root / "benchmark" / "raw_results.csv").open(newline="")))
configs = ["o1+o2+o4", "o1+o2+o4+o5"]
workloads = ["diabetes", "cancer", "housing", "silk-wave", "square-wave"]

summary = []
for workload in workloads:
    for config in configs:
        selected = [r for r in rows if r["workload"] == workload and
                    r["configuration"] == config]
        elapsed = [float(r["elapsed_seconds"]) for r in selected]
        user = [float(r["user_seconds"]) for r in selected]
        system = [float(r["system_seconds"]) for r in selected]
        rss = [int(r["max_rss_kb"]) for r in selected]
        summary.append({"configuration": config, "workload": workload,
                        "runs": len(selected),
                        "median_elapsed_seconds": f"{statistics.median(elapsed):.9f}",
                        "min_elapsed_seconds": f"{min(elapsed):.9f}",
                        "max_elapsed_seconds": f"{max(elapsed):.9f}",
                        "median_user_seconds": f"{statistics.median(user):.3f}",
                        "median_system_seconds": f"{statistics.median(system):.3f}",
                        "median_max_rss_kb": str(int(statistics.median(rss)))})
with (out / "o5_benchmark_results.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, list(summary[0])); w.writeheader(); w.writerows(summary)

speedups = []
for workload in workloads:
    base = next(r for r in summary if r["workload"] == workload and r["configuration"] == configs[0])
    o5 = next(r for r in summary if r["workload"] == workload and r["configuration"] == configs[1])
    b, v = float(base["median_elapsed_seconds"]), float(o5["median_elapsed_seconds"])
    speedups.append({"workload": workload, "o1_o2_o4_median_seconds": f"{b:.9f}",
                     "o1_o2_o4_o5_median_seconds": f"{v:.9f}",
                     "o5_speedup": f"{b/v:.6f}",
                     "runtime_reduction_percent": f"{(1-v/b)*100:.3f}"})
with (out / "o5_speedups.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, list(speedups[0])); w.writeheader(); w.writerows(speedups)

def normalized(path):
    return "\n".join(line for line in path.read_text(errors="replace").splitlines()
                     if "End-to-End" not in line) + "\n"

checks = []
raw = root / "benchmark" / "raw"
for workload in workloads:
    for repeat in range(1, 4):
        base = normalized(raw / f"o1_o2_o4_{workload}_r{repeat}.stdout")
        candidate = normalized(raw / f"o1_o2_o4_o5_{workload}_r{repeat}.stdout")
        checks.append({"workload": workload, "repeat": repeat,
                       "exact_match": str(base == candidate).lower(),
                       "reference_sha256": hashlib.sha256(base.encode()).hexdigest(),
                       "o5_sha256": hashlib.sha256(candidate.encode()).hexdigest()})
with (out / "o5_correctness.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, list(checks[0])); w.writeheader(); w.writerows(checks)

def svg_chart(filename, title, ylabel, series, ymax, value_labels=False):
    width, height, left, top, pw, ph = 1200, 650, 100, 70, 1030, 470
    colors = ["#377eb8", "#e41a1c"]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="600" y="32" text-anchor="middle" font-family="sans-serif" font-size="24">{title}</text>',
             f'<text transform="translate(25 305) rotate(-90)" text-anchor="middle" font-family="sans-serif" font-size="16">{ylabel}</text>']
    for i in range(6):
        value = ymax*i/5; y = top+ph-i*ph/5
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+pw}" y2="{y:.1f}" stroke="#dddddd"/><text x="{left-10}" y="{y+5:.1f}" text-anchor="end" font-family="sans-serif" font-size="12">{value:.2f}</text>')
    group_w, bar_w = pw/len(workloads), pw/len(workloads)/5
    for wi, workload in enumerate(workloads):
        gx = left + wi*group_w
        for si, values in enumerate(series):
            value = values[wi]; h=value/ymax*ph; x=gx+(si+1)*bar_w; y=top+ph-h
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w*.85:.1f}" height="{h:.1f}" fill="{colors[si]}"/>')
            if value_labels:
                parts.append(f'<text x="{x+bar_w*.42:.1f}" y="{y-5:.1f}" text-anchor="middle" font-family="sans-serif" font-size="12">{value:.3f}</text>')
        parts.append(f'<text x="{gx+group_w/2:.1f}" y="{top+ph+25}" text-anchor="middle" font-family="sans-serif" font-size="14">{workload}</text>')
    for si, label in enumerate(configs):
        x=left+si*300
        parts.append(f'<rect x="{x}" y="600" width="15" height="15" fill="{colors[si]}"/><text x="{x+22}" y="613" font-family="sans-serif" font-size="14">{label}</text>')
    parts.append('</svg>')
    (out / filename).write_text("\n".join(parts))

base_times = [float(next(r for r in speedups if r["workload"] == w)["o1_o2_o4_median_seconds"]) for w in workloads]
o5_times = [float(next(r for r in speedups if r["workload"] == w)["o1_o2_o4_o5_median_seconds"]) for w in workloads]
svg_chart("o5_runtime_comparison.svg", "O5 end-to-end runtime comparison (-O3, 4 threads)",
          "Median runtime (seconds)", [base_times, o5_times], max(base_times)*1.12)
reductions = [float(r["runtime_reduction_percent"]) for r in speedups]
svg_chart("o5_runtime_reduction.svg", "O5 median end-to-end runtime reduction",
          "Runtime reduction (%)", [[0.0]*5, reductions], max(reductions)*1.18, True)
print(f"Exact output matches: {sum(c['exact_match']=='true' for c in checks)}/{len(checks)}")

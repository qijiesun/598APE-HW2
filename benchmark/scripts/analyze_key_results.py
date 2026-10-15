#!/usr/bin/env python3
import csv, hashlib, statistics, sys
from pathlib import Path

root, dest = Path(sys.argv[1]), Path(sys.argv[2])
dest.mkdir(parents=True, exist_ok=True)
rows = list(csv.DictReader((root / "raw_results.csv").open(newline="")))
official = [r for r in rows if r["repeat"] == "1"]
baseline = {r["workload"]: float(r["elapsed_seconds"])
            for r in official if r["configuration"] == "baseline"}
for r in official:
    r["speedup"] = f'{baseline[r["workload"]] / float(r["elapsed_seconds"]):.6f}'
fields = list(official[0])
result_fields = [x for x in official[0] if x != "speedup"]
with (dest / "benchmark_results.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, result_fields, extrasaction="ignore")
    w.writeheader(); w.writerows(official)
with (dest / "benchmark_speedups.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(official)

fastest = []
for workload in sorted(baseline):
    fastest.append(min((r for r in official if r["workload"] == workload),
                       key=lambda r: float(r["elapsed_seconds"])))
with (dest / "fastest_configurations.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(fastest)

variability = []
for config in sorted({r["configuration"] for r in rows}):
    vals = [float(r["elapsed_seconds"]) for r in rows
            if r["configuration"] == config and r["workload"] == "diabetes"]
    variability.append({"configuration": config, "n": len(vals),
                        "median_seconds": f"{statistics.median(vals):.9f}",
                        "min_seconds": f"{min(vals):.9f}",
                        "max_seconds": f"{max(vals):.9f}",
                        "range_percent_of_median": f"{(max(vals)-min(vals))/statistics.median(vals)*100:.3f}"})
with (dest / "diabetes_variability.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, list(variability[0])); w.writeheader(); w.writerows(variability)

def normalized(path):
    return "\n".join(x for x in path.read_text(errors="replace").splitlines()
                     if "End-to-End" not in x) + "\n"

correctness = []
for workload in sorted(baseline):
    base = normalized(root / "raw" / f"O3_baseline_{workload}_r1.stdout")
    bh = hashlib.sha256(base.encode()).hexdigest()
    for r in (x for x in official if x["workload"] == workload):
        safe = r["configuration"].replace("+", "_")
        actual = normalized(root / "raw" / f"O3_{safe}_{workload}_r1.stdout")
        correctness.append({"workload": workload, "configuration": r["configuration"],
                            "matches_baseline": str(actual == base).lower(),
                            "normalized_sha256": hashlib.sha256(actual.encode()).hexdigest(),
                            "baseline_sha256": bh})
with (dest / "correctness_matrix.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, list(correctness[0])); w.writeheader(); w.writerows(correctness)

configs = ["baseline", "o1", "o3", "o1+o2+o4", "o2+o3+o4"]
workloads = ["diabetes", "cancer", "housing", "silk-wave", "square-wave"]
colors = ["#777777", "#377eb8", "#984ea3", "#e41a1c", "#4daf4a"]
values = {(r["workload"], r["configuration"]): float(r["speedup"]) for r in official}
width, height, margin, ymax = 1200, 650, 90, max(values.values()) * 1.12
pw, ph = width - 2*margin, height - 2*margin
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
       '<rect width="100%" height="100%" fill="white"/>',
       f'<text x="{width/2}" y="34" text-anchor="middle" font-family="sans-serif" font-size="24">Key configuration speedups (-O3, baseline = 1.0)</text>',
       f'<text transform="translate(24 {height/2}) rotate(-90)" text-anchor="middle" font-family="sans-serif" font-size="16">Speedup over baseline</text>',
       f'<line x1="{margin}" y1="{margin+ph}" x2="{margin+pw}" y2="{margin+ph}" stroke="black"/>']
for i in range(6):
    v=ymax*i/5; y=margin+ph-i*ph/5
    svg.append(f'<line x1="{margin}" y1="{y:.1f}" x2="{margin+pw}" y2="{y:.1f}" stroke="#dddddd"/><text x="{margin-10}" y="{y+5:.1f}" text-anchor="end" font-family="sans-serif" font-size="12">{v:.0f}x</text>')
bw = pw/(len(workloads)*(len(configs)+2))
for wi, workload in enumerate(workloads):
    gx = margin + wi*pw/len(workloads)
    for ci, config in enumerate(configs):
        v=values[(workload,config)]; h=v/ymax*ph; x=gx+(ci+1)*bw; y=margin+ph-h
        svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw*.84:.1f}" height="{h:.1f}" fill="{colors[ci]}"/>')
    svg.append(f'<text x="{gx+pw/len(workloads)/2:.1f}" y="{height-margin+24}" text-anchor="middle" font-family="sans-serif" font-size="14">{workload}</text>')
for ci, config in enumerate(configs):
    x=margin+ci*190
    svg.append(f'<rect x="{x}" y="{height-42}" width="14" height="14" fill="{colors[ci]}"/><text x="{x+20}" y="{height-30}" font-family="sans-serif" font-size="13">{config}</text>')
svg.append('</svg>')
(dest / "key_speedups_O3.svg").write_text("\n".join(svg))

# Runtime chart uses a logarithmic y-axis because image and tabular workloads
# have very different absolute durations.
import math
times = {(r["workload"], r["configuration"]): float(r["elapsed_seconds"])
         for r in official}
tmin, tmax = min(times.values()), max(times.values())
logmin, logmax = math.floor(math.log10(tmin)), math.ceil(math.log10(tmax))
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
       '<rect width="100%" height="100%" fill="white"/>',
       f'<text x="{width/2}" y="34" text-anchor="middle" font-family="sans-serif" font-size="24">End-to-end runtime (-O3, OMP_NUM_THREADS=4)</text>',
       f'<text transform="translate(24 {height/2}) rotate(-90)" text-anchor="middle" font-family="sans-serif" font-size="16">Runtime (seconds, log scale)</text>']
for power in range(logmin, logmax + 1):
    y = margin + ph - (power-logmin)/(logmax-logmin)*ph
    svg.append(f'<line x1="{margin}" y1="{y:.1f}" x2="{margin+pw}" y2="{y:.1f}" stroke="#dddddd"/><text x="{margin-10}" y="{y+5:.1f}" text-anchor="end" font-family="sans-serif" font-size="12">10^{power}</text>')
for wi, workload in enumerate(workloads):
    gx=margin+wi*pw/len(workloads)
    for ci,config in enumerate(configs):
        v=times[(workload,config)]; frac=(math.log10(v)-logmin)/(logmax-logmin)
        h=frac*ph; x=gx+(ci+1)*bw; y=margin+ph-h
        svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw*.84:.1f}" height="{h:.1f}" fill="{colors[ci]}"/>')
    svg.append(f'<text x="{gx+pw/len(workloads)/2:.1f}" y="{height-margin+24}" text-anchor="middle" font-family="sans-serif" font-size="14">{workload}</text>')
for ci,config in enumerate(configs):
    x=margin+ci*190
    svg.append(f'<rect x="{x}" y="{height-42}" width="14" height="14" fill="{colors[ci]}"/><text x="{x+20}" y="{height-30}" font-family="sans-serif" font-size="13">{config}</text>')
svg.append('</svg>')
(dest / "runtime_comparison_O3.svg").write_text("\n".join(svg))

# Direct final-configuration comparison: O1+O2+O4 versus O2+O3+O4.
finals=["o1+o2+o4","o2+o3+o4"]; fcolors=["#e41a1c","#4daf4a"]
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
     '<rect width="100%" height="100%" fill="white"/>',
     f'<text x="{width/2}" y="34" text-anchor="middle" font-family="sans-serif" font-size="24">O1-based versus O3-based final configuration (-O3)</text>',
     f'<text transform="translate(24 {height/2}) rotate(-90)" text-anchor="middle" font-family="sans-serif" font-size="16">Speedup over baseline</text>']
fymax=max(values[(w,c)] for w in workloads for c in finals)*1.12; fbw=pw/(len(workloads)*4)
for i in range(6):
    v=fymax*i/5; y=margin+ph-i*ph/5
    svg.append(f'<line x1="{margin}" y1="{y:.1f}" x2="{margin+pw}" y2="{y:.1f}" stroke="#dddddd"/><text x="{margin-10}" y="{y+5:.1f}" text-anchor="end" font-family="sans-serif" font-size="12">{v:.0f}x</text>')
for wi,wload in enumerate(workloads):
    gx=margin+wi*pw/len(workloads)
    for ci,cfg in enumerate(finals):
        v=values[(wload,cfg)]; h=v/fymax*ph; x=gx+(ci+1)*fbw; y=margin+ph-h
        svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{fbw*.85:.1f}" height="{h:.1f}" fill="{fcolors[ci]}"/><text x="{x+fbw*.42:.1f}" y="{y-5:.1f}" text-anchor="middle" font-family="sans-serif" font-size="12">{v:.2f}x</text>')
    svg.append(f'<text x="{gx+pw/len(workloads)/2:.1f}" y="{height-margin+24}" text-anchor="middle" font-family="sans-serif" font-size="14">{wload}</text>')
for ci,cfg in enumerate(finals):
    x=margin+ci*260
    svg.append(f'<rect x="{x}" y="{height-42}" width="14" height="14" fill="{fcolors[ci]}"/><text x="{x+20}" y="{height-30}" font-family="sans-serif" font-size="13">{cfg}</text>')
svg.append('</svg>')
(dest / "o1_vs_o3_final_O3.svg").write_text("\n".join(svg))
print(f"Analyzed {len(official)} official measurements; exact matches "
      f"{sum(r['matches_baseline']=='true' for r in correctness)}/{len(correctness)}")

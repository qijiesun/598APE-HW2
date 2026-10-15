#!/usr/bin/env bash
set -euo pipefail

repo=${1:-$HOME/CS598/HW2_integration}
out=${2:-$HOME/CS598/HW2_integration_results/key_benchmarks}
threads=${OMP_NUM_THREADS:-4}
mkdir -p "$out/raw" "$out/metadata"

configs=(baseline o1 o3 o1+o2+o4 o2+o3+o4)
workloads=(diabetes cancer housing silk-wave square-wave)
printf 'opt_level,configuration,workload,repeat,elapsed_seconds,user_seconds,system_seconds,max_rss_kb,exit_status\n' > "$out/raw_results.csv"

{
  date --iso-8601=seconds
  uname -a
  lscpu
  g++ --version
  printf 'OMP_NUM_THREADS=%s\n' "$threads"
  git -C "$repo" rev-parse HEAD
  git -C "$repo" status --short --branch
} > "$out/metadata/environment.txt" 2>&1

cd "$repo"
make MODE=benchmark OPT_LEVEL=3 -j2
make MODE=benchmark OPT_LEVEL=3 print-config > "$out/metadata/build_O3.txt"
binary="$repo/build/benchmark-O3/genetic_benchmark"

run_one() {
  local config=$1 workload=$2 repeat=$3
  local safe=${config//+/_}
  local stem="$out/raw/O3_${safe}_${workload}_r${repeat}"
  echo "[$(date --iso-8601=seconds)] O3 $config $workload repeat $repeat"
  set +e
  /usr/bin/time -f $'USER_SECONDS=%U\nSYSTEM_SECONDS=%S\nMAX_RSS_KB=%M\nPROCESS_EXIT=%x' \
    env OMP_NUM_THREADS="$threads" "$binary" "$workload" "$config" \
    > "$stem.stdout" 2> "$stem.stderr"
  local status=$?
  set -e
  local elapsed user system rss
  elapsed=$(sed -n 's/^Time for .*: \([0-9.]*\) seconds$/\1/p' "$stem.stderr" | tail -1)
  user=$(sed -n 's/^USER_SECONDS=//p' "$stem.stderr" | tail -1)
  system=$(sed -n 's/^SYSTEM_SECONDS=//p' "$stem.stderr" | tail -1)
  rss=$(sed -n 's/^MAX_RSS_KB=//p' "$stem.stderr" | tail -1)
  printf '3,%s,%s,%s,%s,%s,%s,%s,%s\n' "$config" "$workload" "$repeat" \
    "$elapsed" "$user" "$system" "$rss" "$status" >> "$out/raw_results.csv"
  (( status == 0 )) || exit "$status"
}

for config in "${configs[@]}"; do
  for workload in "${workloads[@]}"; do
    run_one "$config" "$workload" 1
  done
done

# Three total diabetes observations provide a compact variability check.
for config in "${configs[@]}"; do
  run_one "$config" diabetes 2
  run_one "$config" diabetes 3
done

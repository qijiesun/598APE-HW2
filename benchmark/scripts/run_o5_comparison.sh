#!/usr/bin/env bash
set -euo pipefail
repo=${1:-$HOME/CS598/HW2_o5_experiment}
out=${2:-$HOME/CS598/HW2_o5_results/benchmark}
threads=${OMP_NUM_THREADS:-4}
mkdir -p "$out/raw" "$out/metadata"
printf 'configuration,workload,repeat,elapsed_seconds,user_seconds,system_seconds,max_rss_kb,exit_status\n' > "$out/raw_results.csv"
{
  date --iso-8601=seconds; uname -a; lscpu; g++ --version
  printf 'OMP_NUM_THREADS=%s\n' "$threads"
} > "$out/metadata/environment.txt" 2>&1
cd "$repo"
make MODE=benchmark OPT_LEVEL=3 -j2
make MODE=benchmark OPT_LEVEL=3 print-config > "$out/metadata/build_O3.txt"
binary="$repo/build/benchmark-O3/genetic_benchmark"
configs=(o1+o2+o4 o1+o2+o4+o5)
workloads=(diabetes cancer housing silk-wave square-wave)
for repeat in 1 2 3; do
  for workload in "${workloads[@]}"; do
    for config in "${configs[@]}"; do
      safe=${config//+/_}; stem="$out/raw/${safe}_${workload}_r${repeat}"
      echo "[$(date --iso-8601=seconds)] $config $workload repeat $repeat"
      set +e
      /usr/bin/time -f $'USER_SECONDS=%U\nSYSTEM_SECONDS=%S\nMAX_RSS_KB=%M\nPROCESS_EXIT=%x' \
        env OMP_NUM_THREADS="$threads" "$binary" "$workload" "$config" \
        > "$stem.stdout" 2> "$stem.stderr"
      status=$?
      set -e
      elapsed=$(sed -n 's/^Time for .*: \([0-9.]*\) seconds$/\1/p' "$stem.stderr" | tail -1)
      user=$(sed -n 's/^USER_SECONDS=//p' "$stem.stderr" | tail -1)
      system=$(sed -n 's/^SYSTEM_SECONDS=//p' "$stem.stderr" | tail -1)
      rss=$(sed -n 's/^MAX_RSS_KB=//p' "$stem.stderr" | tail -1)
      printf '%s,%s,%s,%s,%s,%s,%s,%s\n' "$config" "$workload" "$repeat" \
        "$elapsed" "$user" "$system" "$rss" "$status" >> "$out/raw_results.csv"
      (( status == 0 )) || exit "$status"
    done
  done
done

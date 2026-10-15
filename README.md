# CS598 APE HW2: Symbolic Regression Optimization

This repository contains the course symbolic-regression benchmark and five
independently selectable optimizations. It requires a C++17 GCC toolchain,
GNU Make, OpenMP, and the datasets/images already tracked under `benchmark/`.
Racket is optional and is needed only to render emitted image models.

## Optimizations

- `o1`: evaluate each AST node across a column of samples (loop interchange).
- `o2`: evaluate programs in parallel with OpenMP.
- `o3`: use constant-time push/pop in the fixed-capacity AST evaluation stack.
- `o4`: eliminate AST deep copies by swapping generation buffers and moving
  program ownership during final insertion sorting.
- `o5`: hoist node-type dispatch out of O1's per-row loop and evaluate each
  AST node as a typed sample column.

O1 uses its own column evaluator and therefore bypasses the fixed stack. O3 is
accepted in combinations containing O1, but it does not affect that execution
path. O4's move operations and buffer swap preserve AST ownership; cleanup
needed for safe reuse is always enabled as a correctness requirement.
O5 is specific to O1: without O1 it is a no-op. Its per-operator formulas and
row order match the original scalar node evaluator. The `all` configuration
enables O1 through O5; O3 remains enabled in flags but is bypassed by O1.

## Build

Build paths include the mode and optimization level, preventing stale object
files when configurations change:

```bash
make MODE=benchmark OPT_LEVEL=0 -j2
make MODE=benchmark OPT_LEVEL=3 -j2
make MODE=debug OPT_LEVEL=0 -j2
make MODE=asan OPT_LEVEL=1 -j2
make MODE=tsan OPT_LEVEL=1 -j2
make print-config MODE=benchmark OPT_LEVEL=3
```

The benchmark executables are written to, for example,
`build/benchmark-O3/genetic_benchmark`. `make clean` removes all build trees.
Additional compiler or linker flags can be supplied through
`EXTRA_CXXFLAGS` and `EXTRA_LDFLAGS`.

## Run

The command format is:

```bash
OMP_NUM_THREADS=4 ./build/benchmark-O3/genetic_benchmark WORKLOAD CONFIGURATION
```

Workloads are `diabetes`, `cancer`, `housing`, `silk-wave`, and
`square-wave`. A configuration is `baseline`, `all`, one optimization such as
`o3`, or a `+`-separated combination such as `o2+o3+o4`. Commas are also
accepted as separators. Examples:

```bash
OMP_NUM_THREADS=4 ./build/benchmark-O3/genetic_benchmark diabetes baseline
OMP_NUM_THREADS=4 ./build/benchmark-O3/genetic_benchmark cancer o1+o2+o4
OMP_NUM_THREADS=4 ./build/benchmark-O3/genetic_benchmark square-wave all
```

The five official workloads can be run explicitly with:

```bash
for workload in diabetes cancer housing silk-wave square-wave; do
  OMP_NUM_THREADS=4 ./build/benchmark-O3/genetic_benchmark "$workload" all
done
```

O2 is disabled unless explicitly named. `OMP_NUM_THREADS` is still recorded
for every controlled comparison so the environment remains reproducible.
The benchmark parameters and deterministic seeds are defined in
`benchmark/genetic_benchmark.cpp`; optimization flags do not alter them.

## Measured performance

Measurements used an Intel Xeon Silver 4216 VM (4 CPUs), GCC 15.2.0,
`-O3 -fopenmp -fno-omit-frame-pointer`, and `OMP_NUM_THREADS=4`. Three-run
medians for the final O5 comparison were:

| Workload | O1+O2+O4 | O1+O2+O4+O5 | O5 speedup |
|---|---:|---:|---:|
| diabetes | 0.204153 s | 0.174223 s | 1.172x |
| cancer | 4.905033 s | 4.683096 s | 1.047x |
| housing | 3.681520 s | 3.507792 s | 1.050x |
| silk-wave | 9.118888 s | 8.844510 s | 1.031x |
| square-wave | 25.808260 s | 24.605392 s | 1.049x |

The earlier O1-O4 comparison and the O5 median data are tracked under
`benchmark/results/`; figures are under `benchmark/figures/`. The O1-based
configuration was faster than the O3-based configuration on all five workloads
because O1's column-oriented evaluation removes the fixed-stack path that O3
accelerates.

To reproduce the O5 comparison:

```bash
OMP_NUM_THREADS=4 bash benchmark/scripts/run_o5_comparison.sh \
  "$PWD" "$PWD/results/o5"
python3 benchmark/scripts/analyze_o5_results.py \
  "$PWD/results/o5" "$PWD/results/o5/analysis"
```

## Reproduce the evaluation

Run the tracked benchmark script from the repository root:

```bash
OMP_NUM_THREADS=4 bash benchmark/scripts/run_key_benchmarks.sh \
  "$PWD" "$PWD/results/key_benchmarks"
```

The script serially runs the five key configurations (`baseline`, `o1`, `o3`,
`o1+o2+o4`, and `o2+o3+o4`) across all five workloads at `-O3`, captures
stdout/stderr plus GNU `time` resource data, and writes `raw_results.csv`. It
also repeats diabetes three times as a compact variability check. Expensive
benchmarks are never run concurrently. Targeted `-O0` measurements are not part
of the official result set.

For correctness comparisons, remove only the line containing
`End-to-End` from stdout and compare the remaining output. Timing and resource
metadata are written to stderr. Sanitizer builds may also report the known
upstream signed integer overflow at `include/custom_distributions.h:28`; this
project does not change the random-number generator to hide that warning.

Targeted ownership, stack-boundary, and O5 node-column tests are tracked under
`tests/`. Compile them against an ASan build and run with leak detection:

```bash
make sanitizer-tests
```

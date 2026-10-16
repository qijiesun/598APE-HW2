# 598APE-HW1

## Tools

This program assumes the following are installed on your machine:
* A working C++ compiler (g++ is assumed in the Makefile)
* make
* racket (optionally plot images)

If any of the above is missing, you can run the following commands in a terminal:
* `sudo apt update`
* `sudo apt install build-essential`
* `sudo apt install racket`

## Instructions

After pulling the code, open a terminal in the folder the code was pulled into.\
Run `make`.\

### Default program usage:
```
./genetic_benchmark <test name>
```

Test names:
* diabetes
* cancer
* housing
* silk-wave
* square-wave

### Optimized program usage:
```
./genetic_benchmark <test name> <optimizations>
```
The optimizations flag can be a single optimization or a chain of optimizations connected with a "+" character.\
The "all" flag excludes optimization o3 and should be run by itself.
Examples:
```
./genetic_benchmark <test name> o1
```
```
./genetic_benchmark <test name> o1+o2+o4+o5
```
```
./genetic_benchmark <test name> all
```

Optimizations:
* o1
* o2
* o3
* o4
* o5
* all

Optimization o6 is enabled by default, disabling it require editing the Makefile to remove "-O2" and running `make clean` and `make`.


## Optimizations

Optimization flags correspond to the following:
* o1: loop interchange evaluating each AST node across a column of samples.
* o2: evaluate programs in parallel with OpenMP.
* o3: use constant-time push/pop in the fixed-capacity AST evaluation stack.
* o4: eliminate AST deep copies by swapping generation buffers and moving program ownership during final insertion sorting.
* o5: hoist node-type dispatch out of O1's per-row loop and evaluate each AST node as a typed sample column.

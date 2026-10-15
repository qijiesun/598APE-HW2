CXX ?= g++
OPT_LEVEL ?= 3
MODE ?= benchmark

CPPFLAGS := -I include -I.
BASE_FLAGS := -std=c++17 -Wall -Wextra -fopenmp -fno-omit-frame-pointer

ifeq ($(MODE),benchmark)
  MODE_FLAGS := -O$(OPT_LEVEL)
else ifeq ($(MODE),debug)
  MODE_FLAGS := -O0 -g3 -D_GLIBCXX_ASSERTIONS
else ifeq ($(MODE),asan)
  MODE_FLAGS := -O1 -g3 -fsanitize=address,undefined
else ifeq ($(MODE),tsan)
  MODE_FLAGS := -O1 -g3 -fsanitize=thread
else
  $(error Unknown MODE '$(MODE)'; use benchmark, debug, asan, or tsan)
endif

CXXFLAGS := $(BASE_FLAGS) $(MODE_FLAGS) $(EXTRA_CXXFLAGS)
LDFLAGS := -fopenmp $(MODE_FLAGS) $(EXTRA_LDFLAGS)

SRC_DIR := src
BENCH_DIR := benchmark
BUILD_DIR := build/$(MODE)-O$(OPT_LEVEL)
OBJ_DIR := $(BUILD_DIR)/obj
BENCH_BIN := $(BUILD_DIR)/genetic_benchmark
SRCS := $(wildcard $(SRC_DIR)/*.cpp)
OBJS := $(SRCS:$(SRC_DIR)/%.cpp=$(OBJ_DIR)/%.o)
DEPS := $(OBJS:.o=.d)

all: $(BENCH_BIN)

$(BENCH_BIN): $(BENCH_DIR)/genetic_benchmark.cpp $(OBJS) | $(BUILD_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $< $(OBJS) $(LDFLAGS) -o $@

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp | $(OBJ_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -MMD -MP -c $< -o $@

$(BUILD_DIR) $(OBJ_DIR):
	mkdir -p $@

unoptimized:
	$(MAKE) MODE=benchmark OPT_LEVEL=0 all

release:
	$(MAKE) MODE=benchmark OPT_LEVEL=3 all

debug:
	$(MAKE) MODE=debug OPT_LEVEL=0 all

asan:
	$(MAKE) MODE=asan OPT_LEVEL=1 all

tsan:
	$(MAKE) MODE=tsan OPT_LEVEL=1 all

sanitizer-tests:
	$(MAKE) MODE=asan OPT_LEVEL=1 all
	mkdir -p build/tests-asan
	$(CXX) $(CPPFLAGS) $(BASE_FLAGS) -O1 -g3 -fsanitize=address,undefined \
		tests/mutation_ownership_test.cpp build/asan-O1/obj/genetic.o \
		build/asan-O1/obj/node.o build/asan-O1/obj/philox_rng.o \
		build/asan-O1/obj/program.o -fsanitize=address,undefined -o \
		build/tests-asan/mutation_ownership_test
	$(CXX) $(CPPFLAGS) $(BASE_FLAGS) -O1 -g3 -fsanitize=address,undefined \
		tests/stack_boundary_test.cpp -fsanitize=address,undefined -o \
		build/tests-asan/stack_boundary_test
	$(CXX) $(CPPFLAGS) $(BASE_FLAGS) -O1 -g3 -fsanitize=address,undefined \
		tests/o5_node_column_test.cpp build/asan-O1/obj/node.o \
		-fsanitize=address,undefined -o build/tests-asan/o5_node_column_test
	ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 build/tests-asan/mutation_ownership_test
	ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 build/tests-asan/stack_boundary_test
	ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 build/tests-asan/o5_node_column_test

clean:
	rm -rf build

print-config:
	@echo "CXX=$(CXX)"
	@echo "MODE=$(MODE)"
	@echo "OPT_LEVEL=$(OPT_LEVEL)"
	@echo "CPPFLAGS=$(CPPFLAGS)"
	@echo "CXXFLAGS=$(CXXFLAGS)"
	@echo "LDFLAGS=$(LDFLAGS)"
	@echo "BENCH_BIN=$(BENCH_BIN)"

-include $(DEPS)

.PHONY: all unoptimized release debug asan tsan sanitizer-tests clean print-config

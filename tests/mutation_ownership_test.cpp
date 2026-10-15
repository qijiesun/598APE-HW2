#include "flags.h"
#include "genetic.h"
#include "program.h"
#include "src/constants.h"
#include <iostream>
#include <utility>

Flags optimizations;
using namespace genetic;

static bool valid(const program &p) {
  if (p.len <= 0 || p.nodes == nullptr)
    return false;
  int pending = 1;
  for (int i = 0; i < p.len; ++i) {
    if (pending <= 0)
      return false;
    --pending;
    pending += p.nodes[i].arity();
  }
  return pending == 0 && get_depth(p) < MAX_STACK_SIZE;
}

int main() {
  param params;
  params.num_features = 10;
  params.init_depth[0] = 2;
  params.init_depth[1] = 6;
  params.terminalRatio = 0.05f;
  params.function_set = {node::type::add, node::type::sub, node::type::mul,
                         node::type::abs, node::type::sin, node::type::cos,
                         node::type::fdim, node::type::log};
  params.arity_set = {
      {1, {node::type::abs, node::type::sin, node::type::cos, node::type::log}},
      {2, {node::type::add, node::type::sub, node::type::mul, node::type::fdim}}};

  PhiloxEngine rng(2025000000);
  program a, b, cross, point, hoist, subtree;
  build_program(a, params, rng);
  build_program(b, params, rng);

  for (int i = 0; i < 2000; ++i) {
    crossover(a, b, cross, params, rng);
    if (!valid(cross)) return 10;
    point_mutation(cross, point, params, rng);
    if (!valid(point)) return 11;
    hoist_mutation(point, hoist, params, rng);
    if (!valid(hoist)) return 12;
    subtree_mutation(hoist, subtree, params, rng);
    if (!valid(subtree)) return 13;

    program copied(subtree);
    if (!valid(copied)) return 14;
    a = copied;
    program moved(std::move(copied));
    if (!valid(moved) || copied.nodes != nullptr || copied.len != 0) return 15;
    b = std::move(moved);
    if (!valid(b) || moved.nodes != nullptr || moved.len != 0) return 16;
  }

  std::cout << "PASS: 2000 mutation/copy/move ownership cycles\n";
  return 0;
}

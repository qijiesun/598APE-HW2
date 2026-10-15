#include "src/node_detail.h"
#include <cmath>
#include <cstring>
#include <iostream>
#include <vector>

using genetic::node;

static bool same(float a, float b) {
  return (std::isnan(a) && std::isnan(b)) || std::memcmp(&a, &b, sizeof(float)) == 0;
}

int main() {
  constexpr uint64_t n = 17;
  std::vector<float> x(n), y(n), data(2 * n), out(n);
  for (uint64_t i = 0; i < n; ++i) {
    x[i] = (static_cast<int>(i) - 8) * 0.37f;
    y[i] = (static_cast<int>(i) - 7) * 0.23f;
    data[i] = x[i];
    data[n + i] = y[i];
  }

  for (uint32_t raw = static_cast<uint32_t>(node::type::functions_begin);
       raw <= static_cast<uint32_t>(node::type::functions_end); ++raw) {
    node current(static_cast<node::type>(raw));
    genetic::detail::evaluate_node_column(current, data.data(), n, x.data(),
                                          y.data(), out.data());
    for (uint64_t i = 0; i < n; ++i) {
      const float in[2] = {x[i], y[i]};
      const float expected =
          genetic::detail::evaluate_node(current, data.data(), n, i, in);
      if (!same(expected, out[i])) {
        std::cerr << "Mismatch for node " << raw << " at row " << i << '\n';
        return 1;
      }
    }
  }

  node constant(1.25f);
  genetic::detail::evaluate_node_column(constant, data.data(), n, nullptr,
                                        nullptr, out.data());
  for (float value : out) if (!same(value, 1.25f)) return 2;
  node variable(1);
  genetic::detail::evaluate_node_column(variable, data.data(), n, nullptr,
                                        nullptr, out.data());
  for (uint64_t i = 0; i < n; ++i) if (!same(out[i], y[i])) return 3;

  std::cout << "PASS: O5 column evaluation matches scalar evaluation for all node types\n";
}

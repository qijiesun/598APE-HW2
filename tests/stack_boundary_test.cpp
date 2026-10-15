#include "src/reg_stack.h"
#include <iostream>

template <bool Fast> bool exercise() {
  genetic::stack<int, 4, Fast> s;
  if (!s.empty() || s.size() != 0 || s.pop() != 0) return false;
  for (int i = 1; i <= 4; ++i) s.push(i);
  s.push(99);
  if (!s.full() || s.size() != 4) return false;
  for (int i = 4; i >= 1; --i)
    if (s.pop() != i) return false;
  return s.empty() && s.pop() == 0;
}

int main() {
  if (!exercise<false>() || !exercise<true>()) return 1;
  std::cout << "PASS: baseline and O3 stack boundaries\n";
}

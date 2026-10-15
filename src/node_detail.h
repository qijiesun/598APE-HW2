#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <node.h>

namespace genetic {
namespace detail {

static constexpr float MIN_VAL = 0.001f;

inline bool is_terminal(node::type t) {
  return t == node::type::variable || t == node::type::constant;
}

inline bool is_nonterminal(node::type t) { return !is_terminal(t); }

inline int arity(node::type t) {
  if (node::type::unary_begin <= t && t <= node::type::unary_end) {
    return 1;
  }
  if (node::type::binary_begin <= t && t <= node::type::binary_end) {
    return 2;
  }
  return 0;
}

// `data` assumed to be stored in col-major format
inline float evaluate_node(const node &n, const float *data, const uint64_t stride,
                    const uint64_t idx, const float *in) {
  if (n.t == node::type::constant) {
    return n.u.val;
  } else if (n.t == node::type::variable) {
    return data[(stride * n.u.fid) + idx];
  } else {
    auto abs_inval = fabsf(in[0]), abs_inval1 = fabsf(in[1]);
    // note: keep the case statements in alphabetical order under each category
    // of operators.
    switch (n.t) {
    // binary operators
    case node::type::add:
      return in[0] + in[1];
    case node::type::atan2:
      return atan2f(in[0], in[1]);
    case node::type::div:
      return abs_inval1 < MIN_VAL ? 1.0f : (in[0]/in[1]);//fdividef(in[0], in[1]);
    case node::type::fdim:
      return fdimf(in[0], in[1]);
    case node::type::gt:
      return in[0] > in[1] ? 1.0f : 0.0f;
    case node::type::max:
      return fmaxf(in[0], in[1]);
    case node::type::min:
      return fminf(in[0], in[1]);
    case node::type::mul:
      return in[0] * in[1];
    case node::type::pow:
      return powf(in[0], in[1]);
    case node::type::sub:
      return in[0] - in[1];
    // unary operators
    case node::type::abs:
      return abs_inval;
    case node::type::acos:
      return acosf(in[0]);
    case node::type::acosh:
      return acoshf(in[0]);
    case node::type::asin:
      return asinf(in[0]);
    case node::type::asinh:
      return asinhf(in[0]);
    case node::type::atan:
      return atanf(in[0]);
    case node::type::atanh:
      return atanhf(in[0]);
    case node::type::cbrt:
      return cbrtf(in[0]);
    case node::type::cos:
      return cosf(in[0]);
    case node::type::cosh:
      return coshf(in[0]);
    case node::type::cube:
      return in[0] * in[0] * in[0];
    case node::type::exp:
      return expf(in[0]);
    case node::type::inv:
      return abs_inval < MIN_VAL ? 0.f : 1.f / in[0];
    case node::type::log:
      return abs_inval < MIN_VAL ? 0.f : logf(abs_inval);
    case node::type::neg:
      return -in[0];
    case node::type::rcbrt:
      return static_cast<float>(1.0) / cbrtf(in[0]);
    case node::type::rsqrt:
      return static_cast<float>(1.0) / sqrtf(abs_inval);
    case node::type::sin:
      return sinf(in[0]);
    case node::type::sinh:
      return sinhf(in[0]);
    case node::type::sq:
      return in[0] * in[0];
    case node::type::sqrt:
      return sqrtf(abs_inval);
    case node::type::tan:
      return tanf(in[0]);
    case node::type::tanh:
      return tanhf(in[0]);
    // shouldn't reach here!
    default:
      return 0.f;
    };
  }
}

// O5 evaluates one node for an entire sample column, performing type dispatch
// once per node instead of once per row. Formulas match evaluate_node.
inline void evaluate_node_column(const node &n, const float *data,
                                 const uint64_t stride, const float *in0,
                                 const float *in1, float *out) {
#define O5_UNARY(EXPR)                                                         \
  do {                                                                         \
    for (uint64_t i = 0; i < stride; ++i) {                                    \
      const float x = in0[i];                                                   \
      out[i] = (EXPR);                                                          \
    }                                                                          \
  } while (false)
#define O5_BINARY(EXPR)                                                        \
  do {                                                                         \
    for (uint64_t i = 0; i < stride; ++i) {                                    \
      const float x = in0[i];                                                   \
      const float y = in1[i];                                                   \
      out[i] = (EXPR);                                                          \
    }                                                                          \
  } while (false)

  switch (n.t) {
  case node::type::constant: std::fill(out, out + stride, n.u.val); break;
  case node::type::variable:
    std::copy(data + stride * n.u.fid, data + stride * (n.u.fid + 1), out);
    break;
  case node::type::add: O5_BINARY(x + y); break;
  case node::type::atan2: O5_BINARY(atan2f(x, y)); break;
  case node::type::div: O5_BINARY(fabsf(y) < MIN_VAL ? 1.0f : x / y); break;
  case node::type::fdim: O5_BINARY(fdimf(x, y)); break;
  case node::type::gt: O5_BINARY(x > y ? 1.0f : 0.0f); break;
  case node::type::max: O5_BINARY(fmaxf(x, y)); break;
  case node::type::min: O5_BINARY(fminf(x, y)); break;
  case node::type::mul: O5_BINARY(x * y); break;
  case node::type::pow: O5_BINARY(powf(x, y)); break;
  case node::type::sub: O5_BINARY(x - y); break;
  case node::type::abs: O5_UNARY(fabsf(x)); break;
  case node::type::acos: O5_UNARY(acosf(x)); break;
  case node::type::acosh: O5_UNARY(acoshf(x)); break;
  case node::type::asin: O5_UNARY(asinf(x)); break;
  case node::type::asinh: O5_UNARY(asinhf(x)); break;
  case node::type::atan: O5_UNARY(atanf(x)); break;
  case node::type::atanh: O5_UNARY(atanhf(x)); break;
  case node::type::cbrt: O5_UNARY(cbrtf(x)); break;
  case node::type::cos: O5_UNARY(cosf(x)); break;
  case node::type::cosh: O5_UNARY(coshf(x)); break;
  case node::type::cube: O5_UNARY(x * x * x); break;
  case node::type::exp: O5_UNARY(expf(x)); break;
  case node::type::inv: O5_UNARY(fabsf(x) < MIN_VAL ? 0.0f : 1.0f / x); break;
  case node::type::log: O5_UNARY(fabsf(x) < MIN_VAL ? 0.0f : logf(fabsf(x))); break;
  case node::type::neg: O5_UNARY(-x); break;
  case node::type::rcbrt: O5_UNARY(1.0f / cbrtf(x)); break;
  case node::type::rsqrt: O5_UNARY(1.0f / sqrtf(fabsf(x))); break;
  case node::type::sin: O5_UNARY(sinf(x)); break;
  case node::type::sinh: O5_UNARY(sinhf(x)); break;
  case node::type::sq: O5_UNARY(x * x); break;
  case node::type::sqrt: O5_UNARY(sqrtf(fabsf(x))); break;
  case node::type::tan: O5_UNARY(tanf(x)); break;
  case node::type::tanh: O5_UNARY(tanhf(x)); break;
  default: std::fill(out, out + stride, 0.0f); break;
  }

#undef O5_BINARY
#undef O5_UNARY
}

} // namespace detail
} // namespace genetic

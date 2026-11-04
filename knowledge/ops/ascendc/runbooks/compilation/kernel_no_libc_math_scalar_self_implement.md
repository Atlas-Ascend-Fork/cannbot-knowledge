---
type: "Runbook"
title: "kernel 无设备侧 libc：数学函数与宿主宏需自实现"
description: "AscendC kernel 编译环境（tikcpp/ccec）不提供标准库数学函数，floorf/rintf/fminf/fmaxf 报 \"use of undeclared identifier\"；需在 kernel 头文件自实现 static __aicore__ inline 标量版本（floor/fmin/fmax/round-half-to-even），并替换全部调用点。R2：经 host 头文件链声明的 floor() 则报 call to __host__ function from __aicore__ function——向量路径 Cast 的 RoundMode::CAST_FLOOR 是设备指令支持的取整模式、不受影响。R3：INFINITY 宏同样是未声明标识符，half ±inf 须按位模式构造（+inf=0x7C00，-inf=0xFC00，quiet NaN=0x7E00）。"
tags: [task.debugging, topic.compilation, topic.compute.elementwise.math_function]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/guide/technical_appendix/cpp_standard_support/cpp_language_restrictions/general_restrictions.md
    role: constraint
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/tool_interface/NumericLimits_utils/Infinity.md
    role: supporting
created_at: '2026-09-16T11:20:30Z'
updated_at: '2026-10-28T10:01:10Z'
platforms: ["310p", "950"]
---

# kernel 无 libc 数学函数需自实现

## 现象

自定义算子的 kernel 头文件 `op_kernel/arch35/<op>.h` 里，坐标取整与钳位直接用了标准 C 数学函数：`floorf`（bilinear 邻域索引、reflection 取模）、`rintf`（nearest 就近取整）、`fminf/fmaxf`（border 钳位）。host 侧库全部编译通过后，kernel 编译报错原文：

```text
op_kernel/arch35/bench_no_harness_grid_sampler_3d.h:232:31: error: use of undeclared identifier 'floorf'; did you mean '__floorf'?
op_kernel/arch35/bench_no_harness_grid_sampler_3d.h:232:31: error: use of undeclared identifier 'floorf'; did you mean '__floorf'?
```

（rintf/fminf/fmaxf 同样未声明。）在 CANN 安装的 tikcpp 目录里搜 math 头文件与这些符号均无命中——AscendC kernel 编译环境不带 libc math 声明，编译器只提示内置的 `__floorf`。

## 适用场景

- 工程形态：AscendC kernel 开发（op_kernel/*.h/*.cpp，标量路径中的取整/钳位/取模计算）。
- API 路径：kernel 内标量数学——无 AscendC 官方标量 floor/rint API 的场景；编译环境为 tikcpp/ccec（CANN 9.1.0）。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0（`exp2f` 未声明 → `__builtin_exp2f` 链接失败 → 自实现 `KExp2` 通过精度）；ascend950/arch35 内核编译（CANN 9.1.0）——与 frontmatter `platforms` 一致；CANN 版本以正文实测记录为准。
- 适用粒度：platform_wide（编译环境行为，与算子无关）；本卡按同一根因的三种报错文本（未声明 / `__host__` 拒绝 / 宿主宏未声明）分派处置，各自验证平台见 `## 同一根因的三种报错形态`。
- 路线优先级：recommended_fastpath。
- 明确不适用 / 未验证场景：向量化的 Floor/Round 等 AscendC 向量 API（本卡为标量路径）；`__floorf` 等编译器内置路径（存在提示但未采用未验证）；其他 CANN 版本。

## 根因

AscendC kernel 侧编译环境（tikcpp/ccec）不提供标准库 `math.h` 的 `floorf/fminf/fmaxf/rintf` 声明，kernel 代码中直接调用这些函数即编译失败；标量数学需开发者自行实现。


### 310P/CANN 9.1.0 补充（exp2f 未声明 + `__builtin_exp2f` 编过链不过）

同一类问题在 Ascend310P3（dav-m200）+ CANN 9.1.0 上以 `exp2f` 的形态再次出现，并且多出一层"前端放行、链接失败"的陷阱：

- 直接写 `exp2f(x)`：`error: use of undeclared identifier 'exp2f'`——与 `floorf`/`fminf`/`fmaxf` 同因（kernel 侧没有 libc 数学声明）。
- 改写 `__builtin_exp2f(x)`：**编译通过**，但 kernel 链接阶段报未定义符号（该内建在 m200 后端没有对应实现）。这是本卡要补的第二种失败形态：**"编过"不等于"链得过"**，必须确认最终的 kernel `.o` / `.so` 是否真正生成。
- 最终按本卡同一路线自实现 `KExp2`：把 `x` 拆成整数部分 `e = floor(x)` 与小数部分 `f = x - e`，小数域用 6 项 Taylor 展开 2^f，再用 IEEE754 指数位拼装（`reinterpret_cast<uint32_t>` 后加 `e << 23`）；对 `e < -126` 的下溢区显式返回 0，避免负指数位移的未定义行为。

结论：`exp2f` 属于同一"kernel 无标准数学库"家族；`__builtin_*` 前缀不是规避手段，只是把报错从编译期推迟到链接期。

## 解决配方

修复（两部分）：

**1. 在 kernel 头文件添加标量实现（verbatim）：**

```cpp
// 标量数学函数（Kernel 环境中标准数学函数不可用）
static __aicore__ inline float ScalarFloor(float x)
{
    int32_t i = (int32_t)x;
    float fi = (float)i;
    return (fi > x) ? (fi - 1.0f) : fi;
}

static __aicore__ inline float ScalarFmin(float a, float b)
{
    return (a < b) ? a : b;
}

static __aicore__ inline float ScalarFmax(float a, float b)
{
    return (a > b) ? a : b;
}

static __aicore__ inline float ScalarRint(float x)
{
    // round-half-to-even (banker's rounding)
    float lower = ScalarFloor(x);
    float frac = x - lower;
    if (frac < 0.5f) {
        return lower;
    }
    if (frac > 0.5f) {
        return lower + 1.0f;
    }
    // frac == 0.5: round to even
    int32_t lowerInt = (int32_t)lower;
    return (lowerInt % 2 == 0) ? lower : (lower + 1.0f);
}
```

**2. 替换全部调用点（修复前 → 修复后，逐处 verbatim）：**

```cpp
        int32_t w0 = (int32_t)floorf(wPadded);   // -> int32_t w0 = (int32_t)ScalarFloor(wPadded);
        int32_t h0 = (int32_t)floorf(hPadded);   // -> int32_t h0 = (int32_t)ScalarFloor(hPadded);
        int32_t d0 = (int32_t)floorf(dPadded);   // -> int32_t d0 = (int32_t)ScalarFloor(dPadded);
        int32_t wn = (int32_t)rintf(wPadded);    // -> int32_t wn = (int32_t)ScalarRint(wPadded);
        int32_t hn = (int32_t)rintf(hPadded);    // -> int32_t hn = (int32_t)ScalarRint(hPadded);
        int32_t dn = (int32_t)rintf(dPadded);    // -> int32_t dn = (int32_t)ScalarRint(dPadded);
```

border 钳位（ApplyPadding 内，完整函数修复后形态）：

```cpp
template <typename T, int INTERP_MODE>
__aicore__ inline float GridSampler3D<T, INTERP_MODE>::ApplyPadding(
    float coord, int64_t size, int64_t padMode, bool alignCorners)
{
    float low, high;
    if (alignCorners) {
        low = 0.0f;
        high = (float)(size - 1);
    } else {
        low = -0.5f;
        high = (float)size - 0.5f;
    }

    switch (padMode) {
        case 0: // zeros: 不修改坐标
            return coord;
        case 1: // border: 钳位到 [0, size-1]
            return ScalarFmin(ScalarFmax(coord, 0.0f), (float)(size - 1));
        case 2: // reflection
            return ComputeReflection(coord, low, high);
        default:
            return coord;
    }
}
```

reflection 取模（ComputeReflection 内，修复后形态）：

```cpp
    float s = coord - low;
    // 正数取模: s mod (2*span)
    s = s - 2.0f * span * ScalarFloor(s / (2.0f * span));
```

## 设计决策

- 选自实现而不是编译器内置 `__floorf`：内置符号名是编译器实现细节（无官方声明头、跨版本/跨编译器不保证），自实现行为可控且可移植。
- `ScalarRint` 显式实现 round-half-to-even（银行家舍入）而非简单 +0.5 截断：对齐 torch `nearbyint` 的取整语义（nearest 模式的索引与 torch golden 逐位一致依赖此语义）。
- `ScalarFloor` 用 int32 截断 + 回退：依赖坐标范围在 int32 内（网格采样坐标量级远小于 2^31），超范围行为未定义——见失效边界。

## 预防

- kernel 侧代码从 CPU 原型迁移时，扫描一遍 `floorf/ceilf/rintf/nearbyintf/fminf/fmaxf/fabsf/powf` 等标准数学调用；kernel 环境可用的只有 AscendC 向量 API 与自实现标量。
- 编译报 "did you mean '__floorf'?" 时，把它当作"该环境无标准 math"的信号，而不是直接改用 `__` 前缀符号。

## 验证信号

问题与验证来源：算子骨架开发过程中 kernel 编译发现，替换调用点后重编验证。

- 修复前：`error: use of undeclared identifier 'floorf'; did you mean '__floorf'?`（两处重复报错）（来源平台：ascend950 kernel 编译 / CANN 9.1.0；证据等级：tool_observed）。
- 修复后：同一构建中 floorf/rintf/fminf/fmaxf 错误全部消失，kernel 编译推进到下一独立问题（DataCopyPad 签名）；最终 `binary` target 100% 构建成功，生成两个 ascend950 kernel `.o`（来源平台：ascend950；证据等级：tool_observed）。


- 310P/CANN 9.1.0 下直接调用 `exp2f`：kernel 编译报 `error: use of undeclared identifier 'exp2f'`（来源平台：310P；证据等级：tool_observed）。
- 改写 `__builtin_exp2f` 后编译阶段通过，但 kernel 链接报未定义符号、产物未生成（来源平台：310P；证据等级：tool_observed）。
- 自实现 `KExp2`（6 项 Taylor + 指数位拼装 + 下溢分支）后 kernel 构建成功，算子对 CPU golden 的精度用例通过（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- `ScalarFloor`/`ScalarRint` 基于 int32 截断：坐标超出 int32 范围时行为未定义；超大 D/H/W（>2^31）场景需换实现。
- `ScalarRint` 的取偶分支假设 |x| < 2^31 且 lower 可被精确表示。
- 未在 CANN 官方向量 API（Floor/Round）上对比数值一致性；本实现只保证与 torch CPU golden 的 nearest 索引语义对齐（同一会话 CPU 黄金自测通过佐证）。
- 相邻知识：`std::min/std::max` 在 `__aicore__` 内同样无法解析（改显式条件比较，见库内「__aicore__ 内 std::min/max 编译失败」卡）；device 侧 `sqrtf` 需改向量 Sqrt 或 CCE 内建（见库内「bisheng 不接受 device 侧 sqrtf」卡）——本卡与两者同属"kernel 环境无标准数学库"家族。

**未决项**：

- CANN 是否提供官方标量数学头（tikcpp 内搜 math.h 无命中，未深挖官方推荐做法）——接续点：查 tikcfw/asc 头文件中是否有 scalar math 工具。

- `KExp2` 只覆盖 f32 标量输入；bf16/fp16 输入需先归一为 f32 再调用。
- 大正指数（`e` 接近 128）时的溢出行为未单独验证；极端定义域建议加显式饱和分支。
- `__builtin_*` 系列在其它后端是否可链接未验证；本卡只证明 310P/CANN 9.1.0 上不行。
- `exp2` 的精度只在算子层面用 golden 验证，未做逐点 ULP 统计。

## 坏实践

- 在 kernel 里直接 `#include <cmath>` 或调用标准数学函数——环境没有这些声明。
- 用 `__floorf` 等编译器内置符号——无声明头、可移植性差。


- 看到 `__builtin_exp2f` 编译通过就认为可用，不检查 kernel 产物是否生成、不跑端到端——把链接期错误留到运行期。
- 自实现指数函数时不做下溢/溢出分支，直接用负指数位移。
- 把 `exp2f` 的未声明误当成缺 include，反复调整头文件顺序。

## 误诊

旧轨迹无成条误诊记录；310P 轨迹新增两条：

- 误诊：`exp2f` 报未声明时，先怀疑少了 `<cmath>` / `math.h` 包含（agent_reported）。真实原因是 kernel 编译环境根本不提供该声明，加 include 无效。
- 误诊：`__builtin_exp2f` 编译通过后，把随后出现的加载失败归因于驱动或环境（agent_reported）；实际是 kernel 没链接出来。

## 同一根因的三种报错形态

本卡是**同一根因**（设备侧 kernel 编译单元没有 libc/STL，既无标量数学声明，也不暴露宿主宏）的家族卡，不是三个独立根因的聚合。三种形态按报错文本分派处置：

- R1「未声明标识符」：`floorf/rintf/fminf/fmaxf/exp2f` 等直接报 undeclared → 在 kernel 头文件自实现标量版本并替换调用点（见 `## 解决配方`）。
- R2「有声明但被 `__host__` 拒绝」：`floor` 经 glibc 声明链进入 kernel TU，报 `call to __host__ function from __aicore__ function` → 批量取整改走向量 `Cast` 的 `RoundMode::CAST_FLOOR`，标量路径自实现或整型截断。
- R3「宿主宏未声明」：`INFINITY`/`NAN`/`HUGE_VAL` 报 undeclared → 按 IEEE 754 位模式构造（half：+inf=0x7C00，-inf=0xFC00，quiet NaN=0x7E00）。

### R2：floor() 的第二种错误形态（独立 trace，Ascend950PR/arch35，TBE 编译链）

kernel 标量代码 `static_cast<int32_t>(floor(h))`（双线性插值坐标取整）走 CompileStage.INFERCHANNEL 编译失败——与 R1 的 "undeclared identifier" 不同，这里的 `floor` 经 glibc `bits/mathcalls.h` 链**有声明**，但带 `__host__` 属性：

```text
error: no matching function for call to 'floor' (<file>.h:232:39)
candidate function not viable: call to __host__ function from __aicore__ function (bits/mathcalls.h:165)
Exception: An error occurred during compile phases of CompileStage.INFERCHANNEL
```

即设备侧 `__aicore__` 函数不允许调用 host 函数（无设备端标量 libm），与 R1 的"无声明"是同一"kernel 环境无标准数学库"事实的两种面目。**向量路径不受影响**：`Cast` 带 `RoundMode::CAST_FLOOR` 是设备指令支持的取整模式——需要批量取整时优先走向量 Cast(CAST_FLOOR)，标量路径按 R1 自实现（或整型转换语义可接受时直接 `static_cast<int32_t>` 截断）。

### R3：INFINITY 宏未声明，half ±inf 按位模式构造（独立 trace，TopK padding 场景，CANN 9.1.0）

kernel 头文件里为 TopK padding 构造 half 极值，初版按宿主习惯写 `static_cast<half>(±INFINITY)`，设备侧编译报：

```text
op_kernel/arch35/<op>.h:45:43: error: use of undeclared identifier 'INFINITY'（同一行报两次，多模板实例重复出现）
RuntimeError: Kernel Compilation Error: OpType <Op> Kernel File ...!
```

AscendC 设备侧编译环境不暴露宿主 `math.h` 的 `INFINITY` 宏；half 的 ±inf 必须按 IEEE 754 半精度位模式直接构造（+inf=0x7C00，-inf=0xFC00，quiet NaN=0x7E00）：

```cpp
inline __aicore__ half GetPadValue(bool isLargest)
{
    union {
        unsigned short u16;
        half h;
    } cvt;
    cvt.u16 = isLargest ? 0xFC00 : 0x7C00;   // -inf : +inf
    return cvt.h;
}
```

配套判读与坏实践：

- 凡在 `__aicore__` 代码里看到 `INFINITY`/`NAN`/`HUGE_VAL` 类宿主宏，都替换为位模式构造（union 或 `__builtin_memcpy` 位视图）并在注释标注位模式来源；`std::numeric_limits<float>::infinity()` 同样编译不过（设备侧无 STL）。
- 不要用有限大数（如 65504.0）代替 ±inf 做 TopK padding：输入本身可能含 ±inf 或极值时会被误选入 top-k。
- padding 填充时机与极值方向选择的完整配方见 [TopK padding 区须 SetValue 填极值卡](../precision/topk_padding_extreme_value_fill.md)；bf16/float 的位模式宽度不同，需按 IEEE 754 重算（未验证）。

### 复现增量验证信号

- R2 修复前：`candidate function not viable: call to __host__ function from __aicore__ function (bits/mathcalls.h:165)` + `CompileStage.INFERCHANNEL` 异常（来源平台：950；证据等级：tool_observed）。修复后（整型化/自实现替换）干净构建通过（来源平台：950；证据等级：tool_observed）。
- R3 修复前：`error: use of undeclared identifier 'INFINITY'`（多处），kernel binary json 未生成（来源平台：950；证据等级：tool_observed）。修复后（union 位模式）：INFINITY 错误消失、构建全绿 `[INFO] Build completed successfully!`，kernel 二进制与 .run 包正常落盘（来源平台：950；证据等级：tool_observed）。

### 复现增量边界

- R2 的 `__host__` 拒绝形态与 R1 的"未声明"形态取决于头文件包含链是否把 glibc math 声明带进 kernel TU，同一环境下两种都可能遇到；处置相同（自实现/向量 API/整型化）。
- R3 位模式常量只对 IEEE 754 binary16（half）成立；TopK padding 语义依赖"inf 被认为是极大值"的排序约定，底层 API 对 inf 处理不同时 padding 方向需重评。

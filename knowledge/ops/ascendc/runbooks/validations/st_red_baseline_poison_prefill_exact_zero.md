---
type: "Runbook"
title: ST 红基线输出 poison 防 stub 巧合命中
description: 接口桩 kernel 不写输出时，输出设备缓冲预填有限哨兵（fp32 3e30/fp16 30000/bf16 截断 3e30），防全零期望用例在红基线意外通过。
tags: [task.testing, topic.implementation]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["950"]
---
# ST 红基线输出 poison 防 stub 巧合命中


## 现象

在算子开发的"测试先行"阶段（ST 用例先于 kernel 数值实现落地），被测 kernel 是接口桩：入口只做 `AscendC::InitSocState()` + `REGISTER_TILING_DEFAULT` + `GET_TILING_DATA_WITH_STRUCT` + `PipeBarrier<PIPE_ALL>()`，不写任何输出。此时 aclnn 两段式调用链（GetWorkspaceSize → aclnn → Sync）**全程返回 OK**，输出设备缓冲保持调用前的内容。

如果测试框架按惯常做法把输出缓冲清零（`aclrtMemset(..., 0, ...)`）再跑数值比对，会遇到一个隐蔽的坑：**期望值恰好全零的用例会"巧合通过"**。本场景的具体算子是 GRU Cell 反向（grad_hy 全零输入 → 五路输出全零的 spec 用例）：golden 链上 `gin = go·(1−z)·(1−n²)` 等五条梯度在 go=0 时全部为 0，若 actual 也被清成 0，则 mere=0 < th，比对通过——而此时 kernel 明明什么都没算。红基线验收口径"本分支数值用例期望通过数 = 0"被击穿，测试先行阶段失去了"证明比对器真的能抓住错误输出"的自证能力（即"stub 不得巧合命中 oracle"原则）。

## 适用场景

- 工程形态：aclnn ST（ops-registry-invoke 算子仓 `tests/aclnn/`），测试先行/红基线阶段（kernel 为接口桩或部分未实现）。
- API 路径：`aclrtMemcpy`（H2D poison 上载）+ aclnn 两段式调用链；输出张量由测试方构造描述符并分配设备内存。
- 验证过的平台与 CANN 版本：Ascend950PR（npu-smi 25.7.rc1.6）+ CANN 9.0.0-beta.2（与 frontmatter `platforms` 严格一致）。
- 适用粒度：`operator_family`——任何"输出为调用方分配的设备缓冲、kernel 可能不写"的自定义算子 ST 均适用。
- 路线优先级：`recommended_fastpath`（红基线诚实性的必要手段，无替代方案时直接采用）。
- 明确不适用/未验证场景：kernel 已实现后的绿基线（poison 会被全量覆写，无害但非必要——本 trace 未验证绿基线）；输出确需保留上轮内容的增量语义算子；kernel 只写部分输出的场景（poison 仍能暴露未写区域，但"部分通过"的解读需结合用例设计）；多 stream 并发写同一输出缓冲的场景。

## 根因

接口桩 kernel 不写输出，且 **aclnn 框架层也不会清零或触碰输出缓冲**——输出设备内存保持测试方上送的原值。于是"实际输出"完全由测试方的输出缓冲初始化决定：

- 初始化为 0（memset 清零）+ 期望全零用例（如 go=0 → 五路输出全 0）→ `rel_err = |0−0|/(0+1e-7) = 0` → mere=0 < th → **PASS（假通过）**。
- 红基线的意义在于证明"比对器能抓住错误输出"；一条巧合通过就破坏了这层自证。

机制算式（为什么选有限大哨兵而不是 0 或 NaN）：

- 哨兵 s 与 golden g 的 rel_err = |s−g|/(|g|+1e-7)。取 s=3.0e30（fp32）、g∈O(0.05–2)（随机数据域）→ rel_err ≈ 3.0e30/|g| ≈ 1.5e30–6e31，mere/mare 远超任何阈值 → 稳定 FAIL。
- 取 fp16 哨兵 30000（< 65504 最大有限值，且远离 U(0,1)/U(−2,2) 数据域）→ rel_err ≈ 30000/|g|，同样稳定 FAIL。
- **不用 NaN 做哨兵**：NaN 位置匹配语义（两侧同 NaN → 匹配）下，NaN 哨兵会与特殊值用例 golden 中的 NaN 位置"同位匹配"（如单 NaN 注入用例的对应列）。虽然整体仍会 FAIL（其余位置错配），但有限哨兵把这最后一类巧合也彻底排除——特殊值用例的 NaN 位置检出必须来自 kernel 真实写入的 NaN，而不是缓冲残留。

## 解决配方

每次调用 aclnn 前，把五路输出缓冲（host 侧填充 + H2D memcpy）覆盖为按 dtype 的**有限哨兵**：

1. fp32 → `3.0e30f`；fp16 → fp16 位型(30000.0)；bf16 → 截断位型(3.0e30)。
2. 每轮调用（含确定性双跑的每一轮）都重新 poison——stub 下两轮输出同为哨兵，位级一致，不影响确定性检查；绿基线下 kernel 覆写，poison 无副作用。
3. (0,) 空输出（0 字节）跳过 poison，也跳过比对（空短路）。
4. 确定性双跑各自 fresh poison 后比对两轮输出位级一致。

为什么不用 `aclrtMemset`：字节 pattern 无法跨 dtype 表达任意位型——memset 0x7F 在 fp32 是 0x7F7F7F7F（≈3.4e38，有限），在 fp16 却是 0x7F7F（指数全 1、尾数非 0 → NaN）；host 填充 + memcpy 是唯一 dtype 精确的方式。

## 设计决策

- **哨兵值选择**：必须(a)有限、(b)远离用例数据值域与 golden 值域、(c)在该 dtype 可精确表示。fp32/bf16 用 3.0e30（bf16 与 fp32 共享指数域，3e30 可表示）；fp16 上限 65504，取 30000。
- **NaN 哨根被否决**：与"NaN 同位匹配"语义存在残余巧合面（见根因节推导），有限哨兵零巧合。
- **poison 放在每轮调用内而非套件开头**：保证确定性双跑各自从已知态出发；也让"kernel 到底写没写"在两轮日志里可读。
- **方向转换器只需截断舍入**：哨兵只须"非零有限"，float→fp16/bf16 的 poison 方向转换用截断即可，无须 round-to-nearest（数值语义转换见 [fp16/bf16 位流转 float 零依赖转换卡](cxx_fp16_bf16_bitstream_to_float_conversion.md)）。
- 当前方案属 `recommended_fastpath` 路线。

## 系统信息

- 实现落点：`operators/ThnnFusedGruCellGrad_package/tests/aclnn/test_aclnn.cpp`（函数 `FillPoison` / `FloatToFp16Bits` / `FloatToBf16Bits`，及 `RunStCase` 中的 poison 调用点）。
- 运行环境：Ascend950PR + CANN 9.0.0-beta.2；构建链 tests/aclnn/CMakeLists.txt（ascendcl/nnopbase/cust_opapi）。
- 相关文件：`test_aclnn.cpp`（写）、`st_cases_branch0.json`（用例清单，S1 为 exact_zero 全零期望用例）、`gen_st_oracle.py`（golden 期望位流）。

## 完整代码

verbatim 取自本 trace 的 `test_aclnn.cpp` 写入事件：

```cpp
// 输出 poison 填充：接口桩阶段 kernel 不写输出，poison 保证红基线不被
// 「device 缓冲恰为零/恰为期望」巧合命中（stub 不得巧合命中 oracle）。
static void FillPoison(std::vector<uint8_t>& buf, StDtype dt)
{
    uint16_t pat16 = 0;
    float pat32 = 0.0f;
    if (dt == StDtype::FP32) {
        pat32 = 3.0e30f;
    } else if (dt == StDtype::FP16) {
        pat16 = FloatToFp16Bits(30000.0f);
    } else {
        pat16 = FloatToBf16Bits(3.0e30f);
    }
    const size_t es = (dt == StDtype::FP32) ? 4 : 2;
    for (size_t i = 0; i + es <= buf.size(); i += es) {
        if (dt == StDtype::FP32) {
            std::memcpy(buf.data() + i, &pat32, sizeof(pat32));
        } else {
            std::memcpy(buf.data() + i, &pat16, sizeof(pat16));
        }
    }
}
```

```cpp
// float → fp16 / bf16 位流（仅用于输出 poison 填充；截断舍入即可，只须非零有限）
static uint16_t FloatToFp16Bits(float f)
{
    uint32_t x = 0;
    std::memcpy(&x, &f, sizeof(x));
    const uint32_t sign = (x >> 16) & 0x8000U;
    const uint32_t expF = (x >> 23) & 0xFFU;
    const uint32_t man = x & 0x7FFFFFU;
    if (expF == 0xFFU) {
        return static_cast<uint16_t>(sign | 0x7BFFU);  // Inf/NaN → 最大有限（poison 保持有限）
    }
    const int32_t exp = static_cast<int32_t>(expF) - 127 + 15;
    if (exp >= 0x1F) {
        return static_cast<uint16_t>(sign | 0x7BFFU);
    }
    if (exp <= 0) {
        return static_cast<uint16_t>(sign | 0x0001U);
    }
    return static_cast<uint16_t>(sign | (static_cast<uint32_t>(exp) << 10) | (man >> 13));
}

static uint16_t FloatToBf16Bits(float f)
{
    uint32_t x = 0;
    std::memcpy(&x, &f, sizeof(x));
    uint32_t bits = x >> 16;
    if (bits == 0x7F80U || bits == 0xFF80U) {
        bits = 0x7F7FU;  // Inf/NaN → 有限大值
    }
    return static_cast<uint16_t>(bits);
}
```

调用点（`RunStCase` 内，每轮执行前）：

```cpp
// 5) 同输入连跑 2 次（确定性必检项）：每次 poison 输出 → 完整两段式 aclnn → 读回
std::vector<uint8_t> runOut[2][5];
for (int run = 0; run < 2 && ok; ++run) {
    // 5.1 poison 输出（红基线反巧合：接口桩不写输出时保持非期望值）
    for (int k = 0; k < 5; ++k) {
        if (outBytes[k] == 0) {
            continue;
        }
        std::vector<uint8_t> poison(outBytes[k]);
        FillPoison(poison, c.dtype);
        if (aclrtMemcpy(devOut[k], outBytes[k], poison.data(), outBytes[k],
                        ACL_MEMCPY_HOST_TO_DEVICE) != ACL_SUCCESS) {
            res.frameworkError = true;
            res.message = "aclrtMemcpy poison 失败";
            ok = false;
            break;
        }
    }
    ...  // 描述符构造 → GetWorkspaceSize → aclnn → Sync → 读回
}
```

## 预防

- 测试先行阶段写 ST 时，输出缓冲初始化策略要过一遍"期望值反推"：枚举 manifest 里期望全零/常量的用例，确认清零初始化不会与之巧合相等；有疑义直接上 poison。
- poison 值选好后做一次量级核对：`|s|/max(|g|)` 应超出阈值至少 10 个数量级（本例 3e30/2 ≈ 1.5e30 vs 阈 1e-5）。
- 特殊值用例（NaN/Inf 注入）存在时，优先有限哨兵而非 NaN 哨兵。

## 验证信号

来源说明：以下信号来自 GRU Cell 反向算子 Branch-0 aclnn ST（测试先行、kernel 接口桩）的红基线实测，同一套 20 条 manifest 用例、Ascend950PR 上单次运行。

- S1（grad_hy 全零 → 期望五路全 0，exact_zero 断言）实测 `grad_input_gates FAIL (exact_zero: nonZeroActual=96 nonZeroOracle=0)`、`grad_hidden_gates FAIL (exact_zero: nonZeroActual=96 nonZeroOracle=0)`——输出保持 poison 非零值被精确断言拦下，oracle 侧全零自检通过；全零期望用例**未**巧合通过（来源平台：950；证据等级：tool_observed）。
- 红基线总量：`Branch-0 ST summary: PASSED=0 FAILED=20 ERROR=0 TOTAL=20`——20/20 全 FAIL，无一条数值用例意外通过（来源平台：950；证据等级：tool_observed）。
- FAIL 指标量级与 poison 保留一致（stub 未写输出的间接证据）：E01 fp32 `mere=8.254e+32 mare=5.964e+34`，与 `3.0e30/|g|`（g∈O(0.05–2)）的推导量级吻合；E02 fp16 `mare=2.280e+08` 与 `30000/|g|` 吻合（来源平台：950；证据等级：tool_observed）。
- 同输入连跑 2 次全部 20 例 `determinism OK(bitwise,2runs)`——poison 不干扰确定性检查（stub 下两轮同为哨兵位型）（来源平台：950；证据等级：tool_observed）。
- E04（has_bias=false）两路 (0,) 空 bias 输出跳过 poison 且不产生误报（空短路）（来源平台：950；证据等级：tool_observed）。

## 失效边界

- 哨兵值落入用例数据/golden 值域时会产生局部元素匹配——选值时须避开（本例数据域 U(−2,2)/U(0,1)，golden 值域同量级，3e30/30000 无交集）。
- 绿基线（kernel 实现后）poison 被全量覆写的行为未在本 trace 验证（红基线 trace）；采用后建议绿基线首跑核对 poison 无残留。
- 若 kernel 合法地只写部分输出（如尾部块清零逻辑缺失），poison 会暴露为"未写区域保持哨兵"——这正确反映了缺陷，但需要结合逐元素 diff 定位。
- fp16 哨兵 30000 与"近最大值"类极值用例（如全 60000 输入的 golden 输出可达 ~6e4）同量级时，mare 仍远超阈值（rel_err≈30000/60000≈0.5 ≫ 1e-3），判 FAIL 不受影响，但"个别元素恰好等于哨兵"的理论可能仍在——极值用例值域贴近 30000 时改选其他哨兵。

## 坏实践

- 输出缓冲 `aclrtMemset` 清零后直接跑红基线：全零期望用例（go=0 类）巧合通过，红基线失真。
- 用 NaN 做哨兵：与"同位 NaN 匹配"语义存在残余巧合面（特殊值用例的 golden NaN 位置会被缓冲残留命中）。
- 只在套件开头 poison 一次：确定性双跑的第二轮起点状态不受控，位级一致性结论失效。

## 误诊

- "stub kernel 会把输出清零/框架会帮忙初始化"——不会：aclnn 只把设备指针传给 kernel，桩不写就是保持原值；这是本卡整个前提的反面误判。
- "红基线反正都会挂，输出初始化随便"——正是全零期望用例这条漏网之鱼让"随便"变成假通过。



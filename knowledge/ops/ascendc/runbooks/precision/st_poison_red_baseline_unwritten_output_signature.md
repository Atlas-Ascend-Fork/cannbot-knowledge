---
type: "Runbook"
title: 红基线 mere~1e33＝poison 保持：stub 未写输出
description: aclnn ST 每次调用前往输出缓冲预填有限毒值（fp32=3.0e30）；stub kernel 零 IO 早退使输出保持毒值，比对产生 1e30~1e37 量级 mere/mare、位级确定、nan_inf_mismatch=0 的特征真红签名。
tags: [task.testing, topic.precision, topic.implementation.debugging]
status: stable
sources: []
created_at: '2026-09-09T11:49:41Z'
updated_at: '2026-09-09T11:49:41Z'
platforms: ["950"]
cann_versions: ["9.0.0-beta.2"]
---
# 红基线 mere~1e33＝poison 保持：stub 未写输出


## 现象

在一个对标 torch GRU Cell 反向的融合算子仓（aclnn 接口，host tiling 按 tilingKey 分发 base/group/empty 三路模板）做 group 分支的 Kernel ST 验收，处于"测试先行"阶段：group 模板 kernel 还是占位 stub（入口可编译但 ProcessGroup 全核早退、零计算零 IO），base 模板已实现并通过 20 条 ST。执行 `cd operators/…/tests/aclnn && ./run.sh`（一键重编译 vendor 包 + 独立 oracle 重生成期望值 + 实跑测试二进制）后，输出：

```text
==== ThnnFusedGruCellGrad aclnn smoke summary: 1/1 cases OK ====
==== Branch-0 ST summary: PASSED=20 FAILED=0 ERROR=0 TOTAL=20 ====
==== Branch-1 ST summary: PASSED=0 FAILED=11 ERROR=0 TOTAL=11 (group kernel 数值链未实现阶段 0 passed 属预期红基线，内部任务编号（原始输出原文的一部分）) ====
```

run.sh 退出码 255。Branch-1 的 11 例全部 FAIL，单例明细（正向用例 E07，fp32 B=512 H=16）五路输出全部失败且数值量级异常巨大：

```text
[ST] E07 fp32 B=512 H=16 bias=1 …
     grad_input_gates   FAIL mere=4.376e+33 mare=1.330e+37 mare_budget=1.000e-04 [10*th] th=1.0e-05 nan_inf_mismatch=0
     grad_hidden_gates  FAIL mere=5.180e+33 mare=1.330e+37 mare_budget=1.000e-04 [10*th] th=1.0e-05 nan_inf_mismatch=0
     grad_hx            FAIL mere=8.954e+31 mare=4.752e+34 mare_budget=1.000e-04 [10*th] th=1.0e-05 nan_inf_mismatch=0
     grad_input_bias    FAIL mere=2.548e+30 mare=1.796e+31 mare_budget=1.000e-04 [max(10*th,10*noise=1.671e-06)] th=1.0e-05 nan_inf_mismatch=0
     grad_hidden_bias   FAIL mere=2.637e+30 mare=1.494e+31 mare_budget=1.000e-04 [max(10*th,10*noise=2.515e-06)] th=1.0e-05 nan_inf_mismatch=0
     determinism OK(bitwise,2runs) | verdict FAIL
```

验收要判别的问题：这 11 个 FAIL 是"数值型真红"（kernel 未执行、输出保持测试预填的毒值——测试先行的预期状态），还是测试框架错误/数据问题？判别依据是 mere/mare 的量级恰为毒值幅度、nan_inf_mismatch=0、ERROR=0、两次运行位级一致。

## 适用场景

- 工程形态：aclnn 算子仓（ops-registry-invoke 流程）ST 的 TDD 红基线验收与判读；多分支模板中"被验分支为接口桩"的阶段。
- API 路径：两段式 aclnn 调用链（GetWorkspaceSize → aclnn）；aclrtMemcpy 输出缓冲预填；ST harness（run.sh / test_aclnn.cpp / gen_st_oracle.py 双 manifest 槽）。
- 验证过的平台与 CANN 版本：Ascend 950（ascend950 构建目标、实机 aclnn 运行）+ CANN 9.0.0-beta.2（与 frontmatter platforms 一致）。
- 适用粒度（transfer_scope）：operator_family——该 ST harness 模板按算子复制使用（换算子名即复用），"aclnn 输出缓冲由调用方分配、框架不清零"的运行时语义跨算子一致。
- 路线优先级：recommended_fastpath（毒值签名判真红；毒值填充为该 harness 的既定反巧合设计）。
- 明确不适用/未验证场景：kernel 已实现后的 FAIL 判读（毒值签名消失，须按数值精度问题分析）；非本 harness 模板的测试框架（毒值与度量名不同，须按各自框架对账）；GEIR/TTK kernel 模式等其它接入层未验证。

## 根因

aclnn 调用不清零调用方分配的输出缓冲：接口桩阶段的 kernel 零 IO 早退后，输出保持测试在每次调用前预填的有限毒值（fp32 pat=3.0e30f），与 oracle 期望值比对即产生 mere/mare 达 1e30~1e37 量级的特征失败——这是"kernel 未写输出"的直接证据，而非框架错误。

量级对账（不跳步）：fp32 毒值 3.0e30，期望值 O(1) 量级 → rel_err=|a−g|/(|g|+1e-7) ≈ 3.0e30/|g|；对 |g|~0.7~5 的元素 mere 落在 1e30 量级（观测 2.5e30~5.2e33，偏大者对应小 |g| 元素）；mare（对大 |g| 平均）1e31~1e37。五路输出全部毒值量级 + nan_inf_mismatch=0（毒值经 Inf/NaN→最大有限 0x7BFF 位流转换保持有限）+ determinism OK（毒值确定性填写）→ 唯一解释是 kernel 未写输出。

## 判别方法

红基线判读清单（TDD 测试先行阶段，被验分支 kernel 为桩）：

1. 汇总行：本分支 PASSED=0 且 FAILED=TOTAL、ERROR=0；冒烟与已实现分支保持全绿（本例 1/1 与 20/20）。
2. 单例明细：全部输出 mere/mare 均达毒值量级（fp32 ~1e30+）、nan_inf_mismatch=0、determinism OK(bitwise,2runs)。
3. 日志中 grep "ERROR" 的命中须逐条核对内容——本例 `grep -c "ERROR"` 返回 2，两处均为汇总行 "ERROR=0" 字样，不是框架错误。
4. 退出码：run.sh 契约为"smoke + Branch-0/1 ST 全过 = 0"，红基线阶段非 0（本例 255）属预期，不作为框架错误判据。

四条齐备 → 数值型真红（kernel 未写输出），按"本分支数值用例期望通过数 = 0"口径放行验收；任一不满足（ERROR>0、nan_inf_mismatch>0、mere 在正常数值量级、determinism MISMATCH）→ 框架/数据问题，先修测试再谈红基线。

## 设计决策

- 毒值取"远超任何合法数值但保持有限"的量级（fp32 3.0e30、fp16 30000、bf16 3.0e30）：既要不被"device 缓冲恰为零/恰为期望"巧合命中（harness 注释原文：poison 保证红基线不被巧合命中，stub 不得巧合命中 oracle），又要避免 Inf/NaN 污染 nan_inf_mismatch 判读通道。
- 每次 aclnn 调用前对五路输出重新 aclrtMemcpy 毒值上载（两段式调用链外层、每 run 每输出）：保证 2-run 确定性检查测的是 kernel 行为而非缓冲残留。
- 放弃的候选：不填毒值靠"输出全零"判红（device 缓冲可能恰为零，假绿风险）；毒值用 Inf/NaN（会触发 nan_inf_mismatch，混淆"kernel 未写"与"kernel 写了坏值"两类失败）。
- 当前方案属哪档路线：recommended_fastpath。

## 系统信息

- 工具链：CANN 9.0.0-beta.2（ASCEND_OPP_PATH=<home>/Ascend/cann-9.0.0-beta.2/opp），GCC 13.3.0，python3 3.12.9 + torch 2.7.1+cpu（数据生成侧，TORCH_DEVICE_BACKEND_AUTOLOAD=0 关 torch_npu autoload）。
- 目标平台：ascend950（实机 ACLNN 运行）。
- 目录布局：operators/<pkg>/tests/aclnn/{run.sh, test_aclnn.cpp, gen_st_oracle.py, st_cases_branch0/1.json}；oracle：docs/<op>/develop/golden.py（纯 torch/numpy，独立于被测 kernel）。
- 相关文件（与事件流实际读写一一对应）：test_aclnn.cpp（FillPoison/位流辅助/2-run 确定性/汇总与退出码）、run.sh（一键链路与退出码契约注释）、st_cases_branch1.json（红基线用例清单）、golden.py（期望值）、op_kernel/arch35/<op>_group.h（stub）。

## 完整代码

毒值填充与位流辅助（test_aclnn.cpp，verbatim）：

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

每 run 毒值上载 + 2-run 确定性（test_aclnn.cpp 主循环，verbatim）：

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
    …
}
```

退出码契约（run.sh 尾部注释，verbatim）：

```bash
# 退出码：smoke + Branch-0/1 ST 全过 = 0；Branch-1（group）kernel 数值链未实现的
## 阶段为红基线（本分支数值用例 0 passed，Branch-0 用例与最小通路用例保持通过），
## 退出非 0 属预期（内部任务编号（原始输出原文的一部分）；Task 28.2.4 kernel 实现后转绿）。
```

## 预防

- 新算子复制该 ST harness 模板时保留毒值填充与 2-run 确定性检查（反巧合红基线的最小保障）。
- 判读红基线按上文四条清单核对，不要只看退出码或 FAILED 数。
- grep ERROR 类快速判读必须逐条看内容，防止汇总行 "ERROR=0" 被误计为框架错误。

## 验证信号

来源说明：以下信号来自该 group 分支 Kernel ST 一次独立验收会话内的实跑输出与 harness 源码读取（验收者自跑 run.sh 并逐例判读明细，未引用任何前序日志）。

- Branch-1 ST PASSED=0 FAILED=11 ERROR=0 TOTAL=11；Branch-0 20/20、冒烟 1/1 保持通过（来源平台：950；证据等级：tool_observed）
- E07 五路输出 mere=4.376e+33 / 5.180e+33 / 8.954e+31 / 2.548e+30 / 2.637e+30、mare 至 1.330e+37、五路 nan_inf_mismatch=0、determinism OK(bitwise,2runs)（来源平台：950；证据等级：tool_observed）
- run.sh 退出码 255（契约：全过=0，红基线非 0 属预期）（来源平台：950；证据等级：tool_observed）
- 毒值机制代码（FillPoison：fp32 3.0e30f / fp16 30000.0f / bf16 3.0e30f；Inf/NaN→0x7BFF 保持有限；每 run 每输出重新上载）取自 harness 源码读取，绑定仓库当前提交（来源平台：950；证据等级：tool_observed）

## 失效边界

- fp16 毒值 30000（mere 量级 ~1e4 档）与 bf16 3.0e30 的签名量级不同，判读时按各自 dtype 毒值对账。
- 该签名仅在"输出缓冲由调用方分配且框架不清零 + 测试预填毒值"的 harness 成立；aclnn 不清零输出为本仓实测口径，其它接入层（GEIR/TTK kernel 模式）未验证。
- kernel 实现后红转绿，本签名不再出现；届时 FAIL 须按数值精度分析，不得沿用毒值判读。
- 毒值具体数值（3.0e30/30000）是本 harness 的设计选择，复制模板时可调，但须保持"非零有限且远离合法数值域"两个性质。

## 坏实践

- 只看 run.sh 退出码非 0 就判"测试失败/框架坏了"——红基线阶段非 0 是契约内预期。
- 把 "ERROR" 字样的 grep 计数当框架错误数——汇总行 "ERROR=0" 会被计入。
- 不填毒值直接判红——device 缓冲恰为零/恰为期望的巧合会造成假绿（stub 巧合命中 oracle）。
- 毒值填 Inf/NaN——混淆 nan_inf_mismatch 判读通道，无法区分"kernel 未写"与"kernel 写坏"。

## 误诊

- "11/11 FAIL 是数据生成（oracle）问题"——期望值由独立 golden 生成且 Branch-0 20/20 全过（同一 oracle 同一链路），排除。
- "mere 1e33 是数值溢出"——量级恰为毒值 3.0e30 的相对误差换算结果（见根因算式），五路一致、位级确定，非计算溢出。
- "日志有 2 处 ERROR"——均为 "ERROR=0" 汇总行字样，非框架错误。

## 未决事项

无未解决遗留：根因已追到机制层（调用方输出缓冲不被清零 + 毒值反巧合设计 + stub 零 IO），红基线为测试先行阶段的预期状态、无需修复；判读清单已闭环。

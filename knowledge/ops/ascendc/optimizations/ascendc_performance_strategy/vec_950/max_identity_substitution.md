---
type: Optimization
title: 恒等冗余消除：以链上已有中间量替换整遍归约扫描
description: 两遍 softmax 第二遍 max 归约 m2=max(s) 位级恒等于 rcp1=fl(1.0/sum1)（或其 RNE 量化像 castUp(castDown(rcp1))），以常数条指令替代整遍 UB 扫描。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/max-identity-substitution.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "恒等替换必须给出位级等价论证（本 run：e_max=exp(0)=1.0 精确、sum1>=1、IEEE 1.0x=x、RNE cast 单调 ⇒ 恒等成立），不可仅凭数学近似",
      "新增变体承载替换（Pass2IdentityRowAligned/Unaligned + wrapper），已验证的 VF 本体零改动，保证可独立回滚",
      "降级路径（本 run cChunkMode 的 ±inf 域 case12）与 row-split 路径必须字面不动"
    ],
    "excluded_conditions": [
      "被替换的归约结果在语义上不恒等于已有值（例如 sum1 可能 <1 或 1.0x≠x 成立不了的域）时不适用",
      "走非 IEEE 舍入/非单调 cast 的降级域不在本机制范围，须显式排除在派发之外",
      "若该归约并非整遍 UB 扫描（指令数已很低），替换收益不足以摊薄新增变体的代码体积"
    ],
    "required_conditions": [
      "存在「某遍归约的结果位级恒等于链上已有中间量」的结构性冗余（本 run：两遍 softmax 第二遍 m2=max(s) 恒等于 rcp1=fl(1.0/sum1)，或其 RNE 量化像 castUp(castDown(rcp1))）",
      "被替换的归约是一整遍 UB 扫描（本 run softmax_vf.h 中 pass2 max 扫在全部主路径字面保留 4 处），替换后降为常数条指令",
      "vec 管线主导（本 run 20 case aiv_vec_time 合计 859us，~91% aiv_time；case9 vec 占比 97%）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 27.949,
      "before_us": 29.314,
      "operator": "softmax",
      "operator_class": "normalization",
      "pairs": 10,
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "session_ids": [
        "ses_f798906cbffeJknPOZk7NfH7lC",
        "ses_f7951be0effeRqq5tjqgGcetWw",
        "ses_f78e2b4deffetLzsr4i00EqcxW",
        "ses_f78c5713fffeflJFz3hJ7XIeCV"
      ],
      "speedup": 1.0489,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "redundant-ub-scan",
      "vec-ub-traffic-bound",
      "structural-identity"
    ],
    "pattern": "identity-substitution",
    "structure": [
      "two-pass-normalization",
      "mathematical-identity-proof",
      "constant-instruction-replacement",
      "degraded-path-untouched"
    ]
  },
  "generality": "op_class",
  "id": "SMX-MAX-IDENTITY-SUBSTITUTION",
  "implementation_steps": [
    "softmax_vf.h: Norm1Pass2FusedRowCallee 删除 Max 累加/ReduceMax/槽存/BRC 链，扫 B 直接用 rcp1",
    "softmax_vf.h: QuantRtPass2FusedRowCallee/Vf + wrapper 增加 sum1 入参，m2 = castUp(castDown(rcp1))",
    "softmax_vf.h: 新增 Pass2IdentityRowAligned/Unaligned + Pass2IdentityStats* + wrapper ComputeSoftmaxPass2StatsIdentity",
    "softmax_vf.h: 新增 SoftmaxNorm2ndAligned/Unaligned + wrapper SoftmaxNormalize2ndInplace",
    "softmax_vf.h: castTraitF322F16 定义上移（声明顺序修复，repair 1）",
    "softmax_kernel_a.h: Compute 对齐分支 QuantRt 传 s1、else 分支切换 Identity wrapper",
    "softmax_kernel_b.h: Compute 第二次 SoftmaxNormalizeInplace -> SoftmaxNormalize2ndInplace",
    "cChunkMode 降级路径与 row-split 路径零改动"
  ],
  "intent": "把两遍归约中位级冗余的第二遍扫描替换为链上已有中间量，用常数条指令替代整遍 UB 扫描，直接削减 vec 管线在 UB 上的访存与发射。",
  "mechanism": "两遍 softmax 第二遍 max 归约 m2=max(s) 位级恒等于 rcp1=fl(1.0/sum1)（或其 RNE 量化像 castUp(castDown(rcp1))），以常数条指令替代整遍 UB 扫描。",
  "name": "恒等冗余消除：以链上已有中间量替换整遍归约扫描",
  "operator_class": "normalization",
  "operator_scope": "多遍归约的融合类算子（本 run 为两遍 softmax 的对齐/非对齐双模板主路径）：某一遍归约的结果位级恒等于链上已有中间量，且该归约实现为一整遍 UB 扫描",
  "principle": "多遍归约里常存在结构性冗余：第二遍所需的统计量可由第一遍的中间量解析给出，而不必重新扫一遍数据。判定标准是位级恒等而非近似——一旦 F(已有值) 与 G(重扫结果) 在所有可派发域上逐位相同，整遍 UB 扫描就可降为常数条指令。这类替换的风险全在「恒等式在降级域是否仍成立」，因此实现要求新增变体承载替换、原 VF 本体零改动、降级路径字面不动，使回滚是纯派发切换而非算法回退。",
  "related_anti_patterns": [],
  "risks": [
    "恒等式依赖若干数值事实（e_max=exp(0)=1.0 精确、sum1>=1、IEEE 1.0x=x、RNE cast 单调），若上游链的数值性质改变（如换舍入模式）则论证失效",
    "新增变体抬高 kernel 代码体积，需确认未触碰 case 无副作用回退",
    "build 门假阳性教训：外层 rc=0 不代表 kernel 编译成功，必须核验 kernel 二进制产物非空（本 run 首轮 cand 实为旧二进制回退）"
  ],
  "slug": "max-identity-substitution",
  "summary": "两遍 softmax 第二遍 max 归约 m2=max(s) 位级恒等于 rcp1=fl(1.0/sum1)（或其 RNE 量化像 castUp(castDown(rcp1))），以常数条指令替代整遍 UB 扫描。形式化配对校验 speedup=1.0489（29.314→27.949us，10 对 balanced alternating），19/20 case 改善，精度 20/20。",
  "verification": {
    "correctness": [
      "精度 20/20 PASS（accuracy_r2 于真实新二进制，kernel .o 时间戳核验）",
      "位级等价论证：e_max=exp(0)=1.0 精确、sum1>=1、IEEE 1.0x=x、RNE cast 单调 ⇒ 恒等式成立；±inf 域（case12）走未触碰的 cChunkMode 降级路径",
      "编译 2 次修复（castTrait 声明顺序 + RoundMode 命名空间），修复后 kernel 产物核验非空、可复现构建（md5 一致）"
    ],
    "performance": [
      "形式化配对校验 10 对 balanced alternating：29.314→27.949us，speedup 1.0489",
      "19/20 case 改善且与筛选结论一致（无歧义）；筛选 +4.55%，formal +4.89%",
      "累计链路 39.766→27.949us（1.423x）"
    ],
    "rollback_signals": [
      "恒等式在某个可派发域不再位级成立（精度门回退）",
      "未触碰 case（cChunkMode / row-split）出现超出噪声的回退",
      "kernel 二进制产物为空或与源码不匹配（build 假阳性）"
    ]
  }
}
-->

# 性能优化策略：恒等冗余消除：以链上已有中间量替换整遍归约扫描

两遍 softmax 第二遍 max 归约 m2=max(s) 位级恒等于 rcp1=fl(1.0/sum1)（或其 RNE 量化像 castUp(castDown(rcp1))），以常数条指令替代整遍 UB 扫描。形式化配对校验 speedup=1.0489（29.314→27.949us，10 对 balanced alternating），19/20 case 改善，精度 20/20。

## 1. 原理

多遍归约里常存在结构性冗余：第二遍所需的统计量可由第一遍的中间量解析给出，而不必重新扫一遍数据。判定标准是位级恒等而非近似——一旦 F(已有值) 与 G(重扫结果) 在所有可派发域上逐位相同，整遍 UB 扫描就可降为常数条指令。这类替换的风险全在「恒等式在降级域是否仍成立」，因此实现要求新增变体承载替换、原 VF 本体零改动、降级路径字面不动，使回滚是纯派发切换而非算法回退。

实现机制：两遍 softmax 第二遍 max 归约 m2=max(s) 位级恒等于 rcp1=fl(1.0/sum1)（或其 RNE 量化像 castUp(castDown(rcp1))），以常数条指令替代整遍 UB 扫描。

## 2. 性能问题模式

- 优化目标：把两遍归约中位级冗余的第二遍扫描替换为链上已有中间量，用常数条指令替代整遍 UB 扫描，直接削减 vec 管线在 UB 上的访存与发射
- 适用数据流：多遍归约的融合类算子（本 run 为两遍 softmax 的对齐/非对齐双模板主路径）：某一遍归约的结果位级恒等于链上已有中间量，且该归约实现为一整遍 UB 扫描
- Feature signature：`{"bottleneck": ["redundant-ub-scan", "vec-ub-traffic-bound", "structural-identity"], "pattern": "identity-substitution", "structure": ["two-pass-normalization", "mathematical-identity-proof", "constant-instruction-replacement", "degraded-path-untouched"]}`

## 3. 正确性红线

- 恒等式依赖若干数值事实（e_max=exp(0)=1.0 精确、sum1>=1、IEEE 1.0x=x、RNE cast 单调），若上游链的数值性质改变（如换舍入模式）则论证失效
- 新增变体抬高 kernel 代码体积，需确认未触碰 case 无副作用回退
- build 门假阳性教训：外层 rc=0 不代表 kernel 编译成功，必须核验 kernel 二进制产物非空（本 run 首轮 cand 实为旧二进制回退）

资源与硬件约束：

- 恒等替换必须给出位级等价论证（本 run：e_max=exp(0)=1.0 精确、sum1>=1、IEEE 1.0x=x、RNE cast 单调 ⇒ 恒等成立），不可仅凭数学近似
- 新增变体承载替换（Pass2IdentityRowAligned/Unaligned + wrapper），已验证的 VF 本体零改动，保证可独立回滚
- 降级路径（本 run cChunkMode 的 ±inf 域 case12）与 row-split 路径必须字面不动

## 4. 泛化条件

- 策略作用域：op_class：normalization

适用：

- 存在「某遍归约的结果位级恒等于链上已有中间量」的结构性冗余（本 run：两遍 softmax 第二遍 m2=max(s) 恒等于 rcp1=fl(1.0/sum1)，或其 RNE 量化像 castUp(castDown(rcp1))）
- 被替换的归约是一整遍 UB 扫描（本 run softmax_vf.h 中 pass2 max 扫在全部主路径字面保留 4 处），替换后降为常数条指令
- vec 管线主导（本 run 20 case aiv_vec_time 合计 859us，~91% aiv_time；case9 vec 占比 97%）

不适用：

- 被替换的归约结果在语义上不恒等于已有值（例如 sum1 可能 <1 或 1.0x≠x 成立不了的域）时不适用
- 走非 IEEE 舍入/非单调 cast 的降级域不在本机制范围，须显式排除在派发之外
- 若该归约并非整遍 UB 扫描（指令数已很低），替换收益不足以摊薄新增变体的代码体积

## 5. 实施步骤

1. softmax_vf.h: Norm1Pass2FusedRowCallee 删除 Max 累加/ReduceMax/槽存/BRC 链，扫 B 直接用 rcp1
2. softmax_vf.h: QuantRtPass2FusedRowCallee/Vf + wrapper 增加 sum1 入参，m2 = castUp(castDown(rcp1))
3. softmax_vf.h: 新增 Pass2IdentityRowAligned/Unaligned + Pass2IdentityStats* + wrapper ComputeSoftmaxPass2StatsIdentity
4. softmax_vf.h: 新增 SoftmaxNorm2ndAligned/Unaligned + wrapper SoftmaxNormalize2ndInplace
5. softmax_vf.h: castTraitF322F16 定义上移（声明顺序修复，repair 1）
6. softmax_kernel_a.h: Compute 对齐分支 QuantRt 传 s1、else 分支切换 Identity wrapper
7. softmax_kernel_b.h: Compute 第二次 SoftmaxNormalizeInplace -> SoftmaxNormalize2ndInplace
8. cChunkMode 降级路径与 row-split 路径零改动

## 6. LLM 前置问题

- 目标实现是否满足：存在「某遍归约的结果位级恒等于链上已有中间量」的结构性冗余（本 run：两遍 softmax 第二遍 m2=max(s) 恒等于 rcp1=fl(1.0/sum1)，或其 RNE 量化像 castUp(castDown(rcp1))）？
- 目标实现是否满足：被替换的归约是一整遍 UB 扫描（本 run softmax_vf.h 中 pass2 max 扫在全部主路径字面保留 4 处），替换后降为常数条指令？
- 目标实现是否满足：vec 管线主导（本 run 20 case aiv_vec_time 合计 859us，~91% aiv_time；case9 vec 占比 97%）？
- 是否命中排除条件：被替换的归约结果在语义上不恒等于已有值（例如 sum1 可能 <1 或 1.0x≠x 成立不了的域）时不适用？

## 7. 验收标准

正确性：

- 精度 20/20 PASS（accuracy_r2 于真实新二进制，kernel .o 时间戳核验）
- 位级等价论证：e_max=exp(0)=1.0 精确、sum1>=1、IEEE 1.0x=x、RNE cast 单调 ⇒ 恒等式成立；±inf 域（case12）走未触碰的 cChunkMode 降级路径
- 编译 2 次修复（castTrait 声明顺序 + RoundMode 命名空间），修复后 kernel 产物核验非空、可复现构建（md5 一致）

性能：

- 形式化配对校验 10 对 balanced alternating：29.314→27.949us，speedup 1.0489
- 19/20 case 改善且与筛选结论一致（无歧义）；筛选 +4.55%，formal +4.89%
- 累计链路 39.766→27.949us（1.423x）

回滚信号：

- 恒等式在某个可派发域不再位级成立（精度门回退）
- 未触碰 case（cChunkMode / row-split）出现超出噪声的回退
- kernel 二进制产物为空或与源码不匹配（build 假阳性）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260909_010738-free-001（operator=softmax, status=accepted, speedup=1.0489, 29.314→27.949us, 10 对配对）

## 检索卡（短卡）

动作：把位级冗余的整遍归约扫描替换为链上已有中间量，新增变体承载替换、原 VF 本体零改动。
适用：多遍归约中某遍结果位级恒等于链上中间量，且该归约是一整遍 UB 扫描、vec 管线主导。
限制：恒等替换须位级等价论证；降级路径（cChunkMode ±inf）与 row-split 须字面不动；须核验 kernel 产物非空。
范围：normalization 多遍归约融合算子的对齐/非对齐主路径。
检索词：ReduceMax、BRC 广播、RNE cast、castUp/castDown、rcp1、cChunkMode
机会：第二遍 max 归约整遍重扫 UB，指令数本已很低却仍占向量发射槽。
代价：新增变体抬高 kernel 代码体积。

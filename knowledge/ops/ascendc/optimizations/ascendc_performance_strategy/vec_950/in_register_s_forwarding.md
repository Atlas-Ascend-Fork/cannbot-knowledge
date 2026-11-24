---
type: Optimization
title: 中间量寄存器直通：消除多 pass 链的 UB store→reload 往返与 RAW 屏障
description: 两遍 softmax 的中间量 s 当前必须落 UB 再读回（模板A 对齐 fp32 2r2w、DX 量化路径 4r4w，非对齐同构，模板B 2 访存遍 + 每 unit 4 条 RAW 屏障）。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/in-register-s-forwarding.md
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
      "中间量的唯一下游消费必须是逐元素纯函数（本 run：e2=exp(s−m2)），否则寄存器直通会改变消费次数或副作用语义",
      "合成所需的全部参数须在中间量生产前即可构造（本 run：m2 恒等于 rcp1，由 d001 已证，故可在 s 生产前构造），否则链序无法前移",
      "位级等价须由同指令同操作数序列保证——只删存取往返与屏障，不改任何算术形式",
      "降级路径（本 run cChunkMode case12 ±inf 域）与已验证 VT 组件零改动"
    ],
    "excluded_conditions": [
      "对齐快路径等往返本就便宜的链不适用：本 run round_01 在对齐路径强行链式化导致 +10~42% 回退，round_02 以 scope 修复切回原链——位点条件「往返昂贵链」是该机制成立的前提",
      "中间量有多个消费者、或消费者非逐元素纯函数（需要跨行/跨段可见）时不适用",
      "中间量需要在屏障点对外可见（如被其它管线读取）时不适用"
    ],
    "required_conditions": [
      "存在多 pass 计算链，中间量以 UB store→reload 往返传递（本 run 模板A DX 快路径 s 链 4r4w + 2 条 RAW 屏障/行；fp32 2r2w + 1 屏障/行；模板B n1.sp3 写 s 与 n2.sp2 读 s 为纯往返 + 每 unit 4 条 LocalMemBar）",
      "该往返在预算中占可观份额（本 run 模板A DX 4/14、fp32 2/10、模板B 2/11 访存份额）",
      "vec 管线主导（本 run aiv_vec 803.4us / aiv_mte2 403.2 / aiv_mte3 242.7 / aiv_scalar 96.2，vec 占 aiv 约 72%）",
      "中间量的构造与消费均为确定性逐元素运算（Mul/Div/Cast RNE/Exp），寄存器值与落 UB 读回值位级相同"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 26.22,
      "before_us": 27.948,
      "operator": "softmax",
      "operator_class": "normalization",
      "pairs": 10,
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "session_ids": [
        "ses_f78bdff14ffe48WzgRnepMi3EI",
        "ses_f784f3a96ffe03DfQ4Caa4qzvX"
      ],
      "speedup": 1.0659,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "ub-store-reload-roundtrip",
      "raw-barrier-overhead",
      "vec-ub-traffic-bound"
    ],
    "pattern": "in-register-forwarding",
    "structure": [
      "multi-pass-chain",
      "intermediate-elision",
      "same-instruction-operand-order",
      "scope-conditioned-on-expensive-roundtrip"
    ]
  },
  "generality": "op_class",
  "id": "SMX-IN-REGISTER-S-FORWARDING",
  "implementation_steps": [
    "softmax_vf.h: 新增链式组件 Norm1QuantPass2ChainedRowCallee/UnalignedCallee + Vf wrapper（对齐/非对齐两型，DX cast↓/cast↑ 链内寄存器完成），e→s=fl(e×rcp1)→e2=exp(s−m2) 单遍直通，s 不落 UB",
    "softmax_vf.h: 新增 SoftmaxNormNoDivAligned/Unaligned 与 SoftmaxNormChain12Aligned/Unaligned（模板B：n1 子遍1+2 去子遍3 + Chain12 寄存器直通消 n2.sp2 读 s 往返，屏障 4→2/unit），wrapper ComputeNorm1QuantPass2Chained / SoftmaxNormalizeChain12Inplace",
    "softmax_kernel_a.h: Compute 非对齐 else 分支切换为 ComputeNorm1QuantPass2Chained（替代 Norm1 + flat QuantRoundTrip + Pass2Identity 三段，消 4r4w→1r1w DX / 2r2w→1r1w fp32）",
    "softmax_kernel_a.h（round_02 scope 修复）: 对齐快路径恢复 baseline 原链（round_01 筛选证伪链式在对齐路径回退 +10~42%）",
    "softmax_kernel_b.h: Compute 第二次 SoftmaxNormalizeInplace → SoftmaxNormalizeChain12Inplace（NoDiv+Chain12）",
    "cChunkMode 降级路径与已验证 VT 组件零改动"
  ],
  "intent": "消除多 pass 链上中间量的 UB store→reload 往返与配套 RAW 屏障：把只有逐元素纯函数消费的中间量全程驻留寄存器，把两遍链路合并为单遍直通，直接削减 vec 管线的 UB 访存遍数与屏障数。",
  "mechanism": "两遍 softmax 的中间量 s（第一遍归一化输出 = 第二遍 exp 扫输入）当前必须落 UB 再读回：模板A 对齐快路径 2r2w（DX 量化路径再叠加 QuantRt 的 tmp cast↓/st cast↑ 两整遍往返，合计 4r4w）；非对齐路径同构 4r4w；模板B 2 访存遍 + 每 unit 4 条 RAW 屏障。s 的唯一下游消费是 e2=exp(s−m2)（逐元素纯函数），而 m2 恒等值（d001 已证 m2≡rcp1）在 s 生产前即可构造——故 s 可全程驻留寄存器：e→s=fl(e×rcp1)[DX: cast↓→cast↑]→e2=exp(s−m2) 单遍融合完成，仅物化 e2。同指令同操作数序列，仅删除存取往返与屏障，位级等价。",
  "name": "中间量寄存器直通：消除多 pass 链的 UB store→reload 往返与 RAW 屏障",
  "operator_class": "normalization",
  "operator_scope": "多 pass 计算链的融合类算子：中间量以 UB 往返传递、唯一下游消费是逐元素纯函数、且合成所需参数可在中间量生产前构造（含 DX 量化 cast↓/cast↑ 往返叠加的路径）",
  "principle": "多 pass 链把中间量物化到 UB 再读回，代价是访存遍数 + 每遍的 RAW 屏障。若该中间量的唯一下游消费是逐元素纯函数、且消费所需参数能在生产前构造，则中间量可全程驻留寄存器，两遍合并为单遍直通——同指令同操作数序列，位级等价，只是删掉了往返与屏障。关键边界是「往返昂贵链」：对齐快路径等往返本就便宜的位点强行链式化反而回退（本 run +10~42%），故该机制必须按位点条件派发，不可无差别应用。",
  "related_anti_patterns": [],
  "risks": [
    "位点条件误判会引入回退：round_01 无差别链式化在对齐快路径回退 +10~42%，必须按「往返昂贵链」筛位点（round_02 scope 修复）",
    "寄存器压力上升，R 大或 liveness 长的链可能触发 spill，需以 kernel .o 体积与实测双重确认",
    "屏障删除后若存在未识别的跨管线可见性依赖，会表现为偶发精度问题——须以真实新二进制跑精度（build 假阳性防护）"
  ],
  "slug": "in-register-s-forwarding",
  "summary": "两遍 softmax 的中间量 s 当前必须落 UB 再读回（模板A 对齐 fp32 2r2w、DX 量化路径 4r4w，非对齐同构，模板B 2 访存遍 + 每 unit 4 条 RAW 屏障）。因 s 唯一下游消费是逐元素纯函数 e2=exp(s−m2) 且 m2 恒等值可在 s 生产前构造，故 s 可全程驻留寄存器，两遍合并为单遍直通，仅物化 e2。形式化配对校验 speedup=1.0659（27.948→26.220us，10 对 ABBA，逐对 1.0622~1.0709 全部>1）。",
  "verification": {
    "correctness": [
      "精度 20/20 PASS（baseline/round_01/round_02 三份 pytest 均 20 passed，运行于真实新二进制）",
      "位级等价论证完备：同指令同操作数序列，仅删存取往返与屏障；cChunkMode 降级路径与已验证 VT 组件零改动"
    ],
    "performance": [
      "形式化配对 10 对 ABBA 平衡交替（B=10 A=10，order B A A B B A A B B A A B B A A B B A A B）：27.948→26.220us，speedup 1.0659",
      "逐对 1.0622~1.0709 全部 >1（median 1.0652）；169/200 case-pair 更快",
      "改善集中在非对齐 Gather/Scatter 链与模板B 多遍扫位点（-7.5~-17.8%）；对齐快路径与 cChunkMode 域持平",
      "两轮均真实产出 kernel 二进制（时间戳 + md5 核验，与 baseline 可区分），0 编译错误、0 编译修复；累计链路 39.766→26.220us（1.517x）"
    ],
    "rollback_signals": [
      "对齐快路径等往返廉价位点出现回退（本 run round_01 已实证）",
      "kernel .o 体积异常膨胀或 md5 与源码不可区分（build 假阳性）",
      "cChunkMode / 模板B 等零改动域出现超出噪声的回退",
      "精度门在真实新二进制上失败"
    ]
  }
}
-->

# 性能优化策略：中间量寄存器直通：消除多 pass 链的 UB store→reload 往返与 RAW 屏障

两遍 softmax 的中间量 s 当前必须落 UB 再读回（模板A 对齐 fp32 2r2w、DX 量化路径 4r4w，非对齐同构，模板B 2 访存遍 + 每 unit 4 条 RAW 屏障）。因 s 唯一下游消费是逐元素纯函数 e2=exp(s−m2) 且 m2 恒等值可在 s 生产前构造，故 s 可全程驻留寄存器，两遍合并为单遍直通，仅物化 e2。形式化配对校验 speedup=1.0659（27.948→26.220us，10 对 ABBA，逐对 1.0622~1.0709 全部>1）。

## 1. 原理

多 pass 链把中间量物化到 UB 再读回，代价是访存遍数 + 每遍的 RAW 屏障。若该中间量的唯一下游消费是逐元素纯函数、且消费所需参数能在生产前构造，则中间量可全程驻留寄存器，两遍合并为单遍直通——同指令同操作数序列，位级等价，只是删掉了往返与屏障。关键边界是「往返昂贵链」：对齐快路径等往返本就便宜的位点强行链式化反而回退（本 run +10~42%），故该机制必须按位点条件派发，不可无差别应用。

实现机制：两遍 softmax 的中间量 s（第一遍归一化输出 = 第二遍 exp 扫输入）当前必须落 UB 再读回：模板A 对齐快路径 2r2w（DX 量化路径再叠加 QuantRt 的 tmp cast↓/st cast↑ 两整遍往返，合计 4r4w）；非对齐路径同构 4r4w；模板B 2 访存遍 + 每 unit 4 条 RAW 屏障。s 的唯一下游消费是 e2=exp(s−m2)（逐元素纯函数），而 m2 恒等值（d001 已证 m2≡rcp1）在 s 生产前即可构造——故 s 可全程驻留寄存器：e→s=fl(e×rcp1)[DX: cast↓→cast↑]→e2=exp(s−m2) 单遍融合完成，仅物化 e2。同指令同操作数序列，仅删除存取往返与屏障，位级等价。

## 2. 性能问题模式

- 优化目标：消除多 pass 链上中间量的 UB store→reload 往返与配套 RAW 屏障：把只有逐元素纯函数消费的中间量全程驻留寄存器，把两遍链路合并为单遍直通，直接削减 vec 管线的 UB 访存遍数与屏障数
- 适用数据流：多 pass 计算链的融合类算子：中间量以 UB 往返传递、唯一下游消费是逐元素纯函数、且合成所需参数可在中间量生产前构造（含 DX 量化 cast↓/cast↑ 往返叠加的路径）
- Feature signature：`{"bottleneck": ["ub-store-reload-roundtrip", "raw-barrier-overhead", "vec-ub-traffic-bound"], "pattern": "in-register-forwarding", "structure": ["multi-pass-chain", "intermediate-elision", "same-instruction-operand-order", "scope-conditioned-on-expensive-roundtrip"]}`

## 3. 正确性红线

- 位点条件误判会引入回退：round_01 无差别链式化在对齐快路径回退 +10~42%，必须按「往返昂贵链」筛位点（round_02 scope 修复）
- 寄存器压力上升，R 大或 liveness 长的链可能触发 spill，需以 kernel .o 体积与实测双重确认
- 屏障删除后若存在未识别的跨管线可见性依赖，会表现为偶发精度问题——须以真实新二进制跑精度（build 假阳性防护）

资源与硬件约束：

- 中间量的唯一下游消费必须是逐元素纯函数（本 run：e2=exp(s−m2)），否则寄存器直通会改变消费次数或副作用语义
- 合成所需的全部参数须在中间量生产前即可构造（本 run：m2 恒等于 rcp1，由 d001 已证，故可在 s 生产前构造），否则链序无法前移
- 位级等价须由同指令同操作数序列保证——只删存取往返与屏障，不改任何算术形式
- 降级路径（本 run cChunkMode case12 ±inf 域）与已验证 VT 组件零改动

## 4. 泛化条件

- 策略作用域：op_class：normalization

适用：

- 存在多 pass 计算链，中间量以 UB store→reload 往返传递（本 run 模板A DX 快路径 s 链 4r4w + 2 条 RAW 屏障/行；fp32 2r2w + 1 屏障/行；模板B n1.sp3 写 s 与 n2.sp2 读 s 为纯往返 + 每 unit 4 条 LocalMemBar）
- 该往返在预算中占可观份额（本 run 模板A DX 4/14、fp32 2/10、模板B 2/11 访存份额）
- vec 管线主导（本 run aiv_vec 803.4us / aiv_mte2 403.2 / aiv_mte3 242.7 / aiv_scalar 96.2，vec 占 aiv 约 72%）
- 中间量的构造与消费均为确定性逐元素运算（Mul/Div/Cast RNE/Exp），寄存器值与落 UB 读回值位级相同

不适用：

- 对齐快路径等往返本就便宜的链不适用：本 run round_01 在对齐路径强行链式化导致 +10~42% 回退，round_02 以 scope 修复切回原链——位点条件「往返昂贵链」是该机制成立的前提
- 中间量有多个消费者、或消费者非逐元素纯函数（需要跨行/跨段可见）时不适用
- 中间量需要在屏障点对外可见（如被其它管线读取）时不适用

## 5. 实施步骤

1. softmax_vf.h: 新增链式组件 Norm1QuantPass2ChainedRowCallee/UnalignedCallee + Vf wrapper（对齐/非对齐两型，DX cast↓/cast↑ 链内寄存器完成），e→s=fl(e×rcp1)→e2=exp(s−m2) 单遍直通，s 不落 UB
2. softmax_vf.h: 新增 SoftmaxNormNoDivAligned/Unaligned 与 SoftmaxNormChain12Aligned/Unaligned（模板B：n1 子遍1+2 去子遍3 + Chain12 寄存器直通消 n2.sp2 读 s 往返，屏障 4→2/unit），wrapper ComputeNorm1QuantPass2Chained / SoftmaxNormalizeChain12Inplace
3. softmax_kernel_a.h: Compute 非对齐 else 分支切换为 ComputeNorm1QuantPass2Chained（替代 Norm1 + flat QuantRoundTrip + Pass2Identity 三段，消 4r4w→1r1w DX / 2r2w→1r1w fp32）
4. softmax_kernel_a.h（round_02 scope 修复）: 对齐快路径恢复 baseline 原链（round_01 筛选证伪链式在对齐路径回退 +10~42%）
5. softmax_kernel_b.h: Compute 第二次 SoftmaxNormalizeInplace → SoftmaxNormalizeChain12Inplace（NoDiv+Chain12）
6. cChunkMode 降级路径与已验证 VT 组件零改动

## 6. LLM 前置问题

- 目标实现是否满足：存在多 pass 计算链，中间量以 UB store→reload 往返传递（本 run 模板A DX 快路径 s 链 4r4w + 2 条 RAW 屏障/行；fp32 2r2w + 1 屏障/行；模板B n1.sp3 写 s 与 n2.sp2 读 s 为纯往返 + 每 unit 4 条 LocalMemBar）？
- 目标实现是否满足：该往返在预算中占可观份额（本 run 模板A DX 4/14、fp32 2/10、模板B 2/11 访存份额）？
- 目标实现是否满足：vec 管线主导（本 run aiv_vec 803.4us / aiv_mte2 403.2 / aiv_mte3 242.7 / aiv_scalar 96.2，vec 占 aiv 约 72%）？
- 目标实现是否满足：中间量的构造与消费均为确定性逐元素运算（Mul/Div/Cast RNE/Exp），寄存器值与落 UB 读回值位级相同？
- 是否命中排除条件：对齐快路径等往返本就便宜的链不适用：本 run round_01 在对齐路径强行链式化导致 +10~42% 回退，round_02 以 scope 修复切回原链——位点条件「往返昂贵链」是该机制成立的前提？

## 7. 验收标准

正确性：

- 精度 20/20 PASS（baseline/round_01/round_02 三份 pytest 均 20 passed，运行于真实新二进制）
- 位级等价论证完备：同指令同操作数序列，仅删存取往返与屏障；cChunkMode 降级路径与已验证 VT 组件零改动

性能：

- 形式化配对 10 对 ABBA 平衡交替（B=10 A=10，order B A A B B A A B B A A B B A A B B A A B）：27.948→26.220us，speedup 1.0659
- 逐对 1.0622~1.0709 全部 >1（median 1.0652）；169/200 case-pair 更快
- 改善集中在非对齐 Gather/Scatter 链与模板B 多遍扫位点（-7.5~-17.8%）；对齐快路径与 cChunkMode 域持平
- 两轮均真实产出 kernel 二进制（时间戳 + md5 核验，与 baseline 可区分），0 编译错误、0 编译修复；累计链路 39.766→26.220us（1.517x）

回滚信号：

- 对齐快路径等往返廉价位点出现回退（本 run round_01 已实证）
- kernel .o 体积异常膨胀或 md5 与源码不可区分（build 假阳性）
- cChunkMode / 模板B 等零改动域出现超出噪声的回退
- 精度门在真实新二进制上失败

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260909_010738-free-002（operator=softmax, status=accepted, speedup=1.0659, 27.948→26.220us, 10 对 ABBA）

## 检索卡（短卡）

动作：把中间量 s 从落 UB 再读回改为全程驻留寄存器，两遍链路合并为单遍直通，仅物化 e2
适用：多 pass 链中间量以 UB store→reload 往返传递且占预算可观份额、vec 管线主导，唯一下游消费是逐元素纯函数
限制：只删存取往返与屏障、不改算术形式；对齐快路径等往返廉价位点不可链式化（回退 +10~42%）；中间量多消费者时不适用
范围：normalization 的多 pass 计算链融合类算子
检索词：寄存器直通、LocalMemBar、RAW 屏障、cast↓/cast↑、m2≡rcp1
机会：中间量以 UB store→reload 往返传递，占模板A DX 4/14、fp32 2/10 访存份额
代价：寄存器压力上升，R 大或 liveness 长的链可能 spill，须以 kernel .o 体积确认

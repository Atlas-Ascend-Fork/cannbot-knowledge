---
type: Optimization
title: 非对齐域转对齐域：行粒度 strided 搬运 + UB 行槽 32B 自动垫整 + 行距参数化对齐前端
description: 模板A 非对齐主路径 GM↔UB 搬运改行粒度 strided DataCopyPad（UB 行槽 32B 自动垫整，模板B R8 同款契约）+ 计算链切换行距参数化对齐前端（LoadAlign/StoreAlign），消除全部 Arange/Adds/Gather/Scatter。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/mte-row-pad-strided-staging.md
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
      "UB 侧行槽必须由 MTE 自动垫整到 32B 行距（dstStride=0 + 行粒度 blockCount/blockLen），计算链行距参数化后行基恒对齐；掩码宽度保持实际 dimC，pad 道全程被掩码隔离不进任何归约/出口",
      "GM 布局不变：每行只搬 blockLen=dimC×elemBytes 实际字节，srcStride 描述 GM 行距",
      "host 侧 batchRows 预算公式须按 padded 行距重算（本 run 非对齐口径 4×AlignUp(dimC×e,32)+AlignUp(dimC×4,32)+32），对齐行保持原式零扰动",
      "尾 chunk 掩码宽度须与 dimC 一致，不可用 padded 宽度"
    ],
    "excluded_conditions": [
      "GM 行本身连续（行距 == dimC×elemBytes）时不存在非对齐问题，本机制无对象",
      "降级域（本 run cChunkMode ±inf）与已对齐域不适用：应保持原链，强行切换只是徒增代码体积",
      "若 padded 行距使 batchRows 预算塌缩到 ≤1 行，收益会被批数上升抵消——需在验收中核对 batchRows 实际值"
    ],
    "required_conditions": [
      "存在非对齐主路径（rowBaseAligned=false，dimC×elemBytes%32≠0），当前整域走 Gather/Scatter 向量前端",
      "非对齐每元素 vec 开销达对齐同 dtype 的 2~3 倍（本 run：非对齐 fp32 case8 10.6 / case15 6.8 ns·K vs 对齐 fp32 case2 3.5 / case5 1.9；非对齐 bf16 case16 5.7 vs 对齐 bf16 case3 2.8）",
      "代码库内已有同类布局契约的生产级先例可移植（本 run：模板B CopyInStrided/CopyOutStrided 的 R8 行槽自动补位，已在 case9/11/13/14/18/19/20 生产路径长跑验证）",
      "非对齐 case 数量与耗时占比可观（本 run 7/20 case 全域命中且全部 vec 主导，case17 单 case 31us 为 Top7）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 21.110,
      "before_us": 26.259,
      "operator": "softmax",
      "operator_class": "normalization",
      "pairs": 10,
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "session_ids": ["ses_f77336320ffe7GXvTNNasseED7"],
      "speedup": 1.2439,
      "status": "accepted",
      "worst_pair_ratio": 1.235
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "unaligned-gather-scatter-frontend",
      "vec-index-arithmetic-overhead",
      "unaligned-row-base"
    ],
    "pattern": "mte-row-pad-strided-staging",
    "structure": [
      "row-granular-strided-datacopypad",
      "ub-row-slot-32b-auto-padding",
      "stride-parameterized-aligned-vf",
      "unaligned-domain-conversion"
    ]
  },
  "generality": "op_class",
  "id": "SMX-MTE-ROW-PAD-STRIDED-STAGING",
  "implementation_steps": [
    "softmax_vf.h: 新增行距参数化对齐 VF 组件 Pass1FusedStrided/Norm1Pass2FusedStrided/QuantRtPass2FusedStrided/Norm2FusedStrided（LoadAlign/StoreAlign + 尾 chunk 掩码，行基步进 strideX/stride32，掩码宽度保持 dimC）及 Layer-1 wrapper",
    "softmax_kernel_a.h: Init 垫整行距/Buffer 尺寸（padMain_ 派发域）+ CopyIn/CopyOut 改行粒度 strided DataCopyPad（DataCopyExtParams{blockCount=tileRows, blockLen=dimC×e, srcStride=0, dstStride=0}，UB 行槽 32B 自动垫整，模板B R8 同款契约）+ Compute 非对齐分支切换对齐前端变体",
    "op_host/softmax_tiling.cpp: 非对齐 shape（dimC×e%32≠0）batchRows 预算公式换垫整口径（4×AlignUp(dimC×e,32)+AlignUp(dimC×4,32)+32），对齐行保持原式零扰动",
    "零改动域：cChunkMode 降级路径（case12 ±inf）、模板B、对齐域原链（case1-5）"
  ],
  "intent": "把非对齐主路径从 Gather/Scatter 向量前端转换为「行粒度 strided 搬运 + 行距参数化对齐计算链」，消除 Arange/Adds 索引构造与逐 lane 寻址，使非对齐 case 的每元素 vec 开销回落到对齐同 dtype 的水平。",
  "mechanism": "模板A rank-2 非对齐主路径（rowBaseAligned=false，dimC×elemBytes%32≠0）把 GM↔UB 搬运改为行粒度 strided DataCopyPad（blockCount=tileRows、blockLen=dimC×e、srcStride/dstStride=0——UB 侧行槽由 MTE 自动补位到 32B 对齐行距，即模板B CopyInStrided/CopyOutStrided 已在生产路径验证的 R8 布局契约），使 UB 内 x/y 行基恒 32B 对齐；计算链切换为行距参数化的对齐 VF 变体（LoadAlign/StoreAlign + 尾 chunk 掩码，行距由 dimC 换为 padded stride），消除全部 Arange/Adds/Gather/Scatter。数值位级等价：逐行同指令同操作数（mask 限宽 dimC，pad 道被掩码隔离不进任何归约/出口）；GM 布局不变（每行只搬 blockLen=dimC×e 实际字节）。",
  "name": "非对齐域转对齐域：行粒度 strided 搬运 + UB 行槽 32B 自动垫整 + 行距参数化对齐前端",
  "operator_class": "normalization",
  "operator_scope": "双路径（对齐/非对齐）布局的融合类算子，非对齐域当前以 Arange+Adds+Gather+Scatter 向量前端实现、每元素 vec 开销达对齐同 dtype 的 2~3 倍，且代码库内已有 UB 行槽自动补位的生产级布局契约可移植",
  "principle": "非对齐域走 Gather/Scatter 的根因是 UB 内行基不能对齐 32B；但只要 GM 侧能用行粒度 strided 描述符搬运、且 UB 侧行槽能被 MTE 自动补位到 32B 行距，UB 内的行基就恒对齐，计算链即可整体切换到对齐前端。pad 道由掩码隔离不影响数值，GM 布局不变，故是位级等价的结构转换而非近似。该转换把「逐 lane 索引算术」换成「描述符参数化」，收益来源是消除索引构造与逐 lane 寻址，代价是 host 预算公式需按 padded 行距收紧。",
  "related_anti_patterns": [],
  "risks": [
    "padded 行距使 UB 预算收紧，极端紧 case 的 batchRows 可能塌到 ≤1 行，批数上升抵消部分收益——须在验收中核对 batchRows 实际值",
    "行距参数化改动面较大（VF 组件 + kernel_a Init/CopyIn/CopyOut + host tiling 三处），任一处漏改会表现为数值或越界问题",
    "pad 道若未被掩码完整隔离，会污染归约（Max/Add）或出口写出——位级等价论证依赖掩码宽度等于 dimC"
  ],
  "slug": "mte-row-pad-strided-staging",
  "summary": "模板A 非对齐主路径 GM↔UB 搬运改行粒度 strided DataCopyPad（UB 行槽 32B 自动垫整，模板B R8 同款契约）+ 计算链切换行距参数化对齐前端（LoadAlign/StoreAlign），消除全部 Arange/Adds/Gather/Scatter。formal 26.259→21.110us（1.2439x，10 对 ABBA 全部 speedup>1，min 1.2350，candidate faster 148/200 case-pairs）；设计位点非对齐 7 case（6/7/8/10/15/16/17）case 级 -36~-57%，非目标域 ±2.3% 噪声带内；精度 20/20。",
  "verification": {
    "correctness": [
      "精度 20/20 PASS（test_softmax.py，candidate_accuracy_r0.log，真实新二进制上运行）",
      "位级等价论证：逐行同指令同操作数、pad 道全程掩码隔离、GM 每行仅搬实际字节；±inf（case12）走未触碰的 cChunkMode 降级路径",
      "1 实现轮即编译通过（0 error），kernel .o 33976/34536/34536B 三 tiling-key md5 与 baseline 全部可区分——无编译假阳性"
    ],
    "performance": [
      "筛选 -19.6%（geomean 26.209→21.076）；formal（B = 冻结基线构建二进制 md5 钉死）26.259→21.110us（1.2439x）",
      "10 对 ABBA 全部 speedup>1（min 1.2350），candidate faster 148/200 case-pairs",
      "设计位点非对齐 7 case（6/7/8/10/15/16/17）case 级 -36~-57%；非目标域 ±2.3% 噪声带内"
    ],
    "rollback_signals": [
      "pad 道未被掩码隔离导致归约/出口被污染（精度门回退）",
      "host batchRows 预算公式漏改导致 UB 越界或批数异常",
      "对齐域（case1-5）/ 模板B / cChunkMode 出现超出噪声的回退",
      "kernel .o md5 与 baseline 不可区分（build 假阳性）"
    ]
  }
}
-->

# 性能优化策略：非对齐域转对齐域：行粒度 strided 搬运 + UB 行槽 32B 自动垫整 + 行距参数化对齐前端

模板A 非对齐主路径 GM↔UB 搬运改行粒度 strided DataCopyPad（UB 行槽 32B 自动垫整，模板B R8 同款契约）+ 计算链切换行距参数化对齐前端（LoadAlign/StoreAlign），消除全部 Arange/Adds/Gather/Scatter。formal 26.259→21.110us（1.2439x，10 对 ABBA 全部 speedup>1，min 1.2350，candidate faster 148/200 case-pairs）；设计位点非对齐 7 case（6/7/8/10/15/16/17）case 级 -36~-57%，非目标域 ±2.3% 噪声带内；精度 20/20。

## 1. 原理

非对齐域走 Gather/Scatter 的根因是 UB 内行基不能对齐 32B；但只要 GM 侧能用行粒度 strided 描述符搬运、且 UB 侧行槽能被 MTE 自动补位到 32B 行距，UB 内的行基就恒对齐，计算链即可整体切换到对齐前端。pad 道由掩码隔离不影响数值，GM 布局不变，故是位级等价的结构转换而非近似。该转换把「逐 lane 索引算术」换成「描述符参数化」，收益来源是消除索引构造与逐 lane 寻址，代价是 host 预算公式需按 padded 行距收紧。

实现机制：模板A rank-2 非对齐主路径（rowBaseAligned=false，dimC×elemBytes%32≠0）把 GM↔UB 搬运改为行粒度 strided DataCopyPad（blockCount=tileRows、blockLen=dimC×e、srcStride/dstStride=0——UB 侧行槽由 MTE 自动补位到 32B 对齐行距，即模板B CopyInStrided/CopyOutStrided 已在生产路径验证的 R8 布局契约），使 UB 内 x/y 行基恒 32B 对齐；计算链切换为行距参数化的对齐 VF 变体（LoadAlign/StoreAlign + 尾 chunk 掩码，行距由 dimC 换为 padded stride），消除全部 Arange/Adds/Gather/Scatter。数值位级等价：逐行同指令同操作数（mask 限宽 dimC，pad 道被掩码隔离不进任何归约/出口）；GM 布局不变（每行只搬 blockLen=dimC×e 实际字节）。

## 2. 性能问题模式

- 优化目标：把非对齐主路径从 Gather/Scatter 向量前端转换为「行粒度 strided 搬运 + 行距参数化对齐计算链」，消除 Arange/Adds 索引构造与逐 lane 寻址，使非对齐 case 的每元素 vec 开销回落到对齐同 dtype 的水平
- 适用数据流：双路径（对齐/非对齐）布局的融合类算子，非对齐域当前以 Arange+Adds+Gather+Scatter 向量前端实现、每元素 vec 开销达对齐同 dtype 的 2~3 倍，且代码库内已有 UB 行槽自动补位的生产级布局契约可移植
- Feature signature：`{"bottleneck": ["unaligned-gather-scatter-frontend", "vec-index-arithmetic-overhead", "unaligned-row-base"], "pattern": "mte-row-pad-strided-staging", "structure": ["row-granular-strided-datacopypad", "ub-row-slot-32b-auto-padding", "stride-parameterized-aligned-vf", "unaligned-domain-conversion"]}`

## 3. 正确性红线

- padded 行距使 UB 预算收紧，极端紧 case 的 batchRows 可能塌到 ≤1 行，批数上升抵消部分收益——须在验收中核对 batchRows 实际值
- 行距参数化改动面较大（VF 组件 + kernel_a Init/CopyIn/CopyOut + host tiling 三处），任一处漏改会表现为数值或越界问题
- pad 道若未被掩码完整隔离，会污染归约（Max/Add）或出口写出——位级等价论证依赖掩码宽度等于 dimC

资源与硬件约束：

- UB 侧行槽必须由 MTE 自动垫整到 32B 行距（dstStride=0 + 行粒度 blockCount/blockLen），计算链行距参数化后行基恒对齐；掩码宽度保持实际 dimC，pad 道全程被掩码隔离不进任何归约/出口
- GM 布局不变：每行只搬 blockLen=dimC×elemBytes 实际字节，srcStride 描述 GM 行距
- host 侧 batchRows 预算公式须按 padded 行距重算（本 run 非对齐口径 4×AlignUp(dimC×e,32)+AlignUp(dimC×4,32)+32），对齐行保持原式零扰动
- 尾 chunk 掩码宽度须与 dimC 一致，不可用 padded 宽度

## 4. 泛化条件

- 策略作用域：op_class：normalization

适用：

- 存在非对齐主路径（rowBaseAligned=false，dimC×elemBytes%32≠0），当前整域走 Gather/Scatter 向量前端
- 非对齐每元素 vec 开销达对齐同 dtype 的 2~3 倍（本 run：非对齐 fp32 case8 10.6 / case15 6.8 ns·K vs 对齐 fp32 case2 3.5 / case5 1.9；非对齐 bf16 case16 5.7 vs 对齐 bf16 case3 2.8）
- 代码库内已有同类布局契约的生产级先例可移植（本 run：模板B CopyInStrided/CopyOutStrided 的 R8 行槽自动补位，已在 case9/11/13/14/18/19/20 生产路径长跑验证）
- 非对齐 case 数量与耗时占比可观（本 run 7/20 case 全域命中且全部 vec 主导，case17 单 case 31us 为 Top7）

不适用：

- GM 行本身连续（行距 == dimC×elemBytes）时不存在非对齐问题，本机制无对象
- 降级域（本 run cChunkMode ±inf）与已对齐域不适用：应保持原链，强行切换只是徒增代码体积
- 若 padded 行距使 batchRows 预算塌缩到 ≤1 行，收益会被批数上升抵消——需在验收中核对 batchRows 实际值

## 5. 实施步骤

1. softmax_vf.h: 新增行距参数化对齐 VF 组件 Pass1FusedStrided/Norm1Pass2FusedStrided/QuantRtPass2FusedStrided/Norm2FusedStrided（LoadAlign/StoreAlign + 尾 chunk 掩码，行基步进 strideX/stride32，掩码宽度保持 dimC）及 Layer-1 wrapper
2. softmax_kernel_a.h: Init 垫整行距/Buffer 尺寸（padMain_ 派发域）+ CopyIn/CopyOut 改行粒度 strided DataCopyPad（DataCopyExtParams{blockCount=tileRows, blockLen=dimC×e, srcStride=0, dstStride=0}，UB 行槽 32B 自动垫整，模板B R8 同款契约）+ Compute 非对齐分支切换对齐前端变体
3. op_host/softmax_tiling.cpp: 非对齐 shape（dimC×e%32≠0）batchRows 预算公式换垫整口径（4×AlignUp(dimC×e,32)+AlignUp(dimC×4,32)+32），对齐行保持原式零扰动
4. 零改动域：cChunkMode 降级路径（case12 ±inf）、模板B、对齐域原链（case1-5）

## 6. LLM 前置问题

- 目标实现是否满足：存在非对齐主路径（rowBaseAligned=false，dimC×elemBytes%32≠0），当前整域走 Gather/Scatter 向量前端？
- 目标实现是否满足：非对齐每元素 vec 开销达对齐同 dtype 的 2~3 倍（本 run：非对齐 fp32 case8 10.6 / case15 6.8 ns·K vs 对齐 fp32 case2 3.5 / case5 1.9；非对齐 bf16 case16 5.7 vs 对齐 bf16 case3 2.8）？
- 目标实现是否满足：代码库内已有同类布局契约的生产级先例可移植（本 run：模板B CopyInStrided/CopyOutStrided 的 R8 行槽自动补位，已在 case9/11/13/14/18/19/20 生产路径长跑验证）？
- 目标实现是否满足：非对齐 case 数量与耗时占比可观（本 run 7/20 case 全域命中且全部 vec 主导，case17 单 case 31us 为 Top7）？
- 是否命中排除条件：GM 行本身连续（行距 == dimC×elemBytes）时不存在非对齐问题，本机制无对象？

## 7. 验收标准

正确性：

- 精度 20/20 PASS（test_softmax.py，candidate_accuracy_r0.log，真实新二进制上运行）
- 位级等价论证：逐行同指令同操作数、pad 道全程掩码隔离、GM 每行仅搬实际字节；±inf（case12）走未触碰的 cChunkMode 降级路径
- 1 实现轮即编译通过（0 error），kernel .o 33976/34536/34536B 三 tiling-key md5 与 baseline 全部可区分——无编译假阳性

性能：

- 筛选 -19.6%（geomean 26.209→21.076）；formal（B = 冻结基线构建二进制 md5 钉死）26.259→21.110us（1.2439x）
- 10 对 ABBA 全部 speedup>1（min 1.2350），candidate faster 148/200 case-pairs
- 设计位点非对齐 7 case（6/7/8/10/15/16/17）case 级 -36~-57%；非目标域 ±2.3% 噪声带内

回滚信号：

- pad 道未被掩码隔离导致归约/出口被污染（精度门回退）
- host batchRows 预算公式漏改导致 UB 越界或批数异常
- 对齐域（case1-5）/ 模板B / cChunkMode 出现超出噪声的回退
- kernel .o md5 与 baseline 不可区分（build 假阳性）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260909_010738-free-003（operator=softmax, status=accepted, speedup=1.2439, 26.259→21.110us, 10 对 ABBA）

## 检索卡（短卡）

动作：把非对齐主路径从 Gather/Scatter 前端改为行粒度 strided DataCopyPad（UB 行槽 32B 自动垫整）+ 行距参数化对齐前端。
适用：rowBaseAligned=false（dimC×elemBytes%32≠0）、非对齐每元素 vec 开销达对齐 2~3 倍。
限制：掩码宽度须保持 dimC、pad 道全程被掩码隔离；host batchRows 预算须按 padded 行距重算。
范围：normalization 双路径融合算子的非对齐主路径搬运与计算链。
检索词：DataCopyPad、DataCopyExtParams、dstStride、LoadAlign、StoreAlign
机会：非对齐域整域走 Arange+Adds+Gather/Scatter，逐 lane 索引算术主导 vec。
代价：padded 行距收紧 UB 预算，batchRows 塌到 ≤1 行会抵消收益。

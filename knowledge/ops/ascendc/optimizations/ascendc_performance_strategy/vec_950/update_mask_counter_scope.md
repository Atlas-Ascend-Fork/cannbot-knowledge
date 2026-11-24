---
type: Optimization
title: UpdateMask 计数器作用域与 POST_DECREMENT 跨块语义
description: UpdateMask<T>(sreg) 为 POST_DECREMENT 语义：返回 min(sreg, VL) 的逐块有效 lane 掩码后原地递减。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.precision
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/update-mask-counter-scope.md
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
      "修复只改掩码簿记（标量语句/声明位置），不得改变循环结构与向量指令数",
      "b64（BLK=32）与 fp16/bf16/fp32 三条 dtype 路径须同时检查同一缺陷"
    ],
    "excluded_conditions": [
      "全部 innerChunk 均为 BLK 整数倍（末块恒为全 lane 掩码），计数器作用域错误不触发",
      "掩码通过显式 min(innerChunk-off, BLK) 每块计算，不依赖计数器跨块递减状态"
    ],
    "required_conditions": [
      "向量归约路径用 UpdateMask<T>(sreg) 或等价 POST_DECREMENT 语义的掩码计数器逐块递减",
      "归约轴长度 innerChunk 可能不是 BLK(64/32) 整数倍（存在非对齐尾块）",
      "输出索引/值经 StoreAlign 等全宽向量写回 UB，掩码错误会同时造成越界写与尾 lane 未写"
    ]
  },
  "classification": "negative_boundary",
  "evidence": [
    {
      "comparison_sha256": "280b5b0d9598604eda508b12723ceb7018353bdfd1d74db4187a7c33553b6bf6",
      "decision_sha256": "973c6d8c076844cb0b6b2ec3e53ea18222625d5bfa9bba120a6cbb81d63ec3be",
      "operator_class": "sort-select",
      "performance_sha256": "cbe966b4dd1315076246c7f6084935fdbba7861ed50c3fe1ed62bf517b39faa9",
      "round": 2,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "ba75f34965b98edcbb536e189172e24b55bd491ad9e9caa370cac3299a6c268f",
      "verify_sha256": "35164bfd7f58667499b80e764ced5dbf69ae4b06cbfedee62efb737e21cb6fc2"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "tail-block-oob",
      "precision-mismatch",
      "mask-counter-scope"
    ],
    "pattern": "update-mask-counter-scope",
    "reduce_mode": "argmax-argmin",
    "structure": [
      "vector-reduce",
      "mask-counter",
      "tail-mask"
    ]
  },
  "generality": "op_class",
  "id": "NEG-UPDATEMASK-COUNTER-SCOPE",
  "implementation_steps": [
    "定位逐块掩码计数器声明/初始化位置，确认是否为块内循环重置",
    "若依赖跨块递减：把计数器初始化移回块外循环（保持跨块 POST_DECREMENT 语义）",
    "或在块首显式计算 blockCount=min(innerChunk-off, BLK) 逐块部分掩码，不依赖计数器状态",
    "对非 BLK 整数倍的 innerChunk 构造尾块 case（如 1016、368）做精度验证，检查输出首列与尾列",
    "全 dtype（含 b64）路径源码级复核同一缺陷是否一并修复"
  ],
  "intent": "避免把逐块掩码计数器错误初始化在块内循环导致非对齐尾块越界读写 UB 的确定性正确性 bug（性能收益无法掩盖）。",
  "mechanism": "round 2 把 uint32_t sreg{innerChunk} 从原验证版 VF 的循环外（rr 循环内、b 循环外）错误移入逐块 b 循环（arg_max_impl.h:132/182/224）。每块 sreg=innerChunk>=64 时 UpdateMask 恒返回 64 lane 全掩码；末块（case8 innerChunk=1016 末块 56 lane、case10 innerChunk=368 末块 48 lane）越过尾界：StoreAlign(maxValUb+off) 越界写 32-64B 覆写相邻 UB 缓冲，StoreAlign(maxIdxUb+off) 使 maxIdxBuf_ 尾部 lane 从未写入残留垃圾，且 maxValBuf_ 越界数据（UB 分配顺序紧邻 maxIdxBuf_ 之前）覆写 maxIdxBuf_[0..3]/[0..7] 导致输出前几列错误。修复：sreg 声明移回循环外（恢复跨块 POST_DECREMENT），或在块首显式 UpdateMask<DX>(min(innerChunk-off, BLK)) 计算逐块部分掩码；b64（BLK=32）路径须一并修复。",
  "name": "UpdateMask 计数器作用域与 POST_DECREMENT 跨块语义",
  "operator_class": "sort-select",
  "operator_scope": "使用 UpdateMask<T>(sreg) 或等价 POST_DECREMENT 掩码计数器的 strided argmax/argmin 向量归约（dimIsLast=0、stridedMode=1 的 T2 路径）",
  "principle": "掩码计数器若设计为跨块递减（POST_DECREMENT），其状态必须跨块保留：计数器初始化为块总长度，逐块递减，末块自动得到部分尾掩码。若在每块入口重新初始化为完整 innerChunk，末块不再有部分尾掩码，任何 innerChunk%BLK!=0 的长度都必然越界。",
  "related_anti_patterns": [],
  "risks": [
    "掩码错误是确定性正确性 bug 而非随机噪声：重采/重复测量不能修复，必须源码修复",
    "越界写覆写相邻 UB 缓冲（maxValBuf_ 覆写 maxIdxBuf_ 头部），输出前几列与尾列同时出错；部分输入可能因邻接内存可读而偶发通过"
  ],
  "slug": "update-mask-counter-scope",
  "summary": "UpdateMask<T>(sreg) 为 POST_DECREMENT 语义：返回 min(sreg, VL) 的逐块有效 lane 掩码后原地递减。掩码计数器 sreg 的声明/初始化位置决定跨块行为——若被移入逐块循环，非 BLK 整数倍的末块会得到全 lane 掩码，StoreAlign 越界写 UB 且尾 lane 残留垃圾，输出首尾列同时出错。",
  "verification": {
    "correctness": [
      "非对齐尾块 case（innerChunk%BLK!=0）输出 flat 索引与 golden 完全一致，无垃圾前缀/越界残留"
    ],
    "performance": [
      "修复前 target 6/6 对齐 case 精度正确且 3.77x-8.05x 加速、aiv_vec_time 崩塌（性能机制本身有效），修复仅改掩码簿记可复用 stable 证据，建议重采确认无 perf 偏移"
    ],
    "rollback_signals": [
      "任一非对齐 case 输出首列/尾列与 golden 不一致",
      "StoreAlign 越界写或 maxIdxBuf_ 尾 lane 残留垃圾复现"
    ]
  }
}
-->

# 性能优化策略：UpdateMask 计数器作用域与 POST_DECREMENT 跨块语义

单一优化点：UpdateMask<T>(sreg) 为 POST_DECREMENT 语义：返回 min(sreg, VL) 的逐块有效 lane 掩码后原地递减。掩码计数器 sreg 的声明/初始化位置决定跨块行为——若被移入逐块循环，非 BLK 整数倍的末块会得到全 lane 掩码，StoreAlign 越界写 UB 且尾 lane 残留垃圾，输出首尾列同时出错。

## 1. 原理

掩码计数器若设计为跨块递减（POST_DECREMENT），其状态必须跨块保留：计数器初始化为块总长度，逐块递减，末块自动得到部分尾掩码。若在每块入口重新初始化为完整 innerChunk，末块不再有部分尾掩码，任何 innerChunk%BLK!=0 的长度都必然越界。

实现机制：round 2 把 uint32_t sreg{innerChunk} 从原验证版 VF 的循环外（rr 循环内、b 循环外）错误移入逐块 b 循环（arg_max_impl.h:132/182/224）。每块 sreg=innerChunk>=64 时 UpdateMask 恒返回 64 lane 全掩码；末块（case8 innerChunk=1016 末块 56 lane、case10 innerChunk=368 末块 48 lane）越过尾界：StoreAlign(maxValUb+off) 越界写 32-64B 覆写相邻 UB 缓冲，StoreAlign(maxIdxUb+off) 使 maxIdxBuf_ 尾部 lane 从未写入残留垃圾，且 maxValBuf_ 越界数据（UB 分配顺序紧邻 maxIdxBuf_ 之前）覆写 maxIdxBuf_[0..3]/[0..7] 导致输出前几列错误。修复：sreg 声明移回循环外（恢复跨块 POST_DECREMENT），或在块首显式 UpdateMask<DX>(min(innerChunk-off, BLK)) 计算逐块部分掩码；b64（BLK=32）路径须一并修复。

## 2. 性能问题模式

- 优化目标：避免把逐块掩码计数器错误初始化在块内循环导致非对齐尾块越界读写 UB 的确定性正确性 bug（性能收益无法掩盖）。
- 适用数据流：使用 UpdateMask<T>(sreg) 或等价 POST_DECREMENT 掩码计数器的 strided argmax/argmin 向量归约（dimIsLast=0、stridedMode=1 的 T2 路径）
- Feature signature：`{"bottleneck": ["tail-block-oob", "precision-mismatch", "mask-counter-scope"], "pattern": "update-mask-counter-scope", "reduce_mode": "argmax-argmin", "structure": ["vector-reduce", "mask-counter", "tail-mask"]}`

## 3. 正确性红线

- 掩码错误是确定性正确性 bug 而非随机噪声：重采/重复测量不能修复，必须源码修复
- 越界写覆写相邻 UB 缓冲（maxValBuf_ 覆写 maxIdxBuf_ 头部），输出前几列与尾列同时出错；部分输入可能因邻接内存可读而偶发通过

资源与硬件约束：

- 修复只改掩码簿记（标量语句/声明位置），不得改变循环结构与向量指令数
- b64（BLK=32）与 fp16/bf16/fp32 三条 dtype 路径须同时检查同一缺陷

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- 向量归约路径用 UpdateMask<T>(sreg) 或等价 POST_DECREMENT 语义的掩码计数器逐块递减
- 归约轴长度 innerChunk 可能不是 BLK(64/32) 整数倍（存在非对齐尾块）
- 输出索引/值经 StoreAlign 等全宽向量写回 UB，掩码错误会同时造成越界写与尾 lane 未写

不适用：

- 全部 innerChunk 均为 BLK 整数倍（末块恒为全 lane 掩码），计数器作用域错误不触发
- 掩码通过显式 min(innerChunk-off, BLK) 每块计算，不依赖计数器跨块递减状态

## 5. 实施步骤

1. 定位逐块掩码计数器声明/初始化位置，确认是否为块内循环重置
2. 若依赖跨块递减：把计数器初始化移回块外循环（保持跨块 POST_DECREMENT 语义）
3. 或在块首显式计算 blockCount=min(innerChunk-off, BLK) 逐块部分掩码，不依赖计数器状态
4. 对非 BLK 整数倍的 innerChunk 构造尾块 case（如 1016、368）做精度验证，检查输出首列与尾列
5. 全 dtype（含 b64）路径源码级复核同一缺陷是否一并修复

## 6. LLM 前置问题

- 目标实现是否满足：向量归约路径用 UpdateMask<T>(sreg) 或等价 POST_DECREMENT 语义的掩码计数器逐块递减？
- 目标实现是否满足：归约轴长度 innerChunk 可能不是 BLK(64/32) 整数倍（存在非对齐尾块）？
- 目标实现是否满足：输出索引/值经 StoreAlign 等全宽向量写回 UB，掩码错误会同时造成越界写与尾 lane 未写？
- 是否命中排除条件：全部 innerChunk 均为 BLK 整数倍（末块恒为全 lane 掩码），计数器作用域错误不触发？

## 7. 验收标准

正确性：

- 非对齐尾块 case（innerChunk%BLK!=0）输出 flat 索引与 golden 完全一致，无垃圾前缀/越界残留

性能：

- 修复前 target 6/6 对齐 case 精度正确且 3.77x-8.05x 加速、aiv_vec_time 崩塌（性能机制本身有效），修复仅改掩码簿记可复用 stable 证据，建议重采确认无 perf 偏移

回滚信号：

- 任一非对齐 case 输出首列/尾列与 golden 不一致
- StoreAlign 越界写或 maxIdxBuf_ 尾 lane 残留垃圾复现

## 8. 分类与证据

- Classification：`negative_boundary`
- Generality：`op_class`
- Related anti-patterns：无

- arg_max-20260824_083424-ff0f95（round=2, status=rejected）

## 检索卡（短卡）

动作：将逐块重置的掩码计数器初始化移到块外，恢复跨块 POST_DECREMENT 状态
适用：掩码计数器采用跨块递减的 POST_DECREMENT 语义
限制：仅改掩码簿记及声明位置，不得改变循环结构与向量指令数
范围：selection-reduce 的向量归约逐块掩码路径
检索词：UpdateMask、sreg、POST_DECREMENT、innerChunk、尾掩码
机会：计数器在块内重置，非对齐尾块失去部分尾掩码

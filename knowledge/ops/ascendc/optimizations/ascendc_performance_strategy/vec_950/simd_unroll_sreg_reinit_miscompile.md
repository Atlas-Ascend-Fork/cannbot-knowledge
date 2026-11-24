---
type: Optimization
title: 手工展开循环后重置 auto-decrement sreg 的尾段会静默清空掩码
description: 在每块起点显式重建尾段掩码，弃用展开循环遗留的auto-decrement或POST_UPDATE递减值。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/simd-unroll-sreg-reinit-miscompile.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "applicability": {
    "constraints": [
      "此类变体的验收必须做 A/B 逐位差分（覆盖 0/±0/±inf/nan/subnormal/±极大值与 epsilon 边界）并包含余数行形态，源码级等价论证不充分",
      "证据平台为 ascend950 / dav_m510 工具链；其它后端未测，不得假设同类行为，也不得假设已修复"
    ],
    "excluded_conditions": [
      "无手工展开的常规掩码循环，以及尾段掩码显式按块起点重建的路径（实测数值干净）",
      "本教训不否定掩码/循环不变量外提本身——不依赖展开后 sreg 重置的外提与循环互换路径数值干净"
    ],
    "required_conditions": [
      "向量函数内存在手工展开的块/行循环，且尾段复用同一掩码寄存器并重新初始化 auto-decrement sreg",
      "验证集必须包含会产生余数行的形状（批行数不能整除每核行数），否则结构性通过（批行数整除、全零输入、全 run 仅单个余数行）会掩盖损坏"
    ]
  },
  "classification": "lesson",
  "evidence": [
    {
      "comparison_sha256": "4dc876649e72820031349f41c6ae3618c8dc0b0e334743bac2a1a1fead5c0641",
      "decision_sha256": "73aeb0ac11d3917e941919c334a1fa3c4e39c1bbd741b6784b683ba25236f69f",
      "operator_class": "normalization",
      "performance_sha256": "df45564ca9b64b47a7b89b0fed0efc877ad83b3d097f20c1b3f530817de00acc",
      "round": 2,
      "run_id": "<run-id>",
      "status": "rejected",
      "strategy_sha256": "009722b5e4c2d47a18af4975198630b8f8d630629e8fe72ee4b8ffaea47652ee",
      "verify_sha256": "394a676c049220ab52b8f5a0451ce778b55876a86b5552f8df10a1a0328ed1ba"
    }
  ],
  "feature_signature": {
    "domain": "vector-function-microapi",
    "failure_mode": "codegen-mask-empty-silent-corruption",
    "pattern": "simd-unroll-sreg-reinit",
    "signature": "row-factor ~ sqrt(blockCount) on odd-remainder tail rows",
    "structure": [
      "manual-unroll",
      "auto-decrement-sreg",
      "tail-remainder-segment"
    ]
  },
  "generality": "common",
  "id": "L-SIMD-UNROLL-SREG-REINIT",
  "implementation_steps": [
    "尾段掩码显式重建：每块起点重算掩码宽度（如 sregBlk = dDim - 64*blk），弃用展开循环遗留的 auto-decrement/POST_UPDATE 递减值",
    "或把余数尾段隔离为独立 __simd_callee__ 函数，切断与展开主体的寄存器别名",
    "任何此类重构后先在含余数行的形状上做 A/B 逐位差分定位损坏行集合，再做全量精度验证"
  ],
  "intent": "防止向量函数循环重构（手工展开、不变量外提、快路径拆分）引入静默数值损坏——源码级掩码宽度等价论证不等于编译产物行为，该等价性在本平台被证伪。",
  "mechanism": "缺陷形态：向量函数内 blockCount>=2 的线性 fold 手工双链展开 + 其后奇余数行单链尾段重新初始化 auto-decrement sreg。识别签名：逐行最小二乘行因子差分（f=<y,g>/<g,g>）显示损坏行恰为奇 rowCnt 批的最后一行，f 样本 ≈ sqrt(blockCount)；同文件中不依赖『展开后重置 sreg』的新路径（blockCount==1 快路径的余数行、blk 外层显式按块起点重建掩码宽度、外提）数值全部干净——即缺陷绑定『展开循环后 sreg 生命周期』这一具体形态，不是掩码外提或循环互换本身。规避：尾段掩码显式按块起点重建（弃用展开循环遗留的 auto-decrement/POST_UPDATE 递减值），或把尾段隔离为独立 __simd_callee__ 函数切断寄存器别名。",
  "name": "手工展开循环后重置 auto-decrement sreg 的尾段会静默清空掩码",
  "operator_scope": "所有在 __simd_vf__ 向量函数中手工展开块循环并在尾段复用掩码寄存器的算子（末轴规约、逐元素、行批数据流均适用，跨 operator class）",
  "principle": "MicroAPI 掩码语义由 sreg 寄存器状态与 UpdateMask 更新模式共同决定；手工展开循环中建立的 auto-decrement sreg 生命周期在尾段被重新初始化后，编译器对后续掩码的生成与源码语义偏离（掩码为空等效 ZEROING），损坏确定可复现且随块数放大。",
  "related_anti_patterns": [],
  "risks": [
    "损坏无编译期警告、无设备错误码，只能靠差分定位；结构性通过的用例（批行数整除、全零输入、仅单个余数行）会被误判为数值安全",
    "同一机制中『双链展开独立寄存器链 + 不变量外提提升 vector 发射率』的性能假设已被同步证伪（干净路径上指令条数减少反而更慢，有效发射率约减半），不得以性能动机重试同一代码形态"
  ],
  "slug": "simd-unroll-sreg-reinit-miscompile",
  "summary": "手工展开的块循环之后，紧接着重新初始化 auto-decrement sreg（如 sreg = dDim 再 UpdateMask POST_UPDATE）的尾段会在 ascend950 编译产物中把后续块掩码编译为空：余数行只累加约第 0 块，统计量被低估 blockCount 倍、缩放因子放大 sqrt(blockCount) 倍，且无编译期诊断。规避方式是尾段掩码显式重建或把尾段隔离为独立向量函数。",
  "verification": {
    "correctness": [
      "全量 case 精度验证，必须覆盖奇余数行形态（批行数不整除每核行数）与 inf/nan/全零/极小 epsilon",
      "A/B 逐位差分（改前 vs 改后）确认无非余数行偏差、无行级缩放因子（f≈sqrt(blockCount) 即为损坏签名）"
    ],
    "performance": [
      "本条目为正确性教训，性能不作为验收维度；在损坏内核上采集的性能数据只能作机制证伪证据，不得作任何加速声明"
    ],
    "rollback_signals": [
      "任一 precision_mismatch 立即回退到上一个 accepted kernel，并按逐行行因子差分定位损坏行集合，区分实现 bug 与机制性损坏后再决定修复或放弃"
    ]
  }
}
-->

# 性能优化策略：手工展开循环后重置 auto-decrement sreg 的尾段会静默清空掩码

单一优化点：手工展开的块循环之后，紧接着重新初始化 auto-decrement sreg（如 sreg = dDim 再 UpdateMask POST_UPDATE）的尾段会在 ascend950 编译产物中把后续块掩码编译为空：余数行只累加约第 0 块，统计量被低估 blockCount 倍、缩放因子放大 sqrt(blockCount) 倍，且无编译期诊断。规避方式是尾段掩码显式重建或把尾段隔离为独立向量函数。

## 1. 原理

MicroAPI 掩码语义由 sreg 寄存器状态与 UpdateMask 更新模式共同决定；手工展开循环中建立的 auto-decrement sreg 生命周期在尾段被重新初始化后，编译器对后续掩码的生成与源码语义偏离（掩码为空等效 ZEROING），损坏确定可复现且随块数放大。

实现机制：缺陷形态：向量函数内 blockCount>=2 的线性 fold 手工双链展开 + 其后奇余数行单链尾段重新初始化 auto-decrement sreg。识别签名：逐行最小二乘行因子差分（f=<y,g>/<g,g>）显示损坏行恰为奇 rowCnt 批的最后一行，f 样本 ≈ sqrt(blockCount)；同文件中不依赖『展开后重置 sreg』的新路径（blockCount==1 快路径的余数行、blk 外层显式按块起点重建掩码宽度、外提）数值全部干净——即缺陷绑定『展开循环后 sreg 生命周期』这一具体形态，不是掩码外提或循环互换本身。规避：尾段掩码显式按块起点重建（弃用展开循环遗留的 auto-decrement/POST_UPDATE 递减值），或把尾段隔离为独立 __simd_callee__ 函数切断寄存器别名。

## 2. 性能问题模式

- 优化目标：防止向量函数循环重构（手工展开、不变量外提、快路径拆分）引入静默数值损坏——源码级掩码宽度等价论证不等于编译产物行为，该等价性在本平台被证伪。
- 适用数据流：所有在 __simd_vf__ 向量函数中手工展开块循环并在尾段复用掩码寄存器的算子（末轴规约、逐元素、行批数据流均适用，跨 operator class）
- Feature signature：`{"domain": "vector-function-microapi", "failure_mode": "codegen-mask-empty-silent-corruption", "pattern": "simd-unroll-sreg-reinit", "signature": "row-factor ~ sqrt(blockCount) on odd-remainder tail rows", "structure": ["manual-unroll", "auto-decrement-sreg", "tail-remainder-segment"]}`

## 3. 正确性红线

- 损坏无编译期警告、无设备错误码，只能靠差分定位；结构性通过的用例（批行数整除、全零输入、仅单个余数行）会被误判为数值安全
- 同一机制中『双链展开独立寄存器链 + 不变量外提提升 vector 发射率』的性能假设已被同步证伪（干净路径上指令条数减少反而更慢，有效发射率约减半），不得以性能动机重试同一代码形态

资源与硬件约束：

- 此类变体的验收必须做 A/B 逐位差分（覆盖 0/±0/±inf/nan/subnormal/±极大值与 epsilon 边界）并包含余数行形态，源码级等价论证不充分
- 证据平台为 ascend950 / dav_m510 工具链；其它后端未测，不得假设同类行为，也不得假设已修复

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 向量函数内存在手工展开的块/行循环，且尾段复用同一掩码寄存器并重新初始化 auto-decrement sreg
- 验证集必须包含会产生余数行的形状（批行数不能整除每核行数），否则结构性通过（批行数整除、全零输入、全 run 仅单个余数行）会掩盖损坏

不适用：

- 无手工展开的常规掩码循环，以及尾段掩码显式按块起点重建的路径（实测数值干净）
- 本教训不否定掩码/循环不变量外提本身——不依赖展开后 sreg 重置的外提与循环互换路径数值干净

## 5. 实施步骤

1. 尾段掩码显式重建：每块起点重算掩码宽度（如 sregBlk = dDim - 64*blk），弃用展开循环遗留的 auto-decrement/POST_UPDATE 递减值
2. 或把余数尾段隔离为独立 __simd_callee__ 函数，切断与展开主体的寄存器别名
3. 任何此类重构后先在含余数行的形状上做 A/B 逐位差分定位损坏行集合，再做全量精度验证

## 6. LLM 前置问题

- 目标实现是否满足：向量函数内存在手工展开的块/行循环，且尾段复用同一掩码寄存器并重新初始化 auto-decrement sreg？
- 目标实现是否满足：验证集必须包含会产生余数行的形状（批行数不能整除每核行数），否则结构性通过（批行数整除、全零输入、全 run 仅单个余数行）会掩盖损坏？
- 是否命中排除条件：无手工展开的常规掩码循环，以及尾段掩码显式按块起点重建的路径（实测数值干净）？

## 7. 验收标准

正确性：

- 全量 case 精度验证，必须覆盖奇余数行形态（批行数不整除每核行数）与 inf/nan/全零/极小 epsilon
- A/B 逐位差分（改前 vs 改后）确认无非余数行偏差、无行级缩放因子（f≈sqrt(blockCount) 即为损坏签名）

性能：

- 本条目为正确性教训，性能不作为验收维度；在损坏内核上采集的性能数据只能作机制证伪证据，不得作任何加速声明

回滚信号：

- 任一 precision_mismatch 立即回退到上一个 accepted kernel，并按逐行行因子差分定位损坏行集合，区分实现 bug 与机制性损坏后再决定修复或放弃

## 8. 分类与证据

- Classification：`lesson`
- Generality：`common`
- Related anti-patterns：无

- rms_norm-20260825_084147-d55800（round=2, status=rejected）

## 检索卡（短卡）

动作：在每块起点显式重建尾段掩码，弃用展开循环遗留的auto-decrement或POST_UPDATE递减值。
适用：向量函数有手工展开循环，尾段复用掩码寄存器并重初始化auto-decrement sreg。
限制：每块起点重算掩码；验收须逐位差分，覆盖余数行及0/±0/±inf/nan/subnormal。
范围：跨算子的向量函数手工展开与尾段掩码路径。
检索词：auto-decrement sreg、UpdateMask、POST_UPDATE、尾段掩码、ZEROING。
机会：尾段重初始化sreg后，编译产物的后续掩码偏离源码语义。

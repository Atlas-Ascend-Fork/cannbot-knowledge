---
type: Optimization
title: 多行批数据流：rowsPerTile 批处理 + 批量标量 IO + 每批一次队列编排
description: 把逐行 pipeline 迭代改为按 rowsPerTile 批处理：一条多块 2D DataCopyPad + flat R*4B 标量批读。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/multirow-batch-scalar-io-dataflow.md
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
      "UB 侧多块 {R,rowBytes,0,0} 按 k*AlignUp32(rowBytes) padded slot 落盘；UB→GM 压实按每块 AlignUp32(blockLen) 推进 UB 源、GM 连续落盘（host/kernel 的 alignUnit 必须一致）",
      "每核 tile 数 >=2（保深度 2 双缓冲重叠）；R 由 host 按 shape 推导，R==1 回退路径必须逐字保留",
      "新增 TilingData 字段后，run 隔离安装流程不自动刷新 op_tiling 宿主库（libcust_opmaster_rt2.0.so）：每次触碰 host tiling 的 build 后必须重同步，否则旧字段布局喂新结构使 rowsPerTile 读到垃圾值、kernel 以全零输出 + 507035 呈现（环境陷阱，易误判为机制失败）"
    ],
    "excluded_conditions": [
      "宽行 shape 被 flat-span 守卫（R*rowBytes<=65535）钉在 R==1：机制不适用，保持逐字原路径（收益为零但零风险）",
      "把守卫放宽为 per-field 语义并整体抬高 R：copy-safe 且字节精确，但 R 增长超过 ~6 后在多 case 单调回归——G3 近满的 R 挤占深度 2 ping-pong UB（本 run rounds/005 证伪记录）",
      "机制落地后再做跨阶段 MTE2 预取（CopyIn(t+1) 提前到 Compute(t) 前）：scalar 发射流是 pacing 资源，新增 per-tile 预取分支只增 scalar 工作而无重叠收益（本 run rounds/004 证伪记录）",
      "用单条 flat R*rowBytes 整段拷入：奇数行使行首地址非 32B 对齐、迫使 VF 全走 unaligned load（本 run v1 中间版本实测回归后弃用）；奇 H 必须用 padded-slot 多块形式"
    ],
    "required_conditions": [
      "行在每核内连续（host 连续行块 + kernel 连续推导），使 R 行的 x/y/activation_scale/scale 各构成可用单条描述符表达的 GM 跨度",
      "baseline 为每行一个 pipeline 迭代：逐行 MTE 描述符 + 逐行 4B 标量 IO + 4 对 TQue 队列操作，profiling 显示 SCALAR_BOUND 或跨流水 LOW_OVERLAP",
      "UB 预算在深度 2 双缓冲下容纳 R 行批（含 32B padded slot 与标量 slot），host 守卫（flat-span 字段上限、每核 >=2 tile、UB 预算）能按 shape 推导 R，超界回退 R==1 原路径",
      "DataCopyPad 字段上限满足：块 blockLen（字节）<=65535、2D 形式 blockCount<=4095；4B 标量批读走 flat R*4B span（R 为 8 的倍数时 32B 对齐）或 2D padded-slot 形式，批出走 2D 压实",
      "批内 VF 计算仍按行进行（per-row scale/amax 语义不被跨行合并）：批处理只改 IO/编排粒度，不改数学"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-01",
  "evidence": [
    {
      "comparison_sha256": "dc2e5133c1635d602c9766a3c187c83cf2de19a73bf841685398a74b1f044a3e",
      "decision_sha256": "902e7c85235371f115afe7f985b028d068035e768587004c662ccf71702b47c4",
      "operator_class": "fused-composite",
      "performance_sha256": "6ddebf4e44e04ab37276e8b49a05047463a63b5a867bf8a272f5436b100d8961",
      "round": 1,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "3145918b1b17bea51486ee0047c6a9362b03d845153a0d8a0c6c3305d83d18f2",
      "verify_sha256": "c3ad028bbe36e484fadaed26d4bf250cad65c25a1533679e9f8bf67462712343"
    },
    {
      "comparison_sha256": "92feee6ff84d959b0868b8429aa270d03299655b98b99a9a46a0a904a80f614a",
      "decision_sha256": "aa3af16400237f8ecaa9dee1265fb6a8e52eb9f278ace720fe72f2b27991e20a",
      "operator_class": "layout-transform",
      "performance_sha256": "74cecfc4904cff5b90774c3495c569371bdf0522d45a92cbd3a904ecb345c859",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "1c1fa6c1e5e97a385c0247353361b4efdd3b9f3cebe5ac0b39b3687bab11af6a",
      "verify_sha256": "2231d092f6983f7fbc0246a0370f8024072681cec4915e7b36e0b930c19837e9"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "scalar-bound",
      "per-iteration-overhead",
      "low-pipeline-overlap"
    ],
    "dtypes": [
      "int32",
      "fp16",
      "bf16"
    ],
    "pattern": "multirow-batch-scalar-io-dataflow",
    "structure": [
      "row-batching",
      "batched-scalar-io",
      "padded-slot-multiblock-datacopy",
      "tque-batch-orchestration"
    ]
  },
  "generality": "common",
  "id": "DSQ-R1-MULTIROW-BATCH-SCALAR-IO",
  "implementation_steps": [
    "host：DeriveRowsPerTile 按 flat-span 字段上限 / 每核 >=2 tile / 双缓冲 UB 预算推导 R 并写入新 TilingData 字段；保留原 UB 预算校验对 R==1 的可行性检查",
    "kernel Init：解析 rowsPerTile，按 R 缩放队列与缓冲尺寸（R==1 时数值不变）",
    "CopyInBatch/ComputeBatch/CopyOutBatch：padded-slot 多块 x in + flat R*4B 标量批读（GetValue(r) 回读）；内层逐行 VF（y/scale 落 32B slot）；{R,H,0,0} y 压实 + {R,4,0,0} scale 压实",
    "Process：R<=1 走原逐行循环（逐字保留），否则 ceil(myCoreTokens/R) tile 循环 + 尾批裁剪",
    "先用独立 probe 在设备上 bit-exact 验证四种批形式（标量批入 flat/2D、标量压实批出、R 行 span 入、压实批出，含奇 H 与尾批），再全量 verify/measure；用 op_summary 迭代数算术确认每核迭代数按 ~R 下降"
  ],
  "intent": "消除逐行 pipeline 编排开销：每行 2 条 MTE2 + 2 条 MTE3 DataCopyPad（含 4B 标量 padded 到 32B 的描述符）、1 次 GetValue、4 对 TQue Alloc/EnQue/DeQue/Free 与多个 DataCopyExtParams 构造，使 SCALAR_BOUND 或跨流水低重叠的 case 转向 vec/mte-bound。",
  "mechanism": "host 在 tiling 中 DeriveRowsPerTile：G1 flat-span 字段上限 R*rowBytes<=65535、G2 每核 >=2 tile（保深度 2 双缓冲重叠）、G3 双缓冲 UB 预算 2*(R*rowAlignedBytes + [ws]AlignUp32(4R) + R*AlignUp32(H) + R*32) + 常驻 ws/qs + swigluOut + 32 <= UB 容量，任一失败回退 R=1；新 TilingData 字段 rowsPerTile 下发。kernel Init 按 R 缩放队列/缓冲尺寸（R==1 时数值不变）；Process 分支：R<=1 逐字保留原逐行循环，否则 tile 循环 ceil(myCoreTokens/R) + 尾批行裁剪。CopyInBatch：一条多块 {R,rowBytes,0,0} x 拷入（padded slot 布局，A 块 load 恒对齐）+ 一条 flat R*4B activation_scale span；ComputeBatch 内层 r 循环在批缓冲的 per-row 指针上跑原 vf_0→vf_1→vf_2 链（y/scale 落 32B 对齐 slot，per-row scale 语义不变）；CopyOutBatch：一条 {R,H,0,0} y 压实 + 一条 {R,4,0,0} scale 压实；TQue Alloc/EnQue/DeQue/Free 每批一次，BUFFER_NUM=2 跨批 ping-pong 保持 CopyIn(t+1)||Compute(t)||CopyOut(t-1) 重叠。",
  "name": "多行批数据流：rowsPerTile 批处理 + 批量标量 IO + 每批一次队列编排",
  "op": "dequant_swiglu_quant",
  "operator_class": "",
  "operator_scope": "行式（tokens×2H）elementwise 融合数据流：host 给每核连续行块，kernel 每行一个 CopyIn/Compute/CopyOut 迭代（TQue 深度 2 双缓冲），且每行伴随 4B 标量 activation_scale/scale 读写与逐行派生的 per-row scale",
  "principle": "当每行 pipeline 编排（描述符构造、队列操作、标量回读、同步）由 scalar 单元串行发射并成为 wall 时，把 R 行合并为一批可按 ~R 摊薄每行编排成本；批内 GM 跨度连续使多行 x 可由一条多块描述符表达，4B 标量数组可按 flat span 整批读、按 2D 压实整批写。关键布局不变式：多块 {R,rowBytes,srcStride=0,dstStride=0} GM→UB 拷贝在 UB 侧按 k*AlignUp32(rowBytes) padded slot 落盘，与逐行 R==1 路径的 per-row 布局完全一致，批处理不改变 VF 层的对齐假设；UB→GM 多块压实按每块 AlignUp32(blockLen) 推进 UB 源、GM 连续落盘。",
  "related_anti_patterns": [
    "per-element-mte-descriptor-spray"
  ],
  "risks": [
    "flat 整段形式破坏奇 H 行对齐（见排除条件）：必须用 padded-slot 多块形式保持 A 块 load 对齐",
    "host/kernel 的 alignUnit 或 slot 步长不一致会跨行错位；blockCount/blockLen/stride 溢出会构建失败或越界 UB 访问",
    "新增 TilingData 字段触发的宿主库刷新缺口（见 constraints）会以全零输出 + 507035 呈现，须先排除环境因素再判机制",
    "R 推导过保守（坍缩到 1）时机制不生效；抬到 G3 近满则挤压双缓冲重叠而回归（G2/G3 守卫即为此设）"
  ],
  "slug": "multirow-batch-scalar-io-dataflow",
  "summary": "当每行一个 pipeline 迭代、每行携带独立 MTE 描述符、一次标量回读和 4 对 TQue 队列操作时，scalar 单元编排成为 wall；host 按 UB 预算 + DataCopyPad 字段上限 + 每核 tile 数守卫推导 rowsPerTile R，kernel 每批处理 R 行连续行：一条多块 {R,rowBytes,0,0} GM→UB DataCopyPad（UB 按 32B padded slot 落盘，与 R==1 逐行布局一致，A 块 load 保持对齐）、一条 flat R*4B activation_scale 批读（GetValue(r) 回读）、内层逐行 VF 链、一条 {R,H,0,0} y 压实写出、一条 {R,4,0,0} scale 压实写出；TQue 操作与同步每批一次，R==1 时逐字保留原路径。",
  "verification": {
    "correctness": [
      "rounds/001 verify 20/20 通过（all_cases，kernel afcb8e3c114791d8）；v1 flat-span 中间版本曾使奇 H bf16 case 回归（0.884x/0.910x），改 padded-slot 多块形式后 20/20 全过",
      "probe 在设备上 bit-exact 验证四种批形式：flat R 标量批入 + GetValue(r)、{R,4,0,0} scale 压实、R 行 span 入、{R,H,0,0} y 压实；覆盖 int32/bf16/fp16、ws/qs 有无、对齐与奇 H（2049）、R in {3,7,63} 与尾批；无 507015/UB 溢出"
    ],
    "performance": [
      "incremental total_speedup 1.2875x（4376.1→3399.0us/step，11 improved / 0 regressed，最小 control 0.966x）；最大 case 18 2.210x、case 17 2.201x、case 20 1.907x、case 14 1.418x、case 13 1.369x",
      "每核迭代数按 ~R 下降（R 派生使 14/20 case 达 R>=2；case 11/16 被 G1 钉在 R==1，无增益无回归）；官方路径 spot_check case 18 复现（74.79 vs 74.44us，ratio 1.0046）",
      "全部样本 n=1（对称环境边界，双方同协议）；最大声称经官方路径独立复现"
    ],
    "rollback_signals": [
      "宽行 control 中位数 <0.95x（双缓冲重叠丢失）或任一 correctness 失败（正确性范围须为全量 all_cases）",
      "per-core tile 数 <2、507015/字段溢出，或 SCALAR_BOUND case 的迭代数未按 ~R 下降（R 坍缩为 1，机制未触发）",
      "奇 H case 回归（span/尾部处理破坏对齐或越界）"
    ]
  }
}
-->

# 性能优化策略：多行批数据流：rowsPerTile 批处理 + 批量标量 IO + 每批一次队列编排

单一优化点：当每行一个 pipeline 迭代、每行携带独立 MTE 描述符、一次标量回读和 4 对 TQue 队列操作时，scalar 单元编排成为 wall；host 按 UB 预算 + DataCopyPad 字段上限 + 每核 tile 数守卫推导 rowsPerTile R，kernel 每批处理 R 行连续行：一条多块 {R,rowBytes,0,0} GM→UB DataCopyPad（UB 按 32B padded slot 落盘，与 R==1 逐行布局一致，A 块 load 保持对齐）、一条 flat R*4B activation_scale 批读（GetValue(r) 回读）、内层逐行 VF 链、一条 {R,H,0,0} y 压实写出、一条 {R,4,0,0} scale 压实写出；TQue 操作与同步每批一次，R==1 时逐字保留原路径。

## 1. 原理

当每行 pipeline 编排（描述符构造、队列操作、标量回读、同步）由 scalar 单元串行发射并成为 wall 时，把 R 行合并为一批可按 ~R 摊薄每行编排成本；批内 GM 跨度连续使多行 x 可由一条多块描述符表达，4B 标量数组可按 flat span 整批读、按 2D 压实整批写。关键布局不变式：多块 {R,rowBytes,srcStride=0,dstStride=0} GM→UB 拷贝在 UB 侧按 k*AlignUp32(rowBytes) padded slot 落盘，与逐行 R==1 路径的 per-row 布局完全一致，批处理不改变 VF 层的对齐假设；UB→GM 多块压实按每块 AlignUp32(blockLen) 推进 UB 源、GM 连续落盘。

实现机制：host 在 tiling 中 DeriveRowsPerTile：G1 flat-span 字段上限 R*rowBytes<=65535、G2 每核 >=2 tile（保深度 2 双缓冲重叠）、G3 双缓冲 UB 预算 2*(R*rowAlignedBytes + [ws]AlignUp32(4R) + R*AlignUp32(H) + R*32) + 常驻 ws/qs + swigluOut + 32 <= UB 容量，任一失败回退 R=1；新 TilingData 字段 rowsPerTile 下发。kernel Init 按 R 缩放队列/缓冲尺寸（R==1 时数值不变）；Process 分支：R<=1 逐字保留原逐行循环，否则 tile 循环 ceil(myCoreTokens/R) + 尾批行裁剪。CopyInBatch：一条多块 {R,rowBytes,0,0} x 拷入（padded slot 布局，A 块 load 恒对齐）+ 一条 flat R*4B activation_scale span；ComputeBatch 内层 r 循环在批缓冲的 per-row 指针上跑原 vf_0→vf_1→vf_2 链（y/scale 落 32B 对齐 slot，per-row scale 语义不变）；CopyOutBatch：一条 {R,H,0,0} y 压实 + 一条 {R,4,0,0} scale 压实；TQue Alloc/EnQue/DeQue/Free 每批一次，BUFFER_NUM=2 跨批 ping-pong 保持 CopyIn(t+1)||Compute(t)||CopyOut(t-1) 重叠。

## 2. 性能问题模式

- 优化目标：消除逐行 pipeline 编排开销：每行 2 条 MTE2 + 2 条 MTE3 DataCopyPad（含 4B 标量 padded 到 32B 的描述符）、1 次 GetValue、4 对 TQue Alloc/EnQue/DeQue/Free 与多个 DataCopyExtParams 构造，使 SCALAR_BOUND 或跨流水低重叠的 case 转向 vec/mte-bound。
- 适用数据流：行式（tokens×2H）elementwise 融合数据流：host 给每核连续行块，kernel 每行一个 CopyIn/Compute/CopyOut 迭代（TQue 深度 2 双缓冲），且每行伴随 4B 标量 activation_scale/scale 读写与逐行派生的 per-row scale
- Feature signature：`{"bottleneck": ["scalar-bound", "per-iteration-overhead", "low-pipeline-overlap"], "dtypes": ["int32", "fp16", "bf16"], "pattern": "multirow-batch-scalar-io-dataflow", "structure": ["row-batching", "batched-scalar-io", "padded-slot-multiblock-datacopy", "tque-batch-orchestration"]}`

## 3. 正确性红线

- flat 整段形式破坏奇 H 行对齐（见排除条件）：必须用 padded-slot 多块形式保持 A 块 load 对齐
- host/kernel 的 alignUnit 或 slot 步长不一致会跨行错位；blockCount/blockLen/stride 溢出会构建失败或越界 UB 访问
- 新增 TilingData 字段触发的宿主库刷新缺口（见 constraints）会以全零输出 + 507035 呈现，须先排除环境因素再判机制
- R 推导过保守（坍缩到 1）时机制不生效；抬到 G3 近满则挤压双缓冲重叠而回归（G2/G3 守卫即为此设）

资源与硬件约束：

- UB 侧多块 {R,rowBytes,0,0} 按 k*AlignUp32(rowBytes) padded slot 落盘；UB→GM 压实按每块 AlignUp32(blockLen) 推进 UB 源、GM 连续落盘（host/kernel 的 alignUnit 必须一致）
- 每核 tile 数 >=2（保深度 2 双缓冲重叠）；R 由 host 按 shape 推导，R==1 回退路径必须逐字保留
- 新增 TilingData 字段后，run 隔离安装流程不自动刷新 op_tiling 宿主库（libcust_opmaster_rt2.0.so）：每次触碰 host tiling 的 build 后必须重同步，否则旧字段布局喂新结构使 rowsPerTile 读到垃圾值、kernel 以全零输出 + 507035 呈现（环境陷阱，易误判为机制失败）

## 4. 泛化条件

- 策略作用域：common（跨 operator class）

适用：

- 行在每核内连续（host 连续行块 + kernel 连续推导），使 R 行的 x/y/activation_scale/scale 各构成可用单条描述符表达的 GM 跨度
- baseline 为每行一个 pipeline 迭代：逐行 MTE 描述符 + 逐行 4B 标量 IO + 4 对 TQue 队列操作，profiling 显示 SCALAR_BOUND 或跨流水 LOW_OVERLAP
- UB 预算在深度 2 双缓冲下容纳 R 行批（含 32B padded slot 与标量 slot），host 守卫（flat-span 字段上限、每核 >=2 tile、UB 预算）能按 shape 推导 R，超界回退 R==1 原路径
- DataCopyPad 字段上限满足：块 blockLen（字节）<=65535、2D 形式 blockCount<=4095；4B 标量批读走 flat R*4B span（R 为 8 的倍数时 32B 对齐）或 2D padded-slot 形式，批出走 2D 压实
- 批内 VF 计算仍按行进行（per-row scale/amax 语义不被跨行合并）：批处理只改 IO/编排粒度，不改数学

不适用：

- 宽行 shape 被 flat-span 守卫（R*rowBytes<=65535）钉在 R==1：机制不适用，保持逐字原路径（收益为零但零风险）
- 把守卫放宽为 per-field 语义并整体抬高 R：copy-safe 且字节精确，但 R 增长超过 ~6 后在多 case 单调回归——G3 近满的 R 挤占深度 2 ping-pong UB（本 run rounds/005 证伪记录）
- 机制落地后再做跨阶段 MTE2 预取（CopyIn(t+1) 提前到 Compute(t) 前）：scalar 发射流是 pacing 资源，新增 per-tile 预取分支只增 scalar 工作而无重叠收益（本 run rounds/004 证伪记录）
- 用单条 flat R*rowBytes 整段拷入：奇数行使行首地址非 32B 对齐、迫使 VF 全走 unaligned load（本 run v1 中间版本实测回归后弃用）；奇 H 必须用 padded-slot 多块形式

## 5. 实施步骤

1. host：DeriveRowsPerTile 按 flat-span 字段上限 / 每核 >=2 tile / 双缓冲 UB 预算推导 R 并写入新 TilingData 字段；保留原 UB 预算校验对 R==1 的可行性检查
2. kernel Init：解析 rowsPerTile，按 R 缩放队列与缓冲尺寸（R==1 时数值不变）
3. CopyInBatch/ComputeBatch/CopyOutBatch：padded-slot 多块 x in + flat R*4B 标量批读（GetValue(r) 回读）；内层逐行 VF（y/scale 落 32B slot）；{R,H,0,0} y 压实 + {R,4,0,0} scale 压实
4. Process：R<=1 走原逐行循环（逐字保留），否则 ceil(myCoreTokens/R) tile 循环 + 尾批裁剪
5. 先用独立 probe 在设备上 bit-exact 验证四种批形式（标量批入 flat/2D、标量压实批出、R 行 span 入、压实批出，含奇 H 与尾批），再全量 verify/measure；用 op_summary 迭代数算术确认每核迭代数按 ~R 下降

## 6. LLM 前置问题

- 目标实现是否满足：行在每核内连续（host 连续行块 + kernel 连续推导），使 R 行的 x/y/activation_scale/scale 各构成可用单条描述符表达的 GM 跨度？
- 目标实现是否满足：baseline 为每行一个 pipeline 迭代：逐行 MTE 描述符 + 逐行 4B 标量 IO + 4 对 TQue 队列操作，profiling 显示 SCALAR_BOUND 或跨流水 LOW_OVERLAP？
- 目标实现是否满足：UB 预算在深度 2 双缓冲下容纳 R 行批（含 32B padded slot 与标量 slot），host 守卫（flat-span 字段上限、每核 >=2 tile、UB 预算）能按 shape 推导 R，超界回退 R==1 原路径？
- 是否命中排除条件：宽行 shape 被 flat-span 守卫（R*rowBytes<=65535）钉在 R==1：机制不适用，保持逐字原路径（收益为零但零风险）？

## 7. 验收标准

正确性：

- rounds/001 verify 20/20 通过（all_cases，kernel afcb8e3c114791d8）；v1 flat-span 中间版本曾使奇 H bf16 case 回归（0.884x/0.910x），改 padded-slot 多块形式后 20/20 全过
- probe 在设备上 bit-exact 验证四种批形式：flat R 标量批入 + GetValue(r)、{R,4,0,0} scale 压实、R 行 span 入、{R,H,0,0} y 压实；覆盖 int32/bf16/fp16、ws/qs 有无、对齐与奇 H（2049）、R in {3,7,63} 与尾批；无 507015/UB 溢出

性能：

- incremental total_speedup 1.2875x（4376.1→3399.0us/step，11 improved / 0 regressed，最小 control 0.966x）；最大 case 18 2.210x、case 17 2.201x、case 20 1.907x、case 14 1.418x、case 13 1.369x
- 每核迭代数按 ~R 下降（R 派生使 14/20 case 达 R>=2；case 11/16 被 G1 钉在 R==1，无增益无回归）；官方路径 spot_check case 18 复现（74.79 vs 74.44us，ratio 1.0046）
- 全部样本 n=1（对称环境边界，双方同协议）；最大声称经官方路径独立复现

回滚信号：

- 宽行 control 中位数 <0.95x（双缓冲重叠丢失）或任一 correctness 失败（正确性范围须为全量 all_cases）
- per-core tile 数 <2、507015/字段溢出，或 SCALAR_BOUND case 的迭代数未按 ~R 下降（R 坍缩为 1，机制未触发）
- 奇 H case 回归（span/尾部处理破坏对齐或越界）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`common`
- Related anti-patterns：per-element-mte-descriptor-spray

- dequant_swiglu_quant-20260831_113139-0cf99e（round=1, status=accepted）
- moe_re_routing-20260903_134013-4b9448（round=3, status=accepted）

## 检索卡（短卡）

动作：把逐行 pipeline 迭代改为按 rowsPerTile 批处理：一条多块 2D DataCopyPad + flat R*4B 标量批读。
适用：行在每核内连续、每行一个 pipeline 迭代且每核 tile >=2、profiling 显示 SCALAR_BOUND。
限制：blockLen<=65535、blockCount<=4095；须用 padded-slot 形式；R==1 回退逐字保留。
范围：行式 elementwise 融合数据流的逐行流水编排。
检索词：rowsPerTile、DataCopyPad、padded slot、BUFFER_NUM=2、TQue
机会：每行 2 条 MTE2/MTE3 描述符、1 次 GetValue、4 对 TQue 操作由 scalar 串行发射。
代价：R 抬到 UB 近满会挤压深度 2 ping-pong 重叠；新增 TilingData 字段须重同步。

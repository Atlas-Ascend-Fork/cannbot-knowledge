---
type: Optimization
title: GM 访存节食：成对打包事务 / 直访载体解除 chunk 上界 / 尾块右尺寸紧凑落盘
description: 把相邻两元素打包进一次宽事务、UB chunk 流水改为 direct-GM SIMT 载体、尾块改右尺寸紧凑落盘。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/gm-access-diet.md
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
      "打包路径的语义必须按位不变：寄存器内拆包 → 各自独立计算（数学逐字同源）→ 重打包，非稠密/广播/尾窗等不命中的情形逐字保留原实现为回退臂",
      "尾块右对齐须紧凑落盘：dstStride 必须保持 0，blockLen=AlignUp32(有效字节)；新增的 pitch 推导须单源（CopyIn 与 Compute 共用同一个 TailPitchElems）",
      "direct-GM SIMT 载体需要独立 tiling-key 实例做隔离（多个 __simt_vf__ 不可共存于同一实例），且 Init 需追加行映射表 GM 地址直读",
      "门控条件必须显式且可静态判定（稠密 canon 逐维相等 / 全 D 窗 / 侧 strides 相等），逐线程入口一次均匀分支"
    ],
    "excluded_conditions": [
      "dstStride!=0 的 DataCopyPad GM→UB 组合在本后端会触发设备侧 AIV 异常——尾块必须紧凑落盘（dstStride=0），不可用 dstStride 做塌陷",
      "非稠密/广播/D 尾窗等不命中门控的路径不适用，须走原回退臂（本 run gcd I64 臂与 host/tiling 零改动，产物 SHA 复核 byte-identical）",
      "ubChunk 未被双缓冲 UB 跨度压制时不适用：direct-GM 载体的收益来自解除 chunk 上界，若 chunk 本就够大则收益有限",
      "行重用以 L2 为主的 case（请求率锁死）收益有限：本 run gather case10 仅 1.013x，属预测内持平"
    ],
    "required_conditions": [
      "profiling 显示逐元素 GM 访问成本主导（本 run gcd 两级线性拟合：dtype 无关固定成本 ≈3.97 cyc/elem 占 83-93%，排除法收敛到 3 次/元素 direct-GM 逐 lane 访问；gather case5/10 vec_ratio 0.998/0.995；arg_max case10 aiv_mte2 125.43us / kernel 134.401us = 93%）",
      "存在可压缩的访问结构：可成对打包（每元素 GM 访问 3→1.5）、可解除 chunk 上界换全 wave 在飞（本 run gather ubChunk 被 SIMT_SAFE_FOOTPRINT_BYTES=8192B 压至 256/682，在飞 load 数 ≤chunkLen）、或尾块存在流量放大（本 run arg_max case10 尾 ib 有效 20B 却每块仍复制 1472B）",
      "同 vendor 树已有已验证的同类载体可作为先例（本 run gather 参照 gcd.h 已验证的 __simt_vf__ 直接 GM 读+写与 grid-stride 多迭代）",
      "打包访存有匹配的发射宽度：u64 打包的实际发射宽度可能低于半减假设（见 risks）"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 93.78,
      "before_us": 143.6,
      "mechanism": "dense-flat-pair-packed-gm-io",
      "operator": "gcd",
      "operator_class": "broadcast",
      "pairs": 10,
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "speedup": 1.5313,
      "status": "accepted"
    },
    {
      "after_us": 242.572,
      "before_us": 267.415,
      "mechanism": "whole-row-direct-gm-simt-carrier",
      "operator": "gather",
      "operator_class": "index-gather",
      "pairs": 45,
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "speedup": 1.1024,
      "status": "accepted"
    },
    {
      "after_us": 155.325,
      "before_us": 171.848,
      "mechanism": "right-sized-tail-block-dma",
      "operator": "arg_max",
      "operator_class": "sort-select",
      "pairs": 10,
      "pair_ratio_range": "1.1043-1.1075",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "speedup": 1.1064,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "per-element-gm-access-cost",
      "dma-traffic-amplification",
      "chunk-capped-inflight-loads",
      "mte2-saturation"
    ],
    "pattern": "gm-access-compression",
    "structure": [
      "pair-packed-single-transaction",
      "direct-gm-simt-carrier-full-wave",
      "right-sized-tail-block-compact-landing",
      "dense-canonical-gate-with-fallback-arm"
    ]
  },
  "generality": "op_class",
  "id": "GM-ACCESS-DIET",
  "implementation_steps": [
    "先量化访问成本来源：做两级线性拟合分离固定成本与指令相关成本（本 run gcd：cyc/elem ≈ 3.97(固定) + 0.0053×body指令×平均迭代数），用排除法定位到「每元素 N 次 direct-GM 逐 lane 访问」",
    "成对打包路径：新增门控谓词（全 D 窗 + 两侧 strides 与稠密 canon 逐维相等，逐线程入口一次均匀分支）+ 与原子核热循环逐字同源的 SteinCore；每线程每 k 迭代处理 2 个相邻元素——1 次 u32/u64 打包 load 每输入覆盖 2 元素 + 寄存器内拆包 → 各自独立计算 → 重打包 → 1 次打包 store；寻址由逐元素 odometer 换成每对一次的平坦游标 gStart+2*pi",
    "direct-GM SIMT 载体路径：tiling_data 追加开关字段；host 侧命中时 route 到独立编号（新独立 tiling-key 实例）并置开关；tiling_key 模板键扩位新增该组合；新增 DirectVF（index GM 直读 + x GM 散射读 + y GM 直写，行循环 grid-stride 多迭代）；kernel 模板追加 DIRECT 参；Init 追加行映射表 GM 地址直读；Process 命中分支单次 VF 调用覆盖本核全部行；非命中显式置 false 做实例级隔离",
    "尾块右尺寸路径：尾 ib 按有效字节右对齐 blockLen=AlignUp32(有效字节)，紧凑落盘 dstStride=0，新增 TailPitchElems 单源推导供 CopyIn 与 Compute 共用，Compute 以 pitch 作为累加器宽度实参（VF 函数体零修改）",
    "不命中门控的路径逐字保留为回退臂"
  ],
  "intent": "逐元素路径上，wall 常由每元素的 GM 访问成本决定（访问次数 × 每次固定惩罚），或由 MTE2 的 DMA 流量放大决定。三类已验证的压缩手段：把 2 个相邻元素打包进 1 次宽事务（3→1.5 访问/元素）、解除 chunk 上界改直访 GM 让在飞 load 达到全 wave、把越界跨读的尾块改成右尺寸紧凑落盘。",
  "mechanism": "三类 GM 访存节食手段。(a) 稠密门控平坦成对打包：x1/x2 均为规范稠密行主序且窗口为全 D 范围时，每线程每 k 迭代处理 2 个相邻元素——1 次 u32(I16)/u64(I32) 打包 load 每输入（覆盖 2 元素）+ 寄存器内拆包 → 各自独立计算（数学逐字同源）→ 重打包 → 1 次打包 store；寻址由逐元素 odometer/回绕机换成每对一次的平坦游标，每元素 GM 访问数 3→1.5。(b) 整行 direct-GM SIMT 载体：以 index GM 直读 + x GM 散射读 + y GM 直写替代 UB 队列 chunk 流水，消除 index MTE2/y MTE3 中转与 per-chunk 队列/启动税，在飞 GM load 数从 chunkLen 升至全 wave。(c) 尾块右尺寸紧凑落盘：尾 inner 块按有效字节右对齐 blockLen 并保持 dstStride=0 紧凑落盘，消除整宽搬运造成的 DMA 流量放大。三者都不命中门控时逐字保留原实现为回退臂。",
  "name": "GM 访存节食：成对打包事务 / 直访载体解除 chunk 上界 / 尾块右尺寸紧凑落盘",
  "operator_class": "index-gather",
  "operator_scope": "逐元素路径上 GM 访问成本主导（每元素多次 direct-GM 逐 lane 访问或 MTE2 饱和）的算子，存在可成对打包、可解除 chunk 上界或尾块流量放大的结构",
  "principle": "逐元素路径的 GM 成本 = 访问次数 × 每次固定惩罚，且固定惩罚常与 dtype 无关（本 run gcd 拟合出 3.97 cyc/elem 的 dtype 无关固定项，占 83-93%）。因此三类手段有明确的作用点：成对打包把访问次数减半（3→1.5/元素）、直访载体把在飞 load 数从 chunk 上界解到全 wave、尾块右尺寸消除无效字节的搬运放大。判定收益前须先用两级线性拟合把固定成本与指令相关成本分离，否则会误把依赖链当访问成本。",
  "related_anti_patterns": [],
  "risks": [
    "dstStride!=0 的 DataCopyPad GM→UB 组合在本后端触发设备侧 AIV 异常：本 run arg_max round_001 用 dstStride 做尾块塌陷导致 case8 设备异常，round_002 改紧凑落盘（dstStride=0）+ VF 侧 pitch 消费才通过。崩溃归因经排除法唯一收敛到 dstStride≠0（仓内与策略库全部已验证用法均 dstStride=0）",
    "u64 打包的实际发射宽度可能低于半减假设：本 run gcd I32/u64 侧仅兑现 -20%（对比 I16/u32 侧 -32%/-49%），提示打包收益与打包宽度非线性",
    "多个 __simt_vf__ 不可共存于同一模板实例，必须用独立 tiling-key 做实例级隔离",
    "行重用以 L2 为主的 case 受请求率锁死，直访载体收益有限（gather case10 仅 1.013x）"
  ],
  "slug": "gm-access-diet",
  "summary": "三类 GM 访存节食手段的合并族：(a) 稠密门控平坦成对打包（gcd，每元素 GM 访问 3→1.5，geomean 143.60→93.78us ×1.5313，逐 case 1.4568/1.2545/1.9648x）；(b) 整行 direct-GM SIMT 载体（gather，消除 index MTE2/y MTE3 中转与 per-chunk 队列税，在飞 load 从 chunkLen 256/682 升至全 wave 512/1024，45 对配对 geomean ×1.1024）；(c) 尾块右尺寸紧凑落盘（arg_max，消除尾 inner 块整宽搬运的 DMA 流量放大，×1.1064）。三者均精度 20/20，非命中路径逐字保留为回退臂。",
  "verification": {
    "correctness": [
      "gcd：编译/精度一次通过（0 修复），20/20 位型一致；产物 SHA 复核 I64 kernel byte-identical，仅 I16/I32 kernel 变更",
      "gather：三重门全通过，45 对平衡交替配对候选全胜，无 case 回退",
      "arg_max：编译 0 修复、精度修复 1 次（round_001 dstStride≠0 触发设备异常 → round_002 紧凑落盘），20/20 PASS"
    ],
    "performance": [
      "gcd：形式化 10 对平衡交替配对（同 shape、byte-identical rebuild 溯源、30/30 逐对更快），geomean 143.60→93.78us（1.5313x）",
      "gather：形式化 45 对配对，geomean 267.415→242.572us（1.1024x）；case5 1.285x、case10 1.013x（L2 请求率锁死分支如预测持平）、case1 1.029x",
      "arg_max：形式化 10 对 ABBA 配对全对正向（pair ratio 1.1043-1.1075），case10 134.359→99.261us（1.3536x），kernel_geomean 171.848→155.325us（1.1064x），T1 路径零扰动",
      "成本拟合：gcd cyc/elem ≈ 3.97(固定) + 0.0053×body指令×平均迭代数，dtype 无关固定成本占 83-93%"
    ],
    "rollback_signals": [
      "使用 dstStride!=0 的 DataCopyPad 组合（本后端确定会触发设备异常）",
      "打包路径与非打包路径语义不再按位一致（回退臂漏隔离）",
      "多个 VF 载体共用同一模板实例导致实例级隔离失效",
      "未命中门控的路径出现超出噪声的回退"
    ]
  }
}
-->

# 性能优化策略：GM 访存节食：成对打包事务 / 直访载体解除 chunk 上界 / 尾块右尺寸紧凑落盘

三类 GM 访存节食手段的合并族：(a) 稠密门控平坦成对打包（gcd，每元素 GM 访问 3→1.5，geomean 143.60→93.78us ×1.5313）；(b) 整行 direct-GM SIMT 载体（gather，消除 index MTE2/y MTE3 中转与 per-chunk 队列税，在飞 load 从 chunkLen 256/682 升至全 wave 512/1024，45 对配对 geomean ×1.1024）；(c) 尾块右尺寸紧凑落盘（arg_max，消除尾 inner 块整宽搬运的 DMA 流量放大，×1.1064）。三者均精度 20/20，非命中路径逐字保留为回退臂。

## 1. 原理

逐元素路径的 GM 成本 = 访问次数 × 每次固定惩罚，且固定惩罚常与 dtype 无关（本 run gcd 拟合出 3.97 cyc/elem 的 dtype 无关固定项，占 83-93%）。因此三类手段有明确的作用点：成对打包把访问次数减半（3→1.5/元素）、直访载体把在飞 load 数从 chunk 上界解到全 wave、尾块右尺寸消除无效字节的搬运放大。判定收益前须先用两级线性拟合把固定成本与指令相关成本分离，否则会误把依赖链当访问成本。

实现机制：三类 GM 访存节食手段。(a) 稠密门控平坦成对打包：x1/x2 均为规范稠密行主序且窗口为全 D 范围时，每线程每 k 迭代处理 2 个相邻元素——1 次 u32(I16)/u64(I32) 打包 load 每输入（覆盖 2 元素）+ 寄存器内拆包 → 各自独立计算（数学逐字同源）→ 重打包 → 1 次打包 store；寻址由逐元素 odometer/回绕机换成每对一次的平坦游标，每元素 GM 访问数 3→1.5。(b) 整行 direct-GM SIMT 载体：以 index GM 直读 + x GM 散射读 + y GM 直写替代 UB 队列 chunk 流水，消除 index MTE2/y MTE3 中转与 per-chunk 队列/启动税，在飞 GM load 数从 chunkLen 升至全 wave。(c) 尾块右尺寸紧凑落盘：尾 inner 块按有效字节右对齐 blockLen 并保持 dstStride=0 紧凑落盘，消除整宽搬运造成的 DMA 流量放大。

## 2. 性能问题模式

- 优化目标：逐元素路径上，wall 常由每元素的 GM 访问成本决定（访问次数 × 每次固定惩罚），或由 MTE2 的 DMA 流量放大决定。三类已验证的压缩手段：把 2 个相邻元素打包进 1 次宽事务（3→1.5 访问/元素）、解除 chunk 上界改直访 GM 让在飞 load 达到全 wave、把越界跨读的尾块改成右尺寸紧凑落盘
- 适用数据流：逐元素路径上 GM 访问成本主导（每元素多次 direct-GM 逐 lane 访问或 MTE2 饱和）的算子，存在可成对打包、可解除 chunk 上界或尾块流量放大的结构
- Feature signature：`{"bottleneck": ["per-element-gm-access-cost", "dma-traffic-amplification", "chunk-capped-inflight-loads", "mte2-saturation"], "pattern": "gm-access-compression", "structure": ["pair-packed-single-transaction", "direct-gm-simt-carrier-full-wave", "right-sized-tail-block-compact-landing", "dense-canonical-gate-with-fallback-arm"]}`

## 3. 正确性红线

- dstStride!=0 的 DataCopyPad GM→UB 组合在本后端触发设备侧 AIV 异常：本 run arg_max round_001 用 dstStride 做尾块塌陷导致 case8 设备异常，round_002 改紧凑落盘（dstStride=0）+ VF 侧 pitch 消费才通过。崩溃归因经排除法唯一收敛到 dstStride≠0（仓内与策略库全部已验证用法均 dstStride=0）
- u64 打包的实际发射宽度可能低于半减假设：本 run gcd I32/u64 侧仅兑现 -20%（对比 I16/u32 侧 -32%/-49%），提示打包收益与打包宽度非线性
- 多个 __simt_vf__ 不可共存于同一模板实例，必须用独立 tiling-key 做实例级隔离
- 行重用以 L2 为主的 case 受请求率锁死，直访载体收益有限（gather case10 仅 1.013x）

资源与硬件约束：

- 打包路径的语义必须按位不变：寄存器内拆包 → 各自独立计算（数学逐字同源）→ 重打包，非稠密/广播/尾窗等不命中的情形逐字保留原实现为回退臂
- 尾块右对齐须紧凑落盘：dstStride 必须保持 0，blockLen=AlignUp32(有效字节)；新增的 pitch 推导须单源（CopyIn 与 Compute 共用同一个 TailPitchElems）
- direct-GM SIMT 载体需要独立 tiling-key 实例做隔离（多个 __simt_vf__ 不可共存于同一实例），且 Init 需追加行映射表 GM 地址直读
- 门控条件必须显式且可静态判定（稠密 canon 逐维相等 / 全 D 窗 / 侧 strides 相等），逐线程入口一次均匀分支

## 4. 泛化条件

- 策略作用域：op_class：index-gather

适用：

- profiling 显示逐元素 GM 访问成本主导（本 run gcd 两级线性拟合：dtype 无关固定成本 ≈3.97 cyc/elem 占 83-93%，排除法收敛到 3 次/元素 direct-GM 逐 lane 访问；gather case5/10 vec_ratio 0.998/0.995；arg_max case10 aiv_mte2 125.43us / kernel 134.401us = 93%）
- 存在可压缩的访问结构：可成对打包（每元素 GM 访问 3→1.5）、可解除 chunk 上界换全 wave 在飞（本 run gather ubChunk 被 SIMT_SAFE_FOOTPRINT_BYTES=8192B 压至 256/682，在飞 load 数 ≤chunkLen）、或尾块存在流量放大（本 run arg_max case10 尾 ib 有效 20B 却每块仍复制 1472B）
- 同 vendor 树已有已验证的同类载体可作为先例（本 run gather 参照 gcd.h 已验证的 __simt_vf__ 直接 GM 读+写与 grid-stride 多迭代）
- 打包访存有匹配的发射宽度：u64 打包的实际发射宽度可能低于半减假设（见 risks）

不适用：

- dstStride!=0 的 DataCopyPad GM→UB 组合在本后端会触发设备侧 AIV 异常——尾块必须紧凑落盘（dstStride=0），不可用 dstStride 做塌陷
- 非稠密/广播/D 尾窗等不命中门控的路径不适用，须走原回退臂（本 run gcd I64 臂与 host/tiling 零改动，产物 SHA 复核 byte-identical）
- ubChunk 未被双缓冲 UB 跨度压制时不适用：direct-GM 载体的收益来自解除 chunk 上界，若 chunk 本就够大则收益有限
- 行重用以 L2 为主的 case（请求率锁死）收益有限：本 run gather case10 仅 1.013x，属预测内持平

## 5. 实施步骤

1. 先量化访问成本来源：做两级线性拟合分离固定成本与指令相关成本（本 run gcd：cyc/elem ≈ 3.97(固定) + 0.0053×body指令×平均迭代数），用排除法定位到「每元素 N 次 direct-GM 逐 lane 访问」
2. 成对打包路径：新增门控谓词（全 D 窗 + 两侧 strides 与稠密 canon 逐维相等，逐线程入口一次均匀分支）+ 与原子核热循环逐字同源的 SteinCore；每线程每 k 迭代处理 2 个相邻元素——1 次 u32/u64 打包 load 每输入覆盖 2 元素 + 寄存器内拆包 → 各自独立计算 → 重打包 → 1 次打包 store；寻址由逐元素 odometer 换成每对一次的平坦游标 gStart+2*pi
3. direct-GM SIMT 载体路径：tiling_data 追加开关字段；host 侧命中时 route 到独立编号（新独立 tiling-key 实例）并置开关；tiling_key 模板键扩位新增该组合；新增 DirectVF（index GM 直读 + x GM 散射读 + y GM 直写，行循环 grid-stride 多迭代）；kernel 模板追加 DIRECT 参；Init 追加行映射表 GM 地址直读；Process 命中分支单次 VF 调用覆盖本核全部行；非命中显式置 false 做实例级隔离
4. 尾块右尺寸路径：尾 ib 按有效字节右对齐 blockLen=AlignUp32(有效字节)，紧凑落盘 dstStride=0，新增 TailPitchElems 单源推导供 CopyIn 与 Compute 共用，Compute 以 pitch 作为累加器宽度实参（VF 函数体零修改）
5. 不命中门控的路径逐字保留为回退臂

## 6. LLM 前置问题

- 目标实现是否满足：profiling 显示逐元素 GM 访问成本主导（本 run gcd 两级线性拟合：dtype 无关固定成本 ≈3.97 cyc/elem 占 83-93%，排除法收敛到 3 次/元素 direct-GM 逐 lane 访问；gather case5/10 vec_ratio 0.998/0.995；arg_max case10 aiv_mte2 125.43us / kernel 134.401us = 93%）？
- 目标实现是否满足：存在可压缩的访问结构：可成对打包（每元素 GM 访问 3→1.5）、可解除 chunk 上界换全 wave 在飞（本 run gather ubChunk 被 SIMT_SAFE_FOOTPRINT_BYTES=8192B 压至 256/682，在飞 load 数 ≤chunkLen）、或尾块存在流量放大（本 run arg_max case10 尾 ib 有效 20B 却每块仍复制 1472B）？
- 目标实现是否满足：同 vendor 树已有已验证的同类载体可作为先例（本 run gather 参照 gcd.h 已验证的 __simt_vf__ 直接 GM 读+写与 grid-stride 多迭代）？
- 目标实现是否满足：打包访存有匹配的发射宽度：u64 打包的实际发射宽度可能低于半减假设（见 risks）？
- 是否命中排除条件：dstStride!=0 的 DataCopyPad GM→UB 组合在本后端会触发设备侧 AIV 异常——尾块必须紧凑落盘（dstStride=0），不可用 dstStride 做塌陷？

## 7. 验收标准

正确性：

- gcd：编译/精度一次通过（0 修复），20/20 位型一致；产物 SHA 复核 I64 kernel byte-identical，仅 I16/I32 kernel 变更
- gather：三重门全通过，45 对平衡交替配对候选全胜，无 case 回退
- arg_max：编译 0 修复、精度修复 1 次（round_001 dstStride≠0 触发设备异常 → round_002 紧凑落盘），20/20 PASS

性能：

- gcd：形式化 10 对平衡交替配对（同 shape、byte-identical rebuild 溯源、30/30 逐对更快），geomean 143.60→93.78us（1.5313x）
- gather：形式化 45 对配对，geomean 267.415→242.572us（1.1024x）；case5 1.285x、case10 1.013x（L2 请求率锁死分支如预测持平）、case1 1.029x
- arg_max：形式化 10 对 ABBA 配对全对正向（pair ratio 1.1043-1.1075），case10 134.359→99.261us（1.3536x），kernel_geomean 171.848→155.325us（1.1064x），T1 路径零扰动
- 成本拟合：gcd cyc/elem ≈ 3.97(固定) + 0.0053×body指令×平均迭代数，dtype 无关固定成本占 83-93%

回滚信号：

- 使用 dstStride!=0 的 DataCopyPad 组合（本后端确定会触发设备异常）
- 打包路径与非打包路径语义不再按位一致（回退臂漏隔离）
- 多个 VF 载体共用同一模板实例导致实例级隔离失效
- 未命中门控的路径出现超出噪声的回退

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260907_170122-free-002（operator=gcd, mechanism=dense-flat-pair-packed-gm-io, status=accepted, speedup=1.5313, 143.60→93.78us, 10 对配对）
- loop_20260907_170122-free-001（operator=gather, mechanism=whole-row-direct-gm-simt-carrier, status=accepted, speedup=1.1024, 267.415→242.572us, 45 对配对）
- loop_20260907_170122-free-002（operator=arg_max, mechanism=right-sized-tail-block-dma, status=accepted, speedup=1.1064, 171.848→155.325us, 10 对 ABBA）

## 检索卡（短卡）

动作：把相邻两元素打包进一次宽事务、UB chunk 流水改为 direct-GM SIMT 载体、尾块改右尺寸紧凑落盘
适用：逐元素 GM 访问成本主导或 MTE2 饱和；存在可成对打包、可解除 chunk 上界或尾块放大
限制：dstStride!=0 的 DataCopyPad GM→UB 触发 AIV 异常；多 __simt_vf__ 不可共存于同一实例
范围：index-gather 的 direct-GM 访问路径
检索词：成对打包、direct-GM SIMT、__simt_vf__、tiling-key 隔离、TailPitchElems
机会：逐元素 GM 成本=访问次数×固定惩罚（3.97 cyc/elem 占 83-93%）
代价：u64 打包发射宽度低于半减假设（I32 侧仅 -20%）；L2 锁死 case 收益有限

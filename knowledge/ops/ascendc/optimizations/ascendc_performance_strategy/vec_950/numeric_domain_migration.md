---
type: Optimization
title: 数值域迁移：从后端罚分域搬到便宜向量域（int64→int32 hi/lo 拆分 / fp16→fp32 加宽 SIMD）
description: 把计算从后端罚分域搬到便宜向量域：int64 走 hi/lo 拆分的 int32 字典序键，fp16 走 fp32 向量链→RNE narrow。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/numeric-domain-migration.md
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
      "域迁移后的语义必须与 golden 位级或护栏内等价：int64 走 hi/lo 拆分的字典序键编码，fp16 走 widen→fp32 向量链→RNE narrow 往返",
      "int64→int32 拆分时键编码须精确：hi 用原码有符号比较（正数 hi>=0 / 负数 hi<=-1 天然保序，不翻转），lo 经 klo=lo+0x80000000 翻转后比较有符号序（与无符号序等价）",
      "低精度路径迁移后须保留原有的精确分支护栏（如 fp32 域上的 x<=-7 精确分支），不可因升维而丢失分支语义",
      "两条域迁移路径都必须显式保留原域实现为回退臂，按门控派发，语义按位不变"
    ],
    "excluded_conditions": [
      "目标域本身已是便宜域时不适用（如计算本就在 int32/fp32 向量域）",
      "宽类型指令不被后端软件分解的硬件上收益不成立：本机制的 16 倍罚分（~9.7 vs ~0.6 cycle/条）是 ascend950/dav 后端的具体事实，换硬件需重新标定",
      "低精度标量链本身已足够短（每元素个位数标量 op）时，升维 SIMD 化的收益不足以覆盖 widen/narrow 两次 cast",
      "b64 罚分若实为依赖链或加载瓶颈而非发射分解，则换域无效——须先用每指令成本恒定性交叉标定（见下）排除"
    ],
    "required_conditions": [
      "profiling 显示瓶颈在 aiv_vec 且该域指令占主导（本 run：arg_max case5 int64 T1 vec 460.09us / kernel 521.546us = 88%；mish_ fp16 case1 aiv_vec 13.047us / TaskDur 16.085us = 81%，case10 16.032/19.035 = 84%）",
      "存在可验证的便宜等价域：int64 可拆 hi/lo 到 int32 域（要求 Reg::DeInterleave 等 b32 交织原语可用），fp16 可 widen 到 fp32 域复用已验证的 fp32 向量链",
      "便宜域有现成的、已验证的实现可镜像（本 run：mish_ fp16 直接镜像已上线的 bf16 widen/compute/narrow 模式）",
      "每指令成本可交叉标定：用两代实现的指令数变化反推单指令成本恒定，以排除依赖链/加载瓶颈"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-09-10",
  "evidence": [
    {
      "after_us": 97.115,
      "before_us": 155.489,
      "mechanism": "int32-domain-hilo-lexicographic-deinterleave-scan",
      "operator": "arg_max",
      "operator_class": "sort-select",
      "pairs": 10,
      "pair_ratio_range": "1.5969-1.6062",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "speedup": 1.6011,
      "status": "accepted"
    },
    {
      "after_us": 19.508,
      "before_us": 36.599,
      "mechanism": "simt-to-simd-revectorization",
      "operator": "mish_",
      "operator_class": "elementwise",
      "pairs": 10,
      "pair_ratio_range": ">1.0 on all 3 perf cases",
      "precision": "20/20 PASS",
      "run_id": "<run-id>",
      "speedup": 1.8761,
      "status": "accepted"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "b64-vector-op-penalty",
      "low-precision-scalar-transcendental-chain",
      "vec-instruction-issue-bound"
    ],
    "pattern": "costly-domain-to-cheap-domain-migration",
    "structure": [
      "hi-lo-deinterleave-int32-domain",
      "fp16-widen-to-fp32-simd-chain",
      "original-domain-kept-as-fallback-arm",
      "signed-key-lexicographic-encoding"
    ]
  },
  "generality": "op_class",
  "id": "DOM-MIGRATION-CHEAP-PIPE",
  "implementation_steps": [
    "先做每指令成本交叉标定：用两代实现的指令数变化反推单指令周期（本 run arg_max 两代 16→5 条/块，vec 时间同步下降，反推 ~9.5-9.7 cycle/条恒定；对照 b32 路径 ~0.6 cycle/条），确认瓶颈是发射分解而非依赖链",
    "int64→int32 路径：LoadAlign<int32_t> 取交织视图 + Reg::DeInterleave 得稠密 lo/hi + 偏移二进制键（hi 原码有符号比较，klo=lo+0x80000000）+ Compare/And/Or + Select + Arange + 切片末两段 Reduce 合并",
    "int64 标量重建层改 int32 视图槽布局（word0=hi / word8=lo / word16=idx / word24=0），word0 直落 maxKhi、loVal=maxKlo+flip 自反还原",
    "fp16→fp32 路径：LoadAlign<half, DIST_UNPACK_B16> widen + Cast F16->F32 → 复用已验证的 fp32 向量链（Exp/Adds/Ln/Compares/Select/Muls/Div）→ Cast F32->F16（CAST_RINT=RNE, SAT）+ StoreAlign<DIST_PACK_B32>",
    "低精度路径同时把 SIMT 逐线程标量启动改为 TQue 同步的同步 SIMD 调用，去掉 per-tile SetFlag/WaitFlag HardEvent 对",
    "原域实现逐字保留为回退臂（gcd/mish_ 的 I64、bf16 与 dormant SIMT 参考路径零改动）"
  ],
  "intent": "当 aiv_vec 饱和且瓶颈集中在某个「后端罚分域」时，把计算迁移到便宜等价域。两类已验证的罚分域：b64 向量指令被后端均匀软件分解发射（~9.7 cycle/条 vs b32 ~0.6），以及低精度逐线程标量超越函数链（~30+ 标量 op/元素 at 256 threads/tile）。迁移到 int32 向量域或 fp32 加宽向量域后，指令数的等价缩减直接按比例转化为 wall 收益。",
  "mechanism": "两类域迁移。(a) int64→int32 hi/lo 字典序拆分：int64 T1 切片扫描用 2×LoadAlign<int32_t> 交织视图 + Reg::DeInterleave 拆出稠密 lo/hi，构造偏移二进制字典序键（hi 原码有符号比较 + klo=lo+0x80000000 翻转后比较），以 3 Compare/And/Or + 3 Select 在 int32 域完成等价扫描，切片末两段 Reduce 合并，标量层改 int32 视图四槽重建。(b) fp16 SIMT→SIMD 重向量化：把逐线程标量链（__half2float + expf/logf/tanhf + __float2half_rn，~30+ 标量 op/元素）换成 widen 到 fp32 的 SIMD 向量核（LoadAlign<half,DIST_UNPACK_B16> + Cast → 13 条 v-insn 的 fp32 链 → Cast RNE + StoreAlign<DIST_PACK_B32>），并把 SIMT 异步启动改为 TQue 同步调用，去掉 per-tile HardEvent 对。两者的共同点是把计算从罚分严重的域搬到便宜域，且原域实现逐字保留为回退臂。",
  "name": "数值域迁移：从后端罚分域搬到便宜向量域（int64→int32 hi/lo 拆分 / fp16→fp32 加宽 SIMD）",
  "operator_class": "sort-select",
  "operator_scope": "aiv_vec 饱和且瓶颈集中于 b64 向量指令或低精度逐线程标量超越函数链的算子，存在可验证的便宜等价域（int32 向量域 / fp32 加宽向量域）与可镜像的现成实现",
  "principle": "同一后端对不同域的指令成本差异远大于直觉：ascend950 上 b64 向量指令被均匀软件分解发射，实测 ~9.7 cycle/条，而 b32 仅 ~0.6 cycle/条——16 倍的固定罚分。低精度路径把超越函数放在逐线程标量链上，每元素 ~30+ 标量 op，同样远超向量域。因此当 aiv_vec 饱和且时间集中在罚分域时，把计算等价地搬到便宜域，指令数缩减就近似线性地转化为 wall 收益。判定前提是先用「每指令成本恒定性」交叉标定排除依赖链/加载瓶颈——否则换域只是换了个瓶颈。语义等价靠原域实现逐字保留为回退臂 + 门控派发来保证。",
  "related_anti_patterns": [],
  "risks": [
    "键编码易错：本 run arg_max round_001 把无符号翻转误放在 hi（应只翻 lo），导致混合符号 4096/4096 行索引错；修正后 20/20 通过。全零并列的 case16 对该错误不可见，说明测试集覆盖需含混合符号样本",
    "Reg::DeInterleave 的 dst0=偶 lane 语义须经失败签名分析 + 精度双证，不可按文档想当然",
    "域迁移会改变 kernel 二进制体积（新增回退臂），需确认未触碰域无副作用回退",
    "低精度升维后若丢失原精确分支护栏（如 x<=-7），会在边界 case 上静默失精度"
  ],
  "slug": "numeric-domain-migration",
  "summary": "把计算从 ascend950 后端罚分严重的域搬到便宜向量域，两类已验证迁移：(a) int64→int32 hi/lo 字典序拆分（arg_max，Reg::DeInterleave 拆稠密 lo/hi + 偏移二进制键 + 3 Compare/And/Or + 3 Select，标量层改 int32 视图四槽），case5 4.094x、kernel_geomean 155.489→97.115us（1.6011x）；(b) fp16 SIMT→SIMD 重向量化（mish_，widen 到 fp32 SIMD 链 + RNE narrow，去 per-tile HardEvent 对），case1 2.36x / case10 2.80x、kernel_geomean 36.599→19.508us（1.8761x）。两者精度均 20/20，fp32/bf16/I64 等对照路径平坦。",
  "verification": {
    "correctness": [
      "arg_max：编译 0 修复、精度修复 1 次（round_001 键编码翻转位错误 → round_002 修正），20/20 PASS；失败签名分析（case16 全零并列过 + case5 混合符号全行大偏差）同时排除 vdintlv lane 语义错误",
      "mish_：20/20 PASS，fp16 护栏下 -7 精确分支护栏保持；fp32 对照 160.420→160.508us 平坦（证伪收益外溢）"
    ],
    "performance": [
      "arg_max：形式化 10 对 ABBA 平衡交替配对全对正向（pair ratio 1.5969-1.6062，无一反向）；case5 4.094x（521.576→127.345us，vec 460→55us）；kernel_geomean 155.489→97.115us（1.6011x）；case1/case10 零扰动",
      "mish_：形式化 10 对配对，三个 perf case 逐对 ratio 全 >1.0；case1 16.007→6.780us（2.36x）、case10 19.092→6.822us（2.80x）；fp16 aiv_vec 管道整体 13.0/16.1us → ~3.3us；kernel_geomean 36.599→19.508us（1.8761x）",
      "成本量化：arg_max 两代实现交叉标定 b64 ~9.5-9.7 cycle/条 vs b32 ~0.6 cycle/条（16 倍）；mish_ fp16 从 ~30+ 标量 op/元素降到 13 v-insn/repeat"
    ],
    "rollback_signals": [
      "键编码或 lane 语义错误导致混合符号/并列样本索引错（须含此类样本的精度集）",
      "每指令成本标定显示瓶颈非发射分解（换域无效）",
      "未触碰域（I64 / bf16 / fp32 对照臂）出现超出噪声的回退",
      "升维/降维往返引入超出护栏的误差（低精度尤其注意）"
    ]
  }
}
-->

# 性能优化策略：数值域迁移：从后端罚分域搬到便宜向量域（int64→int32 hi/lo 拆分 / fp16→fp32 加宽 SIMD）

把计算从 ascend950 后端罚分严重的域搬到便宜向量域，两类已验证迁移：(a) int64→int32 hi/lo 字典序拆分（arg_max，Reg::DeInterleave 拆稠密 lo/hi + 偏移二进制键 + 3 Compare/And/Or + 3 Select，标量层改 int32 视图四槽），case5 4.094x、kernel_geomean 155.489→97.115us（1.6011x）；(b) fp16 SIMT→SIMD 重向量化（mish_，widen 到 fp32 SIMD 链 + RNE narrow，去 per-tile HardEvent 对），case1 2.36x / case10 2.80x、kernel_geomean 36.599→19.508us（1.8761x）。两者精度均 20/20。

## 1. 原理

同一后端对不同域的指令成本差异远大于直觉：ascend950 上 b64 向量指令被均匀软件分解发射，实测 ~9.7 cycle/条，而 b32 仅 ~0.6 cycle/条——16 倍的固定罚分。低精度路径把超越函数放在逐线程标量链上，每元素 ~30+ 标量 op，同样远超向量域。因此当 aiv_vec 饱和且时间集中在罚分域时，把计算等价地搬到便宜域，指令数缩减就近似线性地转化为 wall 收益。判定前提是先用「每指令成本恒定性」交叉标定排除依赖链/加载瓶颈——否则换域只是换了个瓶颈。语义等价靠原域实现逐字保留为回退臂 + 门控派发来保证。

实现机制：两类域迁移。(a) int64→int32 hi/lo 字典序拆分：int64 T1 切片扫描用 2×LoadAlign<int32_t> 交织视图 + Reg::DeInterleave 拆出稠密 lo/hi，构造偏移二进制字典序键（hi 原码有符号比较 + klo=lo+0x80000000 翻转后比较），以 3 Compare/And/Or + 3 Select 在 int32 域完成等价扫描，切片末两段 Reduce 合并，标量层改 int32 视图四槽重建。(b) fp16 SIMT→SIMD 重向量化：把逐线程标量链（__half2float + expf/logf/tanhf + __float2half_rn，~30+ 标量 op/元素）换成 widen 到 fp32 的 SIMD 向量核（LoadAlign<half,DIST_UNPACK_B16> + Cast → 13 条 v-insn 的 fp32 链 → Cast RNE + StoreAlign<DIST_PACK_B32>），并把 SIMT 异步启动改为 TQue 同步调用，去掉 per-tile HardEvent 对。两者的共同点是把计算从罚分严重的域搬到便宜域，且原域实现逐字保留为回退臂。

## 2. 性能问题模式

- 优化目标：当 aiv_vec 饱和且瓶颈集中在某个「后端罚分域」时，把计算迁移到便宜等价域。两类已验证的罚分域：b64 向量指令被后端均匀软件分解发射（~9.7 cycle/条 vs b32 ~0.6），以及低精度逐线程标量超越函数链（~30+ 标量 op/元素 at 256 threads/tile）。迁移到 int32 向量域或 fp32 加宽向量域后，指令数的等价缩减直接按比例转化为 wall 收益
- 适用数据流：aiv_vec 饱和且瓶颈集中于 b64 向量指令或低精度逐线程标量超越函数链的算子，存在可验证的便宜等价域（int32 向量域 / fp32 加宽向量域）与可镜像的现成实现
- Feature signature：`{"bottleneck": ["b64-vector-op-penalty", "low-precision-scalar-transcendental-chain", "vec-instruction-issue-bound"], "pattern": "costly-domain-to-cheap-domain-migration", "structure": ["hi-lo-deinterleave-int32-domain", "fp16-widen-to-fp32-simd-chain", "original-domain-kept-as-fallback-arm", "signed-key-lexicographic-encoding"]}`

## 3. 正确性红线

- 键编码易错：本 run arg_max round_001 把无符号翻转误放在 hi（应只翻 lo），导致混合符号 4096/4096 行索引错；修正后 20/20 通过。全零并列的 case16 对该错误不可见，说明测试集覆盖需含混合符号样本
- Reg::DeInterleave 的 dst0=偶 lane 语义须经失败签名分析 + 精度双证，不可按文档想当然
- 域迁移会改变 kernel 二进制体积（新增回退臂），需确认未触碰域无副作用回退
- 低精度升维后若丢失原精确分支护栏（如 x<=-7），会在边界 case 上静默失精度

资源与硬件约束：

- 域迁移后的语义必须与 golden 位级或护栏内等价：int64 走 hi/lo 拆分的字典序键编码，fp16 走 widen→fp32 向量链→RNE narrow 往返
- int64→int32 拆分时键编码须精确：hi 用原码有符号比较（正数 hi>=0 / 负数 hi<=-1 天然保序，不翻转），lo 经 klo=lo+0x80000000 翻转后比较有符号序（与无符号序等价）
- 低精度路径迁移后须保留原有的精确分支护栏（如 fp32 域上的 x<=-7 精确分支），不可因升维而丢失分支语义
- 两条域迁移路径都必须显式保留原域实现为回退臂，按门控派发，语义按位不变

## 4. 泛化条件

- 策略作用域：op_class：sort-select

适用：

- profiling 显示瓶颈在 aiv_vec 且该域指令占主导（本 run：arg_max case5 int64 T1 vec 460.09us / kernel 521.546us = 88%；mish_ fp16 case1 aiv_vec 13.047us / TaskDur 16.085us = 81%，case10 16.032/19.035 = 84%）
- 存在可验证的便宜等价域：int64 可拆 hi/lo 到 int32 域（要求 Reg::DeInterleave 等 b32 交织原语可用），fp16 可 widen 到 fp32 域复用已验证的 fp32 向量链
- 便宜域有现成的、已验证的实现可镜像（本 run：mish_ fp16 直接镜像已上线的 bf16 widen/compute/narrow 模式）
- 每指令成本可交叉标定：用两代实现的指令数变化反推单指令成本恒定，以排除依赖链/加载瓶颈

不适用：

- 目标域本身已是便宜域时不适用（如计算本就在 int32/fp32 向量域）
- 宽类型指令不被后端软件分解的硬件上收益不成立：本机制的 16 倍罚分（~9.7 vs ~0.6 cycle/条）是 ascend950/dav 后端的具体事实，换硬件需重新标定
- 低精度标量链本身已足够短（每元素个位数标量 op）时，升维 SIMD 化的收益不足以覆盖 widen/narrow 两次 cast
- b64 罚分若实为依赖链或加载瓶颈而非发射分解，则换域无效——须先用每指令成本恒定性交叉标定（见下）排除

## 5. 实施步骤

1. 先做每指令成本交叉标定：用两代实现的指令数变化反推单指令周期（本 run arg_max 两代 16→5 条/块，vec 时间同步下降，反推 ~9.5-9.7 cycle/条恒定；对照 b32 路径 ~0.6 cycle/条），确认瓶颈是发射分解而非依赖链
2. int64→int32 路径：LoadAlign<int32_t> 取交织视图 + Reg::DeInterleave 得稠密 lo/hi + 偏移二进制键（hi 原码有符号比较，klo=lo+0x80000000）+ Compare/And/Or + Select + Arange + 切片末两段 Reduce 合并
3. int64 标量重建层改 int32 视图槽布局（word0=hi / word8=lo / word16=idx / word24=0），word0 直落 maxKhi、loVal=maxKlo+flip 自反还原
4. fp16→fp32 路径：LoadAlign<half, DIST_UNPACK_B16> widen + Cast F16->F32 → 复用已验证的 fp32 向量链（Exp/Adds/Ln/Compares/Select/Muls/Div）→ Cast F32->F16（CAST_RINT=RNE, SAT）+ StoreAlign<DIST_PACK_B32>
5. 低精度路径同时把 SIMT 逐线程标量启动改为 TQue 同步的同步 SIMD 调用，去掉 per-tile SetFlag/WaitFlag HardEvent 对
6. 原域实现逐字保留为回退臂（gcd/mish_ 的 I64、bf16 与 dormant SIMT 参考路径零改动）

## 6. LLM 前置问题

- 目标实现是否满足：profiling 显示瓶颈在 aiv_vec 且该域指令占主导（本 run：arg_max case5 int64 T1 vec 460.09us / kernel 521.546us = 88%；mish_ fp16 case1 aiv_vec 13.047us / TaskDur 16.085us = 81%，case10 16.032/19.035 = 84%）？
- 目标实现是否满足：存在可验证的便宜等价域：int64 可拆 hi/lo 到 int32 域（要求 Reg::DeInterleave 等 b32 交织原语可用），fp16 可 widen 到 fp32 域复用已验证的 fp32 向量链？
- 目标实现是否满足：便宜域有现成的、已验证的实现可镜像（本 run：mish_ fp16 直接镜像已上线的 bf16 widen/compute/narrow 模式）？
- 目标实现是否满足：每指令成本可交叉标定：用两代实现的指令数变化反推单指令成本恒定，以排除依赖链/加载瓶颈？
- 是否命中排除条件：目标域本身已是便宜域时不适用（如计算本就在 int32/fp32 向量域）？

## 7. 验收标准

正确性：

- arg_max：编译 0 修复、精度修复 1 次（round_001 键编码翻转位错误 → round_002 修正），20/20 PASS；失败签名分析（case16 全零并列过 + case5 混合符号全行大偏差）同时排除 vdintlv lane 语义错误
- mish_：20/20 PASS，fp16 护栏下 -7 精确分支护栏保持；fp32 对照 160.420→160.508us 平坦（证伪收益外溢）

性能：

- arg_max：形式化 10 对 ABBA 平衡交替配对全对正向（pair ratio 1.5969-1.6062，无一反向）；case5 4.094x（521.576→127.345us，vec 460→55us）；kernel_geomean 155.489→97.115us（1.6011x）；case1/case10 零扰动
- mish_：形式化 10 对配对，三个 perf case 逐对 ratio 全 >1.0；case1 16.007→6.780us（2.36x）、case10 19.092→6.822us（2.80x）；fp16 aiv_vec 管道整体 13.0/16.1us → ~3.3us；kernel_geomean 36.599→19.508us（1.8761x）
- 成本量化：arg_max 两代实现交叉标定 b64 ~9.5-9.7 cycle/条 vs b32 ~0.6 cycle/条（16 倍）；mish_ fp16 从 ~30+ 标量 op/元素降到 13 v-insn/repeat

回滚信号：

- 键编码或 lane 语义错误导致混合符号/并列样本索引错（须含此类样本的精度集）
- 每指令成本标定显示瓶颈非发射分解（换域无效）
- 未触碰域（I64 / bf16 / fp32 对照臂）出现超出噪声的回退
- 升维/降维往返引入超出护栏的误差（低精度尤其注意）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- loop_20260907_170122-free-003（operator=arg_max, mechanism=int32-domain-hilo-lexicographic-deinterleave-scan, status=accepted, speedup=1.6011, 155.489→97.115us, 10 对 ABBA）
- loop_20260907_170122-free-002（operator=mish_, mechanism=simt-to-simd-revectorization, status=accepted, speedup=1.8761, 36.599→19.508us, 10 对配对）

## 检索卡（短卡）

动作：把计算从后端罚分域搬到便宜向量域：int64 走 hi/lo 拆分的 int32 字典序键，fp16 走 fp32 向量链→RNE narrow。
适用：profiling 显示瓶颈在 aiv_vec 且该域指令占主导、存在可验证的便宜等价域与可镜像的现成实现、每指令成本可交叉标定。
限制：键编码须精确（hi 用原码有符号比较，只翻 lo 的 klo=lo+0x80000000）；升维后须保留精确分支护栏。
范围：aiv_vec 饱和且瓶颈集中于 b64 指令或低精度标量超越链的算子。
检索词：Reg::DeInterleave、LoadAlign、DIST_UNPACK_B16、DIST_PACK_B32、klo 翻转
机会：b64 向量指令被后端软件分解（~9.7 vs b32 ~0.6 cycle/条），超越链每元素 30+ 标量 op。
代价：新增回退臂改变 kernel 体积；精度集须含混合符号样本。

---
type: Optimization
title: 有序索引链与独占owner的SIMT累加
description: 为同目的索引建稳定first/next链，每(o,d,p)由首命中owner沿j升序SIMT取数，FP32累加后一次转换写回。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/ordered-index-chain-simt-accumulation.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "ORDERED-INDEX-CHAIN-SIMT-ACCUMULATION",
  "slug": "ordered-index-chain-simt-accumulation",
  "created": "2026-10-14",
  "classification": "validated_strategy",
  "operator_class": "scatter-update",
  "phase": [
    "design",
    "tuning"
  ],
  "feature_signature": {
    "pattern": "stable-first-next-chain-exclusive-owner",
    "bottleneck": [
      "per-hit-tiny-dma",
      "dense-destination-scan"
    ],
    "structure": [
      "index-only-preprocess",
      "j-ascending",
      "SIMT-direct-GM",
      "FP32-register-accumulator",
      "metadata-fallback"
    ]
  },
  "related_strategy_ids": [
    "destination-owned-ordered-fp32-ub-accumulation",
    "gm-fp32-workspace-column-serial-rmw",
    "simd-simt-gather-to-vector-math",
    "simt-direct-gm-dtype-aware-gate",
    "launch-core-count-convergence"
  ],
  "name": "有序索引链与独占owner的SIMT累加",
  "mechanism": "相同目的的j构成升序first/next链；首次j为每(o,d,p)唯一owner，SIMT沿链以FP32 acc按原顺序乘加，最后一次转换写self。",
  "operator_scope": "短索引的浮点散射更新（index_add / scatter_add 及同类）：索引预处理 + 独占 owner 的 SIMT 直接 GM 取数 + FP32 累加",
  "intent": "把短索引的逐命中微 DMA/同步、D 值域密集扫描或逐更新 GM 读改写，改为索引预处理、唯一 owner 直接 GM 取数与 FP32 累加后一次写回。",
  "implementation_steps": [
    "以 self[O,D,I]、source[O,L,I] 为例，每 j 写 first[j]（同目的首次）与 next[j]（其后最近的同目的 j，末尾终止）；简单 prep 最坏 O(L²)、链 scratch O(L)，不依赖 D",
    "compute 枚举 O*L*I，非 first 项跳过；首次 j 为每 (o,index[j],p) 唯一 owner，从 self 初始化 FP32 acc",
    "沿严格升 j 的 next 链读取 source 并按契约 alpha 乘加；链结束一次转换写 self[(o*D+d)*I+p]；各 owner 目的不交，不用 atomic/跨核重组",
    "两 kernel 在同一当前 stream 顺序提交；prep 完整写链后 compute 才消费；改变 stream/消费域/缓存需重新证明可见性",
    "每调用独立分配/管理 scratch，寿命覆盖全部异步消费者；D-head 变体（head[d]+next 链）仅在受限域保留"
  ],
  "risks": [
    "简单 prep 最坏 O(L²)、D-head 变体 prep O(DL)；长 L/深重复链或启动开销主导时回退",
    "FP32 acc 仅在原契约允许时合法；alpha/乘加/最终 cast 舍入须与原路径一致，不能重排重复 index、忽略 j 或用低精度 atomic 换速度",
    "source/index 与 self 写区重叠时 owner 独占 ≠ 未读输入安全，须证明读先于写或用契约允许的暂时暂存并计入成本",
    "布局/别名/寿命未证明、宽 inner/稀疏域、L≥D 不代表真实密度，不得全 dtype 套用",
    "广域替换出现过退化；受限实现仅 FP16、I=1、中等 D、L 相对 D 足够大的域保留"
  ],
  "verification": {
    "correctness": [
      "覆盖重复/唯一 index、浮点与索引宽度、alpha/特殊值、未命中原值、负 dim、布局/别名、尾 owner、scratch 边界、新地址/stream；主 guard、D-head/J 链切换与 fallback 两侧都验证",
      "验证 NaN/Inf、有符号零及相消输入；原容差、equal_nan 与 bit-exact 分名；未命中值保持原值及接口位型",
      "int32/int64 索引宽度与链 ID 宽度分开，int32 链项要求 L 与终止值可表示；乘加前提升足够宽位，越域回正确宽位/generic"
    ],
    "performance": [
      "受限实现与配对实测支持分组/载体/数据流组合，没有各部分独立收益；扩展参数与资源域另验，不泛称 bit-exact",
      "比较须合计 prep+compute、scratch 与启动工作；同轮正反序测完整 op 至完成同步、event 与 device，profiler 计入两 kernel/辅助及逐组回退",
      "prep 与 compute 工作不同，分别调 thread/grid；计入 prep，不把没有同上下文 stage 配对的跨次 profiler 数字当独立因果"
    ],
    "rollback_signals": [
      "用 atomic/重排/跨核局部和替代稳定重复索引累加即回退",
      "布局/别名/寿命未证明、长 L/深链、启动开销主导时保留 fallback",
      "未验证扩展域保持条件性结论；精度/覆盖失败或稳定退化就修复、收缩或回退"
    ]
  },
  "principle": "把“逐命中微 DMA / 密集目的扫描 / 逐更新 GM 读写”改为“索引预处理 + 唯一 owner 直接 GM 取数 + FP32 累加后一次写回”的稳定升序链；收益以同轮实测为准，不拆独立收益。",
  "validation_scope": "已有受限实现与配对实测支持分组/载体/数据流组合，没有各部分独立收益。扩展参数与资源域须另验，文档不构成新增设备验证。",
  "applicability": {
    "required_conditions": [
      "合法索引可建立唯一目的owner，FP32链和稳定j顺序符合接口",
      "别名、布局、链ID/offset宽度、scratch及异步寿命安全"
    ],
    "excluded_conditions": [
      "用atomic/重排/跨核局部和替代稳定重复索引累加",
      "长L/深重复链或启动开销主导",
      "布局/别名/寿命未证明"
    ],
    "constraints": [
      "简单prep最坏O(L^2)，J链scratch O(L)，不能称线性prep",
      "D-head变体prep O(D*L)，scratch L+D，需严格守卫",
      "参考guard和thread/grid不是通用最优值"
    ]
  }
}
-->
# 性能优化策略：有序索引链与独占owner的SIMT累加

将短索引的逐命中微DMA/同步、D值域密集扫描或逐更新GM读改写，改为索引预处理、唯一owner直接GM取数与FP32累加后一次写回。index_add、scatter_add及同类浮点更新仅在接口、合法索引、数值链和顺序契约相符时采用；已有受限组合实现支持，不拆分独立收益或泛称bit-exact。

## first/next链与唯一owner

以连续self[O,D,I]、source[O,L,I]为例。每j写first[j]（相同目的首次出现）和next[j]（其后最近的同目的j，末尾终止）。简单构造扫描j前后索引，**最坏O(L²)**；next[L]+first[L]是2L链项，即**O(L) scratch**。构造和存储不依赖D，不提前计算数值输出。

compute枚举O*L*I，非first项跳过。首次j为每(o,index[j],p)唯一owner，从self初始化FP32 acc，沿严格升j的next链读取source[(o*L+j)*I+p]，按契约做alpha乘加；链结束后一次转换写self[(o*D+d)*I+p]。各owner目的不交，同目的重复index由同一owner完成，不用atomic或跨核数学重组；未命中self不写。

避免D大小的桶/前缀与逐命中目的往返是可能收益；代价是O(L²)比较、非first跳过、两launch、scratch与依赖。长重复链串行、distinct目的少时并行不足；不依D不代表任意稀疏/密集形状都快。

## 精度、接口与别名

- FP32 acc只有原契约规定/允许该链才合法。alpha转换、先乘后加或融合乘加、最终cast/舍入与原路径一致；低精度source按契约拓宽，owner直到链结束才降回，不中间舍回。不能重排重复index、忽略j或用低精度atomic换速度。
- 验证NaN/Inf、有符号零及相消输入，原容差、数值equal_nan和bit-exact分名。未命中值保持原值及接口要求位型，原地接口返回同对象/存储；其它接口保持自身初值/别名要求。
- 核对rank、dim及负dim、source轴大小、L、index值域/dtype和offset乘积。int32/int64索引宽度与链ID宽度分开；int32链项要求L和终止值可表示。地址乘加前提升到足够宽位，越域回正确宽位/generic路径。
- 连续视图公式不适用于未经证明的非连续布局；只有实际stride和尾部安全才进快路，否则按接口回generic或拒绝明确不支持的布局。L=0/空输入遵守返回和副作用；L=1可保留既有精确快路。
- source/index与self写区重叠时，owner独占不等于未读输入安全。证明全部读先于潜在覆盖，或用契约允许的独立暂存并计入成本；做不到回原支持路径。不得静默缩小合法别名域。

## 两kernel依赖与资源

prep完整写链后compute才消费，两kernel在同一当前stream顺序提交并遵守运行时依赖。改变stream、消费域或缓存路径需重新证明可见性，不照搬跨核fence/SyncAll，只有确需且验证过才加同步。

每调用独立分配或安全管理scratch，不缓存链/输出、不跨调用复用未验证内容。scratch及输入寿命覆盖全部异步消费者，核对allocator/stream绑定、释放复用、多stream和fresh地址。完整调用必须包含scratch管理、两个kernel和必要辅助任务。

thread/grid/launch_bounds一致，grid-stride和尾保护覆盖全部索引/owner。实际查询AIV、线程/寄存器/栈及容量限制，不能套固定机器值；预算、地址或分配无法满足就回正确路径。

## 目的head表变体与负边界

按d建立head[d]及同一next链：每d升j扫描，compute按连续O*D*I目的offset枚举，空head跳过。简单prep最坏**O(DL)**，scratch为**next[L]+head[D]**。目的读写组织可能更好，但D表扫描与未命中线程增加；地址连续不能直接证明带宽收益。

广域替换出现过退化；受限实现仅在FP16、I=1、中等D、L相对D足够大的域保留，其他dtype/宽inner/稀疏域回J链。参考守卫FP16且I=1、1024≤D≤4096、L≥D，并满足主链域。它是实测范围而非通用阈值，**L≥D不等于真实密度**，不能全dtype套用或拆分每个谓词的独立贡献。

比较必须合计prep+compute、scratch和启动工作；D-head是稳定链机制的变体/负边界，不另建连续目标必快策略。

## guard与按阶段配置

参考主链域1<L≤4096且(I=1或O≥64)，只代表受限实现。按L/D/O/I、dtype、重复分布、资源和既有快路建立metadata guard，不按评测编号/缓存输入值分派。超长L、长链、tiny-work固定成本或合法性条件不满足时保留fallback。

prep与compute工作不同，分别调thread/grid。prep线程数同时影响ceil(L/threads)派生grid与活跃核数，属于耦合配置；不能拆独立贡献或称64/256通用最佳。计入prep，不把没有同上下文stage配对的跨次profiler数字当独立因果证据。

## 关系与验收

UB目的块驻留卡是source批MTE2与目的UB数据流；GM列独占卡的中间acc在GM；SIMT gather到SIMD数学卡是取数交接。这里是索引scratch、SIMT直接GM和owner内acc，关联这些机制而不重复或替代其作用域。

覆盖重复/唯一index、浮点及索引宽度、alpha/特殊值、未命中原值、负dim、布局/别名、尾owner、scratch边界、新地址/stream；主guard、D-head/J链切换与fallback两侧都验证。源码/成功编译/实际load绑定后同轮正反序测完整op至完成同步、event和device，profiler计入两kernel/辅助工作、prep/compute及逐组回退；事件仪器不冒充独立wall。未验证扩展域保持条件性结论，精度/覆盖失败或稳定退化就修复、收缩或回退。

## 检索卡（短卡）

动作：为同目的索引建稳定first/next链，每(o,d,p)由首命中owner沿j升序SIMT取数，FP32累加后一次转换写回。
适用：短索引、独占目的、别名与布局安全，稳定j/FP32链符合接口。
限制：prep最坏O(L²)，scratch O(L)；长L/深链、位宽/寿命不符或负收益回退。
范围：index_add/scatter_add等契约匹配的浮点索引更新。
检索词：SIMT、first/next、唯一owner、j升序、FP32 acc、直接GM、head表
机会：逐命中微DMA/同步或稀疏大D密集桶扫描主导。
代价：两kernel与scratch；D-head需O(DL)扫描，仅限验证域，空目的枚举可退化。

---
type: Optimization
title: 小inner目的块驻留与有序FP32累加
description: 将小inner的逐命中微搬运改为目的块驻留、source批搬和有序片上累加；依据精度链、别名、UB总预算与重复扫描成本分派，不承诺通用阈值或独立收益百分比。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/destination-owned-ordered-fp32-ub-accumulation.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "DESTINATION-OWNED-ORDERED-FP32-UB-ACCUMULATION",
  "slug": "destination-owned-ordered-fp32-ub-accumulation",
  "created": "2026-10-14",
  "classification": "validated_strategy",
  "operator_class": "scatter-update",
  "phase": [
    "design",
    "tuning"
  ],
  "feature_signature": {
    "bottleneck": [
      "tiny-dma-per-update",
      "per-update-gm-rmw",
      "scalar-source-gm-read"
    ],
    "pattern": "destination-owned-ordered-ub-scatter-accumulate",
    "structure": [
      "exclusive-output-tile",
      "fp32-ub-accumulator",
      "source-index-bulk-mte2",
      "j-ascending",
      "metadata-gated-fallback"
    ]
  },
  "related_strategy_ids": [
    "row-split-ub-accumulator-workspace",
    "gm-fp32-workspace-column-serial-rmw",
    "index-scalar-bulk-mte2-tbuf-gated-independent-ub-budget",
    "low-precision-atomic-accumulation-precision-loss",
    "multirow-strided-datacopy-tiny-row"
  ],
  "name": "小inner目的块驻留与有序FP32累加",
  "mechanism": "每核独占连续目的块，读入原值并将FP32累加器驻留UB；索引和source分段批量搬入UB，按原j顺序更新本块。完整FP32链契约下跨source段保留acc，全部更新结束后一次转换并写回。",
  "operator_scope": "小 inner 的浮点散射更新（index_add / scatter_add 及同类）：目的块驻留 UB + source/index 分段批搬 + 按 j 原序 FP32 累加",
  "intent": "单一优化点：把小 inner 路径逐命中的微小 GM 搬运、GM 读改写与 source 标量 GM 读，改为每核独占目的块、FP32 累加器驻留 UB、source/index 分段批搬、按 j 原序片上累加；在要求全程 FP32 的契约下 acc 跨输入段存活、最后一次转换写回。",
  "implementation_steps": [
    "本核独占目的块 (o, d0:d1, inner 区间)，目的块读入 UB 并保留未命中元素所需的原值/位型",
    "acc 按契约转 FP32；source/index 按有界段 MTE2 批搬入 UB 并等待可被 Scalar/Vector 安全消费",
    "按严格升序 j 遍历：命中本块的 index[j] 做 acc[index[j]-d0,p] += 按契约计算(alpha*source[j,p])，保持原 j 顺序",
    "段消费完成后才复用输入槽；全部 j 完成后按契约一次转换/合并原值，MTE3 写回",
    "每核独占输出、异步消费者完成后才复用目的槽；保留微 L/单索引、稀疏、宽 inner、超预算 fallback"
  ],
  "risks": [
    "逐更新 GM 往返换成目的块暂存 + 全 L 筛选 + 可能的 source 重复读取；大 D 稀疏命中时整块读写与筛选会浪费工作",
    "分 source 段降回再读入会额外舍入；契约要求全程 FP32、最终仅转换一次时不可用",
    "别名不安全、非连续布局、索引/offset 宽度、MTE 缓冲复用依赖未证明时不得采用",
    "预算不足或全 L 重扫 + source 重搬可能稳定慢于已有正确路径；很小 L 时分配/初始化/批搬/同步固定成本可能更高"
  ],
  "verification": {
    "correctness": [
      "覆盖重复/唯一 index、三种浮点及索引宽度、负 dim、alpha、特殊值、未命中原值、短尾、fresh 地址与适用 stream；原容差与接口副作用/返回别名先验证",
      "严格数值相等含 NaN 位置与 bit-exact 分名；要求跨段 FP32 时专门比较段边界两侧与相消序列，不放宽容差",
      "确认 fallback 实际执行；未验证扩展域标待验证，不把单 source 段证据外推"
    ],
    "performance": [
      "受限实现 + 配对实测支持目的块驻留与批量输入组织；无独立消融时保留组合归因，不虚构各项收益",
      "源码/编译对象/实际 load 绑定后，同输入完成语义正反序比较，计入 host 分派、合法暂存、全部 kernel 与辅助；完整调用至完成同步 / event / device 分列",
      "profiler 核对 kernel/批搬/辅助工作数量与耗时，分输入组报告固定成本、全 L 重扫、source 重搬、初始化与尾部"
    ],
    "rollback_signals": [
      "顺序/精度、别名、布局、地址宽度、同步或预算无法满足时先回退",
      "候选虽正确但逐组稳定回归时收缩适用域，不把小 inner 全域强制走此路径",
      "更换 SDK / 布局 / dtype / owner 切分 / 队列深度 / acc 寿命后须重验"
    ]
  },
  "principle": "把小 inner 逐命中的 GM 往返与标量取数，换成“目的块独占 + FP32 acc 驻留 UB + source/index 批搬 + j 原序累加”的片上数据流；收益以同轮实测为准，不承诺通用阈值或独立收益。",
  "summary": "将小inner的逐命中微搬运改为目的块驻留、source批搬和有序片上累加；依据精度链、别名、UB总预算与重复扫描成本分派，不承诺通用阈值或独立收益百分比。",
  "validation_scope": "目的块驻留与批量输入组织已有受限实现和配对实测支持；未经独立消融不能拆分收益。跨source段保留FP32、其它布局和参数扩展须另验，文档扩展不构成新增设备验证。",
  "applicability": {
    "required_conditions": [
      "接口允许将目的数据规约为outer/D/inner视角，目的块可由单一核全程独占",
      "浮点累加的顺序、乘加精度和最终转换可与原契约一致，合法重复索引按j原序处理",
      "目的写回不会覆盖尚未消费的source/index；必要暂存及当前stream寿命有合法实现",
      "FP32 acc、输入/输出、source/index、队列、对齐guard和预留空间共同满足实际UB预算"
    ],
    "excluded_conditions": [
      "通过跨核局部归约、重排重复索引、低精度原子或不允许的中间舍回来换取性能",
      "未证明别名安全、非连续布局映射、索引/offset宽度或MTE缓冲复用依赖",
      "预算不足或全L重复扫描与source重搬使候选稳定慢于已有正确路径"
    ],
    "constraints": [
      "inner、D、L、命中密度、tile和队列配置是需要验证的分派维度；参考阈值不是通用最优值",
      "全程FP32契约必须让acc跨source/index分段存活，分段降回只能在契约及验证明确许可时使用"
    ]
  }
}
-->
# 性能优化策略：小inner目的块驻留与有序FP32累加

把小inner路径逐命中的微小GM搬运、GM读改写和source标量GM读，改为**每核独占目的块、FP32累加器驻留UB、source/index分段批搬、按j原序片上累加**。在要求全程FP32的契约下，acc跨输入段保持存活，最后一次转换写回。该机制有受限实现与配对实测支持；参数扩展和跨段实现仍须验证，没有各组成部分的独立收益百分比或全形状性能保证。

## 1. 原理与适用对象

可将连续目的数据视为`self[outer,D,inner]`，source为`source[outer,L,inner]`，index为长度L的一维合法索引；更新语义为`self[o,index[j],p] += alpha*source[o,j,p]`。index_add、scatter_add以及同类浮点散射更新仅在**接口、索引映射、稳定顺序和数值契约相符**时适用，名字相近不能代替核验。

每核拥有不相交的`(o,目的D块,inner区间)`写集合，并在整个j遍历期间持有该集合。把连续目的块一次读入UB、建立FP32 acc；source和index按有界段用MTE2批搬，内层只访问UB并对落在本块的更新做乘加。减少的是逐更新GM往返和细碎搬运，新增的是目的块暂存、全L筛选和可能的source重复读取。

小inner只是机会信号。应确认真实瓶颈来自微DMA/事件或source标量GM读，而不是已经饱和的带宽、很长的片上标量依赖链或已有高效单索引路径。

## 2. 有序数据流与精度链

一个保持完整FP32链的组织如下；它描述合法数据流，不指定通用tile尺寸或唯一API组合。

```text
for 本核独占的目的块(o,d0:d1,inner区间):
    原dtype目的块 -> UB；保留未命中元素所需的原值/位型
    acc <- 按契约转换为FP32
    for source/index段，j起点严格升序:
        MTE2批搬对应index段和source段 -> UB
        等待数据可被Scalar/Vector安全消费
        for j in 当前段，保持原序:
            if index[j]属于本目的块:
                acc[index[j]-d0,p] += 按契约计算(alpha * source[j,p])
        等待本段消费完成，之后才能复用输入槽
    全部j完成 -> 按契约一次转换/合并原值 -> MTE3写回
    等待异步消费者完成，之后才能复用目的/输出槽
```

- 合法重复index不能排序后改变同一目的的j顺序，不能用低精度atomic或跨核局部和替代要求稳定顺序的累加。不同owner间不共享目的写地址，无需为本机制强行增加跨核归约。
- FP32 acc只有在原接口规定或允许该精度链时才合法。alpha转换、先乘后加或融合乘加、舍入方式、NaN/Inf/有符号零均与原契约对齐；更高精度也不自动等于bit-exact。其它dtype/整数/复数或不同归约语义走已支持的正确路径。
- **分source段降回再读入会额外舍入**。如果契约要求全部更新都在FP32完成、最终仅转换一次，acc必须跨所有source段和index批保留到结束。只能在契约与验证明确许可时采用分段舍回，不能把它描述为全程一次转换或不改变数值路径。
- 单source段实现的精度证据不证明跨段实现。可限定单段适用域，或实现跨段acc寿命；后者可能要求目的块外层循环，从而增加source重搬，须计量而非视为免费修复。

## 3. 接口、别名与未命中值

- 验证rank、dim并按接口归一化负dim，核对source非索引轴大小、L与index长度、索引dtype、合法值域及地址乘积。int32/int64保持合法接口；乘加前提升到足够宽的类型，不无证明窄化offset。
- 连续视图公式不能直接用于任意非连续输入。非连续布局只有在实际stride映射、块连续性和尾部处理被证明时进入快速路；否则回正确generic路径，或按原接口的明确限制报错。空输入及L=0遵守原返回/副作用语义。
- self/source/index的存储重叠须先证明写回不会破坏后续未读输入，核间写集合不交不等于输入别名安全。合法但有覆盖风险时使用契约允许的安全暂存并计入完整调用；不能实现时回原支持路径。接口明确不支持的别名才按契约拒绝，不自行缩小合法域。
- 原地接口继续写回self并返回原对象/存储；out-of-place接口按自己的别名要求处理。暂存不能对外暴露中间结果。
- 只写命中元素时保证覆盖完整；整块回写时未命中元素必须保留原值。若接口要求位型稳定，必须保留并合并原dtype位型，不能靠FP32转换再降回宣称NaN payload或有符号零不变。初始化acc也不得用未经允许的`+0`改变符号。

## 4. 批搬、资源与时序

连续视图的源偏移为`(o*L+j)*inner+p`，目的为`(o*D+d)*inner+p`。source段、index段和acc局部offset必须使用同一j基准。非连续或跨inner边界的块要按实际stride拆成合法连续片段，不能把逻辑长度当物理pitch。

- source/index用DataCopy/DataCopyPad等已验证MTE接口批搬；按目标SDK核对blockLen、blockCount、stride单位、字段上限、32B填充、UB行距及尾数。奇数L、短尾段、非对齐dtype/index宽度不能越界读写；mask只限制算术lane，不自动证明物理读取安全。
- UB总预算包含FP32 acc、原dtype目的/输出、source/index缓冲、命中mask或原值暂存、队列深度、对齐guard、控制暂存和编译器/SDK预留。按实际可用UB、AIV核数和InitBuffer占用求解tile，不能把已知机器或示例预算当通用上限。
- MTE2完成后Scalar/Vector才读；acc或输入消费完成后才重用槽；MTE3完成后才重用其源缓冲。使用匹配的MTE事件或已验证TQue依赖，覆盖RAW/WAR及双缓冲复用，不凭同stream提交顺序替代核内异步流水依赖。也不无依据增加PIPE_ALL、SyncAll或cache操作。
- 双缓冲只在预算与依赖都成立时使用。增加depth/扩大tile会提高占用并可能损失重叠，不能仅依据描述符数量推断收益。

## 5. 分派、成本与回退

以dtype、布局、inner、D、L、tile数量、实际资源和已有正确路径建立可复查的metadata guard，不按评测编号或缓存输入值分派。命中密度可依据已有合法信息或必要设备工作评估；不要仅为选路追加未经计量的D2H回读。

参考实现曾使用`inner<32`、acc为8192个FP32元素（32KB）、source为8192元素、index批上限4096。它们是**实现范围和调优起点，不是通用最优阈值或硬件常量**。source按元素预算切段时，单段条件需同时考虑L、inner和index批上限；超过该域就按上节处理acc精度寿命，不能保持分段舍回却声称全程FP32。

每个目的块可能筛选全部L，工作随`outer*目的块数*L`增长；跨目的块的source/index重搬也是实际代价。大D稀疏命中时整块读写与筛选会浪费工作；很小L时分配、初始化、批搬和同步固定成本可能高于原路径。保留已正确的微L/单索引、稀疏、宽inner和超预算路径，对边界两侧及组合条件实测后决定守卫。

顺序/精度、别名、布局、地址宽度、同步或预算无法满足时先回退；原路径不存在合法支持时按接口报错，不输出部分结果。候选虽正确但逐组稳定回归时收缩适用域，不把小inner全部强制走此路径。

## 6. 关联与去重

- `row-split-ub-accumulator-workspace`按输入行拆核、局部结果落workspace后合并，适合允许重组的归约并明确排除顺序敏感场景。本机制按目的块全程独占、保留j顺序，没有该跨核数学重组；两者共享UB段累加经验而非等价模板。
- `gm-fp32-workspace-column-serial-rmw`共享目的独占、j升序和FP32精度原则，但主要存储/更新在GM且使用不同载体与资源组织；本机制以UB目的块和source批搬减少细碎GM工作，不替换其大足迹作用域。
- `index-scalar-bulk-mte2-tbuf-gated-independent-ub-budget`提供输入索引预算/门控经验，驻留对象不是目的acc。`low-precision-atomic-accumulation-precision-loss`提供中间舍入负边界；`multirow-strided-datacopy-tiny-row`提供批搬与stride经验，不能自动保证本平台非对齐散射更新合法。

## 7. 验证与证据边界

已有受限机制实现与配对实测支持目的块驻留和批量输入组织；没有独立消融时保留组合归因，不给每项或完整新参数域虚构收益。该策略正文的维护不等于重新编译、精度测试或设备实测。

1. 先验证原容差及接口副作用/返回别名；严格数值相等含NaN位置与bit-exact分名。覆盖重复/唯一index、三种浮点及索引宽度、负dim、alpha、特殊值、未命中原值、短尾、fresh地址与适用stream。要求跨段FP32时专门比较段边界两侧和相消序列，不放宽容差。
2. 核对inner门、L与source/index段边界、D/tile、稀疏/密集、布局、别名和UB预算边界两侧及交叉条件；确认fallback实际执行。未验证扩展域明确标待验证，不把单段证据外推。
3. 源码、成功编译对象与实际load二进制绑定。对相同输入、完成语义和设备重复比较正反顺序，计入host分派、合法暂存、所有kernel及辅助工作，分别报告完整调用至完成同步、event与device；事件仪器工作不能冒充独立wall口径。
4. profiler核对所有kernel/批搬/必要辅助工作的数量和耗时，分输入组报告固定成本、重复全L扫描、source重搬、初始化与尾部。候选无收益或稳定退化就保留负证据并回退/收缩。
5. 更换SDK、布局、dtype、owner切分、队列深度或acc寿命后重验；同步和资源结论限于已证明范围。未做上述设备验证的变体不得声称已获全域性能或bit-exact保证。

## 检索卡（短卡）

动作：把小inner逐更新GM往返改为独占目的块FP32 acc驻留UB，source/index分段批搬并按j原序累加。
适用：目的块全程单核独占、别名与布局安全；接口要求稳定顺序且FP32链可保持。
限制：全程FP32契约须跨段保留acc并最终一次转换；全部缓冲/guard超UB预算或语义不符回退。
范围：接口与顺序契约匹配的浮点索引加法/散射更新。
检索词：index_add、scatter_add、小inner、目的块、FP32 acc、UB驻留、MTE2、j升序、source批搬
机会：小inner每命中微DMA/事件或source标量GM读主导。
代价：每目的块全L扫描、source重搬及UB占用；微L/大D稀疏域可能回退。

---
type: Optimization
title: SIMD主体的SIMT离散取数与向量数学交接：UB直交接/GM桥接
description: Preserve original math and casts; evaluate UB budget and repeated VF costs against extra GM traffic, with guarded vector and scalar fallbacks.
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.pipeline
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/simd-simt-gather-to-vector-math.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "simd-simt-gather-to-vector-math",
  "slug": "simd-simt-gather-to-vector-math",
  "created": "2026-10-13",
  "classification": "validated_strategy",
  "operator_class": "index-gather-map",
  "phase": [
    "design",
    "tuning"
  ],
  "feature_signature": {
    "bottleneck": [
      "serial-scalar-gather",
      "per-element-gm-access-cost"
    ],
    "pattern": "irregular-indexed-read-before-vector-math",
    "structure": [
      "SIMD-main-SIMT-input-phase",
      "output-GM-scratch",
      "ordered-MTE2-UB-consumer",
      "original-FP32-math-RNE",
      "bounded-shape-dtype-fallback"
    ]
  },
  "related_strategy_ids": [
    "gm-access-diet",
    "simt-write-to-mte-read-visibility",
    "simt-direct-gm-size-gate-regression",
    "simt-whole-kernel-direct-gm-carrier"
  ],
  "name": "SIMD主体的SIMT离散取数与向量数学交接：UB直交接/GM桥接",
  "mechanism": "SIMT indexed reads feed original SIMD math through verified per-core UB handoff or ordered GM scratch and MTE2; choose by correct address/lifetime ownership and measured call/traffic costs.",
  "operator_scope": "gather 后向量数学的取数阶段（index-gather → vector math）；非纯 SIMT log 全域替换",
  "intent": "把逐元素标量 GM 取数改为每核一次 SIMT VF，输出 GM 暂存后 MTE2 回 UB 执行原 FP32 数学/RNE，在不改数值路径的前提下消除串行标量取数瓶颈。",
  "implementation_steps": [
    "识别离散 gather 热点与合法 int64 索引/源偏移域，确认独占核域与队列生命周期",
    "每核一次 SIMT VF：按每个输出独立 int64 index 算源地址，写输出 GM 独占区（复用输出作暂存）",
    "VF 后逐 tile MTE2 读暂存到 UB → 原 FP32 SIMD 数学链 → 一次 CAST_RINT(RNE) 低精度回写",
    "按核内 V/S 锁与 MTE 队列生命周期保证可见性；核只消费自己的分区",
    "保留 Fast/行线程分派/队列等分域变体；N>UINT32_MAX 与不完整尾组回退标量/generic 路径"
  ],
  "risks": [
    "GM 写读、锁与队列、索引控制带来额外开销；小 shape 或缓存命中域可能无收益",
    "跨核消费者或另一 SDK 的缓存可见性未经证明不得承诺；须按工具链核验",
    "行臂 tpr 不整除 1024 时尾线程组可能与后续完整组重叠（迁移边界，source_review 未新测）",
    "N>UINT32_MAX 必须保留标量路径；超大分配域未设备实测"
  ],
  "verification": {
    "correctness": [
      "原 FP32 数学/转换契约与容差保持不变；F32 atol/rtol 1e-5、F16/BF16 1e-3",
      "20 正式例 + 105 回归通过；索引搬运不作近似数学，不宣称整个 Ln bit-exact",
      "NaN/Inf/0 维持原路径（0→-Inf）"
    ],
    "performance": [
      "E1 同轮完整 wall A269.859447/B57.075662/v1 70.041398us；gap 收窄 93.9066%，较 A 降 74.0452%（3.8529x）",
      "final 按轮 4/5、每 case 中位数再跨 case/轮 geomean：A267.855658/B57.346160/v5 57.934526us，gap 收窄 99.7205%，仍比 B 慢 1.02599%（含 Fast+lane+queue 组合）",
      "组合收益不跨轮拆分；阈值为本版参数，非通用最优"
    ],
    "rollback_signals": [
      "地址收窄/UB 写域/缓冲生命周期/跨核缓存可见性未证明",
      "approximate SIMT 数学替换了要求的原数值链",
      "尾线程组未证明且无 generic fallback"
    ]
  },
  "principle": "把『离散标量取数』与『向量数学』解耦：取数阶段换成 SIMT 并行、数学阶段保持原 SIMD 数值链，用受适用域约束的分域混合（而非全域替换）消除串行取数瓶颈；收益以同轮实测为准，不按历史倍数预测。",
  "summary": "Preserve original math and casts; evaluate UB budget and repeated VF costs against extra GM traffic, with guarded vector and scalar fallbacks.",
  "validation_scope": "Conditional mechanism; each SDK, memory layout, dtype, mapping and consumer scope requires correctness and performance verification. No all-domain performance guarantee.",
  "applicability": {
    "required_conditions": [
      "Legal per-output indices and source offsets within the interface address-width contract",
      "Exclusive producer/consumer ownership or separately proven synchronization and visibility",
      "Original SIMD math, conversions, special values and error tolerance preserved"
    ],
    "excluded_conditions": [
      "Unproved address narrowing, UB write range, buffer lifetime or cross-core cache visibility",
      "Incomplete row-thread groups without an ownership proof or generic fallback",
      "Approximate SIMT math replacing a required original numerical chain"
    ],
    "constraints": [
      "VF UB byte budget must be verified for the actual SDK/layout; no universal fixed write limit",
      "Thread/core/size thresholds are reference tuning parameters, not universal optimal gates"
    ]
  },
  "route_variants": {
    "UB_direct": "Same-core UB handoff; corrected precision can still have poor performance from repeated small VF calls; restricted by verified allocation, mapping and write domain",
    "GM_bridge": "Per-core GM scratch plus MTE2 to original SIMD math; extra write/read traffic may outweigh reduced VF calls"
  },
  "references": [
    {
      "title": "CANN9.1.X SIMD/SIMT mixed programming; official9.1.0 gather&adds source",
      "url": "https://gitcode.com/cann/asc-devkit/blob/9.1.0/examples/05_simd_simt_hybrid/00_introduction/simd_simt_gather_and_adds/gather_and_adds.asc"
    },
    {
      "title": "CANN9.1.X asc_unlock constraints",
      "url": "https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/C-API/sync/asc_unlock.md"
    }
  ]
}
-->

# 性能优化策略：SIMD主体的SIMT离散取数与向量数学交接

只把离散取数阶段交给SIMT，连续数学阶段保留原SIMD实现。UB直交接与GM桥接是同一机制的存储交接变体，不是混合编程仅有的两种形态，也不意味着SIMT总比标量/向量Gather快。适合逐元素GM GetValue或不规则索引控制成为热点、完整源块难以驻留UB的场景；先确认真实数据流与瓶颈，不把现有载体的条件上限当平台下限。

## 两种数据流

| 变体 | 生产/消费域与数据流 | 主要收益与代价 |
| --- | --- | --- |
| U：UB直交接 | GM源/索引→SIMT VF→同核UB暂存→原SIMD数学→MTE3最终GM | 省中间GM往返；受UB资源/可写域、线程映射、多次VF发射与同步成本限制 |
| G：GM桥接 | GM源/索引→每核一次SIMT VF→核独占GM暂存→同核MTE2→UB原SIMD数学→MTE3最终GM | 减少小VF调用；相对U增加约 `2*n_core*sizeof(T)` 中间GM字节（写一次、读一次）与MTE2工作 |

`n_core`是核内输出元素数，`T`是暂存dtype。上述字节比较不含两路共有的源/索引读取和最终输出写入；缓存、带宽与流水重叠仍需实测。源数据留在GM，不要求将完整源slab搬入UB。数学如Ln是可复用示例，不是唯一适用算子。

## 正确性、接口与数值契约

- 每输出按自己的合法运行时索引计算源地址，不能假设一行或一段共享同一idx。以接口契约核对rank、dim（包括负dim归一化）、非gather轴缩小、重复索引及gather输出轴长大于源轴等合法域；不人为缩小索引合法范围。
- 核对索引dtype、线性位置、乘积和物理offset宽度。int64索引接口不能无证明窄化；乘加前先提升到足够宽的类型，signed源offset也须不溢出。若实现使用uint32输出计数/位置，域外必须走宽位generic或标量fallback；例如 `N>UINT32_MAX` 不能继续进入该窄位实现。宽位源offset不自动保证窄位输出计数安全。
- 输入连续性按原接口处理；需要contiguous副本时保持当前stream与寿命，并计入完整调用。空输出按契约返回。不得因重用输出暂存破坏输入别名、副作用或外部可见性。
- 只做原dtype bit搬运，保留原数学、精度提升、cast次数与舍入顺序。仅在原计算语义允许逐输出独立处理时采用该分区；跨元素依赖、归约或状态更新不能未经证明改成逐输出并行或重排。若原契约为F16/BF16升FP32→SIMD Ln→一次RNE，则两路都保持；F32保留原FP32运算。不用SIMT近似log、低精度计算或重复舍入换速度。NaN/Inf/零及其它特殊值按原接口核验；例如Ln(0)的负无穷语义不可丢。原容差不放宽，容差通过不等于bit-exact；要求bit-exact的接口另证。

## UB直交接：分配、写域与复用

使用已声明的静态/动态UB或LocalMemAllocator分配，指针保留 `__ubuf__`，源GM保留 `__gm__`。计入数学、输入/输出队列、对齐、DCache及编译器预留空间；不能将动态数组与动态allocator当作两块互不重叠内存。SIMT只写分配及验证范围内的地址；全局输出起点、UB局部lane与有效尾数分开计算，保证覆盖不重不漏。

某工具链/地址布局的验证中曾出现单VF受限写入域及基址约束；迁移时必须探针确认每VF安全写入字节预算，不能假定固定上限，也不能用随意指针重定基、双TBuf或顺序多调用绕过边界。举例：**若已验证**预算为8192B且映射可覆盖，F32字节预算对应2048元素，F16对应4096元素；这只是预算换算，不证明其它dtype、地址或重复调用已正确。底层机理未证明时保持未知。官方CANN9.1.X描述的编译器8KB预留UB区是独立概念，不能将它认定为受限VF写域的原因。

SIMT写完才允许SIMD读；SIMD数学与异步MTE3消费完才重用UB槽。多VF/tiles须验证分块ownership、mask、顺序排空与队列槽寿命。已出现过“修正取数精度后，多次VF发射仍使大输出退化”的负面机制，所以U不是总赢家，也不是永久不可用。跨核消费者或与输入别名时先另证合法生命周期与可见性，否则回退。

## GM桥接：暂存与流水依赖

优先使用核独占GM区，每核一次VF覆盖其全部有效输出，再分tile搬入UB计算。可在接口允许时复用独立输出作为原dtype暂存，但须证明暂存dtype与最终输出dtype的大小/对齐、布局、分区和逐字节地址覆盖相容，输出分配足以容纳暂存且当前stream寿命完整；不能仅因同dtype就认定安全。不同dtype/布局使最终写入覆盖尚未消费tile或其它核暂存时，改用独立workspace或正确fallback。不覆盖源/索引，不对外暴露中间结果；本核只消费自己的分区，某tile暂存已完整搬入UB且相关异步读取完成后，才向同一GM区写最终数学结果。跨tile输入/output队列Free/复用也要等消费完成。

若另配workspace，证明大小、对齐、分区和当前stream寿命覆盖全部异步工作，将分配/释放纳入约定完整调用边界。GM桥增加中间读写和MTE2，可能在小输出、缓存命中好或已有FastPath域无收益；一VF/core只描述调用次数，不证明负载均衡或性能最优。

同步按具体RAW/WAR依赖图安排。一个已验证的同核交接范式是 `asc_lock(PIPE_V,id)`→SIMT `asc_vf_call`→`asc_unlock(PIPE_V,id)`→`asc_lock(PIPE_S,id);asc_unlock(PIPE_S,id)`，再由MTE2/VECIN队列依赖完成搬入/计算/搬出；迁移仍需确认目标SDK中的pipe语义、缓存与队列顺序，而不是机械复制锁组合。`asc_unlock`须与lock使用同mutex/mode配对、不嵌套；连续同pipe同mutex锁对不能代替单流水依赖所需 `asc_sync_pipe`。VF/Vector/Scalar与MTE并行时，所有读写依赖及反向缓冲复用依赖都须处理。

官方gather&adds示例先SIMT写同核UB，再SIMD计算，V→MTE3事件后搬出；这是同核范式，不能当作跨核或跨SDK缓存保证。SIMT GM缓存、MainScalar缓存与MTE不同通路要按目标SDK核验；block barrier不代替流水事件或缓存处理。只在明确依赖要求并验证后加入cache操作/fence，不能盲加SyncAll/threadfence。

## 线程映射、核分区与fallback

设VF总线程数为B。generic映射可用 `k=tid;k<n_core;k+=B`，逐元素保护load/store和宽位全局起点；B须匹配launch_bounds与寄存器/stack预算。运行线程数不等于物理核数；按真实可用AIV、工作量和profiler配置核数，保护最后一个核的短分区。对CANN9.1.X混合调用，dim3各维乘积须≤2048且≤所声明的launch_bounds；launch_bounds取1–2048、缺省1024，运行线程配置不得超限。混合grid的x≤65535、y=z=1；其它SDK以其正式接口限制为准，不把纯SIMT三维grid直接移植。GM/UB参数必须保留相应地址空间，VF参数不能指向MainScalar局部存储。

物理suffix完整且映射可证明时，可用行臂减少重复divmod：每行P元素、R总行数，`rowThread=tid/tpr`、`lane=tid%tpr`，行内 `t=lane;t<P;t+=tpr`；每个输出仍读自己的idx。根据总行数、行宽与资源共同选tpr，不能仅按行长度决定。参考配置可从B=1024、tpr∈{8,32,128,256,1024}起做少量有依据的比较；这不是通用最优表。

若使用行步长 `B/tpr`，须满足 `B%tpr==0`，或另外证明不完整尾线程组的行认领不重不漏。`min(tpr,P)`可能破坏整除条件；例如B=1024/tpr=3时，不完整尾组可能与后续完整组重叠。未处理就回generic，不能因几个形状通过便宣称全域正确。按完整行划核时使用向上取整rowsPerCore、宽位blockLen和短尾核保护，核间/线程间ownership分别证明。

整行源与索引能安全驻留UB时保留SIMD Gather/FastPath；对齐head/body/tail、mask/guard、大索引/巨行、动态shape和地址界都需验证。Fast阈值按字节预算和实测分域建立，不无条件改成SIMT。无法满足宽度、资源或同步证明的域保持已正确的generic/标量fallback。

## 可执行选路

1. 先证明语义、地址宽度、核/线程独占、尾组、UB/GM分配与生命周期、原数学/转换/特殊值及同步缓存条件。未证明的路不进入性能比较；按原容差和接口全域回归，失败则回退该域。
2. 对目标SDK、布局、dtype、B和重复调用，实测U的安全预算 `B_verified`（字节、基址/区间、重复调用条件）。令 `E=min(floor(B_verified/sizeof(T)), verified_mapping_capacity, allocated_tile_elements)`；E>0时至少 `ceil(n_core/E)` 次VF。只有映射可覆盖整个预算，才可简化为 `ceil(n_core*sizeof(T)/B_verified)`。不能拿总UB容量或示例8192B直接代入；一线程一元素的映射还受B限制。计入每次发射、同步、尾块及SIMD/MTE交接成本。
3. 对G估一次VF/core的索引与线程循环、阶段交接，加相对U约 `2*n_core*sizeof(T)` 中间GM字节/MTE2。按dtype、shape、n_core、源散度、B/tpr、核数及已有FastPath分域比较；实际缓存/带宽/重叠必须测，不能仅靠字节数或“小shape”直接定胜负。
4. 同轮、相同输入和合理匹配的核映射，绑定实际源码与成功编译对象，比较op调用至设备完成同步的full-call以及真实device工作/辅助任务。计时边界写清，event不冒充wall/device；非连续转换、workspace工作计入约定边界。保留原始精度、调用次数、字节/资源、逐域耗时及波动，再设置guard。队列/线程/Fast组合未经消融不能拆为各项独立收益。
5. 逐域标 proposed/tested/restricted/rejected/adopted；提出未执行的变体保持未验证，精度失败、无收益和小幅收益都留机制及回退原因。U/G没有全形状优势承诺，也不把取数bit搬运正确等同于数学全bit-exact。更换SDK、地址布局、线程/核映射或消费者范围重新核验。

## 原理关系与公共参考

GM-ACCESS-DIET提供direct-GM取数机制，但没有替代这里的SIMD数学桥接；whole-kernel整数策略的无UB规范不能套到浮点数学主体。visibility机制提示写后读依赖，跨核fence案例不能直接复制到同核交接。复用已有机制，不把路径变体拆成重复卡。

- [CANN asc-devkit 9.1.0 gather&adds源码](https://gitcode.com/cann/asc-devkit/blob/9.1.0/examples/05_simd_simt_hybrid/00_introduction/simd_simt_gather_and_adds/gather_and_adds.asc)：演示GM→UB离散取数、SIMD连续数学及V_MTE3同步；固定一维float/uint32索引、每核1024元素的示例不是跨算子契约或性能承诺。
- CANN9.1.X《SIMD与SIMT混合编程》核函数配置、内存层级及编程示例：明确GM/UB地址空间、共享UB分配、DCache/预留与异步流水依赖。目标安装版本的接口和实际资源另核，混合编译不能无条件套纯SIMT `--enable-simt` 配置。
- [CANN9.1.X asc_unlock](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/C-API/sync/asc_unlock.md)：核内锁配对、排空及单流水重复锁限制。

## 检索卡（短卡）

动作：用SIMT离散取数接原SIMD数学：直写UB，或每核一次VF写GM再MTE2回UB；按验证预算与调用/搬运成本选路。
适用：A5离散gather热点；合法索引/宽位offset、独占核域，原数学/转换链可保留。
限制：UB写域/基址须实证；窄位计数域外回退；行tpr须整除B或证明尾组；跨SDK重验。
范围：gather后向量数学的取数交接，非纯SIMT log全域替换。
检索词：SIMT、asc_vf_call、SIMT→UB、GM桥接、GetValue、MTE2、FP32 Ln、RNE。
机会：标量GM取数主导或源超UB；多VF摊销与GM往返需比较。
代价：UB预算/多VF同步，或GM写读/锁队列；小shape可无收益。

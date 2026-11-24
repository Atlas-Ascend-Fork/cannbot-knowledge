---
type: Optimization
title: 固定小K有序键单遍候选槽选择
description: 把重复归约扫描改为每tile一次搬入与有序键转换，每lane维护K个键/索引候选槽，跨tile保留。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/fixed-small-k-ordered-key-lane-slot-single-pass.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "FIXED-SMALL-K-ORDERED-KEY-LANE-SLOT-SINGLE-PASS",
  "slug": "fixed-small-k-ordered-key-lane-slot-single-pass",
  "created": "2026-10-14",
  "classification": "validated_strategy",
  "operator_class": "top-k-selection",
  "phase": [
    "design",
    "tuning"
  ],
  "feature_signature": {
    "pattern": "fixed-small-K-streaming-lane-candidate-slots",
    "bottleneck": [
      "repeated-reduction-dimension-read",
      "repeated-key-conversion",
      "dependent-insertion-chain"
    ],
    "structure": [
      "ordered-int32-key",
      "single-CopyIn-per-tile",
      "K-key-index-slots-per-lane",
      "cross-tile-candidate-lifetime",
      "snapshot-before-update",
      "tail-mask",
      "metadata-guard"
    ]
  },
  "related_strategy_ids": [
    "register-resident-accumulator-arg-reduce",
    "topk-small-k-vector-rowsort-select",
    "bounded-heap-candidate-selection",
    "host-fitted-cost-model-seg-routing",
    "row-resident-single-gm-read-cross-pass-reuse"
  ],
  "name": "固定小K有序键单遍候选槽选择",
  "mechanism": "对固定小K的独立列lane，以有序键与配对索引维护K个降序候选槽；每个归约维/列块tile只搬入和转换一次，顺序消费归约行，候选跨tile保留，末尾一次输出。",
  "operator_scope": "固定小 K 的 top-k 选择 / 最大值及索引（每 lane 独立列，沿归约维 D 取 K 个候选）",
  "intent": "单一优化点：把沿归约维反复扫描/搬运/转换的选择过程，改为每 tile 一次 CopyIn/转换、每 lane 维护 K 个有序键与配对索引的候选槽；K 固定且小、候选跨 tile 存活，不是整 tensor 塞入 UB。",
  "implementation_steps": [
    "各 lane 的 K 槽初始化为独立哨兵域最差键；另管理合法候选数量/有效性，索引不能仅凭初值视为有效",
    "每个 D tile 只 CopyIn、窄浮点→FP32 转换、有序键构造各一次；按 D 行推进，每行新 (key,index) 插入自身 K 槽（始终降序、键/索引配对）",
    "K 槽跨全部 D tile 保留，仅切到新工作单元时重置；global index 含 D tile 起始行",
    "全部 D 完成后输出 K 槽与接口要求值；尾 D 行、尾 lane 掩码、向量对齐 padding 与输出计数分开，padding 不作合法候选",
    "k=5 参考变体：对同一旧五槽快照独立算 mask，降序槽使 mask 为后缀 true，从 t=4 降到 1 用两层 Select 更新（升序原地更新会覆盖下一槽旧值，须快照/前置 mask 防覆盖）"
  ],
  "risks": [
    "K 增大时指令量、候选 buffer、掩码与寄存器压力同步增长，超收益/资源域应回正确 sort/heap 或既有通用路径",
    "有序键编码仅针对 IEEE binary32；NaN 秩/payload、tie、±0、位型保留契约不同时须另证明或回合法路径",
    "INT32_MIN 是独立编码域哨兵、严格小于 -inf；不能只用浮点 -inf 打孔，否则全 -inf 可能重复选同索引",
    "升序原地更新或仅前置 mask 会覆盖下一槽要读的旧值，导致重复/丢失候选",
    "槽内 index 临时放 FP32 仅在整数可精确表示守卫内（如 D<=2^24）；更大 D 改经验证的整数索引载体或 fallback"
  ],
  "verification": {
    "correctness": [
      "验证值/index 对应、索引范围且互异、gather 值多重集、契约要求的降序、返回 shape/dtype；重复值 tie 顺序只按接口决定可否变化",
      "按原容差核验，equal_nan、非有限值一致与 bit-exact 分别记录；K>D、K=0、空输入、负维、别名、非连续各按接口处理，不用此快路静默改语义",
      "k=5 之外须构建并验证对应插入网络、快照与更新顺序，不直接沿用 k=5 的依赖深度/收益"
    ],
    "performance": [
      "组合实现测量支持该组织（k=5、FP16/BF16/FP32、受限跨步布局及资源域）；有序键、单遍数据流、槽更新、tiling 与 host 改动的独立贡献未分离，不把组合收益全归此卡",
      "计时区分完整调用至完成同步、event 与全部 device/辅助工作；按输入域配对比较，覆盖队列/输出/host 成本与稳定回退",
      "资源/正确性修复后重数 GM 搬运、Cast、比较、同步与受影响域工作量"
    ],
    "rollback_signals": [
      "扩展 K/布局前未做正确性与同轮性能验证不得采用",
      "无收益、覆盖失败、资源不足或稳定退化时修复、收缩守卫或回退，不承诺所有小 K 更快",
      "非连续输入须按实际 stride 计算地址，不能套连续 offset 公式"
    ]
  },
  "principle": "把“沿归约维反复扫描/搬运/转换”的选择，重构为“每 tile 一次搬入与有序键构造 + 每 lane K 个跨 tile 存活的降序候选槽”；K 固定且小，单遍消费归约行、末尾一次输出。",
  "validation_scope": "已验证实现范围为k=5、fp16/bf16/fp32及受限跨步布局。通用K是算法组织原则；其它K、位型、布局和插入网络必须另验。组合实现实测支持，独立机制贡献未测，不能宣称全部bit-exact。",
  "applicability": {
    "required_conditions": [
      "K固定且较小，K<=归约长度，独立lane可唯一拥有候选与输出",
      "有序键、NaN秩、tie与索引契约已证明，tile资源/地址/同步守卫满足"
    ],
    "excluded_conditions": [
      "任意浮点编码或稳定tie规则未经证明",
      "K增长使候选/指令/临时buffer成本超预算",
      "布局、索引宽度、尾部或异步寿命未证明"
    ],
    "constraints": [
      "首个已验证具体范围仅k=5；其它K需验证对应插入网络",
      "候选跨D tile保留，不要求整tensor驻UB",
      "连续布局与既有长行跨核快路分别门分派，不全域替换"
    ]
  }
}
-->
# 性能优化策略：固定小K有序键单遍候选槽选择

> 单一优化点：把沿归约维反复扫描、搬运和转换的选择过程，改为每个tile一次CopyIn/转换、每lane维护K个有序键与配对索引的候选槽。K固定且小，候选跨tile存活；不是整tensor一次塞入UB。

## 1. 原理与数据流

以逻辑输入[O,D,S]为例，D是选择归约维，S是独立列lane，输出沿D取得K个候选。每个工作单元拥有一个(o,S列块)，以[D行块,C列块]分块读取；物理非连续输入必须按实际stride计算地址，不能套连续offset公式。

1. 将各lane的K槽初始化为独立哨兵域的最差键，另管理合法候选数量或有效性；索引不能仅凭初始化值视为有效。
2. 对每个D tile只CopyIn一次，窄浮点到FP32转换及有序键构造也各一次。按D行推进，每行的各lane新(key,index)插入自身K槽，槽始终降序且键/索引配对。
3. **K槽跨全部D tile保留**，只在切到新工作单元时重置；global index包含D tile起始行，不是tile内j。完成全部D后才输出K槽及接口要求的值/最大值。
4. 尾D tile仅消费实际行；尾S lane掩码、向量对齐padding与输出精确计数分开。padding不能成为合法候选，也不能越界读写。

一般插入可用串行displaced链：新候选与旧槽比较，胜者留槽、败者携带其配对索引进入下一槽。保存被替换旧值后才继续，作为正确性对照。K槽不是单个argmax寄存器；可以用UB向量槽或经验证的寄存器载体，不保证任意K都适合完全寄存器驻留。

每tile输入/键工作量为O(D_tile*S_tile)，候选状态O(K*S_tile)，基本插入比较为O(D*K*S)。K增大时指令量、候选buffer、掩码与寄存器压力同步增长；超过收益或资源域就回正确sort/heap或既有通用路径，不能宣称单遍必优。

## 2. 有序键与精度红线

参考编码针对IEEE binary32：FP16/BF16有限值先精确拓宽到FP32，在接口允许时将NaN规范成正quiet NaN。令b为32位原始位型，按有符号int32比较；非负位型key=b，负位型key=~(uint32(b)+0x80000000u)。标量加法必须用明确定义的unsigned模2^32运算，向量Adds/Not实现也需核验指令语义与编译结果，禁止依赖C++ signed overflow。

- 规范NaN键0x7fc00000高于+inf键0x7f800000，只适用于契约把NaN排最高且允许该规范化的域。负NaN必须先处理，不能直接套负数变换。若契约的NaN秩或payload保留不同，保留原值/位型或回合法路径。
- -inf变成键0x807fffff；**INT32_MIN(0x80000000)是独立编码域哨兵，严格小于-inf**。不能只用浮点-inf打孔，否则全-inf可能重复选同索引。没有NaN规范化或采用其他位型时须重新证明哨兵不与真实键冲突。
- -0键0xffffffff、+0键0，键次序人为区分数值相等的零。仅在tie契约允许时采用；稳定tie、零符号、NaN payload或返回原始位型要求需额外保存/解码证明，不能因“没有数值加法”就宣称bit-exact。
- 参考负键反变换与正键直通可恢复规范FP32位型；窄化舍入、NaN/inf输出及gather原值语义仍须检查。不得将所有浮点位型、整数或其它dtype直接代入此编码。
- 槽内index若临时放FP32，仅在整数可精确表示的守卫内采用，例如保守D<=2^24；更大D改用经验证的整数索引载体或fallback。输出int32/int64宽度、地址stride乘积及tile基址分别核对，乘加前提升到足够宽位。

验证值/index对应、索引范围且互异、gather值多重集、契约要求的降序、返回shape/dtype；重复值只按接口决定tie顺序可否变化，不能因为比较器忽略索引顺序而免除关系检查。K>D、K=0、空输入、负维、别名和非连续布局遵循各自接口，不用这个快路静默改语义。

## 3. k=5参考调优变体与负边界

已验证的具体实现为k=5。先针对**同一旧五槽快照**独立计算m[t]=(newKey>=oldKey[t])，降序槽使mask为后缀true。然后从t=4降到1：inner[t]按m[t-1]在oldSlot[t-1]与new之间选，再按m[t]决定写inner或保留oldSlot[t]；最后更新槽0。key与index使用完全相同mask和顺序。

五mask前置减少串行携带链的依赖；每槽两层Select的读源必须仍是旧状态。**升序原地更新会先覆盖下一槽要读的oldSlot，导致重复/丢失候选**；仅前置mask不能防这种覆盖。采用独立旧状态buffer时需证明生命周期并重计UB。保留串行displaced链与两层Select配对正确性对照，不推广“任意顺序都正确”。

GE允许相等新候选进入，但配对移位须保证互异索引；需要稳定tie时把合法tie键纳入比较，或回支持该契约的路径。其它K必须构建并验证对应插入网络、快照和更新顺序，不能直接声称也有相同两层Select、依赖深度或收益。

## 4. UB预算、队列与同步

令L为padding后的lane宽，C_d为D行块，E=C_d*L，w为输入字节数。一个具体UB向量槽实现的预算清单为：depth-2输入队列2Ew，规范/转换FP32 E*4，有序键E*4，窄dtype额外scratch E*4，BuildKeys与K mask共享区align32(max(E,K*L))字节，K键4KL、FP32索引4KL，单候选键/索引与行号暂存12L，int64输出索引8KL，以及公共归约scratch、guard/padding、输出value staging、其它queue/TBuf与保留空间。合计该组织的主体为2Ew+8E+[窄dtype:4E]+align32(max(E,KL))+(16K+12)L，**不是全实现的通用上界**。

以实际InitBuffer、queue深度、复用时序、对齐和编译资源报告逐项验预算，不能遗漏未走分支仍分配的buffer。寄存器版本另验寄存器/栈/occupancy；选择C_d和lane宽时同时考虑发射固定成本、padding浪费、tile数及完整调用成本，不凭元素吞吐估算最优。

双缓冲最多保持已预算的outstanding输入：CopyIn/EnQue完成依赖后DeQue消费，直到键/消费者结束才Free；不能预取覆盖当前tile。候选、mask和单槽暂存禁止被下一行提前改写。V到MTE3输出、MTE3读取结束到buffer复用、标量/向量交接按实际TPipe依赖同步；新增早退或scalar gate须证明可见性，不能删除必要同步换速度。

每工作单元独占输出，不跨调用缓存候选或输入；新地址、多stream、异步生命周期与scratch释放均要覆盖。跨核D切分需要独立候选合并及同步证明，不能直接共享这些槽。

## 5. 泛化、分派与临时补偿

当前证据支持k=5、FP16/BF16/FP32与已验证的受限跨步布局及其资源域。固定小K主体是可复用算法原则，其它K、布局、特殊值契约或设备资源均保持待验证，不借用k=5正确性或性能结论。

连续归约维可保留其已验证的行归约/排序路径；宽列跨步路径按metadata守卫选此单遍组织。若已有长归约跨核快速路径，保留其已验证域并测边界，不默认用单核候选槽替换。守卫依据shape/dtype/stride/K/资源与实测成本，不能使用用例编号或缓存输入值。

资源不足时缩C_d/lane宽、减少安全queue深度或回正确fallback；不能把容量修复偷偷改成每个候选轮重搬入整tile、重复Cast/键构造而仍称单遍。NaN/-inf临时mask或索引补偿若用于恢复正确性，明确其退出条件：新编码、互异索引与特殊值测试已证明覆盖后才撤；未证明就保留安全路径并计入成本。

## 6. 实施与验收

先锁定接口、键秩、tie与资源域，建立串行候选链正确对照，再验证tile一次搬入/转换与跨tile槽存活；需要时加入快照插入网络。测K槽、D tile、lane尾、重复/全-inf/混合NaN和±inf/±0、负有限值、索引精度边界、布局/地址宽度和fallback两侧。

成功编译的源码与实际加载绑定，按原容差核验值和索引关系，equal_nan、非有限值一致与bit-exact分别记录。计时区分完整调用至完成同步、event和全部device/辅助工作；按输入域配对比较，覆盖队列/输出/host成本和稳定回退。资源/正确性修复后重数GM搬运、Cast、比较、同步与受影响域工作量。

已有组合实现测量支持这套组织，**有序键、单遍数据流、槽更新、tiling及host改动的独立贡献未分离**；不得把组合收益全归此卡。扩展K或布局先做正确性与同轮性能验证；无收益、覆盖失败、资源不足或稳定退化时修复、收缩守卫或回退，不承诺所有小K更快。

## 检索卡（短卡）

动作：把重复归约扫描改为每tile一次搬入与有序键转换，每lane维护K个键/索引候选槽，跨tile保留。
适用：固定小K、独立列lane、契约和UB守卫满足；已验证仅k=5与FP16/BF16/FP32受限跨步布局。
限制：核验NaN秩、±inf/±0、tie、互异索引与tail-mask；snapshot-before-update，升序覆盖旧槽错误。
范围：top-k选择/最大值及索引；连续和既有长行快路独立分派。
检索词：top-k、small fixed K、ordered key、lane槽、snapshot-before-update、tail-mask
机会：多遍GM搬运/转换及串行插入依赖；k=5可用五mask前置和降序两层Select。
代价：候选UB与插入指令随K增长；其它K/布局另验，超域回正确sort/heap。

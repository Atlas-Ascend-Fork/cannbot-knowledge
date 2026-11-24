---
type: Optimization
title: Stein 轮体两级尾零剥离 + 奇偶安全收缩：软件模拟 tz 阶梯宽度 {16,8,4,2,1}→{2,1}、B!=0 守卫收缩改奇偶交换收缩，每轮向量指令 26→15
description: 将尾零阶梯缩为 {2,1}，每轮最多剥三位；若剥离后 B 仍为偶，则交换以维持不变量。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.data_movement
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/stein-roundbody-twolevel-tzstrip-parity-swap.md
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
      "MAX_ROUNDS 不得下调且必须以穷举+结构化对抗扫描复算新轮体的轮数上界（本轮 31-bit 对抗 max=37 < 64 裕度 1.73x、16-bit 域穷举 max=19 < 47 裕度 2.47x），不得以『典型数据 4 chunk』为由收紧安全网",
      "向量轮体重写属静默损坏高危类别，必须以改前/改后双相位内核绑定的 A/B 逐位差分验收（L-SIMD-UNROLL-SREG-REINIT），验证集须含对抗 tz 形态（b=2^k·m、a=2^k±1、gcd=2^k 近邻对）与余数行输入，并辅以全值域模型等价穷举（1.19G 对 diff=0）",
      "掩码粒度纪律：数据面 API 精确 cnt，Compare/Compares/Select 及新奇偶 And+Compares 按 AlignUp(cnt,64)，尾 lane 只触碰私有 scratch；不引入 RegTensor 数组化/动态索引（NEG-4）、不新增访存基址与步幅（NEG-3）",
      "共享轮体改动会实例化到每个 dtype/BCT 组合：correctness 必须全量 all_cases，性能必须全集采集，回归检测以逐 route 预测带 + A/B 差分 + 结构不变量（Block Num、MTE2 绝对时长、host 逐字节）承担空控制组",
      "跨模板共享的 done/gate 计数 scratch 不得与其他用途的缓冲元素别名：本轮 A/B 定位 parent 潜伏缺陷——done/gate scratch 别名 wzero 恒零缓冲首元素（每 tile 仅清零一次），SAME 路径 +0 复制读同一元素，MAX_CHUNKS 耗尽的 slice 把非零 not-done 计数泄入下一 slice 元素 0 的操作数（触发条件仅为提升/原生域 abs-with-wrap INT_MIN 永不收敛 lane，属确定性错答的潜伏缺陷）；修复候选为每 slice 前重置该元素或移到专用 TBuf，落地任何共享轮体改动前应排查同类别名"
    ],
    "excluded_conditions": [
      "阶梯宽度集合缺尾部宽度 1 级的组合已被仿真证伪（如 {16,1}/{2}/{4}/{8}/{4,2}/{8,2}/{6,2}：92-100% slice chunk 升档、31-bit 对抗轮数越界 MAX_ROUNDS 即静默错误结果），不得重试；同机制降级参数 {4,2,1}（19 op）保留为一次修正重试选项",
      "轮体被单条 dominant 指令主导或冗余指令已被编译器消除（单指令边际消减不转化 wall-time，见 NEG-ELEM-VEC-OPCOUNT-NO-GAIN）",
      "值域/分布使升档率高的 route 承载主要权重且升档代价未被吸收（逐 route 预测带跌破下带即回退）",
      "非 VEC-bound 时不预期收益；一次性公共剥离阶段（normalize）不得套用本机制——它需要完整宽度把公共 2 的幂一次剥净"
    ],
    "required_conditions": [
      "发射代价标定已完成：增量 chunk 成本 ≈ 轮体指令数×chunk 轮数/64 lane（无 dominant 指令、无编译器 CSE 塌缩），即轮体按 ~1 op/cycle 发射吞吐运行——否则落入 NEG-ELEM-VEC-OPCOUNT-NO-GAIN 边界",
      "轮体中存在为强后置条件（如『剥离后必奇』）设计的多级软件模拟阶梯，而被剥离量分布集中于小值（几何/幂律），使宽度层级冗余",
      "存在可保持收敛不变量与吸收态的等价收缩形式（如奇偶交换），替换后每轮指令数下降而收敛轮数近似不变（需分布级仿真验证 chunk 档位不升或升档代价可被吸收）",
      "收敛轮数上界可以穷举（到有效位宽的子集）+ 结构化对抗扫描方法复算，且对既有 MAX_ROUNDS 裕度 >= ~1.7x；上界安全网不得下调"
    ]
  },
  "classification": "validated_strategy",
  "created": "2026-08-27",
  "evidence": [
    {
      "comparison_sha256": "f1749b064cd252087644634ea6119d2c86c2f27f862f9e4ff508830b39ca4514",
      "decision_sha256": "4b2cf9c5d644e6739faa0af36d5c5f2a4a31383cff1e091a3a37c10c5eede18e",
      "operator_class": "broadcast",
      "performance_sha256": "4a3187920ce3af4eccb551ef0e97f77e896c2841fa1167b98430ee7dac56115d",
      "round": 3,
      "run_id": "<run-id>",
      "status": "accepted",
      "strategy_sha256": "8a2ba014e6a1cb9dbd02613ebd99cff95f59c37e79bb44ad372d4273215a2e20",
      "verify_sha256": "a965995b5e2d02faa24c058593c80b4137ad161321bd9df26dd759b3e3dcf2cb"
    }
  ],
  "feature_signature": {
    "bottleneck": [
      "vec-bound",
      "vec-instruction-count",
      "software-emulated-tz-ladder",
      "fixed-round-loop"
    ],
    "dtypes": [
      "int16",
      "int32",
      "int64"
    ],
    "pattern": "roundbody-opcount-tzstrip-parity-swap",
    "structure": [
      "vec-iterative-loop",
      "streaming-elementwise",
      "per-lane-convergence",
      "chunk-early-exit",
      "shared-cross-template-body"
    ]
  },
  "generality": "op_class",
  "id": "ELEM-STEIN-ROUNDBODY-TZSTRIP2-PARITY-SWAP",
  "implementation_steps": [
    "发射代价标定：用增量 chunk 成本 vs 指令计数模型（轮体指令数×chunk 轮数/64 lane）确认全部指令真实发射、无 dominant 指令、无 CSE 塌缩；不满足则按 NEG-ELEM-VEC-OPCOUNT-NO-GAIN 放弃立项",
    "分布级仿真选择阶梯宽度集合：按被剥离量的分布（tz 几何分布）比较各候选的每轮指令数 × chunk 档位期望，证伪缺尾部宽度 1 级的组合（升档率与对抗轮数越界检查）",
    "实现宽度削减 + 等价收缩形式（奇偶交换 Select），保持 normalize 公共剥离、final 折回、门/早退骨架、chunk 粒度逐字不变；宽度掩码在块循环外 Duplicate 按名传参",
    "以穷举（到有效位宽子集）+ 结构化对抗扫描复算轮数上界并记录对 MAX_ROUNDS 的裕度；上界安全网不下调",
    "全量 all_cases verify + 双相位内核绑定 A/B 逐位差分（含对抗 tz 与强制失败臂探针）+ 全集性能采集，按逐 route 预测带与指令比理论上界验收（任一 case 收益超理论上界即怀疑测量假象）"
  ],
  "intent": "消除软件模拟 tz 阶梯的纯发射成本：当轮体无 dominant 指令、全部指令真实发射且按 ~1 op/cycle 吞吐运行时，阶梯的冗余宽度层级（为大 tz 值设计、而 tz 分布集中于小值）是轮体指令数的主体，削减真实发射指令数直接转化为 wall-time。",
  "mechanism": "GcdStripOddLadder 的 int32 臂宽度集合 {16,8,4,2,1}→{2,1}（每级 And+Compares+ShiftRights+Select 共 4 op，5 级 20 op → 2 级 8 op；宽度掩码寄存器已在现有签名，继续在块循环外 Duplicate 后按名传参）；GcdSteinStep 的收缩由 Compares(B!=0) 守卫双 Select 改为按剥离后 B 奇偶的一次交换 Select（B 偶->(|A-B|,min)，B 奇->(min,|A-B|)；奇偶测试置于 ladder 调用后，op 计数与数据流等价，15 op/轮）。逐字保留：GcdSteinNormalize 的一次性公共尾零剥离 + 奇偶 swap（需要完整阶梯把公共 2 的幂一次剥净并建立 A 奇不变量，压减它只会把公共 2 推进轮循环）、final 的 P=2^g 折回、数据域门与 lane packing、ComputeGcdChunkVF/ComputeGcdNarrowChunkVF32 的 not-done 判据（B 收敛恰到 0 的吸收态）与 EUCLID_CHUNK=8 分块早退；MAX_ROUNDS 47/64/93 不下调。轮体被三个 dtype 模板的快速路径共享（int16 提升域、int32 原生域、int64 窄域视图），故作用面为全部 route，回归检测以逐 route 预测带 + 全量 A/B 逐位差分 + 结构不变量（Block Num、MTE2 绝对时长、host 逐字节不变）替代空控制组。",
  "name": "Stein 轮体两级尾零剥离 + 奇偶安全收缩：软件模拟 tz 阶梯宽度 {16,8,4,2,1}→{2,1}、B!=0 守卫收缩改奇偶交换收缩，每轮向量指令 26→15",
  "operator_class": "broadcast",
  "operator_scope": "VEC-bound 的流式 elementwise 整数迭代计算（GM->UB->VEC->UB->GM），热链为分块固定轮逐 lane 迭代收敛循环（如 Stein/无除法二进制 GCD，已有 chunk 早退/停止保护），轮体全部由 ~1 cycle ALU 向量指令（And/Shift/Compares/Select/Sub/Abs/Min）组成、无单条 dominant 指令、无编译器 CSE 塌缩（增量 chunk 成本已标定 ≈ 轮体指令数×chunk 轮数/64 lane），且尾零剥离必须由多级条带阶梯软件模拟（载体无 ctz/ffs 类原语）、被剥离量的分布集中于小值（几何分布）",
  "principle": "Stein 收缩并不要求 B 为奇：把阶梯降为 {2,1}（每轮最多剥 3 位）后，用『剥离后 B 仍为偶』做一次交换 Select 维持不变量——A 奇不变量两条支路都保持（A 奇 B' 偶 => |A-B'| 奇），gcd(min,|A-B|) 与次序无关，B'!=0 时 max 严格下降，B==0 落在偶支 (|A-0|,min(A,0))=(A,0) 是与守卫形式等价的吸收态。由于两次奇数相减差值的 tz 服从几何分布（P(tz>=k)=2^-(k-1)），小宽度高频命中而大宽度几乎不触发，{2,1} 使每轮指令 26→15（chunk 项成本 ×15/26=0.577）而 chunk 档位基本不升（worst-lane chunk 数在多数值域与父版完全一致）。该机制的立项前提是发射代价标定（增量 chunk 成本 ≈ 指令计数模型）：若被消减指令已被 CSE 合并或被 dominant 指令稀释，则单指令消减不转化 wall-time（见 NEG-ELEM-VEC-OPCOUNT-NO-GAIN 的边界）；反之大幅削减真实发射的阶梯层级收益为正且受指令比理论上界包住。代价是轮数上界抬升：必须保留尾部宽度 1 级并以穷举+结构化对抗扫描复算 MAX_ROUNDS 裕度。",
  "related_anti_patterns": [],
  "risks": [
    "阶梯宽度选错：缺尾部宽度 1 级的组合导致 chunk 大量升档甚至对抗轮数越界 MAX_ROUNDS——越界是静默错误结果而非崩溃，必须靠轮数复算与对抗探针拦截",
    "收缩形式替换破坏吸收态或 A 奇不变量（B==0 分支、gcd 次序无关性），属静默损坏高危类别，源码级等价论证不充分，必须 A/B 逐位差分",
    "共享轮体改动泄漏到全部 dtype/BCT 实例：空控制组时须以逐 route 预测带 + 结构不变量兜底，任一 route 跌破下带即归因回退",
    "done/gate 计数 scratch 与恒零缓冲别名的既有潜伏缺陷会随轮体变化改变泄漏取值（同错/凑对分布漂移），A/B 差分须做逐点定位与 golden 交叉归因，不得把 parent 既有缺陷误判为本轮实现 bug，也不得因此放过真实现 bug",
    "超预测带落点需归因（发射资源冲突缓解的超线性效应、固定停顿项随轮体缩短），须以理论上界包住性检验排除测量假象，不得直接上调验收带"
  ],
  "slug": "stein-roundbody-twolevel-tzstrip-parity-swap",
  "summary": "对无除法二进制迭代轮体的软件模拟 tz 剥离阶梯做宽度削减 + 收缩形式替换：阶梯 int32 臂由 5 级 {16,8,4,2,1}（20 op）降为 2 级 {2,1}（8 op），守卫收缩（B!=0 守卫 Select）改为按剥离后 B 奇偶的一次交换 Select，每轮向量指令 26→15 而收敛轮数近似不变（tz 几何分布下 {2,1} 每轮最多剥 3 位已覆盖 87.5% 轮次）；normalize 一次性公共尾零剥离、final P 折回、数据域门、lane packing、分块早退骨架逐字保留，MAX_ROUNDS 不下调。实测全部 8 条 route 的 20 case 全 improved、20-case incremental 1.4503x、cumulative 1.6908x、逐 case 收益全部低于 26/15=1.7333x 指令比理论上界；A/B 逐位差分 48,931,648 元素中 1832 处差异 100% 归因 parent 既有 done-scratch 别名缺陷（与本机制无关）。",
  "verification": {
    "correctness": [
      "round 3 verify ok=true 20/20（run.json.all_cases 全量，跨模板共享轮体），fingerprint kernel b9ca42ec2533eeb1 与 build/verify/安装态四字段闭环",
      "A/B 逐位差分（rounds/003/probe/ab_evidence.json，双相位内核绑定：phase A=parent 2cc7b7d9 / phase B=round-3 b9ca42ec）：45 探针 48,931,648 元素，43 探针位精确；2 探针共 1832 处差异逐点复核 100% 位于 tile 内 slice 序号>=1 的首元素且前一 256-slice 含 INT32_MIN lane——全部归因 parent 既有 wzeroBuf_[0] done-scratch 别名缺陷（golden 交叉：两 kernel 同错 24,444 / 仅 parent 凑对 149 / 仅新凑对 130），缺陷包络外 48,929,816 元素位精确",
      "轮数上界独立复算（穷举到 b13 + 结构化对抗扫描 + 16-bit 域全穷举 1.07G 对）：新轮体 31-bit 对抗 max=37 < MAX_ROUNDS 64（裕度 1.73x）、16-bit 域 max=19 < 47（裕度 2.47x）；模型等价性 1.19G 对 parent/新轮体最终输出 diff=0（非 INT_MIN 输入全部收敛且与 |gcd| 参考一致）"
    ],
    "performance": [
      "20/20 case 全部 improved、0 regressed、0 missing；20-case 时延加权 incremental 1.4503x（机制确认线 1.15x，名义预测带 [1.28,1.42] 上沿 +2.1%，归因 V 管发射资源冲突缓解的超线性效应与固定停顿项缩短）、cumulative vs baseline 1.6908x",
      "逐 case 收益全部被 26/15=1.7333x 的 chunk 项理论天花板包住（最深 chunk case 1.6924x 恰为全场最大），排除测量假象；route 级 R1-R8 全部 1.19-1.66x，广播驻留 route 落带内（其固定 gather 开销不随轮体变化）",
      "1-chunk case 无任何 chunk 升档签名（cyc/elem 下降 ~2.0）；vec_time 降幅大于总时长降幅且随 chunk 深度单调（compute-only 改动指纹）；MTE2 绝对时长持平（零新增 GM 流量）、Block Num 全部 64、op_host 逐字节不变（tiling/route 划分零变化）"
    ],
    "rollback_signals": [
      "20-case incremental < 1.15x（指令数->周期转化假设失败，NEG-ELEM-VEC-OPCOUNT-NO-GAIN 型边界成立）或任一 case < 0.95x（含 1-chunk case cyc/elem 高于 parent 的升档回归）",
      "任一 A/B 逐位差分非零且不能 100% 归因到已登记的 parent 既有缺陷包络（逐点格点复核 + golden 交叉是判据），或对抗 tz 探针在既有 MAX_ROUNDS 内不收敛/结果错误",
      "任一 route 跌破逐 route 预测带下带（升档代价未被吸收），或结构不变量破坏（Block Num 变化、MTE2 绝对时长上涨、host 字节变化）"
    ]
  }
}
-->

# 性能优化策略：Stein 轮体两级尾零剥离 + 奇偶安全收缩：软件模拟 tz 阶梯宽度 {16,8,4,2,1}→{2,1}、B!=0 守卫收缩改奇偶交换收缩，每轮向量指令 26→15

单一优化点：对无除法二进制迭代轮体的软件模拟 tz 剥离阶梯做宽度削减 + 收缩形式替换：阶梯 int32 臂由 5 级 {16,8,4,2,1}（20 op）降为 2 级 {2,1}（8 op），守卫收缩（B!=0 守卫 Select）改为按剥离后 B 奇偶的一次交换 Select，每轮向量指令 26→15 而收敛轮数近似不变（tz 几何分布下 {2,1} 每轮最多剥 3 位已覆盖 87.5% 轮次）；normalize 一次性公共尾零剥离、final P 折回、数据域门、lane packing、分块早退骨架逐字保留，MAX_ROUNDS 不下调。实测全部 8 条 route 的 20 case 全 improved、20-case incremental 1.4503x、cumulative 1.6908x、逐 case 收益全部低于 26/15=1.7333x 指令比理论上界；A/B 逐位差分 48,931,648 元素中 1832 处差异 100% 归因 parent 既有 done-scratch 别名缺陷（与本机制无关）。

## 1. 原理

Stein 收缩并不要求 B 为奇：把阶梯降为 {2,1}（每轮最多剥 3 位）后，用『剥离后 B 仍为偶』做一次交换 Select 维持不变量——A 奇不变量两条支路都保持（A 奇 B' 偶 => |A-B'| 奇），gcd(min,|A-B|) 与次序无关，B'!=0 时 max 严格下降，B==0 落在偶支 (|A-0|,min(A,0))=(A,0) 是与守卫形式等价的吸收态。由于两次奇数相减差值的 tz 服从几何分布（P(tz>=k)=2^-(k-1)），小宽度高频命中而大宽度几乎不触发，{2,1} 使每轮指令 26→15（chunk 项成本 ×15/26=0.577）而 chunk 档位基本不升（worst-lane chunk 数在多数值域与父版完全一致）。该机制的立项前提是发射代价标定（增量 chunk 成本 ≈ 指令计数模型）：若被消减指令已被 CSE 合并或被 dominant 指令稀释，则单指令消减不转化 wall-time（见 NEG-ELEM-VEC-OPCOUNT-NO-GAIN 的边界）；反之大幅削减真实发射的阶梯层级收益为正且受指令比理论上界包住。代价是轮数上界抬升：必须保留尾部宽度 1 级并以穷举+结构化对抗扫描复算 MAX_ROUNDS 裕度。

实现机制：GcdStripOddLadder 的 int32 臂宽度集合 {16,8,4,2,1}→{2,1}（每级 And+Compares+ShiftRights+Select 共 4 op，5 级 20 op → 2 级 8 op；宽度掩码寄存器已在现有签名，继续在块循环外 Duplicate 后按名传参）；GcdSteinStep 的收缩由 Compares(B!=0) 守卫双 Select 改为按剥离后 B 奇偶的一次交换 Select（B 偶->(|A-B|,min)，B 奇->(min,|A-B|)；奇偶测试置于 ladder 调用后，op 计数与数据流等价，15 op/轮）。逐字保留：GcdSteinNormalize 的一次性公共尾零剥离 + 奇偶 swap（需要完整阶梯把公共 2 的幂一次剥净并建立 A 奇不变量，压减它只会把公共 2 推进轮循环）、final 的 P=2^g 折回、数据域门与 lane packing、ComputeGcdChunkVF/ComputeGcdNarrowChunkVF32 的 not-done 判据（B 收敛恰到 0 的吸收态）与 EUCLID_CHUNK=8 分块早退；MAX_ROUNDS 47/64/93 不下调。轮体被三个 dtype 模板的快速路径共享（int16 提升域、int32 原生域、int64 窄域视图），故作用面为全部 route，回归检测以逐 route 预测带 + 全量 A/B 逐位差分 + 结构不变量（Block Num、MTE2 绝对时长、host 逐字节不变）替代空控制组。

## 2. 性能问题模式

- 优化目标：消除软件模拟 tz 阶梯的纯发射成本：当轮体无 dominant 指令、全部指令真实发射且按 ~1 op/cycle 吞吐运行时，阶梯的冗余宽度层级（为大 tz 值设计、而 tz 分布集中于小值）是轮体指令数的主体，削减真实发射指令数直接转化为 wall-time。
- 适用数据流：VEC-bound 的流式 elementwise 整数迭代计算（GM->UB->VEC->UB->GM），热链为分块固定轮逐 lane 迭代收敛循环（如 Stein/无除法二进制 GCD，已有 chunk 早退/停止保护），轮体全部由 ~1 cycle ALU 向量指令（And/Shift/Compares/Select/Sub/Abs/Min）组成、无单条 dominant 指令、无编译器 CSE 塌缩（增量 chunk 成本已标定 ≈ 轮体指令数×chunk 轮数/64 lane），且尾零剥离必须由多级条带阶梯软件模拟（载体无 ctz/ffs 类原语）、被剥离量的分布集中于小值（几何分布）
- Feature signature：`{"bottleneck": ["vec-bound", "vec-instruction-count", "software-emulated-tz-ladder", "fixed-round-loop"], "dtypes": ["int16", "int32", "int64"], "pattern": "roundbody-opcount-tzstrip-parity-swap", "structure": ["vec-iterative-loop", "streaming-elementwise", "per-lane-convergence", "chunk-early-exit", "shared-cross-template-body"]}`

## 3. 正确性红线

- 阶梯宽度选错：缺尾部宽度 1 级的组合导致 chunk 大量升档甚至对抗轮数越界 MAX_ROUNDS——越界是静默错误结果而非崩溃，必须靠轮数复算与对抗探针拦截
- 收缩形式替换破坏吸收态或 A 奇不变量（B==0 分支、gcd 次序无关性），属静默损坏高危类别，源码级等价论证不充分，必须 A/B 逐位差分
- 共享轮体改动泄漏到全部 dtype/BCT 实例：空控制组时须以逐 route 预测带 + 结构不变量兜底，任一 route 跌破下带即归因回退
- done/gate 计数 scratch 与恒零缓冲别名的既有潜伏缺陷会随轮体变化改变泄漏取值（同错/凑对分布漂移），A/B 差分须做逐点定位与 golden 交叉归因，不得把 parent 既有缺陷误判为本轮实现 bug，也不得因此放过真实现 bug
- 超预测带落点需归因（发射资源冲突缓解的超线性效应、固定停顿项随轮体缩短），须以理论上界包住性检验排除测量假象，不得直接上调验收带

资源与硬件约束：

- MAX_ROUNDS 不得下调且必须以穷举+结构化对抗扫描复算新轮体的轮数上界（本轮 31-bit 对抗 max=37 < 64 裕度 1.73x、16-bit 域穷举 max=19 < 47 裕度 2.47x），不得以『典型数据 4 chunk』为由收紧安全网
- 向量轮体重写属静默损坏高危类别，必须以改前/改后双相位内核绑定的 A/B 逐位差分验收（L-SIMD-UNROLL-SREG-REINIT），验证集须含对抗 tz 形态（b=2^k·m、a=2^k±1、gcd=2^k 近邻对）与余数行输入，并辅以全值域模型等价穷举（1.19G 对 diff=0）
- 掩码粒度纪律：数据面 API 精确 cnt，Compare/Compares/Select 及新奇偶 And+Compares 按 AlignUp(cnt,64)，尾 lane 只触碰私有 scratch；不引入 RegTensor 数组化/动态索引（NEG-4）、不新增访存基址与步幅（NEG-3）
- 共享轮体改动会实例化到每个 dtype/BCT 组合：correctness 必须全量 all_cases，性能必须全集采集，回归检测以逐 route 预测带 + A/B 差分 + 结构不变量（Block Num、MTE2 绝对时长、host 逐字节）承担空控制组
- 跨模板共享的 done/gate 计数 scratch 不得与其他用途的缓冲元素别名：本轮 A/B 定位 parent 潜伏缺陷——done/gate scratch 别名 wzero 恒零缓冲首元素（每 tile 仅清零一次），SAME 路径 +0 复制读同一元素，MAX_CHUNKS 耗尽的 slice 把非零 not-done 计数泄入下一 slice 元素 0 的操作数（触发条件仅为提升/原生域 abs-with-wrap INT_MIN 永不收敛 lane，属确定性错答的潜伏缺陷）；修复候选为每 slice 前重置该元素或移到专用 TBuf，落地任何共享轮体改动前应排查同类别名

## 4. 泛化条件

- 策略作用域：op_class：broadcast

适用：

- 发射代价标定已完成：增量 chunk 成本 ≈ 轮体指令数×chunk 轮数/64 lane（无 dominant 指令、无编译器 CSE 塌缩），即轮体按 ~1 op/cycle 发射吞吐运行——否则落入 NEG-ELEM-VEC-OPCOUNT-NO-GAIN 边界
- 轮体中存在为强后置条件（如『剥离后必奇』）设计的多级软件模拟阶梯，而被剥离量分布集中于小值（几何/幂律），使宽度层级冗余
- 存在可保持收敛不变量与吸收态的等价收缩形式（如奇偶交换），替换后每轮指令数下降而收敛轮数近似不变（需分布级仿真验证 chunk 档位不升或升档代价可被吸收）
- 收敛轮数上界可以穷举（到有效位宽的子集）+ 结构化对抗扫描方法复算，且对既有 MAX_ROUNDS 裕度 >= ~1.7x；上界安全网不得下调

不适用：

- 阶梯宽度集合缺尾部宽度 1 级的组合已被仿真证伪（如 {16,1}/{2}/{4}/{8}/{4,2}/{8,2}/{6,2}：92-100% slice chunk 升档、31-bit 对抗轮数越界 MAX_ROUNDS 即静默错误结果），不得重试；同机制降级参数 {4,2,1}（19 op）保留为一次修正重试选项
- 轮体被单条 dominant 指令主导或冗余指令已被编译器消除（单指令边际消减不转化 wall-time，见 NEG-ELEM-VEC-OPCOUNT-NO-GAIN）
- 值域/分布使升档率高的 route 承载主要权重且升档代价未被吸收（逐 route 预测带跌破下带即回退）
- 非 VEC-bound 时不预期收益；一次性公共剥离阶段（normalize）不得套用本机制——它需要完整宽度把公共 2 的幂一次剥净

## 5. 实施步骤

1. 发射代价标定：用增量 chunk 成本 vs 指令计数模型（轮体指令数×chunk 轮数/64 lane）确认全部指令真实发射、无 dominant 指令、无 CSE 塌缩；不满足则按 NEG-ELEM-VEC-OPCOUNT-NO-GAIN 放弃立项
2. 分布级仿真选择阶梯宽度集合：按被剥离量的分布（tz 几何分布）比较各候选的每轮指令数 × chunk 档位期望，证伪缺尾部宽度 1 级的组合（升档率与对抗轮数越界检查）
3. 实现宽度削减 + 等价收缩形式（奇偶交换 Select），保持 normalize 公共剥离、final 折回、门/早退骨架、chunk 粒度逐字不变；宽度掩码在块循环外 Duplicate 按名传参
4. 以穷举（到有效位宽子集）+ 结构化对抗扫描复算轮数上界并记录对 MAX_ROUNDS 的裕度；上界安全网不下调
5. 全量 all_cases verify + 双相位内核绑定 A/B 逐位差分（含对抗 tz 与强制失败臂探针）+ 全集性能采集，按逐 route 预测带与指令比理论上界验收（任一 case 收益超理论上界即怀疑测量假象）

## 6. LLM 前置问题

- 目标实现是否满足：发射代价标定已完成：增量 chunk 成本 ≈ 轮体指令数×chunk 轮数/64 lane（无 dominant 指令、无编译器 CSE 塌缩），即轮体按 ~1 op/cycle 发射吞吐运行——否则落入 NEG-ELEM-VEC-OPCOUNT-NO-GAIN 边界？
- 目标实现是否满足：轮体中存在为强后置条件（如『剥离后必奇』）设计的多级软件模拟阶梯，而被剥离量分布集中于小值（几何/幂律），使宽度层级冗余？
- 目标实现是否满足：存在可保持收敛不变量与吸收态的等价收缩形式（如奇偶交换），替换后每轮指令数下降而收敛轮数近似不变（需分布级仿真验证 chunk 档位不升或升档代价可被吸收）？
- 是否命中排除条件：阶梯宽度集合缺尾部宽度 1 级的组合已被仿真证伪（如 {16,1}/{2}/{4}/{8}/{4,2}/{8,2}/{6,2}：92-100% slice chunk 升档、31-bit 对抗轮数越界 MAX_ROUNDS 即静默错误结果），不得重试；同机制降级参数 {4,2,1}（19 op）保留为一次修正重试选项？

## 7. 验收标准

正确性：

- round 3 verify ok=true 20/20（run.json.all_cases 全量，跨模板共享轮体），fingerprint kernel b9ca42ec2533eeb1 与 build/verify/安装态四字段闭环
- A/B 逐位差分（rounds/003/probe/ab_evidence.json，双相位内核绑定：phase A=parent 2cc7b7d9 / phase B=round-3 b9ca42ec）：45 探针 48,931,648 元素，43 探针位精确；2 探针共 1832 处差异逐点复核 100% 位于 tile 内 slice 序号>=1 的首元素且前一 256-slice 含 INT32_MIN lane——全部归因 parent 既有 wzeroBuf_[0] done-scratch 别名缺陷（golden 交叉：两 kernel 同错 24,444 / 仅 parent 凑对 149 / 仅新凑对 130），缺陷包络外 48,929,816 元素位精确
- 轮数上界独立复算（穷举到 b13 + 结构化对抗扫描 + 16-bit 域全穷举 1.07G 对）：新轮体 31-bit 对抗 max=37 < MAX_ROUNDS 64（裕度 1.73x）、16-bit 域 max=19 < 47（裕度 2.47x）；模型等价性 1.19G 对 parent/新轮体最终输出 diff=0（非 INT_MIN 输入全部收敛且与 |gcd| 参考一致）

性能：

- 20/20 case 全部 improved、0 regressed、0 missing；20-case 时延加权 incremental 1.4503x（机制确认线 1.15x，名义预测带 [1.28,1.42] 上沿 +2.1%，归因 V 管发射资源冲突缓解的超线性效应与固定停顿项缩短）、cumulative vs baseline 1.6908x
- 逐 case 收益全部被 26/15=1.7333x 的 chunk 项理论天花板包住（最深 chunk case 1.6924x 恰为全场最大），排除测量假象；route 级 R1-R8 全部 1.19-1.66x，广播驻留 route 落带内（其固定 gather 开销不随轮体变化）
- 1-chunk case 无任何 chunk 升档签名（cyc/elem 下降 ~2.0）；vec_time 降幅大于总时长降幅且随 chunk 深度单调（compute-only 改动指纹）；MTE2 绝对时长持平（零新增 GM 流量）、Block Num 全部 64、op_host 逐字节不变（tiling/route 划分零变化）

回滚信号：

- 20-case incremental < 1.15x（指令数->周期转化假设失败，NEG-ELEM-VEC-OPCOUNT-NO-GAIN 型边界成立）或任一 case < 0.95x（含 1-chunk case cyc/elem 高于 parent 的升档回归）
- 任一 A/B 逐位差分非零且不能 100% 归因到已登记的 parent 既有缺陷包络（逐点格点复核 + golden 交叉是判据），或对抗 tz 探针在既有 MAX_ROUNDS 内不收敛/结果错误
- 任一 route 跌破逐 route 预测带下带（升档代价未被吸收），或结构不变量破坏（Block Num 变化、MTE2 绝对时长上涨、host 字节变化）

## 8. 分类与证据

- Classification：`validated_strategy`
- Generality：`op_class`
- Related anti-patterns：无

- gcd-20260826_142703-b3c56c（round=3, status=accepted）

## 检索卡（短卡）

动作：将尾零阶梯缩为 {2,1}，每轮最多剥三位；若剥离后 B 仍为偶，则交换以维持不变量。
适用：轮体指令均真实发射，且无 dominant 指令、无 CSE 塌缩。
限制：不得随意下调 MAX_ROUNDS；必须用穷举及结构化对抗输入验证迭代上界。
范围：elementwise-arithmetic 的 Stein 收缩轮体。
检索词：Stein、两级尾零剥离、{2,1}、交换 Select、MAX_ROUNDS。
机会：软件模拟 tz 阶梯存在纯发射成本及冗余宽度层级。
代价：阶梯宽度错误会使 chunk 大量升档，甚至越过 MAX_ROUNDS。

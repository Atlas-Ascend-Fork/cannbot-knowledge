---
type: Optimization
title: 尾部退化维阶段卸载到向量核并与相邻向量级融合（n≪分形宽的 GEMV）
description: 把链上退化维矩阵级（N≪分形宽的 GEMV）整体卸载到上游向量级同一 pass，与下游点态融合后直接写出，删除该级与 workspace 往返及两对跨核标志。
tags:
- task.optimization
- topic.programming_model.execution_unit.cube
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/cv-A5/41-gemv-tail-stage-aiv-offload-fusion.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

# 性能优化策略：尾部退化维阶段卸载到向量核并与相邻向量级融合（n≪分形宽的 GEMV）

> **来源：A5 自由探索实测（lrlrls-sigmoid，2026-09-15，107 裸机）**
> direction_key: `cv-serial-chain-latency::c2-gemv-aiv-offload-v2v3-fusion::tail-projection-stage`
> 证据：<AOA_ROOT>/campaigns/lrlrls-sigmoid-a5-107-20260915-opencode/framework/aoa_out/linear_relu_linear_relu_linear_sigmoid_custom/loop_<run-id>/explore/direction_001/
> 实测：1.0897 x（geomean 19.1883→17.6088us，23 个 case 全部改善，worst 0.881 / best 0.957，46 对逐 case 全部 A<B）；精度 22/22。

## 原理

链式算子的尾投影阶段是 **N=1 的 GEMV**，但矩阵单元按最小分形宽度（n=16）掩码执行，**浪费 15/16 的 cube 工作**；同时该阶段的输入来自上一级、输出喂给下一级，中间结果经 GM workspace 往返并配两对跨核标志。

机制：把该阶段**整体卸载到向量核**，并与相邻向量级融合——

1. 上游向量级在 UB 内算完后，**同一 pass 内**做逐行 fp32 累加 GEMV（`×weight + bias`），按 golden 舍入链处理（**先舍回输出 dtype 再加 bias**），继续做完下游点态（如 sigmoid）后直接写输出——即 V2/V3 融合；
2. 删除该级本身、中间结果的 GM workspace 双向往返（实测每 tile·core 约 40KB×2 方向）、以及两对跨核标志（H2Ready/H2Free、Tmp3Ready/Tmp3Free）；
3. AIC 每 tile 的串行工作降为 C0+C1，逐 tile 关键路径由 `C1→V2→C2→V3` 缩短为 `C1→V2*`。

## 性能问题模式（哪些 profiling 信号说明该用）

- 链上某级的输出维度**远小于矩阵分形宽**（如 N=1/2/4 而分形 n=16），该级在 AIC 上按掩码执行、cube 利用率是 1/16 量级。
- 该级的前后都是向量级，且中间量经 GM workspace 往返（有 Ready/Free 标志对）。
- 逐 tile 关键路径上该级是串行链的一环（AIC 队列里它排在最后，且它的输入依赖上游向量级）。
- 该级绝对耗时不大但处在关键路径上（延迟型，不是吞吐型）。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **舍入链必须与 golden 一致**：先按输出 dtype 舍回、再加 bias（实测该顺序是过门前提）；若 golden 是 fp32 域累加后一次舍入，必须照做，不能凭直觉合并。
2. **累加域与累加序改变须实测**：向量核逐行 fp32 累加与 cube 的 K 维累加序不同，精度面必须用全量用例实测（实测 22/22 通过），不得只做理论论证。
3. **UB 预算与指令数上升**：融合后该向量级的 UB 占用与每行指令数上升，须确认它没有变成新的顶（若向量级本就贴顶，本条可能不赚）。
4. **workspace 与标志删除要清干净**：删掉的两对跨核标志与 workspace 必须逐 case 确认无残留引用（编译期 + 运行期各一处），否则会出现「读到上一轮陈旧数据」的偶发错误。
5. **卸载粒度是整级**：只在该级是「退化维 + 前后都是向量级」时成立；若该级还承担其它已发布消费者（例如中间量被别处读），不得删除其 workspace。
6. **量化/低精度输出时的中间精度**：若输出是低精度 dtype，中间累加仍须在 fp32 域完成再舍回，避免在低精度域累加。

## 泛化条件（dtype / shape / pipeline / 算子类型）

- shape：该级输出维度 N ≪ 分形宽（分形浪费倍数 ≥ 4 时收益明显）；上游/下游均为向量级的链式形态收益最大。
- dtype：与输入 dtype 无关；输出 dtype 决定舍入链位置。
- 流水线：`overlap`（跨核交接）与 `aiv_vec`；对任何「链上有退化维矩阵级」的融合算子适用。
- 与 04 号卡（交接流水）的关系：04 优化交接环的深度/同步/信用以重叠生产消费；本条是**把这一级直接删掉**（连交接一起消失），当该级是退化维时为更彻底的解。
- 与 22/38 号卡（切分/归并）无关（那两张针对长归约欠铺）。

## 实施步骤（从证据里的真实 diff 抽象成通用步骤）

1. 找出链上退化维级，量出分形浪费倍数（分形宽 ÷ 实际 N）与该级在关键路径上的位置。
2. 确认该级的全部消费者与生产者：若中间量仅被紧邻的下一级消费，则删除其 GM workspace 与两对跨核标志可行。
3. 在**上游向量级的同一 pass**里插入逐行 fp32 累加 GEMV，按 golden 舍入链（先舍回输出 dtype 再加 bias）实现。
4. 把下游点态融合进同一 pass，直接写最终输出；删除原级与其 launch/同步配置。
5. 复核 UB 预算与该向量级是否成为新顶；复核无残留 workspace/flag 引用。
6. 全量精度用例通过后做配对测量，报逐 case 结果（本条实测 23/23 case 全部改善）。

## LLM 前置问题（应用前必须自问）

1. 该级输出维度相对分形宽浪费了多少倍？它在关键路径上吗（延迟型还是吞吐型）？
2. 中间量的消费者只有紧邻下一级吗？删掉 workspace 安全吗？
3. golden 的舍入链是什么顺序（先舍回还是后舍回）？
4. 累加域是 fp32 吗？改变累加序后精度面测过吗？
5. 融合后该向量级的 UB 与指令数上升多少？它会不会变成新的顶？
6. 删除的跨核标志与 workspace 引用清干净了吗（编译期 + 运行期）？

## 验收标准（编译 / 精度 / 性能判据，含噪声底口径与回退阈值）

- **构建**：编译通过；被删级的 launch/同步配置无残留（编译期 + 运行期各一处核对）。
- **精度**：全量用例通过（实测 22/22），须覆盖链式算子的全部 dtype 组合。
- **性能**：配对 geomean 超噪声底（实测 1.0897x）；**逐 case 全部改善**（实测 23/23，最差 0.881 仍为改善）。
- **零劣化判据**：无 case 回退；若某 case 因 UB 压力回退，须单列并门控。
- **回退**：舍入链无法对齐 golden、累加序改变导致精度不过、或融合后向量级成为新顶时，恢复原矩阵级与 workspace 路径。

## 检索卡（短卡）

动作：把链上退化维矩阵级（N≪分形宽的 GEMV）整体卸载到上游向量级同一 pass，与下游点态融合后直接写出，删除该级与 workspace 往返及两对跨核标志。
适用：链式算子某级输出维度 N≪矩阵分形宽（分形浪费 ≥4 倍）、前后均为向量级且中间量只被紧邻下一级消费。
限制：舍入链须与 golden 一致（先舍回输出 dtype 再加 bias）；累加序改变须实测；确认向量级未成新顶；workspace/标志引用清干净。
范围：链式算子尾部退化维矩阵级（GEMV）的跨核卸载与相邻向量级融合。
检索词：GEMV 卸载、退化维、V2/V3 融合、分形掩码浪费、舍入链、跨核标志、workspace 往返、关键路径。
机会：该级按最小分形宽掩码执行浪费 15/16 cube 工作；中间量经 GM workspace 往返并配两对标志。
代价：融合后该向量级 UB 与每行指令数上升，可能成为新顶。

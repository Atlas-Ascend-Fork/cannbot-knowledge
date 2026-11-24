---
type: Optimization
title: 成本模型铺核 + 单内核 SyncAll 归约 + tile-B 解耦
description: 小 shape 归约/聚合内核用实测成本模型铺核，并以单内核 SyncAll 收口归约、tile-B 解耦降低 halo。
tags:
- task.optimization
- topic.compute.neighborhood.convolution
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/conv-A5/02-cost-model-core-fill-single-kernel-reduce.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

# 性能优化策略：成本模型铺核 + 单内核 SyncAll 归约 + tile-B 解耦

> **来源：多任务内核评审与同构实现对照沉淀（2026-11-11）**
> 证据形态：四个子机制（实测成本模型选核、单内核归约收口、tile 维度解耦、VF 装载与 mask 冗余）已在多任务同构交付中得到实测验证（铺核数提升、launch 次数减少、halo 放大系数下降均有效）；本仓任务为首次引入，须按验收标准盲调
> 参考量级：同类改造中 halo 读放大可由 25~33% 降到约 6%；小 case 加速与铺核数/launch 次数收益以目标任务实测为准

## 原理

归约/聚合类 Vector 内核常见的四个结构性保守决策，是「小 case 慢、大 case 不到顶」的主要来源：

1. **静态门槛压死小 case 铺核**：用「最小工作量/核」门槛（如工作量 < 32K 元素压到单核）+ 固定列宽常数（如 HC 固定 384，不足则单块）——小 shape 整卡单核跑，启动延迟占比失控。推荐形态：无静态门槛，tile 宽度按枚举步进搜索；核数由**实测回填的周期成本模型**（向量 ops 周期 + 搬运周期 + halo/workspace 惩罚 + 读回惩罚）逐 shape 选出，halo/workspace 占比 >5% 的候选直接剔除，小 shape 也铺满 min(样本维, 核数)。
2. **双 kernel + GM workspace 往返**：跨核归约时部分和落 GM workspace，再二次发射归约 kernel——多一次 launch + 全量 fp32 写读往返（`__vector__` 载体不能核间同步，被迫如此）。推荐形态：K1 改 `__mix__(0,1) __schedmode__(1)` 保留调度模块并获得核间同步能力，单内核内 `SyncAll<true>()` 后根核按序累加收口；成本模型显式计入读回惩罚项（小范围部分和读回 ≈µs 量级/核）。
3. **tile 结构与 batch 耦合**：UB 预算公式含 batch 因子时，tile 行数与 B 耦合，大 B 时每 tile 行数被压小，halo 读放大 2/(Tc+2) 可达 25~33%。推荐形态：b 循环移到 tile 外层，每 tile 只装单 b 的 Tt 行，Tt 由 UB 预算闭式解给出、不受 B 影响，halo ≈6%。「加宽装载块」类迭代若出现「加宽即回退」的负结果，根因通常就是该耦合（结构问题而非参数问题）。
4. **VF 装载与 mask 冗余**：滑动窗口类 VF 每 N 输出组从 UB 重装 N+k 行（相邻组重叠 k 行，装载放大 (N+k)/N），mask 每行多条指令（BRC 装载+Compares+Select）。推荐形态：轮流装入不同的具名寄存器（依赖编译器寄存器改名，**禁止显式寄存器搬移**——显式搬移+底部 advance 装载会引入串行依赖，实测可劣化 20%+）每行仅装一次；行标志在装载点以「1 字节/32B 块」DataCopyPad 原位展开成 0/1 值，mask 化简为 BRC+Mul 两条。

## 性能问题模式（哪些 profiling 信号说明该用）

- 小 shape case 的 kernel 时长接近启动/固定开销地板，且启核数远小于核数（门槛条件命中即单核）。
- 存在第二次 kernel 发射（归约 kernel），且主 kernel 末期向 GM workspace 写部分和、二次 kernel 全量读回。
- tile 行数被 UB 预算公式里的 batch 因子压小，halo/重叠读占比 >10%。
- 加宽装载块的迭代出现「加宽即回退」的负结果且无法只改一个参数。
- VF 循环中相邻迭代重复装载同一 UB 行（重叠窗口放大系数 >1），mask 路径每行指令数 ≥3。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **`__mix__` 改造必须保留调度模块声明**（`__schedmode__`）：有实测记录的坑——bisheng 编译器 `KERNEL_TASK_TYPE_DEFAULT` 与 mix 模式冲突会静默改变调度行为。
2. **SyncAll 前所有核必须已完成部分和写出**，根核归约顺序必须与分核映射确定同序；SyncAll 属全核 Barrier，不得放在分叉控制流内。
3. **滚动窗口装载禁止显式寄存器搬移**：该形态（显式搬移 + 底部 advance 装载）因串行依赖有实测 20%+ 劣化记录；正确形态是轮流装入不同寄存器变量、依赖编译器寄存器改名，若编译器未做改名则该子项放弃。
4. **mask 改 0/1 行标志乘法必须保持零值与恢复语义**：标志展开的字节布局（1 字节/32B 块）与 DataCopyPad 原位展开路径须与行边界语义逐 case 对齐。
5. **成本模型必须实测回填**：周期系数、读回惩罚、块启动成本须用真实 case 标定，不得拍脑袋设常数；halo+workspace 占比 >5% 的候选直接剔除。

## 泛化条件（dtype / shape / 流水线 / 算子类型）

- 流水线：aiv_vec 主导的多核归约/聚合类算子（gather+reduce、segment 归约、加权聚合）。
- shape：小 shape（铺核不足）与大 B（tile 耦合）两端收益最大；中大型且 B=1 的 case 中性。
- dtype：与 dtype 无关（结构策略）；换 dtype 只影响成本模型系数，须重标定。
- 前提：归约链可表达为「部分和 + 确定性合并」；若合并顺序影响浮点结果，须用固定树形合并保逐位一致。
- 与静态 tiling 枚举类策略正交可叠加：本策略替换「选核与内核组织」，不改变块内计算。

## 实施步骤

1. 统计小 case 的门槛命中情况（门槛值 × 最小 shape），确认铺核不足是当前病灶（启核数 vs 核数）。
2. 移除静态门槛，实现周期成本模型：向量 ops 周期 + 搬运周期 + halo/workspace 惩罚 + 读回惩罚，系数用 2~3 个真实 case 实测回填；候选含 halo+ws>5% 者剔除。
3. 主内核属性改 `__mix__(0,1)` 并保留 `__schedmode__`，归约 kernel 改为 SyncAll 后根核按序累加；删除 workspace 通路与第二次发射；验证编译器任务类型冲突。
4. tile 结构解耦 batch：b 循环外移到 tile 层，Tt 按 UB 预算闭式解取上限，halo 摊薄；重新枚举候选并过成本模型。
5. VF 装载改轮流装入滚动窗口（禁显式搬移，编译器不改名则放弃）；mask 改装载点 0/1 行标志展开 + BRC+Mul。
6. 全量精度用例过门（重点：合并核数与合并 kernel 后的浮点求和顺序变化），再走平衡交替配对复测。

## LLM 前置问题（应用前必须自问）

1. 当前门槛条件下有多少个 case 命中单核/少核？占性能失分的比例？
2. 内核当前载体属性是否允许核间同步？改 `__mix__` 后编译器任务类型是否冲突（查 bisheng 文档或实测）？
3. 成本模型的周期系数来自哪里？是实测回填还是估算？读回惩罚是否计入？
4. 合并归约 kernel 后浮点求和顺序变了，哪些 case 对顺序敏感（精度护栏是否会破）？
5. 编译器对轮流装载是否做寄存器改名？如何验证（看汇编寄存器分配）？
6. tile 解耦后 UB 总预算是否仍守恒（双缓冲份数计入）？

## 验收标准

- **构建**：编译通过；mix 属性与调度模式在目标编译器上无冲突告警。
- **精度**：全量用例与基线一致一次通过；对求和顺序敏感的 case 单独核对（必要时固定树形合并）。
- **性能**：小 case（原门槛命中组）加速显著；平衡交替配对 geomean 超噪声底；单 case 回退 <3%。
- **归因**：收益归因于铺核数上升、launch 次数减少、halo 放大系数下降三项，逐项用启核数/发射次数/搬运量对比确认。
- **回退**：SyncAll 死锁/编译冲突、滚动窗口编译器未改名（劣化>5%）、成本模型候选全被剔除时回退旧结构。

## 检索卡（短卡）

动作：小 shape 用实测回填的周期成本模型枚举铺核（去「最小工作量/核」静态门槛与固定列宽常数），归约收口并入同一内核（__mix__(0,1)+SyncAll 根核按序累加）替代双 kernel GM workspace 往返；tile 与 batch 解耦（b 外移，Tt 按 UB 预算闭式解取上限）；VF 装载改轮流装入不同寄存器的滚动窗口，mask 改装载点 0/1 行标志展开
适用：aiv_vec 主导的多核归约/聚合类算子；小 shape 铺核不足、大 B 压小 tile 行数、存在第二次归约 kernel 发射
限制：SyncAll 前全核须完成部分和写出且根核顺序确定；滚动窗口依赖编译器寄存器改名，未改名则放弃；成本模型系数须实测回填
范围：gather+reduce、segment 归约、加权聚合类内核的核分配与内核组织
检索词：成本模型铺核、SyncAll、__mix__、静态门槛、tile 解耦、滚动窗口、workspace 往返
机会：小 case 单核/少核+双 kernel launch+全量 fp32 往返+halo 放大并存
代价：架构级改造，编译器任务类型冲突须实测；求和顺序敏感 case 需固定树形合并

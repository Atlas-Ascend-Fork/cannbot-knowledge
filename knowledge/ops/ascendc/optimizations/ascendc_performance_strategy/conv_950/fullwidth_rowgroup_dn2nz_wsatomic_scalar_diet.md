---
type: Optimization
title: fullWidth 整行组 L1 分段 + wsAtomic 单写者协议 + 标量流瘦身（Dn2Nz 事务粒度重组织）
description: 用 fullWidth 整行组 staging 让 Dn2Nz 恒走单矩阵快路径，配合 wsAtomic 单写者协议与标量流瘦身降低固定税。
tags:
- task.optimization
- topic.compute.neighborhood.convolution
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/conv-A5/01-fullwidth-rowgroup-dn2nz-wsatomic-scalar-diet.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-20T06:35:03Z'
platforms:
- '950'
---

# 性能优化策略：fullWidth 整行组 L1 分段 + wsAtomic 单写者协议 + 标量流瘦身（Dn2Nz 事务粒度重组织）

> **来源：conv/backprop 类内核评审与同构实现对照沉淀（2026-11-11）**
> 证据形态：四个子机制（fullWidth 事务合并、单写者写回协议、标量流三件套、波次 floor 候选）在同类交付中实测有效——MTE2 util 提升、memset/原子税消除、尾零成本下降均有数据背书；源策略仅保留定性收益结论，未保留逐 case 数字（源文件见 frontmatter sources），量化幅度须在目标任务实测
> 平移到其它 conv/backprop 任务时按红线复核后套用，收益幅度以目标任务实测为准

## 原理

「Dn2Nz 排布转换带宽地板」不是物理极限，而是**事务粒度**问题——同一转换按大粒度事务组织即可打穿。四个子项：

1. **fullWidth 整行组 staging，Dn2Nz 恒走单矩阵快路径**：常见保守形态允许窗口切宽（woL0<wout）的分块候选，窗口非全宽时每输入行一个 Dn2Nz 描述符做 2D 散排搬运（grad 侧同理）——描述符数 = 行数，MTE2 发射密度爆炸，宏观表现为「带宽地板」。推荐形态：L1 K-segment staging 要求块跨满整个 Wo（fullWidth=整行组），整行组在 GM 位置轴连续 → 搬运恒为 `dnNum=1` 单矩阵快路径，内层子 chunk 只重指 Load 起点与 Mmad.k；per-channel burst 随块宽等比放大、描述符数除以同因子，MTE2 util 显著抬升。
2. **wsAtomic 单写者协议**：常见保守形态是无条件 memset 整个 fp32 workspace + 无条件 `SetAtomicAdd`（GM 读改写）——即使 posSplits==1 每元素单写者也照付全量清零任务 + 原子税。推荐形态：tiling 产出 `wsAtomic` 字段：M-mode 且 posSplits==1（单写者、纯覆写）时 =0，CopyOut 条件跳过 SetAtomicAdd、plugin 跳过 memset，且 zero fill 成本计入 posSplits 决策（小 case 直接选串行——少一个设备任务、少一次 HBM 清零流量、Fixpipe 纯写）。**用调度保证单写者消灭冲突面，而不是用同步消化冲突。**
3. **标量流三件套**：常见保守形态是每 chunk 逐字段重建全部参数结构（数十次标量写）+ TQue 每子 chunk 成对 flag + 尾零整槽 InitConstValue+PIPE_ALL 排空。推荐形态：Init 期打包所有 chunk 不变的描述符半段（每 chunk 2~4 次标量写）；blk 路径手驱 L0 双 buffer、一对 event 盖全部依赖路（flag 次数减半）；尾零一次跨步 fill 只补 K 尾并按 stage 记账（清零+排空从每次 fill 一次降到每 stage 一次）。原则：「标量流与工作量成正比而非循环次数成正比」。
4. **波次 floor 候选**：常见保守形态的分核只按 ceil 填核，「刚超一波」时多付一整波块启动成本（µs/块量级）。推荐形态：候选集追加 floor 候选 `w*coreNum/jobs`，M-mode 在串行/满波候选间选优并与 wsAtomic 联动。

## 性能问题模式（哪些 profiling 信号说明该用）

- conv/backprop 类 Dn2Nz 随路转换搬运，MTE2 pipe 占比高而矩阵 pipe 低，且搬运描述符数/主循环迭代 ≫1（per-row 散排形态）。
- tiling 候选集含窗口切宽（woL0<wout）且无 fullWidth 约束。
- plugin 存在无条件 workspace memset；kernel 存在无条件 SetAtomicAdd；分核策略存在「单写者」形态却未利用。
- 小 case（µs 量级地板）kernel 时长被标量初始化/每 chunk 重建描述符/TQue flag 占比抬高（标量流与循环次数成正比）。
- 分核数刚超整波（jobs 与 coreNum 非整除关系）时性能阶跃回退。

## 正确性红线（什么情况下禁止用 / 必须回退）

1. **fullWidth staging 的前提是块跨满整 Wo**：位置轴 GM 连续才可 `dnNum=1`；窗口被切（woL0<wout）时禁用单矩阵快路径，保持 per-row 散排或改块边界。代价是块数上升，用 kBlockOverheadNs 时间模型裁决，不得无约束放宽。
2. **wsAtomic=0 的前提是严格单写者**：每输出元素恰好一个核写入（M-mode posSplits==1 且无跨核重叠）；HW-mode 因块可能整块跳过（纯 padding 区域），必须保留 atomic+memset 旧路径。
3. **K 尾 stale 行不可容忍**：整槽预清零 + 搬运排空旧路径在 K 尾/尾带场景必须保留；跨步尾填充只负责 [curM, kAligned) 尾，且按 stage 记账防重复清零与漏清零。
4. **event 对必须覆盖全部依赖路**：手驱双 buffer 少 flag 的前提是依赖图完备；漏盖一路即数据竞争（静默错误，评测用例未必暴露）。
5. **描述符打包只折叠「不变半段」**：随 chunk 变化的字段（起点/步长/k）不得进打包；打包错误即整面板错位（布局错误，排空重试无效）。

## 泛化条件（dtype / shape / 流水线 / 算子类型）

- 流水线：aic_mte2（描述符密度/发射瓶颈）+ aic_fixpipe（原子税/memset 税）+ aic_scalar（标量流瓶颈）三类信号并存或其一主导。
- 算子：一切「GM→L1 分形重排（Dn2Nz/Nd2Nz）随路转换」的 conv/backprop/matmul 类内核；im2col 类（Load3D）同理适用 fullWidth 约束。
- shape：大 case 吃子项 1（事务合并），小 case 吃子项 2/3/4（固定税削减）；两者正交可分步采纳。
- dtype：与 dtype 无关；换 dtype 须复核描述符字段合法性与分形重叠条件（对齐 [bpanel_wide_nd2nz_kblock_copy.md](../cv_950/bpanel_wide_nd2nz_kblock_copy.md) 的红线 1）。
- 与 cv_950/bpanel_wide_nd2nz_kblock_copy 的关系：该卡管「面板怎么搬更宽」，本条管「块边界怎么切才能恒走宽路径」+ 固定税；先按本条切块，再按该卡合并搬运。

## 实施步骤

1. 统计当前块候选的 fullWidth 占比与每迭代 Dn2Nz 描述符数，确认 per-row 散排是 MTE2 热点（对照 msprof aic_mte2 占比）。
2. tiling 候选集加 fullWidth（woDim=1）约束，引入整行组 L1 K-segment staging；Dn2Nz 恒走 dnNum=1；块数上升用 kBlockOverheadNs 模型裁决。
3. tiling 增加 wsAtomic 字段与 zero fill 成本项（kMemSetTaskNs+wsElems×4/64）：M-mode posSplits==1 → 纯覆写 Fixpipe + 跳过 memset；HW-mode 保留 atomic+memset。
4. 标量流三件套：Init 期打包不变描述符半段；L0 双 buffer 手驱 event 对（覆盖全部依赖路）；尾零改跨步尾填充 + stage 级记账。
5. 候选集增补 floor 候选，ceil/floor/串行三方在块启动成本模型下竞争，与 wsAtomic 联动。
6. 全量精度用例过门（重点：K 尾、纯 padding 块、跨核单写者无重叠验证），平衡交替配对复测。

## LLM 前置问题（应用前必须自问）

1. 当前每主循环迭代 Dn2Nz 描述符数多少？fullWidth 候选占比多少？MTE2 util 实测多少？
2. 分核后是否存在每元素单写者的形态？memset/atomic 的无条件成本每次 launch 多少（清零任务固定成本+流量项估算）？
3. 每子 chunk 标量写次数与 flag 次数各多少？打包后剩多少？
4. 块 fullWidth 化后块数上升多少？kBlockOverheadNs 模型下净收益为正吗？
5. K 尾/尾带/纯 padding 块的旧清零路径是否全部保留并条件化？event 对覆盖的依赖路是否列全？
6. 平台差异：A3/其它 SoC 上 SetAtomicAdd、Dn2Nz 描述符语义是否一致（迁移须重验）？

## 验收标准

- **构建**：编译通过；描述符打包后字段合法性静态核对（变字段未误入打包）。
- **精度**：全量用例一次通过；K 尾/纯 padding/单写者覆盖 case 单独核对——评测用例未暴露不等于无缺陷，静默数据竞争类缺陷必须靠覆盖 case 兜底。
- **性能**：大 case MTE2 描述符数下降一个量级（随块宽等比放大）；小 case 消除 1 次设备任务（memset）与原子税；平衡交替配对 geomean 超噪声底；单 case 回退 <3%。
- **归因**：四子项分别归因（MTE2 util / memset 任务数 / 每子 chunk 标量周期 / 波次数），禁止混算。
- **回退**：单写者前提破坏、fullWidth 净收益为负、event 依赖覆盖不全、K 尾精度失败时回退对应子项。

## 检索卡（短卡）

动作：块候选约束 fullWidth（跨满整个 Wo，位置轴 GM 连续）+整行组 L1 staging，使 Dn2Nz 随路转换恒走 dnNum=1 单矩阵快路径，内层子 chunk 只重指 Load 起点与 Mmad.k；tiling 产出 wsAtomic 字段，每元素单写者（posSplits==1）时=0，纯覆写 Fixpipe 并跳过 workspace memset 与 SetAtomicAdd；标量流三件套：Init 打包 chunk 不变描述符半段、L0 双 buffer 手驱 event 对、K 尾零改跨步填充+stage 记账；psCand 增补 floor 候选与串行选项
适用：GM→L1 分形重排随路转换的 conv/backprop/matmul 类内核；MTE2 描述符密度高、无条件 memset/原子税或标量流随循环数膨胀
限制：窗口被切（woL0<wout）禁用单矩阵快路径；HW-mode 块可整块跳过须保留 atomic+memset；K 尾 stale 行旧清零路径必须保留；event 对漏盖依赖路即静默数据竞争
范围：conv/backprop 类内核的块边界组织、写回协议与标量流
检索词：Dn2Nz、dnNum、fullWidth、L1 staging、wsAtomic、SetAtomicAdd、memset、描述符打包、floor 波次
机会：per-row 描述符散排+无条件清零原子加+每 chunk 标量重建并存
代价：fullWidth 化块数上升须成本模型裁决；单写者前提破坏须回退；布局错误排空重试无效

# 优化机制卡

OpsTune 机制卡索引：verdict 判定完成后按 findings 的机制标识路由到具体机制卡（证据先行：没有判定不加载机制卡）。机制卡八要素（原理 / 适用前提 / 实施形态 / 预期收益 / 架构限制 / 精度风险 / 验证与回滚 / 失效边界）由各卡正文承载。

## rule → 机制路由表

| rule_id | 机制卡 | 一句话机制 |
| --- | --- | --- |
| L1_MTE2_BOUND / L1_MTE3_BOUND / L1_FIXP_BOUND | data_copy | 真饱和→数据量/复用；假 bound→对齐/合并小搬运 |
| L1_VEC_BOUND | api_usage + ascendc_regbase_vf（A5 深度档） | UB 融合/减 Cast/融合指令；VF 范式 |
| L1_CUBE_BOUND | ascendc_tiling | tiling / L1 复用 / L0C 累加 |
| L1_SCALAR_BOUND | api_usage | 标量削减六法 |
| L1_LATENCY_SYNC_SUSPECT / L1_SERIAL_NO_OVERLAP | pipeline | Double Buffer / 流水掩盖 / 同步删减 |
| L2_CORE_TAIL / L2_IMBALANCE_* / L2_UNDERUTILIZATION | ascendc_tiling | 尾块均衡 / swat / Block Dim 提升 |
| L2_HEAD_OVERHEAD | api_usage | 减核 / 缩 TilingData / TPipe 外置 |
| L3_MC2_*（全档） | mc2_fusion | Local Matmul 首选 + 通信掩盖 + 膨胀控制 |
| L3 配平环节 | mc2_fusion | TilingData 驱动系统搜索（四剪枝 + Top-N） |
| L3_MTE2_POLLUTED | mc2_fusion | 单核访存机制无效，改道通信掩盖 |
| L3_RANK_IMBALANCE | mc2_fusion | 跨 rank 长尾排查 |
| L0_ICACHE_MISS | api_usage | 代码布局/分支整理 |
| L0_L2_LOW_HIT | memory_hierarchy | CacheMode 二分 + 工作集切分 |
| L0_STALL_DOMINANT | pipeline | stall 枚举 → 对应流水机制 |

## 跨 DSL 实施边界

机制卡实施细节以 Ascend C 为准；Triton / CATLASS / TileLang 的等价原语以工具仓机制索引的跨 DSL 原语对照表为路由线索、对应 DSL 专项文档为深度参考，不按本目录卡字面照搬。

## 已知覆盖缺口

- FA 类混合绑核（AIC+AIV CrossCore mode2）：跨 j 迭代 GM buffer ping-pong、flag 粒度放宽、GM→L1 滚动预取只有通用原理，实施细节自行论证 + 提高验证强度；
- MoE routing / key-value sort / gather-scatter / histogram（SIMT 不规则读写）；
- Double Buffer 非 TQue 形态（ping-pong event id + prologue/drain 自行论证）。

- [优化机制卡：API 使用与计算量优化（标量削减六法 / Cast 削减 / 融合指令 / 头开销）](api_usage.md)：标量削减六法（缩小 TilingData/减少核数/TPipe 外置/循环不变量外提/标量向量化/地址计算优化）对应 L1_SCALAR_BOUND 与 L2_HEAD_OVERHEAD；Vec bound 的 Cast 削减（fp32 ratio 高 → 减 Cast 或批量转换）；mul+add 等融合指令查表合并；深度 VEC bound 的减少计算量策略。
- [优化机制卡：RegBase / SIMD VF 向量范式（A5 寄存器驻留计算）](ascendc_regbase_vf.md)：A5（dav-3510）RegBase 范式把数据驻留 RegTensor 用 SIMD VF 指令直接计算，绕开 UB 往返与队列同步；适用多步短生命周期计算（量化/激活/归一化组合）与 UB 带宽约束的 Vector 算子；编译修复顺序固定四步（命名空间别名→API 签名→include 路径→最后才降级对应分支），VF 舍入行为与高层 API 可能不同须做数值稳定性验证。仅 A5，A2/A3 保留兼容分支禁止下沉此路径。
- [优化机制卡：Ascend C Tiling 优化（切分与多核负载）](ascendc_tiling.md)：切核不足时 Block Dim 提升是最低垂果实（4 核→20 核案例利用率 10%→50%）但 Task <25us 时增核放大头开销；核间长尾走尾块均衡（swat 蛇形行窗口+尾块合并+末轮再切分）；MN 欠并行走 streamk（切 K 到空闲核）；多机制候选冲突时先做三层联动 tiling 建模再选单变量。
- [优化机制卡：数据搬运优化（MTE2/MTE3 真假 bound 二分 + 11 项机制清单）](data_copy.md)：先分真假 bound 再选机制：实际耗时≈理论（active_bw ≥峰值 80%）为真带宽饱和，走数据量削减（增大搬运量/L2 CacheMode/UB 常驻/增大 tile）；active_bw <40% 峰值为假 bound，走搬运组织（512B 对齐/合并小搬运/避免同地址多核访问）；11 项机制清单各带适用条件与检查方式；MC² 算子先过 L3_MTE2_POLLUTED。
- [优化机制卡：MC² 通算融合（Local Matmul 首选 + 通信掩盖 + 膨胀控制）](mc2_fusion.md)：MC² 优化固定顺序：① Local Matmul 首选（本 rank 数据无需通信，独立计算与通信重叠，任何 R 档位先做）→ ② R 值与 TilingData 驱动的流水配平系统搜索（禁止 1-2 个经验值交付）→ ③ matmul 计算效率（仅计算 bound）；模式选型按执行顺序（Pattern A 通信后计算→前置独立；Pattern B 计算后通信→后置独立），Local 数据段 M 维切分必须连续。
- [优化机制卡：存储层次优化（L2/UB/L1/L0 复用与 Bank 冲突规避）](memory_hierarchy.md)：按存储层次选机制：L2 CacheMode 二分（有复用开 NORMAL、流式数据 DISABLE 防污染）、L1 小侧矩阵驻留（fullload）、L0C 累加不回写、UB 常驻复用（TBuf 替代重复 MTE2）、寄存器驻留；Bank 冲突规避按判定字段（bankgroup/bank/资源/MTE 四类冲突）对应修法。
- [优化机制卡：流水优化（Double Buffer / 流水掩盖 / 同步降本）](pipeline.md)：单缓冲下 MTE 搬运与计算串行（pipe 求和≈100% 但各 pipe 均不满）判串行无重叠指纹，双缓冲把搬运与上tile计算重叠，理想收益上界 ≈ max(t_copy,t_compute)/(t_copy+t_compute)；分场景实施形态（TQue 标准流水 / 裸 MTE ping-pong / Cube-Vector 混合 workspace 份数 / AIC:AIV 配比 / 同步删减）；无 Bound 形态六机制与回滚条件。

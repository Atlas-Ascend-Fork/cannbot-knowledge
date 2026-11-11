# 判定规则语义

OpsTune 分层瓶颈判定规则（L0 指令 / L1 单核 / L2 核间 / L3 卡间）的语义卡：判定条件、反证条目、阈值溯源与机制路由。机器真源为 asc-tools 固定提交 `14714fd` 的 `ops-verdict/rules/` 规则 YAML（判定引擎按其求值）；本目录卡片保存「为什么这样判、阈值哪来的、改了会怎样」，阈值以 YAML 为准，卡片变更不自动生效。

- [L0 指令级判定规则语义（ICache 缺失 / L2 命中率 / PC 采样 stall 枚举）](l0_instruction_level_rules.md)：icache_miss >15%、L2 hit <50%、top stall >40% 三条；无 Roofline 产物不得推断 Roofline Bound；L0_STALL_DOMINANT 为占位规则（draft）。
- [L1 单核层瓶颈判定规则语义（MTE2/Cube/Vec/MTE3/FixP/Scalar/低占用/串行指纹）](l1_single_core_bound_rules.md)：pipe 级 Bound 八条规则与真带宽饱和/假 bound/对齐等反证；串行无重叠指纹（max<70% 且求和 85~115%）是 Double Buffer 首选信号。
- [L2 核间层瓶颈判定规则语义（长尾/离散度/切核不足/头开销/host 下发）](l2_inter_core_bound_rules.md)：max>mean×1.25 长尾、(max-min)/max 离散度两档、切核不足（<物理核 33%）与短任务反证、头开销 >30%、host 下发阻塞（规划态）。
- [L3 卡间层 MC² 通算比判定规则语义（R 值五档 + MTE2 污染路由 + rank 不均衡）](l3_inter_card_mc2_rules.md)：隔离测试 R=T_compute/T_comm 五档判定；MTE2 污染命中时禁用单核访存规则改道通信掩盖；仅 950 实测标定。

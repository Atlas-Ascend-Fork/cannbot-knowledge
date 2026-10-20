# MoE 跨卡 dispatch 优化

融合 MoE 算子在专家并行（EP）下的跨卡 token 分发路径上沉淀的优化经验，
含机制、实测证据与**不适用边界**。

## 知识卡

- [按 (token, expert) 取数的冗余与本地暂存](per_token_expert_fetch_redundancy_local_staging.md)：跨卡 dispatch 按 (token,expert) 粒度取数，冗余 `topk×(LOCAL_E/E)`，首用本地暂存消除；arch35/950 实测 5/5 shape ratio>1.0、几何平均 1.1325、输出逐位相同，并含"大 FFN 下被 GMM1 遮蔽故无收益"的不适用边界。

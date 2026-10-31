# 模型推理优化

先按优化规则判断条件，再查看具体案例、反模式和基准观测。完整操作流程位于指南目录中的优化流程。

- [优化规则](rules/index.md)：共 103 张知识卡（如 950(Ascend950) MXFP8 fused-MoE：进分组 matmul 前激活量化 scale 必须打包成 [M, N//2, 2] 并中心化收口、aclgraph decode 稳态期优化：warm-up 后 skip_guard_eval_unsafe 跳 guard 复评 + custom op reinplace 映射、Attention-FFN 解耦（AFD）部署：把 MoE/FFN 剥到独立 rank，Send/Recv over SDMA 解除同卡多流控核约束降 decode TPOT 等）。
- [优化案例](cases/index.md)：共 20 张知识卡（如 DIA A3 大融合算子的泳道图调优案例、DeepSeek/Kimi A3 Prefill CP：统一元数据与请求所有者、V3.2-Exp Offload 的 Prefill 搬运流与事件 等）。
- [优化反模式](anti_patterns/index.md)：共 7 张知识卡（如 310P 上 dense/VL 模型 bringup：须显式规避的不可用算子路径 + KV cache/mask 的 NZ 布局约束、AscendC 算子入参校验的静默失效陷阱：可选输入漏 nullptr 守卫·&& 串联漏拦截·meta 侧漏守卫、写 AscendC MicroAPI 向量核的静默正确性陷阱：多行 UB 地址步长·寄存器作用域 等）。
- [基准观测](benchmark_observations/index.md)：共 26 张知识卡（如 A3 LI TopK 融合与 HcPost 的来源观测、AutoFuse A3 部分编译与 hc_post 的来源观测、DeepSeek-V3.2-Exp 当前量化精度来源表 等）。

# 概念

- [运动控制](locomotion/index.md)：共 2 张知识卡（如 LQC（Learning-based Quadruped Controller · 昇腾 A2 训推）、NMR（Neural Motion Retargeting · SMPL-X→G1 · 昇腾 A3 训推））。
- [操作](manipulation/index.md)：共 8 张知识卡（如 ACT (Action Chunking with Transformers) · 昇腾训练 + 310P OM 离线推理、Diffusion Policy (DP) · 310P OM 离线推理、Isaac GR00T N1.6（双系统 VLA · A3 推理图模式优化） 等）。
- [网络模块](modules/index.md)：共 2 张知识卡（如 Action Chunking（动作分块 / ACT Transformer）、Flow-Matching Action Expert（流匹配动作专家））。
- [导航](navigation/index.md)：Alpamayo-R1（下文 AR-1）是 NVIDIA 提出的面向 L4/L5 级智能驾驶的视觉-语言-动作（VLA）大模型，cann-recipes-embodied-ai 在昇腾 Atlas A2 上完成其推理迁移与计算逻辑优化。AR-1 融合视觉感知与自然语言指令构建结构化场景理解，并引入显式的因果思维链（Chain-of-Causal-Thinking, CoC）机制，模拟人类驾驶员「观察—分析因果—预判后果—决策」的认知流程，生成稳健可验证的轨迹规划，同时输出自然语言决策解释。
- [平台](platforms/index.md)：华为昇腾 Ascend 310P 系列推理芯片，是 cann-recipes-embodied-ai 操作类 VLA 模型 OM 离线推理样例的目标部署平台（边缘/嵌入式推理形态，如 OrangePi AI Station）。Pi0、Pi0.5、ACT、Diffusion-Policy 的 infer_with_om/ 样例都以 310P 为运行环境。
- [优化技术](techniques/index.md)：共 3 张知识卡（如 DDP 静态图训练优化（static_graph=True）、梯度检查点精细化（disable outer suffix checkpoint）、OM/ATC 离线静态图推理（310P 部署范式））。
- [世界模型](world_models/index.md)：共 3 张知识卡（如 AgiBot Arm World Model（机械臂世界模型，昇腾 A2 训练+推理）、Cosmos-Predict2.5-2B 视频生成世界基础模型（昇腾 A3）、Cosmos-Transfer2.5-2B 视频风格转换世界模型（昇腾 A3））。

# 操作

- [ACT (Action Chunking with Transformers) · 昇腾训练 + 310P OM 离线推理](act.md)：ACT 是论文 Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware（arXiv:2304.13705）提出的基于 Transformer 的模仿学习控制策略。核心思想是动作分块（Action Chunking）：一次性预测一段连续动作序列（action chunk），从而缓解逐步预测的误差累积，在多个双臂精细操作任务上验证有效。cann-recipes-embodied-ai 提供两条样例链路：Atlas A2 训练（基于 HuggingFace LeRobot）+ Ascend 310P OM 离线推理。
- [Diffusion Policy (DP) · 310P OM 离线推理](diffusion_policy.md)：Diffusion Policy（DP）出自论文 Diffusion Policy: Visuomotor Policy Learning via Action Diffusion（RSS 2023）。它把机器人策略表示为一个条件去噪扩散过程：相比传统自回归形式，具备更好的多模态动作分布处理能力和高维空间稳定性，是许多后续研究（如 3D 扩散策略）的基石。cann-recipes-embodied-ai 提供其 Ascend 310P OM 离线推理样例（基于 HuggingFace LeRobot 的 DP policy）。
- [Isaac GR00T N1.6（双系统 VLA · A3 推理图模式优化）](isaac_gr00t.md)：cann-recipes-embodied-ai 的操作类通用机器人基础模型样例：NVIDIA Isaac GR00T N1.6 在 Atlas A3 上的昇腾迁移与推理性能优化。一手源：manipulation/Isaac-GR00T/README.md 与 docs/manipulation/GR00T N1.6/README.md。
- [OpenVLA（自回归 VLA · 310P OM 离线推理）](openvla.md)：cann-recipes-embodied-ai 的操作类 VLA 模型样例，演示 OpenVLA 在 Ascend 310P 上的离线模型转换、推理、精度验证与仿真评测。一手源：manipulation/openvla/infer_with_om/README.md。
- [Pi0（π0 · VLA 流匹配模型 · 昇腾训练/在线推理/OM 离线三链路）](pi0.md)：cann-recipes-embodied-ai 的操作类（manipulation）VLA 模型样例，演示 Pi0（π0） 在昇腾上的 训练（Atlas A2）/ 在线 torch 推理（A2）/ OM 离线推理（310P） 三条完整链路。
- [Pi0.5（π0.5 · 开放世界泛化 VLA · 昇腾训练/在线推理/OM 离线三链路）](pi05.md)：cann-recipes-embodied-ai 的操作类（manipulation）VLA 模型样例，演示 Pi0.5（π0.5） 在昇腾上的 训练（Atlas A2）/ 在线 torch 推理（A2/310P）/ OM 离线推理（310P） 三条链路。
- [SmolVLA（SmolVLM 主干 · Atlas A2 LIBERO 训练）](smolvla.md)：cann-recipes-embodied-ai 的操作类 VLA 训练样例：在 昇腾 Atlas A2（910b） 上用 LeRobot 训练框架对 SmolVLA 做 LIBERO 离线模仿学习训练 + 在线评测。一手源：manipulation/smolvla/train/README.md 与 manipulation/smolvla/train/doc/README.md。
- [Spirit-v1.5（千寻智能 VLA · 310P 在线推理）](spirit_v1_5.md)：cann-recipes-embodied-ai 的操作类 VLA 模型样例：在 Ascend 310P 平台上适配 Spirit-v1.5 并做推理。一手源：manipulation/spirit-v1.5/infer_with_torch/README.md。

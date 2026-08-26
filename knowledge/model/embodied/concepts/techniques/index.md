# 优化技术

- [DDP 静态图训练优化（static_graph=True）](ddp_static_graph.md)：Pi0.5 在昇腾 Atlas A2 多卡 DDP（DistributedDataParallel）训练中的图固定优化：通过固定训练图、关闭无用参数探测、复用梯度 bucket view，减少 DDP 反向通信侧的额外开销。cann-recipes-embodied-ai 的 Pi0.5 训练样例默认开启，由本页 canonical 描述。
- [梯度检查点精细化（disable outer suffix checkpoint）](gradient_checkpoint_refine.md)：Pi0 / Pi0.5 在昇腾 Atlas A2 多卡 DDP 训练上收益最大的单项性能优化：关闭位置不合适的外层 suffix checkpoint，避免反向阶段整段后缀被重复重算。cann-recipes-embodied-ai 的 Pi0/Pi0.5 训练样例共享此优化，由本页 canonical 描述。
- [OM/ATC 离线静态图推理（310P 部署范式）](om_atc_offline.md)：cann-recipes-embodied-ai 操作类 VLA 模型在 Ascend 310P（OrangePi AI Station 等边缘形态）上的离线推理部署范式：PyTorch → ONNX → ATC → OM，固定 shape、静态图、ACL Runtime 执行。Pi0、Pi0.5、ACT、Diffusion-Policy 的 infer_with_om/ 样例共享这条链路，由本页 canonical 描述。

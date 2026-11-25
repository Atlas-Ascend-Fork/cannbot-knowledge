---
{
  "type": "Runbook",
  "title": "VGGT-1B 单卡 dtype/量化对照：fp32→bf16 同负载 1.39×（官方 6.62% 为 8 卡 A2 累计口径不可比）；W8A8 量化推理耗时与 bf16 持平且输出统计量偏差微小",
  "description": "模型/框架：cann-recipes-embodied-ai `3d_vision/vggt` VGGT-1B 单卡 NPU 推理；`quantization.dtype`（bf16/fp32）与 `int8-w8a8`（build+enable 两步）路径。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# VGGT-1B 单卡 dtype/量化对照：fp32→bf16 同负载 1.39×（官方 6.62% 为 8 卡 A2 累计口径不可比）；W8A8 量化推理耗时与 bf16 持平且输出统计量偏差微小

## 适用场景

- 平台范围依据：source 0 seq 1、source 0 seq 247、source 0 seq 248的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型/框架：cann-recipes-embodied-ai `3d_vision/vggt` VGGT-1B 单卡 NPU 推理；`quantization.dtype`（bf16/fp32）与 `int8-w8a8`（build+enable 两步）路径。
- 平台/版本：Atlas A3（910_9382）单卡 die 0，CANN 9.2.0，torch 2.7.1 + torch_npu 2.7.1.post2；同权重、同 25 图输入、demo 口径（1 warmup + 6 计时取均值）。

## 触发与观测

- I2 F05（bf16 vs fp32，同开关全开）：fp32 1732.84 ms vs bf16 1245.82 ms（Phase A 冻结主路径，条件相同）→ 1.39×（39.1%）；官方 vggt_optimization.md 声称 6.62%（条件：8 卡 A2、累计优化栈、无独立口径说明），与本次单卡 A3 隔离口径不可比（source 0 seq 248/252）。
- F06 W8A8 两步全通：build（exp_w8a8_build.yaml，34s，生成 VGGT_model_W8A8.pt 2,212,398,704 字节≈2.21GB，文档写 2.16G）→ enable（single_w8a8.yaml）推理 1246.77 ms，输出全部有效（source 0 seq 236/242）。
- 输出统计量对比（bf16 主路径 vs W8A8 vs fp32，source 0 seq 200/242/252）：

```text
pose_enc mean: bf16 0.321151 | W8A8 0.320910 | fp32 0.321428   (fp32 dtype 输出)
depth    mean: bf16 1.174652 | W8A8 1.175214 | fp32 1.176620
depth    max : bf16 3.921875 | W8A8 3.984375 | fp32 3.963760
所有配置 finite_ratio=1.000000
```

## 探针与操作

- fp32 实验：`config/exp_fp32.yaml`（开关全开 + dtype: fp32）；日志确认 `[OPTIMIZATION] quantization.dtype: fp32 (torch.float32)`；伴随警告 `In npu autocast, but the target dtype is not supported. Disabling autocast.`（source 0 seq 248）。
- W8A8 enable：`python demo_infer.py --config config/single_w8a8.yaml`，日志含 `Loading W8A8 quantized model...` / `W8A8 quantized model object loaded successfully`（source 0 seq 242）。

## 机制与判别

- dtype 收益判别：fp32→bf16 的 487ms 差距在"开关全开"相同条件下取得，属 dtype 单变量；本机 1.39× 远超官方 6.62% 的原因是口径不同（单卡 A3 隔离 vs 8 卡 A2 累计栈），不能当通用加速承诺。
- W8A8 判别：W8A8（1246.77 ms）与 bf16 主路径（1245.82 ms）耗时持平——该路径收益在显存/精度而非速度（文档无 W8A8 速度声称）；输出统计量相对 bf16 偏差在第三位小数（pose 0.3209 vs 0.3212、depth 1.1752 vs 1.1747），与文档「精度损失 <0.5%」量级一致，本次为统计量观测而非基准指标（accuracy eval 脚本未运行）。
- fp32 的 pose_enc/depth 输出为 torch.float32 且值域与 bf16 版本略有差异（0.321428 vs 0.321151），属 dtype 数值差而非错误。

## 验证信号

- tool_observed：fp32/W8A8 运行 demo_RC=0 verify_RC=0，计时与 pred 统计逐字在案（seq 242/248/252）；W8A8 build 产物大小与激活日志逐字在案（seq 236）。
- 单次运行口径；精度对比是输出统计量（mean/min/max/finite_ratio），非官方 eval 基准（eval_co3d/eth3d/dtu 未运行）。

## 适用与失效边界

- 适用于：VGGT-1B 在 A3 + CANN 9.2.0 单卡场景对 dtype 与 W8A8 的预期——bf16 相对 fp32 有实质单机收益；W8A8 不提速但输出统计量偏移小、模型体积约 2.21GB（bf16 checkpoint 4.9GB 的一半以下）。
- 失效/边界：bf16 加速比不可外推到 8 卡 A2 或其他 SoC；W8A8「<0.5% 精度损失」的正式验收需跑 accuracy eval（本轨迹未做）；fp32 autocast 警告表明 fp32 路径上 autocast 被禁用，其语义未深究。

## 附：断言存档

- VGGT-1B 单卡 A3 同负载（开关全开）：fp32 1732.84 ms vs bf16 1245.82 ms（1.39×/39.1%）；官方 6.62% 为 8 卡 A2 累计栈口径，与本次单卡隔离口径不可比，不能作通用加速承诺

```text
INFO:root:Loading W8A8 quantized model...
INFO:root:W8A8 quantized model object loaded successfully
INFO:root:Average inference time: 1246.77 ms (1.2468 s)
INFO:root:pred[pose_enc]: shape=(1, 25, 9) dtype=torch.float32 min=-0.906250 max=1.664062 mean=0.320910 finite_ratio=1.000000
```

```text
INFO:root:Average inference time: 1732.84 ms (1.7328 s)
INFO:root:pred[pose_enc]: shape=(1, 25, 9) dtype=torch.float32 min=-0.908116 max=1.674559 mean=0.321428 finite_ratio=1.000000
INFO:root:pred[depth]: shape=(1, 25, 350, 518, 1) dtype=torch.float32 min=0.329034 max=3.963760 mean=1.176620 finite_ratio=1.000000
```

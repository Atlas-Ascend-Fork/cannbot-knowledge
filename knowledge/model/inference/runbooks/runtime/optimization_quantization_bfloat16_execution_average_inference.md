---
{
  "type": "Runbook",
  "title": "VGGT-1B 单卡 A3 优化栈逐项消融：DPT 位置编码缓存与 cos/sin dtype 各自独立消除 ~3.3× 瓶颈，rope-cache 与卷积权重预转换单卡无独立收益",
  "description": "模型/框架：cann-recipes-embodied-ai `3d_vision/vggt`（VGGT-1B 3D 视觉几何基础模型，NPU 推理适配 @ 7eca6a6），`demo_infer.py --config config/*.yaml` 主路径。",
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

# VGGT-1B 单卡 A3 优化栈逐项消融：DPT 位置编码缓存与 cos/sin dtype 各自独立消除 ~3.3× 瓶颈，rope-cache 与卷积权重预转换单卡无独立收益

## 适用场景

- 平台范围依据：source 0 seq 1、source 0 seq 199、source 0 seq 200的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型/框架：cann-recipes-embodied-ai `3d_vision/vggt`（VGGT-1B 3D 视觉几何基础模型，NPU 推理适配 @ 7eca6a6），`demo_infer.py --config config/*.yaml` 主路径。
- 任务：单卡（die 0）对 shipped 优化栈（rope-cache / dpt-pos-embed-cache / cos-sin-dtype-optimization / conv-weight-layout-preconvert）做单变量消融，定位主瓶颈。
- 平台/版本：Atlas A3（Ascend 910_9382），CANN 9.2.0，torch 2.7.1 + torch_npu 2.7.1.post2，Python 3.11.13，权重 ckpt/model.pt（md5 f39ee4461f14347f5c38bfba772afbcf），输入 examples/kitchen/images（25 图）。

## 触发与观测

- 触发（I1 规则）：从 baseline 出发一次配置体验——shipped single.yaml 四开关全开 + bf16 主路径均速 1245.82 ms（Phase A 首跑，seq 139），全部关闭的 B0 基线 4224.59 ms（source 0 seq 200），累计优化栈 3.39×。
- 逐项实测（同负载、同 die、demo 自带口径：1 次内部 warmup + num-runs 6 取均值）：

```text
B0  全关 + bf16                  4224.59 ms   [4244.10,4154.56,4270.82,4164.60,4283.75,4229.69]
C1  rope-cache 单开              4300.49 ms
C2  dpt-pos-embed-cache 单开     1274.82 ms   （~3.31× / -69.8%）
C3  cos-sin-dtype 单开           1281.88 ms   （~3.30× / -69.6%）
C4  conv-weight-preconvert 单开  4344.66 ms
```

- 开关隔离经 grep 复核（source 0 seq 224）：每个实验 config 只有一个目标开关为 True，W8A8 关闭、dtype bf16。

## 探针与操作

实验 config 由 single.yaml 程序化派生（B0=四开关全关；C1-C4=在 B0 上单开一个开关），运行方式逐字为（source 0 seq 199 等）：

```bash
python demo_infer.py --config config/exp_baseline.yaml > $L/i1_baseline_demo.log 2>&1; RC=$?
python verify_predictions.py --config config/exp_baseline.yaml --out preds_baseline.npz > $L/i1_baseline_verify.log 2>&1; RC2=$?
```

每个配置同时跑 demo（计时）与自写 verify_predictions.py（镜像 quick_start() 路径，dump 位姿/深度/点云统计）。

## 机制与判别

- 主瓶颈：DPT 头位置编码的 sincos 计算在关闭 dtype 优化时走 FP64/AI-CPU 慢路径；`dpt-pos-embed-cache`（缓存）与 `cos-sin-dtype-optimization`（bf16 计算）**各自单独**消除同一瓶颈（4224.59→1274.82 / 1281.88 ms，二者互为替代路径，效果几乎相同）（source 0 seq 212/218/224）。
- 无独立收益项：`rope-cache`（4300.49 ms，与 B0 差 +75.9 ms，在 B0 自身 ±3% 离散带内）与 `conv-weight-layout-preconvert`（4344.66 ms，同带内）在单卡、重复同尺寸输入的计时口径下无可测独立收益（source 0 seq 206/230）——Transdata 转换节省与 rope 缓存收益小于 run-to-run 噪声。
- 数值有效性：全部配置 verify 输出 pose_enc (1,25,9)、depth (1,25,350,518,1)、world_points (1,25,350,518,3) finite_ratio=1.0（source 0 seq 200/212/218/230）。

## 验证信号

- tool_observed：各配置 demo_RC=0 verify_RC=0，`[OPTIMIZATION]` 开关日志逐字在案（seq 200/224）；计时均值与 6 次明细逐字在案（seq 200）。
- 单次可用性复测口径（agent 自述 implementation-debugging.md 免责声明：not a formal benchmark），未做多次重复实验的统计显著性检验。
- 单观测：均为单次配置运行（每配置 6 次计时取均值），非多轮重复实验。

## 适用与失效边界

- 适用于：VGGT-1B 在 A3 910_9382 + CANN 9.2.0 + torch_npu 2.7.1.post2 单卡场景的优化项取舍——只开 dpt-pos-embed-cache 或 cos-sin-dtype-optimization 之一即可获得主收益（~3.3×），rope-cache/conv-preconvert 可按需省略。
- 失效/边界：结论为单卡 die 0、25 图固定输入的隔离消融；多卡/序列并行路径另有 FIA 算子阻断（见同分片 SP 候选）；C1/C4 的"无收益"受 ±3% 噪声带限制，不排除更精细计时下的微小收益；官方 vggt_optimization.md 的 BF16 6.62% 为 8 卡 A2 累计口径，与本次单卡隔离口径不可比。

## 附：断言存档

- VGGT-1B 单卡 A3 上，dpt-pos-embed-cache 与 cos-sin-dtype-optimization 各自单独开启即可把基线 4224.59 ms 降到 1274.82 / 1281.88 ms（各约 3.3×），二者互为替代路径、消除同一 DPT 头 sincos FP64/AI-CPU 瓶颈

```text
INFO:root:[OPTIMIZATION] quantization.dtype: bf16 (torch.bfloat16)
INFO:root:[OPTIMIZATION] rope-cache: False
INFO:root:[OPTIMIZATION] dpt-pos-embed-cache: False
INFO:root:[OPTIMIZATION] cos-sin-dtype-optimization: False
INFO:root:Execution times (ms): [4244.1041469573975, 4154.5586585998535, 4270.8189487457275, 4164.602994918823, 4283.746242523193, 4229.68864440918]
INFO:root:Average inference time: 4224.59 ms (4.2246 s)
```

```text
INFO:root:Average inference time: 1274.82 ms (1.2748 s)
```

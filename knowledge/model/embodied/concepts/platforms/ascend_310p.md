---
type: Concept
title: Ascend 310P（OM 离线推理目标平台）
description: 华为昇腾 Ascend 310P 系列推理芯片，是 cann-recipes-embodied-ai 操作类 VLA 模型 OM 离线推理样例的目标部署平台（边缘/嵌入式推理形态，如 OrangePi AI Station）。Pi0、Pi0.5、ACT、Diffusion-Policy 的 infer_with_om/ 样例都以 310P 为运行环境。
tags:
- task.lookup
- topic.architecture
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/docs/deployment_troubleshooting.md
  role: supporting
- resource: https://gitcode.com/cann/cann-recipes-embodied-ai/blob/aed7a4788dfe94f6b90084f16ce493f9969471b1/manipulation/pi05/infer_with_om/README.md
  role: supporting
created_at: '2026-06-13T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- 310p
---

# Ascend 310P（OM 离线推理目标平台）

华为昇腾 **Ascend 310P** 系列推理芯片，是 `cann-recipes-embodied-ai` 操作类 VLA 模型 **OM 离线推理样例**的目标部署平台（边缘/嵌入式推理形态，如 OrangePi AI Station）。Pi0、Pi0.5、ACT、Diffusion-Policy 的 `infer_with_om/` 样例都以 310P 为运行环境。

> `cann-recipes-embodied-ai` 的 OM 样例声明目标平台为「310P」，未提供其算力、die、HBM、功耗等硬件规格；硬件细节以昇腾官方资料为准。

## OM 部署要求

- **角色**：310P 是 OM 离线推理（PyTorch→ONNX→ATC→OM）链路的执行平台。在线训练 / torch 推理优化样例则跑在 Atlas A2（见 [gradient-checkpoint-refine](../techniques/gradient_checkpoint_refine.md)）。
- **芯片型号确认**：`npu-smi info` 的 Name/Device 列给出芯片型号（如 `310P1`、`310P3`），ATC 转换的 `--soc_version` 必须与之一致（如 `Ascend310P1`）。型号不符会报 `acl.mdl.execute error 507011`。
- **CANN 版本**：OM 样例支持 `CANN 8.0.0 ~ 8.2.RC1`，需下载对应架构的 `Ascend-cann-toolkit_*.run` 与 `Ascend-cann-kernels-310p_*.run`（如 `Ascend-cann-kernels-310p_8.2.RC1_linux-x86_64.run`），来源 `manipulation/pi0/infer_with_om/README.md`、`manipulation/pi05/infer_with_om/README.md`。
- **Runtime 依赖**：OM 执行依赖 ACL / ACLLite Python 包，需把 `acllite_utils.py` 所在目录上一级加入 `PYTHONPATH`（如 `/path/to/Ascend/ascend-toolkit/latest/thirdpart/python/`）。
- **CPU 侧导出**：ONNX 导出阶段在 310P 宿主机的 Host CPU/GPU 上执行（`onnxruntime` / `onnxruntime-gpu`），ATC 编译与 OM 执行在 310P NPU 上。

## 各 OM 样例（infer_with_om）

| 样例 | OM 切分 | 目标芯片 | 备注 |
| --- | --- | --- | --- |
| `manipulation/pi0/infer_with_om` | VLM + action expert 两段 OM（part2 调 10 次） | Ascend310P1 | `--precision_mode_v2=origin` |
| `manipulation/pi05/infer_with_om` | part1(VLM) + part2(action expert) 两段 OM | Ascend310P1 / Ascend310P3 | 需 Gemma + opset14 ONNX symbolic 补丁 |
| `manipulation/act/infer_with_om` | 整模型单个 `act.om` | Ascend310P1 | 用 `Ascend-cann-kernels-310b` 包（README 实录） |
| `manipulation/diffusion-policy/infer_with_om` | 见样例 README | 310P | 同走 ATC→OM 链路 |

> ACT README 给出的 kernels 包名为 `Ascend-cann-kernels-310b_8.2.RC1_linux-x86_64.run`（与其它样例的 `-310p` 不同）。

## OM 离线推理实测时延（310P / OrangePi AI Station）

`cann-recipes-embodied-ai` 根 README 能力入口表给出三个操作类模型在 310P（OrangePi AI Station 边缘设备）上的 OM 静态图离线推理端到端实测时延：

| 模型 | OM E2E 时延 | 设备 | 来源 |
| --- | --- | --- | --- |
| **Pi0** | **~270 ms** | OrangePi AI Station | root README 能力入口表 |
| **Pi0.5** | **~410 ms**（实测 410.2 ms） | OrangePi AI Station | root README + pi05 样例 README |
| **ACT** | **~200 ms** | OrangePi AI Station | root README 能力入口表 |

> 对照：Pi0 在线（torch）在 Atlas A2 上 ~80 ms、Pi0.5 在线（torch）在 310P 上 ~862 ms，与上表 OM 离线时延同属 root README 能力入口表。

Pi0.5 逐模块拆解（`manipulation/pi05/infer_with_om/README.md`）：PaliGemma(Part1) 平均 223.08 ms，Gemma(Part2，每次 10 步) 平均 15.58 ms，端到端（Part1 + 10×Part2 + KV 拷贝）410.2 ms；OM vs PyTorch 动作平均余弦相似度 0.999984。

OM/ATC 部署范式、算子退化、多段切分细节见 [om-atc-offline](../techniques/om_atc_offline.md)。

## 平台 family 对照

`cann-recipes-embodied-ai` 全仓覆盖三类昇腾平台：

| 平台 | 角色 | 详见 |
| --- | --- | --- |
| **Ascend 310P** | VLA OM 离线推理（边缘） | 该页 |
| **Atlas A2** | VLA 训练 / 在线 torch 推理（910B 系） | [atlas-a2](../../../spatial/concepts/platforms/atlas_a2.md)（空间智能域） |
| **Atlas A3** | cann-infer 主力推理平台（910_93 系） | [atlas-a3](../../../inference/concepts/platforms/atlas_a3.md) |

310P 与 A2/A3 同属昇腾 NPU family 但代际/定位不同：310P 偏边缘离线推理（OM 静态图），A2/A3 偏数据中心训推。具身样例据此分流——训练与在线推理在 A2，边缘离线推理在 310P。

## Links

- 部署范式：[om-atc-offline](../techniques/om_atc_offline.md)
- 受益模型：[pi0](../manipulation/pi0.md)、[pi05](../manipulation/pi05.md)、[act](../manipulation/act.md)
- 平台 family：[atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)、[atlas-a2](../../../spatial/concepts/platforms/atlas_a2.md)
- 源：[cann-recipes-embodied-ai](https://gitcode.com/cann/cann-recipes-embodied-ai/tree/aed7a4788dfe94f6b90084f16ce493f9969471b1)

<!-- cannbot:related:start -->
## 相关

- [OM/ATC 离线静态图推理（310P 部署范式）](../techniques/om_atc_offline.md)（`related`）：Ascend 310P 执行 VLA 模型经 PyTorch → ONNX → ATC 转换得到的固定 shape OM 静态图，运行时依赖 ACL Runtime。
<!-- cannbot:related:end -->

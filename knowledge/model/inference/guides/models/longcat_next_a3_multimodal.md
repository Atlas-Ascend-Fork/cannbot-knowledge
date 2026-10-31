---
type: Guide
title: LongCat-Next A3 多模态离线推理
description: 说明 A3 上 LongCat-Next 六类任务的请求清单、媒体路径、TP/EP、生成头图模式及结果验收，区分多模态与纯文本入口。
tags:
- task.implementation
- topic.multimodal
- topic.model_architecture
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_next/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_next/config/longcat_next_multimodal_tp4_ep4.yaml
  role: example
created_at: '2026-10-29T12:19:41Z'
updated_at: '2026-10-29T12:19:41Z'
platforms:
- a3
---

# LongCat-Next A3 多模态离线推理

## 适用条件与模型入口

当前 Recipes 样例面向 Atlas A3，使用 LongCat-Next 官方完整权重，覆盖文本、图像理解/生成及音频理解/生成；采用 Paged Attention、TP/EP、多模态生成头图模式和官方生成状态机。本样例只支持离线推理，不由这些能力推导在线服务可用。

来源环境为 CANN 9.1.0、Python 3.12、PyTorch/torch_npu 2.8.0。配置 `executor/scripts/set_env.sh` 的 CANN 路径及多节点 IP 后加载环境，并安装 `models/longcat_next/requirements.txt`。官方权重无需转换或替换其中的文件。

## 配置与输入契约

以 `models/longcat_next/config/longcat_next_multimodal_tp4_ep4.yaml` 为起点：`world_size=4`，attention/dense/embed/lmhead/o_proj 为 TP4，`moe_tp_size=1` 对应 EP4。模型权重路径写入 `model_config.model_path`。

- `data_config.dataset` 保持 `longcat_multimodal`，使用 `model_config.custom_params.multimodal` 配置；改为其他 dataset 却保留该段会报错。
- `request_file` 相对 `models/longcat_next/` 解析；请求内部的 `media` 路径则相对该 JSON 清单所在目录解析，两者不同。
- `head_tp_size=1` 是单 owner 参考实现；随附多模态配置为 `4`。`head_exe_mode` 可选择 `eager`、`ge_graph`、`npugraph_ex`，与主干的 `model_config.exe_mode` 分开配置。
- 每个请求 ID 只接受 `[A-Za-z0-9_-]`、最多80字符，并在清单内唯一；它也用于输出子目录。

| task | 必要 media | 主要产物 |
| --- | --- | --- |
| `text` | 无 | `text.txt` |
| `image_understanding` | `image` | `text.txt` |
| `image_generation` | 无 | `image*.png` |
| `audio_to_text` | `audio` | `text.txt` |
| `audio_to_audio` | `audio` 与 `reference_audio` | `audio*.wav` |
| `speech_synthesis` | `reference_audio` | `audio*.wav` |

`text`、`image_generation`、`speech_synthesis` 必须提供 prompt。media 键必须与任务要求完全相符，素材必须存在；路径不能含 `<longcat_…>` 控制标记。

## 最小启动

创建 `models/longcat_next/requests/text.json`，并让 YAML 的 `request_file` 指向它：

```json
{
  "schema_version": 1,
  "requests": [
    {"id": "text_001", "task": "text", "prompt": "请简述你的能力", "generation": {"max_new_tokens": 128}}
  ]
}
```

```bash
source executor/scripts/set_env.sh
bash executor/scripts/infer.sh --model longcat_next --yaml longcat_next_multimodal_tp4_ep4.yaml
```

清单串行执行。每个请求的 `max_new_tokens` 不能超过 `scheduler_config.max_new_tokens`，后者同时用于 KV 预留；实际运行输出上限取请求中的最大值。存在图像生成任务时，运行时 batch size 为2以执行 CFG，其余任务为1。

`enable_thinking` 写在请求顶层，不能放入 generation；生成图像或音频的任务不接受显式 thinking 参数。音频按官方 processor 重采样，生成音频采用24 kHz 配置。

纯文本 `longcat_next_text_*.yaml` 走通用框架流程，需要在 `data_config.dataset_path` 目录中准备 `default_prompt.json`，不使用上述多模态请求清单。

## 验收与回退

结果位于 `models/longcat_next/res/<日期>/longcat_next_<yaml名>/`：逐 rank 日志用于定位失败，`results/<请求id>/result.json` 记录请求、耗时和产物列表。先用 eager 和少量请求分别验收六类任务，再逐项开启生成头 TP 与图模式，检查文本、图像和音频产物，以及 KV 预留、编译和峰值内存。图模式或质量异常时恢复对应 eager 配置重新建立基线；本仓未执行 NPU 实测。

## 相关入口

- [多模态统一拉起架构](../../concepts/frameworks/mm_inference_launch.md)
- [多模态推理框架](../../concepts/frameworks/cann_executor.md)

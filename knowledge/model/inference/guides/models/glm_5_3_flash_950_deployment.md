---
type: Guide
title: GLM-5.3-Flash 950DT 部署与验收
description: 基于当前8卡EP样例准备算子与Hybrid权重，限定TP/CP、npugraph_ex和共享专家多流，并按输入、精度和时延验收。
tags:
- task.implementation
- topic.model_architecture
- topic.performance.analysis
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5_3/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5_3/config/glm_5_3_flash_ep8.yaml
  role: example
created_at: '2026-10-29T12:19:41Z'
updated_at: '2026-10-29T12:19:41Z'
platforms:
- '950'
---

# GLM-5.3-Flash 950DT 部署与验收

## 条件与准备

本页面向 Recipes 的 Ascend 950DT、Linux ARM部署，默认8卡EP；不套用同仓A3单卡CPU offload集成方案。模型结构与精度分工见[GLM-5.3-Flash](../../concepts/models/glm_5_3_flash.md)。

安装 `models/glm_5_3/requirements.txt`，准备提供 mHC 的 `custom_ops` 和提供 causal_conv1d 的 `cann_ops_transformer`，加载 `models/glm_5_3/set_env.sh`。随后配置公共 `executor/scripts/set_env.sh` 的CANN安装位置及多节点IP。

## 权重转换

从官方取得FP8发布权重，输入与输出目录必须不同：

```bash
python models/glm_5_3/utils/convert_model.py \
  --input_hf_path /path/to/GLM-5.3-Flash \
  --output_hf_path /path/to/GLM-5.3-Flash-HIF8
```

该入口生成Hybrid HiF8–MXFP8–MXFP4运行时权重并改写 `config.json` 中的量化配置，不能只修改YAML而继续加载未经转换的发布权重。

## YAML 与启动

修改 `models/glm_5_3/config/glm_5_3_flash_ep8.yaml` 的 `model_config.model_path` 为转换结果。当前配置为world_size=8，CP、attention/dense/MoE/embed/lmhead TP均为1；来源还要求o_proj/shared TP为1。框架据 `moe_tp_size=1` 派生EP=world_size。

`exe_mode` 支持 eager、npugraph_ex；默认npugraph_ex。`custom_params.enable_multi_streams=True` 在decode中让共享专家与路由专家重叠。模型当前不支持MTP，不应复制其他模型的MTP参数。

数据集支持default、LongBench、InfiniteBench；默认输入长度8192，需按README准备InfiniteBench的 `longbook_qa_eng.jsonl`。先用小批次和少量样本建立基线，然后在各节点同步执行：

```bash
source models/glm_5_3/set_env.sh
bash executor/scripts/infer.sh --model glm_5_3 --yaml glm_5_3_flash_ep8.yaml
```

## 验证与停止条件

记录驱动、CANN与算子包版本、转换日志、最终配置、输入长度、每卡batch及全局world size；检查量化权重加载、KDA状态与DSA缓存、mHC输出的有限值，以及eager与图模式输出差异。

逐项验证共享专家多流和npugraph_ex后再扩大batch，分别记录每步decode时延、每卡TPS与全局TPS。README中的8K测量只代表来源配置，不能作为任意负载的保证。编译失败、输出异常或精度下降时恢复eager、关闭相应重叠并回到已验证的小批次基线。本仓未运行设备推理或性能复测。

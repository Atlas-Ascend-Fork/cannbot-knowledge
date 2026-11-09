---
type: Guide
title: vLLM Ascend调优配方：投机K、专家重排与量化校准证据
description: 区分离线goodput最优K、示例EPLB规划、llm-compressor校准/动态量化和发布recipe硬件声明，核对测量输入、conditional概率口径、checkpoint目标与版本化部署边界。
tags:
- task.implementation
- task.testing
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_DSD_k_tuner/manager.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/eplb/eplb_deepseek.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/eplb/eplb_strategy.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_DSD_k_tuner/generate_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/quantization/llm-compressor/mixed_mxfp4_mxfp8_dynamic_moe.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/quantization/llm-compressor/w4a8_dynamic_moe.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/quantization/llm-compressor/w8a8_int8.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/quantization/llm-compressor/w8a8_int8_dynamic.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/quantization/llm-compressor/w8a8_int8_dynamic_moe.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/recipes/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/recipes/manifest.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/recipes/overlays/Qwen/Qwen3-30B-A3B.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/recipes/overlays/Qwen/Qwen3.5-397B-A17B.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/recipes/overlays/Qwen/Qwen3.6-27B.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/recipes/overlays/Qwen/Qwen3.8-27B.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/recipes/overlays/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/recipes/overlays/deepseek-ai/DeepSeek-V4-Flash.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/recipes/overlays/moonshotai/Kimi-K3.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/recipes/overlays/zai-org/GLM-5.3-Flash.yaml
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/recipes/overlays/zai-org/GLM-5.3.yaml
  role: constraint
created_at: '2026-11-03T05:18:22Z'
updated_at: '2026-11-03T05:18:22Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend调优配方：投机K、专家重排与量化校准证据

## 离线K调参需要真实ITL和无条件接受率

DSD manager要求batch_stats、接受率非空、接受率在[0,1]，含BS1和最大BS，每个BS包含K0/K1且key按升序。K0基线goodput=1/ITL0；其他K用AL/ITL，AL=1+前K个位置的无条件接受率之和，不把位置率再连乘；非正ITL跳过。仅严格更高goodput更新K，平分保留已有选择。输入的K0 ITL与非finite值没有在所读检查中全面验证，测量数据须先检查。

查询按bisect_right取不大于当前batch size的已测BS，低于最小值取首项；输出合并相邻同K的闭区间，不插值估算未测时延。generate_config从sweep DataFrame提median_itl_ms，无spec配置当K0；另运行模型收spec_decode指标并拒绝完全未启用投机的情况，tokenizer已应用chat模板时避免二次BOS。不同方法Eagle/Eagle3/ngram/draft_model/MTP、实际负载与目标依赖都要匹配，生成配置不等于本次已优化。

## EPLB示例是规划，不是控制器提交

balanced_packing要求对象数能被pack数整除，按权重降序把对象放入未满且当前负载最小的pack；replicate_experts把新增副本给当前weight/replica-count最大的逻辑专家，返回物理到逻辑映射、replica rank与计数。入口按num_groups是否可被num_nodes整除选择hierarchical或全局退化路径，再生成带-1空位的逆映射。

这是示例规划/统计数据处理；输入权重来源、实际网络分层、生产EPLB注册/迁移/commit和量化专家ABI仍另核。plot/average脚本输出与规划映射不是真实all-rank权重迁移、模型质量或性能结果。

## 量化脚本的recipe不是可跨模型复制的scheme

五个llm-compressor示例各自指定模型、target/ignore和校准流程：mixed MXFP4/MXFP8将attention/shared-expert与routed experts分组，并用datafree pipeline；动态MoE INT8忽略lm_head及mlp.gate。静态INT8示例还可忽略down_proj，校准文件格式有限；另一个脚本用512样本、最大长度2048、SmoothQuant强度0.8和GPTQ W8A8。不能从文件名dynamic或W4A8代替实际recipe中的weights/input_activations定义。

模型/分词器、样本、模板、truncate/padding、输出保存与skip层要共同记录；oneshot完成和生成文本打印不构成新模型量化精度或Ascend实际kernel兼容证明。数据免校准也不等于免任务评估。

## 发布overlay按variant和硬件精确解读

recipe overlays有Qwen3/3.5/3.6/3.8、DeepSeek V4/视觉、Kimi-K3及GLM5.3系列，分别声明INT8/MXFP4/MXFP8、checkpoint、TP/DP、图/投机默认和image。示例：Qwen3.6的MXFP8 variant写950DT/TP1，而INT8 variant写910C/TP2；Qwen3.5-397B的W8A8与MXFP4均有独立checkpoint。不能按家族名合并这些不同布局与拓扑。

GLM950PR条目写TP8、block-size512、对应镜像/补丁及EP不适用；Kimi-K3只在特定strategy/hardware维度宣称支持，DeepSeek视觉的4卡可见集合与8卡节点资源说明也需分开。这些是该固定overlay的发布声明；meta.hardware=verified、VRAM minimum及min_vllm_version不转成本知识卡verified或实测性能，字段缺省也不推普遍支持。

recipes README/manifest定义导入、overlay与发布责任，manifest当前只有schema_version，不能独立构成完整外部recipe内容。variant-specific extra_args/env、hardware_overrides、strategy_hardware与feature mode共同解析，目标工具/镜像仍需核实际版本。


## 固定示例职责索引

- `examples/offline_DSD_k_tuner/manager.py`：接口/状态与执行顺序示例。
- `examples/eplb/eplb_deepseek.py`：接口/状态与执行顺序示例。
- `examples/eplb/eplb_strategy.py`：接口/状态与执行顺序示例。
- `examples/offline_DSD_k_tuner/generate_config.py`：接口/状态与执行顺序示例。
- `examples/quantization/llm-compressor/mixed_mxfp4_mxfp8_dynamic_moe.py`：接口/状态与执行顺序示例。
- `examples/quantization/llm-compressor/w4a8_dynamic_moe.py`：接口/状态与执行顺序示例。
- `examples/quantization/llm-compressor/w8a8_int8.py`：接口/状态与执行顺序示例。
- `examples/quantization/llm-compressor/w8a8_int8_dynamic.py`：接口/状态与执行顺序示例。
- `examples/quantization/llm-compressor/w8a8_int8_dynamic_moe.py`：接口/状态与执行顺序示例。
- `recipes/README.md`：配置与部署说明；记录其版本化声明。
- `recipes/manifest.yaml`：配置与部署说明；记录其版本化声明。
- `recipes/overlays/Qwen/Qwen3-30B-A3B.yaml`：配置与部署说明；记录其版本化声明。
- `recipes/overlays/Qwen/Qwen3.5-397B-A17B.yaml`：配置与部署说明；记录其版本化声明。
- `recipes/overlays/Qwen/Qwen3.6-27B.yaml`：配置与部署说明；记录其版本化声明。
- `recipes/overlays/Qwen/Qwen3.8-27B.yaml`：配置与部署说明；记录其版本化声明。
- `recipes/overlays/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp.yaml`：配置与部署说明；记录其版本化声明。
- `recipes/overlays/deepseek-ai/DeepSeek-V4-Flash.yaml`：配置与部署说明；记录其版本化声明。
- `recipes/overlays/moonshotai/Kimi-K3.yaml`：配置与部署说明；记录其版本化声明。
- `recipes/overlays/zai-org/GLM-5.3-Flash.yaml`：配置与部署说明；记录其版本化声明。
- `recipes/overlays/zai-org/GLM-5.3.yaml`：配置与部署说明；记录其版本化声明。

本次只读源码、模板和配置，没有执行示例、下载、安装、部署、测试、量化、NPU或Agent A/B；示例默认值、所称verified或输出打印不提升为本知识卡已复核事件。

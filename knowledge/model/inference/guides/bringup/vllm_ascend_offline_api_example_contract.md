---
type: Guide
title: vLLM Ascend离线示例：Prompt Embeds、指标、重载与RL状态验证
description: 核对固定离线示例的模型输入、pooling/audio、request指标、DP launcher、sleep和权重更新顺序，区分打印演示、结构断言及真实checkpoint/NPU质量证据。 补充固定3164 checkpoint坐标稀疏HCCL与失败后暂停恢复边界。
tags:
- task.implementation
- task.testing
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/prompt_embed_inference.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/chat_templates/template_qwen2_audio.jinja
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/device_id_mapping_demo.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/device_print_demo.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_data_parallel.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_embed.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_external_launcher.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_inference_audio_language.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_inference_metrics.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_inference_npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_inference_npu_long_seq.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_inference_npu_tp2.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_inference_sleep_mode_npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_reload_weight.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/offline_weight_load.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/prefix_cache_repro.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/prompt_embedding_inference.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/rl/rlhf_async_new_apis.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/rl/rlhf_http_hccl.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/rl/rlhf_http_lora.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/rl/rlhf_http_npu_ipc.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/examples/save_sharded_state_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/examples/rl/rlhf_sparse_hccl.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/e2e/pull_request/four_card/test_sparse_hccl_checkpoint.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/tests/ut/distributed/weight_transfer/test_sparse_hccl_engine.py
  role: implementation
created_at: '2026-11-03T05:18:22Z'
updated_at: '2026-11-03T06:56:11Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend离线示例：Prompt Embeds、指标、重载与RL状态验证

## 输入、指标与设备身份

两个prompt-embedding示例都用匹配的HF tokenizer和同模型embedding层，apply_chat_template带generation prompt，再squeeze batch维以prompt_embeds喂给启用enable_prompt_embeds的LLM；单项dict与batch dict列表分开。它们不证明任意embedding维度/processor兼容。pooling示例显式选择runner，音频示例另要求librosa、模型对应prompt和multi_modal_data；Qwen2-audio模板区分字符串与content列表、计数Audio特殊token并可追加assistant提示，不能把文本chat模板泛用到所有音频模型。

request metrics示例设置disable_log_stats=False，默认关闭统计时output.metrics可为None；指标收集、同步与实际请求身份一并确认，不能把无指标当零时延。device-id demo打印可见logical0到host physical ID映射，不假设两者相等。device-print demo分别比较eager、aot_eager/fullgraph和graph replay，修改原输入后检查输出随之改变；打印或同步本身不是完整编译/数值验收。

## 启动与生命周期

基本、长序列、TP2、offline DP和external_launcher使用不同显式参数；external launcher把各rank交外部进程启动，实际设备划分、环境、清理与所有rank结果需另核。sleep示例演示调用和再次生成，不给出跨模型统一释放量或恢复正确率。prefix cache repro也只提供问题输入与重复请求，实际命中/缓存一致性仍需指标和结果。

reload示例先dummy/eager/TP4生成，再collective_rpc(update_config)把load_format改auto，随后reload_weights再打印输出。代码把后者描述为真实加载，但没有用完整任务oracle断言质量；Agent应核真实checkpoint、所有rank参数和前后可判定结果，不能把“makes sense”打印当通过。offline_weight_load及310 sharded-state保存另涉及checkpoint/量化描述、按worker分片及失败清理，不用一种save文件名推通用loader ABI或跨TP重用。

## RL全量权重与LoRA更新分开

async Ray示例把训练/推理放不同NPU，展示pause/resume与batch-invariant生成；HTTP HCCL、NPU IPC及LoRA三个示例各自走不同初始化/更新/finish和load/unload接口。IPC共享设备/句柄前提不由HCCL样例自动满足，LoRA adapter替换也不等于全模型参数替换。

保留更新前reference、dummy或旧参数、更新后及重载后的可判定输出/签名，核pause/finish/resume的真实状态与异常清理；HTTP成功或后续文本不同不能独立证明参数完整同步。样例会启动服务/训练进程、调用状态接口或写文件，本次未执行任何这些操作。


## 固定示例职责索引

- `examples/prompt_embed_inference.py`：接口/状态与执行顺序示例。
- `examples/chat_templates/template_qwen2_audio.jinja`：接口/状态与执行顺序示例。
- `examples/device_id_mapping_demo.py`：接口/状态与执行顺序示例。
- `examples/device_print_demo.py`：接口/状态与执行顺序示例。
- `examples/offline_data_parallel.py`：接口/状态与执行顺序示例。
- `examples/offline_embed.py`：接口/状态与执行顺序示例。
- `examples/offline_external_launcher.py`：接口/状态与执行顺序示例。
- `examples/offline_inference_audio_language.py`：接口/状态与执行顺序示例。
- `examples/offline_inference_metrics.py`：接口/状态与执行顺序示例。
- `examples/offline_inference_npu.py`：接口/状态与执行顺序示例。
- `examples/offline_inference_npu_long_seq.py`：接口/状态与执行顺序示例。
- `examples/offline_inference_npu_tp2.py`：接口/状态与执行顺序示例。
- `examples/offline_inference_sleep_mode_npu.py`：接口/状态与执行顺序示例。
- `examples/offline_reload_weight.py`：接口/状态与执行顺序示例。
- `examples/offline_weight_load.py`：接口/状态与执行顺序示例。
- `examples/prefix_cache_repro.py`：接口/状态与执行顺序示例。
- `examples/prompt_embedding_inference.py`：接口/状态与执行顺序示例。
- `examples/rl/rlhf_async_new_apis.py`：接口/状态与执行顺序示例。
- `examples/rl/rlhf_http_hccl.py`：接口/状态与执行顺序示例。
- `examples/rl/rlhf_http_lora.py`：接口/状态与执行顺序示例。
- `examples/rl/rlhf_http_npu_ipc.py`：接口/状态与执行顺序示例。
- `examples/save_sharded_state_310.py`：接口/状态与执行顺序示例。

本次只读源码、模板和配置，没有执行示例、下载、安装、部署、测试、量化、NPU或Agent A/B；示例默认值、所称verified或输出打印不提升为本知识卡已复核事件。


## 固定3164：checkpoint坐标的稀疏HCCL演示

rlhf_sparse_hccl示例要求trainer/server从同一未量化Qwen3 MoE checkpoint启动，trainer能放下完整BF16模型，独立trainer设备与TP/DP推理设备分开；PP不支持。其补丁针对首层/末层、expert0与中间expert的gate_proj前两行交换，检查至少两个expert/中间行、完整shape且交换不是no-op。HF fused gate_up存储先按[experts,2*intermediate,hidden]验证，再提取gate片段。

SparseWeightPatch传完整checkpoint名称/shape和片段的全局flat坐标，把TP/EP映射留给Native loader，不把runtime packed/NZ坐标当checkpoint坐标。通信world为1+TP*DP，参数需匹配server。演示先生成、pause、初始化trainer、send_weights，finally在engine存在时shutdown；只有所有步骤成功才resume再生成，初始化/传输/关闭失败会留在暂停状态等待恢复，不能把finally当权重回滚事务。

该示例打印前后token与更新计数，不独立证明完整模型精度。相邻稀疏checkpoint E2E以小型synthetic Qwen3 MoE比较Native dense加载与稀疏加载、先确认补丁会改变签名、恢复baseline后再比各worker digest及生成token；这比“文本改变”强，但仍不是预训练模型任务准确率或真实吞吐。unsupported PP/EPLB/量化、空patch、全部layer视图异常恢复等还需按对应测试断言与实际环境分别执行；本次未运行。

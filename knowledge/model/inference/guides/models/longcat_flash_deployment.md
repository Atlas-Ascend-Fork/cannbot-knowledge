---
type: Guide
title: LongCat-Flash A3 部署与优化验收流程
description: 当前 LongCat A3 统一 Executor 启动、五类配置、复数多流开关、GE/npugraph_ex 边界、AFD/MTP 与验收。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/config/longcat_flash_densetp8_ep64_gegraph_mtp2_eplb_afd_w8a8.yaml
  role: constraint
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/scripts/infer.sh
  role: implementation
created_at: '2026-10-21T09:02:43Z'
updated_at: '2026-10-29T13:49:53Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - moe
        - mla
---

# LongCat-Flash A3 部署与优化验收

## 准备权重与配置

使用本卡登记的当前源码，在 Atlas A3 配套 CANN/torch_npu 环境中准备 BF16 权重或转换后的 W8A8 权重。源转换器仍接受以下参数：

```bash
python models/longcat_flash/utils/convert_model.py \
  --input_bf16_hf_path /data/models/LongCat-Flash-Chat \
  --output_hf_path /data/models/LongCat-Flash-Chat-W8A8
```

将输出路径写入实际 YAML 的 model_config.model_path。不能从目录名称判断权重量化布局；准备配套 tokenizer 和 prompt，并记录实际软件版本。

## 当前配置差异

| YAML | world_size | 关键差异 |
| --- | --- | --- |
| longcat_flash_densetp8_ep32.yaml | 32 | BF16/eager，MTP0，不开强制均衡 |
| longcat_flash_densetp8_ep32_gegraph_mtp.yaml | 32 | BF16/GE，MTP1，o_proj TP8 |
| longcat_flash_densetp8_ep128_gegraph_mtp_eplb_w8a8.yaml | 128 | W8A8/GE，MTP2，强制均衡，多流/预取/SuperKernel |
| longcat_flash_densetp8_ep64_gegraph_mtp2_eplb_afd_w8a8.yaml | 128 | W8A8/GE，AFD两半，MTP2，batch256 |
| longcat_flash_densetp8_ep32_npugraph_ex_mtp2_eplb_w8a8.yaml | 32 | W8A8/npugraph_ex，静态kernel，多流；预取/SuperKernel关闭 |

world_size 是逻辑进程数，不直接等于物理卡数。模型特性开关位于 model_config.custom_params；当前字段为 enable_multi_streams（复数）。CP 必须为1；Attention TP>1时要求与 o_proj TP 相等；MTP宽度仅0/1/2。预取需多流，SuperKernel仅GE。

force_eplb 是性能测试配置，不能直接作为真实路由的精度验收。正式比较应明确关闭或记录该项；scheduler_config 控制 batch、block_size 和请求 token 预算，不能继续使用旧顶层字段名。

## 运行当前入口

```bash
bash executor/scripts/infer.sh --model longcat_flash \
  --yaml longcat_flash_densetp8_ep64_gegraph_mtp2_eplb_afd_w8a8.yaml
```

从仓库根目录运行，多机各节点保持相同配置并核对节点IP与设备映射。在线PD模式通过 --mode online、--pd-role prefill/decode 及可选 --p-yaml-name/--d-yaml-name 选择两端配置；具体能力仍需核对该模型与框架组合。

当前共享 Executor/ModelWorker 管理编译：GE 与 npugraph_ex 用对应编译器，缓存位于 model_config.output_path/compile_cache。旧 runner 的 CASE_NAME/_spec 缓存与 models/longcat-flash/infer.sh 不再作为当前启动流程。

## 按路径验收

先验输出，再分别评估多流、预取、局部TP、MTP和AFD。非AFD多流需要正确事件汇合；npugraph_ex AFD Decode将接收延迟到相加前。长序列 Prefill 的 MoE chunk 在模型入口算出 EP 一致的chunk数，减少每层重复同步并处理负载不均峰值。

保留 warmup、重复次数、实际接受率、端到端时延与输出记录。来源的 MTP2/perfect EPLB 整网数字只在[来源观测](../../optimizations/benchmark_observations/longcat_a3_afd_source_benchmark.md)维护。本次未运行模型。失败时恢复一组匹配的配置、权重和缓存；当前无KVP入口，不复制旧KVP YAML。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/README.md)（primary）
- [modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)（implementation）
- [longcat_flash_densetp8_ep64_gegraph_mtp2_eplb_afd_w8a8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/config/longcat_flash_densetp8_ep64_gegraph_mtp2_eplb_afd_w8a8.yaml)（constraint）
- [infer.sh](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/scripts/infer.sh)（implementation）

## 相关入口

- [多流控核](../../optimizations/rules/decode_multi_stream_overlap_core_balance.md)
- [AFD](../../optimizations/rules/afd_attn_ffn_disaggregation.md)
- [权重预取](../../optimizations/cases/longcat_a3_decode_weight_prefetch.md)
- [图模式](../optimization/graph_mode_decode_only_compile_backends.md)

---
type: Guide
title: compressed-tensors 接入：产物契约、targets/ignore 与运行加载链
description: 量化配置读取优先级：顶层 quantization_config、text_config 和 compression_config；从 targets/ignore、target_scheme_map 到 hf_config.quant_config、weight_loader、post-load 的接线与缺 scale 诊断。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/quantization/__init__.py
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/quantization/compressed_tensors/compressed_tensors.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/fuse_moe_gmm.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-contract.md
  role: supporting
created_at: '2026-11-10T01:14:54Z'
updated_at: '2026-11-10T03:51:43Z'
platforms:
- agnostic
aliases:
- CompressedTensorsConfig.from_config
- compressed-tensors 量化产物契约
- ignore 缺 scale
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# compressed-tensors 运行接入：配置、targets/ignore 与加载后处理

## 范围与交付契约

用于固定 Recipes 统一 Executor 消费 compressed-tensors 产物；这是模型加载契约，不是生成新量化权重的算法。产物应保留 config.json 的 quantization_config 或 compression_config、量化与浮点张量的 safetensors 索引/分片，并说明权重、scale、bias/zero point、smooth scale 的语义和模型前缀映射。旧迁出材料用 deploy_quantization.md 承载交付说明；它是交接材料，加载器不会仅因缺这个 Markdown 文件就自动拒绝运行。

至少核对 quant_method、config_groups.targets、ignore、权重/激活位宽与 dtype、format、可选 kv_cache_scheme。不能只凭文件名 W8A8 认定所有 Linear、MoE、LI 和 KV 都量化；不同对象可以采用不同方案。

## 从配置到运行模块

| 阶段 | 固定实现的责任 |
| --- | --- |
| 读取 | ModelWorker 规范化量化方法并调用 module.quantization.get_quant_config |
| 解析 | CompressedTensorsConfig.from_config 读取 config_groups、ignore、format、weight_block_size 和 kv_cache_scheme |
| 派生 | 构造 target_scheme_map，分别推导 mm_quant_mode、gmm_quant_mode、kv_cache_quant_mode |
| 透传 | hf_config.quant_config 交给建模层，再传给 Linear / FusedMoEGMM 等运行对象 |
| 选择方法 | get_quant_method(layer,prefix) 先按 CompressedTensorsConfig.ignore 判定浮点回退，再匹配类、完整前缀或目标规则 |
| 建立和加载 | create_weights 注册权重、scale 等参数，weight_loader 消费 checkpoint 的实际张量 |
| 后处理 | 模型 process_weights_after_loading 负责转置、NZ/base、scale dtype 和专家 pack/unpack 等例外 |
| 执行 | forward 进入与真实 scheme 匹配的量化内核；MLP 的 SwiGLU 和路由 scale 仍需模型接线 |

get_quant_config 优先读 HF 顶层 quantization_config，也检查 text_config 的量化配置，再回退 compression_config；没有内嵌配置时按所选量化类的文件名定位 JSON，零个或多个候选都可能报错。不能将 from_config 私有入口或旧 per-model runner 的位置当作所有模型唯一加载路径。

## targets、ignore 与缺 scale 的判断

ignore 匹配的 Linear 由 UnquantizedLinearMethod 保持浮点；未 ignore 的目标按 target_scheme_map 和 prefix 选择 scheme。targets 可对应模块类、层前缀或实现支持的匹配形式；MoEGMM 和 Linear 的处理类、位宽/scale 编码可能不同，按实际 get_quant_method 与 get_scheme 检查，不能把任意量化配置视为兼容。

发现一个 Linear 既未列入 ignore，又找不到 weight_scale 时，至少区分“本来应该 BF16 但漏了声明”与“量化 scale 真的缺失”。这只是诊断启发式，不足以授权随意追加 ignore。记录加载键、层前缀、scheme、dtype 和期望 scale，回到产物定义确认后再修复；不能因改了 targets/ignore 就把另一种模型语义当作原模型验收。

## 接入边界和验证

Dense、共享专家、MoE 和 KVCache 分别确认运行对象。量化产物契约缺失与 runtime 不支持是不同缺口；不支持的融合实现可在保持量化语义和验证口径时回退等价非融合路径，不能用浮点替代后仍宣称目标量化已运行。

核对真实权重、分片、加载集合和 post-load 后布局；覆盖 eager/图模式、Prefill/Decode 和不等长请求。测量真实执行的量化分支、精度、无 profiler 的时延与峰值显存，缺任何一项都不由“成功加载”代替。失败时恢复原产物及匹配配置/缓存。

相关：[MLP/MoE scale 接线](w8a8_mlp_and_moe_scale_flow.md)、[量化布局与命名](../../optimizations/rules/quant_weight_load_layout_and_naming.md)、[部署转换路径](../deployment/quant_weight_conversion_path_selection.md)、[LI 独立闭环](lightning_indexer_quantization_scale_cache.md)。


## Evidence

- [module/quantization/__init__.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/quantization/__init__.py)
- [module/quantization/compressed_tensors/compressed_tensors.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/quantization/compressed_tensors/compressed_tensors.py)
- [executor/core/model_worker/model_worker.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/executor/core/model_worker/model_worker.py)
- [module/linear.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/linear.py)
- [module/fuse_moe_gmm.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/fuse_moe_gmm.py)
- [.agents/skills/model-infer-quantization/references/quantization-contract.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-quantization/references/quantization-contract.md)

---
type: Concept
title: MindSpeed-Bridge（运行时注册与 HF/Megatron 权重映射）
description: 当前 pip/.pth 运行时插件注册、委托训练入口、参数映射验证，以及离线 checkpoint 灵活 PP/VPP layout 的互斥限制。
tags:
- task.implementation
- topic.architecture
- topic.compilation
- topic.checkpointing
status: stable
sources:
- resource: cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/docs/zh/install_guide.md
  role: primary
- resource: cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/tools/install_auto.sh
  role: implementation
- resource: cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/mindspeed_bridge/runtime/auto_register.py
  role: implementation
- resource: cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/mindspeed_bridge/scripts/training/run_recipe.py
  role: implementation
- resource: cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/mindspeed_bridge/models/glm_moe_dsa/glm_moe_mappings.py
  role: implementation
- resource: cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/mindspeed_bridge/examples/conversion/compare_hf_and_megatron/README.md
  role: implementation
- resource: cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/tasks/checkpoint/convert.py
  role: implementation
- resource: cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/tasks/checkpoint/convert_hf2mg.py
  role: implementation
created_at: '2026-06-24T00:00:00Z'
updated_at: '2026-10-29T13:38:33Z'
platforms:
- agnostic
---

# MindSpeed-Bridge：运行时注册与权重映射

## 当前接入机制

当前安装采用可编辑 pip 包，.pth autoload 负责模型发现，runtime 插件注册模型与 recipe。训练入口为 `python -m mindspeed_bridge.scripts.training.run_recipe`（多卡用 torchrun --module）；委托 launcher 解析 Feature CLI，将 dotted Hydra override 交给上游，并在运行时补齐 step functions、dataset 等适配。

旧安装脚本复制 mindspeed_bridge 目录、修改 Megatron-Bridge 三处源文件的方式已移除。包顶层 __init__.py 也不再统一 monkey-patch ConfigContainer.validate；具体特性由 FeatureAdaptor 与运行时 adapter 安装，不能再引用旧全局 repatch 顺序解释全部配置。

安装需按当前指南配套 Megatron-LM core_v0.18.0、Megatron-Bridge v0.5.0、MindSpeed Core、MegatronAdaptor、TransformerEngineNPU 和 MindSpeed-Ops。子模块安装是另一种依赖准备方式；是否使用 .pth autoload 和依赖路径应通过 runtime.get_status 的插件状态与 errors 核查。安装文档中的镜像地址仍是占位，不能当作已发布镜像。

## HF↔Megatron 权重桥接框架

权重桥接框架复用上游 Megatron-Bridge 的 **`MegatronParamMapping` / `AutoMapping`** 抽象。
一个 ParamMapping 类绑定一组
`(megatron_param 名, hf_param 名)`，提供两个方向的方法，且**内建张量并行分片语义**：

- `hf_to_megatron(hf_weights, megatron_module)`：HF 全权重 → 按当前 `tp_rank`/`tp_size` 切出
  本 rank 的 Megatron 分片；
- `megatron_to_hf(megatron_weights, megatron_module)`：跨 TP rank **gather** 回完整张量再还原成
  HF 布局；跨 PP 用 `broadcast_obj_from_pp_rank` 同步 config；带量化时 `maybe_dequantize`；
- `resolve(captures)`：把名字里的占位（层号等正则 capture）解析成具体参数名，复制出一个就绪映射。

当前 GLM 派生映射负责 fused gate/up 和专家布局，并委托上游映射处理并行分片。GLMGatedMLPMapping.resolve 在解析 wildcard 后保留 pp/ep/tp/etp process groups；专家映射区分逐专家 2D 参数与 packed grouped 3D 权重，并检查形状。旧 GDNLinearMappingSeparate 已从当前树移除，不能继续作为当前适配接口。

### 单步精度对比验证

`examples/conversion/compare_hf_and_megatron/`（`compare.py`）是桥接正确性的验证工具：同一 prompt
分别跑 HF 模型与转换后的 Megatron 模型单步前向，比对 logits **余弦相似度（阈值 98%）**、Top-5、
最大/平均绝对差；支持 `--tp/--pp/--ep` 多卡、`--roundtrip_hf`（Megatron 再导回 HF 后对比闭环）、
`--enable_debug_hooks`（逐组件前/反向 JSONL 落盘）。注意 Megatron 可能为 kernel 效率 pad
`vocab_size`，对比时截断回 HF 词表大小。

## MindSpeed-LLM checkpoint 转换

[mindspeed](mindspeed.md) 生态里 **MindSpeed-LLM**
（[mindspeed-llm](https://gitcode.com/Ascend/MindSpeed-LLM)）有一套独立、更早的 HF↔Megatron-Mcore 转换引擎
（`mindspeed_llm/tasks/checkpoint/`，入口 `convert_ckpt.py`），与 Bridge 路径定位重叠但**抽象不同**：

| 维度 | Megatron-Bridge | MindSpeed-LLM checkpoint |
|------|------------------------|--------------------------|
| 映射抽象 | `MegatronParamMapping` **类**，内建 TP 分片语义 | `module_mapping` **dict**，配置驱动 |
| 映射来源 | 代码里按模型派生类 | `configs/checkpoint/model_cfg.json` 按 `model_type_hf` 查 `model_hf_key_mapping` |
| 访问方式 | 类方法 `hf_to_megatron`/`megatron_to_hf` | `ModelBase.__register_functions` 用 dict 项**动态合成** `get_/set_/has_<key>_weight` 一族函数，统一作用于 HF 与 Megatron module |
| 切分时机 | 转换即按当前 rank 切 | 离线 `Convert` 类（`convert_hf2mg.py`/`convert_mg2hf.py`）一次性重切分落盘 |

MindSpeed-LLM 转换侧的可复用能力（`Convert`/`Hf2MgConvert`/`Mg2HfConvert`）：

- **TP/PP/EP/VPP 重切分**：`--target-{tensor,pipeline,expert}-parallel-size`、
  `--num-layer-list`（动态 PP 划分）、`--num-layers-per-virtual-pipeline-stage`（VPP）、
  `--noop-layers`（自定义空层，转换后层数 = HF 层数 + 空层数），均匀 PP 要求模型层数能被 PP 数整除，否则添加 noop 层或使用动态 PP；VPP 与动态 PP 二选一；
- **Lora 合并/转换**：`--lora-load/-r/-alpha/--lora-target-modules` 把 Lora 权重与 base 合并后
  转 MG 或 HF；`--save-lora-to-hf` 把 Lora 权重单独导出为 **HF 格式**（源 checkpoint 须为 mcore 格式、fc_type=gate_up_down；该导出路径限制为 llama2/mixtral，不能与 --moe-grouped-gemm 或 --load-hf-from-config 同用）；
- mg→hf 时强制 `TP=PP=1`（HF 不分片），`--save-dir` 须为含 config/词表的原始 HF 目录。

> 选型：Bridge 路径与 Megatron-Core 训练态同进程、按 rank 实时映射，适合训练框架内桥接；
> MindSpeed-LLM 路径是离线批量重切分工具，适合落盘 checkpoint 的并行策略迁移与 Lora 合并。


## 灵活 PP/VPP 转换

当前离线转换新增 pipeline_model_parallel_layout，按 VPP-major 再 PP-major 分配 decoder 层。它与 num_layer_list、num_layers_per_virtual_pipeline_stage、schedules_method、noop_layers 互斥，当前不支持含 MTP 层的此类转换。不能因为训练侧支持某个 layout 就跳过转换器校验。

## Evidence

- [install_guide.md](../../../../../cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/docs/zh/install_guide.md)（primary）
- [install_auto.sh](../../../../../cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/tools/install_auto.sh)（implementation）
- [auto_register.py](../../../../../cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/mindspeed_bridge/runtime/auto_register.py)（implementation）
- [run_recipe.py](../../../../../cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/mindspeed_bridge/scripts/training/run_recipe.py)（implementation）
- [glm_moe_mappings.py](../../../../../cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/mindspeed_bridge/models/glm_moe_dsa/glm_moe_mappings.py)（implementation）
- [README.md](../../../../../cann-recipes-raw/mindspeed-bridge/f74d52a8a318c4594202ccdcf96a615b1f2d32da/mindspeed_bridge/examples/conversion/compare_hf_and_megatron/README.md)（implementation）
- [convert.py](../../../../../cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/tasks/checkpoint/convert.py)（implementation）
- [convert_hf2mg.py](../../../../../cann-recipes-raw/mindspeed-llm/72b0cca64535371e0bbf178087b88448c392970b/mindspeed_llm/tasks/checkpoint/convert_hf2mg.py)（implementation）

## Links

- [MindSpeed](mindspeed.md)
- [检查点管理](../techniques/checkpoint_dcp_hf.md)

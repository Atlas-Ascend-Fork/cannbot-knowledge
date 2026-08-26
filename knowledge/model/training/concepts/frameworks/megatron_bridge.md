---
type: Concept
title: MindSpeed-Bridge（Megatron-Bridge 昇腾非侵入适配 + HF↔Megatron 权重桥接）
description: >-
  MindSpeed-Bridge 通过外挂 mindspeed_bridge 包、少量 import 注入和 ConfigContainer.validate monkey-patch，在
  model.finalize 前调用 MindSpeed repatch，将 Megatron-Bridge 非侵入适配到昇腾。配置合并顺序为
  config.model、Bridge 控制位、extra_repatch_dict。权重桥接复用 MegatronParamMapping/AutoMapping：
  基类负责 TP 分片、跨 TP gather 和跨 PP 配置广播，模型派生类只实现 HF 布局与 Megatron 中间布局的重排。
  可用余弦相似度阈值 98% 和 roundtrip_hf 验证。该训练进程内桥接不同于 MindSpeed-LLM 离线 checkpoint
  转换；后者用于 TP/PP/EP/VPP 重切分、noop 层和 LoRA 合并或单独导出。
tags:
- task.implementation
- topic.architecture
- topic.compilation
- topic.checkpointing
status: stable
sources:
- resource: https://gitcode.com/Ascend/MindSpeed-Bridge/blob/3655c07cbcc9f61d16b11e7d7831573e542c0e92/README.md
  role: primary
- resource: https://gitcode.com/Ascend/MindSpeed-Bridge/blob/3655c07cbcc9f61d16b11e7d7831573e542c0e92/docs/zh/install.md
  role: supporting
created_at: '2026-06-24T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# MindSpeed-Bridge（Megatron-Bridge 昇腾非侵入适配 + HF↔Megatron 权重桥接）

MindSpeed-Bridge 把 NVIDIA **Megatron-Bridge**（NeMo 系的「HF 权重 ↔ Megatron-Core 训练」桥接层）
适配到昇腾 NPU。它**不 fork** Megatron-Bridge 本体，而是以一个外挂包 `mindspeed_bridge/` +
三处 import 注入 + 一个 `ConfigContainer.validate` monkey-patch，复用上游的 Bridge 权重桥接框架，
在 `validate()` 时机触发 [mindspeed](mindspeed.md) 的 repatch（昇腾算子/特性补丁）。
其**非侵入接入机制**与 **HF↔Megatron 双向权重映射抽象**是各模型 provider 的共同底座，当前覆盖两个模型族：**Qwen3.5-VL**（`qwen_vl/`，含 GatedDeltaNet 线性层映射）与 **GLM-5**（`glm_moe_dsa/`，MLA+DSA+MoE），各自的 `*_bridge.py`/`*_provider.py`/`*_mappings.py` 都在其上派生。

## 非侵入接入机制

接入只动 import，不改 Megatron-Bridge 源逻辑。`tools/install_auto.sh` 把
`mindspeed_bridge/` **整目录拷进** Megatron-Bridge 根目录，再做三处**追加式** import 注入
（事务式，任一步失败 `rollback_all` 回滚备份）：

| 注入点 | 文件 | 追加内容 | 作用 |
|--------|------|----------|------|
| 模型注册 | `src/megatron/bridge/models/__init__.py` | `from mindspeed_bridge.models import *` | 让自定义 provider/bridge 进入 Megatron-Bridge 模型表 |
| 配置注册 | `src/megatron/bridge/recipes/__init__.py` | `from mindspeed_bridge.recipes import *` | 注册训练 recipe |
| 训练入口 | `scripts/training/run_recipe.py` | `import mindspeed.megatron_adaptor` + provider forward_step 注册 | 拉起 MindSpeed 适配 + 挂自定义前向 |

逐模型的 forward_step（如 `qwen3_vl_step`）注册的机制即「在 `STEP_FUNCTIONS` dict 追加一项」：
新 provider 把自己的前向步函数挂进同一个 dict，即被训练入口 `run_recipe.py` 按 recipe 选用。
Step4 硬编码注册的是 `qwen3_vl_step`——因 Megatron-Bridge 0.3.1 尚未原生支持 `qwen35_vl`、必须手动补；上游缺哪个模型就手动追加哪个前向，并非自动泛化机制。

### repatch 触发机制（核心非侵入点）

`mindspeed_bridge/__init__.py` 只做一件事：**monkey-patch `ConfigContainer.validate`**。
包一层 `_patched_validate`，在调用上游原 `validate()` **之前**先跑
`apply_mindspeed_repatch(self)`，再走原逻辑（`utils/repatch.py`）：

```python
# mindspeed_bridge/__init__.py
_original_validate = ConfigContainer.validate
def _patched_validate(self) -> None:
    from mindspeed_bridge.utils.repatch import apply_mindspeed_repatch
    apply_mindspeed_repatch(self)   # MindSpeed repatch 必须在 model.finalize() 前生效
    _original_validate(self)
ConfigContainer.validate = _patched_validate
```

选 `validate` 作为切入点的原因：repatch 必须在 `model.finalize()` **之前**
落地，才能让 `pack_sequences_in_batch` 等特性被 MindSpeed 的 feature system 正确处理——
`validate` 是这之前唯一稳定的钩子。

`apply_mindspeed_repatch` 把 Bridge 侧 config 翻译成 MindSpeed `megatron_adaptor.repatch()`
的入参（`utils/repatch.py`），合并优先级 **`config.model` < Bridge 控制位 < `extra_repatch_dict`**：

- `build_model_repatch_config`：`asdict(config.model)` 摊平模型配置；
- `build_bridge_control_repatch_config`：从 `config.dataset` 抽 `pack_sequences_in_batch`、
  从 `config.model` 抽 `mtp_num_layers` 等 MindSpeed 也要感知的控制位；
- 若 `mindspeed.megatron_adaptor` 未安装则 `ImportError` 静默跳过（适配层对纯 GPU 环境无侵害）。

另有 `apply_mindspeed_args_patch`：用 `@wraps` 包 `mindspeed.args_utils.get_mindspeed_args`，
给返回的 args **就地注入/覆盖**字段；重复调用只更新已挂 wrapper 的 `_patch_dict`（幂等，避免
多层包裹）。统一入口 `apply_mindspeed_patches(config, args_patch_dict, extra_repatch_dict)`。

## HF↔Megatron 权重桥接框架

权重桥接框架复用上游 Megatron-Bridge 的 **`MegatronParamMapping` / `AutoMapping`** 抽象。
一个 ParamMapping 类绑定一组
`(megatron_param 名, hf_param 名)`，提供两个方向的方法，且**内建张量并行分片语义**：

- `hf_to_megatron(hf_weights, megatron_module)`：HF 全权重 → 按当前 `tp_rank`/`tp_size` 切出
  本 rank 的 Megatron 分片；
- `megatron_to_hf(megatron_weights, megatron_module)`：跨 TP rank **gather** 回完整张量再还原成
  HF 布局；跨 PP 用 `broadcast_obj_from_pp_rank` 同步 config；带量化时 `maybe_dequantize`；
- `resolve(captures)`：把名字里的占位（层号等正则 capture）解析成具体参数名，复制出一个就绪映射。

MindSpeed-Bridge 在此抽象上**派生模型专用映射**而非另造体系。例如
`mindspeed_bridge/models/conversion/param_mapping.py` 的 `GDNLinearMappingSeparate`
（GatedDeltaNet 输入投影，Qwen3.5 把 Q/K/V/Z/B/A 拆成四个独立 HF 矩阵）：内部用
`_fuse_gdn_separate_to_grouped` 把四张 flat HF 张量按 head 重排成上游
`merge_gdn_linear_weights` 能吃的 head-grouped `qkvz`/`ba`，再委托一个 `AutoMapping`
（`self._tp_mapping`）做实际 TP 切分；反向 `split_gdn_linear_weights` + `_split_gdn_grouped_to_separate`
还原四张 HF 张量。**复用价值**：要支持新模型只需写「HF 布局 ↔ 上游 grouped 中间态」的纯重排，
TP 分片逻辑全部交给基类，不碰并行细节。

### 单步精度对比验证

`examples/conversion/compare_hf_and_megatron/`（`compare.py`）是桥接正确性的验证工具：同一 prompt
分别跑 HF 模型与转换后的 Megatron 模型单步前向，比对 logits **余弦相似度（阈值 98%）**、Top-5、
最大/平均绝对差；支持 `--tp/--pp/--ep` 多卡、`--roundtrip_hf`（Megatron 再导回 HF 后对比闭环）、
`--enable_debug_hooks`（逐组件前/反向 JSONL 落盘）。注意 Megatron 可能为 kernel 效率 pad
`vocab_size`，对比时截断回 HF 词表大小。

## MindSpeed-LLM checkpoint 转换（另一条路径）

[mindspeed](mindspeed.md) 生态里 **MindSpeed-LLM**
（[mindspeed-llm](https://gitcode.com/Ascend/MindSpeed-LLM)）有一套独立、更早的 HF↔Megatron-Mcore 转换引擎
（`mindspeed_llm/tasks/checkpoint/`，入口 `convert_ckpt.py`），与 Bridge 路径定位重叠但**抽象不同**：

| 维度 | Megatron-Bridge | MindSpeed-LLM checkpoint |
|------|------------------------|--------------------------|
| 映射抽象 | `MegatronParamMapping` **类**，内建 TP 分片语义 | `module_mapping` **dict**，配置驱动 |
| 映射来源 | 代码里按模型派生类 | `configs/checkpoint/model_cfg.json` 按 `model_type_hf` 查 `model_hf_key_mapping`（覆盖 100+ 模型） |
| 访问方式 | 类方法 `hf_to_megatron`/`megatron_to_hf` | `ModelBase.__register_functions` 用 dict 项**动态合成** `get_/set_/has_<key>_weight` 一族函数，统一作用于 HF 与 Megatron module |
| 切分时机 | 转换即按当前 rank 切 | 离线 `Convert` 类（`convert_hf2mg.py`/`convert_mg2hf.py`）一次性重切分落盘 |

MindSpeed-LLM 转换侧的可复用能力（`Convert`/`Hf2MgConvert`/`Mg2HfConvert`）：

- **任意 TP/PP/EP/VPP 重切分**：`--target-{tensor,pipeline,expert}-parallel-size`、
  `--num-layer-list`（动态 PP 划分）、`--num-layers-per-virtual-pipeline-stage`（VPP）、
  `--noop-layers`（自定义空层，转换后层数 = HF 层数 + 空层数），VPP 与动态 PP 二选一；
- **Lora 合并/转换**：`--lora-load/-r/-alpha/--lora-target-modules` 把 Lora 权重与 base 合并后
  转 MG 或 HF；`--save-lora-to-hf` 把 Lora 权重单独导出为 **HF 格式**（约束源 checkpoint 须为 mcore 格式）；
- mg→hf 时强制 `TP=PP=1`（HF 不分片），`--save-dir` 须为含 config/词表的原始 HF 目录。

> 选型：Bridge 路径与 Megatron-Core 训练态同进程、按 rank 实时映射，适合训练框架内桥接；
> MindSpeed-LLM 路径是离线批量重切分工具，适合落盘 checkpoint 的并行策略迁移与 Lora 合并。

## Evidence

- 来源仓：[mindspeed-bridge](https://gitcode.com/Ascend/MindSpeed-Bridge) · [mindspeed-llm](https://gitcode.com/Ascend/MindSpeed-LLM)
- MindSpeed-Bridge blob（@3655c07）：
  - 非侵入 patch（`_patched_validate` / `ConfigContainer.validate`）：https://gitcode.com/Ascend/MindSpeed-Bridge/blob/3655c07cbcc9f61d16b11e7d7831573e542c0e92/mindspeed_bridge/__init__.py
  - repatch 翻译（`apply_mindspeed_repatch` / `build_*_repatch_config` / `apply_mindspeed_args_patch`）：https://gitcode.com/Ascend/MindSpeed-Bridge/blob/3655c07cbcc9f61d16b11e7d7831573e542c0e92/mindspeed_bridge/utils/repatch.py
  - 注入安装脚本（Step1 拷目录 + Step2-4 import 注入 + `rollback_all`）：https://gitcode.com/Ascend/MindSpeed-Bridge/blob/3655c07cbcc9f61d16b11e7d7831573e542c0e92/tools/install_auto.sh
  - 适配机制文档（§3 自动/手动适配）：https://gitcode.com/Ascend/MindSpeed-Bridge/blob/3655c07cbcc9f61d16b11e7d7831573e542c0e92/docs/zh/install.md
  - 权重映射（`GDNLinearMappingSeparate` / `_fuse_gdn_separate_to_grouped`，派生自 `MegatronParamMapping`/`AutoMapping`）：https://gitcode.com/Ascend/MindSpeed-Bridge/blob/3655c07cbcc9f61d16b11e7d7831573e542c0e92/mindspeed_bridge/models/conversion/param_mapping.py
  - 单步精度对比（`compare.py`，余弦阈 98% / `--roundtrip_hf`）：https://gitcode.com/Ascend/MindSpeed-Bridge/blob/3655c07cbcc9f61d16b11e7d7831573e542c0e92/mindspeed_bridge/examples/conversion/compare_hf_and_megatron/README.md
- MindSpeed-LLM blob（@183e02c）：
  - 转换基类（`Convert`，TP/PP/EP/VPP/noop 切分）：https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/checkpoint/convert.py
  - 动态合成访问器 + config 驱动 `module_mapping`（`ModelBase.__register_functions` / `get_module_mapping`）：https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/checkpoint/models.py
  - hf2mg 入口（`Hf2MgConvert`）：https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/mindspeed_llm/tasks/checkpoint/convert_hf2mg.py
  - 转换文档（HF↔Mcore + Lora 合并/转换 + 特性清单）：https://gitcode.com/Ascend/MindSpeed-LLM/blob/183e02c21011c2e423a599633cf2d55929ba9ea3/docs/zh/pytorch/tools/checkpoint_convert_hf_mcore.md

## Links

- 被 repatch 注入的训练加速底座：[mindspeed](mindspeed.md)
- 权重转换邻近概念：[model-custom-converter](model_custom_converter.md)（torchtitan-npu 声明式 `to_hf`/`from_hf` 路径）、[npu-fused-op-converters](npu_fused_op_converters.md)（融合算子权重布局改写）

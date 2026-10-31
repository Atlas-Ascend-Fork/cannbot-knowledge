---
type: Concept
title: TorchTitan / torchtitan-npu 训练框架
description: 基于当前插件结构说明 DTensor 并行、配置转换与显式 override、torchtitan_npu.train 入口和单机/多机 launcher 边界。
tags:
- task.implementation
- topic.architecture
- topic.graph_execution
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/architecture.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/user-guides/quickstart.md
  role: supporting
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/developer_guides/config_extensions.md
  role: supporting
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/train.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/__init__.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/scripts/run_train.sh
  role: implementation
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:24:41Z'
platforms:
- '950'
- a3
---

# TorchTitan / torchtitan-npu 训练框架

## 当前职责与边界

TorchTitan 使用 PyTorch 原生分布式训练抽象，以 DTensor 描述参数和计算的设备网格、Shard/Replicate/Partial 布局，组合数据、张量、流水、专家和上下文并行。torchtitan-npu 提供 Ascend NPU 插件、模型与融合算子适配；具体模型的可组合并行度必须以对应 recipe 验证，不能由“5D 并行”推导任意组合可用。

当前训练入口是 `torchtitan_npu.train`：先导入插件包，再调用上游 `torchtitan.train.main`。普通 recipe 可以返回上游 `Trainer.Config`，NPU 的配置转换链提供 `TrainerEx.Config` 扩展字段。

## 插件结构与启用时序

| 位置 | 当前职责 |
| --- | --- |
| `patches/` | 上游 TorchTitan、torch_npu 等尚需替换的实现与兼容补丁。 |
| `config/` | NPU 配置类型、配置转换及显式注册接口。 |
| `extensions/` | Trainer、checkpoint、图编译和可选外部包适配等扩展。 |
| `override/` | 由 `override.imports` 显式启用的组件或方法替换。 |
| `models/` | 尚未上游化的模型、配置、并行与 checkpoint 适配。 |
| `ops/` | 按 AscendC、Triton、TileLang、PyPTO 等后端组织的算子。 |
| `tools/` | checkpoint 转换和导出工具。 |

包入口的实际自动导入顺序为 `patches → config → extensions → ops`；`override` 不自动加载。`config.manager` 当前会安装 `ConfigManager._load_config` 的转换 wrapper，不能把配置模块当成完全无导入副作用。

当前架构同时记录迁移债务与未来目标。`TORCHTITAN_NPU_DISABLE_EXTENSIONS`、`TORCHTITAN_NPU_DISABLE_COMPONENTS` 尚未实现，不能用它们关闭现有扩展。旧 `converters/framework`、`converters/kernels` 下的 Model Custom 注册方案不能继续充当当前接线方式；配置与替换接口见[配置扩展与 override](model_custom_converter.md)，算子入口见[融合算子适配](npu_fused_op_converters.md)。

## 配置与启动

通用单机 launcher 的当前默认值：

| 项目 | 默认值 |
| --- | --- |
| `TRAIN_FILE` | `torchtitan_npu.train` |
| `MODULE` | `torchtitan.models.deepseek_v3` |
| `CONFIG` | `deepseek_v3_debugmodel` |
| `NGPU` | `1` |
| `LOG_RANK` | `0` |

`MODULE` 与 `CONFIG` 共同选择 Python 配置函数，脚本后的额外参数透传到训练入口。不能继续使用已移除的 `entry.py`、`deepseek_v32` 模块拼写或 TOML 路径作为当前默认入口。

```bash
NGPU=1 bash scripts/run_train.sh \
  --hf-assets-path tests/assets/deepseek_v3 \
  --dataloader.dataset c4_test \
  --dataloader.dataset-path tests/assets/c4_test \
  --training.local-batch-size 1 \
  --training.seq-len 2048 \
  --training.steps 5
```

仓库预置的 tokenizer 与测试数据用于 smoke test，不能替代目标模型的训练数据验收。通用脚本不读取 `HF_ASSETS_PATH`、`DATASET`、`DATASET_PATH` 环境变量；这些环境变量由具体 example launcher 解释，再转换为 CLI 参数。

设置 `ASCEND_SET_ENV_PATH` 可指定 CANN 环境脚本；未设置时 launcher 查找预置安装目录并加载可用的 `set_env.sh`，不再需要照搬旧版“启动脚本从不 source”的说明。脚本默认设置 `TORCHINDUCTOR_NPU_BACKEND=ascendc`，其他编译和优化行为仍须由实际配置启用。

多卡任务优先使用 `examples/` 中对应模型的 launcher。当前 DeepSeek-V4 debug 示例为 `examples/deepseek_v4/debug/deepseek_v4_flash_8p_cpt_4k_a3.sh`；多机示例用 `NODE_IPS` 顺序确定节点 rank。修改 tokenizer、checkpoint、网卡和并行度后，须核对最终打印的配置与各节点一致性。

## 当前功能与验证

- 显式 override、配置扩展和模型并行分别接线，不能把配置字段的存在等同于功能已被消费。
- `torch.compile` / Inductor、GraphTrainer、FSDP/EP、MTP、DCP 与优化器功能依赖模型 recipe 和组件组合。相关实现及失效边界分别查阅对应专页。
- TorchAO-NPU 的当前低精度训练文档限定 Ascend 950；即使复用文件名含 `a3` 的启动脚本，也不能据此推导低精度训练支持 A3。
- 来源中的 DeepSeek-V3.2 性能观测是该实践的测量，不能视为当前任意模型、拓扑和并行配置的固定收益；保留在[DeepSeek-V3.2 预训练实践](../../guides/recipes/deepseek_v32_pretrain.md)中核对。

先用少步数检查配置解析、NPU 初始化、数据形状、loss、梯度和 checkpoint 保存/恢复，再逐项开启编译、融合、低精度和通信重叠。必要时使用 `LOG_RANK=0,1,2,3` 查看多个 rank；异常时按组件撤回到已建立的基线。本仓未执行模型或 NPU 实测。

## 相关入口

- [5D 并行与 DTensor](../parallelism/torchtitan_5d_parallel.md)
- [FSDP](../parallelism/fsdp.md)
- [Muon](../techniques/muon_optimizer.md)
- [Virtual Optimizer](../techniques/virtual_optimizer.md)
- [Swap Optimizer](../techniques/swap_optimizer.md)
- [Checkpoint 与 HF 转换](../techniques/checkpoint_dcp_hf.md)
- [可观测与调试](../techniques/training_debug_observability.md)
- [低精度训练](../quantization/hif8.md)
- [DeepSeek-V4 续训](../../guides/recipes/deepseek_v4_continue_pretrain.md)

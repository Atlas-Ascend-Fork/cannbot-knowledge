---
type: Concept
title: torchtitan-npu 配置转换与显式 Override
description: 说明 TrainerConfigConverter 的配置转换、override.imports 的精确工厂选择与构建时序、冲突检查及组件语义边界。
tags:
- task.implementation
- topic.architecture
- topic.compilation
- topic.checkpointing
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/developer_guides/config_extensions.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/config/converters.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/config/manager.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/README.md
  role: supporting
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/architecture.md
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-10-29T12:06:32Z'
platforms:
- agnostic
---

# torchtitan-npu 配置转换与显式 Override

## 当前扩展模型

当前源码把 NPU 配置适配、组件选择与设备 kernel 分开：`TrainerConfigConverter` 把上游 Trainer 配置转换为 NPU 扩展 schema，`override.imports` 再显式选择配置节点的 replacement，后续 `build()` 创建实际组件。旧 `ModelCustomConfig`、`get_model_converter_config("npu_gmm")` 和 `converters/framework` 注册方案已不对应当前目录与激活链，不能继续复制旧的 module/parallel-plan/state-dict 三 hook 示例。

这张卡说明配置和替换机制；具体算子的输入、布局、并行和 checkpoint 条件仍由相应实现负责。

## Trainer 配置转换

`config/manager.py` 在导入时包装 `ConfigManager._load_config`，先调用原 loader，再按返回配置的实际类型查询已注册的 `TrainerConfigConverter`。注册时也为配置基类安装默认映射，以兼容上游模块在替换前捕获的 `Trainer.Config`；更专用的既有映射保留。

`TrainerConfigConverter.convert()` 的职责：

1. 已经是目标 Trainer 配置类型的实例直接返回。
2. 遍历 `component_types`，把配置分组转换为对应 NPU dataclass；仅复制源与目标共有且参与初始化的字段。
3. 使用 `derive(config, target_type, **deltas)` 构造目标 Trainer 配置。目标配置中新字段使用目标类型默认值。

组件目标必须是 dataclass 类型，源必须是 dataclass 实例；不满足时抛 `TypeError`。这是配置结构转换，不会替换模型 module、自动重排 EP 计划或转换 checkpoint 权重。

| 新字段职责 | 当前落点 | CLI 示例 |
| --- | --- | --- |
| 已有 NPU 训练分组 | 对应 extension dataclass | `--training.extension.allow-hf32` |
| optimizer 等上游组件 | 继承其配置，并在 TrainerEx/component_types 接线 | `--optimizer.name` |
| 独立根级扩展 | `ExtensionConfig` 子分组 | `--extension.quantization.recipe` |

字段定义只提供类型和 CLI，拥有该功能的 Trainer 或组件仍必须读取并应用该字段。

## 配置级 Override

每个 `override.imports` 项是完整 `module.function` 路径；只启用该工厂，不会连带启用模块内其他 override。例如：

```bash
--override.imports torchtitan_npu.override.common.rope.workaround
```

多个无参数项可使用空格或逗号分隔。带工厂关键字参数时，将整个 `target=<JSON object>` 作为一个 shell 参数：

```bash
--override.imports \
  'torchtitan_npu.override.deepseek_v4.sparse_attn.asc={"num_heads":128}'
```

应用时序是在配置 `update_from_config()` 后、任何组件 `build()` 前：

1. 导入指定模块，触发 `@override` 注册。
2. 解析本次请求的工厂函数。
3. 基于原始配置树，按 `target`、`exact`、`fqns` 收集所有匹配节点。
4. 在修改前检查同节点及祖先/后代节点冲突。
5. 生成 replacement config，由后续构建过程创建组件。

匹配基于修改前的配置树，replacement 不会被再次遍历，因此调整条目顺序不能解决两个 override 争用同一节点的问题。Float8、LoRA 等 converter 在 override 前执行，需要按转换后的配置类型与 FQN 检查匹配。

## 最小 replacement 的职责

replacement 通常继承目标配置，借助 `derive()` 保留共有字段。例如 `rms_norm.asc` 精确表达使用 `torch_npu.npu_rms_norm` 的组件替换；不是“导入任意 kernel 文件就替换整网”。

- `target` 必须是 `Configurable.Config` 子类；默认可匹配子类，只支持具体类型时声明 `exact=True`。
- `fqns` 可用 glob 收窄配置节点范围；当前来源说明仓内入口尚未采用该限定。
- 自定义 kernel 通过 `torch.library` 提供 schema、fake/meta 和 Autograd，replacement module 再调用它。
- 输入输出、DTensor、sharding、checkpoint 以及 `torch.compile` 语义均由 replacement 保持，不能由成功注册推导正确性。

## Package patch 与排查

导入 `torchtitan_npu.override.*` 仍会先执行包入口，因此自动 patch/extension 也会生效。配置级 override 由本次请求选择，包 patch 则随 `torchtitan_npu` 导入激活，两者不能当成同一层机制。

未生效时检查完整工厂名、最终配置类型、匹配 FQN 及 `[Override]` / `Applied N override(s)` 日志。发生同节点或嵌套节点冲突时，应选择一个覆盖正确范围的 replacement，或通过合法 FQN 限定缩小范围，不能靠重排字符串掩盖冲突。组件构建后再验证前后向、并行布局与保存/恢复；本仓未执行 NPU 验证。

## 相关入口

- [TorchTitan 框架与导入结构](torchtitan.md)
- [融合算子与当前 override 入口](npu_fused_op_converters.md)
- [并行与 DTensor](../parallelism/torchtitan_5d_parallel.md)
- [Checkpoint](../techniques/checkpoint_dcp_hf.md)
- [VLM 训练](../modules/vlm_multimodal_training.md)

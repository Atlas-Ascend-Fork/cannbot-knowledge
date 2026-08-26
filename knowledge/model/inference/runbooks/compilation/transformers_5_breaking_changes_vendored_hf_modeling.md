---
type: Runbook
title: transformers 5.0.0 破坏性升级打断 vendored HF 建模/config 文件的 import 与取值
description: 'cann-recipes-infer 的建模/config 文件多是从 HuggingFace transformers 上游"复制粘贴 + 昇腾改写"得来（文件头注明 # This code is copied from ... transformers/...）。把 requirements.txt 的 transformers 从 4.5x 升到 5.0.0（破坏性大版本）后，这些 vendored 文件会在导入期或 config 取属性期直接报错——ImportError（命中被移除的符号）或 AttributeError（config 字段改名/合并）。症状随文件不同，但根因都是"沿用 4.5x 的 API 写法撞上 5.0.0 的重构"。'
tags:
- task.debugging
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/418
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/423
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# transformers 5.0.0 破坏性升级打断 vendored HF 建模/config 文件的 import 与取值

## 信号（现象）

cann-recipes-infer 的建模/config 文件多是从 HuggingFace transformers 上游"复制粘贴 + 昇腾改写"得来（文件头注明 `# This code is copied from ... transformers/...`）。把 `requirements.txt` 的 transformers 从 4.5x 升到 **5.0.0**（破坏性大版本）后，这些 vendored 文件会在**导入期或 config 取属性期直接报错**——`ImportError`（命中被移除的符号）或 `AttributeError`（config 字段改名/合并）。症状随文件不同，但根因都是"沿用 4.5x 的 API 写法撞上 5.0.0 的重构"。

## 触发条件

`transformers == 5.0.0`（或任何已做同类重构/删符号的更高版本）+ vendored 自 HF 的建模/config 文件。加载/import 模型即触发（model bringup 阶段）。

## 根因 + 修法（逐点对号入座）

### A. config API 重构（config 文件）

观测于 `configuration_qwen3_moe.py` / `configuration_gpt_oss.py`，四个失效点：

1. **基类改名**：`PretrainedConfig` → `PreTrainedConfig`（大写 T）。旧名在 5.0.0 不存在，`from transformers.configuration_utils import PretrainedConfig` 导入即 `ImportError`。类继承同改。
2. **RoPE 参数聚合**：4.5x 的 `rope_theta: float` + `rope_scaling: dict` 两独立字段，5.0.0 合并为单个 `rope_parameters: RopeParameters` 字典；`rope_config_validation` 被移除，改 `from transformers.modeling_rope_utils import RopeParameters`。凡读 `config.rope_theta` 处会 `AttributeError`（`modeling_qwen3_moe.py` 两处：`Qwen3MoeRotaryEmbedding.base`、`Qwen3MoeAttention.rope_theta`）。修法：读值改成 `config.rope_parameters.get("rope_theta", <default>)`。
3. **特殊 token id 不再默认注入**：4.5x 里 `pad_token_id`/`bos_token_id`/`eos_token_id` 由 `super().__init__(**kwargs)` 经父类处理；5.0.0 后不再作为默认 config 属性存在，代码若假设 `config.pad_token_id` 存在会**直接报错**（维护者原文："更新至 5.0.0 后 config 中不存在 pad_token_id 变量，会直接报错"）。修法：在 config `__init__` 里显式赋这三个 id 为自身属性、并在 `super().__init__()` 前赋值。
4. **`layer_type_validation` 签名变更**（gpt_oss）：`layer_type_validation(self.layer_types)` → `layer_type_validation(self.layer_types, self.num_hidden_layers)`，缺第二个入参报错。

关键 diff（`configuration_qwen3_moe.py`）：

```python
-from transformers.configuration_utils import PretrainedConfig
-from transformers.modeling_rope_utils import rope_config_validation
+from transformers.configuration_utils import PreTrainedConfig
+from transformers.modeling_rope_utils import RopeParameters
-class Qwen3MoeConfig(PretrainedConfig):
+class Qwen3MoeConfig(PreTrainedConfig):
-        rope_theta=10000.0,
-        rope_scaling=None,
+        rope_parameters: RopeParameters | dict[str, RopeParameters] | None = None,
+        pad_token_id: int | None = None,
+        bos_token_id: int | None = None,
+        eos_token_id: int | None = None,
-        rope_config_validation(self)
+        self.rope_parameters = rope_parameters
-        super().__init__(tie_word_embeddings=tie_word_embeddings, **kwargs)
+        self.pad_token_id = pad_token_id; self.bos_token_id = bos_token_id
+        self.eos_token_id = eos_token_id; self.tie_word_embeddings = tie_word_embeddings
+        super().__init__(**kwargs)
```

（`modeling_qwen3_moe.py` 读值处随之：`self.base = self.config.rope_parameters.get("rope_theta", 1000000.0)`。gpt_oss 同款处理，`default_theta = 150000.0`。）

### B. 被移除的内部私有 helper `is_torch_fx_available`（建模文件）

观测于 DeepSeek 系/Kimi 的建模文件（`deepseek-v3.2-exp/models/modules.py`、`deepseek-v4/models/modules/common_modules.py`、`deepseek_r1/models/modules.py`、`kimi-k2-thinking/models/modules.py`，均 vendored 自 HF 的 DeepseekV3 派生结构）。5.0.0 移除了 `transformers.utils.import_utils.is_torch_fx_available`，文件顶部 `from transformers.utils.import_utils import is_torch_fx_available` 直接抛 `ImportError`，建模文件无法 import。

修法：不依赖 transformers-internal helper，改本地能力探测（语义等价）：

```python
# Compatibility fix for transformers 5.0.0: is_torch_fx_available was removed
try:
    import torch.fx
    _torch_fx_available = True
except ImportError:
    _torch_fx_available = False

if _torch_fx_available:      # 原 if is_torch_fx_available(): 全部替换为本地标志
    if not is_torch_greater_or_equal_than_1_13:
        import torch.fx
```

（同段的 `is_torch_greater_or_equal_than_1_13` 来自 `transformers.pytorch_utils`，5.0.0 未移除、无需改。该守卫作用是把 `_prepare_4d_causal_attention_mask` 标记为 FX graph 的 leaf function，只在 torch.fx 可用时生效。）

## 可迁移的失败签名

vendored HF 建模/config 文件会耦合 transformers 的公有/私有 API；transformers 大版本升级可能改名或删除这些 API 而破坏 bringup。稳妥修法是**不依赖 transformers-internal helper、改用等价的本地能力探测**（如 `import torch.fx` 判 FX 可用性），并对号处理 config 字段改名/合并（[qwen3-moe](../../concepts/models/qwen3_moe.md)、[gpt-oss](../../concepts/models/gpt_oss.md) 的 config 已按 A 处理；[deepseek-r1](../../concepts/models/deepseek_r1.md) / [deepseek-v4](../../concepts/models/deepseek_v4.md) 等的建模文件已按 B 处理）。

## Evidence

- **A / 代码事实**（合并 diff）：`configuration_qwen3_moe.py`(58+/90-)、`configuration_gpt_oss.py`(61+/39-)、`modeling_qwen3_moe.py`(2+/2-)、`requirements.txt` 三处 `transformers==5.0.0`。
- **A / 维护者确认**："pad_token_id 5.0.0 后不存在会直接报错"在 diff 讨论中由维护者明确答复。
- **B / 代码事实**（clone `@ca88532c7843`，单 commit）：4 个建模文件删 `is_torch_fx_available` 导入、加本地 `try: import torch.fx` 探测、`if is_torch_fx_available():` → `if _torch_fx_available:`。
- 溯源下探：
  - [cann-recipes-infer-pr-418-fix-fix-model-config-explanation-update-cann-version-and-fix-r1-multistr](https://gitcode.com/cann/cann-recipes-infer/merge_requests/418)
  - [cann-recipes-infer-pr-423-fix-transformers-5-0-0](https://gitcode.com/cann/cann-recipes-infer/merge_requests/423)
- 范围限定本仓这些文件与所列符号，不外推为"所有 transformers 版本兼容问题"通用律。

---
type: Runbook
title: aclgraph 图捕获前 monkeypatch upstream graph_capture：用 __base__ 定位模块对多级子类失效，须沿 MRO 找 GPUModelRunner
description: vLLM-Ascend 在 aclgraph 捕获前需把 upstream gpu_model_runner 模块的 CUDA graph_capture 替换为 NPU 版本。若用 self.__class__.__base__.__module__ 定位模块，只对直接继承 GPUModelRunner 的一级子类有效；XliteModelRunner 等多级子类会 patch 到错误模块，upstream 函数未替换并在初始化或捕获时失败，super().capture_model() 也可能递归回本地 override。修复是沿完整 MRO 找到 GPUModelRunner，使用其 __module__ 定位模块，找不到时抛 TypeError，并显式调用 GPUModelRunner.capture_model(self)。该规律适用于需要 monkeypatch 上游模块函数的多级继承场景，一级子类通常不会暴露此问题。
tags:
- task.debugging
- topic.graph_execution
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/5887
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# aclgraph 图捕获前 monkeypatch upstream graph_capture：用 __base__ 定位模块对多级子类失效，须沿 MRO 找 GPUModelRunner

## 信号（现象）

开启 [aclgraph（昇腾 NPU 图模式）](../../concepts/techniques/npu_graph_mode.md)后，某个 model runner 子类**初始化 / 图捕获失败**——症状形如 `XxxModelRunner init failed when aclgraph is enabled`。触发面很窄：**只有比「直接继承 upstream 基类的一级子类」更深一级的 model runner 子类**才会撞上；一级子类（在 vllm-ascend 中即 `NPUModelRunner`）反而正常。若你的类层级是「upstream `GPUModelRunner` → `NPUModelRunner` → 你的 `XxxModelRunner`」这种两级或更多级继承，且 aclgraph 下初始化就挂，就是本签名。

判别边界：这不是「aclgraph 本身不支持该模型」，而是 **图捕获前的一个 monkeypatch 打错了模块** 导致的伪失败；一级子类可正常初始化、深层子类才失败，是最直接的判别特征。

## 触发条件

- 框架：vllm-ascend（vLLM 在昇腾 NPU 上的适配 fork），`vllm_ascend/worker/model_runner_v1.py`。
- 场景：启用 aclgraph（昇腾 NPU graph capture）时的 model runner 初始化 / `capture_model`。
- 类层级出现**多级继承**：upstream vLLM 的 `GPUModelRunner`（模块 `vllm.v1.worker.gpu_model_runner`）→ vllm-ascend 的 `NPUModelRunner(GPUModelRunner)` → 再派生 `XliteModelRunner(NPUModelRunner)` 之类比一级子类更深的 runner。
- 定位「待 patch 模块」的写法用了**直接基类** `self.__class__.__base__.__module__`。

## 根因

aclgraph 图捕获要成立，必须在进入 upstream `GPUModelRunner.capture_model()` 之前，把 upstream 模块 `vllm.v1.worker.gpu_model_runner` 里的 `graph_capture` 函数替换成 NPU 适配版。替换的实现是对目标模块做 `setattr`：

```python
# _replace_gpu_model_runner_function_wrapper(target_module_name) 本质
setattr(sys.modules[target_module_name], "graph_capture", <npu graph_capture>)
```

这一步 monkeypatch 本身是**昇腾特有适配**——upstream 模块里放的是 CUDA 版 `graph_capture`，NPU 图捕获必须把它换成 NPU 版才能走对路径。bug 不在替换机制，而在**「怎么算出 target_module_name」**：

原实现用 `parent_module_name = self.__class__.__base__.__module__`（取直接基类的模块名）。`__base__` 是**直接父类**，只对一级子类碰巧正确：

- 对 `NPUModelRunner`：`__base__` 恰是 `GPUModelRunner`，`__module__` 恰是 upstream `vllm.v1.worker.gpu_model_runner`——巧合成立。
- 对 `XliteModelRunner`：`__base__` 是 `NPUModelRunner`，`__module__` = `vllm_ascend.worker.model_runner_v1`——patch 被打到 **vllm-ascend 自己的模块**上，upstream 模块里的 `graph_capture` 仍是 CUDA 版，从未被替换，NPU 图捕获走错误路径而失败。

同一个 bug 还有第二面：原代码 `super().capture_model()` 从 `XliteModelRunner` 出发按 MRO 解析到的是 `NPUModelRunner.capture_model`（即本 override 自身），而非 upstream `GPUModelRunner.capture_model` 的真实现——深层子类里 `super()` 会递归回自己这层。

一句话根因：**用「直接基类」的模块名去定位 upstream，隐含了「本类是 upstream 一级子类」的假设；一旦继承加深，`__base__` 指向中间层而非 upstream，patch 与调用双双错位。**

## 修法

沿**完整 MRO** 扫描出类名为 `GPUModelRunner` 的类，取其 `__module__` 作为待 patch 模块名，并**直接调用基类方法**而非 `super()`：

```python
def capture_model(self) -> None:
    gpu_model_runner_cls = next((cls for cls in self.__class__.__mro__
                                 if cls.__name__ == "GPUModelRunner"),
                                None)
    if gpu_model_runner_cls is None:
        raise TypeError("Could not find GPUModelRunner in the MRO. "
                        "The class hierarchy may have changed.")
    parent_module_name = gpu_model_runner_cls.__module__
    with _torch_cuda_wrapper(), _replace_gpu_model_runner_function_wrapper(
            parent_module_name):
        GPUModelRunner.capture_model(self)
```

要点：

- **不再用 `__base__`（直接基类），改沿 `self.__class__.__mro__` 找到类名 `GPUModelRunner` 的类**——无论子类嵌套多深，都稳定拿到 upstream 模块 `vllm.v1.worker.gpu_model_runner`，NPU 的 `graph_capture` patch 打对位置。
- 找不到 `GPUModelRunner` 时**抛 `TypeError` 显式失败**（类层级已变），而非静默走错模块。
- 调用改为 `GPUModelRunner.capture_model(self)`——**跳过中间 override 直达 upstream 基类方法**，避免 `super()` 在深层子类里递归回本 override。

通用规律（可迁移到任何「运行时 monkeypatch upstream 某模块的函数、且本类是 upstream 类的多级子类」场景）：**要定位 upstream 类所在模块，别用 `__base__`，用「沿 MRO 找到那个具体 upstream 类、取它的 `__module__`」；调用 upstream 方法用 `UpstreamCls.method(self)` 而非 `super()`。** `__base__` / `super()` 的行为随继承深度漂移，MRO 精确定位不漂移。

等价的更稳健写法：因该模块已 `import GPUModelRunner`，可用 `isinstance(self, GPUModelRunner)` + 直接 `GPUModelRunner.__module__` 定位，免去按字符串名遍历 MRO；合并态采用 MRO 字符串名扫描版，两者对本 bug 等效。

## 参考实现及其约束

- 这是 **vllm-ascend `model_runner_v1.py` 特定的 upstream 桥接机制**：aclgraph 捕获前把 upstream vLLM 模块里的 CUDA `graph_capture` `setattr` 替换成 NPU 版。「必须替换 `graph_capture`」这一约束是昇腾 / upstream 后端桥接特有的，不是各硬件通用逻辑。
- 失败签名的**可迁移面**是「Python 继承层级 + upstream 模块定位 + 图捕获前 patch」：任何比一级子类更深的 vllm-ascend model runner，若沿用 `__base__` 取模块名，都会在 aclgraph 下命中同一 patch-错位失败——该规律由继承行为本身决定，不随版本推进自动消失。
- 纯正确性修复，source 未给 before→after 性能数字。

## 相关经验

- aclgraph 只捕获稳态 decode 段、full 图捕获的范围与守卫见 [SFA/DSA 下 aclgraph full 仅 decode 捕获](sfa_dsa_aclgraph_full_decode_only_capture.md)。
- 图捕获 / 图注册的替换点守卫与融合注册风险见 [图融合注册替换守卫](../../optimizations/experience/rules/graph_fusion_register_replacement_guardrails.md)。
- 运行时 monkeypatch 层替代 fork 做上游模型昇腾适配（patch 注入时机 / triton stub / 权重同步三前置）见 [上游 DiT 运行时 monkeypatch 适配](../../guides/experience/interventions/upstream_dit_video_monkeypatch_npu_adaptation.md)。
- 昇腾图模式的入口决策与 backend 见 [npu-graph-mode](../../concepts/techniques/npu_graph_mode.md)；[TorchAir](../../concepts/frameworks/torchair.md) 图模式后端。

## Evidence

- 合并态 diff：`capture_model` 由 `__base__.__module__` 改为沿 `self.__class__.__mro__` 找 `GPUModelRunner` 取 `__module__`、`super().capture_model()` 改为 `GPUModelRunner.capture_model(self)`、找不到时抛 `TypeError`；`_replace_gpu_model_runner_function_wrapper` 对 `sys.modules[target_module_name]` 的 `graph_capture` 做 `setattr` 替换。见 merge commit `vllm-project/vllm-ascend@cb6cd09388b15f9ceff943b7e62f8cc22fdf2cb6` 下 `vllm_ascend/worker/model_runner_v1.py` 全文与 diff。
- 根因（patch 打错模块）由 source 描述「Ensure function graph_capture of vllm.v1.worker.gpu_model_runner is replaced」、评审意见（继承来的 capture_model 误判待 patch 模块、对昇腾 NPU graph capturing 必需）与 diff 因果一致得出。
- 溯源下探：[vllm-ascend-pr-5887-v0-13-0-bugfix-fix-xlitemodelrunner-init-failed-when-aclgraph-is-enabled](https://github.com/vllm-project/vllm-ascend/pull/5887)（sha `cb6cd09388b15f9ceff943b7e62f8cc22fdf2cb6`）。

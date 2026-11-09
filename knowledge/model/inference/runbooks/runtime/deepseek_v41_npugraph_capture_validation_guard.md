---
type: Runbook
title: recipes专用：抓图预检开关的类型与模式
description: 仅适用于 recipes/CANN Executor 的 unsafe_skip_npugraph_capture_validation：核对真实 bool 与 npugraph_ex 传参边界，保持默认预检。
tags:
- task.debugging
- topic.graph_execution
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:37:06Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：抓图预检开关的类型与模式边界
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# recipes专用：抓图预检开关的类型与模式

## 适用性与框架边界

本卡 guard 与配置处理仅适用于 recipes/CANN Executor。`unsafe_skip_npugraph_capture_validation`/`npugraph_ex` 是该执行器路径中的开关/模式，不能映射为 vLLM 编译或图捕获参数，也不是修复 vLLM 抓图失败的建议。

通用原则：解析后的严格类型、模型 guard、后端选项传递和实际 capture/replay/输出分别取证；跳过验证不等于修复执行错误。

必要条件：只有采用这里的模型检查和 compile_model_forward 分支，才适用下文类型/模式真值表；默认保持 False。没有证据支持开启跳过预检来修复任何后端。

recipes 专属操作：检查这个具体键、仅 True 时要求 npugraph_ex、仅该分支传同名 backend 键以及 cache_compile/torch.compile 参数路径均属于参考执行器。

vLLM 读者可在自身配置解析、模型加载与图执行准备职责中分别找真实类型检查、capture 诊断和 replay 验收；不要添加或启用本卡开关。未验证 vLLM 接入或版本兼容。

## 现象

推理前向把 token 行、hidden state 与缓存等输入送入模型；图执行把前向转换为可重复执行的编译/抓图路径。配置 guard 是启动时对选项的检查，capture validation 是后端对抓图条件的检查，实际回放及输出验收又是下一层证据。通过前一层不能替代后一层。

recipes/CANN Executor 当前 unsafe_skip_npugraph_capture_validation 默认 False。装载检查要求它是 Python bool；只有值为 True 时还要求 exe_mode 为 npugraph_ex。编译入口只在 npugraph_ex 分支且值为真时把同名键传给后端。源码没有“分析 capture 失败并修复依赖”的逻辑，因此不能因跳过预检就宣称抓图问题解决。

本卡能判别的是非布尔值与不匹配的模式组合，不是某条具体 capture 报错的根因。这里没有原始 NPU capture 错误、编译输出或回放结果。

## 适用场景

仅用于 recipes/CANN Executor 的 V4.1 装载前配置检查和 compile_model_forward 选项传递的静态诊断。源码目标 Ascend 950，CANN/torch_npu/npugraph_ex 实际运行版本未知；适用粒度 exact_task，路线 recommended_fastpath，含义是保持默认 False 并核对类型/模式，不建议开启跳过验证。

可迁移的是把“解析后的配置值→模型 guard→编译后端参数→运行证据”分层核对。其它框架的开关名称和抓图契约需自行确认。低时延 TP 另有 eager/npugraph_ex 模式限制，此键不能解锁 GE 支持。

## 判别方法

在该 recipes 执行器中找到配置反序列化/覆盖入口、模型装载前检查、编译选项构造和实际 capture/replay 调用点。外部框架只借鉴分层取证方法，具体检查应使用其自身配置合同。首先保存最终配置的原始值与类型、exe_mode、选中的编译后端、缓存编译开关；若配置由多层合并，回查哪一层把 bool 变成字符串或覆盖成 True。

**recipes guard 教学推演（非 CPU/NPU 实测）**：以下仅按内联 guard 的条件推导，不是其它框架的配置真值表：

| 配置值 | 模式 | 该 guard 的结果 | 应如何处理 |
|---|---|---|---|
| 缺省或布尔 False | npugraph_ex | 不被此 guard 拒绝；编译选项不添加跳过键 | 保持默认，继续查实际 capture 诊断 |
| 布尔 False | 其它模式 | 不被此 guard 拒绝 | 另查该模式自身限制，不能推导模式整体受支持 |
| 字符串 "false" 或整数 0 | 任意 | TypeError | 在配置生产处恢复真实 bool；不要靠字符串真假转换 |
| 布尔 True | 非 npugraph_ex | ValueError | 撤销跳过选项，回到默认 False |
| 布尔 True | npugraph_ex | 此 guard 放行并可能传后端键 | 仅说明配置分支成立，不能作为抓图修复或验收 |

字符串 "false" 的外观像否定，但它不是 bool；模型 guard 会拒绝它。若某个调用入口绕开模型检查直接进入 compiler，就更应核对实际参数，不能用配置文件的视觉外观判断默认路径是否生效。源码只保证上述经过 guard 的行为。

诊断先处理类型/模式错误，再检查 npugraph_ex 分支的 compile_options：默认情况下没有 unsafe_skip_npugraph_capture_validation 键，cache_compile 与 torch.compile 应收到同一组受控选项。若走 GE 分支，该键不被传递；不能据它的存在解释 GE 的编译错误。

修正配置后，在默认不跳过预检的路径重新执行，保存真正的 capture 错误与后端诊断。随后针对错误所指的输入、缓存、流/通信或算子条件定位，分别检查编译、capture、replay 与输出；这是一条待执行的排查路径，本卡没有证明其中哪项是本次根因。若仍失败，应保留失败证据并回到已有可运行的受支持配置，不用跳过检查获得“通过”。以下仅是 recipes 原仓可选导航：

```bash
rg -n 'compile_model_forward' executor/utils/graph_utils.py
```

## 完整代码

以下仅为 recipes/CANN Executor 的完整源码对照；保留逐块导读用于核验，外部框架无需采用其目录、类名或配置结构。

<details>
<summary>展开 recipes 参考实现：完整代码与逐块导读</summary>

以下保留固定源码中的完整函数或因果块；块外导读说明它们怎样连接。

`compile_model_forward` 输入待编译 callable 与 infer_config，返回编译后的 callable；返回函数并不证明已经抓图或成功回放。`exe_mode` 决定 npugraph_ex/GE 两条路径，`enable_cache_compile` 决定缓存编译入口，`cache_namespace` 细分缓存目录，`enable_dynamic_graph` 传给 npugraph_ex 编译。`compile_options` 只在 npugraph_ex 分支构造，frozen_parameter 在此固定为 True；后面的 GE CompilerConfig 则消费函数参数。这些选项各有职责，均不是输出正确性的验证信号。

```python
def compile_model_forward(
    model_forward,
    infer_config,
    frozen_parameter=True,
    tiling_schedule_optimize=True,
    topology_sorting_strategy="StableRDFS",
    cache_namespace=None,
):
    """
    Compile a model.forward method for graph execution.

    Args:
        model_forward: The model.forward callable to compile.
        infer_config: Inference config that provides model graph compile options.
        frozen_parameter: Whether to freeze parameters.
        tiling_schedule_optimize: Whether to enable tiling schedule optimization.
        topology_sorting_strategy: Strategy for topology sorting.
        cache_namespace: Optional subdirectory for an independent static graph shape.

    Returns:
        Compiled forward function.
    """
    import torchair as tng
    import torchair.ge_concrete_graph.ge_converter.experimental.patch_for_hcom_allreduce
    tng.patch_for_hcom()
    # Compile model forward
    torch._dynamo.config.inline_inbuilt_nn_modules = False

    model_config = infer_config.model_config
    exe_mode = model_config.exe_mode
    enable_cache_compile = model_config.enable_cache_compile
    enable_dynamic_graph = model_config.enable_dynamic_graph
    unsafe_skip_npugraph_capture_validation = model_config.custom_params.get(
        "unsafe_skip_npugraph_capture_validation", False
    )
    cache_dir = os.path.join(model_config.output_path, "compile_cache")
    if cache_namespace:
        cache_dir = os.path.join(cache_dir, cache_namespace)
    enable_static_kernel = model_config.enable_static_kernel
    enable_superkernel = model_config.custom_params.get("enable_superkernel", False)

    if exe_mode == "npugraph_ex":
        # npugraph_ex uses torch.compile or cache_compile directly with backend options.
        compile_options = {
            "frozen_parameter": True,
            "static_kernel_compile": enable_static_kernel,
            "super_kernel_optimize": enable_superkernel,
            "super_kernel_optimize_options": {"dcci_disable_on_kernel": [".*"]},
        }
        if unsafe_skip_npugraph_capture_validation:
            compile_options["unsafe_skip_npugraph_capture_validation"] = True
        if enable_cache_compile:
            compiled = torch.npu.npugraph_ex.inference.cache_compile(model_forward, cache_dir=cache_dir,
                                                                     dynamic=enable_dynamic_graph,
                                                                     options=compile_options)

        else:
            compiled = torch.compile(model_forward, dynamic=enable_dynamic_graph, fullgraph=True,
                                     backend="npugraph_ex", options=compile_options)

        return compiled

    # Create and configure CompilerConfig
    compiler_config = CompilerConfig()
    compiler_config.experimental_config.frozen_parameter = frozen_parameter
    compiler_config.experimental_config.tiling_schedule_optimize = tiling_schedule_optimize
    compiler_config.experimental_config.topology_sorting_strategy = topology_sorting_strategy
    # Compile model forward
    if enable_cache_compile:
        if cache_dir is None:
            raise ValueError("cache_dir must be provided when enable_cache_compile=True")

        compiled = tng.inference.cache_compile(
            model_forward,
            cache_dir=cache_dir,
            config=compiler_config,
            dynamic=False,
            fullgraph=True,
            ge_cache=True
        )
    else:
        npu_backend = tng.get_npu_backend(compiler_config=compiler_config)
        compiled = torch.compile(model_forward, dynamic=False, fullgraph=True, backend=npu_backend)

    return compiled
```

装载前检查块读取未经 bool(...) 强制转换的原值：先 isinstance(...,bool)，再判断 True 与模式的组合。`enable_cache_compile/enable_superkernel/moe_chunk_max_len/with_ckpt` 是同一因果块的上下文，不能把它们当成该开关的替代验证。两个异常分别定位类型错误与模式错误。

```python
        exe_mode = model_config.exe_mode
        enable_cache_compile = model_config.enable_cache_compile
        enable_superkernel = custom_params.get("enable_superkernel", False)
        unsafe_skip_capture_validation = custom_params.get(
            "unsafe_skip_npugraph_capture_validation", False
        )
        moe_chunk_max_len = custom_params.get("moe_chunk_max_len", 65536)
        with_ckpt = model_config.with_ckpt

        if not isinstance(unsafe_skip_capture_validation, bool):
            raise TypeError(
                "custom_params.unsafe_skip_npugraph_capture_validation must be a boolean"
            )
        if unsafe_skip_capture_validation and exe_mode != "npugraph_ex":
            raise ValueError(
                "custom_params.unsafe_skip_npugraph_capture_validation only supports "
                "exe_mode='npugraph_ex'; "
                f"got exe_mode='{exe_mode}'"
            )
```

</details>

## 设计决策

默认 False 让后端保留 capture 预检。当前代码只约束用户显式提供的选项，并在特定模式下传递它；既没有基于 capture 失败自动更改开关，也没有给出启用 True 的修复配方。诊断应修配置和根因，不能把少了一道检查当成正确性改善。

## 系统信息

配置 guard 位于 `models/deepseek_v4_1/models/modeling_deepseek.py`，编译选择位于 `executor/utils/graph_utils.py`。完整编译函数依赖原工程和后端；本卡不运行编译或抓图。

## 预防

配置解析后立即检查该键的值与类型，默认保持 False；记录编译模式及实际传递选项。验收记录分别保存配置检查、编译、capture、replay 与输出结果，不用“进入后端”替代后续验证。

## 验证信号

固定源码核对确认 compile_model_forward 的默认值/条件传递，以及装载前类型与模式 guard。只证明静态控制流，未执行此 guard 的 CPU 测试，也没有 NPU capture 或回放结果。（来源平台：源码目标 950；证据等级：artifact_verified。）

## 失效边界

没有原始 capture 错误、NPU 编译输出、真实权重装载或回放验证。True+npugraph_ex 通过 guard 仅表示未被该 guard 拒绝；后端版本是否接受该键、实际抓图是否正确均未知。跳过预检可能隐藏待诊断问题，本卡不提供开启路线或修复 vLLM 抓图的建议，更不能借此扩展低时延 TP 的模式支持范围。

## 坏实践

把字符串 "false" 当布尔 False；使用 True 绕过失败预检并宣称修复；为通过此 guard 主动改成跳过验证的模式组合；编译返回 callable 后省略 capture/replay 与输出检查。

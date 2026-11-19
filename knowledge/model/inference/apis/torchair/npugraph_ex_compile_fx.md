---
type: API
title: npugraph_ex.compile_fx：AOT 后 FX 编译与功能缺口
description: 说明直接编译 FX 的输入和可执行返回值，明确自定义后端不继承全部 npugraph_ex 能力。
tags:
- task.lookup
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/api/npugraph_ex/compile_fx.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/npugraph_ex/compile_fx.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/debug_save.md
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npugraph_ex/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npugraph_ex/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npugraph_ex/inference/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npugraph_ex/inference/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npugraph_ex/scope/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npugraph_ex/scope/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/dynamo/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/torch_compile_api/torch_compile_api.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/dynamo/test_npugraph_ex.py
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/api_list.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/api/api_list.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/quick_start.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/quick_start.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_dynamo.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/setup.py
  role: implementation
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# npugraph_ex.compile_fx：AOT 后 FX 编译与功能缺口

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。本卡选取来源支持的 A2/A3 推理范围，其他产品和特殊参数另行核对。

## 接口

`torch.npu.npugraph_ex.compile_fx(gm,example_inputs=None,options=None)` 接收 AOT 后的 GraphModule，返回可直接调用的已编译 FX 图对象。gm.graph 是目标 FX 图；它不是任意 nn.Module 的等价 torch.compile 替换。

## 直接集成的限制

发布文档明确：通过此接口构造自定义后端时，不支持图编译 Debug 保存、多流表达、限核，以及 input_inplace_pass。不能把通过 backend="npugraph_ex" 可用的选项矩阵全部套到 compile_fx。

示例用 aot_module_simplified 的 fw_compiler 接入；options 的 clone_input=False 仍有旧输入存储覆写与别名边界。自定义编译器获得可执行返回值，不代表已保留所有原地更新和缓存生命周期。

- [图池、拷贝与别名](../../guides/optimization/torchair/npugraph_ex_memory_pool_and_clone.md)
- [图变换与融合控制](../../guides/optimization/torchair/torchair_fx_pass_and_fusion_controls.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 固定主线的差异

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的文档更新了两项能力边界：通过 compile_fx 自定义后端可使用图编译 Debug 保存，但不产生 AOT 前的 dynamo_out_graph.txt；input_inplace_pass 需配合 `aot_module_simplified(keep_inference_input_mutations=True)` 保留推理输入变更。多流表达和限核仍列为不支持。上述是该固定主线的契约，不能反向改写发布子模块的限制。

分布式 Debug 还需在脚本开头 import npugraph_ex，确保目录创建正确。是否保留输入原地语义应通过别名和多次执行验证，不能只看编译接口成功返回。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/api/npugraph_ex/compile_fx.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/npugraph_ex/compile_fx.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/dfx/debug_save.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）


## torch.npu.npugraph_ex命名空间的真实代理层

npugraph_ex 的 api_list 页把 `compile_fx`、`register_replacement`、`inference.cache_compile/readable_cache`、`scope.limit_core_num/deterministic`（deterministic 行仅主线有，与发布页集一致）列在 torch.npu.npugraph_ex 命名空间下；该命名空间不是独立包本身，而是 torch_npu 仓的代理层：`torch_npu/npu/__init__.py` 的模块级 `__getattr__` 首次访问时 `importlib.import_module("torch_npu.npu.npugraph_ex")`（主线 202–211），代理包的函数体再转发进真正的独立包 `npugraph_ex`。compile_fx 代理两版行为分家：主线（15–17）原样转发 `npugraph_ex.compile_fx(gm, example_inputs, options)`，options 由独立包 compile_fx 内部经 `compiler_config._process_kwargs_options` 白名单消化（npu_fx_compiler.py 803）；发布（15–23）则自建 CompilerConfig、置 mode="npugraph_ex"、经 `npugraphex_config._process_kwargs_options` 走 OPTIONS_TO_CONFIG_MAP 平铺→嵌套翻译层，再 `npugraph_ex.get_compiler(compiler_config)` 直接取编译器调用，绕过独立包 compile_fx——同一 options 在两版落到的配置面不同，未知项两版各按自己层抛 ValueError。inference.cache_compile 代理同构分家（主线 inference/__init__.py 10 走 compiler_config、发布走 npugraphex_config），readable_cache 两版都只原样转发。

scope 代理在两固定 torch_npu 源内静态不可解析：`torch_npu/npu/npugraph_ex/scope/__init__.py` 的 limit_core_num/deterministic（主线 1–13，发布 1–7 仅 limit_core_num）在函数体内 `from torch_npu.dynamo.npugraph_ex import scope`，而 `torch_npu/dynamo/npugraph_ex` 模块文件在两固定 torch_npu 提交中均不存在（git ls-tree 核对），仓内也无任何代码把该路径注册进 sys.modules；独立包侧 `_scope.py` 40 行注释承认「source can be loaded as different Python function objects through torch_npu.dynamo.npugraph_ex and npugraph_ex」。因此按两固定源组合，文档承诺的 `torch.npu.npugraph_ex.scope.*` 入口没有可解析的导入路径，限核/确定性的真实实现在独立包 `npugraph_ex.scope`（见[限核与静态编译门控](../../guides/optimization/torchair/npugraph_ex_core_limit_stream_targets_and_static_kernel_gate.md)）；已安装产品若从其他源码态提供 torch_npu/dynamo/npugraph_ex 属固定源外，本卡保持未决不虚报。

## quick_start表1的mode行与options行

quick_start 表1把 torch.compile 的 options 行写成 npugraph_ex 功能配置入口、把 mode 行标为「昇腾NPU暂不支持」。options 消费端在固定源内闭合：backend="npugraph_ex" 经 torch_npu 注册入口 `_exec`（dynamo/__init__.py 主线 192–197、发布 152–156）自建 CompilerConfig 并把 `**kwargs` 原样传给 `npugraph_ex.get_npu_backend(...)` 返回的 `_npu_backend`，后者以 `_process_kwargs_options(compiler_config, kwargs)` 消化 options 键（hasattr 白名单，未知项 ValueError，compiler_config.py 183–210）；torch_npu 自带测试以 `torch.compile(..., backend="npugraph_ex", options={"clone_input": False})` 走通该链（test_npugraph_ex.py 30，两版同）。`_exec` 写入的 `config.mode="npugraph_ex"` 是 CompilerConfig 的内部枚举（OptionValue 候选仅 "npugraph_ex" 一项，compiler_config.py 主线 60/发布 24），不等于 torch.compile 的 mode 形参。mode 行的最终判定不在固定源内：两 torch_npu 提交与独立包均无消费 torch.compile mode 形参的代码，mode→后端的派发在 pytorch 主仓（不在本仓固定源），无法静态证实或证伪「暂不支持」；torch_npu 主线内部文档 `torch_compile_api.md` 对另一条 inductor 入口列出 mode 支持 None/"reduce-overhead"，与 npugraph_ex 入口无关。该行维持文档承诺、配对未决。

## 补充来源

- [固定实现 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npugraph_ex/__init__.py)（implementation）：1–34 全文。
- [固定实现 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npugraph_ex/__init__.py)（implementation）：1–44 全文。
- [固定实现 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npugraph_ex/inference/__init__.py)（implementation）：1–17 全文。
- [固定实现 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npugraph_ex/inference/__init__.py)（implementation）：1–17 全文。
- [固定实现 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npugraph_ex/scope/__init__.py)（implementation）：1–13 全文。
- [固定实现 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npugraph_ex/scope/__init__.py)（implementation）：1–7 全文。
- [固定实现 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）：202–211（模块级 __getattr__ 惰性物化命名空间）。
- [固定实现 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/__init__.py)（implementation）：13、192–200、245–262、_LazyNpuGraphEx 142–172。
- [固定实现 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/dynamo/__init__.py)（implementation）：17、106–132（_LazyNpuGraphEx 与 from . import npugraph_ex 回退）、152–161。
- [固定实现 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py)（implementation）：695–715（代理仅在 npugraph_ex 未入 sys.modules 时安装）。
- [固定约束 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/torch_compile_api/torch_compile_api.md)（constraint）：1–60 全文（主线独有文件；发布无此目录）。
- [固定约束 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/dynamo/test_npugraph_ex.py)（constraint）：21–33。
- [固定约束 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/api_list.md)（constraint）：1–24 全文。
- [固定约束 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/api/api_list.md)（constraint）：1–23 全文（缺 deterministic 行）。
- [固定约束 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/quick_start.md)（constraint）：表1 49–67（mode 行 57、options 行 59）。
- [固定约束 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/quick_start.md)（constraint）：表1 49–67。
- [固定实现 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：803、923–980（_npu_backend/get_npu_backend；kwargs→options 消化在 958）。
- [固定实现 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/configs/compiler_config.py)（implementation）：60、183–210。

## mode行跨pin静态收口与dynamo.npugraph_ex六pin清点

torch_npu 两固定提交为 mode 行判定补上仓内消费者证据：固定源内唯一消费 torch.compile mode 形参的代码是 inductor 入口的包装器——两 pin 都替换 `torch._TorchCompileInductorWrapper`（主线 `torch_npu/utils/_dynamo.py` 134–151、192–243，`new_init(self, mode, options, dynamic, name=None)`、`new_apply_options`、`new_call`；发布 159–198，`new_init(self, mode, options, dynamic)` 少 name 形参）。该包装器由上游 torch.compile 只在 inductor 后端路线创建；主线 `torch_compile_api.md` 对该入口声明 mode 现支持 None 与 "reduce-overhead"。TorchAir 侧两后端链路固定源内零命中 mode 形参消费者：GE `_npu_backend`（python/torchair/npu_fx_compiler.py 995）与独立包 `_npu_backend`（npugraph_ex/npugraph_ex/npu_fx_compiler.py 923）收到的 mode 只属于 TorchAir CompilerConfig 内部枚举，与 torch.compile(mode=...) 不同名同物。若上游把 mode 翻译成 options 并按 options 同路转发——options 转发已被 torch_npu 自带测试钉死（test_npugraph_ex.py 30：`torch.compile(backend="npugraph_ex", options={"clone_input": False})` 走通 `_exec → _npu_backend → _process_kwargs_options`）——独立包两版都会抛 ValueError，但机制不同：主线版字面键 mode 能通过 hasattr 校验（mode 是 CompilerConfig 合法属性，compiler_config.py 60 定义、183–210 为 hasattr 消化入口），拒绝来自赋值时的 OptionValue 枚举校验——mode 候选仅 "npugraph_ex" 一项，非该值抛 ValueError，不是键白名单拒绝；发布版则由键白名单直接拒绝（npugraphex_config.py 91 OPTIONS_TO_CONFIG_MAP/ALLOWED_OPTIONS 无 mode 项）。即 npugraph_ex 入口对 mode 的固定源内行为边界是拒绝未知项而非静默生效；mode 派生的其他白名单外键才由各自键集/属性集校验抛 ValueError。mode→options 翻译表与自定义后端的实际转发仍在上游 torch/__init__.py（六 pin 外），维持未决。据此 mode 行的语义收口为：TorchAir 两后端无 mode 消费者、固定源内 mode 只在 inductor 包装器路径被消费，与 quick_start 表1「昇腾NPU暂不支持」承诺一致；上一节“无法静态证实或证伪”的上游部分不再与该仓内证据混写。

`torch_npu.dynamo.npugraph_ex` 完成六 pin 负向清点：两 torch_npu pin 的 `torch_npu/dynamo/` 目录树仅含 `__init__.py`、`trace_rule.py` 与主线独有 `_deterministic_guard.py`，无 npugraph_ex 子包；torchair 两 pin 的独立包 `npugraph_ex/setup.py` 以 `find_packages()` 只安装顶层 `npugraph_ex` 包，不向 torch_npu 命名空间提供 dynamo.npugraph_ex；op-plugin 两 pin（d84e9b1d/dedc3167）对 `torch_npu.dynamo.npugraph_ex`（含 dynamo/npugraph_ex 路径形态）全树零命中；树内另有泛 npugraph 字样（发布 pin 的 SaveNpugraphTensorKernelNpuOpApi.cpp 与 test_save_npugraph_tensor.py、`NPUGraphsUtils.h` 头文件引用、`backend="npugraph_ex"` 的文档示例等），均不构成该路径的提供或命中。scope 代理函数体内 `from torch_npu.dynamo.npugraph_ex import scope`（torch_npu/npu/npugraph_ex/scope/__init__.py 两 pin）在六固定源组合内无解析目标、仓内无 sys.modules 注册；已安装产品 wheel 是否从其他源码态提供该路径属安装产物核对，固定源外。相比上一节“两 torch_npu 提交不存在”，本清点把负向证据扩到六 pin 全集，并以独立包安装面钉死 torchair 两 pin 不提供该路径；未决范围不扩大也不缩小。

## 补充来源

- [固定实现 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py)（implementation）：134–151、192–243 定向（_TorchCompileInductorWrapper 的 new_apply_options/new_init/new_call 替换与安装点）。
- [固定实现 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_dynamo.py)（implementation）：159–198 定向（同包装器的 __init__(mode, options, dynamic)/__call__ 替换）。
- [固定实现 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/dynamo/__init__.py)（implementation）：202–241 定向（_register_npu_backend 的 EntryPoint 让位逻辑与 _register_backends 对 "npu"/"npugraph_ex" 两名字的注册）。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/setup.py)（implementation）：1–13 全文（name='npugraph_ex'、find_packages() 顶层安装）。

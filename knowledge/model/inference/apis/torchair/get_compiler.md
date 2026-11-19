---
type: API
title: get_compiler：自定义后端中的 GE 编译器
description: 说明 NpuFxCompiler 与 torch.compile backend 的层次差别，保留 AOT 集成前提。
tags:
- task.lookup
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/get_compiler.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/get_compiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# get_compiler：自定义后端中的 GE 编译器

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。发布部分选取 A2/A3；主线 A2/A3 与950的限定范围见下节，不回推发布版。

## 接口

`torchair.get_compiler(compiler_config: CompilerConfig=None)` 返回 NpuFxCompiler；省略配置时使用框架生成的配置。

它供自定义 backend 集成，不把返回值当成 get_npu_backend 的同义入口。来源示例在 backend(gm,example_inputs) 内获取 compiler，再交给 aot_module_simplified(...,fw_compiler=compiler)。因此需要按实际版本核对 AOT 层的输入/返回协议，不能跳过 AOT 处理而把任意普通 Python 模型直接交给低层编译器。

## 检查

观察 AOT 后 FX 图、编译配置与可执行返回对象；确认自定义前/后处理保持输出结构和 mutation。示例的 forward 编译入口不构成训练反向支持或所有调试能力继承的证明。

- [完整 GE 后端入口](get_npu_backend.md)
- [捕获后端的低层接口](npugraph_ex_compile_fx.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线对应入口与延迟编译

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节对应文档已与发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 逐页对照；主线总览声明A2/A3与950PR/950DT，未在这些接口页另列产品排除。950仅属于主线证据，不回推发布配套，也不证明两仓主线组合已兼容。

主线get_compiler仍返回可调用的_NpuFxCompiler，传None时创建CompilerConfig；对象保存传入配置，实际接收(gm:FX GraphModule,example_inputs)后才走图转换/编译，不是调用getter即已得到模型可执行产物。示例把它传给aot_module_simplified的fw_compiler；不能直接把任意nn.Module当作gm，或把仅取得compiler对象计为编译命中/加速。

应保留实际使用的配置和AOT前后图、输入规格及运行返回对象。主线仍主要面向推理，该示例没有反向编译器或训练支持证明。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/get_compiler.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/get_compiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）

---
type: API
title: readable_cache：读取 GE 与捕获后端的编译缓存
description: 说明 compiled_module 解析、打印和文件输出，不将可读缓存当作运行兼容或性能证明。
tags:
- task.lookup
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/inference/readable_cache.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/api/inference/readable_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/inference/readable_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/inference/readable_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npugraph_ex/inference/__init__.py
  role: implementation
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# readable_cache：读取 GE 与捕获后端的编译缓存

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。发布部分选取A2/A3；主线A2/A3与950的限定范围见后文，不回推发布版。

## 接口与输出

GE 为 torchair.inference.readable_cache(cache_bin,print_output=True,file=None)，捕获后端为 torch.npu.npugraph_ex.inference.readable_cache，参数契约相同。cache_bin 指向 cache_compile 生成的 compiled_module 文件。

返回解析内容的 String；print_output 默认 True 打印，file 默认 None 不另外生成可读文件。file 可指定 py/txt 等输出路径，相对路径以调用脚本工作目录解析，检查输入存在和相应读写权限。

## 解读边界

此入口供检查已有缓存，不负责生成匹配当前环境的新缓存或验证反序列化执行兼容。读到相同图文本不能证明源码、参数、软件版本及底层编译产物都相同；仍按 cache_compile 的环境边界检查。不要用生成的可读文件覆盖原始二进制缓存。

- [GE 缓存前提](ge_cache_compile.md)
- [npugraph_ex 缓存前提](npugraph_ex_cache_compile.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线返回文本与可读文件不同

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节文档/实现已核对，主线总览覆盖A2/A3与950PR/950DT；发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的A2/A3条件仍独立保留，不回推发布版950或两仓主线配套。

主线两份readable_cache接口页的参数、返回与发布页一致，但这里实现细节只来自TorchAir的GE缓存解析器。主线PyTorch的torch_npu.npu.npugraph_ex.inference.readable_cache是转发给独立npugraph_ex包；未展开该外部包实现，不能把GE解析器行为视为该包内部格式与检查完全相同的证明。

TorchAir主线先检查输入存在及非软链接，加载CompiledModel；file=None仅返回文本并按print_output选择是否打印。返回String包含缓存meta、FX签名和caller frame的可读指令，而写入file的内容为这些信息的注释加compiled_fx.py_code，不能要求两者逐字相同。file设置时以w写出，创建所需父目录，并设为0o600；这是可读副本，不应与compiled_module同路径。检查可读输出仍不等于执行兼容性或实际缓存命中验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/inference/readable_cache.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/api/inference/readable_cache.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/inference/readable_cache.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/inference/readable_cache.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npugraph_ex/inference/__init__.py)（implementation）

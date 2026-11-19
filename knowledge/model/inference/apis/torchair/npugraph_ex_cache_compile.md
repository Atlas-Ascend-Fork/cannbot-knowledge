---
type: API
title: npugraph_ex cache_compile：options、动态 trace 与缓存契约
description: 独立说明 torch.npu.npugraph_ex.inference.cache_compile，避免混用 GE config/ge_cache
  和以跳 Guards 放宽实际输入。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/inference/cache_compile.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/compile_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/api/inference/cache_compile.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/advanced/compile_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npugraph_ex/inference/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npugraph_ex/inference/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/inference/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/inference/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/inference/_cache_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/inference/_cache_compiler.py
  role: implementation
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# npugraph_ex 编译缓存接口

## 入口

```python
torch.npu.npugraph_ex.inference.cache_compile(
    func, *, dynamic=True, cache_dir=None,
    global_rank=None, tp_rank=None, pp_rank=None, **kwargs)
```

返回 Callable；`options` 通过 kwargs 传入，按该后端的选项配置。此接口没有 GE 的 config、backend、ge_cache 参数合同；不能用 GE 缓存选项代替它的配置。

## 有效范围

持久缓存主要减少 Dynamo 编译成本。来源要求缓存与计算图一一对应，脚本一致，不能在需要重编译时继续复用。加载会跳过 Guards；动态 trace 不是任意动态控制流、地址和状态变化都安全的证明。含 RNG 算子不受支持，跨 CANN 版本缓存无兼容保证。

默认根目录为 `.torchair_cache`，多卡还涉及 world size 和 global rank。调用者提供的目录需有读写权限。func 必须是 Module 实例对象的方法，未被其他装饰器修饰，而且必须支持完整图（full graph）。对会产生多次 trace 的场景分别封装符合这些条件的方法；普通函数或已装饰的方法不满足此入口的使用前提。

## 验证与回退

覆盖真实 batch、序列长度、KV 状态和分支；核对缓存命中、输出与第一次执行开销。变更代码、输入契约或软件配置后，为对应组合重建缓存；取消持久缓存与切换 Eager 是两个动作。本文对应固定主线，未执行捕获或缓存实验。

## 版本入口

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## 发布文档对应关系与分解样例缺口

发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的API和特性页已完整对照：保留dynamic默认True、rank身份、RNG禁用、整图且未装饰的Module绑定方法条件。主线特性页额外明确缓存标识不是源码完整hash；旧页缺少这句不能当作它自动发现源码变化的证明。默认目录和aclgraphcache关键词只是文档路径说明，应核对实际软件入口及生成路径。

npugraph_ex持久缓存省去Dynamo/JIT与Guards，仍需Capture、输入处理和Replay；私有格式输入的信息保留，不从“缓存命中”推导捕获实例已跨进程持久化或首次调用零开销。多卡路径还含world_size/global_rank，TP/PP rank为各自域内编号。

两版API的custom_decompositions示例把add改成 `t1 * 3`，忽略t2，不能作为保持加法语义的分解；其forward只向cached传一个tensor，而inner_forward要求t1、t2，参数数量也不闭合。这里是静态样例审阅，未执行；实际规则需保持数值、参数、输出结构和mutation，不照抄该演示作正确性基线。

## Evidence

- [docs/zh/npugraph_ex/api/inference/cache_compile.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/inference/cache_compile.md)（primary）
- [docs/zh/npugraph_ex/advanced/compile_cache.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/advanced/compile_cache.md)（constraint）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/api/inference/cache_compile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/advanced/compile_cache.md)（constraint）

## 独立 EX 实现的入口与缓存身份

固定 PyTorch 主线/发布快照的公共 shim 都先创建 `npugraph_ex.CompilerConfig()`、设 `mode="npugraph_ex"`、处理 kwargs 选项，再向独立包转发 config 和各 rank；主线通过 `compiler_config`、发布通过 `npugraphex_config` 处理选项。独立包再转发到私有 `_cache_compiler.cache_compile`。因此私有函数存在 config/backend 参数，不会自动扩展上文公共接口的 GE 参数合同。私有入口检查 `MethodType` 和绑定对象为 `torch.nn.Module` 后返回 `LazyCompiledModel`，并非调用 cache_compile 就已完成编译。

两版 `get_cache_bin` 对绑定方法拼接 `str(func.__self__)` 和配置字符串作 MD5；目录还含类名、dynamic/static、`aclgraphcache`、方法名和 `CompiledModel.FILE`。根目录按显式 cache_dir、`TORCHAIR_CACHE_HOME`、当前目录 `.torchair_cache` 取值，再 realpath。分布式已初始化且 world size 大于 1 时才追加 world/global rank，显式 TP/PP rank 独立追加。这里不是模型完整源码、权重、分解表或输入 Tensor 内容的 hash；函数源码分支虽存在，公开的 Module 绑定方法路径不走该分支。

配置身份把 `as_dict()` 的局部选项更新到全局选项字典，再按 `.items()` 顺序拼接，未显式排序。pre/post custom pass 使用 `dis.dis` 输出的 MD5；反汇编遇到 `TypeError` 时改用固定字符串 `custom_pass` 的 MD5。这个退路可能让不同不可反汇编对象共用该项摘要，不能据此保证发现任何自定义 pass 变化。

主线独立 EX 还将有效 `npu_deterministic_level` 加入上述摘要：已加载 torch_npu 时调用 getter，未加载时取 0；其 CacheBackend 尝试安装 NPU 确定性 guard，仅在导入失败时告警跳过。发布快照对应的 key 和 backend 段没有这两项；这只说明固定局部实现差异，不代表发布完全没有其他确定性控制，也不证明任意跨版本缓存兼容。guard 的具体合同见[确定性等级 guard](../../guides/optimization/torch_npu/torch_npu_ascendc_dynamo_deterministic_level_guard.md)。

两版 backend 的前向代码生成返回非字符串时直接跳过持久保存；字符串路径先保存编译 FX，再编译返回 kernel。传入 AOT 的 backward compiler 明确抛出 `Backward cache compilation is not supported yet`。这些是静态源码路径，未执行导入、反汇编、编译或缓存加载。

## 缓存入口与身份的有界源码证据

- [固定实现 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npugraph_ex/inference/__init__.py)（implementation）：4–12；仅本段事实，不提升整文件或外部 helper 资格。
- [固定实现 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npugraph_ex/inference/__init__.py)（implementation）：4–12；仅本段事实，不提升整文件或外部 helper 资格。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/inference/__init__.py)（implementation）：10–30；仅本段事实，不提升整文件或外部 helper 资格。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/inference/__init__.py)（implementation）：10–15；仅本段事实，不提升整文件或外部 helper 资格。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/inference/_cache_compiler.py)（implementation）：183–221、339–355、363–369、372–440、644–685；仅本段事实，不提升整文件或外部 helper 资格。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/inference/_cache_compiler.py)（implementation）：182–209、323–339、347–352、368–404、581–605；仅本段事实，不提升整文件或外部 helper 资格。

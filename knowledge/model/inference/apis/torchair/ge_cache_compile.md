---
type: API
title: GE cache_compile：持久编译缓存与 Guards 失效边界
description: 说明 torchair.inference.cache_compile 的 config/backend、ge_cache、rank 命名空间及跨
  CANN 版本和模型变更时的复用约束。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/inference/cache_compile.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/compile_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/inference/cache_compile.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/compile_cache.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/inference/_cache_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/compiler_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/compiler_config.py
  role: implementation
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# GE 持久编译缓存

## 入口与参数

```python
torchair.inference.cache_compile(
    func, *, config=None, backend=None, dynamic=True, cache_dir=None,
    global_rank=None, tp_rank=None, pp_rank=None, ge_cache=False, **kwargs)
```

返回编译后的 Callable。config 与 backend 同时给出时，二者编译配置必须一致；只传 backend 时会取出其配置。ge_cache 默认关闭；开启后在缓存 Dynamo 环节之外保存 GE 编译结果，仅适用于 GE 路径，并可能增加通信域及显存开销。

## 缓存并非输入检查

缓存路径包含模型/函数、配置、动态模式及分布式 rank 等因素。固定来源明确说明它不等于模型源码的完整哈希；依赖模块或输入语义改变不一定自动失效。使用缓存跳过 JIT 和 Guards，生成与加载脚本、输入契约必须保持一致；同一 callable 需要重编译时不能继续承诺复用。

模型源码、结构、编译配置、确定性、控核、输入输出约束或 CANN 变更后，隔离并重建对应缓存。跨 CANN 版本不能保证缓存兼容，清理应限定于当前组合拥有的缓存。来源还禁止含 RNG 算子的缓存，并列出与 Dynamo 导图、RefData 功能的组合限制。

## 使用与验证

func 必须是 Module 实例对象的方法，未被其他装饰器修饰，并且必须支持完整图（full graph）。将只触发一次 Dynamo trace 的这类方法作为缓存单元；不同阶段或需要不同签名的调用分别封装。使用 cache_compile 后移除原先对应的 torch.compile 编译流程，避免继续叠加装饰或编译。

cache_dir 需可读写；多卡还须区分 world size、global rank 等路径。分别验证无缓存启动、命中启动和稳态输出，保留缓存命中证据。本文为固定主线契约，未做设备测试。

## 版本入口

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## 发布版对应接口与主线产物身份

固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的A2/A3接口页保留相同cache_compile参数、RNG限制、Guard跳过和CANN跨版本清理要求。主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的特性页另外明确匹配身份不是源码完整哈希；不能因旧发布页未写该说明便认定其缓存会自动检查所有代码变化。950范围仍来自主线总览，不回推发布组合。

主线实现先验证func是torch.nn.Module实例绑定方法；backend按get_npu_backend所产生对象的keywords读取compiler_config，不把Any类型理解为任意后端名字都可用。custom_decompositions是独立参数，用于合并模型的算子分解；**kwargs不是torch.compile任意选项的透传承诺。分解规则变化后也需重建对应缓存，不能只看函数名相同。

默认根目录实际先用显式cache_dir，其次TORCHAIR_CACHE_HOME，再用当前目录的.torchair_cache。分布式已初始化且world_size>1时才增加world/global_rank目录，另可追加tp_rank、pp_rank；全局rank是作业身份，TP/PP rank是相应域内身份，不能互相代替或把不同拓扑共用同一目录。

API页称model_info会含aclgraphcache，特性页写ge_cache；主线get_cache_bin实际在reduce-overhead/npugraph_ex模式加aclgraphcache，在max-autotune且ge_cache=True时加gecache。应以实际产物路径及日志核对，不能硬编码文档关键词查找缓存。该实现按绑定对象字符串、配置、确定性级别等算摘要，不足以证明模型源码或custom_decompositions字典内容已完整纳入身份。

## GE缓存文件与命中验收

ge_cache=False只表示不额外启用GE编译结果缓存，不应把它写成同时关闭Dynamo持久缓存。ge_cache=True时除compiled_module外，特性页列graph_key_timestamp.om、graph_key.idx，图有变量时另有rdcpkt变量格式描述。变量格式改变可能使旧产物不能恢复并重新编译；没有rdcpkt本身不表示失败，因为无变量图不需要它。

分别检查saved/loaded日志、当前模型/拓扑/配置、实际文件及首次调用延迟；只看到compiled_module不能证明GE OM已经生成或命中。路径不存在/加载恢复失败才走相应重新编译流程，不能依赖Guard主动发现业务语义改变。来源示例只展示prompt/decode封装和日志，不是本次性能测试。

## Evidence

- [docs/zh/ascend_ir/api/inference/cache_compile.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/inference/cache_compile.md)（primary）
- [docs/zh/ascend_ir/features/advanced/compile_cache.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/compile_cache.md)（constraint）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/inference/cache_compile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/compile_cache.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/__init__.py)（implementation）
## cache 编译入口的模式告警与 ge_cache 无效告警

本节把本卡 cache_compile 的配置检查承诺与两固定 pin 的 `_cache_compiler.py` 实现配对。`_check_config_support` 的名单内容、模式告警与 DeprecationWarning 语义已由[编译调优配对](../../guides/optimization/torchair/ge_compile_optimization_controls.md)按 get_npu_backend 入口配对，此处只补 cache 入口与 ge_cache 的实现锚点，不重述名单。

- `CacheBackend.__init__` 在构造时对传入 config 调 `_check_config_support`（主线 399–400/发布 374–375）。公开链路 cache_compile 返回 LazyCompiledModel（主线 715–717/发布 616–618），其 compile 先查缓存文件：命中即 load/recompile/rebase 并直接返回（主线 648–657/发布 578–590），不构造 ModelCacheSaver、也就不经过该检查；缓存未命中或损坏清除后才构造 ModelCacheSaver（主线 663–670/发布 592–593）→CacheBackend（主线 497/发布 447）。因此该检查只落在实际发生编译/重建的分支——缓存命中路径没有同类模式检查的证据（两 pin 静态读数，只说明该检查不在命中路径上，不宣称命中路径豁免一切检查）。`if config:` 门只对直接构造 CacheBackend(config=None) 留出跳过路径，不是公开 API 行为。
- 由此 cache_compile 与 torch.compile 共用同一模式告警契约：max-autotune 用 unsupport_geconfig_list（5 项 aclgraph debug 类），其余模式用 unsupport_aclgraphconfig_list；UserWarning 仅在 mode ∈ {max-autotune, reduce-overhead} 输出（once 过滤），npugraph_ex 模式检查仍执行但静默，reduce-overhead 另发 DeprecationWarning（compiler_config.py 主线 63–121/发布 63–115：max-autotune 的 unsupport_geconfig_list 两版同为 5 项；其余模式的 unsupport_aclgraphconfig_list 主线 20 项、发布 19 项——`ge_config.multistream_parallel_mode` 仅主线列入，名单内容存在版本差异而告警输出机制同构）。这些告警由 CacheBackend 的实际编译/重建分支执行；成功 cache hit 绕过的只是该显式 CacheBackend 构造/检查，不等于全部检查或下游保证——cache hit 须 load/rebase 成功：load 另有 owner/权限与 VERSION 校验（主线 170–188），compiled_fx 为 None 时 recompile 是 not-supported 占位 RuntimeError（主线 237–238），任一步失败即清除缓存并落回重建分支（主线 658–660/发布 587–589）。独立 npugraph_ex 包无该检查（负向 rg，见编译调优卡，不重述）。
- ge_cache 无效告警两版均有：config 非 None 且 ge_cache=True 且 mode ∈ {reduce-overhead, npugraph_ex} 时 warning_once「Ge_cache will not take effect when config.mode is set to ...」（主线 711–713/发布 624–626）。与本卡「ge_cache 仅适用于 GE 路径」配对：非 GE 模式开 ge_cache 有显式日志告警，但 get_cache_bin 仍照常给 reduce-overhead/npugraph_ex 加 aclgraphcache 后缀、max-autotune 且 ge_cache=True 才加 gecache（主线 228–232/发布 216–219）——告警不改变产物命名，也不能由「无告警」反推 ge_cache 生效。
- cache 场景的静态算子缓存联动：mode ∈ {reduce-overhead, npugraph_ex} 且 experimental_config.aclgraph._aclnn_static_shape_kernel 开启时，ModelCacheSaver 把 `_aclnn_static_shape_kernel.use_cache_compile="1"`、cann_version、compile_cache_dir、deterministic 写入 extend_config（主线 484–493/发布 439–447）；其消费端（use_cache_compile 严格等于字符串 "1" 才走模型 run 包恢复分支）已由[静态 Kernel 消费者](../../guides/optimization/torchair/torchair_integrated_and_standalone_static_kernel_consumers.md)配对，此处不重述。

### 配对差异归组

| 文档/本卡承诺 | 实际门槛与动作（静态读到） | 失败/版本边界 |
| --- | --- | --- |
| cache_compile 与 torch.compile 共用配置约束 | CacheBackend 构造即跑 _check_config_support；仅编译/重建分支构造 ModelCacheSaver/CacheBackend（两版同构），缓存命中路径直接返回 | npugraph_ex 静默；reduce-overhead 另发 DeprecationWarning（两版同构）；命中路径无该检查的运行证据 |
| 「ge_cache 仅适用于 GE 路径」 | 非 GE 模式开 ge_cache → warning_once（两版均有）；产物后缀仍按模式生成 | 告警不改变 aclgraphcache/gecache 命名；config=None 时无告警 |
| aclgraphcache/gecache 后缀判定 | get_cache_bin：reduce-overhead/npugraph_ex→aclgraphcache；max-autotune+ge_cache→gecache（两版同构） | 以实际产物路径与日志核对，不硬编码文档关键词 |

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/inference/_cache_compiler.py)（implementation）：窗口 192–240、370–380、430–450、555–610、602–634（CacheBackend 检查 374–375、ModelCacheSaver 联动 439–447、LazyCompiledModel 默认化 564 与 compile 命中早返回 578–586/失败清除 587–589/ModelCacheSaver 592–593、cache_compile 入口与 ge_cache 告警 624–626、get_cache_bin 后缀 216–219）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/compiler_config.py)（implementation）：窗口 63–125（unsupport 两名单 63–91、_check_config_support 94–121；本卡既有 npu_fx_compiler 入口配对见编译调优卡）。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/compiler_config.py)（implementation）：窗口 63–115（unsupport_geconfig_list 与主线同为 5 项；unsupport_aclgraphconfig_list 19 项、比主线少 `ge_config.multistream_parallel_mode` 一项；_check_config_support 输出条件与主线同构）。
- 本卡既有主线 `_cache_compiler.py` 来源补读窗口 195–245、399–402、460–500、618–675、679–717（get_cache_bin 后缀 228–232、CacheBackend 检查 399–400、ModelCacheSaver 联动 484–493、LazyCompiledModel 默认化 627 与 compile 命中早返回 637–668、cache_compile 入口与 ge_cache 告警 711–713）。复核补读主线 637–676 与发布 572–610（LazyCompiledModel.compile 的缓存命中早返回与 ModelCacheSaver 构造分支，两版同构）。再次补读主线 170–188 与 237–238（CompiledModel.load 的 owner/权限与 VERSION 校验、recompile not-supported 占位 RuntimeError，按 root 行 101 报告引用行段核对；发布对应函数未读）。负向扫描（rg 全 python，两 pin）：「Ge_cache will not take effect」主线/发布各恰 1 行（713/626）。全部为静态读取，未运行上游。

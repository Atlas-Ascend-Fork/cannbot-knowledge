---
type: Guide
title: cache_compile落盘资格、无梯度执行与重编译失效
description: 解释缓存miss后的完整图保存、no_grad和反向拒绝，定位重编译删除缓存、参数来源解析及两版异常处理差异。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/inference/_cache_compiler.py
  role: implementation
created_at: '2026-11-10T11:32:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# cache_compile落盘资格、无梯度执行与重编译失效

## 固定版本与范围

定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c及发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的CacheBackend、ModelCacheSaver和ModelCacheWatcher关键路径；分开记录参数来源解析的实质版本差异。这里只静态审阅保存控制流，没有调用torch.compile、运行模型、写读真实编译工件或做梯度/设备实验；产品矩阵未知，保持draft和空平台。

公共接口、目录身份和配套约束见[GE cache_compile](../../../apis/torchair/ge_cache_compile.md)，加载之后如何绑定参数见[缓存rebase](torchair_cache_rebase_parameter_binding.md)。本卡用于解释“当前模型能跑，但没有生成可复用缓存”及“改输入后缓存为何消失”。

## 缓存生成阶段是推理执行路径

ModelCacheSaver为缓存miss创建torch.compile(func,backend=cache_backend,fullgraph=True,dynamic=dynamic)。这个保存器实例的每次__call__都在ModelCacheWatcher和torch.no_grad上下文中执行compiled_func，并非只在首次trace关闭梯度；CacheBackend.bw_compiler直接抛RuntimeError，说明backward cache compilation尚不支持。

因此不能把这个推理缓存包装当作普通训练torch.compile的可替换入口，也不能用参数requires_grad=True推断会记录完整反向图。no_grad覆盖这个保存器的调用路径；缓存命中后的包装没有同一个ModelCacheSaver上下文，不能由这个局部差异推导命中后获得训练支持。训练性能和梯度正确性需要使用相应训练路径另证。

## 保存同时需要FX代码和调用者代码

fw_compiler取得可持久化Python字符串后才save_compiled_fx，再把字符串恢复为模块kernel。若codegen返回非字符串，记录Skip cache并返回该可调用对象；执行继续不表示缓存已落盘。

save_compiled_fx保存可读签名、py_code和input_parameters；调用者代码则由ModelCacheWatcher退出时查询torch._dynamo.utils.orig_code_map，按原func.__code__匹配后交给save_compiled_fn。找不到该私有工具时只记录Skip cache，不把这视作已经写成空缓存。

CompiledModel.save要求compiled_fn和compiled_fx都存在，否则直接返回。marshal首次序列化ValueError时尝试处理用户常量，再失败便Skip cache；只有走到工件写入完成才有saved日志。只看到目录、一次编译或模型输出，不足以证明两部分工件都已保存。

## 同一保存器发生重编译会删除缓存

save_compiled_fn首次接受code_id时保存它；以后相同code_id立即返回。若_code_id已有值又遇到不同code_id，发出recompiled警告、删除该缓存目录并返回，不覆盖成新签名工件。该分支没有把_code_id重置为None，因此不能假定这个包装之后会自动重新落盘。

输入域、Python分支或其他guard变化若使同一函数需要新的编译代码，可能触发这个资格限制。排查应启用来源提示的torch._logging.set_logs(recompiles=True)，定位具体重编译原因；对确实不同的阶段或签名单独封装、隔离缓存并重新验证，不能仅确认fullgraph=True便认为不会重编译。这里只核对失效机制，未复现任何模型的重编译。

## 参数来源解析需要按版本定位

保存器将gm参数/buffer与当前模型对象按is比较，找到时记录模型名称和Parameter身份；否则尝试gm._param_name_to_source。主线每次save_reserved_params先清空input_parameters与errors，且name既可为可调用对象也可为直接值，异常捕获为(AttributeError,KeyError,ValueError)。记录了errors时save_compiled_fn会Skip cache。

发布版没有上述两份列表的清空动作，且直接调用.name()；其异常写法为`except AttributeError or KeyError or ValueError as e`。按Python表达式语义，这里选择第一个为真的异常类，不能当成三种异常的元组捕获。由此静态推断，同一保存器多次进入参数收集时可能累积旧记录；KeyError/ValueError也不会获得主线相同的处理。这里没有运行异常实验，不把这种差异写成所有模型均发生的缓存故障。

## 异常退出与saved日志的证据边界

ModelCacheWatcher.__exit__不先检查exc_type，仍尝试找已生成代码并调用保存，然后返回False继续传播原异常。因此一次调用抛错，不足以断言没有产生缓存；反过来，saved日志也不独立证明该次完整模型调用和设备结果已经成功。保存阶段异常还应与后续[load/rebase自动清理](torchair_cache_rebase_parameter_binding.md)及实际kernel执行错误分开定位。

验收分别检查无缓存生成、生成资格日志、文件存在、独立进程命中和实际输出；覆盖业务输入域内会触发重编译的边界。性能比较分别记录生成成本、命中启动和稳态耗时，本卡未给出收益数值。

- [GE生成kernel的首次初始化](torchair_ge_cached_kernel_first_run_contract.md)
- [FX的AOT与缓存编译分支](torchair_fx_compiler_pipeline.md)

## Evidence

- [主线缓存保存链](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py)（primary）：145–167、438–462、466–609。
- [发布缓存保存链](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/inference/_cache_compiler.py)（implementation）：144–166、402–425、429–556；仅这些函数的定向差异核对，不表示源文件全文覆盖。

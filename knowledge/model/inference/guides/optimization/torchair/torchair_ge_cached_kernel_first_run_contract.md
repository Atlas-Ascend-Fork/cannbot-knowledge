---
type: Guide
title: GE缓存生成kernel的首次检查与失败重建
description: 区分普通GE执行器和持久化生成代码的初始化状态，说明一次性size/stride检查、配置回退及失败后重用边界。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py
  role: implementation
created_at: '2026-11-10T11:32:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE缓存生成kernel的首次检查与失败重建

## 版本和适用路径

定向核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的GeConcreteGraph.codegen及断言代码生成；所述首次初始化顺序在两版一致。主线另沿get_code和缓存fw_compiler确认回退路径。这里讨论保存并恢复的Python kernel，不把普通GeConcreteGraph.__call__的_is_compiled状态直接套入生成代码。

仅静态阅读代码生成文本与调用关系，没有compile/exec生成代码、加载缓存或调用NPU；完整平台和软件配套未知，保持draft与空平台。公开部署前提仍见[cache_compile接口](../../../apis/torchair/ge_cache_compile.md)。

## 配置可能使代码生成回退

GE codegen遇到enable_ref_data、export_mode或非None的aoe_mode就返回None。主线get_code把这个结果转换为原runner；CacheBackend.fw_compiler若拿到非字符串，也返回该对象，跳过save_compiled_fx。模型能够继续走可调用执行器，不表示已生成可持久化Python图代码或compiled_module。

成功生成时，global_compile_options来自归一化配置，local_compile_options先取配置再由extend_config逐项覆盖。设置ge.graph_compiler_cache_dir时还生成ge.graph_key和_update_ge_cache_dir；目录与key存在不是源码、参数或设备产物已经完整匹配的证明。

## 模块初始化与首次kernel调用分开

生成模块的顶层先initialize_graph_engine，并从serialized_graph建立GeGraph；每个恢复模块有自己的_is_first_run=True。kernel每次先执行输入处理代码，而图的格式/地址绑定、load和compile置于首次分支。

首次分支的实际顺序是：先把_is_first_run改False，再执行生成的assert_size_stride，随后更新ConstPlaceHolder和内部格式，最后load(local_compile_options,create_pg=False)并compile。带通信域的缓存另有顶层重建代码；create_pg=False不能单独解释成整个缓存加载过程从不创建通信域。

## size和stride只在首次分支检查

_codegen_assert_size_stride按_all_meta_tensor_input中每个Tensor的FX索引，生成assert_size_stride(args[idx],meta.shape,meta.stride())。它不是每次调用的完整Dynamo Guards：后续调用直接跳过这个分支，本地断言也没有自行覆盖全部dtype、设备、值依赖、业务分支或固定地址契约。

dynamic shape不会取消输入合同。生成代码使用输入处理阶段建立的符号表达式，不能因首次一个shape/stride检查通过，就保证全部后续输入组合可用。按实际缓存生成脚本和部署输入域验证计划形状；相关分档集合仍由[set_dim_gears](../../../apis/torchair/set_dim_gears.md)约束，不在这里自动padding或自动重编译。

## 初始化失败后不要假定同一kernel会重新初始化

_is_first_run在断言、运行期绑定、load和compile之前就已置False，本生成函数没有try/finally把它恢复。根据这条控制流推断，这些步骤中任一步抛错后，直接再次调用同一个已恢复kernel会跳过首次初始化分支；本卡没有运行复现，不能把这种重试当作可靠恢复方案。

这不同于普通执行器在graph.compile成功后才设置_is_compiled。遇到首次初始化失败时先定位原错误，重新建立匹配的恢复模块或编译包装，再验证首次与后续调用；不能只从“下一次没有编译日志”判断缓存已成功命中。缓存首次load/rebase的自动清理范围与kernel实际执行错误分开，见[加载与重绑定](torchair_cache_rebase_parameter_binding.md)。

- [普通GE首次调用时序](torchair_ge_runtime_binding_and_first_call.md)
- [固定权重地址绑定](torchair_ge_frozen_placeholder_runtime_binding.md)
- [缓存落盘资格与重编译](torchair_cache_save_and_recompile_contract.md)
- [通信图与进程组元数据](torchair_ge_collective_lowering.md)

## Evidence

- [主线GE代码生成](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（primary）：1348–1490、2106–2114；正常编译状态对照1333–1346。
- [发布GE代码生成](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：1104–1230、1706–1713；正常编译状态对照1089–1102。
- [主线get_code](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：623–634。
- [主线缓存fw_compiler](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_cache_compiler.py)（implementation）：438–458。

---
type: Guide
title: FXRT融合内核接入：Inductor注册、mutation与布局ABI
description: 区分通用Python调用、DVM和AutoFuse原生路线，核对写入参数、固定布局、工作区及捕获组合，避免把接入代码当完整运行保证。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/fx_wrapper.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/fx_simplify.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/compiled_kernel_hop.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/compiled_kernel_adapter.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/dvm_fx_wrapper.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/dvm_adapter.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/ascendc_fx_wrapper.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/autofuse_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_compiled_kernel_mutation.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_compiled_kernel_mutation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/aten/op_compiled_kernel_mutation.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/aten/op_compiled_kernel_mutation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/custom/op_compiled_kernel_mutation.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/custom/op_compiled_kernel_mutation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_python_call.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_python_call.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/dvm/op_dvm_call_v2.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/dvm/op_dvm_call_v2.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/dvm/op_dvm_call_v2_register.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/autofuse/op_autofuse_call.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/autofuse/op_autofuse_call.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/autofuse/op_autofuse_call_register.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/data_convert.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/data_convert.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/fxrt/test_fxrt_register_fx_wrapper.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_capture/utils/graph_capture_manager.cpp
  role: implementation
created_at: '2026-11-10T06:16:38Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FXRT融合内核接入：Inductor注册、mutation与布局ABI

## 固定来源与入口选择

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的26份Python/C++实现及注册测试全文，复用同SHA的完整捕获管理器。AutoFuse代码生成中的长模板另按AST静态展开104行审阅，未执行模板、编译shim、加载动态库或运行测试。没有本路线完整产品/配套矩阵，保持draft、空平台，不回推发布版。

直接torch.compile(fn, backend=fxrt.backend)与接管Inductor生成的host FX图是不同入口；Schema/前端映射见[前端降级](torch_npu_fxrt_frontend_lowering.md)，捕获与Storage生命周期见[运行时边界](torch_npu_fxrt_runtime.md)。本卡关注融合kernel保留、mutated buffer和ABI，不宣称底层融合算法、设备kernel或Autograd全部完成验证。

## 显式注册和全局配置

仅import torch_npu不加载FXRT；import torch_npu.fxrt/fxrt会建立同一模块树，但不自动接管device codegen。register_fx_wrapper只有安装成功才返回true并默认把torch._inductor.config.fx_wrapper设true、size_asserts/alignment_asserts设false；后两项原本会产生FX形式不能降级的裸assert行，关闭它们不代表shape/alignment已由其他机制完整验证。

patch_config=False只注册codegen，配置由调用方通过适用版本的config.patch等机制控制。安装失败返回false并保留这些开关；已经是FxrtFxWrapper的设备可重复注册。设备尚无codegen时才尝试导入torch_npu._inductor，已有AutoFuse等codegen时避免这次导入；目标后端注册顺序和GPU_TYPES等PyTorch私有全局状态必须按精确版本核对，FXRT没有自动消除所有后端冲突。

set_fx_wrapper_backend或fx_wrapper_backend上下文决定生成host图交给哪个(gm,example_inputs)后端，None使用FXRT；这是进程全局选择，不是线程局部配置。set_eager_debug必须在有关编译前设置，令host gm.forward作为对照，但融合HOP仍会调用已编译kernel，不能把此对照称为完全无融合的原始模型eager。已缓存编译物也不会因事后翻转开关自动改变。

FxrtFxWrapper拒绝有语义的裸源码字符串，只接受可表示的WrapperLine，注释/空白可忽略；FxConverter的2.9与2.10起参数布局通过检查签名适配，不据该分支泛化到所有PyTorch版本。FX_SYM_DEDUP默认开启，只有精确0关闭；仅在这个wrapper的compile_graph调用上游dedupe_symints，找不到私有模块时告警并跳过，不是直接backend的全局去重开关。

## 融合kernel与写入参数的识别

CompiledKernelFxConverter保留非Triton kernel为compiled_kernel_wrapper_mutation HOP，并把裸sympy/Sym*实参转成真实FX边，避免只嵌入名字而失去符号值生命周期。后端选择按注册顺序，注册器按类型去重，不是多个同类实例配置可以无条件叠加。

| 融合来源 | 识别与mutated参数来源 |
| --- | --- |
| CPU cpp_pybinding | 非gpu定义；类型字符串含*且不以const开头的参数判作写入，不是分析kernel实际写集。 |
| DVM | dvm_前缀或mlir/akg/import_fx编译标记；必须有arg_types，按同一非const指针规则提取写入位置，缺失时拒绝。 |
| AutoFuse AscendC | auto/unsupported_前缀或async_compile_ascendc标记；从调度器_kernel_cache的KernelArgs输出/原地buffer获取**定义处位置**，检查调用参数个数，不能用重用调用点的buffer名字匹配。 |

通用/DVM/AutoFuse的Future展开和launcher也不同；这些接口会依赖PyTorch/TorchNPU私有对象与编译缓存，本次只读源码，没有调用PyCodeCache或Future结果。

## mutation HOP与真实别名

mutation HOP的eager实现直接运行side-table中的kernel并返回None；functional变体按mutated_arg_indices对对应Tensor做clone_preserve_strides，返回index→clone，functionalize再替换并提交输入更新。Fake/Meta实现只生成元数据或clone，没有数值执行；mark_mutation_hidden_from_autograd不是已经提供NPU梯度公式的证明，也不保证多个mutated实参互相alias时仍保持所有别名。

通用adapter要求kernel_idx为整数、args为tuple、mutated索引合法且至少有一个FX Tensor输出buffer，缺example_value拒绝；C++还检查非负、重复索引和输出数。所有原实参（包括被写入者）都传入Op.compiled_kernel_mutation，每个输出ref到对应输入，并重绑后续env。因此部分写入应保留原buffer未改部分，图输入原地写可传回调用方；不能把普通重新分配输出的语义套到此路线。

side table是进程内全局callable索引，add有锁，reset会清索引；它不是可跨进程/重启持久化的kernel身份。复用或序列化host图时不能只保存一个整数并假定另一个进程有同一callable。

## 编译时固定布局的恢复

融合kernel的索引算术已按FX metadata中的stride/offset生成；FXRT的expand等可能产生dense Tensor，值域相同也不代表原stride0广播索引仍正确。restore_compiled_kernel_arg_layouts_在其他视图分解前，对非普通连续布局实参沿纯view白名单和相同Storage身份找根，再插显式torch.as_strided；size1维stride可忽略，但非零offset会触发检查。

遍历不会越过原地写，根Storage必须从offset0开始；非view直接产生的特殊布局、找不到对应FX节点的符号size/stride/offset会明确拒绝，而不是盲目contiguous。只读实参替换HOP对应槽，mutated实参还迁移其全部users以保留写后依赖，最后删除无用纯view并lint/recompile。这里恢复的是编译kernel期待的地址规则，不认证任意as_strided越界、重叠写或全部格式。

## 通用Python桥的执行时机和复制开销

OpCompiledKernelMutation继承PythonCall，但从side table解析callable，不按module/function名查找。实际kernel调用在CalcWorkspace持GIL内发生，NeedLaunch=false，防止在Torch下发队列任务里再嵌套提交真实kernel、被排到后续consumer之后；不能把“查询workspace”当成无副作用探针。它使用Torch认为的当前stream，不自动采用任意传给Launch的FXRT stream。

ref输出除stride/offset还同步StorageShape/Format。Python输入以非拥有from_blob包装现有内存并缓存ATen Tensor；UpdateAtenTensor只比较data_ptr与shape，二者不变时直接返回，改变时更新指针/size/stride，但没有完整刷新所有dtype/format/容量元数据。保持shape和地址并不证明任意stride/格式切换已适配。

普通PythonCall的Tensor输出则要求标准连续、offset0、NPU base format且shape匹配，然后安排D2D拷贝到IR输出；其“zero-copy attached”日志不等于无输出复制。输入桥与对外to_torch是不同函数：内部data_convert表另列QInt8/QUInt4x2，不应据此扩大包对外桥的dtype合同。

## DVM原生路线的额外合同

前端先识别DVM HOP，要求能取得装饰函数的kobj，并懒加载libops_ascend_dvm_v2.so；一旦识别后缺库/对象报错，不是自动保证回落通用Python路线。registry保存函数和kernel对象，C++通过固定版本pybind holder和私有成员取RawKernel/relocs/loads/stores；应视作同版本内部ABI，不能凭Python名称相同混装。

DVM adapter移除mutated槽位，把其他实参和handle交给native op，输出按kernel stores建立并重绑env；native没有通用mutation的输入输出ref配对。**不能将通用路线“保留原buffer/部分原地写”的合同直接套到DVM原生。** FXRT_KERNEL_LAUNCH_GROUP_NUM只要非空，native Init就明确拒绝，0字符串也不是兼容关闭方式。

动态kernel按输入tensor shape/stride及int/bool/symbol标量更新内部refs、Normalize并更新输出；标量float/double不在该动态输入类型表。输出dtype只映射BOOL、FP16、BF16、FP32、INT32、INT64，静态输出shape必须匹配，动态输出才按内核shape调整。输入/输出要求NPU和ND/NCHW dense format，输出还必须连续、offset0。

不能证明连续的输入可在实际Launch前用aclnnInplaceCopy复制到workspace中的连续ND临时Tensor；计划包含原kernel workspace、copy workspace与临时buffer并对齐，Launch检查总容量及copy workspace是否增长。零元素有单独处理，输入正offset的连续范围不等于输出也允许偏移。native调用可能增加复制和临时显存，应把动态stride/地址、split/non-split CodeGen及workspace一起验证，不能宣称原生路线全部零拷贝。

## AutoFuse原生路线与typed shim

只有FXRT_AUTOFUSE_NATIVE精确1且metadata backend为inductor_autofuse才尝试Op.autofuse_call；默认仍走通用compiled kernel路线。native要求adapter_path和kernel_path，按adapter目录找wrapper.so，并读取相邻inductor_wrapper.cpp或wrapper.cpp的函数声明。缺声明、无法解析的类型、编译器或ABI错误会报错，不会在这里自动回落。

typed shim支持限定的指针、整数、bool、float/double，返回int/int64_t；末两参必须是stream指针和kernel_key字符指针。运行时以uint64_t携带Tensor地址/整数/bool或double位模式，float按double解码后转换，不能直接用未经声明匹配的dlsym指针调用任意签名。Python验证允许void*位置为None，但C++EncodeArg没有None分支，故“参数验证通过”不能保证可传空可选指针；整数宽度/无符号范围也需按真实声明核对。

shim缓存键使用真实路径、mtime_ns、size、声明及codegen版本，并非对库/源码内容逐字节哈希；缓存位置由FXRT_AUTOFUSE_CODEGEN_CACHE或临时目录选择。生成需CXX或g++/c++、C++17共享编译，锁和临时文件替换只管理shim缓存，不量化、校准或验证融合模型。

C++检查fxrt_autofuse_abi_version==1、参数个数、必须符号、输出数和mutation索引。shim只加载/调用wrapper.so的init/wrapper（旧产物可按TASK_QUEUE_ENABLE选择task_queue入口），不直接调用kernel符号；以wrapper/kernel/key共享引用状态，生成代码另加RTLD_NODELETE保留wrapper文本及静态状态，finalize也不等于进程内一切动态库立即卸载。

native AutoFuse也在CalcWorkspace调用wrapper，FXRT workspaceSize设0，实际tiling/workspace归wrapper；NeedLaunch=false，但其Launch方法仍会调用wrapper供手动使用。复核的fullgraph普通捕获段却在CalcWorkspace后无条件调用Launch。**若native AutoFuse进入这一捕获段，静态路径存在重复调用wrapper的风险**，不能仅因原生接入和ACLGraph各自有代码就认定可安全组合；本次未做设备复现，也未更改上游。

## 已有测试和采用检查

test_fxrt_register_fx_wrapper只有6个注册/配置方法，含mock安装失败、patch_config行为和subprocess导入探针；缺FXRT包时跳过。它不执行融合kernel数值、dynamic layout、DVM/AutoFuse native或捕获组合。本次没有运行这些探针或上游测试。

实际采用须分别确认目标codegen和全局开关、mutation写集、partial-write/alias、符号边、dtype/stride/offset、真实stream及各路线workspace；再针对有效输入比较数值和显存/时延。编译成功、metadata匹配或知识库Lint通过均不增加verified，也不证明跨版本或任意平台可运行。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/__init__.py)（implementation）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/fx_wrapper.py)（primary）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/fx_simplify.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/compiled_kernel_hop.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/compiled_kernel_adapter.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/dvm_fx_wrapper.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/dvm_adapter.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/ascendc_fx_wrapper.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/autofuse_codegen.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_compiled_kernel_mutation.h)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_compiled_kernel_mutation.cpp)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/aten/op_compiled_kernel_mutation.h)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/cpu/aten/op_compiled_kernel_mutation.cpp)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/custom/op_compiled_kernel_mutation.h)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/custom/op_compiled_kernel_mutation.cpp)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_python_call.h)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/op_base/op_python_call.cpp)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/dvm/op_dvm_call_v2.h)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/dvm/op_dvm_call_v2.cpp)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/dvm/op_dvm_call_v2_register.cpp)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/autofuse/op_autofuse_call.h)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/autofuse/op_autofuse_call.cpp)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/ascend/autofuse/op_autofuse_call_register.cpp)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/data_convert.h)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/data_convert.cpp)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/fxrt/test_fxrt_register_fx_wrapper.py)（example）
- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_capture/utils/graph_capture_manager.cpp)（implementation）

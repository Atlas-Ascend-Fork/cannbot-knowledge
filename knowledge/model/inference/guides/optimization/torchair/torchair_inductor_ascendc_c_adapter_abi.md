---
type: Guide
title: Inductor AscendC独立C Adapter：参数映射、校验与加载寿命
description: 完整核对主线生成的C ABI Adapter、int64到uint32 Tiling门控、Scalar payload、名字别名及嵌入式二进制路径。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/_adapter_codegen.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/_asc_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/asc_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py
  role: implementation
created_at: '2026-11-11T05:37:17Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC独立C Adapter：参数映射、校验与加载寿命

完整读取主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的_adapter_codegen.py，包括生成C头与全部C++字符串。固定发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013没有这个具体路径；仅据此记录目录差异。draft/空平台，未生成、编译或加载Adapter；注释“stable C ABI”是本地作者目标，不能扩为跨所有版本的公开稳定承诺。

## 元数据与三套参数索引

生成头导出GetInfo、GetTilingArgMap、GetLaunchArgMap、Init/Finalize/Tiling/Launch。AutofuseValue为kind、dtype及uint64 payload，kind=0 Tensor地址、1标量值。Info固定abi_version=1、struct_size、flags、dyn_shape_num、launch_arg_num、tiling_data_size、workspace_num=1及kernel_build_id；flags位1/2/4分别表示动态Tiling、标量输入、名字别名。build_id仅取graph.name的SHA256前8字节little-endian，不是全部二进制/ABI/软件栈身份。

IR索引按Tensor/Scalar实参加非Profiler SizeArg排序，Adapter索引按图inputs_outer再outputs_outer，实际Launch索引再加前置block_dim/stream的2。TilingMap登记source dtype=9(int64)、kernel dtype=8(uint32)及三种索引；pk*只服务Profiler，排除出动态shape列表。GetMap的count可为nullptr，空表返回nullptr；Info和数组为静态只读描述。

alias_group只按同一个outer参数名字重复出现分组，不扫描真实指针重叠，也不在Launch要求组内payload相同。Tensor从payload转换地址；标量用memcpy解出Host carrier再static_cast到ASC值类型，编译期static_assert要求载体可平凡复制且≤8字节。允许载体集合见[标量图](torchair_inductor_ascendc_scalar_graph_and_ops.md)，不能把uint64 payload当通用任意数值编码或自动深拷贝Tensor。

## Tiling和Launch的真实检查

Tiling先检查shape个数、tiling_data/workspace_size/block_dim指针及非空shape指针，再要求每个int64 shape在0..uint32_max，随后锁mutex、检查g_tiling，转换成uint32调用；只在返回0时把local_tiling memcpy到用户缓冲。即使静态无shape也要求非空tiling_data。它传resource_limit=nullptr，没有普通Wrapper的ResLimit注入函数。

Launch检查参数个数、需要时args非空，再逐个检查kind和source dtype，之后锁mutex。没有逐Tensor shape/stride/storage容量、device、payload有效地址、workspace容量、stream非空或block_dim范围的独立校验；调用方仍须满足准确Kernel合同。自然对齐的KernelLaunchArgs保存小标量alignas(4)、uint64地址及workspace；仅动态shape时带按值Tiling。

rt分支动态shape要求tiling_data非空，静态可不传；AF分支不论静态动态都要求tiling_data并复制local_tiling再调用。两者直接返回底层状态，没有OpCommand入队、自动工作区分配、Profiler报告或设备完成同步。C++互斥只保护此Adapter对象的Host状态和调用，不认证跨流异步资源寿命或设备串行性。

## 加载与普通Wrapper的交付件区别

Init对空路径返回-1；锁内同路径已加载返回0、另一路径-2，dlopen失败-3，缺必需符号/二进制准备失败-4，catch(...)返回-5。取AutofuseTiling以及AutofuseLaunch；should_use_rt_launch允许的路线还尝试GetKernelBin，存在时把嵌入字节取出、检查非空，以lazy=0和magic选项BinaryLoadFromData，再找规范化Kernel入口。找函数失败时卸载该局部bin并关闭Host句柄；若无GetKernelBin但AutofuseLaunch存在则保留AF路线。

这与[常规rt Wrapper](torchair_inductor_ascendc_codegen_contract.md)的外置kernel.aicore_binary_elf_v1 + BinaryLoadFromFile不同，不能把交付件策略套给所有Adapter。当前prefer_rt_launch受非MM及CANN≥9.3门控；代码的magic另有MM/非MM条件选择，不据该条件表达式声称所有MM已经走此路线。rt调用同样写schemeMode=0、dynUBufSize=221184，未探测设备实际UB。

Finalize锁内清函数、按需BinaryUnLoad、dlclose并清路径，析构委托Finalize；Init/Finalize各有catch(...)，Tiling和Launch没有同样的统一异常捕获，不能概括成所有C入口绝不让C++异常越界。缓冲大小、真实动态库ABI、设备工作区和数值验收仍由调用者与外部实现核对，本文没有执行它们。

## 本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/_adapter_codegen.py)（primary）：1–569。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/__init__.py)（implementation）：15–23。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/_asc_codegen.py)（implementation）：21–142。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/asc_graph.py)（implementation）：17–63。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py)（implementation）：248–270。

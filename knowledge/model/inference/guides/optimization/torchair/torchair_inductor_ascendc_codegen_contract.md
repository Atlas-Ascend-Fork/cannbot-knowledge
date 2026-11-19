---
type: Guide
title: Inductor AscendC Codegen：图产物、双Launch与资源寿命
description: 保留Codegen设计，并完整对照两版生成实现的标量ABI、候选加载、队列工作区、资源限制和不同卸载合同。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/ascendc_codegen.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/ascendc_codegen_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/_asc_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/_asc_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py
  role: implementation
created_at: '2026-11-09T18:28:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC Codegen：IR、标量ABI、Wrapper与转置复用

## 固定设计与使用边界

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c双语设计，仅静态审阅。没有整套硬件矩阵，故draft/空platforms；内部函数、类名及ABI是此提交的解释线索，不是稳定应用API。这里摄取模型编译与调用边界，没有摄取设备Kernel、Host算子或Tiling生产工程。

## 分层与图身份

FX经AOT、Inductor Lowering和调度生成融合单元，再转换AscIR，生成asc_graph.py调用Autofuser.schedule/codegen，得到tiling_def、host_impl、device_impl及Wrapper，最终由output_code.py调用。AF负责实际调度/Tiling及设备代码；CPU stub仅用于框架调试，不是设备执行证据。

asc_ops映射表达算子，符号、size/stride/offset和hint描述轴关系。ASCGraph保留HintGraph层语义，FusedASCGraph以匿名buffer表达融合数据流；后者的匿名化可减少无关名称影响，不能因此省略别名、布局、标量和输出关系检查。惰性attrs存放追踪信息，不代表任意属性/算子均被后端支持。

## 标量与参数ABI

设计区分公共host标量载体和AFScalarData：前者FP16/BF16提升FP32、整数以I64传递，后者保留所需整数位宽。ctypes路径bool用uint8、float用c_float、int用c_int64，Tensor传地址并按生成ABI转换。输入dtype、host传参载体与设备计算dtype是不同层，不能据载体提升推定数值精度或任意类型支持。

SizeArg等动态符号参与运行参数；生成缓存hint时省略具体hint而实际执行保留hint。设计的文本hash基于asc_graph和cpp_wrapper代码，不将其称作所有环境/ABI/依赖的完整验证。编译、加载与首次真实运行的检查分别保留。

## 两类Wrapper与静态候选

设计写常规wrapper.so导出init/wrapper/release并维护候选注册表，空key与非空候选key分别处理，release保留胜出项并卸载其他候选；实际固定源码的两条Launch路线存在不同驻留/卸载合同，见下文完整实现补充。独立tiling_wrapper.so服务TopN，具有自身资源限制状态和get_topn/free_out等入口，不能把给其中一个库设值当两个库都已同步。

PythonWrapper在模块加载时编译，CppWrapper将调用烘焙进C++；两者共用算子Codegen但初始化、profiling状态来源和生命周期不同。autotune_topn>1的Cpp生成先以Python执行真实输入触发选优，再重新生成C++；未访问分支的首候选回退与缓存成本见[静态调优](torchair_inductor_ascendc_static_topn.md)，不能只计最终C++稳态成本。

设计中JIT的host/device对象与Wrapper可并发编译后链接；TopN存在host候选生成→静态设备编译的依赖。TORCH_COMPILE_DEBUG保留调试编译脚本；出现文件或缓存命中不代替实际init与数值检查。较新实现还存在按CANN与launch路线选择Kernel交付件名的分支，不把设计中kernel.so写死成所有路线统一交付名。

## 转置定义去重与调用消除

重复转置函数定义去重与运行时callsite CSE是两种优化。设计的callsite CSE仅在PythonWrapper适用，以stream、转置kernel、物理buffer和符号参数为键；不能据相同逻辑Tensor名字或shape就复用旧结果。

会变更的输入、捐赠/复用存储、主Kernel输出或缺少可判定元数据时禁用相关复用；PyTorch至少2.12时按流跟踪，不跨流机械消除。别名或上游写入改变结果后，旧转置输出不能仅因地址相同而继续复用。T5例子展示减少转置的来源案例，不是本地收益或任意网络的命中保证。

模型侧核对FX/融合前后IR、asc_graph、最终Wrapper和实际调用次数，再用同负载比较数值、内存及稳态；本文未生成、编译、动态加载或执行任何产物。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/ascendc_codegen.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/ascendc_codegen_en.md)（constraint）

## 完整生成实现与固定版本差异

本次补完整主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013的codegen/_asc_codegen.py及包入口；以下是实际生成文本合同，前文设计与其有差异时以这里的准确分支分别记录。没有执行本模块、exec、Autofuser或任何生成代码。

codegen_kernel_def拼AscIR导入、图定义和数学helper，再save_asserts写asc_graph.py，源码随后在load_autofuser上下文内exec(compile(...))；异常包装为带完整图代码的RuntimeError。主线另有schedule_codegen计时及ModularIndexing/Max/Min helper，发布只补Mod/PythonMod。返回dict从local_vars.get取name/tiling_def/host_impl/device_impl，本函数没有把get返回None统一改成完整交付件保证；调用者的后续检查另见[调度生成链](torchair_inductor_ascendc_schedule_codegen_wrapper.md)。

包入口延迟导入具体生成函数。两版都有Kernel和CppWrapper入口；主线另委托Adapter/Header及TilingWrapper。发布缺少这几个具体本地入口和_adapter_codegen.py路径，不代表发布其他目录或外部后端没有任何同类能力。

## 两层ScalarData ABI及Launch路线

TensorArg为void*，SizeArg为int64_t。主线把登记为scalar_inputs的TensorArg改成host_scalar_carrier_dtype载体；生成Launch局部参数再按asc_scalar_dtype或图内记录的dtype static_cast，因此公共host载体和AF值参数可以不同。完整允许集合、bool门控和图内ScalarData对齐见[标量图与操作映射](torchair_inductor_ascendc_scalar_graph_and_ops.md)。

SCALAR_C_TYPES仅有float32→float、int8/16/32/64、uint8及bool，其他直接NotImplementedError。KernelArg按指针末尾*拼签名；ScalarArg保source_c_type，StreamArg仍void*，SymArg/Int64Arg为int64_t，CharPtrArg为char*。这些本地载体不扩展为任意dtype可用。

codegen_cpp_wrapper仅在should_use_rt_launch(is_fused_mm)为真走rt路径：非MM且CANN版本helper判定≥9.3.0；CPU调试helper直接返回True并非真机支持证明。其余包括MM和较旧CANN的非MM走AutofuseLaunch，不能照内部“CV专用”docstring排除后一类。CPU调试强制AutofuseTilingData，其他按图是否含MM选CVAutofuseTilingData或AutofuseTilingData。

主线公共签名依次为Tensor/标量实参、Tiling符号、Profiler额外符号、stream、kernel_key；pk*仅供观测，不进入Tiling形参。输入顺序来自inputs_outer，输出来自outputs_outer，不能按匿名名任意交换。Tiling收符号、tiling_data*、uint64 workspace_size*、uint32 block_dim*及resource_limit；自动生成的Launch再接inputs/outputs/workspace/tiling。发布的workspace_size为uint32、无kernel_key与本地ScalarData/Profiler分类，不混用两版ABI。

rt路径按camel_to_snake(gen_valid_name(graph.name))找设备入口。KernelLaunchArgs以自然C++布局保存标量值、uint64地址和workspace地址；bool/int8/uint8/int16/uint16字段加alignas(4)，不使用packed。仅有Tiling符号时附带按值tiling_data；无符号静态Kernel不带该字段，pk*不使它变动态。配置固定schemeMode=0、dynUBufSize=221184，源码注释称后者暂定，不能当已探测设备UB或普适SIMT策略。

## 默认和候选的初始化、选择与错误状态

两条主线路线的init都锁mutex并在initialized时直接返回0。默认key为nullptr：Autofuse路线dlopen Host库并取AutofuseTiling/AutofuseLaunch；rt路线仍dlopen取Tiling，但从同目录kernel.aicore_binary_elf_v1加载设备二进制（输入路径无目录时用该basename），再找规范化入口。aclrtBinaryLoadFromFile的lazy选项为0。

候选key非空要求tiling_map已有该key；填充这张表的编译/选优消费者见[静态TopN](torchair_inductor_ascendc_static_topn.md)，本生成函数不单独构造全部候选数据。Autofuse候选dlopen并保存Launch函数，rt候选把kernel_file直接当bin路径加载；候选init不立即把initialized置真。map.emplace没有在这里实现同key重复加载的完整替换清理。

运行时先从默认函数/工作区/block_dim/tiling复制，候选函数表命中才替换函数，而tiling_map[key]使用下标访问；不能把任意坏key都说成在wrapper中显式拒绝。动态Tiling仍按符号实参重算，候选存在不等于任意动态shape可直接套旧Tiling。

资源setter在aiv/aic同时为0时清整份ResLimit，否则置valid_num=1并写aiv/aic/ub，resv[10]保持结构字段。普通和TopN Wrapper各有自己的实例；静态默认Tiling在init阶段计算，setter没有独立的“使已算静态Tiling失效并重算”分支，注入时机须随真实消费者核对。动态Tiling也收到该资源指针。Adapter另有不同合同，见[独立C ABI](torchair_inductor_ascendc_c_adapter_abi.md)。

缺符号、Tiling或加载失败返回-1并有部分关闭Host句柄的分支；rt LoadBinFromFile在GetFunction失败时没有就地BinaryUnLoad，父级错误分支也不能被笼统描述为全部资源已回滚。这里只描述本地实际检查与先后，不认证完整加载/失败重试协议。

## TaskQueue位置、工作区和真正的release差异

queue0/1先GetStream、选候选、动态Tiling及MallocWorkspace，再把按值捕获的Launch交RunOpApiV2；正常返回后才FreeWorkspace。queue2先在外层取流/静态数据，回调内恢复debug路径快照，再做动态Tiling、AllocateWorkspaceTensor及Launch。两路非零workspace都先检查≤int64最大值和地址非空，queue2使用局部Tensor保持该回调内对象；实际设备异步寿命继续由队列/分配器合同核对。

Launch状态检查发生在回调内，Profiler push/pop也在该作用域。外层返回0不单独证明设备执行完成；异常越过RunOpApiV2后的FreeWorkspace等路径时，本段没有通用RAII回滚保证。发布Wrapper则直接调用launch_fn，动态Tiling在GetStream前执行，FreeWorkspace发生在检查Launch返回值之前，没有主线queue01/2这一组本地生成函数。

**主线AutofuseLaunch的release只移除落选Launch函数映射，保留候选DSO及handle表驻留，最后置initialized。** 源码注释将其归因设备指令缓存及运行时退出阶段寿命风险，这是作者说明，本次未复现。析构只关闭默认handle。rtLaunch的release才对落选bin执行BinaryUnLoad并删bin/函数映射，胜出项保留；析构处理默认bin和Host库，不遍历候选表。两条release在initialized已经为真时都直接返回，不能把设计中的“卸载其余候选”当全部主线分支共同保证。

TopN tiling_wrapper拥有独立mutex、初始化标记、资源状态及GenerateTopnSolutions/GetTilingDataRepr指针。配置文本按|分字典、;分项、首个=分key/value，无转义；重复key由map后值覆盖，空字典丢弃。get_topn检查函数非空、返回码及三vector长度相等，再逐项strdup并memcpy工作区/blockdim到调用者数组；本函数没有另传数组容量或证明结果数≤调用者容量的本地检查。free_out只free字符串项，不释放外层指针数组；本模块没有该tiling_handle的析构段。具体调用方容量/资源安排继续按TopN消费者核对。

[Profiler实现](torchair_inductor_ascendc_profiler_metadata.md)、[实际Python加载对象](torchair_inductor_ascendc_wrapper_launch_abi.md)与[图IR](torchair_inductor_ascendc_scalar_graph_and_ops.md)分别接续元数据、加载和构图；完整生成文本覆盖不关闭外部AF、二进制入口、设备精度或性能。

## 本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/_asc_codegen.py)（implementation）：1–1623。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/_asc_codegen.py)（implementation）：1–242。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/__init__.py)（implementation）：1–28。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/experimental/_inductor_npu_ext/python/inductor_npu_ext/codegen/__init__.py)（implementation）：1–12。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py)（implementation）：248–270。

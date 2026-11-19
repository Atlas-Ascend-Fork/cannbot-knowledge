---
type: Guide
title: Inductor AscendC 静态TopN：候选、PGO子进程和缓存成本
description: 补齐静态TopN实际门槛、候选/交付件、缓存格式、Profiler子进程与失败状态，保留完整本地定义及外部运行边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/static_shape_autotune.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/static_shape_autotune_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_autotune.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_autotune_child.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_kernel.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py
  role: implementation
created_at: '2026-11-09T18:28:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---


# Inductor AscendC 静态TopN：候选、PGO子进程和缓存成本

## 固定身份与适用条件

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c静态TopN双语设计、手册及完整_autotune.py/_autotune_child.py静态阅读。实验功能无完整产品矩阵，故draft/空platforms；未启动子进程、读取payload、加载so或运行NPU。

逐融合Kernel判定：无SizeArg的静态shape、CANN至少9.1、AF host代码含GenerateTopnSolutions/GetTilingDataRepr、不是matmul template。全满足走TopN；autotune_topn只裁剪候选并决定是否实测，不决定是否静态化。动态图或同图中的动态Kernel仍走JIT运行时tiling，未进入融合图的aten fallback不在这条编译链。

AF固定最多请求10组tiling_repr/workspace/block_dim，再按用户配置裁剪；实际解可能少于请求。TORCHINDUCTOR_ASCENDC_AUTOTUNE_TOPN默认1，直接保存唯一候选而不做PGO；配置>1且真实候选>1才触发选优。正整数之外启动报错，超过10告警且最多10，不把“设3”当一定有3个不同候选。

## 编译、交付件和Wrapper

静态路径依赖tiling.so→tiling_wrapper.so→候选生成→注入tiling_map的wrapper→逐候选静态Kernel编译，整体在一个编译任务内按依赖推进；JIT则可分开提交Wrapper/host/device任务后链接。compile_threads=1为同步调试，不能将进程池并发数误称为每个候选都会并发编译。

kernel_key是tiling_repr|workspace|block_dim的MD5，optimize_tiling记录这三个字段；Wrapper按key找已固化信息，不再为该静态候选运行常规动态tiling。设计常以static_kernel/<key>/kernel.so说明，但当前_autotune.py按should_use_rt_launch(False)选择KERNEL_BIN_NAME或kernel.so，不能硬编码所有新CANN路线都叫kernel.so。

PythonWrapper首次实际调用load时选优；CppWrapper在代码生成期先以Python模式materialize real_inputs并运行整图，克隆将被mutate的输入，再重新生成C++。没有被这次真实执行覆盖的分支记录为unvisited TopN并回首候选，不能称所有分支都已实测选优。缓存虽可免PGO，重新生成CppWrapper仍可能执行这一次Python整图。

## 独立子进程与旧设计差异

旧静态设计写PGO不能嵌套外部采集、数据在./profile_result/<md5>。同提交较新手册和实际autotune入口已改为冷缓存一律独立子进程，包括外层profiler处于wait阶段；目的在于隔离父进程的ProfPathCreator和用户trace目录。缓存命中直接init/release胜出项，不启动采集子进程。不能继续把旧互斥条目作为当前实现的全部规则，也不据隔离目的承诺任意外部采集器和设备组合都已验证。

父进程持compile.lock，将Tensor按stride所需存储范围复制成CPU payload，保留shape/stride/device，连标量、候选和控核信息传给子进程；因此首调还有数据拷贝、序列化和新进程成本，不是只多几个kernel时长。不同Tensor的别名关系没有在该逐参数重建层完整建模，不把它当任意别名/原地模型的等价输入生成器。

子进程先设device再导入实际扩展，加载候选并注入控核；父进程只接受候选集中已知key、长度匹配且有限非负timings。进程非零退出、无结果、坏JSON/状态、未知key或计数/时间非法都报错，不静默把首候选当成功。超时30分钟会kill并收尾；这是源码策略，本次没有等待或触发该路径。

临时数据位于对应Kernel缓存下.autotune_*，TemporaryDirectory由父进程在子进程退出、失败或超时后清理。它清的是自有临时目录，不应照旧说明删除用户profile_result。保存的选优文本仍需格式检查及真实库init，文件存在本身不等于二进制/数值有效。

## 采集口径与缓存

子进程使用Level1/PipeUtilization、schedule wait0/warmup1/active1/repeat1/skip_first1，代码总共4轮；每轮先恢复私有输入buffer，再依次下发所有候选，轮末同步。**不是每个候选前都恢复一遍输入**，有原地写入或别名的Kernel需另外验证候选公平性和语义，不能据“真实输入”保证每个候选起始状态完全相同。

解析kernel_details.csv中Name以autofused开头的Duration(us)，条数必须等于候选数，再按索引对应候选并取最小。该解析假设真实采集顺序/命名与候选对应，不能用通用profiling CSV无条件替换。胜出项经父进程init/release后写optimize_tiling，后续用该key直接下发。

缓存位于原生Inductor缓存根下ascendc，原生FORCE_DISABLE_CACHES不独立清除此缓存；静态控核信息需进入hash，动态JIT复用库但重新tiling。首次候选编译、输入复制/子进程/PGO、Cpp预执行和稳态分别计费；Profiler记录的是候选设备时长，不代表全部模型端到端最优。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/static_shape_autotune.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/static_shape_autotune_en.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals_en.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_autotune.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_autotune_child.py)（implementation）

## 完整compiler包消费者补充

本次完整读取固定主线compiler五个Python模块，并对照固定发布目录的__init__/_compiler。发布目录没有_autotune.py、_autotune_child.py、_kernel.py这些具体路径；发布所读本地实现直接调用jit_compile。此为快照目录/定义差异，不推导发布包、其他分支或后端不存在任何调优能力。主线编译缓存与ABI的完整本地实现分别见[异步编译/PCH](torchair_inductor_ascendc_async_cache_and_pch.md)、[Wrapper加载](torchair_inductor_ascendc_wrapper_launch_abi.md)。

decide_use_topn_tiling先检查原生fx_wrapper，启用即False；之后才按传入is_static、CANN>=9.1和host文本双关键字判断，has_matmul_template字符串True排除。async及sync共用此函数。候选数量配置不改变这个门槛。TilingInfo/KernelInfo只是保存提供字段的本地对象，注解/构造没有完整范围验证。

compile_ascendc在compile.lock内构建可选adapter，再按门槛选择JIT或TopN。TopN先host tiling.so，再tiling_wrapper.so，get_topn要求wrapper路径存在，预载可能缺少的依赖后init_tiling；把父进程device_limit交给独立tiling库setter，再请求最多10组。返回n必须正，逐项UTF8解码tiling_repr并收集workspace/block_dim后才free_out；没有针对所有中间异常的finally释放，也未在Python再检查n<=已分配topn数组长度。

config字典列表按key=value、分号及竖线拼成get_topn参数，当前AUTOTUNE_CONFIGS为空。裁剪后把各候选MD5与TilingInfo注入cpp_wrapper的tiling_map声明，再逐候选构建static_kernel/<key>交付件。仅一候选时直接写optimize_tiling并返回普通NpuInductorKernel，多候选返回AutoTune子类，首次load才实测；此区别保留编译与首调成本。

save_optimize_file直接以w写tiling_repr/workspace/block_dim的竖线文本，没有这个函数内的临时替换事务。load先按整个原始文本MD5推导目录，再校验三段及两个整数可解析；没有验证workspace/block_dim为正。手工增加换行等文本变化即可能改变key，格式通过也不证明对应库存在、有效或数值正确。

AutoTune.load在选优前保存dl并注入控核、调试和Profiler状态，失败不在本地清空dl；run每次再刷新状态，并附带胜出key。autotune在同kernel锁中先检查缓存；缓存命中init及release均显式检查状态。冷缓存子进程返回后，父进程再次init/release胜出项并检查，再写选优文本，未以子进程成功替代父库可用性。

_tensor_storage_view按size/stride求覆盖跨度并从原storage_offset取一维view，零维/空轴情况按本地公式处理；payload保存CPU clone、原shape/stride/device，各Tensor独立复制没有重建跨参数别名。_restore_arg对scalar直接返回，对tensor转目标device并as_strided恢复。父进程以当前device、wrapper绝对路径、候选和显式控核组织payload；PYTHONPATH加入包父目录，stdin为DEVNULL，stdout/stderr归私有child.log，错误只附末8192字符。

child文件入口要求三个参数及非空package，先weights_only加载CPU payload、import torch_npu并set_device，之后才导入实际package.compiler._autotune。子进程主体可复用已读payload；异常捕获BaseException保存traceback，result.json先写.tmp再os.replace。父进程拥有临时目录并负责30分钟超时kill/wait及最终清理；这不是对任意外部payload、动态库或设备上下文的认证。

Profiler循环先init所有候选，建立私有flat-storage快照，每轮恢复一次输入再按序跑全部候选，总计4轮。该采集循环未单独检查每次wrapper返回码，子进程的release返回值也未在该函数检查；父进程timing结构校验和随后init/release检查不能替代每候选数值/状态验证。CSV仍只按autofused前缀与Duration列顺序配对，选择最小值；父进程拒绝bool timing、NaN/inf/负值、数量或key不匹配等结果。

这些补充完成本地序列化、缓存文本、子进程入口和控制流落点；完整设备Kernel、外部Profiler/AF及生成C++候选注册表仍需各自证据。本次未读取真实payload、加载库、起子进程或采集NPU。

## 编译实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_autotune.py)（implementation）：1–361。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_autotune_child.py)（implementation）：1–30。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_compiler.py)（implementation）：1–1230。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/__init__.py)（implementation）：1–718。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/compiler/_kernel.py)（implementation）：1–163。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py)（implementation）：248–270。

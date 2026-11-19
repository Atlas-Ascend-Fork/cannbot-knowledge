---
type: Guide
title: 实验Triton自动调优：计时口径、输入隔离与回退
description: 保存mspti与NPU event的真实单位、样本组织、输入克隆/重置范围及失败后回退，区分runnable与数值验收。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
created_at: '2026-11-11T08:05:18Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton自动调优：计时口径、输入隔离与回退

## 固定实现与选择链

针对TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf实验Triton后端的有界完整函数。审阅本地参数克隆、批量/单配置benchmark、mspti与NPU event路径；配置仅核所列初值与模块安装，不提升整个heuristics或config的资格。没有导入mspti、修改环境、装载库、分配Tensor或运行任何设备计时。

benchmark_all_configs委托批量NPU实现，DEBUG时打印排序结果。批量实现先取当前设备的raw stream，准备隔离输入并对每个候选做PreRun和synchronize；预运行异常把该launcher标记不可运行。非custom kernel只有n_spills不为None且大于spill_threshold（缺省16）时才被禁用；全部不可运行立即抛错。

后续优先尝试mspti，缺失、失败或计数不符返回None才用event；event路径每个候选异常写inf，外层批量异常再尝试单配置bench。最终每项结果交coordesc_tuner.cache_benchmark_result。这里不核对输出数值、NaN/Inf或梯度，也不在返回前统一拒绝全部耗时为inf；“runnable”只代表局部路径没有被禁用，不能代替数值正确性和调优结果验收。

## 克隆范围与每次重置

_clone_all_args_for_autotune分别遍历位置参数和kwargs的直接值，遇torch.Tensor调用clone_preserve_strides，其余原样保留。它不递归遍历list/dict等容器，也没有本地跨参数别名表，因此不能把docstring的“所有Tensor深拷贝”推广成任意嵌套对象与跨参数共享关系均被隔离。

批量路径先做上述一轮直接Tensor克隆，使候选针对bench_args运行；PreRun执行pre_hook、进一步clone_args、reset_to_zero_args再启动。event候选在计时前执行pre_hook和clone_args，之后重复使用该组副本；有reset_to_zero_arg_names才逐次重置相应参数。这里不是每次重置所有Tensor，也不是每次恢复全部初始内容。clone_args、保步幅clone及外部pre_hook实现仍各自独立。

mspti路径虽然注释声称逐候选及时释放避免同时持有多组副本，实际先为所有runnable launcher建立bound字典，保存各自cloned_args/kwargs，再打开统一监控会话，调用结束后才bound.clear()。因此这段实现不能作为“峰值只保留一组候选输入”的内存保证；此处是静态控制流结论，没有执行OOM复现。

单配置bench先套边界downcast包装，并在reset集合包含未标记mutated参数时再做直接Tensor隔离。它使用CPU副本/备份接口；有reset参数时把克隆与清零放在prepare、恢复放在cleanup，没有reset时在kernel_call的finally恢复。单配置的n_spills判断没有批量路径的None保护，缺元数据时不能假定与批量禁用行为完全相同。

## mspti监控的本地门槛与单位

本模块把mspti.KernelMonitor导入的任意Exception转为不可用；_mspti_autotune_enabled还要求实验config.autotune_mspti为真及LD_PRELOAD字符串含libmspti.so。这个字符串判断不是实际库驻留、回调工作或设备支持的验证。

enable_mspti_autotune是独立的尽力准备helper：受enable_mspti控制，字符串已含库名就返回；从ASCEND_HOME_PATH或ASCEND_TOOLKIT_HOME定位tools/mspti/lib64/libmspti.so，路径存在后用ctypes.CDLL(...,RTLD_GLOBAL)保留全局句柄，再追加LD_PRELOAD；OSError则返回。这里只说明helper被调用时的逻辑，不推定任何入口必然调用它，也没有在摄取中执行这些操作。其docstring所称PTA profiler回退，不应替代本次消费者实际选择event的证据。

_mspti_bench_calls先synchronize，启动一次monitor并按候选顺序运行warmup+active次，最后同步并在finally停止monitor。callback仅收name以triton开头的记录，用end-start构造duration；实际记录数必须等于候选数乘迭代数，否则返回None。匹配后按候选顺序切等长块、去warmup、取排序后的中位项，最后除1e6。代码返回的是毫秒，不能沿用docstring中的device-us字样再缩放一次。

这个分组依赖所假设的回调顺序与每次启动一条匹配记录；本地没有通过独立候选ID关联每条事件。前缀筛选可排除不同名称的清零kernel，但不等同于对任意多kernel、并发任务或外部回调都准确归因。默认初始值为mspti_warmup=5、mspti_active=20；调用时从config读取，运行态patch后的值另核。

## event分两种窗口

_do_bench_npu默认warmup=25、rep=100，先做一次未计时调用并同步，再分配int(256e6//4)个torch.int元素用于刷缓存。clone/setup与reset是否进入计时窗口取决于是否传prepare，不能只按“用event”认定同一计时口径。

| 路径 | 计时组织与返回值 |
| --- | --- |
| 有prepare | 为sample_limit=max(1,event_bench_max_samples)分配事件对并预初始化。每次先刷cache、prepare，再record/launch/record，cleanup在finally执行。用包含setup的墙钟样本估计额外warmup与采样预算；实际事件样本按切片取得，排序取中位项。 |
| 无prepare | 用一对event包住多次fn，除重复数摊销开销。先以10次估计耗时，再按event_bench_target_ms和max_inner计算组内次数；warmup若干组、测量若干组，最后取每组均值的中位项。 |

有prepare的warmup_count被夹在0..10，sample_count表达式虽至少3，真正执行仍受预分配event_pairs切片长度限制，不能保证配置上限为1时也得到3个独立样本。无prepare的测量组数至少3的表达式随后又受event_bench_max_groups上限限制，也不构成对任意用户配置的最少3组保证。

所列源码初始值：event_bench_max_inner=256、event_bench_max_groups=25、event_bench_max_samples=20、event_bench_target_ms=8.0，enable_mspti/autotune_mspti均为True；config最终交install_config_module，初值不等于所有运行会话的有效值。NPU event窗口仍可能包含主机enqueue间隙，分组只能减少部分事件开销，不能直接当成纯设备指令耗时。回退告警按进程guard尽力只报一次，未以本地锁证明并发时严格一次。

选择候选时应一起保留有效配置、runnable/inf结果、实际mspti或event路径、reset/克隆范围、event分组参数与独立数值校验。这里没有测量任何示例中的微秒数或提速倍数；普通/静态/fast启动器的选择另见[静态启动协议](torch_npu_experimental_triton_static_launch_contract.md)。

## 固定来源

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)：31–31、76–195、1084–1443；仅所列有界内容。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)：154–161、381–397、471–471；仅所列有界内容。

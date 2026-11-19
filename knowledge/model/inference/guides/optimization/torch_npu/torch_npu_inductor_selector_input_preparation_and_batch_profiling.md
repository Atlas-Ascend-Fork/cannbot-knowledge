---
type: Guide
title: Inductor候选测量：输入重建、批profiling与异常分流
description: 跟踪候选输入storage重建、批profiling归因、同步与异常值，区分设备计时和选择合同。
tags:
- task.implementation
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/select_algorithm.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: implementation
created_at: '2026-11-12T02:15:11Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor候选测量：输入重建、批profiling与异常分流

固定TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的patch_algorithm_selector中，make_benchmark_fn创建输入准备和三种benchmark闭包，最后装到上游AlgorithmSelectorCache；其__call__内的autotune实际调用返回的闭包。发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`同select_algorithm.py路径不存在，仅记录这一路径事实。本组不重审完整缓存选择/预编译算法，没有执行编译、profiler或设备测量。

## 输入去重不等于没有重复生成或别名变化

get_inputs以IR节点名为字典key，但生成表达式仍对每个input_nodes条目执行；同名后值覆盖前值，再取字典values。普通benchmark输入和extern使用的strided输入分别交AutotuneArgs组织，不要把这层命名去重当作任意跨参数Storage别名都已准确重现。

| 输入 | 本地准备 |
| --- | --- |
| 自定义input_gen_fns条目 | extern视图使用真正生成Tensor的size/stride/storage_offset，避免强套原IR几何。 |
| 普通条目 | 从IR尺寸、stride、offset取optimization hint，缺值用配置fallback。 |
| extern所需storage超过现有base | 新建足够长的随机base，再按原base几何及目标几何重建view；float4打包类型先随机uint8再view，其他走randn。 |
| 输出 | 申请示例输出，再用layout offset的hint构造out_extern。 |
| VERIFY启用 | 先测choices[0]，clone其extern输出作为expected；不是独立数学参考实现。 |

扩容分支只把当前extern视图切到新base，没有在这几行把unique_example_inputs中的原对象统一替换；不能假定所有候选路线始终读取同一组Storage和随机值。外部AutotuneArgs、TensorMeta/示例生成器和校验器的完整合同另核。

名为_maybe_reorder_for_catlass_addmm的helper实际门槛是CATLASSTemplateCaller、description不含GroupedMatmulSliceMTla且输入数为3，随后将[0,1,2]改为[1,2,0]。它没有在本地再检查算子名恰好为addmm；函数名/docstring不能加强实际谓词。

## 三条测量路线的准备和错误边界不同

| 选择 | 路线 |
| --- | --- |
| catlass_bench_use_profiling为真 | 直接批profiling，优先于autotune_in_subproc。本地配置初值由环境字符串严格等于'1'生成。 |
| 否则autotune_in_subproc为真 | extern及Catlass仍在当前进程测；其余候选交上游子进程benchmark。 |
| 其余 | 逐候选在当前进程测。 |

逐候选路线先按extern与否取输入/输出、按上述谓词重排、output.zero_，再choice.benchmark；VERIFY启用才校验，有NPU时最后synchronize。它没有在这里逐候选恢复全部输入内容。NPUCompileError、NotImplementedError、RuntimeError转为inf并记诊断；AssertionError重新抛出并标为错误结果；其他Exception只有外部OutOfResources类型被转为inf，其他继续传播。这里不统一拒绝“全部inf”，最终选择仍是外层算法的工作。

批profiling先生成共享输入，为每个候选清output；extern取得to_callable并传out，其余通过bmreq.make_run_fn绑定。所有候选的fn/args/kwargs先保存在列表中，再交一个profiler会话，没有逐项测完立即销毁资源的保证；没有套同一个逐候选异常→inf的try边界，也没有同样的VERIFY调用。

## CSV批profiling是按分隔Kernel组织的均值

批函数申请192×2^20字节所对应数量的int元素，再转float、sum、abs并同步；这是实际缓冲与设备操作请求，不能把“测量开关”当成纯Host日志。NPU Level0 profiler关闭shape/memory/stack/flops/modules和l2_cache记录选项，每个候选调用10次、每次同步，之后追加一次buffer.abs_并同步作为分隔。

| 解析步骤 | 实际行为 |
| --- | --- |
| 文件 | 遍历随机UUID/MD5子目录，遇首个kernel_details.csv就解析并返回；不是合并所有文件。 |
| 行筛选 | 去掉Name含ReduceSum的行，key非None时再按str.contains筛选。不是用独立候选ID归因。 |
| 分隔 | 名称含absaicore的行作为候选末端；按前一分隔后的原DataFrame标签切Duration(us)。 |
| 去首轮 | 当前块行数//10作为首轮Kernel数，丢弃这么多元素，再求和除9与1e3，得到毫秒。 |
| 返回 | 直接按候选下标取func_times[i]；没有在此检查分隔数恰等于候选数。 |

一个候选本身产生同名Abs、ReduceSum，异步/多Kernel事件组织不同，或没有匹配分隔，都可能影响这个局部归因规则；它不是任意模型的通用trace配对算法。数据行按过滤后的标签访问，分隔数量和每轮Kernel数也未独立验证。返回值是上述删首轮后的和/9，不是中位数或完整训练步耗时。

正常读取或找不到文件时会删除测量目录；profiling、CSV读取或解析异常没有统一finally保证清理。对照[Catlass请求与workspace](torch_npu_catlass_binary_cache_and_loading.md)及[实验Triton计时](torch_npu_experimental_triton_autotune_timing_and_input_isolation.md)时，分别保留有效路线、输入/副作用、同步、计时单位和失败值。此卡只有静态证据，没有输出正确性、耗时或产品测量结论。

## 固定实现来源

- [select_algorithm.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/select_algorithm.py)（primary）：34–60、1296–1298、1505–1512、1775–2132。
- [config.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（implementation）：235–238。

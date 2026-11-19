---
type: Guide
title: GE 调度：通算并行、单流、拓扑顺序与静态子图阈值
description: 说明 AllReduce 切分、单流禁用组合、通信顺序和动静子图阈值；隔离主线自动多流策略。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/cc_parallel.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/multistream_parallel_mode.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/single_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/topology_sorting_strategy.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/static_model_ops_lower_limit.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/cc_parallel.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/single_stream.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/topology_sorting_strategy.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/static_model_ops_lower_limit.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/experimental_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/ge_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/ge_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/_option_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/_option_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_prefetch.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_prefetch.py
  role: implementation
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# GE 调度：通算并行、单流、拓扑顺序与静态子图阈值

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。发布部分选取 A2/A3；主线 A2/A3 与950的限定范围见下节，不回推发布版。

## 发布版的调度选择

cc_parallel_enable 默认 False，针对网络 AllReduce 及可连续切分的上下文算子做切分，让计算与通信重叠；不能推广成对所有集合通信的自动切分。

静态 shape 中没有实际并发却承担流切换开销时，可评估 ge_config.enable_single_stream=True，默认 False。该设置不与 npu_prefetch 或 HCCL_OP_EXPANSION_MODE="AIV" 同开，还需遵守显式多流的互斥条件。

## 通信次序和静态子图

experimental_config.topology_sorting_strategy 默认 DFS，可选 BFS/RDFS/StableRDFS。相同通信域的操作没有显式控制边时，非稳定重排可能导致跨 rank 次序不一致。StableRDFS 尽量保留既有顺序，但融合改图后也可能失效；控制依赖仍是主要约束，不把排序策略视为自动修复死锁。

static_model_ops_lower_limit 控制动态图里静态子图的下发：-1 全部动态，0/1 不支持，>1 是阈值，小于阈值的静态段改用动态下发。它不是最大图算子数；提高阈值可能减少统一下发与融合机会，应按实际开销测量。

## 主线补充：自动多流

固定主线 92e1e967bd35ebc37a442b4a969730bf3cf77a3c 的 multistream_parallel_mode 支持 cv、LoadBalance:N、MainStream:N，N 为 1..64；不支持裸 LoadBalance。动态 shape 还要先 ENABLE_DYNAMIC_SHAPE_MULTI_STREAM=1。这是主线补充，不能由本文发布版其他开关推定 26.0 包含相同接口。

- [多流的真实依赖](graph_multistream_dependencies.md)
- [控核与实际核数](torchair_core_limits_and_determinism.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## 四项调度配置的主线对照

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节对应文档已与发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 逐页对照；主线总览声明A2/A3与950PR/950DT，未在这些接口页另列产品排除。950仅属于主线证据，不回推发布配套，也不证明两仓主线组合已兼容。

主线cc_parallel、single_stream、topology_sorting_strategy和static_model_ops_lower_limit页的技术条件与上述发布页保持一致：仅GE，AllReduce切分、静态shape单流及prefetch/AIV互斥、通信显式控制边优先、动态子图阈值分别适用。对照中的文档链接和“使能/启用”措辞变化不表示改变了算法范围。

static_model_ops_lower_limit的完整数值域是[-1,int64最大值]且排除0/1；>1时静态段算子数达到阈值才统一下发，未配置使用GE默认值，不能把默认值补写成示例4。单流与通算并行也不能仅因各自都可设置就推导两者任意组合有收益，仍看最终调度和端到端时间线。

## 自动多流策略的默认与流数量

主线默认None，不启用该项自动多流优化；cv选择Cube/Vector并行，LoadBalance:N按负载分布到至多N条流，MainStream:N把串行节点留在主流并将可并行部分分配到其他流。N为1..64，超过实际可用核数可能降低性能；更多流不是更多硬件资源。动态shape必须先开启环境变量，再由此项选择算法，静态shape可直接生效；仅按文档推荐的网络类型评估，不能从配置被接收推导收益。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/cc_parallel.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/multistream_parallel_mode.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/single_stream.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/topology_sorting_strategy.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/static_model_ops_lower_limit.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/cc_parallel.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/single_stream.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/topology_sorting_strategy.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/static_model_ops_lower_limit.md)（constraint）

## 调度承诺的源码配对

本节把本卡五个功能页的文档承诺对照两固定 pin 的集成配置实现闭合：字段定义与默认值在 `python/torchair/configs/experimental_config.py` 与 `ge_config.py`，setter 校验域在 `_option_base.py`，npu_prefetch 的 GE 转换器在 `_ge_concrete_graph/ge_converter/custom/npu_prefetch.py`。发布 pin 没有 multistream_parallel_mode 字段也没有该文档页，该字段配对仅主线有效；静态源码审阅口径，未运行配置、未编译、未做 GE 侧行为验证。

承诺获得实现锚点（配对涉及的字段在两 pin 定义一致，行号记主线/发布）：

- 默认值与各页声明一致：cc_parallel_enable=OptionValue(False)（experimental_config.py:15/15）、enable_single_stream=OptionValue(False)（ge_config.py:13/13）、topology_sorting_strategy=OptionValue("DFS")（experimental_config.py:24/24）、static_model_ops_lower_limit=IntRangeValue(None,-1,2**63-1)（experimental_config.py:19/19）；仅主线另有 multistream_parallel_mode=OptionValue(None)（ge_config.py:20）。
- topology_sorting_strategy 的候选 BFS/DFS/RDFS/StableRDFS 由 OptionValue setter 强制（_option_base.py:44–56 两 pin 同语义），候选集与文档枚举域一致。
- “若不设置则使用GE的默认值”：static_model_ops_lower_limit 仅在非 None 时把 str(value) 写入 local `ge.exec.static_model_ops_lower_limit`（experimental_config.py:48–51/48–50）。
- “该功能对应GE图引擎的ge.autoMultistreamParallelMode选项”：ge_config.py:42–43（仅主线）非 None 时写 local `ge.autoMultistreamParallelMode`，键名与文档一致。

文档约束不在 TorchAir 层强制（配对差异，按页归组）：

| 文档承诺 | 实际门槛与动作 | 失败/版本边界 |
| --- | --- | --- |
| static_model_ops_lower_limit “0（不支持）/1（不支持）” | IntRangeValue setter 只校验 int 类型与 [-1,2**63-1] 边界（_option_base.py:74–79/61–68）；0、1 通过 setter 并在 max-autotune 序列化时 str() 透传给 ge.exec.static_model_ops_lower_limit | 拒绝点或运行后果不在本仓源码内，静态不可见；数值域本身与文档 [-1,int64最大值] 一致，不能由“被接受”推导 0/1 有可用语义 |
| multistream_parallel_mode “不支持裸LoadBalance（须显式LoadBalance:N）”“N为正整数取值范围[1,64]” | OptionValue(None,None) 无候选校验，任意字符串（含裸LoadBalance、越界N、拼写错误）原样写入 ge.autoMultistreamParallelMode | 格式与范围约束在已读的 setter/序列化路径内无校验点，实际下游拒绝点与运行后果未闭合、静态不可见，不据此断言错误必在 GE 侧暴露；发布版无此字段与文档页，不回推 |
| enable_single_stream 不与 torch_npu.npu_prefetch、HCCL_OP_EXPANSION_MODE="AIV" 同开 | npu_prefetch 转换器只校验 max_size>0、offset>=0、dependency 非 None，不读取该开关；offset!=0 时调 ge.Cmo 包装，默认 offset==0 时构造裸 ge_op(op_type="Cmo"、max_size、type=6、dependencies)，注释标注 7.5 版本 Cmo 无 offset 属性的兼容性动机——同一 GE 算子的两条包装/API 路径，无运行时兼容保证（npu_prefetch.py:18–43/18–44）；HCCL_OP_EXPANSION_MODE 在两 pin 源码零命中，仅文档页出现 | 两条互斥是上游运行期边界：已读的转换器与配置序列化路径内没有该组合的告警或拦截，对 enable_single_stream 的 rg 定位（两 pin python/ 树）也仅命中 ge_config.py 与 compiler_config.py，后者另有路线告警门（见[配置边界](torchair_compiler_config_boundaries.md)），不能由该转换器推断全 TorchAir 无告警；不能把“配置被接受”当作组合安全 |
| cc_parallel/topology_sorting/static_model_ops “仅适用于GE图模式场景” | 三个字段的 GE 键只在 as_dict 的 max-autotune 分支输出（experimental_config.py:40–52/40–51）；捕获路线（reduce-overhead/npugraph_ex）不序列化这些键 | 与文档一致，但精确语义是“捕获路线不输出该键”，不是配置层拒绝；npugraph_ex 模式的告警语义与排除表见[配置边界](torchair_compiler_config_boundaries.md) |

配对不改变前文结论：oo_level=O1 覆盖 ge.topoSortingMode 同名 local 键的合并顺序仍以[分组序列化与模式消费者](torchair_grouped_config_serialization_and_mode_consumers.md)为准；单流/通算并行各自的互斥与收益判断仍按“验证边界”一节执行，不从配置被接收推导收益。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/experimental_config.py)（implementation）：1–55 完整窗口读取（字段定义与 max-autotune 序列化分支）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/experimental_config.py)（implementation）：1–55 完整窗口读取，与主线同段对照；同文件 tiling_schedule_optimize 的 local/global 差异已由序列化卡记录，本节不重述。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/ge_config.py)（implementation）：1–45 全文读取。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/ge_config.py)（implementation）：1–44 全文读取（无 multistream_parallel_mode 字段）。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/_option_base.py)（implementation）：11–62、63–102 两段窗口读取（OptionValue/IntRangeValue setter 校验域）。
- [新增来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/_option_base.py)（implementation）：1–80 窗口读取；两 pin setter 语义一致，全文件 diff 其余为排版差异。
- [新增来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_prefetch.py)（implementation）：1–43 全文读取。
- [新增来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_prefetch.py)（implementation）：1–44 全文读取；校验与双分支 Cmo 转换（offset!=0 走 ge.Cmo，默认 offset==0 走裸 ge_op）与主线一致，仅排版差异。
- 同时对两 pin 的功能页做承诺复核：主线 static_model_ops_lower_limit/topology_sorting_strategy/single_stream/multistream_parallel_mode/cc_parallel 全文复读；发布同路径四页 raw diff 仅链接与措辞差异（static_model_ops_lower_limit 逐字节相同），发布无 multistream_parallel_mode.md。

---
type: Runbook
title: vLLM Ascend msprobe 精度定位：dump 配置、调度步与图模式采集
description: 核对 PrecisionDebugger 与 AclGraphDumper 的配置、start/stop/step、真实调度和 dummy 路径，按 rank、输入及采样点对齐数值差异，防止把无 dump 或局部采集误判为精度通过。 PrecisionDebugger.start 的 scheduled_tokens 是调度采集的具体参数入口。
aliases:
- PrecisionDebugger.start(..., scheduled_tokens=...)
tags:
- task.debugging
- task.testing
- topic.precision
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/performance_and_debug/msprobe_guide.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_model_runner_v1.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/worker/test_model_runner_v2.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_ascend_config.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/performance_and_debug/msprobe_guide.po
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tools/generate_zh_docs.py
  role: implementation
created_at: '2026-10-29T17:33:00Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-02T04:46:39Z'
---

# vLLM Ascend msprobe 精度定位：dump 配置、调度步与图模式采集


## 触发、版本与证据强度

适用于新模型输出漂移、NaN/Inf、图模式与 eager 结果不同，或已启用 msprobe 却没有目标中间张量的排查。来源为 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的文档及 V1/V2 Runner 调用点；msprobe 是外部依赖，本卡没有阅读其内部采集实现，也没有执行服务或生成 dump。

文档未给出覆盖整项工作流的硬件集合，保持 draft 与空平台范围；不从通用 NPU 描述推出所有芯片、模型或图模式均可采集。先记录实际 Runner、有效 `compilation_config.cudagraph_mode`、依赖版本与构建能力，再选路径。

## 第一层探针：配置是否到达实际 Worker

`additional_config.dump_config` 是内联 dict，`additional_config.dump_config_path` 是已有 JSON 的字符串路径。两者同时非 None 会报 ValueError；内联值不是 dict、路径不是 str 也会报错。工厂只做这一层类型/互斥处理，不代表配置里的字段都被外部 msprobe 接受。

内联 dict 被写到进程当前目录下固定的 `.vllm_ascend/msprobe/msprobe_dump_config.json`，再以文件路径传给 debugger。写入使用普通 `open(..., 'w')`；没有按服务实例生成独立文件或原子 rename。由此推导：同一工作目录内启动配置不同的实例可能互相覆盖，须核对 Worker 读到的内容和路径可见性，使用隔离工作目录或各实例独立路径。这个风险是静态推导，不是本次观察到的故障。

配置例子只表示传参形状；输出目录应由目标环境提供：

```json
{
  "dump_config": {
    "task": "statistics",
    "level": "L1",
    "dump_path": "/data/msprobe_dump",
    "statistics": {"list": []}
  }
}
```

检查每个目标节点/Worker 的配置文件、写权限和输出目录。分布式目录的 rank 名、设备身份、全局/局部 rank 映射须随产物记录，不能把目录编号直接当作已核对的拓扑。

## 第二层探针：按有效图模式选择依赖

| Runner 实际模式 | 初始化对象 | 采集前提与边界 |
| --- | --- | --- |
| `CUDAGraphMode.NONE` | `msprobe.pytorch.PrecisionDebugger(dump_cfg)` | 启动真实调度执行时传入 `self.model` 和 `scheduled_tokens`；文档对不识别该参数的 TypeError 要求 msprobe v26.2.0 或更高 |
| 非 NONE | `msprobe.pytorch.AclGraphDumper(dump_cfg)` | 在 load_model 尾部开始，早于后续图 capture/replay；导入失败会报包含 `aclgraph_dump enabled` 的 RuntimeError，需匹配带扩展的外部构建 |
| 没有 dump 配置 | `debugger=None` | start/finalize 都可直接返回，正常完成推理并不意味着执行了采集 |

文档同时保留 `Please enforce eager mode` 的排障建议，但当前源码明确实现图采集分支。不能把所有 dump 故障统一处理为“关闭图”；先判断是选错模式、扩展未编入、版本接口不匹配，还是目标路径未被覆盖。切换 eager 仅能作为受控对照，须保留原图模式的问题证据，不能以 eager 正常证明图模式正确。

## 第三层探针：调度步、正常返回与异常缺口

两个 Runner 的入口为 `_start_dump_data` 与 `_finalize_dump_data`，其小型状态机相同：

```text
start: debugger 缺失或已 started -> no-op
       否则 debugger.start(model, **kwargs)，成功后 started=True
finalize: debugger 缺失或未 started -> no-op
          有 stop 属性则 stop()，started=False
          debugger.step(**kwargs)
```

无 stop 的 debugger 会跨步保持 started；不能要求每次 step 前都出现一次新的 start。源码按对象有没有 stop 判断，而不是按类型名强制调用。外部 stop/step 抛错的恢复语义未由此状态机保证。

| 调用路径 | 静态可见行为 | 消费时的限制 |
| --- | --- | --- |
| V1 真实 batch | 在有效请求 token 列表通过检查后 start，并传入 scheduler 的 `num_scheduled_tokens` | 每个请求可跨多个调度步；chunked prefill、连续批处理或投机不能按一次 HTTP 请求对应一次 step 来对齐 |
| V1 独立 encoder producer | encoder 执行前 start，成功后 finalize，再返回 encoder 输出 | 独立检查 encoder 与 decode 的采样范围，不能只看 decode 目录 |
| V1 普通 PP 非末阶段 / pooling | 返回 intermediate 或 pooling 输出前 finalize | 这些路径不必经过普通采样末尾；按实际分支找收尾点 |
| V1 普通生成 | sample_tokens 路径尾部 finalize | “模型 forward 已返回”不是一定已经完成 dump 的时点 |
| V1 无 token / 无有效 token | 可在 start 之前直接返回；external-launcher DP 的 idle 还可做协调 dummy | 没有 dump 可属于没有真实采样工作，并非工具必然故障 |
| V2 真实调度 | `total_num_scheduled_tokens>0` 且非 dummy 时 start；常规生成在 sample_tokens 后 finalize | 普通 decoding PP 也沿 sample_tokens 收尾；非末 pooling 收到 IntermediateTensors 时单独 finalize，末阶段在 pool 后收尾 |
| V1/V2 dummy / 图预热 | dummy 收尾使用 `step(dump=False)`；V2 eager dummy 不打开新的窗口 | 防止把 warmup/capture 的假请求误作实际故障 token；不能从 dump=False 推导外部工具一定删除所有缓存 |

文档称每条路径都会 step 并得到完整数据集；当前调用点不支持把这句话当成异常保证：start 前存在返回，且模型 forward 等发生异常时，没有统一包住整个 dump 周期的 try/finally 收尾。V2 的 `finish_execution` finally 用于另一执行状态清理，也不能替代 dump finalize。崩溃后保留最后成功 step、错误日志与缺失范围，结论为采集不完整，不是精度通过。

上游 UT 用 mock 描述 stop-capable/no-stop、重复 start、真实/零 token/dummy、PP 与 pooling 等预期；本次仅阅读有关测试片段，没有运行它们，更没有据此证明外部 msprobe 或目标 NPU 的行为。

## 第四层探针：采集粒度与产物是否满足比较任务

先用 statistics 缩小首个异常位置，再在小窗口用 tensor 保留实际数据。task 决定统计或张量负载，level 决定采样层级，两者不能混为一维：L0 为 Module，L1 为 API，mix 两者都有。文档概念段将 L1 简称为统计，但附录也给出 L1 tensor 的 API I/O；不能由 L1 推断没有张量负载。

L0/mix 需要模型/模块句柄；结构可视化须有非空 `construct.json`，L1 的 construct 为空。普通 eager 示例包括每个 step/rank 的 `dump.json`、`stack.json`、`construct.json`、可选 `dump_tensor_data/`；`dump_error_info.log` 是工具失败线索。图模式示例只展示 dump.json，不能假定它具备同样的结构文件或直接满足图可视化前提。

文档说明 rank 空列表取全部，单卡也用 `[]`；step 空列表取全部迭代。其 eager/graph 表明确 graph 不支持 step、async_dump、scope、dump_enable，list 两者均列为支持。按文档层级，过滤 scope/list 等放在相应 task 配置中：scope 是按工具命名规则界定起止范围，list 可为完整 API 名、子串或 mix 的模块展开；别和知识卡检索 Scope 混用。keep_all_ranks、tensor_list、filters、token_range 等仅有提示，具体 schema、层级、版本和作用仍需外部 msprobe 依据，不能自行拼成已验证配方。

dump.json 顶层记录 task、level、framework 和 dump_data_dir；data 内按模块/API 名记录 input_args、input_kwargs、output，模块还可含 parameters。张量元数据包括 dtype、shape、统计值和 data_name；data_name 指向负载时才有逐元素比较基础。模块列表/元组会在名称中增加模块索引；参数、嵌套输入的小数编号和调用计数不能直接当作模型层号。摘要相近、无 NaN 或目录存在都不能证明输出质量通过。

## 对齐、定位与验收

问题侧与可信基准侧固定或明确映射：模型/checkpoint、权重与量化 scale、tokenizer/模板/媒体预处理、原始输入、seed/采样、实际 token/调度范围、并行拓扑、rank 与图模式。跨实现允许显式层映射，但不同算子名、融合边界、shape 或分片需要先解释，不能直接认作数值 bug。

文档提供 `msprobe graph_visualize -tp <problem> -gp <golden> -o <output>`；单图省略 golden，输入粒度可为单 rank、某 step 或多 step 根。结构所需文件齐全后，结果为 build/compare 时间戳的 `.vis.db`，用具备 `tb_graph_ascend` 的 TensorBoard 查看。overflow、fuzzy_match、layer_mapping、tensor_log、progress_log 是外部 CLI 选项，模糊匹配不证明节点语义等价。

沿首个可比的异常节点回溯输入、参数、前后算子与传播顺序，区分非有限值的产生与继发传播。没有干净基准时，自比较/最小复现只能证明采集与复现性，不能证明正确性。任务质量标准按[精度验收合同](../../guides/bringup/vllm_ascend_accuracy_evaluation_contract.md)另验；性能 trace 使用[服务剖析](../../guides/optimization/vllm_ascend_service_profiling.md)，最终性能用关闭 dump 的基线测量。

验收产物应含两侧配置、目标输入与采样点、rank 覆盖、工具版本、原始 dump/错误日志、节点映射及差异判据。恢复服务 dump 配置；数据缺失、调用异常、采样错位或基准不可信时停止根因结论。本卡只完成固定版本静态蒸馏，没有实测精度、采集完整性或优化收益。


## 中文PO与当前正文的对应边界

对应msprobe_guide.po已逐项复核67个有效非空翻译及obsolete区段；译文也保留“每请求都会完整step”的宽泛描述，仍按本卡Runner控制流限定，不因中文措辞相同就提升证据强度。部分附录/模块列表相关译文位于#~记录，不能用有效条目数量声称当前页全译。

固定generate_zh_docs.py仅收集非空msgid/msgstr，源码没有显式检查entry.obsolete或fuzzy；本批未安装/执行外部polib或上游生成器，因此不能单凭#~标记断言当前构建必然排除或采用这些翻译。真正应用还取决于解析器、当前英文文本、围栏/inline保护、匹配和最长非重叠选择；这次来源绑定不等于线上HTML/全部中文页覆盖。

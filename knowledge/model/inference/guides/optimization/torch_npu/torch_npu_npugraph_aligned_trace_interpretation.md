---
type: Guide
title: NPUGraph对齐trace：依赖可视化与重建时间的边界
description: 区分原始dump与派生trace的流合并、时间重建、控制配对和检查范围。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_utils.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/graphs.py
  role: implementation
created_at: '2026-11-12T02:31:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# NPUGraph对齐trace：依赖可视化与重建时间的边界

固定TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的_npugraph_utils与NPUGraph.debug_dump消费者。生成的aligned trace重建时间与流标记，适合看局部依赖，不是保留原始设备时间的性能测量。发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`同helper路径不存在，只记录准确路径差异。本卡未执行trace改写、设备dump或符号求值。

## debug_dump只在文件状态变化后尝试对齐

Python包装在super().debug_dump前后比较stat中的device、inode、size、mtime_ns和ctime_ns；stat失败返回None，当前状态缺失或与之前相同就直接返回原result。它防止对没有被这次dump重写的旧文件盲目对齐，但没有用内容hash证明文件变化或新捕获成功。

super调用本身在try之外；只有后面的helper导入/align异常被转为warning并保留原result。对齐失败时，原有aligned文件可能仍在磁盘而未更新。直接调用align_trace_json则没有同样的统一异常捕获，不能混用两入口的报错语义。

## 流合并与时间重建会主动改变可视化几何

| 阶段 | 本地行为 |
| --- | --- |
| 输入 | json.load后直接把顶层对象当事件列表；不是任意Chrome Trace envelope的通用解包器。 |
| STREAM_ACTIVE | 找Task Type或name符合且有Active Stream Id的事件，把对应streamN上的全部事件搬到激活事件的tid，时间平移到目标流末尾+merge_gap，必要时改args['Stream Id']。 |
| 每流排序 | 按原ts和原列表下标稳定排序；按tid分组，没有再加pid作为分组key。 |
| 时间 | 每条流首事件改从0开始，后续ts=前一个结束+0.2；EVENT_RESET的dur也改为0.2。 |

合并使用源流全部事件，不只选激活点之后的某个窗口；随后重建又丢弃原来的绝对起点与空闲间隔。0.2是可视化常量，不是本次测到的设备等待开销。原始事件dur除reset及后述wait外通常沿用，但仍不能用aligned图的横轴跨度直接比较真实端到端延迟或重叠收益。

## record/wait配对只是一组局部命名规则

_parse_control识别EVENT_RECORD、EVENT_WAIT、MEM_WRITE_VALUE、MEM_WAIT_VALUE前缀，以名字最后一个下划线分量作handle；record/write共享一个槽，wait/mem-wait共享另一个槽，同handle后出现者覆盖前者。没有按设备、pid、代际或重复使用次数建立完整事件历史；EVENT_RESET不参与这组配对。

同tid配对不做跨流对齐。跨tid若wait.ts已经晚于record_end则跳过；否则把wait.dur改为record_end-wait.ts，并按差额平移该流后续任务。差额可以缩短原wait，不是只增加等待时间。最多200轮，无法收敛抛RuntimeError；输入事件已被原地修改，没有失败回滚。

配对后生成Chrome flow和instant标记；handle能int化则直接作id，否则用abs(hash(handle))取模。非数字handle的flow id不保证跨Python进程稳定，取模也不是全局无冲突身份。非控制算子名会删去全小写字母/数字且含超过5个数字的下划线分量，可能折叠名称；不是已证明仅删除某种唯一hash格式。

## validate验证生成规则，不验证设备真实时序

验证只检查ph=='X'的事件：float类型ts/dur的非finite值、跨流已配对事件端点，以及每流首ts=0、后续固定0.2间隙。它不是对所有类型值、负duration、未配对handle、所有原始ph事件或设备并发语义的完整校验。跨流wait开始已晚于record结束的配对另被跳过，不能把通过检查当成所有设备事件均被准确归因。

align_trace_json验证通过后才写JSON，默认另生成.aligned.json；显式output路径没有拒绝等于input，因此“原始文件不变”仅适用于默认派生输出或调用方选择不同路径，不能按模块docstring作无条件承诺。命令行同样只转发input/output/merge-gap，未增加另一层数据验证。

排查时保留raw dump、这次文件状态变化、对齐是否成功和有效流/handle命名，先用raw及真实profiler判断耗时，再用派生图辅助解释依赖。这里没有测量执行时延、认证图捕获产品或扩大底层GE/ACL执行语义。

## 固定实现来源

- [_npugraph_utils.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_utils.py)（primary）：1–414。
- [graphs.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/graphs.py)（implementation）：678–722。

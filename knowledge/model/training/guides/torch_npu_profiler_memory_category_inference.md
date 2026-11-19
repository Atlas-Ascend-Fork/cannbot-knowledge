---
type: Guide
title: Profiler内存类别推断：梯度、参数、激活与优化器状态
description: 解释tracer与dataflow分类顺序、id/key/version优先级及推断边界，避免把类别标签直接当作模型真实语义。
tags:
- task.debugging
- topic.performance.analysis
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py
  role: implementation
created_at: '2026-11-10T13:28:29Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler内存类别推断：梯度、参数、激活与优化器状态

本卡完整阅读固定主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的本地内存时间线模块，并与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`逐行、完整AST对照。两版1099行去行尾空白后相同；严格AST唯一差异是CategoryElement说明docstring的一处尾空格，技术含义相同。本卡补全分类表、分类闭包和消费者；不据此证明外部schema、采集元数据或真实训练归因一致。平台未知，保持draft、空平台；没有执行上游或解析采集数据。

## 实际消费者和分类身份

MemoryTimelineParser.run直接构造MemoryProfile，后者从EventTree建立DataFlowGraph，再依次执行：梯度/临时、Python tracer参数、输入、dataflow参数、激活、优化器状态、autograd细节分类。MemoryProfileTimeline接收同一分类表并用于导出。事件字节累计和类别迁移见[时间线事件合同](../../inference/guides/optimization/torch_npu/torch_npu_profiler_memory_timeline_event_accounting.md)，这里解释标签的来源。

CategoryDict按Tensor的id存储容器，查询依次取`by_id`、`by_key`、`by_version[(key,version)]`。参数、梯度、优化器状态按id设置；临时按完整TensorKey；输入、激活、autograd细节按版本设置。`set_by_id`后写覆盖，版本层则使用setdefault保留先写项；不能把执行顺序解释成“梯度永远优先”，也不能认为一个Tensor的所有版本必然同类。

TensorKey要求tensor id、allocation_id和storage ptr均不缺失，并含设备身份；只有DeviceKey而无TensorKey时类别查询返回None，即Unknown。标签依赖可关联元数据，不是对全部设备分配的语义认证。

## 直接识别的梯度、参数和临时量

| 类别/来源 | 所选实现的判据 |
| --- | --- |
| 梯度 | AccumulateGrad需处于BACKWARD_FUNCTION scope，名字为`torch::autograd::AccumulateGrad`或带`struct `前缀的形式；只检查第一个子事件为`aten::detach`/`aten::add_`且首输入为Tensor元数据，取该输入作为梯度。PyCall中的module/optimizer参数元数据也可提供grad。 |
| tracer参数 | 从PyCall的module_parameters与optimizer_parameters取param.tensor，以id标PARAMETER；不是由Python变量名或Tensor形状识别。 |
| 临时 | 同一DataFlowNode的边同时为allocation与deletion，即所选算子子树内创建又释放，按TensorKey标TEMPORARY；不是一切“寿命很短”的分配。 |

DataFlowGraph选择匹配schema的TorchOp、backward节点和分配事件作为叶子，按开始时间排列；一个节点可包含内部子树。输出包括节点内分配且未删除的Tensor，以及被认定变更的输入的新版本。输入变更判定消费SchemaMatcher结果，所读边逻辑对明确可变或仅未知的集合保守视作变更；相关的[SchemaMatcher与数据流合同](../../inference/guides/optimization/torch_npu/torch_npu_profiler_memory_schema_and_dataflow_versions.md)明确区分仅未知集合与混合False/None集合，不把版本增长当成实际执行了新分配。

## 输入和参数的dataflow推断

`_set_inputs`先逆序遍历结点：如果结点输入/输出中有已标GRADIENT/PARAMETER，或已进入produces_gradient集合的版本，就把该结点所有输入/输出加入集合。随后移除backward结点的输出，并排除id已依赖梯度/参数的候选，余下以版本标INPUT。

“依赖梯度”集合由`_any_version_depends_on_gradient`反复向前传播到不再增长：结点只要有GRADIENT/PARAMETER输入或集合内id输入，就把这些输入id及全部输出id加入。它是所采dataflow上的闭包，不能等同于用户定义的所有模型输入。注释说实际常见两轮即可，但循环实际以集合不再增长为终止条件，没有写死两轮上限。

`_set_parameters_using_data_flow`从已标INPUT版本出发，沿非backward且输入/输出无已标GRADIENT的结点传播前向候选，收集不在候选前向集合中的输入作为候选参数；再要求其版本最终贡献到梯度、其id属于上述梯度依赖集合，才按id标PARAMETER。这是补充推断，不是看到任意常量或跨step复用就认定权重。

只有前向或缺少梯度/参数元数据的采集，可能不具备这些推断链；不能拿Unknown比例或缺少INPUT标签直接评价模型优化是否正确。

## 激活、优化器状态和autograd细节

| 类别 | 判据与先后影响 |
| --- | --- |
| ACTIVATION | 结点输入类别至少有INPUT/ACTIVATION，全部输入类别仅属于INPUT、ACTIVATION、PARAMETER、TEMPORARY，且结点非backward，才对输出版本setdefault。任何未知或其他类别输入都会使该结点不满足这组条件。 |
| OPTIMIZER_STATE | 只从PyCall.optimizer_parameters中各param.state的Tensor元数据提取有效TensorKey，按id设置；不靠Adam、SGD名字或state大小猜测。此步骤在激活之后，可覆盖同id此前的标签。 |
| AUTOGRAD_DETAIL | 只处理当前结点或其祖先TorchOp scope包含BACKWARD_FUNCTION的结点；输出version=0，或前一version类别为None/AUTOGRAD_DETAIL时才setdefault。不是把全部backward输出统一改类。 |

激活传播发生在优化器状态标注之前；这是当前实现顺序，不应改写成分类器已提前知道所有优化器状态。by_id、by_key的更高查询层也可遮蔽版本层标签。颜色、列号和事件版本迁移需按实际导出合同解释，不用Category枚举值直接索引汇总列。

## 诊断使用和边界

先确认采集开关、设备、stack/module及参数/optimizer元数据，再检查相应TensorKey、版本和所采子图；同一逻辑模型在不同采集窗口、缺失事件或元数据下可能获得不同标签。NPU重复输出版本检测在所读DataFlowGraph.validate中仅警告并返回，不意味着它会修复不完整数据。

本卡覆盖本地分类方法及其直接提取/边消费者；SchemaMatcher全部本地分支另见[Schema与数据流版本](../../inference/guides/optimization/torch_npu/torch_npu_profiler_memory_schema_and_dataflow_versions.md)。EventTree身份恢复和Python回放分别按其主题卡解释，外部运行时对象别名与真实训练样本未在本卡验证。没有对分类精度、重计算节省量或OOM根因作运行验证。采集与产品前提复用[时间线与元数据文档](../../inference/guides/optimization/torch_npu/torch_npu_profiler_memory_and_metadata.md)。

## 类别快照不会枚举全部分配对象

_category_snapshot收集各DataFlowNode的输入版本、中间量version0、输出版本，再补by_id_keyset中的key/version0；按key/version排序后查询类别。set_by_id既覆盖该id的当前by_id值，也记录这次设置所见的key；它没有从所有物理分配自动建立完整对象清单。set_by_key和版本表是独立容器，Unknown DeviceKey查询不进入Tensor类别。

get_scopes只沿当前事件到root收集TorchOp的scope；_is_backward只需其中包含BACKWARD_FUNCTION。直接梯度提取则有更窄的tag/首子节点/名字判据，两条检查不能混成“任意backward节点都有梯度”。Python参数提取分别检查module_parameters和optimizer_parameters，二者同时存在时可都产出；这与StorageSizeDict中PyCall元数据先module、elif optimizer的分支不同。分类是否识别与大小是否估算是两条消费者，不能互相替代。

## Evidence

- [ac0e156 _memory_timeline_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py)：直接证据范围 44–64, 145–214, 360–599, 682–866；main complete 1099-line raw text read; release all raw line deltas checked, rstrip-lines exact; strict AST differs only one CategoryElement docstring trailing space; local technical meaning preserved。
- [f3ecfe4 _memory_timeline_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py)：直接证据范围 44–64, 145–214, 360–599, 682–866；main complete 1099-line raw text read; release all raw line deltas checked, rstrip-lines exact; strict AST differs only one CategoryElement docstring trailing space; local technical meaning preserved。

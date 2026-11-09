---
type: Guide
title: vLLM Ascend图更新：provider基数、弱引用资源与重写边界
description: 沿UpdatableGraph、GraphUpdateTask与BreakableACLGraphWrapper核对捕获上下文、provider顺序/基数、运行参数覆盖、PA工作区key和更新流事件，区分ENPU更新顺序及两种no-op清理的实际谓词与未闭合注册，避免将地址相同或shape相同视为图正确。
aliases:
- UpdatableGraph.resolve_tasks
- UpdatableGraph.get_capture_resource
- GraphUpdateTask.bind
- BreakableACLGraphWrapper
- AllGatherChunkNoOpCleanupPass
- NoOpEliminationPass
tags:
- task.implementation
- task.debugging
- topic.graph_execution
- topic.memory
- topic.attention
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/updatable_graph.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/breakable_aclgraph.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/passes/allgather_chunk_noop_pass.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/passes/noop_elimination.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/compilation/acl_graph.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v2/aclgraph_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/attention_v1.py
  role: constraint
created_at: '2026-11-03T04:47:18Z'
updated_at: '2026-11-03T04:47:18Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend图更新：provider基数、弱引用资源与重写边界

## 任务与证据

新Attention在第一次捕获后长度不刷新、多module草稿任务数错位、工作区变小、异步重放读旧参数或清理pass改变别名时，需要检查任务和资源身份。本卡固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取updatable/breakable图与两份清理pass、公共ACLGraphWrapper；utils、MRv2初始化及FIA注册仅读明确片段。

[ACLGraph机制](../../concepts/frameworks/vllm_ascend_aclgraph_replay_lifecycle.md)维护桶与设计，[图融合注册](vllm_ascend_graph_fusion_pass_contract.md)维护另一套pattern生命周期；本卡补实际task/provider与资源接线。Native Breakable父类、torch_npu图API、完整后端与编译器未闭合，未导入、运行上游、图、NPU或性能实验，不宣称完整硬件支持。

## 捕获上下文决定register_task是否登记

UpdatableGraph.capture_begin先调用父begin，再设置_ACTIVE_GRAPH ContextVar并保存token；capture_end在finally重置token、清capture_token并把capture_resources递归转弱引用。资源与task列表没有在这两个方法里完整clear，不能把同一个对象的再次capture当幂等重置；父begin/end失败与部分任务清理需沿外部runtime验证。

模块级register_task在没有active graph时立即运行operation；在捕获中才创建ExternalEvent，先在当前stream安排wait/reset，再开启task group、运行operation、取得handle，弱引用kwargs并登记task。注册动作本身会执行算子，不是纯Host描述构造。

每个provider在字典里累计注册次数，task保存其provider_index。provider必须能作为稳定字典key，等价性与hash决定是否共享计数；不是仅按layer_name字符串全局归类。operation或group-end失败时，此函数没有统一finally完成整个task组回滚，不能靠tasks未追加推断底层capture完全未改变。

## resolve的基数、顺序和参数覆盖

ContextSource调用provider.resolve(context)，返回长度为1的序列；SharedSource按provider.layer_name筛选传入params的同名条目，删除每条的layer_name键，保持原输入顺序。它不调用resolve，也不按spec步号重新排序。缺layer_name得到None并可能匹配同样缺该键的条目，调用者应提供明确身份。

resolve_tasks先为每个provider取参数序列，assert其长度精确等于捕获注册次数，再按provider_index绑定。ContextSource天然只给一项，不能在一个相等provider下登记多次却期待它自动复制。SharedSource即使条数正确，顺序错也会给错误task配参数。

GraphUpdateTask.bind以{原kwargs,运行params}合并，运行值覆盖同名捕获值，并返回dataclass副本；没有额外shape、dtype、alias或版本校验。新增provider要明确哪些字段可以变化、哪些地址必须固定，不能把任意用户字典直接作为安全图更新。

apply在update_stream的graph_task_update_begin/end之间调用operation，再在该流record event；它没有自己的异常finally补end或record。record是提交事件，不是Host等待设备完成。事件需要与捕获时wait和外部replay时序一起验收，不能由Python返回认定本批更新已被消费。

## 工作区key和弱引用不是所有权证明

get_capture_resource按key首次factory并缓存；use_max_workspace=True时每次还再调用factory，比较numel×element_size并保留较大者。首次未命中也可能调用两次factory；这不是无分配查询，也不按dtype/shape变化自动新建key。旧图已捕获的指针是否与后换的大workspace一致，需要实际捕获顺序证明。

capture结束后资源和task kwargs中的NPU Tensor变为不持有原Tensor寿命的弱引用；普通非NPU Tensor原样保留。递归只处理选定容器和IntermediateTensors，不自动识别任意用户对象内部的Tensor。图内存池或明确外部owner必须维持backing；保留弱引用不等于保留其内容与生命周期。

update对精确operation==torch_npu._npu_paged_attention的任务做局部workspace复用，缓存只存在于本次update。key含context_lens指针/shape、q/K/V/block_table/out的shape/dtype、heads与scale；不包含所有输入stride、device或context_lens内容。它不是跨所有Attention/任意布局的普遍workspace相容性证明。

PA查询前从kwargs副本pop workspace，原参数缺该键会失败；查到后修改resolved task的kwargs再apply。FIA的已读调用点则用get_capture_resource及自己的max-workspace查询注册operation/provider，不由PA特殊分支自动重查全部FIA资源。完整kernel workspace算法和异步临时值寿命继续pending。

## wrapper时序按实际路径消费

ACLGraphWrapper按forward context的模式与descriptor捕获/重放；它不把每批输入copy到自建持久buffer。DEBUG地址检查只覆盖位置args里的直接Tensor，不递归检查kwargs或容器，也不证明相同地址的长度/内容已刷新。

FULL且use_updatable_graph命中时必须有update_stream：draft使用SharedSource(draft_model_metadata)，其他使用ContextSource(attn_metadata)。enable_enpu=True按update→replay提交，False按replay→update；不能无版本地把二者改成相同顺序。公共use_updatable_graph仅判断backend是否AscendAttentionBackend子类，不能凭它证明全部混合后端或模型参数可更新。

FULL普通路线在非ENPU且非Eagle draft merge条件下同步当前流，其他路径依赖相应Runner/事件合同。BreakableACLGraphWrapper在FULL捕获前置capturing=True，父capture正常返回后弱引用三套workspace；本覆盖没有独立finally负责复原标志。FULL回放沿相同ENPU/Eagle条件选择同步，再委托Native父replay并返回entry.output。

MRv2管理器选定初始化点按需构造Breakable wrapper，update_stream来自model_runner；这里没有读完其全部capture分段、Native graph key与每次调用。不能由继承名字或标志存在推断所有breakable/multi-module组合已配对。

## 两份清理pass的谓词与可达性

AllGatherChunkNoOpCleanupPass构造时取得TP group/world size，匹配dim0 all_gather后接sequence_parallel_chunk_impl，替换为原input。它注册的是这条精确往返，不是任意AllGather后slice都等于恒等，也没有在本文件增加通用stream/布局extra_check。通信组、chunk语义与实际图匹配要由调用者核对。

NoOpEliminationPass只考虑view/reshape的method或精确aten overload，要求input/output都有val元数据、rank相同且各维statically_known_true相等，才直接替换所有uses并删节点。未知符号维不由它强行守卫；它没有比较stride、storage_offset、allocation或alias。shape相同不充分证明一次可能物化连续副本的reshape在所有后续mutation场景都无意义。

本次全Main引用搜索只找到两pass的类定义，未找到直接构造/注册调用；当前四类GraphFusion manager也未在其configure中添加它们。二者已全文提炼，但运行注册/可达性继续pending；不能把实现文件存在写成默认已生效，亦未证明动态插件绝不会使用。

## Agent验证产物

记录有效图模式、descriptor、provider具体对象/相等关系、layer_name、登记次数及参数顺序、kwargs覆盖键、workspace factory次数/大小/地址与真实owner。首次capture、同桶多步、长度变化、共享provider多task、草稿多步、混合layer shape、异常与再次capture分别观察；先核对输出和事件顺序，再评估内存/延迟。

清理pass另存真实注册点及前后FX图，覆盖同shape不同stride、reshape副本后mutation、符号维和通信组；不以removed_count替代等价性。外部图API、Native父实现、设备同步/数值和性能尚未执行验证，本卡保持draft，不用全文件阅读或弱引用当全链路完成。

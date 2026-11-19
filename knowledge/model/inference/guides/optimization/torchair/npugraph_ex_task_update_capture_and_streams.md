---
type: Guide
title: npugraph_ex任务更新的捕获、事件与重放流
description: 闭合workspace/out、task-group与Replay更新流，解释handle/event、限核、确定性及共享更新列表的边界。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
created_at: '2026-11-10T13:12:12Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npugraph_ex任务更新的捕获、事件与重放流

## 固定版本与实际消费者

本卡定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c中独立npugraph_ex包的workspace/out改写、task-group代码生成、CapturedGraphUpdateAndReplay和捕获元数据交接。仅描述这些消费者，不回推同名发布模块或旧python/torchair路线。没有执行生成代码、捕获、缓存/模型反序列化、设备或并发测试，保持draft与空平台。

可更新参数如何选出见[规则与图key](npugraph_ex_task_update_rules_and_graph_keys.md)；本卡闭合[Host Tiling示意](npugraph_ex_capture_controls.md)背后的捕获/更新调用，不把示意图当成已测量的开销完全重叠。

## 从普通Attention到预分配out重载

fx2acl优化阶段调用replace_dynamic_workspace_ops。仅处理map中的目标，且注册output_keys非空、节点具有Meta val时，才在原节点前插入最大workspace查询、按Meta shape/dtype/device创建输出Tensor，再调用对应out重载并替换原节点uses，最后删除旧节点/lint。输出Meta个数必须与注册输出个数一致；ATB的零output_keys路径在这个改写函数直接跳过，不为它凭空创建workspace或输出。

FIA的workspace与输出由图构造明确传给out重载，不是每次task-update重新运行任意动态分配器。这里的“最大workspace”调用也不是本卡已证明它对所有变化长度、所有模型或产品均足够；需要遵守对应算子合同，并核对实际图shape与捕获策略。一般用户I/O、clone和输出Storage生命周期另见[输入缓冲](npugraph_ex_replay_input_buffers_and_copy_paths.md)与[输出重建](npugraph_ex_output_reconstruction_and_storage_lifetime.md)。

## Capture时插入外部event与task-group

代码生成对need_updated_ops中准确命名节点替换其调用文本。is_capturing分支创建ExternalEvent，在当前capture stream执行wait/reset，再graph_task_group_begin；调用原out/ATB目标之后graph_task_group_end，保存handle、外部event、捕获时流的Cube/Vector限核、参数名/位置及重建后的args/kwargs到UpdatedNodeInfo。

reconstruct_args_kwargs对Tensor按已记录的Storage元数据重建包装，一层list/tuple元素另处理，不是对捕获输入数据做通用深拷贝。它没有在这里任意递归复制所有嵌套对象；不要把“保存args”理解为已经隔离所有存储或可无条件替换参数对象。

捕获调用fx_forward时传入node_info列表和is_capturing=True，成功后为该graph_key建立CapturedGraphUpdateAndReplay。实际源码以字符串替换把task-group片段拼入FX调用体；仅有规则表而没有生成/捕获对应片段，不等于已经拿到可更新handle。

## Replay先下发，参数更新通过event衔接

CapturedGraphUpdateAndReplay.forward首先调用replay_graph.replay，再取得当前replay stream身份；类级_update_stream优先级为-1，若它与replay stream_id相同则重建，直到二者不同。随后根据本次args构造更新参数；空字典时在已经下发replay之后返回。

存在更新项时，在update stream中先等待本包装器_event_for_update_replay，再逐UpdatedNodeInfo执行：

1. 将update stream设置为该节点捕获时记录的Cube/Vector限核。
2. graph_task_update_begin绑定该节点handle。
3. 浅复制原kwargs，用新列表替换允许更新的kwargs；允许更新的位置参数则原地替换保存args中的对应项。
4. 再调用保存的算子，graph_task_update_end，然后在update stream记录该节点ExternalEvent。

最后在当前replay stream记录_event_for_update_replay，源码注释将其用于后续step更新等待当前step完成。Capture里的ExternalEvent wait/reset与这里record组成协议，因此不能仅看Python先调用replay就断言设备算子必然已经用旧参数运行；也不能据这些event调用证明任意交错、设备/多线程或嵌套执行都安全。所读forward没有显式device synchronize，不等于整个Runtime无任何同步成本。

代码生成遇到局部deterministic_scope_level时警告：task update在Replay不重施该scope level，使用进程全局level；Cube/Vector限核重施与确定性scope是不同机制。不要用捕获期scope标记推导每次更新仍有同样局部确定性，相关公开边界见[限核与确定性](torchair_core_limits_and_determinism.md)。

## 更新列表并非每个key的独立快照

AclGraph构造时创建self._updated_node_infos列表，每次capture前对它clear，再让捕获代码追加本次handle/event。为graph_key创建Replay包装器时传同一列表，包装器构造函数直接保留引用，没有在这里复制列表。

因此从这条静态对象链看，后续capture清空/改写列表可影响先前包装器所引用的更新信息；不能仅凭graphs_meta按key保存Replay对象就断言这些handle/event列表已按key隔离。本卡没有运行跨key复现，也未证明原生库必然出现错误；需要同时核对真实key切换、重捕获、分支捕获和句柄生命周期。

_update_stream也是类级共享对象，而_event_for_update_replay属于各包装器，参数位置项还会修改其保存args。所读方法没有线程互斥或每图私有update stream的同一保证，不把正常单次时序直接推广为并发模型执行合同。

诊断时保存实际改写目标、workspace/out节点、捕获节点名与handle/event、key切换、更新参数、stream及限核/确定性配置，再检查时间线和结果。新的图条目尚无replay_func时另有明确错误提示，见[输入处理失败边界](npugraph_ex_replay_input_buffers_and_copy_paths.md)；本卡没有新增verified或调优收益数字。

## Evidence

- [独立acl_graph捕获与Replay消费者](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)：36–83、734–810、860–954、1045–1054、1505–1513、1543–1548、1630–1633、1709–1721。
- [改写入口与task-group生成体](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)：461–469、1033–1045、1068–1076、1282–1340。只静态读取模板文字，未展开执行。
- [参数包装重建](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/utils.py)：180–212。

## 发布对应更新消费者与捕获诊断失败

对照固定发布7c6c754的CapturedGraphUpdateAndReplay和所列capture区间。发布同样把updated_node_infos直接存引用，捕获前clear同一列表，成功后交Replay包装；forward也先replay、等待包装器Event、在类级更新流按handle改参数并记录Event。因而前文“列表不是每key独立快照”和共享流边界在所列发布对象链也成立；只扩充这些准确消费者，不把主线cond、局部确定性代码生成或完整CANN能力回推发布。

两版capture的debug_dump嵌套函数均在try内取得DebugContext路径、创建目录、生成文件名后才给result_path赋值，调用图debug_dump；except记录异常，但return str(result_path)在try/except之外。若异常发生在赋值之前，静态上可能再出现未绑定局部变量错误；若赋值后dump失败，则仍可能返回没有完整文件的路径。不能概括为“所有dump失败只告警、调用一定继续且有可读JSON”。本次没有创建文件或运行异常分支。

TORCH_COMPILE_DEBUG两版均只认字符串'1'；deadlock_check主线用配置真值，发布要求字符串'1'。满足任一条件就调用上述dump，deadlock开启再把返回路径交run_deadlock_check；这条外部检查没有由本组完整审计。dump和可选检查位于输出metadata记录及replay_func赋值之前，因此此处失败也不能用“设备capture已返回”推成该key已经完成全部Python初始化。主线显式缺Replay函数的错误提示与发布直接调用的区别见[首捕获版本对照](npugraph_ex_restored_capture_keys_and_first_call.md)。

## 有界实现对照

- [固定版本 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（primary）：734–785, 1492–1513, 1543–1548, 1594–1635；只对应本卡增补块，不提升整模块或外部被调实现资格。
- [固定版本 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：522–573, 1134–1177, 1218–1255；只对应本卡增补块，不提升整模块或外部被调实现资格。

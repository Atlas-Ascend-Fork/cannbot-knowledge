---
type: Guide
title: 集成 TorchAir AclGraph：输入复制、重捕获与输出克隆
description: 对照集成主线与发布的字符串配置消费、stream核数重捕获、直接Replay槽和四类输出返回，区分独立npugraph_ex及底层存储合同。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
created_at: '2026-11-11T10:03:04Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成 TorchAir AclGraph：输入复制、重捕获与输出克隆

## 先确定 namespace

本文只讨论 `python/torchair/_acl_concrete_graph/acl_graph.py` 的集成实现：主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`、发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`，不是独立 `npugraph_ex/npugraph_ex/` 下的同名类。后端入口对应关系见[两条实现的路由](torchair_integrated_and_standalone_static_kernel_consumers.md)。相同 mode 名、方法名或局部 AST 不证明两个 namespace 的配置和外部 helper 等价。

只读取下列完整方法与必要 caller/metadata 段，没有把主线 1882 行、发布整模块或外部 C++ allocator 提升为整文件资格。没有导入、生成/执行代码、加载缓存、捕获/回放、拷贝数据或设备测试；产品及完整配套未知，保持 draft、空平台与无新增 verified。

## 内部字符串消费者与公共选项要分开

主线 fx2acl_converter 导入的是本 namespace 的 AclGraph。生成初始化代码时，先创建 compile_configs，再将 normalize_config 的各项生成带引号的字符串赋值，按条件追加 extend_config，最后构造 `AclGraph(fx_forward=forward,config=compile_configs)`。发布所列对象构造也使用同 namespace 的 AclGraph，随后 load 元数据；本卡不展开整个 normalize、公开 options 校验或全部生成协议。

两版已读消费者均有以下条件：

| 内部字段/位置 | 实际条件 |
|---|---|
| __call__ 的 run_eagerly | 等于字符串 `'1'` 才直接 Eager |
| 直接 Eager 路线的 _aclnn_static_shape_kernel | 等于字符串 `'1'` 才先静态编译 |
| compile 首次准备的同名静态开关 | 按取值真值判断，缺省 False，**不是**同一个字符串相等谓词 |
| process_input 的 clone_input | 等于字符串 `'1'`，缺省也是 `'1'` |
| 同 FX 池复用的禁用字段 | disable_mempool_reuse_in_same_fx 存在且等于 `'1'` |
| 输出克隆 | enable_output_clone 存在且等于 `'1'` |

因此直接修改内部字典时，Python True 不等于 `'1'`，非空字符串 `'0'` 又是真值；不能用一个布尔判断概括所有分支。这里描述的是序列化后的实际消费，不是推荐绕过公共配置入口，也不从它反推公共 API 接受任意混合类型。独立主线的布尔键名与比较方式不应直接迁入此字典。

## compile 命中、容量与首次失败状态

两版普通 __call__ 均先 compile，处于 fallback 状态则走 Eager，否则依次 process_input、run、reconstruct_outputs。它们的 call/process_input/run 三个所选方法严格 AST 相同；也实际读取两版文本，不把语法相同扩成外部存储、设备或整个模块等价。

首次 compile 先预热并逐轮 synchronize，可进行静态 kernel 准备，再生成 key/update callable；**_captured 在空 pool capture/checkpoint 之前已经置 True**。这一标志不单独认证具体 key 可重放；后续失败没有在该 compile 的异常处理里自动改回 False。静态编译外部成本与消费者复用[两路径静态编译卡](torchair_integrated_and_standalone_static_kernel_consumers.md)，不重新核其完整编译工具链。

已有 key 先检查 is_need_to_recapture；无需重捕获就立即返回，尚未到容量检查。其余路径才用 `len(_graphs_meta) == int(static_capture_size_limit)` 判断；是等于而非大于等于，也不先要求 key 必须全新。所以旧 key 需要重捕获时仍可能触发同一限制。触发后本层设置 _fallback_to_eager、调用 reset 并返回 fallback 标识；完整 reset/allocator 恢复仍独立，不把这个调用名理解为所有实例状态恢复构造默认。

确需重捕获时先保留旧 graph 引用，正常完成 compile_for_graph_key 后才 reset 旧 graph。这不是整个捕获/计数/内存状态的统一事务或所有失败都会自动重试的保证；key、_captured、内存 checkpoint 与最终可执行性需要分别观察。

## 重捕获差异：主线集成也不是独立主线的优先序

| 局部方法 | 集成主线 | 集成发布 |
|---|---|---|
| mutated 输入地址 | 遍历 captured_mutated_inputs，比对本次 data_ptr；改变则 True 并记相应计数 | 同样比地址返回 True；计数在 compile 调用处更新 |
| 当前 stream 的 Cube/Vector 数 | 读取当前 stream 限核，与 graph metadata 中保存值比较，改变则 True | 所读方法没有这一段 |
| 独立主线卡所述 unsafe 跳过/强制重捕获优先分支 | 这里没有同样的分支 | 这里也没有同样的分支 |

主线集成在实际 capture 调用前执行 _save_stream_core_limits：从当时 current_stream 读取并保存 Cube/Vector，Exception 时记录警告并把两值设 None；运行时 is_need_to_recapture 的查询没有同样的局部 catch。字段名字带 captured，不应直接推导完整捕获流/回放流身份已检查或任意跨流执行安全。

这两个方法都没有直接遍历 captured_parameter 作额外参数地址校验；参数 key、其他上层机制及整个模型输入合同仍要另核。这里不从局部缺少分支推导任何上层都无法强制重新建图。独立主线的优先序继续按[其自身捕获键卡](npugraph_ex_restored_capture_keys_and_first_call.md)解释。

## 输入复制不是每次重新 clone

两版集成的 clone_input 字符串路线直接使用 userinputs_metatensor，逐项无条件排入 copy 列表；否则使用 retained_userinputs，只在 metadata.data_ptr 与本次 Tensor.data_ptr 不同时排 copy。随后对同一字典 update 输入引用输出项，并另按实例保存的 alias 地址比较；它没有先复制出一份完全独立的输入字典，后续 copy 项数量可能受先前 update 影响。

主线集成 get_tensor_metadata 明确向 TensorMetadata 的 data_ptr 传 Storage 基址，同时另存 storage_offset、shape/stride、nbytes 等；不能把这个基址与 Tensor 的逻辑起始地址无条件混为一个值。这里未展开发布 metadata producer 或任意外部裸地址重建，地址比较也不是完整 shape/dtype/stride 合法性验证。

copy 项多于一项时，首次将源/目标 base-format 判定缓存到 self._input_base_format；真值走 `_foreach_copy_(non_blocking=True)`，否则逐项 copy_。一项只调用普通 copy_，零项没有这段数据 copy。这段代码不按 key 建格式缓存表，也不逐次重新检测；non_blocking 名称不能替代真实设备时间线。共通存储/别名问题的诊断方法可参考[独立路径输入卡](npugraph_ex_replay_input_buffers_and_copy_paths.md)，适用性仍以本节实际集成字段为准。

## 输出克隆的主线覆盖扩展到早退路线

| reconstruct_outputs 返回位置 | 集成主线 | 集成发布 |
|---|---|---|
| 明确禁用同 FX 池复用 | retained_outputs 再过 clone helper | 直接返回 retained_outputs |
| 只有一个 key | retained_outputs 再过 clone helper | 直接返回 retained_outputs |
| 可根据存活引用取得输出 | 结果再过 clone helper | 直接返回结果 |
| 必须按 metadata 完整重建 | 重建后过同一 clone helper；未开克隆才关联 deleter/告警 | 仅此路线才检查 enable_output_clone；否则关联 deleter/告警 |

主线 helper 对每个 Tensor 分别 clone，但排除 Storage._cdata 已在输入引用输出集合中的项；其他对象原样返回，没有按共享 Storage 去重。发布完整重建路线也有这项排除。开关为 `'1'` 因而不代表所有返回值都是独立快照，克隆后的多视图别名也不能直接假定与原来一致。

发布的前三个早退根本不到克隆分支，不能只读配置日志就认定已经承担了快照复制的成本；主线增加了对应 helper 调用，但仍有上述排除。完整底层 deleter、checkpoint 和 allocator 算法未重审；[独立输出卡](npugraph_ex_output_reconstruction_and_storage_lifetime.md)的低层说明不能仅凭类名跨 namespace 自动套用。

## run 的诊断边界与验收

两版集成 run 都直接调用该 key 的 replay_func，没有独立主线新增的“前次 capture 失败、replay_func 为 None”专门检查。存在 key 或已设置 _captured 不能单独证明该槽可用；同时也不能把其它前置输入/输出错误都归因于这个诊断差异。

对照版本时记录实际导入路径、序列化字典、首次准备状态、key/重捕获理由、stream 限核、copy 项与格式缓存、真实输出返回路线和 clone 项，再检查结果、别名和内存/时间线。本卡不提供零拷贝、任意跨流安全、性能收益或产品支持的运行认证。

## Evidence

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py)（primary）：16–37、924–946、1030–1152、1194–1205、1288–1299、1471–1566、1575–1675；仅此集成命名空间完整局部方法/必要调用，未提升整个模块或外部被调实现资格。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：15–30、822–844、928–1021、1250–1333、1343–1419；仅此集成命名空间完整局部方法/必要调用，未提升整个模块或外部被调实现资格。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/utils.py)（implementation）：63–82、107–136；仅此集成命名空间完整局部方法/必要调用，未提升整个模块或外部被调实现资格。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：18–26、558–578；仅此集成命名空间完整局部方法/必要调用，未提升整个模块或外部被调实现资格。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：18–26、335–341；仅此集成命名空间完整局部方法/必要调用，未提升整个模块或外部被调实现资格。

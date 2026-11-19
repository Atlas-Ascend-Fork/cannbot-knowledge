---
type: Guide
title: 独立npugraph_ex缓存恢复：捕获键与首次运行成本
description: 解释持久代码恢复后的进程内捕获实例、参数地址键、首次同步预热，以及容量已满时旧key重捕获也可能触发Eager回退。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py
  role: implementation
created_at: '2026-11-10T12:00:58Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 独立npugraph_ex缓存恢复：捕获键与首次运行成本

## 固定范围与两层缓存

本卡只定向核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c中独立npugraph_ex包的AclGraph及生成代码入口。它不是python/torchair路径下的同名legacy类，也不把主线布尔选项、捕获限制和重捕获检查直接用于发布实现。

持久编译工件与当前进程的NPUGraph实例是两层状态。公共缓存接口见[npugraph_ex cache_compile](../../../apis/torchair/npugraph_ex_cache_compile.md)，本卡补充恢复后真实运行路径；未读取真实缓存、执行生成代码、捕获NPU图、做精度或性能实验。整卡平台未知，保持draft与空平台。

## 恢复代码仍创建新AclGraph

fx2acl_converter的生成初始化代码新建AclGraph(fx_forward=forward,config=compile_configs,...)，再构造AclGraphCacheInfo并load。构造器初始化_graphs_meta为空、_captured=False；load填入更新规则、输入映射、参数输入、pool/stream等元数据，没有从这段代码恢复已捕获设备图的字典。

因此持久缓存命中不等于已经拿到跨进程可直接replay的设备实例。首次普通调用仍进入compile，按num_warmup_iters执行FX Eager并每轮torch.npu.synchronize；启用static_kernel_compile时还调用静态kernel准备。之后建立输入key/update函数，执行一次空NPUGraph capture以初始化pool并保存checkpoint，再进入当前key的真正捕获。

_captured在空capture与具体key捕获之前已经置True，表示该条一次性准备分支不再进入，不能独立证明当前shape捕获成功。首调延迟应拆分持久代码恢复、预热/同步、静态kernel准备、pool初始化和实际capture，不只看loaded日志。

## 捕获key只包含指定输入的一部分信息

gen_unupdate_input_func使用编译阶段给定的unupdated输入索引：没有这类输入时返回固定字符串no_updated_input；全为符号时使用对应参数值列表的字符串；混合Tensor时对Tensor项只取shape，对符号项取值，再转为字符串。

该局部key没有把全部Tensor内容、stride、dtype、device或模型源码做完整摘要。只有该索引列表指定的项进入这部分key，不能假定动态更新所用的全部符号也都已纳入；同key并不是全部输入语义均已验证的证据，需要维持外部图、输入和更新规则合同。

未启用frozen_parameter且存在parameter_user_inputs时，get_unupdated_input_fn还在key后追加这些参数data_ptr元组的hash；启用冻结或没有参数项时不加这个地址部分。启用frozen_parameter可以跳过该参数地址key处理，但不证明换权重对象或存储仍可无条件复用；地址hash也不是权重内容或跨进程稳定身份。

## 命中key之后仍可能重捕获

key已在_graphs_meta中时，compile先调用is_need_to_recapture，通过检查才直接返回该key。固定主线的检查优先级为unsafe_skip直接False，其次force_recapture为True，再检查mutated输入地址和当前流Cube/Vector控核数。公开开关前提继续按[捕获控制](npugraph_ex_capture_controls.md)核对，本卡不把unsafe跳过当作默认优化。

每次调用随后仍process_input、调用该key的replay_func、重建输出；key命中不自动省去这些阶段。参数地址key、mutated地址重捕获和动态算子参数更新是不同机制，不能用“shape相同”把它们合并。

## capture_limit检查也位于旧key重捕获路径

只有已命中且无需重捕获的key会在前面立即返回。其余路径在compile_for_graph_key之前统一检查len(_graphs_meta)==capture_limit；达到限制便设置_fallback_to_eager、reset_captured_graph，后续调用先走固定Eager回退，不再计算key。

这个检查没有先限定key必须是新的。因此字典已满时，已有key若因地址、控核或force要求重捕获，也会到同一回退检查；不能把容量预算理解为一个完全独立于重捕获条件的“只限制新shape”开关。len统计的是当前key字典数量，不是所有capture事件的累计次数。本节是固定主线控制流补充，未做边界设备实验。

compile_for_graph_key先写入含新NPUGraph且replay_func=None的GraphMeta并更新captured计数，再执行实际capture、保存其后的pool状态。因此字典或计数出现一项，不足以认证对应capture成功；本卡未展开capture内部的全部异常处理，不承诺失败后状态完整或会自动重试。失败后检查原异常、实例状态和实际回退路径，不能只凭计数继续承诺安全replay。

调优时区分持久缓存命中、进程内key命中、是否重捕获及是否已永久回退，分别记录参数地址、未更新符号值、mutated输入、当前控核和捕获前后内存。公共输入输出存储合同仍见[内存池与clone](npugraph_ex_memory_pool_and_clone.md)；本卡没有收益数值或新增verified。

## Evidence

- [独立AclGraph](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（primary）：250–299、1010–1094、1149–1301、1357–1399、1438–1465、1723–1750；只覆盖所选状态和key调用链。
- [生成与恢复入口](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/fx2acl_converter.py)（implementation）：196–255、740–785。

## 发布内部选项名与首次状态对照

仅对照固定发布7c6c754的compile/reset/run/重捕获函数，不扩大到整份1597行模块或整个发布软件栈。发布compile按_aclnn_static_shape_kernel读取静态编译开关，并另传build_dir、use_cache_compile、cached_cann_version、compile_cache_dir、cached_deterministic及_super_kernel_optimize；主线此路径则按static_kernel_compile传config；预热使用ControlFlowOpWarmupCtx，静态编译经self._static_kernel_dump_ctx()，此处不展开该上下文内部。不能把主线配置字典的名字直接换入发布内部对象，相关配置入口仍需配套来源。

发布池复用按disable_mempool_reuse_in_same_fx是否严格等于字符串'1'决定，主线这里仅在reuse_graph_pool_in_same_fx键存在且值为真时启用对应复用；发布捕获容量字段为static_capture_size_limit，主线为capture_limit。两版均用len(graphs_meta)==limit、在旧key需重捕获时也可到同一容量判断，并在回退后不再计算key。这里是内部键名和局部默认分支，不替代公开配置序列化或产品范围。

两版_captured都先于空pool捕获/checkpoint设置True，失败并没有在compile内把它恢复False。reset_captured_graph会同步、reset已存图、清字典/部分计数、GC和empty_cache，但不在函数体清除_fallback_to_eager或_captured；它不是把实例所有配置、输入别名与准备状态重建为构造默认。

发布is_need_to_recapture仅比对captured_mutated_inputs的data_ptr；所列函数没有主线unsafe_skip、force_recapture或当前流控核分支。两版该函数也没有直接循环校验captured_parameter，尽管相邻注释提到参数地址；参数地址key仍按前文frozen_parameter的独立机制处理，不应从注释补出额外运行检查。

主线run遇replay_func=None会给出前次capture失败的专门RuntimeError；发布run直接调用该槽，没有这条本地诊断。字典项先插入、后续准备异常和两版不同错误出口，应与原始异常一起保存，不能拿已出现key、计数或已设置_captured独立认证捕获可用。上述都是静态局部差异，没有执行故障复现、重捕获或设备测试。

## 有界实现对照

- [固定版本 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（primary）：1191–1301, 1317–1342, 1709–1750；只对应本卡增补块，不提升整模块或外部被调实现资格。
- [固定版本 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_acl_concrete_graph/acl_graph.py)（implementation）：924–1018, 1034–1049, 1330–1341；只对应本卡增补块，不提升整模块或外部被调实现资格。

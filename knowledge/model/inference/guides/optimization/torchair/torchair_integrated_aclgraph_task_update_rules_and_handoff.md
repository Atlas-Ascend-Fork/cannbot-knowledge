---
type: Guide
title: 集成 TorchAir AclGraph：任务更新规则与捕获交接边界
description: 核对集成两版任务更新表、字典与None分析失败分支、当前图规则及生成到Replay的实际交接，限定独立包机制的复用范围。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py
  role: implementation
created_at: '2026-11-11T10:15:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 集成 TorchAir AclGraph：任务更新规则与捕获交接边界

本卡只描述固定主线 `92e1e967`、固定发布 `7c6c754b` 的 `python/torchair/_acl_concrete_graph` 集成路径。两版所列本地规则、生成文本及捕获交接已静态对照；没有生成或执行 FX 代码，没有捕获、Replay、设备或并发复现。相同函数体不代表不同命名空间的 globals、配置或底层运行时自动等价。

输入复制、重捕获与输出克隆的版本差异见[集成 AclGraph 运行消费者](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)。[独立包规则与图 key](npugraph_ex_task_update_rules_and_graph_keys.md)及[独立包任务更新时序](npugraph_ex_task_update_capture_and_streams.md)解释另一条路径的机制，本卡补充集成路径的实际接线与失败边界，不把独立主线的条件分支支持直接套入集成路径。

## 可更新目标由本地注册表限定

两版 `_REPLACE_FUNC_MAP` 在模块初始化时按 `hasattr(torch.ops.…, name)` 条件建立下表。FIA 的普通重载关联最大 workspace 查询和 out 重载；ATB 关联其原重载，不在该表声明 workspace/output 槽。表中准入不等于已经运行验证对应算子、产品或所有配套符号均可用。

| 目标 | 允许更新的参数 | 本地额外门槛 |
| --- | --- | --- |
| `npu_fused_infer_attention_score` | 关键字 `actual_seq_lengths`、`actual_seq_lengths_kv`、`actual_shared_prefix_len` | 检测普通算子名；表中直接引用 max-workspace/out 符号 |
| `npu_fused_infer_attention_score_v2` | 关键字 `actual_seq_qlen`、`actual_seq_kvlen` | 同上 |
| `atb._npu_paged_attention` | 位置参数 7 `context_lens` | 算子签名中的参数序号与预置映射一致，否则警告而不加入 |
| `atb._npu_paged_attention_splitfuse` | 位置参数 4 `context_lens`、6 `seq_len` | 同上 |

签名检查取 `get_signature_for_torch_op` 返回的非空列表首项，遍历其参数顺序并核对所有预置名称；这里没有补齐其他返回形态的统一容错。注册表也不是任意动态参数都可原地更新的证明。转换器先调用本命名空间的 `replace_dynamic_workspace_ops`，之后从转换后的同一 FX 图计算保留在 key 中的输入以及可更新规则；workspace/out 改写主体和外部算子执行合同不由本卡重新提升资格。

## 依赖分析的两个实际失败分支

`get_node_all_placeholder_inputs` 从没有被排除的位置参数、关键字参数开始，展开 list/tuple；遇到 FX Node 只记录其中的 placeholder，非 placeholder 节点不会在这里递归展开其生产者。它不是任意 FX 数据流和 Python 容器的通用依赖求解器。

两固定版本都存在下面两条局部分支：

- 遇到 dict 时调用 `cur_input.valus()`，而非 `values()`。普通内建 dict 没有该属性，因此这种对象实际进入该分支存在 `AttributeError` 路径。自定义子类是否另有同名属性不能由普通 dict 的结论代替；也不是所有包含字典的图都会必然到达这条分支。
- 常量检查使用 `isinstance(cur_input, (int, float, bool, str, None))`，把 `None` 值放进本应由类型组成的 tuple。对象已匹配前面的类型时可先结束检查；例如 `None` 这类未匹配前四项的对象继续到无效项时存在 `TypeError` 路径，不能概括为“None 被当作常量安全跳过”。后面的自定义 `RuntimeError` 也不能视为所有未知类型的统一报错。

这些结论来自固定源码和分支条件，没有执行异常复现。直接调用它的 `get_unupdated_sym_input_index` 在所读函数内没有捕获这两类异常，不应承诺出错后自动保守纳入 key 或自动回退 Eager。

## 当前图的规则不等于条件子图映射

两版 `get_updated_ops_rulers_param` 只扫描传入 `graph_module.graph.nodes`，首先要求当前图 placeholder 数与 `meta_inputs` 数一致。它用本地注册表的 out/ATB 目标筛选节点，再由 `get_update_ruler` 构造规则：关键字更新值必须是 list/tuple，元素为当前图直接 placeholder 或 int/float/bool 常量；只有包含 placeholder 才加入更新规则。允许更新的位置槽也必须直接引用当前图 placeholder，其他表达式不会在这里化为通用运行期公式。

结果以当前 `node.name` 保存，另生成关键字名称列表和 `arg_index_<node.name>` 位置列表。运行闭包按位置读取本次 `args`，同规则签名通过 `str(rulers)` 分组并复用解析结果；它不以 `kwargs` 重建任意调用形式。相关算法概念可参照[独立包规则](npugraph_ex_task_update_rules_and_graph_keys.md)，但本段依据是集成版本的实际函数与本地注册表。

所列集成收集器没有独立主线收集器的 branch-placeholder 到 root-input 重映射参数和节点名前缀；`get_unupdated_sym_input_index` 也没有该独立主线的 cond-operand 特殊判断。因而不能仅凭同名函数或新版独立包文档，断言这里已经完成条件分支的更新规则重映射。这只限定本地收集器与其所读调用，不是整个 TorchAir 或发布版不能执行任何条件图的产品结论。

`get_unupdated_input_fn` 的 `frozen_parameter` 开启条件是内部字典的字符串 `'1'`；否则存在参数输入时，key 追加参数 `data_ptr()` 元组的 hash。基础 key 生成器在空待区分索引时返回固定字符串，其他索引按标量值或 Tensor shape 构造基础 key；外层仍可能追加前述参数地址 hash。内部字符串字典的生成背景及其与其他开关真值判断的区别见[集成运行消费者](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)，不要把这个局部比较扩大为公共 API 接受任意配置类型的合同。

## 规则必须接到实际生成、捕获和 Replay

两版转换器把规则写入 `AclGraphCacheInfo`，把 `updated_ops_param` 交给 `_codegen_fx_forward`，创建集成 `AclGraph` 并调用 `load`。`load` 将规则、未更新输入索引和参数输入位置写入实例；首次 compile 再把它们包装为 key 闭包和更新参数闭包。这条接线针对集成模块实际发生，不由独立包中相同函数名推导。

`_codegen_fx_forward_updated_ops` 只处理 `call_function` 且名称命中规则的节点，生成捕获分支中的 ExternalEvent wait/reset、task-group begin/end，以及 `UpdatedNodeInfo` 构造文本。生成的 import 明确指向 `torchair._acl_concrete_graph`；普通调用与捕获调用共用算子调用文本。外层按 `'<node.name> = torch.ops.<target>'` 是否为 FX 代码行的子串来替换，并保留该行分号后的释放语句。静态规则表不等于生成文本已成功匹配、执行并获得 handle；本组没有执行这些字符串，也没有展开重建工具或原生 task-group 实现。

两版实际 capture 都对实例的 `_updated_node_infos` 列表先 `clear()`，再把同一列表以 `node_info=…`、`is_capturing=True` 交生成 forward，最后把该列表原样交给 `CapturedGraphUpdateAndReplay`。包装器构造函数保存引用，未复制成每个 graph key 的私有快照；后一次 capture 的清空/追加因而可能改变旧包装器看到的列表。这是所读本地对象链的静态结果，没有声称已经复现原生句柄错误。

两版集成 Replay 本体先下发 graph replay，随后计算本次更新参数；更新字典为空时，在已调用 replay 后返回。非空时使用类级 `_update_stream` 和包装器自己的完成 Event，依节点记录的限核与 handle 重发允许更新的参数，再记录节点 ExternalEvent。它保留了共享更新流、原地修改保存位置参数列表以及各包装器持有自身 Event 的边界；没有在所读方法里建立每图私有流或线程互斥。详细事件协议可参照[任务更新时序](npugraph_ex_task_update_capture_and_streams.md)，本卡已经核对集成命名空间的实际调用，仍不据 Python 调用顺序断言设备一定读取旧参数，或承诺任意并发交错均安全。

诊断时优先记录实际命名空间、固定提交、命中的注册项、待更新参数位置、生成文本是否匹配、graph key 切换及更新列表/handle/event 的对象关系。对 dict/None 或间接表达式问题先核规则分析阶段；对跨 key 问题再核列表交接，避免将两类问题混成设备性能结论。本卡没有新增 verified、支持矩阵或收益数字。

## Evidence

- [固定集成实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/acl_graph.py)（primary）：16–28、90–552、600–651、904–904、1001–1008、1055–1064、1351–1357、1387–1389、1463–1468；仅列明规则、生成文本与必要交接，不提升整个模块、数据类/重建工具或外部运行时资格。
- [固定集成实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/acl_graph.py)（implementation）：15–26、81–485、526–577、804–804、900–907、948–950、1148–1153、1179–1180、1242–1247；仅列明规则、生成文本与必要交接，不提升整个模块、数据类/重建工具或外部运行时资格。
- [固定集成实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：311–314、336–344、363–372、691–834；仅列明规则、生成文本与必要交接，不提升整个模块、数据类/重建工具或外部运行时资格。
- [固定集成实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_acl_concrete_graph/fx2acl_converter.py)（implementation）：290–292、312–319、335–341、641–772；仅列明规则、生成文本与必要交接，不提升整个模块、数据类/重建工具或外部运行时资格。

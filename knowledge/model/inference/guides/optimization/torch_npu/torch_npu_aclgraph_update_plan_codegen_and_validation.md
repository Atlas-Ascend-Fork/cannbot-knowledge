---
type: Guide
title: ACLGraph update plan：Inductor 侧计划生成、replay 前校验与内置可更新算子面
description: 记录主线独有的 ACLGraph 更新计划生产门、schema 绑定与来源类型语义、校验错误矩阵、内置 handler 的可更新参数槽位，以及图树捕获/重放的消费接线。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_aclgraph_update_plan/resolver.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_aclgraph_update_plan/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/_aclgraph_update_plan/codegen.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/_aclgraph_update_plan/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/wrapper.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/ascend_npu_ir/ascend_npu_ir/npu/codegen/wrapper.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/npugraph_handler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/ifa_handler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/simple_handler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/_fa3_graph_handler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/npu/test_aclgraph_update_plan.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/npu/test_graph_tree.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_npugraph_handlers/npugraph_handler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_npugraph_handlers/ifa_handler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_npugraph_handlers/simple_handler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_npugraph_handlers/__init__.py
  role: implementation
created_at: '2026-11-12T05:41:05Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# ACLGraph update plan：Inductor 侧计划生成、replay 前校验与内置可更新算子面

## 固定版本与适用范围

计划模块是主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`独有：`torch_npu/npu/_aclgraph_update_plan/`与`torch_npu/_inductor/_aclgraph_update_plan/`在发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的Git树中无条目（本次以两 pin 的`find torch_npu -name '*.py'`全列表 diff 核对，非只查目录名）。handler 注册面两版都在，但发布版IFA handler 仅声明 KV 长度更新、且没有 FA3 handler（下文表）。本卡只做静态阅读：未导入 torch_npu、未编译模型、未捕获或重放任何图。draft、platforms 为空，不宣称运行验证。replay 侧与捕获树的生命周期已由[Inductor AscendC 图下沉](../torchair/torchair_inductor_ascendc_graph_tree.md)覆盖，本卡聚焦它未覆盖的生产与校验层；handler 注册协议与默认 `update_args` 见[NpuGraphOpHandler](../../../apis/torch_npu/npugraph_op_handler.md)，不重复。

## 计划是什么、挂在哪里

`torch_npu.npu._aclgraph_update_plan.resolver` 定义全局属性名`ACLGRAPH_UPDATE_PLAN_GLOBAL = "_torch_npu_aclgraph_update_plan"`。Inductor Python wrapper 代码生成时，对每个命中 handler 的外部/回退 kernel 记录一条`{"op": <名>, "updates": {<键>: <来源>}}`，最终在 wrapper 生成代码末尾写`<launcher_fn_name>._torch_npu_aclgraph_update_plan = [...]`。图树 `NPUGraphNode.__init__` 用`getattr(wrapped_function.model, "_torch_npu_aclgraph_update_plan", None) or []`取走计划；replay 前用它把新输入解析成 CPU 侧更新值并提交给已捕获图，属于“免重捕改参数”通道，不是重新捕获拓扑。

## 生成门与接入点

| 门 | 实际检查 |
| --- | --- |
| 三重开关 | `should_generate_inductor_aclgraph_update_plan`：`config.triton.cudagraphs`且`config.triton.cudagraph_trees`同时开，且`V.graph.disable_cudagraphs_reason`为 None；任一不满足则整条 wrapper 不生成计划 |
| 接入点 | 默认 codegen 在`generate_fallback_kernel`与`generate_extern_kernel_alloc`逐节点 append，`generate_after_suffix`一次性 emit；`ascend_npu_ir`（mlir）codegen 同样两个 append 点，根 wrapper emit 时`is_graph_partition_subgraph=False`、子图 codegen 传 True |
| graph_partition | `config.graph_partition`开启时默认 codegen 只在子图 wrapper 上 emit（根不 emit）；mlir 侧由各自的常量参数固定 |
| 算子资格 | 查`_NPU_GRAPH_OP_HANDLERS`注册表（导入`_npugraph_handlers`包触发内置注册）；无 handler 的算子不产生条目；handler 有`should_handle`时先问询（FA3：`input_layout == "BNSD"`返回 False，整条不建记录） |

`_fa3_graph_handler.py`在模块导入时求`_CANN_VERSION = _is_gte_cann_version("9.1.0")`，`should_handle`在其为 False 时直接返回 False：这是导入期一次性判定，不随运行期 CANN 升降变化。FA3 的 BNSD 排除在 codegen 侧被镜像：`_matches_aclgraph_update_exclusion`对`npu_fusion_attention_v3(_grad_v3)`且绑定参数`input_layout == "BNSD"`返回 True，跳过条目。

## schema 绑定与来源类型

`_bind_by_schema`按`op_overload._schema.arguments`把位置实参对到参数名，剩余名从 kwargs 取；`UPDATE_SPECS`里声明的键才进`updates`，全部未命中则该条目为 None（丢弃）。来源由`_inductor_value_to_source`决定：

| kind | 语义与门槛 |
| --- | --- |
| input | 值能对应到图输入：先试`get_name()`（以及`data`/`unwrap_view`间接取名）匹配输入名，否则按对象同一性，再否则把`SymInt/SymFloat/SymBool`的`node.expr`与各输入做`sympy.simplify(lhs-rhs)==0`等价比较；解析出索引`{"kind":"input","index":i}` |
| list | list/tuple 逐元素递归 |
| constant | 生产侧仅 None/int/float/bool/str 标量（None 也用独立 kind "none" 表达），list/tuple 走独立"list"kind 逐元素递归；其他类型报`Unsupported ACLGraph update source`。校验侧 constant 的域更宽（见下节），不要把生产侧的标量域当成校验侧上限 |
| none | 显式空值 |

Tensor 值不允许作为常量：`_literal_to_source`对`torch.Tensor`直接报`Tensor update values must be graph inputs`——想要按输入更新的长度张量必须被 Inductor 提升为图输入，否则编译期失败。测试`test_build_inductor_plan_rejects_unlifted_tensor_actual_seq_constant`以裸`torch.tensor([15])`复现该拒绝。

## 校验与解析（replay 前的确定性失败面）

`validate_aclgraph_update_plan(plan, graph_dispatch_records)`按序检查，任一失败抛 RuntimeError（均带 pta_error(ErrCode.PARAM)）：

| 检查 | 失败文本要点 |
| --- | --- |
| 有可更新记录却无计划 | `Captured updatable ACLGraph operators but missing ACLGraph update plan: <ops>`，并提示两种成因：复用 ACLGraph 关闭时生成的缓存代码、或使用 npugraphs backend（其尚不支持计划） |
| 计划长度 | `plan has N entries but graph captured M updatable records` |
| 条目形状 | 非 dict、op 非字符串、`updates`非 dict 或为空 |
| 算子名 | 与记录的`op_cache_entry.__name__`比对，`.default`/`.out`后缀归一化后仍须一致 |
| 可消费键 | 记录的 kwargs 键 ∪ handler `UPDATE_SPECS` 键之外的未知键报`key(s) that captured op cannot consume`；来源再经`_validate_source`递归检查（input 索引非负整数、constant 经`_validate_literal_constant`：Tensor 拒绝、None/int/float/bool/str 放行、list/tuple 逐元素递归放行、其余类型拒绝——比生产侧的标量 constant 域宽；另 list items 必须 list、未知 kind 拒绝） |

`resolve_aclgraph_update_plan`把每条`updates`解析为实际值：`input`按索引取`new_inputs`（越界报`out of range`）、`constant`取值、`none`为 None、`list`递归。`build_cpu_update_input_for_graph` = 先 validate 后 resolve；测试用 mock 记录覆盖了以上每条错误文本与 `.default`/`.out` 兼容名、list 内嵌不支持常量类型（`object()`）的拒绝——嵌套 list/tuple 字面量本身可递归通过校验——等矩阵（`test/npu/test_aclgraph_update_plan.py`，609 行，用假 schema/handler 纯单测，不含设备）。

## 图树消费点（两处）

- 捕获（`_record`）：进入捕获前先`resolve_aclgraph_update_plan(plan, inputs)`得到`aclgraph_cpu_update_input`；以`auto_dispatch_capture=True`捕获后依次`validate_aclgraph_update_plan_for_graph`（仅`graph.auto_dispatch_capture`为真时校验）与`update_aclgraph_records_for_graph`（提交后返回 True）。kernel-free 分支不建图也不 resolve（测试以 mock 验证 resolve 未被调用）。
- 重放（`Node.run`）：`kernel_free_cudagraph`为真直接跳过更新；否则 resolve + `graph.update(...)`，提交成功后先`run_graph()`再让`graph.graph_dispatch_mode.update_stream.wait_stream(current_stream)`——源码注释解释这是避免下一次更新在本次重放复位可复用外部事件前录制它们。重放时序与输出重建的完整合同见[图下沉卡](../torchair/torchair_inductor_ascendc_graph_tree.md)，本卡不重复展开。

`update_aclgraph_records_for_graph`对`graph is None`、`auto_dispatch_capture`为假或`cpu_update_input`为空都返回 False（不提交），不是错误。

## 内置可更新算子面（主线 vs 发布）

| 算子（注册名） | 更新键 → 槽位 | 版本 |
| --- | --- | --- |
| `npu_fused_infer_attention_score(.default/.out)` | 主线：`actual_seq_lengths`→arg5、`actual_seq_lengths_kv`→arg6；发布：仅`actual_seq_lengths_kv`→arg6 | 两版都在，键面不同 |
| `npu_fused_infer_attention_score_v2(.default/.out)` | 主线：`actual_seq_qlen`→arg7、`actual_seq_kvlen`→arg8；发布：仅`actual_seq_kvlen`→arg8 | 两版都在，键面不同 |
| `_npu_paged_attention.default` | `context_lens`→arg7 | 两版一致 |
| `npu_multi_head_latent_attention.out` | `context_lens`→arg5 | 两版一致 |
| `npu_fusion_attention_v3(.default/.out)` | `actual_seq_qlen`→arg14、`actual_seq_kvlen`→arg15 | 仅主线（发布无 FA3 handler 文件） |
| `npu_fusion_attention_grad_v3(.default/.out)` | `actual_seq_qlen`→arg21、`actual_seq_kvlen`→arg22 | 仅主线 |

发布版的 IFA/PA/MLA handler 仍可用（用各自手写`update_args`/`_OP_ARG_SPECS`），配合 `g.update` 直通道（见 handler API 卡）；但发布没有 Inductor 计划生产层，也没有 FA3 条目，不能把主线“编译期自动生成计划”的覆盖面回推发布。`.default` 调用在 handler `prepare_capture` 里被换成 `.out` 重载并预分配 workspace/输出（IFA 用 `_get_max_workspace`/`_infer_output` 辅助、FA3 换算后 TND+`keep_prob<1` 直接报错并提示走 graph partition 回退），该捕获侧行为与函数替换一致性合同已在 handler API 卡中，不再展开。

## 边界

- 发布快照无计划模块：上文所有生成/校验/消费行为仅绑定主线；不据此宣称发布栈完全没有“replay 前改参”能力（直连 `g.update` 通道在发布可用），也不宣称 npugraphs backend 未来一定补上计划支持。
- 校验/解析/生成全部为静态审阅结论；测试文件本身未运行。FA3/IFA 实际捕获、更新与数值一致性未验证，`should_handle` 的 CANN 版本判定是导入期事实，运行期升级不会自动重判。
- `test_graph_tree.py` 相关两测（968 行起）用 mock 断言 kernel-free 记录/重放跳过更新，属单测证据，不证明任意真实图的更新正确性。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_aclgraph_update_plan/resolver.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/_aclgraph_update_plan/codegen.py)（primary）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/npu/test_aclgraph_update_plan.py)（example）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_npugraph_handlers/_fa3_graph_handler.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_npugraph_handlers/ifa_handler.py)（implementation）

---
type: API
title: register_replacement：两后端 Pattern 替换与匹配校验
description: 记录融合注册参数、标量绑定、重复模式版本门槛和后端开关，链接模型侧布局规则。
tags:
- task.lookup
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/register_replacement-0.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/api/npugraph_ex/register_replacement.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/pattern_fusion_pass.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/register_replacement-0.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/npugraph_ex/register_replacement.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_pass_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/graph_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/graph_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/npugraph_ex/register_replacement.md
  role: constraint
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# register_replacement：两后端 Pattern 替换与匹配校验

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。本卡选取来源支持的 A2/A3 推理范围，其他产品和特殊参数另行核对。

## 入口与语义

GE 使用 torchair.register_replacement，npugraph_ex 使用 torch.npu.npugraph_ex.register_replacement。共同参数为 search_fn、replace_fn、example_inputs，以及 trace_fn=fwd_only、extra_check、search_fn_pattern、scalar_workaround、skip_duplicates=False；均无返回值。

example_inputs 用于追踪模式；extra_check 接收 torch._inductor.pattern_matcher.Match，可按 shape、设备、流等拒绝不合法候选。显式 search_fn_pattern 后不再用 search_fn 作为匹配规则；scalar_workaround 绑定追踪时固化的标量。skip_duplicates 仅 PyTorch≥2.7 生效，True 跳过重复注册、False 报错。

## 开关与边界

GE 为 config.experimental_config.pattern_fusion_pass，要求 PyTorch≥2.6；npugraph_ex 为 options.pattern_fusion_pass，默认开启。接口存在不证明融合算子在对应硬件、dtype 和 shape 上可用，仍需其 Eager/Meta/Converter 或捕获适配。

默认 trace_fn 只追踪前向，不从“可传反向追踪函数”推定完整训练支持。被消除的中间输出若仍被其他节点引用会影响匹配，替换必须保留数值、输出结构、别名和 mutation。来源说明 GE max-autotune 不支持某些 npugraph_ex 融合规则，不能按同名开关共用完整规则集。

- [Pass 的执行层次](../../guides/optimization/torchair/torchair_fx_pass_and_fusion_controls.md)
- [模型侧 shape、scale 与跨流检查](../../optimizations/rules/graph_fusion_register_replacement_guardrails.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线流检查与注册生命周期

TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 保留两入口和参数契约；主线总览列A2/A3/950推理。具体融合算子的产品、dtype与模式仍按独立算子卡，不由框架入口支持范围推导。

主线pattern_pass_manager在调用用户extra_check前，先检查match中call_function节点的stream_label：多个非默认label、或默认与非默认混合会被拒绝，之后才运行用户校验。extra_check返回True不能绕过这个框架检查；缺失label按默认流处理，静态元数据也不是设备时序已经验证的证明。

该实现使用进程内懒初始化的全局Pattern管理器，注册不是每次模型调用的运行节点。反复导入/初始化规则时需考虑重复模式；skip_duplicates的PyTorch版本门槛依然适用，不把修改用户extra_check等同于清除已有注册。默认fwd_only、示例FakeTensor及可传反向trace_fn都不提升npugraph_ex总览的推理/反向捕获范围。

示例替换同时保留归一化结果和残差xOut，extra_check还检查真实匹配的shape；示例张量尺寸只是追踪种子，不能用小形状注册成功代替实际图匹配、输出结构和alias验收。

## 同名独立包入口的附加scope检查

同一主线另有npugraph_ex/npugraph_ex/patterns管理器：在stream一致后，还要求匹配call_function节点的deterministic_scope_level、core_limit_scope分别一致，之后才调用extra_check。python/torchair管理器只保留流检查后调用用户校验；不将独立包行为当已由任意torch.npu别名继承。

两处skip_duplicates分支直接比较torch.__version__与"2.7.0"，不能忽略版本对象自身的比较实现来声称其是纯字典序或已复现误判。API文档的最低版本、所装对象语义及实际传给PyTorch注册器的参数分别核对。本次仅静态阅读完整模块/完整差异，未注册规则或运行匹配。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/register_replacement-0.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/api/npugraph_ex/register_replacement.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/pattern_fusion_pass.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/register_replacement-0.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/npugraph_ex/register_replacement.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_pass_manager.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py)（implementation）


## 独立包pattern_fusion_pass的两级门槛与scope元数据来源

npugraph_ex 文档把 register_replacement 的生效开关写成 options.pattern_fusion_pass（默认开启），未列版本下限；固定实现里该开关实际串联两级门槛。独立包两固定版 pattern_util 的 `_apply_pattern_passes` 都先比较 torch.__version__ 与 "2.6"，低于 2.6 时仅打 warning「The pattern_fusion_pass is unsupported when torch < 2.6 .」并直接返回（主线 21–24、发布 19–21）：已注册的自定义 Pattern 与内置 Pattern 一律不应用，注册本身仍在管理器里。本卡前文「开关与边界」把 ≥2.6 门槛只归于 GE 配置，按此修正为集成与独立两管理器同受此门；比较同样直接用 torch.__version__ 对象，排序语义仍按该对象实现核对。开关开启且版本达标时，每次应用前重新注册五组内置规则（AddRMSNormDynamicQuant 两变体、AddRMSNormCast、BatchMatmulTranspose、AddRMSNormQuant；独立包两版均无集成侧 max-autotune 的按需分支，见[Pass 的执行层次](../../guides/optimization/torchair/torchair_fx_pass_and_fusion_controls.md)），随后才调用管理器 apply_pass（npu_fx_compiler.py 369–370 → pattern_util.py 主线 27–37/发布 24–35）。

独立包附加 scope 检查的元数据来源在 apply 前一次性写入：主线用 `add_scope_metadata_to_node_meta` 按 npugraph_ex.scope_enter/scope_exit 标记把 stream_label、deterministic_scope_level、core_limit_scope 标注到各节点 meta（graph_utils.py 56–89，含嵌套栈与 stream 切换识别）；发布同位置只调用 `add_stream_label_to_node_meta`（graph_utils.py 16 起，air 命名空间标记），因此发布管理器没有 deterministic/core_limit 检查可消费的输入，与「同名独立包入口的附加scope检查」一节的主线限定一致。PatternMatcherPass 仅在构造器带 pass_name 形参时命名为 npugraph_ex_generic_pattern_pass（两版同查 `__init__.__code__.co_varnames`）。scope 元数据是编译期静态标注，不证明设备时序或确定性已运行验证。

## 补充来源

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_util.py)（implementation）：1–40 全文。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/pattern_util.py)（implementation）：1–35 全文。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/graph_utils.py)（implementation）：56–89。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/graph_utils.py)（implementation）：16–38。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：325–374（pre/noop/recover/pattern/view/post 顺序与 pattern_fusion_pass 门）。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py)（implementation）：67–103（pass_name 条件与 add_stream_check 包装，无 execution-scope 检查）。
- [固定约束 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/api/npugraph_ex/register_replacement.md)（constraint）：1–102 全文复核，约束段 32 行未列版本下限。

---
type: Guide
title: GE Ascend IR诊断：符号输入重建与mock映射
description: 解释内部ExportedProgram优化到Ascend IR的符号重建、临时图、converter与mock来源、输出映射及结果对象边界。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/ge_graph_ascend.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
created_at: '2026-11-11T11:10:04Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE Ascend IR诊断：符号输入重建与mock映射

主线内部 `_optimize_and_convert` 对 ExportedProgram 做 decomposition、FX 优化与符号输入重建，再以 `record_ascend_ir=True` 转成 GE 图和 FX→IR 字典。字典可以包含 mock 节点，适合分析转换关系，不能用“成功拿到字典”替代设备编译验收。本卡为固定主线 `92e1e967` 的静态审阅；没有运行 decomposition、FakeTensor、生成图、序列化或设备。

该模块 `__all__=[]`，入口和结果类均使用内部名称。发布固定版 `7c6c754b` 的同一文件路径不存在，仅记录这个路径关系。

## 入口与结果对象

| 阶段 | 实际行为 | 分析结果时注意 |
| --- | --- | --- |
| 配置和 decomposition | 缺 config 时创建 CompilerConfig；取默认表、调用 add_npu_patch，再用 custom_decompositions 更新表 | 自定义同名项后写覆盖；本组不展开外部表与 patch 实现 |
| decomposition | `ep = ep.run_decompositions(...)`，从此时的 ep 取 example_inputs 与 flat_args | 返回容器的 original 是此处 decomposition 后的 ep，不是无条件保存最初传入的对象 |
| FX 优化 | `_transform_do_not_use` 内执行 `_optimize_fx`、`_valid_graph` 并保存优化图 | 这些外部优化 Pass 的合同沿用[FX 编译管线](torchair_fx_compiler_pipeline.md) |
| 诊断图 | 构造 GeConcreteGraph，打开 record_ascend_ir | 构造器并非纯结果容器，初始化行为见[运行期绑定](torchair_ge_runtime_binding_and_first_call.md) |
| 返回值 | `_GeGraphAscend` 保存 proto、ascend_ir_map、original、optimized | property 返回所保存的对象，没有在 getter 中另做深拷贝 |

`to_json_dict` 先调用 protobuf MessageToDict，再递归把仍为 bytes 的值转 hex；已被该外部转换器编码成字符串的字段不会因为这一步自动改成 hex。`_NodeIR` 保存 source、ops 和 mapping，mapping 未给或为空时取空字典。

## 符号输入如何重建

| 处理 | 本地规则 |
| --- | --- |
| ShapeEnv | 创建 assume_static_by_default=True 的新环境，写入 range_constraints，再建 allow_non_fake_inputs=True、export=True 的 FakeTensorMode |
| bound | 有限值用 int；正无穷写 `2**31-1`，负无穷写 `-2**31` |
| 符号登记 | 跳过 lifted 参数/buffer 的占位符，从用户 fake Tensor 的 size、stride、offset 及符号占位符登记简单 SymPy Symbol；已登记表达式不重复覆盖 |
| hint | 已提取符号以其 hint 写 var_to_val；约束中尚未写值的符号用上下界中点填入 |
| 参数/buffer 输入 | Tensor 在新 FakeTensorMode 中 from_tensor(static_shapes=True)，其他值原样保留 |
| 用户输入 | 按符号字符串排序，在所属用户占位符前补符号参数；fake Tensor 重建 size/stride/offset，其他符号重新取/建 SymInt，其他 meta 值原样加入 |
| 显式元数据转移 | 复制 dim_gears；真实输入为 Parameter 时给 fake 输入写 `_torchair_is_parameter=True` |

这些值用于内部符号转换，不是动态范围的运行覆盖实验。尺寸/stride 列表重建 helper 仅显式处理 torch.SymInt 元素；简单符号可复用已登记 SymInt，其他表达式进入 create_symintnode(hint=...)。不要把该流程概括成任意复合约束或所有输入私有属性都已完整迁移。

随后深拷贝 optimized_ep.graph_module 成临时 gm，按已登记符号在原所属 placeholder 之前插新 placeholder，执行 lint/recompile 与 `_optimize_sym_input`，再在新 FakeTensorMode 下运行 `_NpuGraphConverter`。这里只描述源码将调用的流程，本次未执行这些动作。

临时图转换后，按节点名找到 optimized 图中的同名节点；只有临时 `torch_fn` 非 None 且长度比原条目更长，才将该项回写。它没有在这里把临时 gm 的全部 meta 或节点结构复制回 optimized_ep。

## converter检查与mock分支

`_NpuGraphConverter._wrap` 在解包 NPU 参数之前记录图的 op_count_before，parse_node 成功返回后才把该字段设回 None；这里没有给这次复位加 finally。正常的元数据节点上下文来自 run_node 的 converter_context 调用。

| 条件 | `_can_use_converter` / parse_node 行为 |
| --- | --- |
| 四个特殊 scope/record/wait target、无符号零元素快捷路径、sym_stride/sym_storage_offset | 可直接通过局部 availability 判断 |
| auto_functionalized_v2 | 对 args[0] 中的原算子递归判断；不可转换时另以内部 mock 参数走其专门转换器 |
| 普通目标 | 查 get_or_auto_gen_converter，非 None 就返回 True；仅捕获该查询中的 RuntimeError 并返回 False |
| 判断 True | 调用实际转换器并记录新增 OpDef，source 为 `converter` |
| 判断 False | 按 schema 提取输入和输出，创建 op_type 为 str(target) 的 mock GE op，source 为空字符串 |

特殊 target 与空输出准入集合见[GE控制边与空Tensor快捷路径](torchair_ge_multistream_control_edges_and_scope_labels.md)。availability 没有预先执行 converter 证明参数均合法，实际转换失败也没有被这里统一改成 mock。mock 输入构造按 schema 位置优先取 args，再取同名 kwargs；只收 GeTensor 或元素全为 GeTensor 的 list/tuple，其他 tensor 槽写 None，非 tensor schema 参数跳过。

记录逻辑取转换前后新增的 OpDef 切片。没有新增 op 时仍可以留下 `_NodeIR(source=..., ops=[])`；这与未记录该 FX key、mock 节点和可执行 kernel 是不同结果。

## 输出映射的粒度

| 项目 | 实际表示 |
| --- | --- |
| 单个 GE 输出 | 名称加其 index，形成 `name:index` 字符串 |
| 顶层 list/tuple | 逐项处理；None 记录为字符串 `None`，无法取名的项跳过 |
| 名称提取 | 先取 node.name，再取 desc.name；嵌套 list/tuple 只沿第一个元素取名 |
| 嵌套容器 | 名称 helper 虽能递归第一项，外层 mapping 仍访问原对象的 `.index`；不是通用 pytree 输出结构编码 |

特别是 list/tuple 自身也有 index 方法，不能把嵌套容器形成的字符串自动当成正确的 Tensor 输出索引。OpDef 字典同样经 MessageToDict 和递归 bytes 后处理，不是已认证的跨版本序列化协议。

排查时同时查看 source、ops、mapping、临时符号参数和 optimized 节点的 torch_fn。先区分真实 converter、mock 与空新增 op，再结合实际编译/执行结果评价模型优化，避免把诊断可视化的完整程度当成算子支持或性能结论。

## Evidence

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/ge_graph_ascend.py)（primary）：1–340。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：1161–1162、1684–1720、1788–1833、2160–2269。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：157–168、211–234。

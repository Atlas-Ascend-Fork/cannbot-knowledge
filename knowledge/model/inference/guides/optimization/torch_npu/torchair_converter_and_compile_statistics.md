---
type: Guide
title: TorchAir GE 支持度与编译统计：导出结果的解释
description: 区分FX摘要的源码启发式与Fake计数、GE编译统计和实际执行，保留默认Eager回退及融合匹配/生效边界。
tags:
- task.debugging
- topic.compilation
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/compiler_config.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/converter_export.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/export_compile_stat.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/converter_export.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/export_compile_stat.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/fusion_switch_file.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/CONTRIBUTING.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/tests/smoke/README.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/tests/smoke/README_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/tests/smoke/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/fx_summary.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/fx_summary.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py
  role: implementation
created_at: '2026-11-09T02:14:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchAir GE 支持度与编译统计：导出结果的解释

## 版本与范围

依据发布子模块 7c6c754bed00c86ffaaa2a45cb7ac2724f058013 的 GE 配置文档，选择 A2/A3 推理，未运行导出。CompilerConfig 聚合 debug、fusion_config、experimental_config、inference_config、ge_config 等配置；npugraph_ex 的 options 不能与它混用。

## Converter 支持度

config.debug.fx_summary.type="csv" 导出 summary_时间戳.csv，包括目标、类型、调用次数、支持状态和输入输出统计。fx_summary.skip_compile 默认 True，跳过 Ascend IR 编译并执行 FX Eager，适合 Converter 不全时收集完整信息；False 才继续 GE 编译。正式图模式应移除诊断的 fx_summary.type 设置，并确认实际运行路径。

公开文档把“已支持/部分支持”用于Converter状态；下文固定实现实际采用源码文本启发式，不能只凭标签证明当前dtype/shape/属性与硬件可编译或已验证。主线自定义算子的零交付件自动适配是另一条有条件路线，不用它重写发布版支持度结论。

## 编译统计

config.ge_config.export_compile_stat 为字符串：0 关闭、1 正常退出时生成、2 默认在图编译完成时生成。fusion_result.json 的 graph_fusion/ub_fusion 按图记录，match_times 是匹配、effect_times 是实际生效，repository_hit_times 是 UB 优化知识库命中。生成统计文件不等于模型已运行或性能已改善；编译中途尚未完成也不保证有完整结果。

## 验证

核对执行模式、导出时间、对应 FX/GE 图与融合计数，结合实际输入和运行日志定位未支持或未生效原因，再进入精度和性能对照。

- [自定义算子入图契约](../../integration/torchair/custom_operator_graph_contract.md)
- [融合控制](../torchair/torchair_fx_pass_and_fusion_controls.md)


## 主线诊断对应关系

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节文档/实现已核对，主线总览覆盖A2/A3与950PR/950DT；发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的A2/A3条件仍独立保留，不回推发布版950或两仓主线配套。

主线converter_export和export_compile_stat技术条件与发布页一致：GE下fx_summary只支持csv，默认不导出；skip_compile=True以FX Eager执行，False才继续GE编译。调用计数和输入/输出统计帮助定位具体变体，“已实现/部分支持/未实现”不等于当前安装、产品和所有参数已通过验证。

统计页的“异常退出也能生成”依赖已经到达所选写出阶段：默认字符串"2"在编译完成时生成，"1"依赖正常退出，"0"关闭。未完成编译就崩溃不保证文件完整或存在。fusion_result.json按session_and_graph_id区分图，graph_fusion与ub_fusion是不同层次，repository_hit_times也不是端到端收益。

文件生成位置、阶段、图编号与实际执行模式一起保存；收集支持度后撤掉fx_summary诊断设置，再做性能测量，不把Eager路径的时间写成GE优化后耗时。

## 根目录支持度与测试清单不是执行证明

发布贡献说明和主线英文把未支持（壳实现抛异常）、未注册（缺注册）和部分支持（需查输入分支）分别列出；只在目录找到converter文件不足以提升状态。declare_supported仅为声明的样例生成测试，不保证所有dtype/广播/alpha/动态shape被穷举。

三份smoke说明的fullgraph=False、dynamic=None与普通Converter导入限制各自保留，通信npu_define算子需独立hcom入口；prefix匹配不到测试样例不是精度已失败，也不计通过。根README使用CPU Tensor的加法示例、SDK/stub单ST与真实NPU烟测都不能替代目标模型验收，详见[Converter实现](../torchair/torchair_converter_implementation.md)。

## FX摘要的实际支持判据和计数消费者

本节补读固定主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`与发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`的python/torchair实现。既有平台范围沿用前述文档；下面是局部静态实现解释，未新增产品/安装组合、运行精度或verified依据，不用于独立npugraph_ex。

两版_get_compiled_gm只在max-autotune且fx_summary.enabled时调用_summarize_fx_graph，随后skip_compile=True才返回原gm的Eager包装；False继续后续分支，仍可能被data_dump等调试路径提前返回。摘要分析先于这一回退选择，分析抛错不等于已经成功返回Eager。主线_FxSummary默认type=None、候选csv，skip_compile默认True；构图与实际执行的分工继续见[FX编译管线](../torchair/torchair_fx_compiler_pipeline.md)。

_get_converter_status不是用当前Tensor参数试运行Converter，而是inspect.getsource取得源码，再做字符串包含判断：

| 条件 | 返回标签 |
| --- | --- |
| Converter为None | 未注册 |
| 存在__wrapped__且其源码包含`raise NotImplementedError`，同时Converter源码包含`return ` | 部分支持 |
| 仅满足前一条拒绝字符串条件 | 未实现 |
| 仅满足`return `条件 | 已支持 |
| 两个字符串条件均不满足 | 未知状态，请查看源码 |

这些判断没有解析控制流、逐参数guard或调用GE编译；注释/源码文本也可能影响匹配，inspect.getsource失败在所读分析链没有统一降级标签。builtin callable在_OpSummary中直接标“已支持”；其它target按字符串是否含prim粗分prims/aten，再查_ge_converter属性或注册表。类型标签也不是后端支持矩阵。最终仍需查看准确Converter及输入分支，不能从CSV支持率认证完整模型。

_summarize_fx_graph新建Interpreter，取得当前detect_fake_mode(None)并在该上下文中运行example_inputs；它没有在此新建一个保证适用于任意外部调用的FakeTensorMode。所读解释器只覆盖call_function：先调用父实现取得输出，再按target对象聚合并record。因此调用次数是这次摘要遍历中成功到达record的call_function次数，不是训练/服务运行频次、设备Kernel launch数或耗时/带宽测量。call_module/call_method等节点不能仅据这一个override视作都有相同逐节点统计。

record把args与kwargs格式化为字符串，输出另转字符串，分别计入输入和输出字典，再按各自频次排序。两个表是独立聚合，不保存每个输入变体与输出变体的成对映射，也没有完整stride/存储别名或逐次输入数值快照。该格式化临时替换FakeTensor.__repr__并在finally恢复，主要显示dtype和size；这个类属性修改不是线程局部状态，不能据finally认证任意并行摘要的隔离。

两版_contain_statement、_get_converter_status、_OpSummary、_SummarizeFxGraph及_summarize_fx_graph五组选定完整AST相同。repr助手主线用rsplit('.',maxsplit=1)，发布用split('.')后取末项，另记为版本差异，不宣称整模块AST相等。

CSV写入发生在Interpreter运行成功之后，再检查.csv后缀、路径并打开文件，未在这条链运行GE或设备数值对照。文件存在、行数、支持标签、输入变体次数分别用于定位，不等于已完成后续GE编译或当前模型性能验收；摘要分析/源码反射/写文件开销也不当稳态业务耗时。实际Tensor采集与本节Fake摘要不同，见[FX Eager数据Dump消费者](torchair_fx_eager_dump_execution_and_coverage.md)。

本节只读所列关键范围，未执行摘要、反射上游函数、创建Fake模式、写CSV、编译或访问设备；原生Eager、GE、错误分支与性能仍须在匹配栈实测。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/compiler_config.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/converter_export.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/export_compile_stat.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/converter_export.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/export_compile_stat.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/fusion_switch_file.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/CONTRIBUTING.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/tests/smoke/README.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/tests/smoke/README_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/tests/smoke/README.md)（constraint）

- [摘要消费者固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/fx_summary.py)（implementation）：定向范围30–31, 37–152。

- [摘要消费者固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/fx_summary.py)（implementation）：定向范围30–31, 37–158。

- [摘要消费者固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：定向范围690–718。

- [摘要消费者固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)（implementation）：定向范围609–633。

- [摘要消费者固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py)（implementation）：定向范围16–36, 71–75。

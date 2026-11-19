---
type: Guide
title: GE Converter 开发：覆盖场景、类型提升与动态形状
description: 以 fx_summary 定位未注册、未支持和部分支持节点，明确 meta_outputs、dtype_promote 及动态符号的实现职责。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING.md
  role: primary
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
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/supported_declaration.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/supported_declaration.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/tests/smoke/converter_test.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/tests/smoke/converter_test.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
created_at: '2026-11-09T04:39:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# GE Converter 开发：覆盖场景、类型提升与动态形状

## 范围与输入

依据 TorchAir 固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的贡献文档技术章节，选择 A2/A3 GE 入图开发。输入应是准确的 ATen/custom overload、Schema、真实模型输入域及已有 Eager 实现。本卡是 Converter 实现与排查方法，不替代完整 Kernel 源码分析。

## 先分辨缺口

在构造后端前设 `config.debug.fx_summary.type="csv"`，执行模型后检查 summary 时间戳 CSV。未支持表示可能已有抛异常的壳实现；未注册需要添加注册与实现；部分支持需要结合输入列核对具体分支。不能因为在目录找到同名文件或装饰器，就认为真实输入已支持。

## 实现的四个约束

1. 注册准确算子对象，签名保留原 Schema 的参数顺序、可选参数和关键字语义，按需要增加 meta_outputs。declare_supported 描述实际支持的调用形态；无法支持的输入在实现中明确拒绝，不能列为已支持。
2. Converter 的 GE Tensor/TensorSpec 是构图对象，不是有真实数值的运行 Tensor。输入 GE Tensor 不提供运行数值；TensorSpec 虽有静态 size 属性，但动态规格访问会拒绝，详见[构图对象与静态规格](ge_converter_tensor_and_control_edges.md)。动态 shape 应由 GE 算子表达处理，不能读取样例值固化为常量。
3. meta_outputs 用于确定输出 dtype 及可变输出数量。例如 split 的输出数与 add 的类型提升各有职责，不能随意用第一个输入 dtype 替代输出规格。
4. 对要求输入同 dtype 的 GE 节点，按算子语义用 dtype_promote 提升至 meta_outputs.dtype；图编译不会自动替你修正 FP32 与 INT64 常量相加的 GE Add 输入。add 的标量 alpha=1 可用 Add，其他 alpha 路线需适合的带系数 IR，不能忽略 alpha 来追求融合。

## 自定义 IR 和交付

原生自定义路线在 Torch 注册 Schema、PrivateUse1 和 Meta 后，还需有可调用 GE IR。贡献文档的 codegen 路线由 REG_OP 原型生成构图 API，再在 Converter 中按输入、属性、输出映射调用；自己的 GE IR 还要注册 infershape。Schema、Meta、代码生成成功和底层可执行实现是不同交付项。Meta 输出应保留 meta device；不要无意创建 CPU Tensor。

lite 导出场景可在该快照专用 lite Converter 路径后注册同一 ATen 节点以覆盖原实现，但仅启用 config.export.experimental.enable_lite_export 时生效。这不是所有普通 GE 编译都会采用的全局替换规则。

## Decomposition 也影响可优化 IR

interpolate 等操作可能先被分解为多个小算子，影响特定后端性能或离线导出结构。文档给出禁止或替换默认 decomposition 的两种策略；替换后还应检查新算子是否继续被分解、Meta 是否完整。CompositeImplicitAutograd 的 C++ 路径可能缺少 dynamic=True 的符号推导，需要相应 Python 实现/Meta，不能只在静态样例通过后宣称动态支持。

## 验证

declare_supported 可供来源 smoke/converter_test.py 生成测试，但需要真实 NPU、匹配安装和已实现 Converter；本次未执行该测试。实际验收应检查 FX 节点、GE 图、输出数量/dtype、广播、混合类型、alpha 和动态输入，再评估小算子分解对性能的影响。

- [注册接口契约](../../../apis/torchair/register_fx_node_ge_converter.md)
- [Schema、函数化和两类后端交付](../../integration/torchair/custom_operator_graph_contract.md)
- [ATen 高风险限制](torchair_aten_constraint_review.md)

## 根贡献与smoke说明里的示意缺口

发布贡献指南与主线英文示例的custom_op执行x+y，Meta却只empty_like(x)：当y引入广播或类型提升时不能照抄。例如x为[4,1]、y为[4,4]，相加输出应为[4,4]，empty_like(x)仍[4,1]；这是按广播关系的静态推断，未执行算子。保持meta设备只是必要条件，还需返回真实shape/dtype/stride/别名关系。

lite覆盖add的示例直接ge.Add(self,other)，忽略签名里的alpha且省略dtype_promote；它是覆盖注册演示，不能当alpha!=1或混合类型的完整实现。REG_OP示例列类型集合只描述IR原型，不独立证明所有产品/Kernel都实现了每一类型。

smoke文档的7种declare_supported样例覆盖广播、混合类型、常量和alpha，但不是自动穷举完整输入域。表称dynamic=None“静态”，实际该值是自动判定，fullgraph=False也不证明整图无断点；npu_define通信Converter不主动导入，不能由普通converter测试列表空缺断定不支持。具体prefix缺declare_supported时会报Cannot find testcase match prefix，需与实现错误分开。

文档路径仍写smoke/converter_test.py、smoke/hcom_st.py，实际快照目录是tests/smoke；按checkout文件核对工作目录。真实NPU Converter smoke与SDK/stub UT/ST属于不同验收层，当前没有运行其中任一测试。函数/模块已注册、生成测试和运行通过分别记录。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/CONTRIBUTING.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/tests/smoke/README.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/tests/smoke/README_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/tests/smoke/README.md)（constraint）
## 注册表反向核对：declare_supported 是冒烟矩阵，不是运行时门禁

前文把 declare_supported 定位为「描述实际支持的调用形态」的编写义务；本节补注册表→逐目标方向的机械反向核对（本地脚本扫描两 pin `python/torchair` 全树装饰器文本，未 import 上游；脚本与输出随批次 evidence 留档可复算）：

- 运行时注册表 `_CONVERTERS` 只存目标→函数，不携带 dtype/参数约束；转换路径经 `get_or_auto_gen_converter(target)` 查询（fx2ge_converter.py 主线 815 定义、1716/1774 两个调用点，发布同构），从不读取 `_DECLARED_SUPPORTED_CONVERTERS`。该声明表的唯一进程内读者是 `_declare_supported_converters` 访问器（主线 531/发布 365），其唯一仓内消费者是 `tests/smoke/converter_test.py`（两 pin 均 11 导入、137 取表）；`supported_cases` 属性无其他运行时读者（rg 负向）。
- 声明矩阵规模：主线 318 个 `@declare_supported` 装饰器、262 个文件、318 个不同声明目标——其中 aten 目标 251 个（按重载后缀去重后的基名 209 个）、非 aten 67 个（math.ceil/math.floor/operator.mod/operator.neg、torch.ops.npu 自定义与 worker-scheduler 家族等）；发布 315/259/315（aten 目标 250、基名 208、非 aten 65）。类型规格类 12 个（supported_declaration.py 主线 1–112 全读：F32/F16/BF16/F64/I32/I16/I64/I8/U8/C64/BOOL/T；发布版仅 109–111 折行差异）。使用频次 F32 821、F16 481、BF16 143、I32 101、I64 52、I8 49、BOOL 43、U8 25、T 23、I16 16、F64 8、C64 2（发布几乎相同）。
- 与附录清单的反向交叠：151 个文档条目中 101 个至少命中一个带声明用例的目标，50 个没有任何声明用例——含全部 36 个 `_foreach_*` 条目、`_softmax`/`_softmax_backward_data`、`_native_batch_norm_legit(_no_training)`、`clone`/`empty`/`empty_like`/`new_empty`/`detach`、`fft`/`fft2`、`embedding`、`nll_loss`、`MaxPool2d`、`index.Tensor`；两 pin 交叠集合相同。对这些行，文档约束栏的 dtype 承诺没有仓内类型化用例可对，验收只能回到[ATen 约束](torchair_aten_constraint_review.md)的逐算子运行核对；反向地，101 行「有声明用例」也不证明声明覆盖了约束栏全部 dtype。
- 样例：`mse_loss.default` 声明 3 个 F32 用例（reduction 0/1/2），同文件 `mse_loss.out` 无声明且注册体直接 raise（ge_converter/aten/mse_loss.py 主线 1–29/发布 1–34）——注册、声明、可用是三个独立状态。
- 边界：converter_test 实体化规格时 `device = 'npu' if ('torch_npu' in sys.modules) else 'cpu'`（主线 36/发布 37）——torch_npu 未导入时在 CPU 上跑冒烟，通过不证明 NPU 支持面；声明用例本就不是穷举（前文 smoke 结论），本节计数是静态文本扫描口径。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/supported_declaration.py)（implementation）：1–112 全文（`_TypedTensor` 与 12 个规格类、`Support` 参数断言与格式化）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/supported_declaration.py)（implementation）：与主线 diff 仅 109–111 折行。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/tests/smoke/converter_test.py)（implementation）：窗口 1–40（导入 11、as_tensor device 判定 36）、120–170（_test_converters 前缀匹配与逐用例执行）。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/tests/smoke/converter_test.py)（implementation）：同窗口（11/37/137）；与主线仅折行差异。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss.py)（implementation）：1–29 全文。
- [新增来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mse_loss.py)（implementation）：1–34 全文（diff 仅折行与 import 注释）。
- [新增来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：窗口 505–532（`supported_cases` 属性与 setter 508–517、`declare_supported` 519–526、访问器 531）；`get_or_auto_gen_converter` 815 与调用点 1716/1774 为 rg 行号确认。
- [新增来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：窗口 348–366（`declare_supported` 354–364、访问器 365）；声明表定义 145 rg 行号确认。
- 机械扫描（evidence `extract_declared.py`）：两 pin 输出 `declared_stats_main.txt`/`declared_stats_release.txt`（declare_supported 计数、目标归一、dtype 频次、151 行交叠与无声明清单）；151 行入口→分解目标映射沿用 `aten_reverse_map.py` 的既有映射，不重复留档。负向扫描（无截断 rg）：`_declare_supported_converters` 仓内仅 converter_test.py 11/137 消费（两 pin）；`supported_cases` 在 fx2ge_converter.py 之外无读者。全部静态读取，未 import/运行上游。

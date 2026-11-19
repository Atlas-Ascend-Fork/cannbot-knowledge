---
type: Guide
title: GE注册与内建转换：延迟加载及Lite覆盖
description: 核对模块发现与延迟注册、内建和Prims的不同提升规则及主线Lite覆盖，记录量化矩阵乘未消费的转置等参数。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/builtin_converters.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/builtin_converters.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/c10d_functional/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/c10d_functional/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/higher_order/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/higher_order/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/lite/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/lite/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/lite/quantmatmul_lite.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prim/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prim/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/convert_element_type.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/convert_element_type.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/le.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/le.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/lt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/lt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/maximum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/maximum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/minimum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/minimum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/mul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/mul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/quantized/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/quantized/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/rngprims/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/rngprims/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/ge_custom.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/ge_custom.py
  role: implementation
created_at: '2026-11-10T09:50:33Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE注册与内建转换：延迟加载及Lite覆盖

## 固定版本与证据范围

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。十九个加载/内建/Prims/Lite主题中，十八对文件AST相同，主线Lite量化映射缺同路径发布文件；后者不等于发布软件没有量化矩阵乘。主线完整20份分页、发布完整AST/注释差异及限定注册辅助范围已读。

整卡产品矩阵未知，保持draft与空平台；未导入或执行上游、生成并执行Converter、编译或运行NPU。模块文件存在、装饰器语法和Support声明都不是实际注册/运行通过证明。以下注册器、类型辅助和npu_fx_compiler仅覆盖标明的函数/方法，不能称整个大型模块全部审阅。

## 模块发现和延迟加载

ge_converter/__init__.py先导入prim、higher_order、quantized、rngprims、c10d_functional和builtin_converters，再通过try_import_submodule分别加载prims/aten。各子包__all__从pkgutil.iter_modules目录枚举生成，**这不是每个模块成功完成注册的清单**。

try_import_submodule逐个import时只捕获AttributeError并静默跳过；ImportError等其他异常不在这个except范围。custom/__init__.py同样枚举后import，但AttributeError会warnings.warn；lite/__init__.py遇到AttributeError静默跳过。它们没有实现对整个子模块的注册回滚，不能因导入过程中一个异常就假定此前装饰器从未执行或整个家族都不可用。

_get_converter在目标不在_CONVERTERS时延迟导入custom，再优先查看目标的_ge_converter属性，否则索引defaultdict(lambda:None)。get_or_auto_gen_converter若目标已有_ge_converter，直接取用，不先触发这个延迟导入步骤。入口查找顺序和模块加载是不同合同，不把磁盘文件数量当注册覆盖率。

## 注册目标、Meta和自动生成的边界

register_fx_node_ge_converter(None)返回空函数，装饰后没有正常Converter注册，不能把getattr(...,None)兼容声明当有效算子绑定。正常Converter.__call__用_wrap_converter包裹函数，并按原签名是否包含meta_outputs设置require_meta；wrapper将提供的meta_outputs交给get_meta_outputs后调用原函数，原样返回其GE结果。本段没有证明任意Meta或输出别名完整。

注册器先尝试向准确aten_op对象设置_ge_converter属性，失败时放进_CONVERTERS映射，返回Converter对象。不是只凭Python函数名决定注册目标；例如builtin_converters里pow和mod的函数同名，不等于两个操作对象被绑定成同一运算。

主线get_or_auto_gen_converter在未找到绑定后调用_generate_converter_code，其内部依次校验支持、IR和参数/别名，再构建代码；不能仅看外层生成调用就宣称任意算子都支持。发布版先_can_autogenerate_converter检查Torch custom/scalar/IR等条件，否则RuntimeError；其functional命名分支对str(target).split('.')[1]取得的字符串调用pop存在静态类型疑点，未执行验证。自动生成函数调用和真实可编译实现分开核对。

## Lite模式的注册影响不只限于一张图

主线lite_converter_mode使用threading.local().active，进入设True，finally直接设False；注册器在该时刻读取模式。Converter若目标已在进程级_LITE_CONVERTER_OPS集合，直接跳过后来的注册；Lite注册则把目标加入集合再写_ge_converter。退出context只重置active，不在这里清理集合或恢复旧绑定，不能把更改后续配置等同于撤销先前注册。

npu_fx_compiler._NpuFxCompiler._get_compiled_gm在int(config.export.experimental.enable_lite_export.value)为真时，进入该context再import lite子包。Python模块导入缓存、context状态和op上的注册结果需分别核对；不能假定每次编译都会重新执行所有装饰器，也不能给嵌套模式或并发切换补造恢复保证。发布版所选注册器没有对应Lite标记分支。

同一_get_compiled_gm还可能在fx_summary.skip_compile时返回包装原gm，data_dump开启时包装dumper，日志说明回退Eager；名称含compiled不证明每次都完成GE编译。本文只读该方法完整范围，未执行任何debug或导出路径。

## Python内建与ATen节点不是相同入口

| 准确注册目标 | 本层计算 |
| --- | --- |
| operator.add/sub/mul/floordiv/pow | 两输入都不是GE Tensor时直接Python运算；否则按Meta dtype处理两输入，再Add/Sub/Mul/FloorDiv/Pow。 |
| operator.truediv | 同样先分Python标量分支；GE分支按Meta处理后**ge.Div**，不能与[ATen算术](torchair_ge_arithmetic_lowering.md)的RealDiv名称直接互换。 |
| operator.mod | 标量直接Python百分号；GE分支按Meta后**ge.Mod**，不同于ATen remainder映射的FloorMod，负数/混合类型需按真实IR核对。 |
| torch.sym_float | 非GE Tensor转Python float，否则Cast到Meta dtype。 |
| math.floor/ceil | 非GE Tensor调用Python math；GE Tensor先Floor/Ceil，再按Meta处理输出。 |
| operator.neg | 直接ge.Neg(self)，没有复制其他内建的Python标量快捷分支。 |

Torch版本条件经packaging.version.parse比较>=2.6.0且torch有sym_sum时，才注册torch.sym_sum：inputs整体不是GE Tensor就Python sum(inputs)，否则ReduceSum(inputs,INT64轴0)。不能把“列表元素可能为Tensor”的Support候选等同列表整体走GE ReduceSum，实际列表与单个GE Tensor的分支不同。

## Prims不继承ATen的类型特例

| 准确入口 | 直接映射 |
| --- | --- |
| torch.ops.prims.add.default | ge.Add |
| torch.ops.prims.mul.default | ge.Mul |
| torch.ops.prims.le.default | ge.LessEqual |
| torch.ops.prims.lt.default | ge.Less |
| torch.ops.prims.maximum.default | ge.Maximum |
| torch.ops.prims.minimum.default | ge.Minimum |
| torch.ops.prims.convert_element_type.default | torch_type_to_ge_type(dtype)对象翻译后ge.Cast |

这些函数没有前六项统一Meta Cast、bool/UINT8中转或完整广播检查，不能从同名ATen实现套入规则。convert_element_type虽然dtype注解为int，但调用的是Torch dtype对象翻译辅助，不能混同另一个dtype数值翻译函数；参见[类型转换与封装](torchair_ge_dtype_scatter_lowering.md)。

## 主线Lite量化矩阵乘的准确处理

lite/quantmatmul_lite.py注册torch.ops.npu.npu_quant_matmul.default，output_dtype=None时设数值1，经torch_dtype_value_to_ge_type翻译为**GE INT8**，不能按另一枚举把1解释成FP16。这个入口属于所选主线Lite映射，不将其默认值推广为所有量化矩阵乘。

x2_dtype非None且等于torch_npu.int4时，x2 Bitcast为INT4并keep_dim=True；scale为INT64时Bitcast成UINT64，不是数值Cast。随后QuantBatchMatmulV3传x1/x2/scale、offset/bias/pertoken_scale及翻译后的dtype。

虽然签名接收transpose_x1/transpose_x2，两项节点属性都硬编码False；x1_dtype、pertoken_scale_dtype、scale_dtype、group_sizes、y_scale也未被此函数消费。不能因为签名有参数就认证转置、分组、所有低比特格式或缩放精度已经实现。是否真正启用该覆盖映射，还应核对导入顺序、Lite标记和实际FX目标。

## 验证与关联

先保存准确FX目标对象、是否经过分解、模块加载异常、目标_ge_converter/注册映射、Meta与dtype，再分别核对内建/Prims/ATen节点、Lite标记和生成代码。真实IR、精度、别名及性能需在匹配软件栈另验；本文没有执行这些实验。

- [通用Converter开发与声明](torchair_converter_implementation.md)
- [源代码的类型与参数边界](torchair_ge_matmul_lowering.md)
- [文档层集合通信入图](collective_communication_graph_contract.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/__init__.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/__init__.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/__init__.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/__init__.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/builtin_converters.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/builtin_converters.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/c10d_functional/__init__.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/c10d_functional/__init__.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/__init__.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/__init__.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/higher_order/__init__.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/higher_order/__init__.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/lite/__init__.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/lite/__init__.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/lite/quantmatmul_lite.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prim/__init__.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prim/__init__.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/__init__.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/__init__.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/add.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/add.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/convert_element_type.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/convert_element_type.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/le.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/le.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/lt.py)（implementation）
- [固定来源 27](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/lt.py)（implementation）
- [固定来源 28](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/maximum.py)（implementation）
- [固定来源 29](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/maximum.py)（implementation）
- [固定来源 30](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/minimum.py)（implementation）
- [固定来源 31](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/minimum.py)（implementation）
- [固定来源 32](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/prims/mul.py)（implementation）
- [固定来源 33](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/prims/mul.py)（implementation）
- [固定来源 34](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/quantized/__init__.py)（implementation）
- [固定来源 35](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/quantized/__init__.py)（implementation）
- [固定来源 36](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/rngprims/__init__.py)（implementation）
- [固定来源 37](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/rngprims/__init__.py)（implementation）
- [固定来源 38](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 39](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 40](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 41](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 42](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）
- [固定来源 43](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（implementation）
- [固定来源 44](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）
- [固定来源 45](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）
- [固定来源 46](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）

## 自动生成的参数映射与Clone成本

固定主线和发布版的生成器都按Schema与GE注册描述拼接Python代码，再由入口执行并注册。以下是本地生成合同，未运行生成代码；它补充前文准入条件，不替代手写Converter的语义检查。

| 阶段 | 实际规则 | 适配与优化影响 |
| --- | --- | --- |
| GE名称 | 取准确target字符串的第二段，去末尾`_functional`，按下划线分词后`capitalize`拼接 | 名称来自约定，未用Schema与GE描述做逐参数语义配对。主线正确连接去后缀；发布前置准入的字符串`pop()`问题见前文。 |
| 参数签名 | 保留位置参数和关键字专用参数及`repr(default)`；仅类型字符串恰为`Tensor`、`Optional[Tensor]`、`List[Tensor]`归Tensor组 | 生成函数保留`*`，内部却把Tensor组在前、其他组在后的所有名字作为位置实参传给`custom_op`，对应GE描述的顺序需要一致；其他容器类型不会因含Tensor字样自动归入此组。 |
| 数量门槛 | Tensor参数数等于GE输入数；非Tensor参数数不超过GE属性数；write-alias参数数加Schema返回数等于GE输出数 | 这些是数量检查，没有逐项证明dtype、动态列表展开数量或同名参数的含义。允许少于GE属性数，不等于后续位置绑定允许省略这些位置。 |
| GE原地关系 | 先把GE输入/输出描述转dict，按同名键交集确定输入及输出索引 | 有Torch write-alias时再检查数量等于GE原地输出数，未逐项比对Torch alias所指位置与GE交集的位置。 |
| Torch无write-alias，GE却有原地输出 | 给交集中的输入名字生成`Clone(...)`，随后仍返回`custom_op`结果 | 自动适配可能额外插复制节点，应在实际图中检查；这里没有展开Clone的存储和执行实现。 |
| Torch有write-alias且数量匹配 | 执行`custom_op`，从返回值按GE输出索引选取非原地项 | 全部移除时没有显式return；仅剩一项生成`return (out[n])`，没有单元素tuple的逗号，多项才形成tuple。不要仅靠Schema返回数推断该生成文本的Python返回层级。 |

主线准入对`NumberType`作显式拒绝，并按target完整字符串是否含`prim`、`prims`或`aten`子串排除目标；不是只比较namespace。发布版相同判断位于`_is_torch_custom`及`_has_no_scalar`。已有Converter绑定仍先于这些自动生成检查返回。

`custom_op`有位置实参时，用GE输入数加属性数严格检查总数，覆盖显式inputs/outputs/attrs；Tensor动态输入先只检查外层list/tuple，不能由此认证每个元素。属性为None先跳过，其他值按注册类型构造；torch.dtype先映射为GE类型。输出名由GE输出dict的键生成，不在此推导动态输出数量。完整API见[custom_op](../../../apis/torchair/ge_custom_op.md)；生成成功、注册成功与模型数值/别名正确分别验收。

## 实现来源

- [固定实现1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)：815–1095。
- [固定实现2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)：637–903。
- [固定实现3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/ge_custom.py)：12–37。
- [固定实现4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/ge_custom.py)：11–27。
- [固定实现5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)：1696–1759。
- [固定实现6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)：1572–1640。

---
type: Guide
title: GE Tensor元数据：dtype域、缓存与静态规格
description: 区分图API、Proto、c10和Torch类型转换，记录两版低位/无符号映射、Tensor缓存及TensorSpec动态size边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: implementation
created_at: '2026-11-10T12:57:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE Tensor元数据：dtype域、缓存与静态规格

## 固定版本与范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的ge/_ge_graph.py。此前只覆盖局部函数的两份文件在本次补齐全文；本卡限定Python图描述与调用合同，不替代原生执行器、kernel和完整设备能力。产品矩阵未知，保持draft与空平台；未导入上游、构造/反序列化图、生成或执行代码、读设备数据或做性能实验。

## DataType、Proto和c10是不同类型域

模块定义图API DataType、Format与TensorType；ProtoDataType从生成的ge_ir_pb2导入，Torch dtype对象和c10整数值另有转换。不能按相同整数直连；例如图API DT_INT64为9，序列化域为8，c10表为4。枚举存在不等于算子或硬件支持，精确Proto编码见[绑定合同](torchair_ge_protobuf_binding_contract.md)。

Format还列FRACTAL_NZ_C0_16/2/4/8等代码成员，DataType为FLOAT6两类保留名称并注释当前版本不支持；这不是把所有布局或低位类型确认为kernel能力。完整API文档枚举与实现成员范围分别核对。

torch_type_to_ge_type支持明确Torch类型、部分hasattr保护的可选类型，并可通过m参数选目标枚举域；dtype=None直接None。主线新增float4_e2m1fn_x2对象映射，发布没有；未知对象RuntimeError，不按名字猜测。

主线torch_dtype_to_value按Torch>=2.8布局的硬编码c10表、结合实际存在的dtype对象返回整数，发布没有同一表和函数；不得运行无效枚举来探测。torch_dtype_value_to_ge_type则只处理其明确整数分支及285/290至297等特殊值，不是前者的完整逆函数，例如主线uint16映到27，后者没有27分支。

## 各转换表的接受范围不一致

主线ge_type_to_torch_type增加UINT16/32/64，并在有对应Torch类型时将FLOAT4_E2M1映到float4_e2m1fn_x2；发布对应低位类型回退uint8。HIFLOAT8、FLOAT4_E1M2也以uint8容器返回，E8M0有条件取原生dtype，否则uint8；容器类型不等于数值Cast或物理打包已完成。

_ge_dtype_to_ge_proto_dtype和_ge_proto_dtype_to_ge_dtype主线新增UINT16、UINT64、INT4映射；反向另有STRING，发布没有同一分支。两版图API的类型名称、Proto常量及具体转换表不能混为一份全类型双向矩阵，新增Proto HIFLOAT4也没有在这里自动获得对应转换分支。

NumPy转换只覆盖限定常规类型，不含BF16和所有低位/量化类型；_is_supported_ge_dtype_by_numpy捕获转换异常后False。_np_dtype_to_ge_dtype虽标注ProtoDataType，实际返回图API DataType成员，不能只按注解选择编码域。_ge_proto_dtype_str也只打印有限名字，否则Unknown；日志Unknown不能单独证明类型不存在。

## Tensor保存缓存，描述符并非每次反解

Tensor初始化保存node、index、创建时的name:index字符串和output_desc引用，Meta/symsize为空、_ge_dtype为UNDEFINED。dtype属性读缓存而非即时反解desc；手改描述符或重命名节点不保证全部包装器的dtype/边名缓存自动更新。controller按当前node名生成:-1，与已缓存tensor边名职责不同。

set_meta接受torch.Tensor、list或SymInt/SymFloat/SymBool；list通过list_to_torch_dtype检查元素为int/SymInt，返回INT64，一般tuple和普通Python标量没有同一分支。形状保存到_symsize及可读_meta属性，不等于填好了每个原生运行描述符字段或取得实际设备值。

set_torch_dtype通常更新缓存并将Torch类型转Proto写desc；提供ge_outputs且其Proto类型属于HIFLOAT8、E8M0或两类FP4名单时，保留该低位图类型并提前返回。不能把uint8容器Meta简单等同输出真实图类型，名单也没有覆盖所有量化名称。

rank在symsize未知时断言，get_numel只是各符号尺寸相乘，结果未必为Python固定整数。ControlTensor仅给节点:-1控制边，不创建实际完成事件。

## TensorSpec静态size与符号规格分开

TensorSpec对Tensor Meta保存符号size并逐维尝试int(str(dim))，失败时_size=None；访问size断言，rank取符号维数。符号标量规格为rank0、size=[]；其他类型没有完整规格，不能把None当作通用标量TensorSpec。

TensorSpec、Tensor和日志表示都只是编译描述，不能读其字段来认证实际运行值。具体Converter仍需保留正确dtype、shape、别名及动态关系，本次没有执行这些验证。

- [构图对象的文档合同](ge_converter_tensor_and_control_edges.md)
- [元数据辅助与hint](torchair_ge_metadata_support_helpers.md)
- [常量和自动提升](torchair_ge_primitive_const_promotion.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（implementation）

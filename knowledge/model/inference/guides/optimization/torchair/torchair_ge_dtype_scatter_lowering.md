---
type: Guide
title: GE类型转换与写回：FP4打包和描述符边界
description: 区分新旧dtype转换、FP4展开打包、反向不对称、QuantMax描述符与ScatterList输入拷贝，覆盖op-plugin
  eager 侧 npu_scatter_list 实现层（逐项 clone 与 reduce=update 限制），保留准确版本边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_bias.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_bias.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dtype_cast.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dtype_cast.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dtype_cast_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dtype_cast_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gather_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gather_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_max.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_list.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_list.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterListKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScatterListKernelNpuOpApi.cpp
  role: implementation
created_at: '2026-11-10T09:30:27Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE类型转换与写回：FP4打包和描述符边界

## 固定版本与证据范围

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。所选主线完整非空源码、发布完整AST/注释差异已审阅；这批成对Converter的差异为说明字符串、导入顺序、等价异常字符串写法，计算映射不变。QuantMax的同路径仅主线存在，缺路径不推导发布软件缺能力。

本卡限定静态构图合同，整卡平台矩阵未知，保持draft与空平台；未执行上游、GE编译、真机精度/别名/通信或性能实验。Support只是候选，警告和注释不是本次复现。IR参数与真实kernel、调度及外围函数化需分别核对。

## dtype数值、对象和描述符属于不同处理层

torch_dtype_value_to_ge_type/torch_dtype_value_to_ge_proto_type按Torch dtype数值翻译，后者生成Proto枚举；torch_type_to_ge_type按torch.dtype对象比较，支持None返回None、未知对象抛RuntimeError。不能因函数形参都标int，就互换这两种辅助函数的输入域；例如数值1映射INT8，5映射FLOAT16，296/297映射两类FLOAT4。

主线对象翻译辅助函数比发布版多可选float4_e2m1fn_x2名称判断；数值翻译中两版已有296/297。这只说明类型翻译存在，不给具体Cast/量化kernel、Torch安装版本或产品增加支持。

## npu_dtype_cast的FP4展开和打包

| 步骤 | 本层行为 |
| --- | --- |
| input_dtype为296/297 | 从Shape(self)与[1,...,1,2]相乘得到展开shape，Bitcast为对应低比特类型再Reshape；不是普通数值Cast。 |
| 其他非None input_dtype | 直接改self.desc.dtype为Proto类型，没有数据转换节点，不能用于任意数值重编码。 |
| 目标dtype | 先Cast至数值翻译后的GE类型，再设置out.desc.dtype。 |
| 目标285(INT4)或296/297(FP4) | Shape(out)沿最后轴除2，追加分量轴2后Reshape，Bitcast为UINT8，再Reshape成减半的末轴，返回字节封装对象。不能直接从逻辑目标dtype推断返回图对象就是同样存储格式。 |

局部代码没有完整rank、末轴偶数或底层打包格式校验；空/奇数末轴及动态shape需按真实ABI核对。本层写desc与Bitcast、Cast语义不同，不能为消除转换成本任意替换。

## 反向和旧入口不完全对称

npu_dtype_cast_backward.default的grad_dtype非None时，296/297先按相似路线展开，其余仅改self.desc.dtype。input_dtype非None时按其数值类型Cast并改Proto描述符，但输出打包只对296/297执行，**没有前向dtype==285的同样打包条件**；input_dtype=None时改为torch_type_to_ge_type(dtype)对象翻译后Cast。

旧torch.ops.npu._npu_dtype_cast.default与_npu_dtype_cast_backward.default均只经torch_type_to_ge_type(dtype)再Cast，不自动共享新入口的input_dtype/grad_dtype、描述符与FP4打包合同。要按实际FX入口区分，不按相似名字合并。

## 反量化、QuantMax和索引写回

npu_dequant_bias.default在output_dtype=None时默认GE FLOAT16；否则用对象翻译，然后ge.dequant_bias(x,weight_scale,activate_scale,bias,output_dtype=...)。它没有按Meta默认选择输出精度，也没有在此层证明scale公式或所有bias广播。

主线npu_quant_max.default把dst_dtype数值翻译后传QuantMax，并设置y.desc.dtype，amax原样返回。默认dst_dtype=291对应FLOAT8_E5M2；round_mode默认rint，group_list可选，均没有完整本地值域和分组校验。设置y描述符不说明amax同样dtype；发布同路径缺失不作能力否定。

npu_gather_backward.default以self_size及grad.dtype的0构造Fill，再ScatterElements(zero,index,grad,axis=dim,reduction=add)。sparse_grad形参未被使用，没有本地统一index Cast或稀疏结果分支；不能从形参存在认证稀疏梯度。

npu_scatter_list.default对var列表**逐项TensorMove**后传ScatterList，indice/updates/mask及reduce/axis原样透传。来源警告提到意外输入修改，本层拷贝不能为消除搬运任意删除；也不能仅凭这些拷贝认证外围所有别名、mask和重复索引语义。reduce默认update、axis默认-2，不等于所有字符串与维度都经过完整校验。

优化前核对逻辑dtype与封装字节、形状扩缩、描述符副作用、前反向入口以及真实写回对象；验证数值、精度、别名和索引范围后再测性能。本次未执行。

## 准确映射清单

仅列所选文件实际注册，有构图分支不证明全部参数或产品可用；未声明的其他重载不作能力否定。

| 文件主题 | 准确入口 |
| --- | --- |
| npu_dequant_bias | `torch.ops.npu.npu_dequant_bias.default` |
| npu_dtype_cast | `torch.ops.npu.npu_dtype_cast.default`、`torch.ops.npu._npu_dtype_cast.default` |
| npu_dtype_cast_backward | `torch.ops.npu.npu_dtype_cast_backward.default`、`torch.ops.npu._npu_dtype_cast_backward.default` |
| npu_gather_backward | `torch.ops.npu.npu_gather_backward.default` |
| npu_quant_max | `torch.ops.npu.npu_quant_max.default` |
| npu_scatter_list | `torch.ops.npu.npu_scatter_list.default` |

## op-plugin eager 侧 npu_scatter_list 实现层

上文记录 converter 侧逐项 TensorMove；本节补 eager 侧 `ScatterListKernelNpuOpApi.cpp`（57 行，两 pin 语义等价仅排版差，读毕）。非原地 `npu_scatter_list(self, indice, updates, mask, reduce, axis)` 先把 self 列表**逐 Tensor `clone()`** 组成新 TensorList 再交 `EXEC_NPU_CMD(aclnnScatterList, ...)`——eager 侧同样存在每项拷贝，与本卡 converter 侧结论互补：这些拷贝不能为消除搬运而随意删除。原地 `npu_scatter_list_` 直接以原 TensorList 执行、无 clone。`reduce` 以 `char*` 透传，源注释明示 ScatterList 的 reduce 属性**只支持 'update'**；indice/updates/mask/axis 原样透传。设备侧 ScatterList 对重复索引与 mask 的语义未读。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_bias.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_bias.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dtype_cast.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dtype_cast.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dtype_cast_backward.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dtype_cast_backward.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gather_backward.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_gather_backward.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_max.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_list.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_scatter_list.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（implementation）

- [ScatterListKernelNpuOpApi.cpp 两 pin](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScatterListKernelNpuOpApi.cpp)（implementation）：全文 57 行（全读）；发布仅缩进排版差。

---
type: Guide
title: GE推理准备：模型权重私有格式与量化参数改写
description: 说明两版模型层权重与量化scale原位替换的类型门槛、递归及失败状态。
tags:
- task.optimization
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/experimental/inference.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/experimental/inference.py
  role: primary
created_at: '2026-11-12T01:57:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE推理准备：模型权重私有格式与量化参数改写

`use_internal_format_weight(model)` 遍历模型，按模块类型替换weight.data或量化scale.data。它是编译前的状态修改，与[GE运行期描述符绑定](torchair_ge_frozen_placeholder_runtime_binding.md)分开；固定主线92e1e967与发布7c6c754b所列条件相同，没有执行模型、格式转换或设备实验。

| 模块分支 | 门槛与修改 |
| --- | --- |
| torch.nn.Conv2d子类 | weight及data非None；CPU权重报错；groups>1或非FP16则返回本次模块处理，否则format_cast到4（FRACTAL_Z） |
| torch.nn.Linear子类 | CPU权重报错，然后format_cast到29（FRACTAL_NZ）；本分支没有Conv的weight非None保护或dtype筛选 |
| 已加载DeepSpeed的LinearLayer/LinearAllreduce子类 | CPU权重报错，format_cast到29 |
| LinearA8W8Quant | 先npu_trans_quant_param(scale,offset)替换scale.data；设备名包含Ascend310P才将weight到29 |
| LinearQuant | weight到29 |
| LinearWeightQuant | quant_scale非None时按可选quant_offset转量化参数；设备名包含Ascend310P或Ascend910B时weight到29 |
| 可得QuantConv2d类型 | weight及data非None、非CPU、groups<=1且INT8时weight到4；随后仅scale为FP32才转量化参数 |

这些是代码的类型/字符串门控，不是额外产品支持矩阵。QuantConv先改weight再检查scale.dtype，不因后者不匹配就回滚weight。若多个独立if同时匹配，同一模块可能依次经过多个分支；本地没有记录“已转换”或统一撤销之前赋值。

入口只检查torch_npu是否已在sys.modules，缺少时记录error并返回，不主动导入。取已加载模块保存到全局；DeepSpeed存在时也保存全局引用，但本函数没有在其后来从sys.modules移除时把旧引用清None。部分contrib类型路径被直接访问，只有QuantConv的类型包做局部hasattr，不能说所有缺少可选类都自动跳过。

递归先处理当前模块再遍历model.children()。`if not model.children`检查的是该属性本身，不是先构造子模块列表判空；没有孩子时最终由迭代为空自然结束。函数没有在这里按共享weight存储去重，或对全部层做两阶段验证后再统一写入。

在准备固定地址权重时，应先完成需要的设备/私有格式转换，再建立匹配的编译图与地址承诺，见[固定地址契约](../../../optimizations/rules/frozen_parameter_address_contract.md)。`weight.data = ...`不是保持原存储地址的证明；重复调用也没有本地幂等标记。主线同模块另导出CPU格式转换助手，发布没有该Python入口，详见[CPU到NZ转换](torchair_int8_nz_cpu_format_conversion.md)。

## 实现来源

- [固定实现1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/experimental/inference.py)：1–126。
- [固定实现2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/experimental/inference.py)：1–107。

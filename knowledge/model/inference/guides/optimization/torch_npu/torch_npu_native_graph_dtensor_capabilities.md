---
type: Guide
title: 入图与DTensor清单：逐接口交集和产品脚注
description: 逐名比较两份固定清单，区分Eager、编译入图和分片能力，保留产品及版本限制。
tags:
- task.lookup
- topic.compilation
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/graph_supported_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/graph_supported_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/dtensor_supported_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/dtensor_supported_apis.md
  role: constraint
created_at: '2026-11-09T14:18:23Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 入图与DTensor清单：逐接口交集和产品脚注

## 固定来源和能力维度

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的中英文未分版本原生API附录。DTensor清单列186个入口，入图清单列181个，准确名称的交集142个，另有44个仅DTensor列出、39个仅入图列出。以下是两个独立支持声明的交叉整理，不是把同名别名、Tensor方法与torch函数合并后的统计。

入图在来源中指可被torch.compile计算图捕获并参与优化，不特指原生NPUGraph捕获重放或TorchAir某个后端的全部能力。DTensor是Tensor子类，按SPMD通过DeviceMesh及Shard/Replicate/Partial表达分布式布局。Eager实现、编译前端/后端与DTensor分发是独立条件。

本指南涉及A2/A3训练系列与950DT的明确脚注，不包含950PR。未分版本清单没有逐项产品、dtype、layout、placement和完整版本矩阵；“共同列出”尤其不证明某个DTensor输入同时可在某后端编译，不能推成所有产品/参数组合均支持。“仅一份清单列出”表示另一份未收录，不表示已证实不支持。未列的API可能也有能力，来源表示尚待验证；来源已验证不等于本仓设备复测。

## 准确名称的清单交叉表

| API分组 | 清单交叉关系 | 名称 |
| --- | --- | --- |
| Tensor索引与归约 | 仅入图清单列出 | `Tensor.argmax`、`Tensor.argmin`、`Tensor.index_add`、`Tensor.index_fill`、`Tensor.index_put` |
| Tensor索引与归约 | 共同列出 | `Tensor.all`、`Tensor.any`、`Tensor.cumsum`、`Tensor.gather`、`Tensor.histc`、`Tensor.index_select`、`Tensor.masked_fill`、`Tensor.max`、`Tensor.maximum`、`Tensor.mean`、`Tensor.min`、`Tensor.minimum`、`Tensor.scatter_`、`Tensor.scatter_add`、`Tensor.sort`、`Tensor.sum`、`Tensor.topk` |
| Tensor几何与视图 | 仅DTensor清单列出 | `Tensor.flatten`、`Tensor.permute`、`Tensor.reshape`、`Tensor.squeeze`、`Tensor.transpose`、`Tensor.unsqueeze`、`Tensor.view_as` |
| Tensor几何与视图 | 仅入图清单列出 | `Tensor.repeat_interleave`、`Tensor.roll` |
| Tensor几何与视图 | 共同列出 | `Tensor.copy_`、`Tensor.repeat`、`Tensor.where` |
| Tensor数学方法 | 仅DTensor清单列出 | `Tensor.add_`、`Tensor.addcdiv_`、`Tensor.addcmul_`、`Tensor.div_`、`Tensor.isnan`、`Tensor.mul_`、`Tensor.sub_` |
| Tensor数学方法 | 仅入图清单列出 | `Tensor.ne` |
| Tensor数学方法 | 共同列出 | `Tensor.abs`、`Tensor.add`、`Tensor.addmm`、`Tensor.bitwise_and`、`Tensor.bitwise_not`、`Tensor.bitwise_or`、`Tensor.bmm`、`Tensor.clamp`、`Tensor.cos`、`Tensor.div`、`Tensor.eq`、`Tensor.ge`、`Tensor.gt`、`Tensor.le`、`Tensor.log2`、`Tensor.logical_and_`、`Tensor.logical_not`、`Tensor.lt`、`Tensor.matmul`、`Tensor.mm`、`Tensor.mul`、`Tensor.neg`、`Tensor.pow`、`Tensor.reciprocal`、`Tensor.remainder`、`Tensor.rsqrt`、`Tensor.sigmoid`、`Tensor.sign`、`Tensor.sin`、`Tensor.softmax`、`Tensor.sqrt`、`Tensor.sub`、`Tensor.tril`、`Tensor.triu` |
| Tensor填充与转换 | 共同列出 | `Tensor.fill_`、`Tensor.to` |
| Tensor随机方法 | 共同列出 | `Tensor.exponential_`、`Tensor.uniform_` |
| Tensor运算符 | 仅DTensor清单列出 | `Tensor.__add__`、`Tensor.__bool__`、`Tensor.__eq__`、`Tensor.__ge__`、`Tensor.__gt__`、`Tensor.__iadd__`、`Tensor.__imul__`、`Tensor.__isub__`、`Tensor.__mul__`、`Tensor.__or__`、`Tensor.__pow__`、`Tensor.__radd__`、`Tensor.__rmul__`、`Tensor.__setitem__`、`Tensor.__sub__`、`Tensor.__truediv__` |
| TorchNPU专用入口 | 仅DTensor清单列出 | `torch_npu.npu_apply_adam_w`、`torch_npu.npu_conv2d`、`torch_npu.npu_cross_entropy_loss`、`torch_npu.npu_grouped_matmul_add_` |
| TorchNPU专用入口 | 共同列出 | `torch_npu.npu_add_rms_norm`、`torch_npu.npu_all_gather_base_mm`、`torch_npu.npu_dtype_cast`、`torch_npu.npu_fusion_attention`、`torch_npu.npu_grouped_matmul`、`torch_npu.npu_mm_reduce_scatter_base`、`torch_npu.npu_moe_token_permute`、`torch_npu.npu_moe_token_unpermute`、`torch_npu.npu_rms_norm`、`torch_npu.npu_rotary_mul`、`torch_npu.npu_swiglu` |
| torch梯度模式 | 仅入图清单列出 | `torch.no_grad` |
| torch创建函数 | 仅DTensor清单列出 | `torch.ones`、`torch.ones_like` |
| torch创建函数 | 共同列出 | `torch.arange`、`torch.zeros` |
| torch索引与归约 | 仅DTensor清单列出 | `torch.histc`、`torch.norm` |
| torch索引与归约 | 仅入图清单列出 | `torch.argmax`、`torch.argmin`、`torch.index_add`、`torch.ne` |
| torch索引与归约 | 共同列出 | `torch.all`、`torch.any`、`torch.cumsum`、`torch.eq`、`torch.gather`、`torch.ge`、`torch.gt`、`torch.index_select`、`torch.le`、`torch.lt`、`torch.masked_fill`、`torch.max`、`torch.maximum`、`torch.mean`、`torch.min`、`torch.minimum`、`torch.scatter`、`torch.scatter_add`、`torch.sort`、`torch.sum`、`torch.topk` |
| torch几何与视图 | 仅DTensor清单列出 | `torch.chunk`、`torch.repeat_interleave`、`torch.split` |
| torch几何与视图 | 仅入图清单列出 | `torch.roll` |
| torch几何与视图 | 共同列出 | `torch.cat`、`torch.stack`、`torch.tril`、`torch.triu`、`torch.where` |
| torch数学函数 | 仅入图清单列出 | `torch.floor_divide`、`torch.rsub`、`torch.threshold` |
| torch数学函数 | 共同列出 | `torch.abs`、`torch.add`、`torch.bitwise_and`、`torch.bitwise_not`、`torch.bitwise_or`、`torch.clamp`、`torch.cos`、`torch.div`、`torch.exp`、`torch.fill_`、`torch.log`、`torch.logical_not`、`torch.mul`、`torch.neg`、`torch.pow`、`torch.reciprocal`、`torch.remainder`、`torch.rsqrt`、`torch.sigmoid`、`torch.sign`、`torch.sin`、`torch.softmax`、`torch.sqrt`、`torch.sub` |
| torch矩阵函数 | 共同列出 | `torch.addmm`、`torch.bmm`、`torch.convolution`、`torch.embedding`、`torch.matmul`、`torch.mm` |
| torch随机函数 | 仅入图清单列出 | `torch.normal` |
| torch其他入口 | 仅入图清单列出 | `torch._foreach_copy_`、`torch.device`、`torch.dropout`、`torch.index_fill`、`torch.index_put` |
| torch其他入口 | 共同列出 | `torch._fused_adamw_`、`torch._log_softmax`、`torch._softmax_backward_data`、`torch.constant_pad_nd`、`torch.index`、`torch.linalg.vector_norm`、`torch.logical_and_`、`torch.native_dropout`、`torch.relu` |
| 模块与functional | 仅DTensor清单列出 | `torch.nn.functional.embedding`、`torch.nn.functional.linear`、`torch.nn.functional.pad` |
| 模块与functional | 仅入图清单列出 | `torch.nn.functional.cross_entropy`、`torch.nn.functional.scaled_dot_product_attention` |
| 模块与functional | 共同列出 | `torch.nn.GELU`、`torch.nn.functional.layer_norm`、`torch.nn.functional.mse_loss`、`torch.nn.functional.one_hot`、`torch.nn.functional.silu`、`torch.nn.functional.softmax` |
| 集合通信与进程组 | 仅入图清单列出 | `torch.distributed.ReduceOp`、`torch.distributed._all_gather_base`、`torch.distributed._reduce_scatter_base`、`torch.distributed.all_gather`、`torch.distributed.all_gather_into_tensor`、`torch.distributed.all_reduce`、`torch.distributed.all_to_all_single`、`torch.distributed.get_process_group_ranks`、`torch.distributed.get_rank`、`torch.distributed.get_world_size`、`torch.distributed.init_process_group`、`torch.distributed.is_gloo_available`、`torch.distributed.reduce_op`、`torch.distributed.reduce_scatter_tensor` |


## 产品和版本脚注优先

入图清单对A2/A3在PyTorch2.7.1排除torch.device及functional.cross_entropy。950DT的functional.scaled_dot_product_attention在2.7.1、2.9、2.10、2.11、2.12、2.13、2.14均不支持入图；清单未列2.8，不补推其结论。专用npu_fusion_attention被列出不覆盖原生SDPA入口的脚注。

torch._foreach_copy_虽在入图名单，私有支持页仍对950明确暂不支持；普通产品、dtype、版本与编译条件需共同核对，不能只凭此名单单独选中该产品。DTensor名单包含的原地方法、索引赋值及运算符也不自动证明任意别名、副作用、梯度或分片组合合法。

## 组合前的验收

先核对准确API和实际配套版本，再核对产品、dtype/shape、placement、本地shape和通信域。随后分别建立Eager、DTensor前后向参考与具体编译后端的捕获/输出证据，覆盖重编译、状态更新和通信，再测端到端性能。本次没有执行上游、DTensor、编译或设备实验。

- [张量并行与DTensor参数范围](../../../../training/guides/torch_npu_native_tensor_parallel_constraints.md)
- [图后端职责与模式限制](../../../concepts/frameworks/torchair_backend_boundaries.md)
- [原生NPUGraph的推理和方法边界](torch_npu_native_graph_support_scope.md)
- [SDPA接口](../../../../training/apis/torch_npu/scaled_dot_product_attention.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/graph_supported_apis.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/graph_supported_apis.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/dtensor_supported_apis.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/dtensor_supported_apis.md)（constraint）

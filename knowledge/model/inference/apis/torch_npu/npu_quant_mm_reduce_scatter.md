---
type: API
title: npu_quant_mm_reduce_scatter：反量化矩阵乘与归约散射
description: 说明 M 轴整除、平台通信默认值、MXFP4 配对参数和 amax 文档与 Meta 差异。
tags:
- task.lookup
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_mm_reduce_scatter.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMatmulReduceScatterKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_reduce_scatter_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_mm_reduce_scatter.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_mm_reduce_scatter.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantMatmulReduceScatterKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_mm_reduce_scatter.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_reduce_scatter_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
created_at: '2026-11-09T07:58:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# npu_quant_mm_reduce_scatter：反量化矩阵乘与归约散射

## 版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整产品/参数页及包装实现；图转换另核对TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`。支持训练与推理，页面提供图模式说明/示例，但这两个主线快照未获得跨仓兼容或设备验证证明。950证据仅列950DT，不能扩大到950PR。发布来源组合没有由本卡推定新增接口兼容。

## 接口与输出

```text
npu_quant_mm_reduce_scatter(Tensor self, Tensor x2, str hcom, int world_size, *, str reduce_op='sum', Tensor? bias=None, Tensor? x1_scale=None, Tensor? x2_scale=None, Tensor? quant_scale=None, int block_size=0, int comm_turn=0, int[]? group_sizes=None, bool amax_output=False, int? y_dtype=None, int? x1_dtype=None, int? x2_dtype=None, int? x1_scale_dtype=None, int? x2_scale_dtype=None, str? comm_mode=None) -> (Tensor, Tensor)
```

公开入口为torch_npu.npu_quant_mm_reduce_scatter；先完成本rank的矩阵乘、对应反量化和可选bias，再ReduceScatter。reduce_op当前仅sum，不能用它表达平均。self连续ND [m,k]，x2逻辑[k,n]且只允许由转置产生的非连续；m必须整除world_size，k∈[256,65535)。返回(output,amax)，output=[m/world_size,n] ND。

bias在归约之前加入，本rank重复完整bias会在sum中累计；需按模型并行语义准备bias，不能把融合调用直接等同于归约完成后只加一次bias。

## 产品与通信模式

|产品|输入、卡数与格式|通信及空输入|
|--|--|--|
|A2/A3|FP16/BF16/INT8；2/4/8卡；x2可ND/FRACTAL_NZ|默认及唯一aiv，缓冲区≥200MB，不支持空Tensor|
|950DT|FP16/BF16/FP8 E4M3/E5M2/HiF8/MXFP4；2..64的2次幂；x2仅ND|默认ai_cpu，可ccu；仅FP16/BF16路径允许空m/n，k不可空|

950DT ccu限单机UB域，ai_cpu可跨机UB域；ReduceScatter通信总量m*n*输出元素字节数≤63*256MB，某些shape更严。FP8的E4M3/E5M2可混用，其余路径两输入同dtype；不能由广义950支持推断950PR支持。

## 反量化参数

|量化路径|x1_scale|x2_scale（逻辑K×N右矩阵）|
|--|--|--|
|A2/A3 INT8 pertoken/perchannel|FP32 [m,1]|[1,n]，dtype另按接口限制|
|950DT pertensor FP8/HiF8|FP32 [1]|FP32 [1]|
|950DT perblock FP8/HiF8|FP32 [ceil(m/128),ceil(k/128)]|FP32 [ceil(k/128),ceil(n/128)]|
|950DT MX FP8/FP4|E8M0 [m,ceil(k/64),2]|非转置[ceil(k/64),n,2]；转置存储[n,ceil(k/64),2]|

量化方式由scale形状决定，group_sizes只描述反量化分组；它与仅支持0的输出量化block_size不是同一参数。FP16/BF16输入时两scale必须None。低精度输出应显式y_dtype=FP16/BF16/FP32；FP16/BF16输入则保持相同输出dtype。

A2/A3 x2_scale INT64仅FP16输出时支持；x1_scale为FP32。A2/A3 bias为[n]：INT8输入可FP16/BF16/FP32，浮点输入可同输入dtype或FP32。950DT低精度pertensor/MX bias需FP32，perblock只None；普通FP16/BF16路径采用与输入同dtype的共同支持范围。

quant_scale当前仅None，block_size和comm_turn仅0。group_sizes使用[M,N,K]三个0..65535值，950DT典型perblock[128,128,128]、MX[1,1,32]；A2/A3仅零分组。页面一处称必须传三项，签名和实现又允许None；C++None/空列表都编码0，GE Converter对显式空列表报错，采用None或平台允许的三项零列表。

## MXFP4与amax差异

MXFP4需同时提供x1_dtype/x2_dtype=FP4以及两个scale dtype=E8M0，缺一不可。物理打包区分两种右矩阵：非转置时C++检查self.size(1)*2==x2.size(0)，输出N=x2.size(1)*2；转置视图时物理K轴检查相等且N不翻倍。只按逻辑k/n套普通MatMul形状会分配错误。文档K需偶数，非转置N亦需偶数。

amax_output的参数/返回段描述True生成FP32[1]，但示例注明当前仅False，且Meta不论开关始终生成0元素FP32；C++True却分配[1]再下发。保留此冲突，本卡只推荐共同明确的False路径，不据C++有分支就宣称True可入图。False下C++使用未定义Tensor占位，不能假设它具有与Meta相同的可访问shape。

## 验证与配套

确认真实hcom、rank顺序、world_size、各rank输入/scale切分一致，比较通信展开后的参考和融合输出；同时核对返回项dtype、物理shape和无效输出。包装只下发V2 aclnn接口，没有由本卡确认旧接口兼容回退，需核对实际CANN交付件。默认确定性实现是页面契约，不是本次重复实验结果；训练场景支持也不替代具体autograd/梯度路径的核对。本次未执行上游代码或NPU多卡测试。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 发布CCU固定值与主线平台默认值

发布Schema、Meta和GE无comm_mode参数，C++固定ccu；主线增加该参数，C++及GE才按平台选择A2/A3默认aiv、950默认ai_cpu。发布未含主线MXFP4物理K/N修正、四类型配对检查和GE的形状扩展，不能回推新低精度布局。

C++的group helper把None或空列表编码0，并检查非空三项0..65535；两GE显式空列表都因长度不是3而拒绝，公共路径使用None或公开平台允许的三项值。默认确定性与训练/推理是页面契约，不等于梯度或跨模式兼容已实测。

主线GE的MXFP4对任一单端标记都要求双端FP4与双scale E8M0齐全，通过Bitcast及形状扩展解释容器；这与普通INT8数值转换不同。两版GE在y_dtype=None时对最终描述另用值1，BF16默认分支的输出描述需独立核对。amax=True的Meta/C++差异继续保留，不由GE透传开关宣布已入图验证。

两版测试逐字节相同、只选950八卡FP16无scale，却把二元组返回值直接调用cpu，结果进入比较之前即有返回处理错误。该测试不能证明任何量化、amax、空输入、偏置累加或新FP4协议；也未执行设备/多进程测试。bias在各rank局部反量化后、跨rank求和前，逐rank完整复制bias会随sum累计，不能等同于最终输出只加一次。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_mm_reduce_scatter.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantMatmulReduceScatterKernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_reduce_scatter_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_mm_reduce_scatter.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_mm_reduce_scatter.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantMatmulReduceScatterKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_mm_reduce_scatter.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/matmul_reduce_scatter_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）

---
type: API
title: npu_all_gather_quant_mm：量化 AllGather 与矩阵乘融合
description: 区分 A2/A3 的 aiv 与 950DT 低精度路径，说明输出、分组和 FP4 物理存储。
tags:
- task.lookup
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_gather_quant_mm.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllGatherQuantMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/all_gather_matmul_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_all_gather_quant_mm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_all_gather_quant_mm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllGatherQuantMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_all_gather_quant_mm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/all_gather_matmul_v2.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
created_at: '2026-11-09T07:58:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# npu_all_gather_quant_mm：量化 AllGather 与矩阵乘融合

## 版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整产品/参数页及包装实现；图转换另核对TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`。支持训练与推理，页面提供图模式说明/示例，但这两个主线快照未获得跨仓兼容或设备验证证明。950证据仅列950DT，不能扩大到950PR。发布来源组合没有由本卡推定新增接口兼容。

## 接口与通信顺序

```text
npu_all_gather_quant_mm(Tensor self, Tensor x2, str hcom, int world_size, *, Tensor? bias=None, Tensor? x1_scale=None, Tensor? x2_scale=None, Tensor? quant_scale=None, int block_size=0, int gather_index=0, bool gather_output=True, int comm_turn=0, int[]? group_sizes=None, bool amax_output=False, int? y_dtype=None, int? x1_dtype=None, int? x2_dtype=None, int? x1_scale_dtype=None, int? x2_scale_dtype=None, str? comm_mode=None) -> (Tensor, Tensor, Tensor)
```

公开入口为torch_npu.npu_all_gather_quant_mm；先AllGather左矩阵，再与右矩阵做MatMul并按路径反量化。self逻辑[m,k]且不转置，x2为逻辑[k,n]、仅转置视图允许非连续。k∈[256,65535)，m/n≤2147483647。文档某处写转置形状[n,k]，实际C++以x2.size(1)作为输出列，需区分底层转置存储与传入Tensor的逻辑视图，不能直接传相反逻辑K轴。

返回(y,gather_out,amax)：y逻辑[m*world_size,n]；gather_output=True时gather_out为AllGather后的输入存储，False为空。gather_index当前仅0，gather_output=False仍执行通信，并不是取消AllGather。

## 产品与通信配置

|产品|输入/卡数|必须单独核对的条件|
|--|--|--|
|A2/A3|FP16/BF16/INT8/INT4，2/4/8卡|comm_mode显式aiv；bias=None；不支持空Tensor；通信缓冲区≥200MB；INT4的k/n为偶数|
|950DT|FP16/BF16、FP8 E4M3/E5M2、HiF8、MXFP4，2/4/8/16/32/64卡|ai_cpu或ccu；FP8两格式可混用，其余两输入同dtype；m/n可空，k不可空|

C++对comm_mode=None统一用ai_cpu，未按A2/A3改默认；因此A2/A3必须显式aiv。950DT ccu仅单机UB域，ai_cpu可跨机UB域；ccu的AllGather总量m*k*元素字节数*卡数不能超过63*256MB，实际shape可能更严。

## scale、bias与预留参数

|量化路径|x1_scale|x2_scale（逻辑K×N右矩阵）|
|--|--|--|
|A2/A3 INT8 pertoken/perchannel|FP32 [m,1]|[1,n]，dtype另按接口限制|
|950DT pertensor FP8/HiF8|FP32 [1]|FP32 [1]|
|950DT perblock FP8/HiF8|FP32 [ceil(m/128),ceil(k/128)]|FP32 [ceil(k/128),ceil(n/128)]|
|950DT MX FP8/FP4|E8M0 [m,ceil(k/64),2]|非转置[ceil(k/64),n,2]；转置存储[n,ceil(k/64),2]|

量化方式由scale形状决定，group_sizes只描述反量化分组；它与仅支持0的输出量化block_size不是同一参数。FP16/BF16输入时两scale必须None。低精度输出应显式y_dtype=FP16/BF16/FP32；FP16/BF16输入则保持相同输出dtype。

A2/A3 x2_scale可FP32或INT64，INT64只在页面所列INT8输入或FP16输出条件使用，不能当普通整数scale。950DT浮点输入bias与输入同dtype；低精度pertensor/MX bias为FP32，perblock必须None；A2/A3所有路径bias必须None。公式中的bias位置随路径说明不同，不能把低精度bias直接当普通浮点MatMul的bias复用。

quant_scale=None、block_size=0、gather_index=0、comm_turn=0、amax_output=False是当前公开限制；amax不是可直接开启的校准输出。group_sizes按[M,N,K]三个0..65535值编码(K | N<<16 | M<<32)，950DT二维以上scale才有意义，0由shape推导，典型perblock[128,128,128]、MX[1,1,32]。A2/A3页面只支持None。C++接受None/空列表为0，而主线GE Converter拒绝非None空列表，跨模式采用共同有效的None。

## FP4与无效输出的边界

FP4通常以每字节两值承载；x1_dtype/x2_dtype和两个E8M0 scale dtype提示是解释存储，不会转换/量化数据。C++校验提示dtype与底层itemsize一致；MXFP4非转置x2的输出N按x2.size(1)*2分配，gather_out仍保留输入的物理打包shape，不能按逻辑K申请双倍物理空间。K需偶数，x2非转置时N也需偶数。

关闭amax时C++使用未定义Tensor占位，Meta固定返回0元素FP32；不能将文档“空Tensor”推断成所有执行路径都可直接访问其shape/device。关闭gather时C++确实分配0元素Tensor，两种无效输出的存储语义分别处理。主线GE另有FP4 Bitcast/Reshape与回打包，必须验证实际图输出规格，不以dtype枚举出现当作全路径验证。

## 验证与配套

确认真实hcom、rank顺序、world_size、各rank输入/scale切分一致，比较通信展开后的参考和融合输出；同时核对返回项dtype、物理shape和无效输出。包装只下发V2 aclnn接口，没有由本卡确认旧接口兼容回退，需核对实际CANN交付件。默认确定性实现是页面契约，不是本次重复实验结果；训练场景支持也不替代具体autograd/梯度路径的核对。本次未执行上游代码或NPU多卡测试。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 发布签名差异与图描述检查

发布Schema、Meta、C++和GE均无comm_mode参数，C++固定使用ccu；主线才新增可选参数且C++默认ai_cpu。不能把主线A2/A3显式aiv的写法回推为发布签名可接受。发布也没有主线的MXFP4非转置N翻倍、Gather回打包及相同itemsize校验；存在旧V2入口不等于这些新存储协议均已可用。

主线GE额外验证卡数及MXFP4两数据与双scale类型，并对uint8物理容器做Bitcast/Reshape，再将Gather输出转回打包容器。该路径是位解释，不会生成量化数据。两版GE都在y_dtype=None时先按输入决定GE输出类型，随后把y_dtype设为1用于最终描述；默认BF16的实际图输出描述仍需检查，不能只看Meta形状。

公开量化模式由尺度shape隐式决定，所有rank须传各自本地左尺度并保持右尺度语义一致。perblock与MX公式里的求和上界按页保留，不直接生成一个忽略尾块或物理编码的通用参考实现。

## 测试返回项错误与零值FP4的局限

两版旧测试只用FP16、没有量化尺度，却将三返回值接口拆成两个变量；主线新增两卡950 MXFP4零输入测试也仍只接两个返回值。它们在结果比较前就存在解包问题，不构成有效多卡数值证明。零值FP4、固定尺度和单种非转置布局即使修正解包，也不能证明非零打包、尾块、混合FP8、bias或所有quant模式。

C++可为amax=True分配[1]，Meta却固定0元素，而本接口公开只支持False；不据实现分支开启未公开校准输出。False的未定义Tensor与真实空Gather Tensor也继续区分。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_all_gather_quant_mm.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllGatherQuantMatmulKernelNpuOpApi.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/all_gather_matmul_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_all_gather_quant_mm.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_all_gather_quant_mm.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllGatherQuantMatmulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_all_gather_quant_mm.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/all_gather_matmul_v2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

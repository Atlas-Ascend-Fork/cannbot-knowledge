---
type: API
title: npu_grouped_matmul_swiglu_quant：融合GMM、SwiGLU与动态INT8量化
description: 区分固定主线及发布版V1的A8W8/A8W4、NZ布局、有效前缀和输出尺度；950扩展按中文产品条款限定。
tags:
- task.optimization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_swiglu_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_swiglu_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulSwigluQuantNpuOpapi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_grouped_matmul_swiglu_quant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedMatmulSwigluQuantNpuOpapi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_grouped_matmul_swiglu_quant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-10T01:53:04Z'
updated_at: '2026-11-10T01:55:36Z'
platforms:
- a2
- a3
- '950'
---

# npu_grouped_matmul_swiglu_quant：融合GMM、SwiGLU与动态INT8量化

## 版本与适用产品

本卡为OpPlugin V1公开接口协议，固定主线d84e9b1d6a558e5f27973cd4329f62968e46fdda及发布dedc316708372c9a8bfde4527abd2a94b74840f5。发布来自ascend_26_0_pt28组合，主线配套未确认。主线英文页仅列Atlas A2/A3，中文页还明确列Ascend950系列（包含旧称Atlas A5）的PR/DT，但950只支持A8W8、激活per-token与权重per-channel；不能把A2/A3的A8W4、per-group或INT64尺度扩到950。英文缺少950条款不作为明确不支持的证据。

接口为torch_npu.npu_grouped_matmul_swiglu_quant(x,weight,weight_scale,x_scale,group_list,bias=None,offset=None)，返回(output,output_scale,output_offset)。它把各专家的量化GMM、反量化、SwiGLU、逐token对称INT8量化融合。中文页明确Eager，Schema中的op_api/all_version及internal_format不构成所有历史版本或图后端可用证据；两固定TorchAir中没有找到对应V1转换器，不从V2转换器推导V1图支持。文档声明适用训练和推理，但这里没有新增梯度实现或训练验证。

## 分组与有效输出前缀

x为INT8 ND[M,K]；x_scale为FP32[M]；group_list为INT64[E]的累计行边界，允许空专家。例如[3,4,4,6]表示四专家分别处理3、1、0、2行，不能当作独立行数。边界非递减且末值不超过M，按边界顺序取各专家的权重和尺度。

output分配INT8[M,N/2]，output_scale分配[M]；只有[0,group_list[-1])前缀有效，尾部未初始化，不能因为返回shape为M便读取或比较全部行。output_offset是预留FP32形状[]的标量占位，并非零元素Tensor；来源没有定义其有效数值，不能用于后续反量化。公开非原地语义不由返回shape代替校验。

文档样例的随机分组生成器在缩放到M后又强制严格递增，可能再次越过M；必须在最终结果上核对范围、非递减和末边界。空专家本来合法，不必人为改为严格递增。

## A2/A3的权重、尺度与物理NZ

A8W8：weight为INT8，逻辑[E,K,N]，页面要求呈现NZ的五维view[E,N/32,K/16,16,32]。A8W4：weight以INT32存储打包INT4，每个INT32装8个值，对应五维view[E,N/64,K/16,16,8]。真正的NZ物理存储须先通过相应格式转换形成，单纯view不能把ND数据变成NZ；C++也没有代调用者转换格式。

weight_scale支持per-channel[E,N]或per-group[E,K_group,N]；数据类型为FP32/FP16/BF16，文档把INT64限定在per-channel描述中，不据测试的per-group INT64张量扩展该条款。INT64编码尺度也不能用随机整数代替正确编码。x_scale是逐token的反量化尺度。文档允许非连续输入仍须满足物理存储和逻辑轴约定，不能只检查is_contiguous。

A8W8的K<65536；A8W4的K<20000；N<=10240。N同时是SwiGLU前两半总宽度，实际布局和对齐仍要满足页面要求，包装层的整数除2不构成任意奇数N受支持的证据。

## 950的逻辑view与存储另外限定

主线中文页的950分支仅INT8权重，logical view为三维[E,K,N]，物理格式仍为NZ，不能套A2/A3的五维view。x不转置，weight可不转置或转置：不转置存储为[E,ceil(N/32),ceil(K/16),16,32]；转置时逻辑stride为[K*N,1,K]，存储为[E,ceil(K/32),ceil(N/16),16,32]。

950要求N为正的64倍数、E<=1024、输入同设备；weight_scale仅二维per-channel且FP32/FP16/BF16，bias与offset均为None。这里没有950 A8W4、MXFP8或其他低精度协议。仓库中同名下游适配器的MXFP8规则不能替代本固定OpPlugin V1协议，也不能据其尺度[N,2]布局改写本接口。

## 尺度方向与A8W4辅助矩阵

A8W8先对每个专家做INT8整数矩阵乘，再乘x_scale和weight_scale反量化；沿N分成两半，对前半做SiLU后乘后半。对每行SwiGLU结果计算absmax，输出反量化尺度为absmax/127，INT8输出按127/absmax乘法量化并取整。因此output_scale是反量化系数，不能把它与倒数形式的量化乘子交换。来源没有为全零absmax提供独立验证的特殊值协议，不在此发明回退值。

A8W4仅在A2/A3条款内。bias是weightAssistMatrix，不能按普通线性层偏置处理：per-channel时为8*weight_scale*sum_k(weight)，per-group时为8*sum_k(weight[k]*scale[group(k)])。激活拆为high=floor(x/16)、low=(x&0xF)-8，恢复(highMM*16+lowMM+assist)*x_scale后再做SwiGLU和动态量化。A8W4需要合法辅助矩阵，A8W8要求bias=None；offset尚未支持，传None。

文档A8W4例中随机bias和随机INT64 weight_scale不构成正确辅助矩阵与尺度编码的构造方法。低位打包、符号扩展、专家轴和尺度轴都应与实际权重绑定，不能把随机形状示例当作离线量化配方。

## 主线与发布输出维数的变化

主线C++和Meta都从weight_scale最后一轴取得N；发布C++和Meta则从weight.size(2)取得N。发布测试的format_cast保留三维逻辑view，第三轴确实是N；不能据此称发布入口普遍失效。但若直接把主线文档的五维NZ view传给旧分配逻辑，第三轴已是分块K，不能假设输出分配仍相同。迁移时必须同时核对版本、逻辑view与输出N来源。

两版本都调aclnnGroupedMatmulSwigluQuantWeightNZ，没有在这层区分SoC。output_scale沿用x_scale的dtype分配，而公开x_scale要求FP32；Meta没有完整校验累计边界、dtype、辅助矩阵或NZ内容，其成功只表明推导得到输出描述。

## 验证现状与检查方法

发布测试仅一个标A2的数值方法且无条件skip；主线仍保留该skip，新增三个未skip的A2测试分别覆盖A8W8、INT32打包A8W4和per-group，但使用torch.empty未初始化输入，只检查shape/dtype，不算数值正确性、950或A3支持证明。per-group测试给INT64 scale、A8W4给empty bias，均不能覆盖公开尺度限定和辅助矩阵数值。

原数值参考在CPU做INT32矩阵乘、FP32反量化、前半SiLU门控及INT8量化，仅比较有效前缀，INT8绝对容差为1并比较output_scale；没有检验预留offset、全零行、950转置、A8W4数值或默认确定性。默认确定性是页面声明，不标为本次设备实测。本次只静态审阅，没有执行上游代码。

实际集成应先确认版本与产品，再检查分组边界、权重物理格式、尺度方向、辅助矩阵和有效前缀，分别比较融合前后输出及反量化结果；性能比较需另测完整MoE路径，不从融合名称推断端到端收益。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_swiglu_quant.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_grouped_matmul_swiglu_quant.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GroupedMatmulSwigluQuantNpuOpapi.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_grouped_matmul_swiglu_quant.py)（example）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GroupedMatmulSwigluQuantNpuOpapi.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_grouped_matmul_swiglu_quant.py)（example）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

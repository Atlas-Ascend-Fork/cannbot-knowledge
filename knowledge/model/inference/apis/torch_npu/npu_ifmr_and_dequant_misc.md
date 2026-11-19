---
type: API
title: npu_ifmr/npu_dequant_bias/npu_quant_matmul_dequant：量化校准与反量化杂项的Eager合同
description: IFMR校准走旧ACE算子且本地wrapper无字面TORCH_CHECK；dequant_bias限half/bfloat16并走无格式检查aclnn；quant_matmul_dequant由gen_opapi生成、Meta限2D fp16乘int8配1D fp32且trans=true要求先转置权重；官方用例多skip加机型门，dequant_bias用例golden自比不能作数值证据。
tags:
- task.lookup
- topic.precision
- topic.compute.quantization
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/IfmrKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/IfmrKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DequantBiasNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DequantBiasNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_ifmr.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_ifmr.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_quant_matmul_dequant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_quant_matmul_dequant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_dequant_bias.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_npu_dequant_bias.py
  role: example
created_at: '2026-11-12T07:54:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npu_ifmr/npu_dequant_bias/npu_quant_matmul_dequant：量化校准与反量化杂项的Eager合同

## 版本与范围

本卡成组覆盖三个量化杂项入口：npu_ifmr（PTQ 校准）、npu_dequant_bias、npu_quant_matmul_dequant（量化矩阵乘的 Eager 直调）。三个 schema 在主线 pin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 与发布 pin `dedc316708372c9a8bfde4527abd2a94b74840f5` 均注册：ifmr 为 `acl_op: all_version`（主线 6408–6410、发布 6138–6140），dequant_bias 为 `op_api: all_version`（主线 7035–7037、发布 6820–6822），quant_matmul_dequant 为 `op_api: all_version` 加 gen_opapi 生成块（主线 6769–6778、发布 6569–6578，两 pin 块内容一致，块末行即 exec 行）。ifmr 与 dequant_bias 实现文件两 pin 字节一致或仅排版差异（diff 核实）；test_ifmr.py 两 pin 字节一致（sha256 相同），test_npu_dequant_bias.py 两 pin 仅行尾空白差异（diff 核实）。三者均无官方 API 文档页、无 derivatives 反向接线（两 pin derivatives.yaml 对三名 rg 均零命中）。图内的反量化/QuantMax/索引写回与 matmul 降图消费已由[torchair GE dtype/scatter 指南](../../guides/optimization/torchair/torchair_ge_dtype_scatter_lowering.md)与[torchair GE matmul 指南](../../guides/optimization/torchair/torchair_ge_matmul_lowering.md)覆盖，本卡只记 torch_npu Eager 层合同。全部结论为静态源码阅读，未执行任何上游代码；不做模型归属或整模型性能承诺。

## npu_ifmr：ACE 校准入口

签名（两 pin 同文）：`npu_ifmr(Tensor data, Tensor data_min, Tensor data_max, Tensor cumsum, float min_percentile, float max_percentile, float search_start, float search_end, float search_step, bool with_offset) -> (Tensor, Tensor)`。实现（IfmrKernelNpu.cpp，两 pin 字节一致，57 行全文读毕）：两输出 scale/offset 都以 data_min 为模板、ACL_FORMAT_NCHW 分配；走旧 ACE 算子 IFMR（非 aclnn），search_start/search_end 打包成 float 数组属性 search_range 传入，min/max_percentile、search_step、with_offset 亦为属性。本地 Ifmr wrapper 全文无字面 TORCH_CHECK；shape、dtype、设备检查若存在，位于哪一层（OpCommand preparation、执行框架、设备侧 ACE 等）不在已读来源内，不据缺席断言其无，也不把剩余校验全部定位到 ACE 算子内部，不能据包装断言无任何检查。

官方基线用例（test_ifmr.py，两 pin 字节一致，150 行全文读毕）给出的调用约定与预期：jit_compile=True；fp32、ND 与 NCHW 两种格式、4D 与 2D 形状；min/max 以 `torch.min/max` 取值后 reshape 成 (1,)，cdf 用 CPU 上 `histc(bins=128)` 的 `cumsum` 转 int32 再上 NPU。golden 是 numpy 复刻的 IFMR 搜索（步进 [0.7,1.3)×0.01）：with_offset 时 scale=(max−min)/255 且下限 1.192092896e-07、offset=−(round(min/scale)+128)；否则 scale=max/127、offset=0。断言 scale 相对误差 <1e-4、offset 精确相等。用例口径是逐元素统计校准，不承诺 scale/offset 的设备端逐位一致。

## npu_dequant_bias：反量化偏置

签名：`npu_dequant_bias(Tensor x, Tensor weight_scale, Tensor? activation_scale, Tensor? bias, *, ScalarType? output_dtype=None) -> Tensor`。实现（DequantBiasNpuOpApi.cpp，主线 41 行、发布 39 行全文读毕，仅排版与尾换行差异）：output_dtype 缺省 Half；仅接受 Half/BFloat16，否则 PARAM 错误（报错文案 "The dtype should be half or bfloat16"）；输出按 x.sizes() 与目标 dtype 无格式分配；目标 dtype 经 convert_to_acl_data_type 转成整数枚举传入；执行走 `EXEC_NPU_NO_FORMAT_CHECK_CMD(aclnnDequantBias, ...)`（无格式检查变体）。Meta（两 pin 同文，主线 6078–6084、发布 5619–5625）：同样缺省 fp16、仅 fp16/bf16，但违规抛 RuntimeError 且类别码为 NOT_SUPPORT——与 C++ 的 TORCH_CHECK/PARAM 不同类，同一非法 dtype 在 Meta 与 C++ 两条路径得到的错误类别不一致；Meta 返回 empty_like(x, dtype)。activation_scale/bias 的形状与广播合同不在 host 层，属 aclnn 设备侧语义，不在已读来源内。

官方用例（test_npu_dequant_bias.py，101 行全文读毕，两 pin 仅行尾空白差异）只提供有限证据：三个用例（basic、no_optional、broadcast）全部 `@unittest.skip` 且 `@SupportedDevices(["Ascend910B"])`，当前不运行。用例把 x 构造成 int32（randint 0..255）、weight_scale 为末维 fp32（广播逐列）、activation_scale 为首维 fp32、bias fp32、output_dtype fp16；golden 只算 `x.float() * weight_scale` 再转目标 dtype——golden 不消费 activation_scale 与 bias，且三处断言都是 `assertRtolEqual(golden_result, golden_result, prec16=1e-2)`（golden 与自身比较，恒真），npu_result 算出后从未参与断言。该用例不能作为数值合同证据，也不能据 golden 反推 activation_scale/bias 的真实语义。

## npu_quant_matmul_dequant：gen_opapi 生成的量化矩阵乘

签名：`npu_quant_matmul_dequant(Tensor x, Tensor quantized_weight, Tensor weight_scale, *, Tensor? bias=None, Tensor? x_scale=None, Tensor? x_offset=None, Tensor? smooth_scale=None, str? quant_mode='pertoken') -> Tensor`。无手写包装 cpp（op_plugin/ops/ 下 rg 零命中）：host 层由 yaml gen_opapi 生成块生成（两 pin 同文）——输出尺寸 `{x.size(0), weight_scale.size(0)}`、dtype 同 x；new_params 把 quant_mode 有值时转 `const_cast<char*>`、无值转 nullptr，另固定注入 trans=true；exec 为 `aclnnQuantMatmulDequant, x, quantized_weight, weight_scale, bias, x_scale, x_offset, smooth_scale, quant_mode_attr, trans, out`。生成层不做 quant_mode 取值白名单，字符串原样直传。

Meta（两 pin 同文，主线 4725–4760、发布 4369–4404）：x 必须 2D 且 fp16、quantized_weight 必须 2D 且 int8、weight_scale 必须 1D 且 fp32，并要求 x.shape[1]==quantized_weight.shape[1]、weight_scale.shape[0]==quantized_weight.shape[0]（均为 VALUE 错误）；输出 empty((x.shape[0], weight_scale.shape[0]), x.dtype)。这些检查只在 Meta 路径：Eager 直调不经过本 Meta（生成 host 层的检查集不在已读来源内，不断言其无检查）。

trans=true 的调用约定由官方用例固定（test_quant_matmul_dequant.py，两 pin 字节一致，71 行全文读毕）：调用方先把 (K,N) 的 int8 权重 `transpose(0,1).contiguous()` 成 (N,K) 再传入；golden 为 `(x_quant @ W) * perchannel_scale * pertoken_scale` 后转 half，即设备侧按已转置权重计算。用例另固定 set_compile_mode(jit_compile=False)。注意该文件仅有的两个用例（dynamic_pertoken 与 static_pertensor）都带 `@unittest.skip` 且 `@SupportedDevices(['Ascend310P'])`：官方 Eager 直调用例当前不运行且仅声明 310P，A2/A3/950 上的 Eager 行为没有官方运行证据，本卡不据此推断设备支持范围。

## 失败与版本边界

- 三个入口两 pin 行为一致（实现字节一致或排版等价），没有发布/主线分叉；acl_op all_version（ifmr）与 op_api all_version（另两者）仅为注册证据，不是 CANN 最小版本或设备支持证明。
- ifmr 的 search 参数语义（起点/终点/步进如何约束搜索域）在 ACE 算子内部，host 只透传；传负步进或 start≥end 的行为未核验。
- dequant_bias 在两 pin 的 derivatives.yaml 无具名接线（定向 rg 零命中，仅为扫描内的缺席），且该文件三个用例（basic/no_optional/broadcast）全 skip 且 910B 门、断言自比恒真：autograd 的实际注册、回退与运行时行为未建立，不据接线缺席推断其反向不存在、梯度为零/当常量或训练路径必然失败；该全 skip 且断言自比的用例文件未提供数值行为的官方运行证据，不据此断言官方运行证据整体缺席。
- quant_matmul_dequant 的 quant_mode 合法取值集合（用例出现 'pertoken'/'pertensor'，缺省 'pertoken'）无 host 白名单；非法字符串在 aclnn 侧的行为未核验。
- 全部静态口径：未执行上游、未跑用例、未验证数值。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/IfmrKernelNpu.cpp)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/IfmrKernelNpu.cpp)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DequantBiasNpuOpApi.cpp)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DequantBiasNpuOpApi.cpp)（primary）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（header）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（header）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_ifmr.py)（example）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_ifmr.py)（example）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_quant_matmul_dequant.py)（example）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_quant_matmul_dequant.py)（example）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_dequant_bias.py)（example）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_npu_dequant_bias.py)（example）

---
type: API
title: npu_matmul_compress_dequant：压缩权重、反量化与输出维度
description: 补齐压缩权重矩阵乘的offset限制、双来源N维度、Meta UINT64尺度与固定skip载荷测试边界。
tags:
- task.implementation
- topic.compute.quantization
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulCompressDequantKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_matmul_compress_dequant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulCompressDequantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_matmul_compress_dequant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-11T07:01:39Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# npu_matmul_compress_dequant：压缩权重、反量化与输出维度

## 固定来源与接口

依据OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的完整Host包装、测试AST及所列Schema/Meta。两版CPP完整非注释token和注释相同；测试完整AST相同，发布仅多4个末尾空行。发布配套为ascend_26_0_pt28，主线配套未知，保持draft和空平台；没有导入上游、生成Tensor、解压缩、运行测试或设备验证。

```text
npu_matmul_compress_dequant(x1, x2, compress_index, bias, scale,
  *, offsetW=None, offsetX=None) -> Tensor
```

它把压缩权重矩阵乘和反量化交给ACLNN，Host包装不实现压缩编码器或解码器。x2不是普通[K,N]密集权重，compress_index也不是一般矩阵行索引；固定测试内的字节常量不能替代任意模型权重的压缩格式合同。

## 入口可用性与offset限制

函数内static bool缓存首次`check_aclnn_kernel_available("aclnnMatmulCompressDequant")`结果，失败立即TORCH_CHECK，消息同时提及主API和GetWorkspaceSize并要求升级CANN；本函数没有回退普通matmul或自行解压。测试skip理由写等待CANN9.0.0，但这只是固定测试的说明，不是本卡确认的最低运行版本或全产品支持证明。

包装拒绝任何has_value的offsetW，包括显式传入但未定义的Tensor；offsetX缺省变为0，非0拒绝。下传时重新构造nullopt offset_w和int 0，并不是把任意offset原样交后端。它还要求x1、scale、bias均二维，未在此完整检查x1/x2/index/scale的dtype、压缩长度、数值、矩阵尺寸相等或bias广播范围。

## 输出N与压缩信息n来自不同对象

令M=x1.size(0)、K=x1.size(1)。输出分配为[M,bias.size(1)]，沿x1设备、固定FP16和ACL_FORMAT_ND；不继承x1的INT8 dtype或任意内部格式。

compressInfo在本地固定为`[8,8,K,scale.size(1),1]`。因此输出N来自bias，压缩信息n来自scale，本包装没有校验这两者相等，不能把合法的维度关系默默补成已经通过本地检查。完整ACLNN参数顺序为x1、x2、compress_index、bias、scale、null offsetW、0 offsetX、compressInfo、result；本地没有逐元素计算反量化。

## Meta更严格的dtype检查不覆盖全部Eager条件

两版Meta同一函数要求：

| 输入 | Meta要求 |
| --- | --- |
| x1 | 二维INT8 |
| x2、compress_index | 各一维INT8 |
| bias | 二维INT32 |
| scale | 二维UINT64 |

Meta返回device='meta'、FP16[x1.shape[0],bias.shape[1]]。它没有检查offsetW/offsetX的上述限制，也没有验证bias/scale尾宽相等、压缩载荷/索引正确、后端符号可用或真实格式转换。Meta成功不能证明Eager会接受非0 offsetX，也不能将UINT64 scale当作可直接替换的FP32尺度Tensor。Schema的all_version登记同样不认证任意CANN/设备组合。

## 数字载荷按静态AST审阅，不推导通用codec

测试generate_compressed_weight仅返回`torch.tensor(固定数字列表,dtype=torch.int8)`；主线13–466行的大列表由6528个整数字面量组成，范围[-127,73]，完整AST和原始字节均已静态核对。该数值载荷做静态解析、数量/范围与摘要对账，没有执行生成器或把逐个字节解释为通用编码规则；发布具有相同完整AST和相同字面值序列。

唯一测试方法同时有Ascend310P装饰器和unittest.skip。它用M=16/K=256/N=128，x1为全1 INT8，密集参考x2为全0 INT8，bias为全0 INT32；调用侧则把固定压缩字节及8字节INT8索引[51,-128,0,0,0,0,0,0]作为x2/index。测试只是将这份固定载荷与零权重参考配对，本地没有先独立解压确认或覆盖一般非零模型权重。

输入尺度先设FP32 ones，经NPU的npu_trans_quant_param再转UINT64送入API；参考以INT32密集matmul加bias再乘原FP32尺度。比较时两边转FP32 CPU NumPy，容差参数0.01；它不是独立解码器或全量量化误差验证。skip方法没有本次运行结果，也没有覆盖非零权重、bias、可选offset、非法压缩index、N不一致或其他shape/dtype/设备。

模型接入应分别确认固定版本压缩器产物、index与compressInfo、UINT64尺度表示及FP16输出，再以非零非均匀权重核对端到端数值，并将权重压缩/传输、工作区和解压矩阵乘成本一起计入收益；本卡没有性能数字或新增verified。

## Evidence

- [MatmulCompressDequantKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulCompressDequantKernelNpuOpApi.cpp)（primary）：1–87；完整本地定义/静态AST范围。
- [test_npu_matmul_compress_dequant.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_matmul_compress_dequant.py)（example）：1–489；完整本地定义/静态AST范围。
- [_meta_registrations.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）：4678–4722；仅此片段。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5678–5679；仅此片段。
- [MatmulCompressDequantKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulCompressDequantKernelNpuOpApi.cpp)（implementation）：1–76；完整本地定义/静态AST范围。
- [test_npu_matmul_compress_dequant.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_matmul_compress_dequant.py)（example）：1–493；完整本地定义/静态AST范围。
- [_meta_registrations.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）：4322–4366；仅此片段。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：5439–5440；仅此片段。

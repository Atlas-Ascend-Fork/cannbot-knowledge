---
type: API
title: SGL SwiGLU 分组量化的三种 scale 布局
description: 区分SwiGLU三种量化scale布局，并补旧Direct Host的可选指针、空域、Tiling缓存及clamp key遗漏边界。
tags:
- task.implementation
- topic.compute.quantization
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/swiglu_group_quant.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/swiglu_group_quant/op_host/swiglu_group_quant.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/swiglu_group_quant/op_host/tiling/swiglu_group_quant_tiling_data.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/activation/swiglu_group_quant/torch_adapter.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/common.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/common_tiling.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/defines.h
  role: header
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T18:07:53Z'
platforms:
- '950'
aliases:
- swiglu_group_quant
---

# SGL SwiGLU 分组量化的三种 scale 布局

## 调用入口

```python
from sgl_kernel_npu.operators.activation import swiglu_group_quant

def swiglu_group_quant(x, topk_weight=None, group_index=None, dst_type=None, quant_mode=1, group_size=128, round_scale=False, ue8m0_scale=False, output_origin=False, group_list_type=0, clamp_value=0.0, *, impl='auto'): ...
```

## 语义与后端范围

输入 `x:[...,2C]` 为连续FP16/BF16，末维依次存gate和up，执行SiLU(gate)×up。可在激活前clamp，并乘每token FP32路由权重。auto固定选950的AscendC，不在arch22自动切到torch_native；参考后端另声明支持arch22。此卡的平台范围限定原生融合路径。

| quant_mode | 分组/scale | 关键开关与输出 |
| --- | --- | --- |
| 1 | 每128个激活一个FP32 scale；支持E4M3FN/E5M2 | `y:[...,C]`，scale为 `[...,C/128]`。 |
| 2 | 每32个激活一个E8M0 scale，依据输入dtype舍入后的指数构造 | scale视图 `[...,C/64,2]`；MXFP8。 |
| 3 | 每128个值一组，amax下限1e-4，基准448 | round_scale把scale上取整到2的幂；ue8m0_scale与之配合存指数；仅此模式的output_origin=True使y_origin有效。 |

输入末维在模式1/3须为256的倍数，模式2须为128的倍数。group_size保留兼容接口，不能据其传值改变各模式固定分组宽度。quant_mode默认1，dst_type默认E4M3FN。

## 分组、输出和验证

前导维展平为N行。可选topk_weight为FP32 `[N]`，group_index为int64 `[E]`，所有张量同一NPU；None或空可选Tensor视作未提供。group_list_type=0表示逐expert计数，各项非负，只定义前 `min(N,sum(counts))` 行。输入不变，输出为y、scale、输入dtype的y_origin；未启用origin的分支不能读取该缓冲区。

验证时显式指定ascendc与torch_native，按模式分别核对dtype、scale视图和有效前缀。不要把mode2的32值分组误当KV压缩接口的64/128值分组，也不要把参考后端的arch22支持解释为原生kernel支持。

## 固定来源与验证状态

- [activation/swiglu_group_quant.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/activation/swiglu_group_quant.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。

## 旧Direct Host的可选输入、输出与调度

完整数学继续复用[mode1 FP8分组](../../operators/aclnn/nn/activation/sgl_swiglu_group_quant_fp8_950.md)、[mode2 MXFP8](../../operators/aclnn/nn/activation/sgl_swiglu_group_quant_mxfp8_950.md)与[mode3 block FP8](../../operators/aclnn/nn/activation/sgl_swiglu_group_quant_block_fp8_950.md)，不因旧wrapper不同就重建Operator。旧root Torch构建在SGL_KERNEL_ENABLE_A5_ONLY_OPS下，把 `torch.ops.npu.swiglu_group_quant` 的PrivateUse1实现绑定旧Host，kernel进入workspace_kernel；新activation域adapter的同名schema改经 `aclnnSglSwigluGroupQuantGetWorkspaceSize/aclnnSglSwigluGroupQuant`。

旧schema默认值与前文公开原型一致，区别在Host准备/缓存。令d=x最后维、C=d/2、N=前导维连乘：

| 项目 | 旧Host实际合同/分支 |
| --- | --- |
| x/dtype | rank>=1、FP16/BF16且连续；dst_type缺省E4，显式只允许E4/E5，决定输出dtype及POD dtype bit，不是完全惰性参数 |
| 尾维 | mode1/3要求d%256=0，mode2要求d%128=0；另检查偶数，没有独立d>0 guard |
| group_size | 接受但不参与Tiling公式、分组宽度或参数检查，仍是mode1/3每128、mode2每32 |
| optional存在性 | topk_weight/group_index均需has_value、defined且numel>0；None/未定义/零元素一律视作未提供，Host与实际传给Kernel的nullptr保持一致 |
| optional约束 | 本wrapper没有完整dtype/shape/同device/连续性检查；前文FP32[N]权重和INT64[E]计数仍是caller合同，不会自动cast |
| clamp | double转float clampValue；hasClampValue由原double!=0判定，不是正值/有限性检查；非零参数不能只保留一个boolean而忽略值 |
| 输出allocation | y[...,C]为E4/E5，y_origin[...,C]总是以x dtype分配；mode1/3 scale[...,ceil(C/128)]，mode2 scale[...,ceil(ceil(C/32)/2),2] |
| scale dtype | mode2或mode3且ue8m0_scale时E8M0，其余FP32；origin只按前文有效分支消费，分配不代表有写入 |
| 空域 | 构造三输出后只在N==0早退，早于group_list_type检查；这不是“任意x.numel()==0都早退”，d=0/N>0没有相同保护 |
| group/分核 | 非空group_index令g=numel，group_list_type仅0；Host按AIV/UB规划count表，有group时launch全部coreNum供每核读取计数、无group时只launch UsedCoreNums |
| POD/key | packed212B：25个I64、clampValue F32@200、dtype I32@204、key U32@208；dtype bits为x BF16/y E5/scale E8，内部keys为1/2/31/32 |
| launch | 每次32B Byte workspace；8个GM槽按x、topk_ptr、group_ptr、y、scale、origin、workspace、tiling传给ACLRT_LAUNCH_KERNEL(swiglu_group_quant) |

Host按三种mode独立算UB。首个全D探测超过UB后，各函数进入else但收缩循环条件写成 `while(totalSize < ubSize_)`；这时循环不会进入，base仍1、dFactor变0，随后有splitD%dFactor表达式。这里保留可定位静态算术终点，不写成“必定安全降级到列分块”，也不编造已运行错误。类似资源/零域边界在新raw数学卡已有记录；本增量没有把它们当作新数学域。

### 旧clamp缓存key遗漏

旧captureMap的tuple key包含hasClampValue，却**没有clampValue本身**；Host上传的212B POD仍包含float clampValue。因而在其余key字段一致、同一个hash槽曾缓存、两次clamp均非零且转换后的float值不同的条件下，第二次命中cache不会更新POD，按该路径继续使用先前float clamp值。改成零会改变hasClampValue，不属于这一精确条件。此为固定源码静态推导，未数值复现，也不是新raw ACLNN的缓存结论。

### 旧1024项Tiling缓存与raw指针生命周期

旧Host以TupleHasher的64位hash直接索引captureMap，没有保存完整参数/POD作碰撞核对；函数内static globalTilingBuffer首次按输入设备分配1024个固定slot，map/counter没有device维度或mutex。cache hit只返回该slot的from_blob非拥有视图；新key且未满则CPU Byte tensor memcpy(POD)→pin_memory→to当前NPU device→copy_入固定slot；超过1024项的新key改为每次一次性上传，不加入map。源码不查询capture状态，不拒绝capture中的首次miss；“capture cache”命名和注释不代表本次graph重放验证。

TorchNpuHelper的CopyTensorHostToDevice选择**当前**NPU设备，不是自动读取x/cache的device；旧静态slab又保留首调用设备且key不含device，不能当作多设备隔离。EXEC_KERNEL_CMD只把Tensor转换成data_ptr，用当前stream调用ACLRT_LAUNCH_KERNEL；lambda捕获的是指针tuple，没有输入/输出/workspace/一次性tiling Tensor owners或record_stream，也没有独立DeviceGuard。宏不检查launch返回值并固定返回0。这里记录本层边界，不臆测RunOpApi内部完成方式或宣称已观察悬空指针故障。

新raw ACLNN adapter则有DeviceGuard、ACL descriptor owners、tensor/workspace record_stream、两段式状态检查，并在lambda捕获Tensor/descriptor/workspace/executor；没有把上述旧1024项slab缓存搬到新adapter。两者可复用量化数学知识，不能互相继承缓存和生命周期保证。
SwiGLU旧POD212B的upload slot对齐为224B，持有slab为224×1024=229376B。key包含尺寸、Tiling派生字段、round/E8/origin/hasClamp、group信息、UB/core与dtype/key，但不补造遗漏clamp或device标识。这里仅保存旧Direct Host的Reference增量，不宣称整个旧wrapper source_closed，未执行上游、构建、capture、真机、数值或性能测试；保留原API status/platform，无新增verified。

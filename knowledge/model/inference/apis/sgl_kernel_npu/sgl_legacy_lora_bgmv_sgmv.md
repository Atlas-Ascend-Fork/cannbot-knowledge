---
type: API
title: SGL旧Torch LoRA接口：固定rank的BGMV与分段SGMV
description: 区分bgmv/sgmv逐行和分段路由、统一rank与标量scale、FP32中间值、expand原地累加及旧构建绑定边界。
tags:
- task.implementation
- topic.model_adaptation
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/op_host/bgmv_expand.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/op_kernel/bgmv_expand_kernel.cpp
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/op_host/bgmv_shrink.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/op_kernel/bgmv_shrink_kernel.cpp
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/op_host/sgmv_expand.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/op_kernel/sgmv_expand_kernel.cpp
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/op_host/sgmv_shrink.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/op_kernel/sgmv_shrink_kernel.cpp
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/op_kernel/lora_common_kernel.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_lora_kernels.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernel-group.yml
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/scripts/prepare_kernel_tests.sh
  role: supporting
created_at: '2026-11-09T05:59:57Z'
updated_at: '2026-11-09T14:14:46Z'
platforms:
- a3
- '950'
aliases:
- bgmv_expand
- bgmv_shrink
- sgmv_expand
- sgmv_shrink
cann_versions:
- 9.1.0
---

# SGL旧Torch LoRA接口：固定rank的BGMV与分段SGMV

## 入口与构建身份

本卡只描述固定提交根Torch构建中的旧绑定。根`csrc/pytorch_extensions.cpp`在`npu`的PrivateUse1实现中注册下列四个符号，`cmake/legacy_kernels.cmake`明确将相应Host与Kernel源加入旧共享库；包初始化通过`torch.ops.load_library`加载`libsgl_kernel_npu.so`。补读活动CI与prepare脚本后，CANN9.1的A3/950整体legacy构建会接入这些基础Host/Device及PrivateUse1注册；本卡按该源码范围定位两平台。该配置不是本次编译事件，也不证明当前安装wheel包含符号或芯片数值已经验收。

```python
import torch
import torch_npu
import sgl_kernel_npu  # 初始化并加载原生库后，访问 torch.ops.npu

# 以下为注册签名的Python形式；均没有impl参数。
def bgmv_shrink(x, weight, indices, y, scale): ...  # -> None

def bgmv_expand(x, weight, indices, y, slice_offset, slice_size): ...  # -> Tensor

def sgmv_shrink(x, weight, lora_indices, seq_len, y, scale): ...  # -> None

def sgmv_expand(x, weight, lora_indices, seq_len, y, slice_offset, slice_size): ...  # -> Tensor
```

它们不同于[SGEMMV/SGEMMC shrink](/model/inference/apis/sgl_kernel_npu/sgl_lora_shrink.md)与[expand](/model/inference/apis/sgl_kernel_npu/sgl_lora_expand.md)：本组没有逐适配器`lora_ranks`、`lora_scales`或多切片`slice_offsets`，一次调用使用统一rank；不能把两组元数据位置直接互换。

## 路由与数学含义

设T为token行数、H为输入隐藏维、R为本次统一rank、O为expand切片宽度，适配器编号为i。

| 接口 | 路由元数据 | 写入语义 |
| --- | --- | --- |
| bgmv_shrink | int64 `indices[T]`，每行一个适配器 | FP16/BF16 `x[T,H]`与同类型`A[L,R,H]`，计算`y[t,:]=float(scale)*(x[t,:] @ A[i,:,:].T)`，写入FP32 `y[T,R]`。 |
| sgmv_shrink | int64 `lora_indices[B]`与int64 `seq_len[B]`，长度为各连续token块的行数 | 同一块共享适配器，运算和FP32输出与bgmv相同；scale是全调用共享的一个标量。 |
| bgmv_expand | int64 `indices[T]` | FP32 `x[T,R]`与FP16/BF16 `B[L,O,R]`相乘，累加到同类型`y[T,F]`的`[slice_offset:slice_offset+O]`，其中O=slice_size。 |
| sgmv_expand | int64 `lora_indices[B]`与int64 `seq_len[B]` | 分段共享适配器，其他运算与bgmv_expand相同。 |

shrink把输入/权重转FP32做逐行点积并乘标量scale，再覆盖对应y行；不是向旧y累加。expand将权重和已有y转FP32，完成点积与加法后以CAST_RINT写回y类型；没有再乘scale，需避免重复应用alpha/r。expand返回`y_out=y`的别名，shrink返回None，两者均原地修改传入输出。

负适配器ID会跳过相应行/块，保留原y，并不自动清零。SGMV以`BlockIterator`对seq_len累积定位块；零长度块自然跳过，未被长度总和覆盖的行得到块号-1后跳过。完整覆盖时调用方须保证seq_len非负、sum(seq_len)=T、两组分段元数据同长，每个非负ID均小于权重适配器数。

## Host检查与调用方前提

Host显式检查shrink的x为FP16/BF16、expand的y为FP16/BF16，x/y二维、weight三维或四维；BGMV还检查indices一维及x/y/indices行数相等。shrink要求H>R；expand要求R<=slice_size、slice_offset>=0且slice_offset+slice_size<=F。T=0会在num_tokens_per_core检查处拒绝。

其余合同不能从上述少量检查中推导：Kernel直接解释原始指针、不处理通用stride，调用方须提供同一NPU上的连续Tensor、表中dtype和完整权重形状；四维weight只能使用中间单例维`[L,1,R,H]`或`[L,1,O,R]`，否则Host虽可能接受维数，Kernel的适配器stride仍按三维紧密布局计算。SGMV Host未校验x/y行数、metadata维度/dtype/长度或权重几何；这些都须在接入层核对。

expand的归约只实现R=8/16/32/64四个分支；Host不拒绝其他rank，不能把“未抛异常”当支持证明。R=0还会进入初始化的除法。尾部实现以`(O*R % 8192) // 64`计完整计算repeat，没有任意子repeat掩码，故`O*R`非64倍数存在未完整计算尾部的静态风险；搬运仍使用普通DataCopy，本卡没有证明任意未对齐slice_offset、O或F有效。shrink同样未提供任意H/R搬运尾部准入表，不能把expand的rank分支机械等同于shrink已验证范围。

四个Host从当前NPU流启动，但查询Vector core数时使用硬编码device_id=0。多设备非同型环境的能力查询与目标执行设备需单独核对，不能由接口存在推导任意多NPU部署已验收。

## 验证方法与停止条件

先核对加载库身份和四个实际Torch符号，再使用独立输出缓冲验证shrink覆盖、expand对非零y累加、负ID保留、SGMV分段边界及未选切片哨兵。参考可按行/块选择A/B并在FP32中计算；expand在最终加法后才按输出dtype舍入，不能在中间结果先降精度。

遇到错误dtype、非连续布局、非法ID、未覆盖token、非支持expand rank或不满足尾部计数条件时停止调用，先修正元数据/布局。源码附近`tests/python/sgl_kernel_npu/test_lora_kernels.py`实际调用的是`sgemmv_shrink/expand`，不能作为本卡四个入口的直接覆盖或测试通过证据。本次未执行上游程序、编译、真机、精度或性能测试，也未记录verified事件。

## Evidence

- [旧Torch注册与PrivateUse1绑定](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp#L67)：四个签名与323–329行绑定。
- [旧构建源清单](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake#L56)：66–69行Host、145–148行Kernel。
- [BGMV expand指针、rank与尾部](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/op_kernel/bgmv_expand_kernel.cpp#L28)：FP32输入、254–285行归约分支、136–166行尾部及219–235行累加/舍入。
- [SGMV分段迭代](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/lora/op_kernel/lora_common_kernel.h#L25)：按长度累计定位token块。


## 源码实现与资源复用

四种数学入口分别保存完整源码卡，不能仅凭名字互换元数据。shrink将输入/权重转FP32，H≤11776时一行X跨rank驻留，更大H按固定tile为每rank重载X，显式UB为141312+8R字节；expand用131584B固定UB，64lane重复FP32 X、四rank归约后在FP32加旧y，最后一次CAST_RINT。两者都无按UB容量动态降tile的Host fallback，也没有把邻近SGEMMV测试当作本组通过。

| 数学入口 | A3源码 | 950源码 |
|---|---|---|
| BGMV shrink | [逐token缩维](../../operators/direct/nn/matmul/sgl_bgmv_shrink.md) | [逐token缩维950](../../operators/direct/nn/matmul/sgl_bgmv_shrink_950.md) |
| BGMV expand | [逐token累加](../../operators/direct/nn/matmul/sgl_bgmv_expand.md) | [逐token累加950](../../operators/direct/nn/matmul/sgl_bgmv_expand_950.md) |
| SGMV shrink | [分段缩维](../../operators/direct/nn/matmul/sgl_sgmv_shrink.md) | [分段缩维950](../../operators/direct/nn/matmul/sgl_sgmv_shrink_950.md) |
| SGMV expand | [分段累加](../../operators/direct/nn/matmul/sgl_sgmv_expand.md) | [分段累加950](../../operators/direct/nn/matmul/sgl_sgmv_expand_950.md) |

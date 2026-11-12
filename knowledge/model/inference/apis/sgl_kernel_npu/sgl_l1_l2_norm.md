---
type: API
title: SGL行归一化接口的带符号和与L2平方和
description: 区分 l1_norm 的带符号求和、FP32输出与 l2norm_fwd 的平方和epsilon和auto/triton宽度上限。
tags:
- task.implementation
- topic.compute.normalization
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/l1_norm.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/l2norm_fwd.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/norm/l1_norm.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l1_norm.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/l2norm.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l2norm_fwd.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
aliases:
- l1_norm
- l2norm_fwd
---

# SGL行归一化接口的带符号和与L2平方和

## 调用入口

```python
from sgl_kernel_npu.operators.norm import l1_norm

def l1_norm(input, *, impl="auto"):
    ...

from sgl_kernel_npu.operators.norm import l2norm_fwd

def l2norm_fwd(x, eps=1e-6, output_dtype=None, *, impl="auto"):
    ...
```

## 两个不同的归一化定义

| 接口 | 分母 | 输入/输出 |
| --- | --- | --- |
| l1_norm | 每行元素的带符号和，不取绝对值、不加epsilon | auto/triton要求连续NPU `[B,H]` FP16/BF16/FP32，H为正二次幂；torch_native可处理CPU及非连续二维输入，不要求二次幂H。均返回新FP32 `[B,H]`。 |
| l2norm_fwd | `sqrt(sum(x*x)+eps)`，不是均方根 | auto/triton要求连续NPU `[...,D]`；torch_native可处理CPU及能view的非连续输入。两者均要求D>0且可view(-1,D)；新输出保持shape，output_dtype默认x.dtype，也可指定FP16/BF16/FP32。 |

l1可用于专家权重重新归一化，但行和为零会产生NaN/Inf。不要用通用绝对值L1范数API作为参考。公共入口不添加连续化或完整输入检查，auto/triton输入须满足线性寻址约束，不能把该布局限制推广给显式torch_native。

l2使用FP32中间值，eps默认1e-6，加在平方和后、根号内。仅impl="auto"/"triton"按输入dtype限定宽度上限`65536 // x.element_size()`，超过会RuntimeError，改变输出dtype不能放宽该上限；D<=512与更宽D的内部kernel分流也仅属于Triton。torch_native直接用PyTorch计算，不执行这一宽度检查或kernel分流。

## 参考和验证

auto均指向triton，没有自动失败回退。l1的torch_native先转FP32并复制到CPU，用NumPy计算再传回输入设备，故不适合NPU图捕获；l2参考用PyTorch计算FP32平方和与rsqrt。

分别测试正行和/零行和、L2零输入和不同output_dtype；核对shape、输出dtype和输入不变。不能把l1的CPU同步参考成本当作NPU kernel性能，两个API也不能互换。

## 旧模块副本与设备属性缓存

固定提交仍保留 `sgl_kernel_npu.norm.l1_norm` 的 `l1_norm`。与 `implementation.triton.norm.l1_norm` 逐项对照，差异只有设备属性helper的导入位置及部分说明文本；函数、JIT装饰器、autotune配置和Host参数/全局量一致。两个helper的get_device_properties函数及其依赖也相同：读取当前NPU，经Triton driver查询num_aicore/num_vectorcore，要求两者为正。它们是独立模块中的源码副本，并非同一个Python函数对象的转发别名；不保证共享JIT/autotune缓存，也不把旧入口存在作为公共后端准入扩大的依据。

get_device_properties使用无参数functools.cache，缓存键不含device。两个helper模块各自保存首次成功查询的核数；在同一进程切换设备后，不能假定会重新查询新设备拓扑。该事实限定固定源码，未测量异构多卡进程或任何性能影响。

[带符号行归一化的A2/A3源码卡](/model/inference/operators/direct/nn/norm/sgl_l1_norm.md)、[950源码卡](/model/inference/operators/direct/nn/norm/sgl_l1_norm_950.md)。


## 旧FLA L2接口及带guard的模块包装

固定commit另有 `sgl_kernel_npu.fla.l2norm`。其直接 `l2norm_fwd(x,eps=1e-6,output_dtype=None)` 与新版implementation的数学/launcher可共享分析：两个JIT body、do_not_specialize=["NB","T","MBS"]、num_warps=8/num_stages=3、D<=512分支、BT=min(109,(109*128)//BD)、输入元素字节决定的64KiB宽度guard及返回原shape均相同；旧宽分支名为l2norm_fwd_kernel1，新名为l2norm_fwd_kernel。实际helper导入分属旧utils与implementation.utils，不是同一Python函数对象或共享缓存。

但旧模块还有当前公共API签名未包含的实际包装：

```python
from sgl_kernel_npu.fla.l2norm import l2norm_fwd, l2norm, l2_norm, L2Norm
direct = l2norm_fwd(x, eps=1e-6, output_dtype=None)
guarded = l2norm(x, eps=1e-6, output_dtype=None)
same_entry = l2_norm(x)  # l2_norm = l2norm
module = L2Norm(eps=1e-6, output_dtype=None)
guarded = module(x)
```

L2Norm只保存eps/output_dtype，forward调用l2norm；l2norm调用L2NormFunction.apply，其静态forward被input_guard装饰，最终才调用旧l2norm_fwd。没有新的归一化数学或Device Kernel。L2NormFunction未定义backward，也未保存反向所需tensor，不能因用了torch.autograd.Function就承诺训练反向支持；本次没有执行autograd。

### input_guard的真实转换与设备边界

input_guard先建立位置参数的惰性生成器，并立即对Tensor关键字参数各自.contiguous；随后从原参数中选择第一个Tensor（先位置、再关键字）的device.index，进入torch.npu.device(index) context，再在调用被装饰函数的参数展开时对Tensor位置参数执行.contiguous。无Tensor才nullcontext；两类连续化的时机不同，不能概括为均在设备context前完成。对于该forward，正常首Tensor为x，因此guarded入口提供连续化和当前设备context，和raw l2norm_fwd的view-only/current-device调用不同。它不检查所有Tensor同设备、不转换数据dtype或验证eps，也不是CPU参考backend选择器。

raw l2norm_fwd只做x.view(-1,D)，没有input_guard或.contiguous；能view的padded row stride仍未必满足两个JIT裸packed stride(D,1)。不能用guarded接口处理strided输入的能力扩大raw前提，或把公共torch_native的CPU能力传播到这个NPU context包装。empty input仍按旧launcher形成相应分支，没有新增guarded空域短路。

旧文件另定义get_npu_properties()，每次直接查询current_device属性；实际l2norm_fwd没有调用它，而是D<=512才用从旧utils导入的零参数@cache get_device_properties。两者不能混同。小D路径在切设备后可能保留先前核数；input_guard切换context不清该cache，new implementation helper又有独立cache。D>512分支不查询这两个helper。BT_LIST=[8,16,32,64,128]也没有参与当前launcher选择，不能编造autotune路线。

### 复用的资源、精度与静态边界

FP32平方和在根号内加eps，D<=512用rsqrt，多行block_ptr边界只按全局(T,D)，没有限制到每program的M=ceil(T/P)行配额；Q=ceil(M/BT)若使Q*BT>M，可产生相邻program行写集合重叠。D<BD时block_ptr load未指定padding_option；不能补造归约padding为0。宽分支一program一row，显式mask other0、用1/sqrt。旧body同样保留这些静态边界，并非由于加guard便证明结果或race安全。

每个小D逻辑tile BT*BD个FP32值约4BTBD B，行归约BT项；宽分支BD个FP32值约4BD B。无自有workspace/UB/L1/L0/queue/event、atomic或barrier，编译器物理分配不由逻辑张量相加确定。guarded连续化可能新增X容量大小的临时copy，输出仍新分配T*D*e(output) B，view与临时寿命由Torch/Triton当前流管理；没有自有跨stream发布或手工hostwait。源码不修改X；输出stride与y.view能否成立仍依实际allocation和输入合同。

[新版L2 A2/A3源码卡](/model/inference/operators/direct/nn/norm/sgl_l2norm_fwd.md)及[950源码卡](/model/inference/operators/direct/nn/norm/sgl_l2norm_fwd_950.md)保存两JIT/完整参数、行访问次数及padding/race边界。本节复用同数学分析并补旧Host包装，不新增重复Operator，也不把新版平台/完整闭包标签传播到旧入口。所有上述均为静态阅读，未执行编译、反向、真机或数值验证。


## 固定来源与验证状态

- [norm/l1_norm.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/l1_norm.md)
- [norm/l2norm_fwd.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/norm/l2norm_fwd.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

- [python/sgl_kernel_npu/sgl_kernel_npu/fla/l2norm.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/l2norm.py)（implementation）：旧L2包装、guard与同数学实现证据。
- [python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/fla/utils.py)（implementation）：旧L2包装、guard与同数学实现证据。
- [python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l2norm_fwd.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/norm/l2norm_fwd.py)（implementation）：旧L2包装、guard与同数学实现证据。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。

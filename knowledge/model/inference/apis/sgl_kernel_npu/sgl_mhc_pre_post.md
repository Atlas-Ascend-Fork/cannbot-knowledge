---
type: API
title: SGL mHC预处理Sinkhorn与后混合厂商接口
description: 说明固定CANN9.1依赖的mHC预处理与后混合接入、ACLNN映射、输出类型、requires_grad分支和950发布冲突。
tags:
- task.implementation
- topic.model_architecture
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/hyper_conn/mhc_pre_sinkhorn.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/hyper_conn/mhc_post.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/hyper_conn/mhc_pre_sinkhorn.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/hyper_conn/mhc_post.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/torch_extension/cann_ops_transformer/docs/zh/mhc_pre_sinkhorn.md
  role: primary
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/torch_extension/cann_ops_transformer/docs/zh/mhc_post.md
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/torch_extension/cann_ops_transformer/ops/mhc_pre_sinkhorn.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/torch_extension/cann_ops_transformer/ops/mhc_post.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/torch_extension/cann_ops_transformer/ops/csrc/mhc_pre_sinkhorn.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/torch_extension/cann_ops_transformer/ops/csrc/mhc_post.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/torch_extension/cann_ops_transformer/op_builder/builder.py
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/mhc/mhc_pre_sinkhorn/README.md
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/mhc/mhc_post/README.md
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/mhc/mhc_post/docs/aclnnMhcPost.md
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/version.cmake
  role: supporting
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/mhc/mhc_pre_sinkhorn/op_host/op_api/aclnn_mhc_pre_sinkhorn.cpp
  role: implementation
- resource: https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/mhc/mhc_post/op_host/mhc_post_tiling.cpp
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a3
- '950'
aliases:
- mhc_pre_sinkhorn
- mhc_post
---

# SGL mHC预处理Sinkhorn与后混合厂商接口

## 调用入口

```python
from sgl_kernel_npu.operators.hyper_conn import mhc_pre_sinkhorn

def mhc_pre_sinkhorn(x, phi, alpha, bias, hc_mult=4, num_iters=20, hc_eps=1e-6, norm_eps=1e-6, *, impl="auto"):
    ...

from sgl_kernel_npu.operators.hyper_conn import mhc_post

def mhc_post(x, h_res, h_out, h_post, *, impl="auto"):
    ...
```

## Pre/Sinkhorn

x为FP16/BF16 `[T,N,D]`，phi为FP32 `[(2+N)*N,N*D]`，alpha `[3]`、bias `[(2+N)*N]` 也为FP32。flatten残差流后以norm_eps做FP32 RMS归一化，再投影并按pre/post/res三部分缩放偏移。pre/post用sigmoid，post再乘2；res矩阵交替按行列作Sinkhorn，num_iters默认20、hc_mult默认4、hc_eps/norm_eps默认1e-6。不融合输出RMSNorm。固定9.1厂商ACLNN路线的CheckShape强制N=hc_mult=4、num_iters=20，二者不是可任意更改的默认值；同提交README另将D%128=0列为支持约束，此对齐要求按文档记录，不冒充已定位的Host拒绝分支。torch_native独立参考不继承这组厂商准入。

返回hin `[T,D]`、hpost `[T,N]` FP32、hres `[T,N*N]` FP32。vendor后端把输入适配为 `[T,1,N,D]` BSND再去序列维，SGL层不作输出cast。下述固定9.1 C++绑定以 `x.options()` 分配hin、以 `phi.options()` 分配hpost/hres，因此在此绑定的合法输入域hin与x同dtype，后两者为FP32；这是固定绑定事实，不能外推为任意vendor版本或后端的保证。

## Post

mhc_post参数为x `[T,N,D]` FP16/BF16、h_res `[T,N,N]` FP32、h_out `[T,D]` 同x类型、h_post `[T,N]` FP32。FP32计算 `h_post[i]*h_out[d]+sum_j h_res[j,i]*x[j,d]`，输出 `[T,N,D]`，SGL层保留vendor类型；下述固定9.1绑定用 `at::empty_like(x)` 分配输出，因此与x同dtype。固定9.1厂商A3的非空路线在CheckSpecConstraints强制N=4、0<D<100000且D%128=0；950在该检查前另行返回，不能把此A3检查扩展为950限制。参考后端独立bmm并转输入激活dtype，不受这组厂商专用检查约束。


## 固定9.1厂商入口映射

本轮对照官方 ops-transformer 提交 `c77c0829f1f0f0b8f882db1d9b051a758b605472`，其 `version.cmake` 明写9.1.0。SGL此处从公开 `cann_ops_transformer.ops` 导入，未把该包二进制绑定到某个Git提交；这里提供可核验的同版本源码映射，不保证部署中任何同名9.1二进制逐字相同，也不以bundled 9.2 profile或其它tag替换该依赖。

| SGL路径 | 固定厂商Python/C++链 | 精确ACLNN两段式入口 | 复用的实现知识 |
|---|---|---|---|
| `mhc_pre_sinkhorn._cann_impl` | x的unsqueeze(1)视图 → `ops/mhc_pre_sinkhorn.py` → `MhcPreSinkhornOpBuilder.sources`指定`ops/csrc/mhc_pre_sinkhorn.cpp` → `ACLNN_CMD` | `aclnnMhcPreSinkhornGetWorkspaceSize/aclnnMhcPreSinkhorn` | [A2/A3 MhcPreSinkhorn](../../../../ops/ascendc/operators/aclnn/transformer/mhc/mhc_pre_sinkhorn.md)，包含投影Cube及MIX前向两阶段 |
| `mhc_post._cann_impl` | 原参数直接转发 → `ops/mhc_post.py` → `MhcPostOpBuilder.sources`指定`ops/csrc/mhc_post.cpp` → `ACLNN_CMD` | `aclnnMhcPostGetWorkspaceSize/aclnnMhcPost` | [A2/A3 MhcPost](../../../../ops/ascendc/operators/aclnn/transformer/mhc/mhc_post.md)、[950 MhcPost](../../../../ops/ascendc/operators/aclnn/transformer/mhc/mhc_post_950.md)，均为Vector流式/常驻X路线 |

`OpBuilder.load` 按算子名复用进程内已加载模块；首次缺缓存时源码调用 `torch.utils.cpp_extension.load`，来源C++文件、include与链接参数由builder提供。这是固定厂商Python接入的行为，不表示本次安装、JIT编译或执行过。SGL自身缓存导入的Python函数，不改厂商builder和ACLNN的错误传播。

## requires_grad与中间量边界

固定厂商入口只显式对输入Tensor的 `requires_grad` 作布尔或：pre检查x/phi/alpha/bias，post检查x/h_res/h_out/h_post；这两个入口没有额外调用 `torch.is_grad_enabled` 等全局grad模式查询。以下是源码选择与调用关系，不推断外部PyTorch在某种全局模式下后续如何保留或释放saved tensor。

- pre无输入需梯度时，C++以 `outFlag=False` 调ACLNN；hin/hpost/hres为新分配主输出，五个中间输出是新分配的零元素Tensor，Python丢弃这五个返回值，仅向SGL交三个主输出。A2/A3算子内部仍需要的invRms/投影临时量由已有Operator所述workspace承担。
- pre任一输入需梯度时，`MhcPreSinkhornFunction.forward` 强制 `outFlag=True`，C++以phi的FP32 options新分配h_pre `[B,S,N]`、hc_before_norm `[B,S,N*N+2N]`、inv_rms `[B,S,1]`、sum_out `[2I,B,S,N]`、norm_out `[2I,B,S,N,N]`，并以输入和这些中间Tensor调用 `ctx.save_for_backward`；Python仍只返回三个主输出，SGL再squeeze序列维。输出flag改变前向中间量owner及workspace路线，不等于调用Backward。
- post任一输入需梯度时选 `MhcPostFunction.apply`，forward仍调用同一C++与ACLNN前向入口，源码向 `ctx.save_for_backward` 传入四个输入；否则直接调同一C++。输出仍由C++以 `empty_like(x)` 新建。
- 两个Function的 `backward` 才分别导入并调用 `mhc_pre_sinkhorn_backward` 或 `mhc_post_backward`，属于独立数学入口；本卡仅标明边界，不把其Device实现归并为前向闭包。

## 分发和证据边界

两接口auto固定cann_ops_transformer，依赖CANN9.1公开Python接口，首次执行加载缓存；错误直接上抛，不回退旧算子，也不额外设架构白名单。适配层不新增输入元信息或标量约束；支持范围交所选后端。空输入/IDLE短路仍属于SGLang调用方，不能依赖此wrapper新增处理。

SGL上游固定文档报告A3 Ascend910_9362和950DT Ascend950DT_9582的CANN9.1精度用例，使用模型配置尺寸的构造Tensor，没有checkpoint或捕获激活，不代表整网验收。HF32投影也使post/comb需要专门容差；按文档FP32 post/comb用atol/rtol=5e-5，FP16激活atol1e-5/rtol2e-3、BF16激活atol1e-5/rtol1e-2核验，不用宽松共享绝对误差掩盖小值错误。

固定9.1依赖的 `mhc_pre_sinkhorn/README.md` 和厂商Python文档同时将950列为不支持，而SGL固定文档报告了上述950精度用例。前向Host/arch35 Device接线的存在不能消除这项发布证据冲突；因此保留SGL报告但不据此新增950 pre正式Operator或宣称固定9.1公开支持。MhcPost的厂商Python文档也将950列为不支持，但同提交的MhcPost README和ACLNN API文档明确950支持，且存在对应arch35路线；这是Python文档与ACLNN发布表的内部差异，不能用其中一层静默覆盖另一层。MhcPost两平台实现通过已有独立卡复用，不能把pre的发布冲突传播成post整体不支持。

## 固定来源与验证状态

- [hyper_conn/mhc_pre_sinkhorn.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/hyper_conn/mhc_pre_sinkhorn.md)
- [hyper_conn/mhc_post.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/hyper_conn/mhc_post.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的API契约与厂商接入映射蒸馏，Host/Tiling/Device实现通过上文已有Operator链接复用；不重复生产同实现正文。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。

## 约束与接入的固定源码

- [aclnn_mhc_pre_sinkhorn.cpp](https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/mhc/mhc_pre_sinkhorn/op_host/op_api/aclnn_mhc_pre_sinkhorn.cpp)：Pre的N/hcMult/numIters强制值。
- [mhc_post_tiling.cpp](https://gitcode.com/cann/ops-transformer/blob/c77c0829f1f0f0b8f882db1d9b051a758b605472/mhc/mhc_post/op_host/mhc_post_tiling.cpp)：Post的非950 N/D约束及950提前返回。

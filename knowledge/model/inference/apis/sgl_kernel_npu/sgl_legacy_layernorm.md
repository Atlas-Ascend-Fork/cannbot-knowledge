---
type: API
title: 旧attentions LayerNorm 的输出形状与动态ACLNN接入
description: 说明旧layernorm的normalized_shape推导、mean/rstd继承输入dtype及format、动态两段式调用与未确认平台版本边界。
tags:
- task.implementation
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/layernorm.cpp
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/layernorm.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/register_ops.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/pytorch_npu_helper.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/find_op_path.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/find_op_path.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/CMakeLists.txt
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_plugin.sh
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_ops.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/build/build_ascendc_ops.sh
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/setup.py
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/attentions/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/attentions/env.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/attentions/attentions/lib.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/build.sh
  role: supporting
created_at: '2026-11-09T17:52:51Z'
updated_at: '2026-11-09T17:54:19Z'
platforms: []
aliases:
- torch.ops.attentions.layernorm
- layernorm_npu
---

# 旧attentions LayerNorm 的输出形状与动态ACLNN接入

## 接口与注册

固定提交的独立插件将 `layernorm_npu` 注册为PrivateUse1实现，入口为 `torch.ops.attentions.layernorm`；不是 `sgl_kernel_npu` 的新原生算子命名空间。

```python
torch.ops.attentions.layernorm(
    input, normalized_shape, weight=None, bias=None,
    eps=1e-5, impl_mode=0,
)  # (output, mean_out, rstd_out)
```

| 参数 | wrapper真实行为 |
| --- | --- |
| input | 按原Tensor的shape、stride、dtype、storage_offset和底层storage转ACL描述符；本wrapper未限制dtype、rank、format或连续性 |
| normalized_shape | 必选Host int64数组，长度决定本地统计量shape；数组值原样转AclIntArray交给ACLNN |
| weight/bias | optional Tensor，None变成未定义Tensor再转nullptr；本地不分配ones/zeros替代 |
| eps | double，默认1e-5，原样传；本地未验证正值/有限性 |
| impl_mode | int64，默认0，原样作为调用最后一个业务实参；本地未白名单检查 |
| 返回 | (output,mean_out,rstd_out)，三个Tensor由wrapper拥有，不是外部返回的裸指针 |

## 输出分配与normalized_shape推导

输出output先按input.sizes()分配，options与NPU format都继承input；mean/rstd没有被强制成FP32。代码仅用normalized_shape的**长度**推导shape，并未在计算beginAxis之前校验它与input尾维相等。

令r=input.dim()、d=normalized_shape.size()，beginAxis=r-d，m为input前beginAxis个维度的连乘（初值int64 1）：

| 分支 | mean_out/rstd_out的实际分配 | dtype/format |
| --- | --- | --- |
| m>0 | 保留input前beginAxis维，后d维全改为1；例如input[2,3,4]、normalized_shape长度2→[2,1,1] | input.options()、get_npu_format(input) |
| m<=0 | 直接一维shape[m]；正常非负shape中前缀含0可得[0] | 同上，不沿用完整rank的统计shape |
| beginAxis=0 | 空前缀连乘m=1；正常走m>0，全rank置1 | 同上 |
| normalized_shape为空 | 本层没有拒绝；d=0意味着mean_shape保持input所有维度，再交ACLNN | 不据此承诺核心接受空归一化域 |

例如FP16 input会在wrapper层得到FP16 output/mean/rstd，BF16亦然；这只描述分配，不宣称外部ACLNN的统计精度或所有dtype均支持。变量mean_out/rstd_out的命名不替代核心计算、方差定义或数值舍入证据。

由本地算术可知，调用前至少需确保d<=r，否则size_t beginAxis会下溢，随后的前缀迭代器算术早于外部ACLNN校验；代码没有本地保护。不应指望ACLNN后续校验修复已经发生的本地shape推导。m乘积没有显式溢出检查；固定源码的SmallVector<int64_t,8>中8是内联容量，注释不能单独证明wrapper已校验rank<=8。以上为静态边界，未执行错误输入或复现故障。

## ACLNN调用与外部核心边界

实际参数序列为：

```text
aclnnLayerNormWithImplModeGetWorkspaceSize(
  input, normalized_shape, weight_or_null, bias_or_null, eps,
  output, mean_out, rstd_out, impl_mode, &workspaceSize, &executor)
aclnnLayerNormWithImplMode(workspace, workspaceSize, executor, currentStream)
```

这里按本wrapper的真实顺序记录，不用另一个版本的公开prototype重排参数。对应符号由动态loader解析；本次固定来源没有把这个外部LayerNorm核心的Host/Tiling/Device绑定到唯一安装版本，不能宣称完整Operator闭包，亦不从其他LayerNorm或同包attention构建目标推导平台/CANN版本。因此保留draft、platforms为空且不填写cann_versions。

### 旧插件的加载、描述符与两段式边界

旧独立package名为attentions，import先将包内ops/vendors/aie_ascendc与customize目录置于原ASCEND_CUSTOM_OPP_PATH之前，再在NPU可用时加载plugin/libPTAExtensionOPS.so；TORCH_LIBRARY(attentions)与PrivateUse1注册暴露对应torch.ops.attentions接口。csrc/attentions/csrc/CMakeLists.txt显式编译六个wrapper（la、rain、ada、sparse estimate、layernorm、pool indexer）及注册/find_op_path，使用C++17，ABI宏取USER_ABI_VERSION（仅0/1，缺省0），链接torch/torch_npu/ascendcl/nnopbase/opapi。build_plugin.sh从已安装toolkit配置环境并复制so入Python包，build_ops.sh只选择laser_attention、ada_block_sparse_attention、sparse_block_estimate三项；这个列表不证明LayerNorm或Rain核心也随包提供。构建脚本未固定可核验的CANN版本，不能由其latest路径或其他新接口推导旧wrapper版本。

EXEC_NPU_CMD按“ASCEND_CUSTOM_OPP_PATH中各op_api/lib的libcust_opapi.so → ASCEND_OPP_PATH/vendors/config.ini的load_priority顺序 → 默认libopapi.so”逐符号查找API及GetWorkspaceSize；两者各自解析，未强制来自同一个so。路径列表在共享库初始化时保存，函数指针为模板静态缓存，不会逐次重新探测环境。缺符号TORCH_CHECK失败，没有Python参考fallback。

Tensor转换保留sizes/strides/storage_offset和原storage指针，并按维数选ACL format：3D=NCL、4D=NCHW、5D=NCDHW、其余ND；storageDims为storage字节数/itemsize的一维容量。它不是按input_layout字符串重新转形、转置、连续化或重排数据。未定义Tensor/缺省optional Tensor转nullptr；IntArrayRef调用aclCreateIntArray转换为AclIntArray，空数组也经该创建函数，而非同义的null tensor。包装层支持的dtype映射不单独证明外部算子支持该dtype。

调用顺序为可选InitHugeMemThreadLocal → 转换参数并调用GetWorkspaceSize得workspaceSize/executor → size>0分配Byte NPU workspace（0为nullptr）→ 取当前NPU stream → OpCommand自定义handler调用第二阶段 → 正常返回时ReleaseConvertTypes/ReleaseHugeMem → cmd.Run后UnInitHugeMem。非零两阶段状态用aclGetRecentErrMsg抛错；源码未用RAII覆盖所有异常清理路径，handler按值捕获描述符裸指针但不捕获workspaceTensor本体，不能仅凭本地代码宣称异步或异常生命周期已验证。executor、底层Host/Device算法与流完成语义依赖实际安装库及torch_npu；本卡只记录wrapper，不提供源码级完整Operator闭包或运行通过结论。

## 来源与提取状态

主来源为[layernorm.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/layernorm.cpp)，声明见[layernorm.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/layernorm.h)，schema/PrivateUse1接线见[register_ops.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attentions/csrc/plugin/register_ops.cpp)。已有通用LayerNorm知识不能替代这个旧Torch ABI的输出分配和调用顺序。

本次只读固定源码后写Reference，未执行上游、构建、插件加载、数值、真机、性能或测试；无verified事件。来源固定与静态检查不替代运行结果。

---
type: Guide
title: 原生FFT：环境依赖、rfftn尺寸与950DT限制
description: 保存ATB/ASDSIP环境要求、rfftn输入数值与长度条件，以及ifftshift的950DT类型排除；含FFT计划缓存（FFTMixCache容量与淘汰）、系数矩阵生成与ASDSIP ABI层（libasdsip.so句柄生命周期与MKI描述符）。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-fft.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-fft.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-signal.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-signal.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-signal.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-signal.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-signal.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-signal.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-signal.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FFTc2cKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FFTr2cKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FFTc2rKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/FFTCommonOpApi.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FFTc2cKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FFTr2cKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FFTc2rKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/FFTCommonOpApi.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/StftKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/StftKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/FFTCommonOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/FFTCommonOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/FFTPlanNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/FFTPlanNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/fft_plan_op_api.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/fft_plan_op_api.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/AsdSipNpuOpApi.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/AsdSipNpuOpApi.h
  role: implementation
created_at: '2026-11-09T12:28:09Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# 原生FFT：环境依赖、rfftn尺寸与950DT限制

## 固定来源与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14支持页；七版本及实际存在的中英文页分别审阅，不回推26.0/PyTorch2.8发布组合，也不将950DT扩为950PR。文档未收录的接口/产品只表示此清单未验证；支持条目不是完整社区参数手册。本卡仅静态审阅，未执行上游、设备或性能实验。

## 环境依赖先于调用支持

中英文七版本FFT页在导言要求配置CANN安装目录下nnal/atb/set_env.sh与nnal/asdsip/set_env.sh。这是来源的部署前提，本文未执行脚本，也不据路径存在证明任意版本的动态库已经配套。

中文页对fft/ifft、fft2/ifft2、fftn/ifftn、rfft/irfft、rfft2/irfft2、irfftn、hfft/ihfft、hfft2/ihfft2、hfftn/ihfftn、fftfreq/rfftfreq、fftshift/ifftshift列A2/A3训练系列与950DT。英文页只收录其中部分，不从英文缺项推定中文条目失效；这些普通支持项未给完整dtype、norm、dim、stride及反向矩阵。

## rfftn不能套用相近变换

两种语言七版本均列rfftn在A2/A3支持、950DT不支持。input仅FP32，每个值在[-100,100]；支持1至8维，来源另具体描述1维(n)、2维(batch,n)，没有完整解释更高维的每个轴映射。

batch可取1/8/16/24/32/64；n满足下列任一条件：2的幂且指数不超过23；由2/3/5/7相乘且乘积不超过1,000,000；由200以内质数相乘且乘积不超过100,000。来源在“2的指数”与“长度n”中复用n符号，应分别理解，不能把任意长度或任意batch并入。更高维的逐轴规则仍按实际参数补证，不由1至8维声明自行补造。

## ifftshift的类型排除

ifftshift虽然列三类产品，950DT另明确不支持FP64、complex64、complex128；这是该入口的限制，不自动扩到fftshift或所有FFT。中文逗号与英文措辞的版本变化未改变这三个排除类型。

## 验收

固定库版本、环境、实/复数变换、长度、轴、归一化与数据分布，比较参考输出及逆变换误差，再测量首次加载、稳态执行和内存。支持清单、额外环境配置与真实精度/性能是三个独立证据，本文没有执行变换。

## Signal窗口的独立支持清单

同提交七份中文torch.signal页均收录windows.exponential/general_cosine，列A2/A3训练系列与950DT；bartlett/blackman/cosine/gaussian/general_hamming/hamming/hann/kaiser/nuttall只在2.13/2.14两页收录，也列三类产品。该路径没有相应英文页，不由旧版未列项推定运行时绝对不可用。清单没有窗口长度、periodic/symmetric、dtype、设备分配和梯度的完整参数表，不能据名称将任意窗口或其与FFT的任意组合当作已经验证，也不从两者都列支持推定相同环境依赖或性能收益。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-fft.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-fft.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-fft.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-fft.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-fft.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-fft.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-fft.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-fft.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-fft.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-fft.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-fft.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-fft.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-fft.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-fft.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-signal.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-signal.md)（constraint）

- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-signal.md)（constraint）

- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-signal.md)（constraint）

- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-signal.md)（primary）

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-signal.md)（constraint）

- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-signal.md)（constraint）

## FFT执行：矩阵分解与ASDSIP的准备成本

OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`中的六个_fft_c2c/r2c/c2r functional/out入口会选择本地矩阵分解或ASDSIP路线；两个反向helper还会补零或倍增频率梯度。它们的Schema均列op_api [v2.1,newest]，C++受VERSION_BETWEEN(V2R1,VERSION_NEWEST)保护。本节补执行准备，不扩大前面的产品、rfftn参数或环境支持范围。

### 路由先看符号，再看维数与类型

DO_ASDSIP_COMPATIBILITY按C2C/R2C/C2R拼接asdFftExec符号名，以宏展开位置的static地址缓存结果；地址为空就直接return传入的_exec_fft表达式。这个兼容路线是本地**矩阵分解与aclnnMatmul**，不是CPU回退，也没有执行失败后统一catch再重跑的协议。

| gate | 所选路线 | 可见准备成本 |
|---|---|---|
| 对应ASDSIP执行符号缺失 | _exec_fft矩阵路线 | 两块real dtype缓冲、输入copy_，逐系数矩阵Matmul与中间整理 |
| 符号存在，但dim.size()>1 | 矩阵路线 | 不因库已加载就免除矩阵与临时缓冲准备 |
| C2C/C2R输入为ComplexHalf，或R2C输入为Half | 矩阵路线 | 与同一入口的其他dtype可能走不同实现 |
| 其余当前入口条件 | _exec_fft_asdsip | permute后contiguous、合并batch、handle/workspace/stream及参数转换 |
| 主线V2R15以上且self.numel()==0 | helper对out.zero_并早返 | functional仍有此前结果申请；各入口此前shape/dim访问也未自动消失 |

C2C透传forward；R2C使用forward=true，C2R使用self.is_conj()作为方向参数。输入/输出局部检查分别要求复数、浮点或相应输出类别，不在本节补造完整dtype/布局支持矩阵。ASDSIP helper虽含signal_ndim==2时设置fftYSize的代码，当前这六个消费者dim.size()>1已经选矩阵路线，不能据helper分支宣布这些入口已走ASDSIP二维FFT。

### 矩阵路线的布局与双缓冲

_exec_fft先以self/out的view句柄准备计算对象。C2C按输入stride降序排列全部变换轴；R2C把dim.back()放在变换轴最前，C2R放在最后，batch轴另按stride排序，再permute。

| 准备阶段 | 本地行为 |
|---|---|
| 复数/实数表示 | HackComplexintoFloat复用storage，末尾加长度2、stride1，原stride及offset乘2并改dtype；逆helper删除末轴，stride及offset除2并改回复数 |
| 初始工作区 | 两次apply_tensor_without_format；每块初始长度取改写后self.numel()，mode非C2C再乘2；第一块resize后copy_(self) |
| 每个变换轴 | get_plan(radix,forward,PlanMode,real dtype)，取系数矩阵及factor列表；按其shape reshape/resize缓冲 |
| 每份系数矩阵 | EXEC_NPU_CMD(aclnnMatmul,...,cube_math_type=0)，交换ping/pong；非最终轴另有copy_整理 |
| 结束 | copy_到输出计算对象、reshape、归一化，恢复复数表示并按逆置换as_strided_写回目标shape/stride |

这些reinterpret helper操作的是本地view句柄的TensorImpl元数据，不等于请求普通数值cast；它们本身没有补齐任意stride、offset整除或外部别名的完整校验。双缓冲后续还会resize，不能把初始长度当作完整峰值上界，结果也不能仅据申请位置就认定始终保持默认连续stride。get_plan构造、系数生成与缓存淘汰不在本节核对。

矩阵路线对长度1有专门处理：单轴C2C满足特例时copy_后直接返回；逐轴R2C的第一轴长度1时用zeros_like_out和cat补实虚表示，其他长度1轴进行reshape。C2R缺全谱时通过slice、flip、虚部neg_与cat补共轭频率；多轴R2C还会按半谱输出尺寸裁剪中间对象。上述处理和原始输入整理同属执行成本，不能只计矩阵乘法。

### ASDSIP路线仍有连续整理和workspace

ASDSIP helper把batch轴排前、信号轴排后，按stride整理；复数输入先改成real表示再permute().contiguous()，随后恢复复数，实数输入也请求permute().contiguous()。再reshape合并batch，按mode设置batchSize、direction、fftXSize及类型。contiguous请求是否实际复制取决于当前布局，不能从库调用只有一次就推导包装无搬运。

执行宏获取当前NPU流、SetDeterministic、getHandle(FFTParam)，查询workspace大小，非零时申请unsafe_empty_workspace并绑定handle；随后绑定stream、ConvertType输入输出，缓存执行符号地址，并把捕获handle/input/output的lambda交给两参RunOpApiV2。lambda检查执行返回值为0。这里仍使用SetDeterministic，不能套用其他OpAPI宏的snapshot改动；宏注释“异步”也不独立证明Host调用完全不等待。handle、转换对象、workspace与队列的完整生命周期，以及动态库加载和缓存容量策略另核。

执行后同样归一化，再reshape并恢复输出stride。R2C的ASDSIP非onesided分支先只处理半谱slice的连续对象，再copy_回原输出，并以conjugate_symmetry翻转低频、否定虚部补高频；该helper对空输入或轴长<=2早返。不能将非onesided概括为直接交库一次生成全谱。

### 归一化与反向准备

本地normalization枚举0为none，1为by_root_n，2为by_n。helper对none取scale=1，对by_root_n取归约轴尺寸乘积的平方根倒数，其他非none分支取尺寸乘积倒数；scale不为1才mul_。R2C用输入sizes，其他模式用输出sizes推导该乘积，没有在这里对任意norm整数补全上层合法性检查。

| 反向helper | 真实准备 |
|---|---|
| fft_r2c_backward，!onesided | 直接取反向_fft_c2c结果的real |
| fft_r2c_backward，onesided | 目标最后轴改last_dim_size；zero_length>0时申请real-view形状的zeros并copy_已有半谱前缀，再view_as_complex进入反向C2C，返回real |
| fft_c2r_backward | 调用onesided _fft_r2c；double_length>0时，从频率1起narrow对应范围，view_as_real后mul_(2)，返回该复数结果 |

zero_length<=0的r2c反向分支复用grad的real view，没有在这段代码按目标长度再做统一裁剪。两个helper的填充、copy_或倍增要与正向路线一起检查，不能只验证输出shape后忽略频率端点与归一化。

### 主线与发布的实质差异

主线新增fft_input_is_empty并由六入口调用，仅V2R15以上启用numel==0时out.zero_早返；发布没有该helper/调用。部分functional在调用它之前已申请结果并读dim.back()，所以不能将它解释成空输入完全免准备或空dim都被本地验证。

矩阵路线单轴C2C的长度1特例，主线检查self_.size(dim.back())，发布检查self_.sizes().back()，后者是物理末维而非必然所选变换轴。发布在初始化sorted_dims后又调用一次_sort_dims；逐轴长度1的非R2C首轴分支调用reshape但没有接收返回值，主线则赋回tmp_pingpong[ping]。这些是实际语句差异，本节未运行或据此宣称已复现数值错误。

fft_c2r_backward主线新增dim非空断言，发布对应函数没有；r2c backward的两版代码相同，仅许可头差异。性能与正确性定位应固定库/快照、轴及其stride、实/复数类型、onesided、norm和正反向，分别观察首次plan/handle、矩阵路线缓冲与Matmul、ASDSIP连续整理及workspace。本节只做静态源码审阅，未导入上游、创建plan、查库或运行CPU/NPU，不新增verified或产品承诺。

### FFT实现证据

- [FFTc2cKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FFTc2cKernelNpuOpApi.cpp)（implementation）：1–663。
- [FFTr2cKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FFTr2cKernelNpuOpApi.cpp)（implementation）：1–59。
- [FFTc2rKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FFTc2rKernelNpuOpApi.cpp)（implementation）：1–38。
- [FFTCommonOpApi.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/FFTCommonOpApi.h)（implementation）：73–85、90–118。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：195–211、7133–7137。
- [FFTc2cKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FFTc2cKernelNpuOpApi.cpp)（implementation）：1–635。
- [FFTr2cKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FFTr2cKernelNpuOpApi.cpp)（implementation）：1–57。
- [FFTc2rKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FFTc2rKernelNpuOpApi.cpp)（implementation）：1–41。
- [FFTCommonOpApi.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/FFTCommonOpApi.h)（implementation）：74–82、87–112。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：195–211、6923–6927。

## STFT：专用执行与分帧FFT组合的准备成本

STFT包装在aclStft专用路线和本地分帧、窗口、FFT组合之间选择；组合路线没有本地CPU转换。它还提供显式反向，涉及补零、连续整理及重叠帧累加，不能只按一次FFT估算成本。

| 条件/阶段 | 本地行为 | 可见准备成本 |
|---|---|---|
| self为Double/ComplexDouble | 支持判断直接true | 不经过后面的Float缓存/GM估算；不等于所有设备支持已认证 |
| Float、window缺省或Float，且估算未超限 | 专用aclStft | 根据return_complex及batch准备输出 |
| 支持判断false | _stft组合 | 窗补零/copy或fill、可选pad、分帧view、窗口mul、FFT及转置 |
| 主线空输入 | 已完成参数/shape准备后返回empty | 不进入专用/组合，但不跳过前置检查 |
| 反向返回实数表示的grad | contiguous再view_as_complex，转置后再contiguous | 不因前向只含view就忽略反向整理 |
| 帧写回可能重叠 | 基底zeros、Long索引及index_add_ | 梯度恢复成本取决于stride/重叠，不是单纯reshape |

### 专用路线gate和参数语义

外层要求self为1D/2D，0<n_fft<=末维长度，hop默认n_fft/4且>0，win_length默认n_fft且在(0,n_fft]；仅同时提供window与win_length时，这段检查明确验证window为1D且长度相符。return_complex缺省取self或window为复数，onesided外层缺省只根据self.is_complex选择，两者不是同一谓词。

frames按(len-nfft)/hop+1，频率数n为onesided?nfft/2+1:nfft；复数输出为[batch,n,frames]或[n,frames]，实数表示在末尾再加长度2。Float/Double在return_complex时对应ComplexFloat/ComplexDouble，复数输入不return_complex时对应其Float/Double实数表示。

除Double特例，is_aclstft_supported只在self为Float且window缺省或Float时可能返回true。它估算matmulN=(len-nfft)/hop+1、matmulM=onesided?nfft/2+1:nfft；nfft400/hop160/未normalized/onesided/不return_complex的特例按8对齐，其余按32对齐。缓存估算为matmulM*nfftAlign*4*2，须<=500*1024*1024；GM估算包含输入、输出、splitWindow与matmul临时项，须<=35*1024^3。

这里batch在1D输入时取0，所以GM公式各项为0，不能当作1D真实内存占用上界；窗口/copy/FFT实际分配也不是这个估算的完整核对。专用调用传nfft/hop/win/normalized/onesided/return_complex，未见DO_COMPATIBILITY，不能据gate false有组合路线就推出专用符号缺失或执行异常也会自动重试。

2.1..2.6签名不含align_to_window；2.7以上接收它，但专用aclStft调用不传此值，支持gate也没读取它。该参数只沿外层false分支进入组合，不能声称任意输入设置它必然改变专用执行。

### 组合路线的window、pad和layout

_stft将1D输入unsqueeze成batch；win_length<nfft时创建nfft长零window，在中心窄片copy原window或fill1。align_to_window为true时按win_length计算帧数，并在输入两侧各pad((nfft-win)/2)；否则按nfft计算。随后as_strided形成[batch,frames,nfft]，stride为原batch stride、hop*原时间stride、原时间stride，有window时执行mul。

分帧后的input若为复数，拒绝onesided并调_fft_c2c；实数调用_fft_r2c。normalized布尔作为本地FFT normalization整数传入，之后transpose_(1,2)，原1D输入squeeze batch；不return_complex则view_as_real。FFT内部矩阵/ASDSIP及双缓冲规则沿用前节，不重复认定全部过程仅为view。组合中onesided缺省按窗口相乘后的input.is_complex决定，外层若此前未显式指定参数，两处默认判断可能不同。

输出类型helper只列Float/Double与ComplexFloat/ComplexDouble分支，外层随后检查输出类型；不能把未列类型理解成有默认安全返回。长参数与类型校验也不替代完整上层STFT接口契约。

### 反向的补零与重叠帧累加

stft_backward先补齐window；不return_complex时对grad_output.contiguous()做view_as_complex，再按需加batch、transpose(1,2).contiguous()。复数输入/窗使用反向_fft_c2c；实数且onesided时将最后频率维补到nfft，必要时申请zeros并copy已有前缀，再反向C2C并取实部连续结果。若有window，乘其conj；self为实数而结果为复数时再次取实部并contiguous。

反向随后重建帧sizes/strides，交本地as_strided_backward_恢复原几何。该helper对零size早返zeros，size1 squeeze，输出stride0的维度先sum；依据按stride排序的覆盖跨度判断可能重叠，按输入/输出offset和最小storage需求申请共同零基底。输出可能重叠时创建Long arange索引并index_add_，否则用as_strided view.copy_；输入几何也可能重叠时另计数index_add_并storage.div_(count)，最后返回输入几何的view。这些是实际申请、累加和除法，不是“反向只把shape改回去”。

反向签名没有align_to_window，其帧数公式仍按nfft；原1D self结束处实际调用unsqueeze(0)，没有对称地squeeze。代码中complex_fft表达式直接访问window_.is_complex()，本节不据此前optional窗缺省就补造它的所有未定义对象行为。这些边界需在启用组合/反向的真实模型中核对，本卡没有复现运行错误。

### 主线与发布差异及验证状态

主线get_output_size用has_batch区分原1D/2D，发布按batch>0判断；主线在两种外层签名计算输出shape后，对numel==0将负shape项置0并empty返回，发布没有该快捷且在gate通过后才计算专用输出shape。空输入判断仍在nfft等检查之后，不能据此认为所有零长度输入都会直接成功。

OpPlugin固定主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`；除上述声明/空batch差异与许可头，完整局部剩余代码一致。Schema前向签名按2.1..2.6和>=2.7划分，backward为>=2.1。仅静态审阅，未执行上游、FFT、设备或性能测试，原21支持页与前节产品边界保持；不新增verified。

### STFT实现证据

- [StftKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/StftKernelNpuOpApi.cpp)（implementation）：1–554。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：4981–4985、7130–7131。
- [StftKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/StftKernelNpuOpApi.cpp)（implementation）：1–531。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：4826–4830、6920–6921。

## FFT 计划缓存、系数生成与 ASDSIP ABI 层

前节把 `get_plan` 构造、系数生成、缓存淘汰、handle 生命周期与动态库加载明确留作边界；本节静态核对该层，来源为 `op_plugin/utils/custom_functions/opapi/` 下的 FFTCommonOpApi.cpp、FFTPlanNpuOpApi.cpp、fft_plan_op_api.h 与 AsdSipNpuOpApi.h。四个文件主线与发布两版本 去空白 token 流一致（仅缩进/换行排版差异），下文行号为主线 d84e9b1d，未复测运行、不新增 verified。

**FFTMixCache 的结构**：全局单例 `fftCache` 初始容量 10（FFTCommonOpApi.cpp :20）。`std::list` 保存 `(FFTCacheKey, FFTCacheValue)` 对，`std::mutex` 保护；`get` 命中时把命中项 move-to-back（近似 LRU），容量满时淘汰队首——**淘汰只销毁 ASDSIP 路线的 handle（`destoryHandle`），矩阵系数 plan 不需要显式销毁**。缓存键是 `(prb_size, is_forward, plan_mode, scalar_dtype)` 的 PlanKey（矩阵路线）或 ASDSIP 的 FFTParam；两类键混在同一个 list，靠 `isAsdSip` 标志区分值形态。

**容量控制是静默钳制**：`setFFTPlanCapacity(maxSize)` 只接受 1..99，越界直接 return 不改也不报错（:86-92）；`setCapacity` 收缩时逐步淘汰队首直至达标。`getFFTPlanCapacity/getFFTPlanSize/clearFFTPlanCache` 提供观测与清空；**没有任何环境变量或 Python 入口在已读窗口内消费这些 setter**，默认容量恒 10——多形状模型反复变换时计划缓存容量是否成为复用上限需按此边界实测，不能预设可调。

**矩阵系数的生成成本**：`make_plan`（fft_plan_op_api.h 声明、FFTPlanNpuOpApi.cpp 实现）对 prb_size 做 `factorize`（试除到 sqrt，含余素数），`make_sure_first_alpha` 把首个因子换成 >=16 的因子（避免首块过小），`merge` 归并相邻因子。每个因子用 `one_rotate_matrix`（:64-140）在 **CPU Double** 上构造旋转系数块：theta 由三段 arange 乘 `2π/(prev_n*factor)` 得到，cos/sin 分四次 `copy_quarter` 填入 `{prev_n, out_n, out_complex, in_complex, in_n}` 五维块；r2c 尾因子输出 `(factor/2)+1` 行、c2r 尾因子输出单实部、r2c/r2c_bothside 首因子输入单实部，随后 cast 到目标 dtype 并 reshape/permute/contiguous 成 `{prev_n, out_n*out_complex, in_complex*in_n}`。因此矩阵路线的首次 plan 构造包含 CPU 上的三角函数与拷贝，循环中每次 `get_plan` 命中后这些成本消失；`FACTOR_BOUND=32`、`NDIM_BOUND=5`（fft_plan_op_api.h :20-21）是生成侧界，与前文 rfftn 文档长度条件不同源。

**ASDSIP ABI 层**（AsdSipNpuOpApi.h，主线 :29-313）：`GetAsdSipApiLibName` 固定 `libasdsip.so`，`GetAsdSipApiFuncAddr` 以 `dlopen(..., RTLD_LAZY)` 静态缓存句柄、失败仅 LOGW 并返回空指针——与 op_api_common 的 libopapi 符号探测独立。函数指针族为 `_asdFftCreate/_asdFftDestroy/_asdFftSetStream/_asdFftSynchronize/_asdFftGetWorkspaceSize/_asdFftSetWorkspace/_asdFftMakePlan1D/_asdFftMakePlan2D` 与执行 `_asdFftExec(handle, const aclTensor*, const aclTensor*)`；MkiTensor 描述符自带 `dims/strides` 的栈上 SVector（DEFAULT_SVECTOR_SIZE=48、上限 256）、`offset`、`dataSize` 与独立 `hostData` 指针，`_asdCreateTensor` 同时接收 device 与 host 两个指针。ASDSIP 路线的 handle 生命周期因此是：FFTParam 相同则从 FFTMixCache 复用 handle（淘汰时销毁），否则 createHandle 新建——前节「首次 plan/handle 成本」的具体来源即此层。

**边界**：本节未核对 libasdsip.so/libopapi 内部（CanUsePTACache 同属外部白名单），未运行 MakePlan/执行路径；`destoryHandle` 的拼写来自源码按原文记录。缓存命中只省去 host 侧构造，不改变 FFT 数值语义；容量 10 的实际命中行为、线程竞争表现与 950 组合均不在本静态窗口结论内。

### 计划缓存与 ABI 层证据

- [FFTCommonOpApi.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/FFTCommonOpApi.cpp)（implementation）：18-105。
- [FFTPlanNpuOpApi.cpp d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/FFTPlanNpuOpApi.cpp)（implementation）：23-200。
- [fft_plan_op_api.h d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/fft_plan_op_api.h)（implementation）：19-117。
- [AsdSipNpuOpApi.h d84e9b1d](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/AsdSipNpuOpApi.h)（implementation）：28-320。
- [FFTCommonOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/FFTCommonOpApi.cpp)（implementation）：17-134，去空白 token 流与主线一致。
- [FFTPlanNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/FFTPlanNpuOpApi.cpp)（implementation）：23-232，同上。
- [fft_plan_op_api.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/fft_plan_op_api.h)（implementation）：19-135，同上。
- [AsdSipNpuOpApi.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/AsdSipNpuOpApi.h)（implementation）：15-263，同上。

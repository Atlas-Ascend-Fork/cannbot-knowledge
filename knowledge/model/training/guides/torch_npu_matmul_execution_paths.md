---
type: Guide
title: TorchNPU矩阵乘执行路径：NZ分派、精度透传与反向搬运
description: 定位OpPlugin原生matmul的格式和符号门槛、显式CubeMathType优先级，以及广播反向的布局处理和版本差异。
tags:
- task.optimization
- topic.precision
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulDoubleBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulDoubleBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddmmKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddbmmKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BaddbmmKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddmmKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddbmmKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BaddbmmKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BmmKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MmKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_bmm_compatible.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BmmKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MmKernelNpuOpApi.cpp
  role: implementation
created_at: '2026-11-10T11:21:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU矩阵乘执行路径：NZ分派、精度透传与反向搬运

## 版本与任务范围

固定OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`，审阅原生`matmul`、`matmul.out`、`matmul_backward`的op_api实现与局部格式/精度helper，不覆盖全部Dispatcher、aclop实现或ACLNN设备kernel。发布来源组合是ascend_26_0_pt28，主线与目标部署的配套未知。整卡平台及完整输入矩阵未确认，保留draft和空平台；没有执行上游、编译、设备、梯度或性能实验。

本卡用于定位“为什么相同矩阵乘换格式、精度设置或训练后成本发生变化”。公开产品和dtype规格沿用[原生矩阵接口约束](torch_npu_native_torch_matrix_signal_scope.md)，HF32/CubeMathType属性的配置方法沿用[精度API](../apis/torch_npu/hf32_and_cube_math_type.md)，不由本层分支扩大产品支持。

## 先确认进入哪条前向实现

两版Schema同时声明aclop和op_api路线。主线matmul还登记dvm，发布该局部Schema没有这一项；这里不把op_api的代码当成所有实际调用的完整执行图。`matmul`和`matmul_out`先执行`DO_MATMUL_COMPATIBILITY`，再进入本文件的分配和ACLNN调用。

该宏先区分两输入都是base format，或右输入NZ的窄分支；base格式检查的是`FormatHelper::IsOpInputBaseFormat`，不能用Python连续性或reshape替代真实NPU storage描述。`is_nd_nz_format`仅认右输入的`ACL_FORMAT_FRACTAL_NZ`，并排除左输入也为同一NZ；它只允许双方二维，或双方三维且`GetSocVersion()>Ascend910_9362`的分支。这个helper不等于对全部FRACTAL_NZ_C0变体和任意高维输入的保证。

NZ路线还要求宏中的Soc条件，以及`IsAclnnOnly()`为真或**两侧均非FP32**。主线在Soc条件额外纳入`Is310PBoolCheck()`（枚举Ascend310P1至Ascend310P7）；发布宏没有这项。该差异只说明包装层候选条件变化，不证明新增产品及任意shape、dtype已可运行。

实际通过检查的op_api前向按上述NZ识别调用`aclnnMatmulWeightNz`，否则调用`aclnnMatmul`，两者都传cube_math_type。宏检查执行符号及GetWorkspaceSize符号；不满足格式/类型路线时，在非AclnnOnly分支回到调用者提供的aclop，AclnnOnly分支拒绝。符号检测和真实设备能力不同；返回aclop也不等同于CPU回退。宏的通用边界见[执行路径与回退门控](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)。

因此先保存实际storage format、rank、dtype、Soc和符号分派，再对比NZ转换的准备成本及重复使用次数。不要把“矩阵形状相同”或“格式cast成功”当成已经命中同一kernel；本文件没有把所有ND权重自动转NZ。

## 显式精度透传优先于HF32默认推导

前向和反向的局部matmul helper都调用`get_cube_math_type_with_passthrough()`。两版的顺序相同：先用`get_cube_math_type(IsAllowMatmulHF32())`取得默认推导值，再调用无参`get_cube_math_type()`；若第二个值非负，就覆盖前一个结果。

因此只记录allow_hf32不足以完整解释这条调用的精度模式；另一个有效的显式CubeMathType会优先下传。此处只观察优先级，没有追完无参getter的全部生产路径，也不把某个枚举数直接解释成每种设备的相同计算算法。性能和精度对照应保存两个设置的实际值、首次生效时机、输入分布和参考误差，再记录最终执行路径。

前向返回按self.options分配普通格式结果，`.out`使用`check_tensor`核对既有结果并标注不支持backward。`get_output_size`会处理向量提升、矩阵输出和batch广播；输出shape推导并未在本函数逐项检查收缩K、全部dtype/格式约束。分配成功或输出shape正确不能替代数值与合法组合验收。

## 广播训练必须连同反向数据布局一起测

反向的局部`matmul_implement_npu`直接调用`aclnnMatmul`，没有前向的WeightNz分派和同一格式兼容宏。前向命中WeightNz不能证明梯度也保持同一格式与后端；本卡也不据此断言底层必定拒绝NZ，需要观察实际适配链。

两版反向分别计算self和other梯度，按mask决定调用；会剥离前导单例batch轴、将向量提升为矩阵，再按是否可归约为二维矩阵乘选择分支。

- 当self侧梯度进入`mat1.dim()==2 && mat2.dim()>2`分支，先转置/reshape另一输入，再将grad按矩阵M轴优先permute，显式调用`.contiguous()`后reshape，最后矩阵乘并还原self形状。连续化在原视图不满足时可增加数据搬运和临时内存；不能把这条反向当成只有一个GEMM。
- 当other侧梯度进入`mat2.dim()==2 && mat1.dim()>2`分支，将mat1和grad的batch/token轴reshape折入二维，再转置mat1做矩阵乘，最后还原other形状。reshape是否需要复制取决于输入stride，不能统一承诺零拷贝。
- 其余分支用广播输出shape分配结果后调用ACLNN，本局部函数没有通用`sum_to`式收缩代码。多轴广播及单例batch梯度的最终形状和归约需连同外围autograd核对，不从局部shape helper推导任意广播梯度已验证。

选择模型布局时，用相同真实batch/token形态分别测forward、两个梯度和完整训练步；记录permute/contiguous及分配的耗时和峰值。只优化forward的NZ或二维GEMM时间，可能漏掉训练中的主要复制成本。

## 空Tensor与梯度mask的版本边界

两版对未定义grad都返回两个未定义Tensor。主线另在grad/self/other任一numel为0时，按mask为所需梯度返回zeros_like，不需要的槽返回未定义Tensor；发布没有这一早退，不能把主线空输入处理回推发布。

非空路径结尾在`other.dim()==1`时访问`other_grad.size(-1)`，这个条件没有先检查`grad_input_mask[1]`或`other_grad.defined()`。所以向量other但不请求other梯度，是需要定向核对的静态风险；本卡未运行该分支，也未追完整Dispatcher/autograd来认证实际用户调用必然触发异常。grad mask为真/假、空输入和向量输入应分别验收，不能用双梯度普通矩阵用例替代。

## 验证与收益边界

固定安装包、设备、layout/stride、M/N/K与batch、dtype和精度设置，先验证输出及所需梯度，再采集实际分派、格式转换、连续化和内存分配。对比应同时包括权重准备、稳态forward和训练步；实际只推理时另排除未使用的反向成本。失败时恢复已验证的格式与精度组合并保留输入，不以更宽误差阈值掩盖位布局或梯度归约错误。本文没有性能数字、设备支持认证或新增verified。

## 二阶梯度的三槽合同与额外分配

两版完整 `MatmulDoubleBackwardKernelNpuOpApi.cpp` 的phase2代码token及全部注释相同，Schema为 `matmul_double_backward(grad_self?,grad_other?,grad_out,self,other,bool[3] mask)` 登记op_api `[v2.1,newest]`。返回依次为grad_grad、self_grad、other_grad，不是原始两个一阶梯度的简单重算。实际自定义autograd调用者、aclop和设备数值支持不由这个Schema独立认证。

grad_out未定义时立即返回三个未定义Tensor；两个可选grad_self/grad_other缺省也转为未定义Tensor。若某个可选梯度的rank恰比其对应self/other多1，就直接取第0个切片；这不是对所有额外batch维求和，也没有在这里完整验证轴长度或任意广播形式。

| 三位mask | 本地计算条件与内容 |
| --- | --- |
| mask[0] | 至少一个可选梯度defined时计算grad_grad=grad_self×other+self×grad_other；缺失项按零贡献。 |
| mask[1] | grad_other defined才调用一阶matmul_mat1_backward(self,grad_other,grad_out)计算self_grad。 |
| mask[2] | grad_self defined才调用一阶matmul_mat2_backward(grad_self,other,grad_out)计算other_grad。 |

grad_grad helper总是先分配两个zeros_like(grad_out)，即使只有一项defined；再分别执行所需matmul，最后Tensor相加生成结果。不能只按最多两个GEMM估算其分配和逐元素加法成本。mask未请求的槽保持未定义Tensor，这不等于零Tensor。

二阶局部matmul helper同样经精度透传调用aclnnMatmul，并执行 `FLOP_COUNT(FlopCounter::mm_flop,...)` 计数宏；一阶helper也有这一宏。代码中声明的ALLOW_FP32_DOWN_PRECISION/KEEP_DTYPE常量没有直接决定这些调用的cube_math_type，实际仍是本卡前述getter优先级。计数宏存在不证明观测覆盖、实际硬件指令数或已测得吞吐。

末尾同样在other为向量时无条件先访问other_grad.size(-1)，没有先检查mask[2]或other_grad.defined()。当不请求other_grad或缺grad_self时，需要结合实际调用者做定向验证；本卡未运行，不声明用户场景已复现异常。它也没有一阶主线的numel==0提前返回，因此不能把一阶空输入合同沿用到二阶。

本卡完整重核一阶主线203行和二阶两版102/106行；一阶发布203行与主线全token/注释相比仅缺前述空numel早退，其余本地定义等价。原卡中的前向、格式宏和精度helper知识按当前旧卡字节复用，本卡没有重新读取或提升那些大文件，也没有梯度、二阶数值或设备实验。

## addmm/addbmm/baddbmm的独立准备与版本边界（新增）

新增对照OpPlugin同一固定主线与发布的三个OpAPI完整CPP，以及各自完整输出shape helper和精确Schema；不重读、重qual原有matmul/反向及共享OpUtils事实。这里是Eager包装，不能用[Triton矩阵梯度分解](torch_npu_triton_matmul_backward_and_batchnorm_decomposition.md)替代其格式、参数与结果申请合同。未导入、执行SDK、helper、FLOP宏、生成器、自动梯度或设备实验。

### Addmm的NZ宏与普通matmul宏不同

addmm的functional/out先走本文件DO_ADDMM_COMPATIBILITY。self、mat1、mat2均为base format时探测aclnnAddmm；否则，本地is_nd_nd_nz_format要求bias self rank为1或2、self不是NZ，并委托共享helper判断mat1/mat2的ND/NZ组合。共享格式识别按本卡前述固定OpUtils来源复用，不能把连续性当NPU storage format。

NZ准入还依赖本宏static保存的SoC条件：`Ascend910B1<=SoC<Ascend310B1`或`SoC>Ascend310B4`。这个Addmm宏两版均没有前述普通matmul主线新增的310P判断，也没有复制其两侧非FP32的限制。它们是不同宏，不把一个文件的额外dtype/产品门控补到另一个。helper注释只写(n,)或(1,n) bias，但本地代码仅检查bias rank，没有检查二维bias第0维必须等于1；注释不代替实际验证。

符合窄NZ条件才探测aclnnAddmmWeightNz；不合条件时，非AclnnOnly返回传入的ACL表达式，AclnnOnly则读取三个storage格式并报错。符号探测与外部SDK支持仍独立，不把本地SoC枚举当产品认证。进入执行后再依据本地ND/NZ helper选择普通或WeightNz命令；包装没有自动把全部ND权重转换成NZ。

addmm_使用另一个直接的aclnnInplaceAddmm兼容探针，随后对self做shape/dtype准备并执行原地命令，没有复用上面的WeightNz选择宏。不能因为functional命中NZ路线，就认为inplace也有相同格式路由。

### 输出申请、显式dtype与兼容表达式

| 入口 | 本地结果准备 |
|---|---|
| addmm functional | 无格式结果，shape由helper决定，普通重载取self.options；主线typed重载改为self.options().dtype(output_dtype) |
| addmm out | 普通重载把out.scalar_type()作为check_tensor的目标类型；主线typed重载改用output_dtype |
| addbmm functional/out | functional调用apply_tensor_with_sizes并取self.options；out以self.scalar_type()做check_tensor |
| baddbmm functional/out | functional无格式结果取self.options；out以self.scalar_type()检查；主线typed两重载分别改为显式输出dtype |

表中只是申请helper及其参照选择，不推导这些helper必然零复制或底层接受任意不同dtype的out。Addmm执行后还propagate_names_for_addmm并传播非空名字；其余两个所读文件没有同一显式步骤，不能自动复制Addmm的局部名字处理结论。

主线Addmm与Baddbmm各新增functional/out的output_dtype重载，Schema只在[v2.9,newest]列op_api/internal_format_opapi；发布所选CPP和Schema没有这四个typed重载。这个缺项限定固定路径，不能扩为发布所有后端都无法实现相应类型。主线typed重载的兼容ACL表达式均调用不带output_dtype的旧重载；该字段未在这个回退表达式透传，不能仅据typed OpAPI正常路径的申请dtype，保证回退返回也与请求相同。真正回退分配和SDK类型支持需另外证据。

### shape helper和参数检查的边界

Addmm的helper调用广播shape计算，将self.sizes()与`[mat1.size(0),mat2.size(1)]`合并；Addbmm则将self.sizes()与`[batch1.size(1),batch2.size(2)]`合并。它们不在这几个小helper中统一校验所有K、batch或精确rank；广播helper的完整规则另计。Addbmm functional/out虽先要求两个batch输入rank>=3，但这个下界不能改写成已经验证恰好3D和所有内维相容。

Baddbmm包装给shape helper传的是batch1、batch2；helper局部仅要求第一个rank>1、第二个rank>2，再返回`[batch1.size(0),batch1.size(1),batch2.size(2)]`。它不以bias self的shape直接作结果shape，也不在此检查所有batch/收缩维相等。因此不能用名字相近把Addbmm的广播shape合同移给Baddbmm。

三个包装均将beta、alpha原样交命令；没有本地beta==0/alpha==0的专用早退、输入省略或NaN处理分支。本卡未核对底层算术实现，不能由包装没有分支推导SDK一定读取被零系数屏蔽的数据，也不能据公式认定实际省掉了相应访存或乘法。

Addbmm_和Baddbmm_先做各自兼容分派，再把self作为out调用本文件out重载，因而会经过out自己的准备流程；它们没有在此自行重建全部广播/别名校验。Addmm functional两个主线重载及Baddbmm functional两个主线重载有FLOP_COUNT，发布普通functional也保留该宏；本组Addbmm文件没有对应本地计数调用。不能将这个局部观察升级为全局计数覆盖、实际指令数或测得吞吐。

### 精度透传和双版本差异

本组调用均把get_cube_math_type_with_passthrough()的结果传到命令，优先级按本卡前述固定getter实现复用，没有为beta/alpha另加新的精度开关。Explicit dtype的结果申请与CubeMathType是不同参数层，不能互相替代。

两版Addbmm完整phase2 token相同，注释只差namespace尾注；Addmm主线去掉新增两个typed函数的精确区间后，与发布全token/宏replacement/注释一致；Baddbmm同样只新增两个typed函数，余下函数体与发布同token，另有排版/namespace注释。Schema的typed重载、internal_format_opapi及主线Addmm的dvm标签差异单独保留，不能只比较同名普通函数就称整组版本无差异。

评估矩阵epilogue优化时，记录真正入口/重载、beta/alpha、显式输出dtype、bias与两矩阵的rank/format、首次SoC/符号判断、是否回退、最终out申请及CubeMathType。先验证同参结果、别名和自动梯度，再测NZ转换/复用和端到端成本；本卡没有进行运行验收。

## Bmm兼容路径：广播视图与切片分派（新增）

同一主线的BmmKernelNpuOpApi新增了广播恢复、batch1 stride规范化、窄切片分派以及两个typed重载；发布所选76行实现没有这些本地分支。两版CPP均实际完整读取，不能把它们按去空白后等价处理。它们共用本卡已记录的DO_MATMUL_COMPATIBILITY与精度getter，源证据按未变的既有卡复用；没有执行库探针、环境读取、as_strided、CANN或设备，也不从注释所称“避免额外算子”直接给出运行收益。

### 结果准备先于布局改写

两版各重载都先要求两个输入恰为3D，再做BatchMatMul/WeightNz兼容分派。主线结果shape按`[max(self.size(0),mat2.size(0)),self.size(1),mat2.size(2)]`申请或检查，发布则第0维只取self.size(0)。主线这个max写法不受下述兼容env控制，也不是任意不等batch、K不相容输入都合法的完整检查。

普通functional无格式结果取self.options，普通out按self.scalar_type准备；主线typed functional/out分别用output_dtype申请或检查。typed Schema仅[v2.9,newest]，兼容ACL表达式没有透传output_dtype，不能把OpAPI正常路径类型自动推广到回退。所有本地路径使用精度透传，执行后按原始输入计算/传播bmm名字；functional还有以原始self/mat2为参数的FLOP_COUNT，out没有同一计数调用。

### 实际命令优先级

| 主线分支 | 实际处理 |
|---|---|
| 右输入为NZ、左非NZ | 直接aclnnBatchMatMulWeightNz，不进入后述广播与切片准备 |
| 兼容启用，self满足窄dim1切片条件，mat2为广播展开 | 取mat2[0]，改调用aclnnMatmul，输出仍为预先准备的result |
| 其余 | maybe_restore_broadcast处理输入后执行aclnnBatchMatMul |

入口兼容宏探测的是BatchMatMul/WeightNz相关符号；这个切片分支没有单独先探测其后来选择的aclnnMatmul。符号存在、外部SDK支持和异常处理必须各自核对，不能说“所有实际命令已由同一入口探针认证”，也没有全函数的执行失败自动回退协议。

兼容helper首次调用以static auto保存std::getenv("TORCH_NPU_USE_COMPATIBLE_IMPL")的**指针**，之后判断该指针非空且所指字符串恰为"1"。这不是CheckCompatibleImpl的通用布尔解析，不接受本地代码未列出的true/yes；也不是每次重新getenv或首次就保存解析后的Bool。运行中改环境是否影响已有指针不能用这段代码作保证，应固定首次调用前的实际进程设置。

### 单侧广播恢复与batch1 stride

is_normal_broadcast_expanded只检查stride(0)==0且size(0)!=0，零batch不被当成普通广播。开启兼容且并非两侧同时广播时，某侧命中后用as_strided把它变为`[1,size(1),size(2)]`，stride改为`[size(1)*size(2),原stride(1),原stride(2)]`；只改batch视图描述，没有在这个helper调用contiguous或clone。完整view合法性及设备布局行为仍由外部实现决定。

随后两侧都执行normalize_batch1_stride：仅对3D且batch=1、stride(0)不等于size(1)*size(2)的对象重设该stride，矩阵两维stride原样保留；即使该侧本卡未经历广播恢复，也可能被规范化。两侧同时广播时更早直接返回原pair，连这一步规范化也跳过，不能只恢复两侧为batch1后仍宣称输出batch不受影响。关闭兼容也直接返回原pair。

### 窄切片判据不要按日志或整除方向改写

self的判据精确要求：3D、stride(0)非0、stride(2)==1、stride(1)==size(2)、stride(0)!=stride(1)*size(1)、size(1)>1且`16 % size(1)==0`。正整数size(1)因此是2/4/8/16，而不是`size(1)%16==0`允许任意16倍数。普通跨步切片若改变row stride也不满足这一窄条件。

分支还要求mat2满足广播判据，但没有要求self.size(0)==1；日志字符串中的“self [1,...]”不能补成准入条件。这里把mat2的第0个矩阵交aclnnMatmul，不能把相似的转置、切片、双侧广播或任意非连续layout全部纳入同一优化。注释旨在减少物理Broadcast/Transpose/复制，本卡未查看CANN生成图或测时，不证明它们已实际消失。

### 固定测试的覆盖边界

主线test_bmm_compatible.py完整202行实际读取；模块在导入torch前设兼容env为1，再设jit_compile=False、allow_internal_format=False。六个测试覆盖左侧广播、右侧广播、双侧广播、双零batch、广播梯度和batch1非标准stride。前三项和零batch使用FP32/FP16/BF16，低精度CPU参考先升FP32再转输出dtype；梯度与batch1 stride用例只含FP32/FP16。

广播梯度用例通过expand后torch.bmm并传ones_like做backward，比较输出及两路基Tensor梯度。双侧广播虽有docstring称不同batch sizes，实际两个base batch均为1，再都expand到同一个b=8；不能据这一个用例证明任意不同原始batch都支持。

batch1 stride用例先在CPU构造转置/异常stride(0)的as_strided视图，再调用.npu()并比较数值，没有断言迁移后NPU stride保持同一异常、没有记录规范化分支命中，也未计数物理Transpose。整个文件不单独检验窄dim1切片命令选择、typed/out重载、NZ分支或兼容关闭情形；测试存在不是本卡运行通过。发布精确测试路径Git为空只说明该路径缺失，不推导所有发布测试或广播功能缺失。

## 同族二维Mm的普通与typed变体

为一起核清二维与批矩阵变体，本卡还完整读取主线MmKernelNpuOpApi155行，并以其完整原始差异、phase2 token/注释核发布74行。两版普通mm/mm_out都先要求输入各为2D且K相等，计算matmul outnames后才做兼容分派；与前述Bmm仅本地要求3D的准备条件不同。输出shape是[self.size(0),mat2.size(1)]，functional取self选项、out普通重载以self.scalar_type准备；执行后传播名字，functional另调用mm FLOP_COUNT。

这个二维包装的普通路线实际为aclnnMm，NZ路线为aclnnMatmulWeightNz；不要把前面通用matmul helper的aclnnMatmul命令名原样套到它。格式兼容宏和共享getter仍按既有证据复用，没有在本组用2D正确性推断任意高维布局支持。

主线mm.dtype/mm.dtype_out与Bmm一样只在Schema[v2.9,newest]列OpAPI/internal-format，发布所选CPP/Schema没有对应typed重载。正常typed functional/out按显式output_dtype申请/检查结果，兼容ACL表达式却没有该参数。还有一个局部差异：typed重载的非NZ路线在get_cube_math_type_with_passthrough()之后，**再次**读取无参OpPreparation::get_cube_math_type()，若非负再覆盖；普通重载及typed NZ分支没有这次额外读取。不能据旧getter优先级把所有变体概括为完全相同的读取序列，也未由此测得性能或并发配置效果。

去掉主线两个typed函数的精确区间后，其余二维Mm完整phase2 token与发布相同，注释仅namespace尾注排版；它与Bmm那组真实新增helper、结果batch和命令选择差异应分开记录。所读Bmm兼容测试没有覆盖本段二维typed/out；不把共享dtype参数或相似命令当作运行支持认证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulKernelNpuOpApi.cpp)（primary）

- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulBackwardKernelNpuOpApi.cpp)（implementation）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulKernelNpuOpApi.cpp)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulBackwardKernelNpuOpApi.cpp)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）

- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

## 完整与有界来源

- [MatmulBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulBackwardKernelNpuOpApi.cpp)（implementation）：1–203；完整本地文件。
- [MatmulDoubleBackwardKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulDoubleBackwardKernelNpuOpApi.cpp)（implementation）：1–102；完整本地文件。
- [MatmulBackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulBackwardKernelNpuOpApi.cpp)（implementation）：1–203；完整本地文件。
- [MatmulDoubleBackwardKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MatmulDoubleBackwardKernelNpuOpApi.cpp)（implementation）：1–106；完整本地文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3394–3396、5825–5827；仅所列Schema条目。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3288–3290、5585–5587；仅所列Schema条目。

## 矩阵epilogue新增固定来源

- [AddmmKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddmmKernelNpuOpApi.cpp)（implementation）：1–192；完整本地小文件。
- [AddbmmKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AddbmmKernelNpuOpApi.cpp)（implementation）：1–96；完整本地小文件。
- [BaddbmmKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BaddbmmKernelNpuOpApi.cpp)（implementation）：1–97；完整本地小文件。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：212–224、354–369；仅所选完整helper/Schema。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：941–951、977–999、1315–1333；仅所选完整helper/Schema。
- [AddmmKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddmmKernelNpuOpApi.cpp)（implementation）：1–143；完整本地小文件。
- [AddbmmKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AddbmmKernelNpuOpApi.cpp)（implementation）：1–65；完整本地小文件。
- [BaddbmmKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BaddbmmKernelNpuOpApi.cpp)（implementation）：1–55；完整本地小文件。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：203–213、327–335；仅所选完整helper/Schema。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：912–922、948–960、1277–1287；仅所选完整helper/Schema。

## Bmm兼容准备与测试的新增固定来源

- [BmmKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BmmKernelNpuOpApi.cpp)（implementation）：1–284；完整本地小文件。
- [MmKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MmKernelNpuOpApi.cpp)（implementation）：1–155；完整本地小文件。
- [test_bmm_compatible.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_bmm_compatible.py)（example）：1–202；完整本地小文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1533–1550、3591–3608；仅所选完整Schema条目。
- [BmmKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BmmKernelNpuOpApi.cpp)（implementation）：1–76；完整本地小文件。
- [MmKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MmKernelNpuOpApi.cpp)（implementation）：1–74；完整本地小文件。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1483–1491、3492–3500；仅所选完整Schema条目。

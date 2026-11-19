---
type: Guide
title: 方差与标准差：correction分派和CPU往返边界
description: 明确Var/Std家族主线correction谓词触发的CPU计算与回写、发布版差异、正常路径兼容入口和输出维度准备。并含 nansum/nanmean 的无回退 aclnn 直发、整数 Long 提升与组合均值。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/VarKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/StdKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/StdMeanKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/VarKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/StdKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/StdMeanKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/StdVarCorrectionUtils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common_base.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NansumKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NanmeanKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NansumKernelNpuOpApi.cpp
  role: implementation
created_at: '2026-11-11T10:40:27Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 方差与标准差：correction分派和CPU往返边界

## 固定来源与实际入口

本文聚合OpAPI的var、var_out、var_mean、std、std_out与std_mean，OpPlugin固定主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。两版Schema对六个correction入口均声明acl_op/op_api为[v2.1,newest]，Scalar? correction默认None；这是固定声明，不认证产品、所有Scalar类型或软件安装组合。

[公开归约范围](torch_npu_native_torch_index_reduce_scope.md)已经提示std可能CPU回退及特定产品dtype边界，本卡补精确条件、检查顺序和复制请求。未执行上游、CPU算子、设备、数值或性能实验，未知平台保持draft、空平台；所读旧ACL兼容表达式不替代完整ACL实现审阅。

## 主线先判断correction，失败时直接请求CPU计算

主线六个入口先执行correction_fits_aclnn_int64；返回false时在DO_COMPATIBILITY之前进入CPU分支，原dim、correction Scalar和keepdim继续传给CPU算子，不先toLong。

| 入口 | 明确请求的CPU路线 |
|---|---|
| var、std functional | self.cpu()，调用同名at::var/at::std，再to(self.options())返回 |
| var_out、std_out | 先out.cpu()取得cpu_out，CPU out算子接收self.cpu()，随后out.copy_(cpu_out)，返回原out引用 |
| var_mean、std_mean | self.cpu()后调用CPU二元组算子，对每一项分别to(self.options())再组成返回元组 |

这些分支包含显式输入转CPU、输出回原选项或out复制请求；不能用最终Tensor仍在NPU或API名相同就省略Host计算与传输。已有CPU对象的.cpu()/.to()是否产生新的storage、复制等待和别名行为由外部实现与实际设备决定，本卡没有固定复制次数或耗时结论。CPU调用自身仍可能拒绝某些correction/dtype，进入该分支不等于CPU已经成功或一定可运行。

这也不是“任何SDK执行异常都会自动改CPU”：CPU选择发生在符号兼容和NPU执行之前，仅受这个谓词控制，局部没有对后续EXEC_NPU_CMD统一catch再重跑协议。

## 谓词按实际double与Scalar分支理解

主线StdVarCorrectionUtils.h完整定义的顺序如下：

1. correction缺省直接true。
2. s.isIntegral(true)直接true，没有在这一分支逐个再比较上下界。
3. 其他非浮点Scalar返回false。
4. 浮点先toDouble，非有限值返回false；v与trunc(v)不相等返回false；再与static_cast<double>(int64_t最大值/最小值)比较，越界则false，否则true。

因此普通分数如0.5会请求CPU路线，而2.0这样的有限整数值不因其原Scalar为浮点就自动改CPU。不能把条件简化为“correction不是整型dtype就CPU”，也不能把头文件注释扩大成对任意Scalar数学意义的完整int64转换安全证明：浮点边界比较本身使用double表示的上下限，整型分支直接true，返回true后外层仍执行Scalar.toLong()。本卡没有测试极值舍入、无符号宽整数或复杂Scalar的最终行为，也不替源码补造额外验证。

主线op_api_common.h包含op_api_common_base.h，后者包含此头文件；这里仅核对了精确include位置，没有运行编译。发布固定tree中没有同一路径StdVarCorrectionUtils.h，三份所读OpAPI CPP也没有这段谓词与CPU分支；路径缺失只表示该快照缺此文件，不能推出整个发行版绝无其他CPU执行能力。

## 发布版与主线正常路径仍有toLong边界

发布这六个入口直接进入原有兼容/参数准备，correction有值时调用toLong，无值则1；不能回填主线的分数/非有限CPU分支。主线谓词返回true后同样按这个规则准备int64参数，不在所读包装扫描correction与归约元素数的完整合法关系。

var/var_out使用aclnnVarCorrection，std/std_out使用aclnnStd，std_mean使用aclnnStdMeanCorrection；这三组正常路径都保留DO_COMPATIBILITY并指向对应旧ACL表达式。var_mean则在两版所读函数中直接EXEC_NPU_CMD(aclnnVarMean)，**没有**同样的DO_COMPATIBILITY。不要把var或std_mean的符号兼容保证套给var_mean，或将旧ACL表达式自动解释成上表CPU分支。

分数correction影响统计定义，不能仅为避开Host往返就随意取整或改默认值。先核调用者所需自由度、数值与梯度，再评估设备路线；本卡不提供改参数后语义等价或更快的运行结论。

## dim准备、输出shape与双输出申请

var/var_out未指定dim时使用空列表；std/std_out、var_mean和std_mean则先由get_dimlist_for_tensor生成0到self.rank-1的所有轴，有dim时替换成传入列表。shape helper的make_dim_mask把空列表解释为全部bit，非空列表调用make_wrap_dim并检查原dim在[-ndim,ndim-1]范围；ndim<=0时用于检查的ndim设为1。

reduce_ops_npu_output_size先复制self.sizes，从后往前遍历被mask选中的维度，keepdim时设1，否则删除。由此两种本地缺省表示均可构造全轴归约shape；不能把空列表一律误写成“不做归约”。该helper采用bitset<64>，本卡不把局部循环推成任意超高rank都合法，也未展开make_wrap_dim之外的完整设备约束。

正常functional输出申请使用self.options：var/std各一份，var_mean/std_mean各两份，不因最终均值与方差可共享某些计算就省略双输出申请请求。var functional申请后还显式check_tensor，std functional所读函数没有同样的这一步；两个out入口按self与计算shape检查out。不能将这些局部差异扩展成任意out设备、dtype、布局或别名组合都支持，也不能只由self.options申请就推导复杂输入统计结果的完整dtype矩阵。

局部正常路线没有因输入元素数为0或correction取特殊值就统一跳过SDK的分支；实际空归约、分母为零及NaN行为依赖所选算子与完整参数约束，本卡没有把Kernel注释或其他接口实测嫁接成这些入口的运行结果。

## 模型性能定位与验证入口

记录准确发行快照、六个入口中的具体重载、correction的原Scalar类型和值、dim/keepdim、self和out设备/shape/dtype。先确认是否走主线谓词失败的CPU路线，再分别观察输入Host拷贝、CPU归约、两个输出回迁或out.copy_；正常路径另核兼容符号和所用NPU算子，不把CPU与旧ACL路线合并。

优化前后验证统计定义、输出shape/dtype、数值与梯度，再比较Host/设备活动及端到端耗时。这里仅整理静态固定来源，没有新增运行记录、产品支持、性能数字或verified。

## Evidence

- [VarKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/VarKernelNpuOpApi.cpp)（primary）：1–94；完整本地入口或谓词头。
- [StdKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/StdKernelNpuOpApi.cpp)（primary）：1–69；完整本地入口或谓词头。
- [StdMeanKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/StdMeanKernelNpuOpApi.cpp)（primary）：1–47；完整本地入口或谓词头。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：77–113、127–142；仅所列完整helper/Schema或准确include，不提升整个源文件。
- [OpUtils.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）：206–213；仅所列完整helper/Schema或准确include，不提升整个源文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：4969–4979、5406–5416；仅所列完整helper/Schema或准确include，不提升整个源文件。
- [VarKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/VarKernelNpuOpApi.cpp)（implementation）：1–92；完整本地入口或谓词头。
- [StdKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/StdKernelNpuOpApi.cpp)（implementation）：1–55；完整本地入口或谓词头。
- [StdMeanKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/StdMeanKernelNpuOpApi.cpp)（implementation）：1–44；完整本地入口或谓词头。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：80–110、127–143；仅所列完整helper/Schema或准确include，不提升整个源文件。
- [OpUtils.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）：204–211；仅所列完整helper/Schema或准确include，不提升整个源文件。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：4814–4824、5239–5249；仅所列完整helper/Schema或准确include，不提升整个源文件。
- [StdVarCorrectionUtils.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/StdVarCorrectionUtils.h)（implementation）：1–45；完整本地入口或谓词头。
- [op_api_common.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：19–19；仅所列完整helper/Schema或准确include，不提升整个源文件。
- [op_api_common_base.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common_base.h)（implementation）：33–33；仅所列完整helper/Schema或准确include，不提升整个源文件。

## nansum/nanmean：无兼容回退的aclnn直发与组合均值

上文var/std家族由correction谓词触发CPU分支；本节补nan前缀归约两个入口作对照。nansum/nansum.out在主线与发布两版本都只登记`op_api: [v2.1, newest]`（主线yaml 3728–3732、发布3612–3616），无acl_op条目；`nanmean.out`只在主线登记（3725–3726），发布yaml全文rg零命中且发布树没有NanmeanKernelNpuOpApi.cpp——该负证据限定在这两份OpPlugin YAML与该命名文件检索，不能写发布支持nanmean，也不据此断言发布版PyTorch NPU的所有路径（未核对的组合/跨仓实现）都无法执行nanmean。两份手写OpAPI文件内都没有DO_COMPATIBILITY分支。

| 实际门槛→动作 | 失败/版本边界 |
| --- | --- |
| nansum functional（主线72–95）：整型self（isIntegralType含Bool）且**未显式给dtype参数**时dstType提升Long、否则self dtype；dim缺省经get_dimlist_for_tensor取全轴；shape复用上文reduce_ops_npu_output_size；按dstType `apply_tensor_without_format`申请后转调nansum_out | 未显式给dtype时整数nansum本地输出Long；与torch.sum提升惯例的运行等价性未验证。dtype参数优先于该提升（此时按dtype申请） |
| nansum_out（主线40–70）：dstType优先级为dtype参数>out.scalar_type()>self dtype；check_tensor以out自身dtype+reduce shape校验；单次`EXEC_NPU_CMD(aclnnReduceNansum,self,dimArray,keepdim,dstType,out)` | 本文件无兼容回退；aclnnReduceNansum符号缺失时的行为在EXEC_NPU_CMD公共宏内——该宏已由原生激活卡按同一主线版本读取（先TORCH_CHECK符号存在），本节不重复展开、不另立抛错/回退结论 |
| 主线新增check_resize_output（20–38）：out shape与推导不符且numel非零时发PyTorch弃用TORCH_WARN（"This behavior is deprecated, and in a future PyTorch release outputs will not be resized ..."），在check_tensor之前 | 发布无此helper（两文件去空白字符流的首个分歧）；发布对shape不符out的行为不由此推断 |
| nanmean.out（主线only，22–41）：先TORCH_CHECK拒绝**self输入**为整型/Bool（检查self.scalar_type()而非dtype参数；原文"nanmean(): integral types and 'Bool' are not supported for nanmean, even for empty tensors."）与要求self为浮点或复数（报错带实际self dtype）；factor=`at::isnan(self).logical_not_().sum(dim,keepdim)`；执行`op_api::nansum_out(self,dim,keepdim,dtype,out).div_(factor)`——dtype参数仍透传给nansum_out参与其dstType优先级 | 组合实现：本入口自身无独立aclnn均值命令、无dim列表与shape代码（完全依赖nansum_out路径）；isn/sum/div_各自经ATen派发、实现未核对；factor计数的dtype/设备行为未核对；factor为0（全NaN/空）时相除行为未核对未运行。发布yaml无nanmean登记且发布树无该命名OpAPI文件（限两份yaml与命名文件检索口径） |
| pin差 | 发布nansum（70行）与主线差异仅为缺check_resize_output及其调用、文件尾`// namespace op_api`注释与排版（其余token等价，整文件diff -u与去空白字符流核对）；nanmean为main-only注册与main-only文件 |

本节host侧均为「检查+一次aclnn直发或ATen组合」形态：不把host命令数当device kernel数，不作性能结论；nanmean组合内sum/div_是否命中NPU注册未在本节重读。未运行任何用例，无数值、性能或verified结论。

### nansum/nanmean 补充证据

- [NansumKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NansumKernelNpuOpApi.cpp)（primary）：1–96；完整本地小文件。
- [NanmeanKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NanmeanKernelNpuOpApi.cpp)（primary）：1–42；完整本地小文件；发布树无同名文件（负证据，限源集检索）。
- [NansumKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NansumKernelNpuOpApi.cpp)（implementation）：1–70；完整本地小文件；与主线差异为缺check_resize_output helper及调用、文件尾namespace注释、排版，其余token等价。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3725–3732；nanmean.out与nansum/nansum.out条目（该文件已列于frontmatter来源）。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3612–3616；仅nansum/nansum.out两条目，nanmean零命中（负证据）。

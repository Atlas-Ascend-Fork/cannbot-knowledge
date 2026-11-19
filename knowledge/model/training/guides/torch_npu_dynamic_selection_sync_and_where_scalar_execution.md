---
type: Guide
title: TorchNPU动态选择：输出定形、流同步与Where标量
description: 聚合Nonzero与MaskedSelect上界分配和同步定形、非连续out复制，以及Where真实标量谓词、dtype申请和设备搬运边界。并含 cpu_scalar 生成分支三例与主线独有边界。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NonzeroKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaskedSelectKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/WhereKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NonzeroKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaskedSelectKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/WhereKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py
  role: implementation
created_at: '2026-11-11T10:14:55Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 动态选择与Where：输出定形、流同步和标量搬运

## 固定来源与实际入口

本文聚合nonzero、masked_select和where的OpAPI包装。OpPlugin分别固定主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`；所用框架helper分别固定TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`、发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`。这些是各仓独立固定来源关系，**不是已认证安装组合**。没有导入、执行宏/helper、查库、同步、搬运、运行设备或测试；产品与完整执行范围未知，保持draft和空平台。

两版Schema均列nonzero与masked_select的functional/out，where单condition与三Tensor变体；where.self_out限定[v2.1,newest]，主线where.self另列dvm。标签说明固定声明，不认证所有dtype、设备、别名或编译后端。所读OpAPI入口的DO_COMPATIBILITY可能转给传入ACL表达式；它不等于CPU回退，完整旧ACL实现不在本卡范围中。

## 动态输出先按上界申请

| 操作 | 本地上界与类型 |
|---|---|
| nonzero普通非0D输入 | `[self.numel(),self.dim()]`，索引输出按Long申请/检查 |
| nonzero的numel=1且rank=0 | helper先调用self.is_nonzero()，据真值取[1,0]或[0,0]；这不是只读shape的路径 |
| masked_select | 对mask/self计算广播shape，以上界广播后mask.numel()作一维结果长度；functional按self申请，out按self dtype检查 |

masked_select的expand_outplace_npu在相同shape时返回原Tensor句柄，其他情况用infer_size并对两输入调用expand；这两个临时对象用于推导上界。变量名maskCast/selfCast不表示做过dtype cast，实际执行仍传原始self、mask，没有在这里先把全部输入物化成连续广播Tensor。外部expand、SDK内部展开与类型限制另核。

最终非零项少，不等于包装只申请了最终长度的内存；上界准备先于实际结果定形。0D nonzero还包含一次真值求取，完整ATen派发未在本组展开，不能把它省略或据名字机械统计“只有一个同步点”。本卡没有测峰值、复用或收缩后storage释放。

## 从SYNC宏追到当前流同步

两个动态输出执行helper都取并缓存aclGetViewShape地址；Nonzero在static初始化lambda内检查非空，MaskedSelect先保存地址再在后面检查。该指针检查发生在普通算子兼容分派通过之后，失败在本地报错，没有另包一个“缺ViewShape则自动改ACL/CPU”的分支。

调用顺序是EXEC_NPU_CMD_SYNC、查询实际view shape、resize输出。宏查询实际算子及GetWorkspaceSize符号，准备当前流、转换参数和所需workspace，再调用`OpCommand::RunOpApiV2(apiName,acl_call,true)`。两版RunOpApiV2可能排入Host任务队列或直接执行；其末尾只要sync为真，就明确调用`AclrtSynchronizeStreamWithTimeout(stream)`，因此这里有**当前流同步请求**，不能只解释成Host队列已排空，也不能在关闭CheckBlockingEnable后自动删去这一步。

这不是本卡对整设备/所有流同步、Host调用耗时或每种图捕获支持的证明。直接分支自身另有blocking配置及capture条件，而最后sync分支独立；框架更底层的stream、队列与捕获实现不在本卡重新资格中。源码未给整段宏统一设备失败后重跑另一实现的协议。

主线SYNC宏在workspace查询前Capture/ApplyDeterministicSnapshot，发布对应位置使用SetDeterministic；主线回调捕获列表另包含snapshot。不能把两段宏称作整段token等价，也不能仅据捕获列表补出所有worker线程再次应用状态的结论。两版RunOpApiV2日志实现也不同，但所选末尾sync请求都明确存在。

## ViewShape、resize与out复制分别核对

Nonzero把参数holder的Get<1>()、MaskedSelect把Get<2>()交aclGetViewShape，分别对应源码所用输出位置；随后把返回维度构造成Host侧shape并resize传给执行helper的out。正常流程在resize之后delete[] view_dims并置空。地址检查、状态检查或后续操作异常的完整资源恢复没有在这里统一RAII核对，不能把成功路径的delete注释当作全部异常清理已证明。

out重载先做上界shape/type准备，再以`result.is_contiguous()?result:result.contiguous()`选择对象执行。之后再次检查result是否连续，非连续时copy_(output)，返回传入result引用。于是out引用不代表没有临时连续缓冲和复制；动态resize发生在执行helper收到的out，局部非连续分支没有另一次显式result.resize_。应实际核对check_tensor整理后的对象、最终逻辑shape和copy_行为，不能仅据这些语句宣称每个非连续out已测试成功，也未据此复现某个错误。

descriptor参数holder在查询期间仍是局部活对象；底层ConvertTypes/ConvertedParams、workspace分配器和外部ACL内存协议独立，所列宏范围不提升整个op_api_common头文件或框架为完整支持资格。

## Where的输出dtype与输入标量不是同一步

单condition的where直接委托at::native::where，没有在该重载执行下面的SWhere三输入准备。三Tensor functional先广播self/other，再与condition广播，调用result_type(self,other)选**输出**dtype，按self选项申请结果；out重载则以out自身为check_tensor参照，没有在该函数重新按result_type选out dtype。

随后unify_tensors_to_npu只处理符合helper谓词的标量：OpPreparation::is_scalar_wrapped_to_tensor委托IsCPUScalar，实际条件是`tensor.dim()==0 && !torch_npu::utils::is_npu(tensor)`。它没有检查TensorImpl的wrapped-number标志，也不是严格限定device.type()==CPU。不能仅凭函数名将普通非NPU零维Tensor排除，或把所有.item()都称成从NPU取值；具体输入设备与值读取派发须分开看。

该函数按condition、self、other顺序寻找第一个**不满足**该谓词的Tensor，以其device作target_device。变量found_npu的名字没有额外执行NPU设备检查；非wrapped的普通CPU Tensor同样可能先被选中。全部满足标量谓词时，只发警告并返回原三元组，外层仍继续执行SWhere；这条警告不是CPU分派或整个operator提前结束的保证。非标量输入也没有在该helper自动统一迁移到同一设备。

## 标量复制实际会做什么

对每个命中谓词的对象，Where调用.item()，再传原对象dtype和target_device给copy_scalar_to_device；它不是把所有输入统一cast成前面的result_type。三参copy helper先建立NPUGuard(target_device)，再委托CalcuOpUtil：Scalar转Tensor后to指定dtype，pin_memory，取得当前NPU设备号，再to(PrivateUse1设备,原dtype,true,true)。这是本地固定路径中的dtype准备、pinned Host存储和设备复制请求，不由non_blocking请求推出Host一定不等待或复制已与计算重叠。

结果分配在标量统一之前发生。所读apply_tensor_without_format最终进入apply_tensor_use_empty：若options中的设备不是PrivateUse1，则改成PrivateUse1；保留指定NPU设备时仍交NPUNativeFunctions::empty，使用Contiguous memory_format。这解释为什么self是非NPU标量时不能直接把self.options理解成结果一定在CPU，也不能从后面的target_device选择推导分配前后所有多设备情形都已验证。

这些helper没有补齐任意CPU/CUDA/NPU混合输入支持；目标设备选择、守卫、Scalar来源、结果申请和SDK类型接受各有边界。本卡只读精确固定实现，不扩展产品或数据类型矩阵，也没有给出数值/性能通过结论。

## 版本对照与验收落点

三对小型算子CPP完整phase2 token一致，差异为排版及namespace尾注；输出上界、标量谓词/复制和empty helper所选主体也同token。SYNC宏与RunOpApiV2的真实快照/日志差异按前述保留，不将局部算子一致扩大成两仓完整runtime或CANN安装一致。Schema主线where.self多dvm标签，不能据发布缺这条标签断言发布所有DVM路径不存在。

分析动态图中Nonzero/MaskedSelect/Where成本时，同时保存实际重载、输入与mask的广播shape、上界和最终shape、out连续性、current stream、首次符号地址状态、标量谓词/输入设备、target_device和结果dtype；再用同参参考核输出、别名、梯度及真实时间/内存。包装调用、最终Tensor位置、resize或non_blocking标志均不能替代运行证据，本卡不新增verified。

## Evidence

- [NonzeroKernelNpuOpApi.cpp op-plugin d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NonzeroKernelNpuOpApi.cpp)（primary）：1–65；完整本地小文件。
- [MaskedSelectKernelNpuOpApi.cpp op-plugin d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MaskedSelectKernelNpuOpApi.cpp)（primary）：1–91；完整本地小文件。
- [WhereKernelNpuOpApi.cpp op-plugin d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/WhereKernelNpuOpApi.cpp)（primary）：1–93；完整本地小文件。
- [op_api_common.h op-plugin d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）：744–812；仅所列完整宏/函数/helper/Schema，其他外部语义另计。
- [KernelNpuOutputSize.cpp op-plugin d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：1000–1014；仅所列完整宏/函数/helper/Schema，其他外部语义另计。
- [op_plugin_functions.yaml op-plugin d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3372–3378、3867–3873、5444–5455；仅所列完整宏/函数/helper/Schema，其他外部语义另计。
- [NonzeroKernelNpuOpApi.cpp op-plugin dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NonzeroKernelNpuOpApi.cpp)（implementation）：1–68；完整本地小文件。
- [MaskedSelectKernelNpuOpApi.cpp op-plugin dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MaskedSelectKernelNpuOpApi.cpp)（implementation）：1–94；完整本地小文件。
- [WhereKernelNpuOpApi.cpp op-plugin dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/WhereKernelNpuOpApi.cpp)（implementation）：1–104；完整本地小文件。
- [op_api_common.h op-plugin dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：677–736；仅所列完整宏/函数/helper/Schema，其他外部语义另计。
- [KernelNpuOutputSize.cpp op-plugin dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：844–859；仅所列完整宏/函数/helper/Schema，其他外部语义另计。
- [op_plugin_functions.yaml op-plugin dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3267–3273、3759–3765、5277–5287；仅所列完整宏/函数/helper/Schema，其他外部语义另计。
- [OpPreparation.cpp pytorch ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）：106–116、122–124、392–411、521–526；仅所列完整宏/函数/helper/Schema，其他外部语义另计。
- [CalcuOpUtil.cpp pytorch ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp)（implementation）：250–260；仅所列完整宏/函数/helper/Schema，其他外部语义另计。
- [OpCommand.cpp pytorch ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpCommand.cpp)（implementation）：234–282；仅所列完整宏/函数/helper/Schema，其他外部语义另计。
- [OpPreparation.cpp pytorch f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）：110–121、128–128、385–408、517–523；仅所列完整宏/函数/helper/Schema，其他外部语义另计。
- [CalcuOpUtil.cpp pytorch f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/CalcuOpUtil.cpp)（implementation）：214–226；仅所列完整宏/函数/helper/Schema，其他外部语义另计。
- [OpCommand.cpp pytorch f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/OpCommand.cpp)（implementation）：232–283；仅所列完整宏/函数/helper/Schema，其他外部语义另计。

- [struct_codegen.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py)（implementation）：180–257；_gen_cpu_scalar_op_code/_gen_cpu_scalar_h2d_code 及其输入helper。
- [struct_codegen.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/struct/struct_codegen.py)（implementation）：全文 rg 负向核实无 _gen_cpu_scalar 函数（0 命中）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：2981–3017、3209–3236、4461–4479；lerp/logical_and/rsub 三族条目。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：2891–2919、3110–3136、4342–4360；对应条目，全文 rg 0 处 cpu_scalar。

## cpu_scalar 生成分支的三个登记实例

前文 IsCPUScalar 标量谓词在 where 之外还有一类**生成代码**形态：op_plugin_functions.yaml 的 gen_opapi `cpu_scalar_op`/`cpu_scalar_h2d` 标记（主线 2985–3017、3213–3234、4465–4476 行段）由 torchnpugen/struct/struct_codegen.py（主线 189–227、230–257）展开成包装分支。lerp/logical_and/rsub 三族共 8 个 Tensor 形参 schema 被登记：

| 名字（主线登记行） | 生成分支 |
| --- | --- |
| lerp.Tensor/lerp.Tensor_out/lerp_.Tensor（cpu_scalar_op: weight，2981–3017） | `if (npu_preparation::IsCPUScalar(weight)) { at::Scalar weight_scalar = weight.item(); EXEC(aclnnLerps/aclnnInplaceLerps, …); return; }`——CPU 0 维 weight 取 .item() 转 Scalar 走**标量过载**；lerp.Scalar/lerp_.Scalar 形参本就是 Scalar，直发 aclnnLerps/aclnnInplaceLerps、不生成分支 |
| logical_and/logical_and.out/logical_and_（cpu_scalar_h2d: [other]，3209–3236） | `at::Tensor other_cp = other; if (IsCPUScalar(other)) { at::Scalar s = other.item(); other_cp = copy_scalar_to_device(s, other.scalar_type(), device_expr); }`——CPU 0 维 other 的值按原 dtype 复制到目标设备（本族取首个非复制 Tensor 形参 self 的设备），命令实参换成 other_cp；主 exec aclnnLogicalAnd/aclnnInplaceLogicalAnd 不变 |
| rsub.Scalar/rsub.Tensor（cpu_scalar_h2d: [self]，4461–4479） | self 为 CPU 0 维时同上 H2D 复制（rsub 的被减数是 self），直发 aclnnRsubs；rsub.Tensor 另叠加 cpu_scalar_op: other 的 .item() 标量过载分支（4475–4479），主 exec aclnnRsub |

标量过载分支按 cpu_scalar_op 条目逐个生成、命中即先于默认 exec 返回；h2d 复制不改变主 exec 选择。h2d 目标设备由生成 helper 统一选择（struct_codegen.py 242–249），顺序为：首个非复制 Tensor 形参的 device()，否则另一个复制参数的 device()，最后才退回 c10::Device(PrivateUse1)；三族 cpu_scalar_h2d 各只有一个复制参数，logical_and.other 与 rsub.Tensor.self 落在首序（分别取 self/other 的设备），rsub.Scalar 无非复制 Tensor 形参、落到 PrivateUse1 兜底——不宣称多复制参数场景一律走默认设备。该机制与本卡 where 小节的 IsCPUScalar/copy_scalar_to_device helper 同源，但它是**注册驱动的生成代码**，不是手写包装；不能用 where 包装的手读行为直接代换这些生成分支的全部细节。

**版本边界：整个 cpu_scalar 生成特性是主线独有。** 发布版本 的 op_plugin_functions.yaml 全文 0 处 cpu_scalar 标记（rg 负向核实），同名 8 个 schema 以普通 gen_opapi 直发张量过载（aclnnLerp/aclnnLogicalAnd/aclnnInplaceLogicalAnd/aclnnRsub；rsub.Scalar 直发 aclnnRsubs），发布 struct_codegen.py 亦无 _gen_cpu_scalar 函数（rg 0 命中）。即同一 CPU 0 维 weight/other/self 在发布生成包装里不做 .item() 标量切换、也不做 0 维 H2D 复制，按普通张量路径进入张量过载。这一分支差异是静态注册事实；未验证任一版本的实际设备行为、数值一致性与性能差异。

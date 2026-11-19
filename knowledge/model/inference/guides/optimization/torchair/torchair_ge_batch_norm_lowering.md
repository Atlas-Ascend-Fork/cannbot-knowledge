---
type: Guide
title: GE批归一化：训练统计量、布局与梯度分支
description: 核对两份固定TorchAir源码中BatchNorm训练推理、统计量顺序、布局标注、同步片段及部分梯度的构图边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit_no_training.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit_no_training.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit_functional.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit_functional.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_batch_norm_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_batch_norm_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_elemt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_elemt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_backward_elemt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_backward_elemt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_backward_reduce.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_backward_reduce.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_batch_norm_gather_stats_update.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_batch_norm_gather_stats_update.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py
  role: implementation
created_at: '2026-11-10T08:42:35Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE批归一化：训练统计量、布局与梯度分支

## 版本、架构选择与证据范围

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。主线完整非空源码、发布版完整AST和注释差异均已审阅。18组实际成对文件中17组AST一致，GroupNormSilu仅docstring空白不同；量化RMSNorm反向的一条映射路径仅主线存在，不据此断言发布软件没有该能力。

is_arch35在主线按设备名包含Ascend910_95、Ascend950或Ascend350选分支，发布版只查前两种；仅捕获ImportError，不能当成完整产品支持矩阵。950对应Ascend950系列（包含旧称Atlas A5），原始设备字符串保留用于分支核对。本卡平台矩阵未知，保持draft与空平台；未执行上游、GE编译、精度/训练或性能实验。declare_supported是候选输入声明，不等于实测覆盖。

specific_op_input_layout/output_layout仅向节点属性追加索引和布局字符串，函数不执行Transpose、数据搬运或物理存储检查。因此下述NCHW/NCDHW/ND标注不独立证明数据已转换或任意stride可用。

## 训练前向、无统计量和函数化不能混写

| 准确入口 | 构图及返回合同 |
| --- | --- |
| _native_batch_norm_legit.default | training=False直接RuntimeError，rank<2拒绝；只有is_arch35分支调用BatchNormV3，其他架构选择直接NotImplementedError。GE五返回按(output,batch_mean,batch_variance,mean,variance)重排。源码Schema注释只写三返回，不能用注释掩盖函数实际五项元组，外围消费仍须单独核对。 |
| _native_batch_norm_legit.no_stats | 同样要求training=True、rank>=2和is_arch35；running_mean用0、running_var用1按通道大小填充，再BatchNormV3，返回(output,batch_mean,batch_variance)。不是推理统计量分支。 |
| _native_batch_norm_legit_functional.default | 要求training=True和rank>=2；先TensorMove(running_mean/running_var)，再BatchNormV3，没有default的is_arch35拒绝分支。局部变量接收(output,mean,var,save_mean,save_rstd)并原序返回五项；不能按上一行的重排方式解释。两次拷贝用于隔离源running统计量，不能为消除搬运就直接删除。 |

这些入口权重或bias为None时，以Shape(input,INT32)的通道索引1构造1/0填充，标量Cast为input.dtype。rank2/3补到4维；rank>5把前四轴及-1组成5维，再恢复原Shape；rank<=4标NCHW，其他标NCDHW，恢复Reshape标ND。Shape是INT32，不能从SymInt签名推导所有极大或动态维度均无损。高层BatchNorm模块的track_running_stats与内部训练形参属于不同层次，继续核对[ATen清单](torchair_aten_constraint_review.md)。

## 推理前向返回空统计量

_native_batch_norm_legit_no_training.default要求rank>=2，缺weight/bias同样填1/0；构造Shape=[0]、input.dtype的empty，并返回(output,empty,empty)，后两项为同一构图对象。is_arch35走BatchNormV3(is_training=False)，rank>5先压到5维；其他选择走BNInfer，rank>=5压为[N,C,D,-1]四维。两条路径均恢复必要的输出形状，不能将空统计量拿给需要训练saved统计量的反向。

out重载直接抛RuntimeError，报错里的“before pytorch 2.1.0/might be supported”只是该快照字符串，不是版本可用承诺。

## Native反向的统计量、精度和掩码

native_batch_norm_backward.default要求rank>=2，weight=None填input.dtype的1。is_arch35调用BatchNormGradV3，传running和saved统计量以及is_training；推理模式如请求weight/bias梯度，还单独把dy、x、running_mean和running_var转FP32，计算(x-mean)*(var+eps)^(-0.5)与dy的归约，最后按相应Meta dtype回转。NCHW归约[0,2,3]、NCDHW归约[0,2,3,4]；训练模式没有这段推理补算。

其他架构选择：训练取save_mean/save_invstd，推理取running_mean/running_var；先BNTrainingUpdateGrad或BN3DTrainingUpdateGrad，输入梯度再分别走BNTrainingReduceGrad或BNInferGrad。该分支没有上述独立FP32推理补算，不能假定与另一架构完全相同的中间精度或统计量解释。

两种架构均对rank2/3补维，对rank>5折叠和恢复形状。最终__mask_output只在output_mask[1]/[2]为False时返回对应None，**不按output_mask[0]屏蔽grad_in，也不由此证明输入梯度计算被剪掉**。选择部分梯度的优化需检查最终图，不能只看bool[3]签名。out重载为直接RuntimeError。

## 同步BatchNorm片段不自行建立通信

| 准确入口 | 局部计算与边界 |
| --- | --- |
| batch_norm_elemt.default | inp必须4维；参数running_var按1/(running_var*running_var)-eps还原为var，再传推理BatchNormV3（is_arch35）或BNInfer。不应把此处参数名直接解读为已经是普通方差，weight/bias虽可选但本层不补默认值。 |
| batch_norm_backward_reduce.default | grad_out必须4维，input_g、weight_g、bias_g必须全True；对除通道1外所有轴，求dy*x及dy之和，再SyncBatchNormBackwardReduce；返回(sum_dy,sum_dy_xmu,grad_weight,sum_dy)，第一与第四项复用同一结果。weight形参未参与本层计算。 |
| batch_norm_backward_elemt.default | grad_out必须4维；对count所有轴求和作除数，sum_dy/sum_dy_xmu除该数；mean、invstd、weight及两个均值补维广播到Shape(inp)，再SyncBatchNormBackwardElemt。weight=None虽在签名允许，这条路径没有对应保护；零count和任意广播未由局部检查证明。 |
| torch.ops.npu.batch_norm_gather_stats_update.default | 检查self.rank==4，counts转INT32；all_sum、sequare_sum、counts、running统计量传SyncBatchNormGatherStats，指定momentum和eps；四个GE结果只返回batch_mean、batch_invstd。本层self未作为GE数据输入，也没有把mean/variance额外Assign回用户对象。 |

这些片段消费已经提供的统计量和count，函数本身没有显式创建进程组或调用AllReduce/AllGather。不能凭Sync或gather名字认证分布式通信、统计量写回或跨卡一致性已完成；应继续审阅调用方与图后处理。

## 优化前核对

按真实FX准确入口检查train、rank、saved/running统计量含义、tuple顺序和输出Meta；比较缺weight/bias、空输入、混合精度及部分梯度的最终图，再评估布局标注、函数化拷贝和归约成本。本次没有运行这些验证。通用开发方法见[Converter指南](torchair_converter_implementation.md)。

## 准确入口与拒绝重载

表中仅表示所选Python映射有构图分支，不表示参数、平台或kernel已验证；范围由前文逐项限定。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| _native_batch_norm_legit | `torch.ops.aten._native_batch_norm_legit.default`、`torch.ops.aten._native_batch_norm_legit.no_stats` | `torch.ops.aten._native_batch_norm_legit.out` (NotImplementedError)、`torch.ops.aten._native_batch_norm_legit.no_stats_out` (NotImplementedError) |
| _native_batch_norm_legit_no_training | `torch.ops.aten._native_batch_norm_legit_no_training.default` | `torch.ops.aten._native_batch_norm_legit_no_training.out` (RuntimeError) |
| _native_batch_norm_legit_functional | `torch.ops.aten._native_batch_norm_legit_functional.default` | 无无条件拒绝壳；仍受正文条件限制 |
| native_batch_norm_backward | `torch.ops.aten.native_batch_norm_backward.default` | `torch.ops.aten.native_batch_norm_backward.out` (RuntimeError) |
| batch_norm_elemt | `torch.ops.aten.batch_norm_elemt.default` | 无无条件拒绝壳；仍受正文条件限制 |
| batch_norm_backward_elemt | `torch.ops.aten.batch_norm_backward_elemt.default` | 无无条件拒绝壳；仍受正文条件限制 |
| batch_norm_backward_reduce | `torch.ops.aten.batch_norm_backward_reduce.default` | 无无条件拒绝壳；仍受正文条件限制 |
| npu_batch_norm_gather_stats_update | `torch.ops.npu.batch_norm_gather_stats_update.default` | 无无条件拒绝壳；仍受正文条件限制 |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit_no_training.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit_no_training.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit_functional.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_native_batch_norm_legit_functional.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/native_batch_norm_backward.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/native_batch_norm_backward.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_elemt.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_elemt.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_backward_elemt.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_backward_elemt.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_backward_reduce.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/batch_norm_backward_reduce.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_batch_norm_gather_stats_update.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_batch_norm_gather_stats_update.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py)（implementation）

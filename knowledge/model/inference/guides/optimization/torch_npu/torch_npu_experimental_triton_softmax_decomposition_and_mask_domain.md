---
type: Guide
title: 实验Triton分解注册：softmax宽度路由与掩码语义前提
description: 保存共享表安装顺序、safe_softmax输入域、按归约宽度的raw节点路由和反向/折叠覆盖，区分分解命中与数值验收。
tags:
- task.optimization
- topic.compilation
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/decomposition.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
created_at: '2026-11-11T08:42:52Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton分解注册：softmax宽度路由与掩码语义前提

## 固定实现及共享表

针对TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的decomposition.py所列完整函数与实验config片段。它直接导入torch._inductor.decomposition的decompositions/register_decomposition，以及torch._decomp的decomposition_table/remove_decompositions，不是本地新建一份完全隔离的注册表。没有导入上游、修改注册、追踪/生成图、执行softmax或模型；平台未知，保持draft和空平台。

本卡补[后端激活和回退注册](torch_npu_experimental_triton_activation_and_lowering_routes.md)明确保留的分解层。只审所列函数；GELU、RMSNorm、dropout、RNG gate、BatchNorm和matmul backward的被调正文仍按各自范围处理，不能因为安装函数调用了它们就把全部实现提升为完成。

## 安装顺序和排除列表

_register_triton_experimental_decompositions先准备排除列表：convolution_backward、native_dropout、max_pool2d_with_indices及反向、adaptive_max_pool2d、embedding及dense backward、expm1、reflection_pad2d及反向、bilinear2d及反向；当is_a5谓词为真时，把两个embedding项从这张列表移除。这里记录实际谓词，不用名字推断所有产品的能力矩阵。

接着清部分implicit dispatcher分解、注册bilinear2d.vec dispatcher、对列表调用remove_decompositions，并清fast_random_decomps缓存。随后依序安装matmul should_fold、softmax backward、safe_softmax、普通softmax宽度、GELU/RMSNorm/native dropout覆盖，写BatchNorm两项，再调RNG gate；若matmul_backward.default还没在decompositions中才注册本地反向函数，最后注册expm1并再次清缓存。

这是一次顺序修改，不是本地事务；中途异常没有统一回滚已写表项，也没有finally保证末尾清缓存执行。不能将排除列表、单个配置或模块导入成功当全部覆盖已原子安装。remove_decompositions与各外部dispatcher/被调override的完整实现不在本卡展开。

disable_implicit_decomposition带@run_once，外部装饰器的完整生命周期行为另计。函数按字符串匹配nearest1d/2d/3d与bilinear2d的vec/default，对decomposition_table中匹配op的py_kernels删除Autograd及CompositeImplicitAutograd项。它处理的是这两个dispatch key，不是在这里删光全部CPU/NPU实现或直接证明最终图只剩原生kernel。

## safe_softmax改写有输入域假设

_override_safe_softmax_decomp只有调用时safe_softmax_aclnn_fallback为真才安装：给aten._safe_softmax.default写新分解，删除packet分解并移除packet/default已有lowering。wrapper在dtype非None时先x.to(dtype)，再调用aten._softmax(x,dim,False)。源码初值开关True；安装后仅把配置改False并不会在这个函数里自动恢复旧表项。

新wrapper没有保留原safe语义中的“整行全为负无穷时归零”保护。注释将其视为目标输入域中的死分支，依赖因果对角或外部模型预处理不会留下完全遮蔽行；本地函数既不检查这个前提，也不重建该guard。因此不能从开关名字中的fallback或某个模型示例，推导任意mask/全遮蔽行与原safe_softmax逐项等价。该wrapper自身也没有NPU device门槛，实际使用范围需结合共享表与调用路线核对。

它调用的是普通_softmax，后者仍可能按宽度保留分解；不能把这步改写概括为所有safe_softmax无条件直达原生设备kernel。注释提及的外部模型修正、示例时间和“bit-identical”不是本次执行或完整输入域证据。

## 普通softmax看归约宽度，且严格大于阈值

_override_plain_softmax_width_decomp先取现有_softmax.default分解orig；没有就整个返回。新wrapper对非NPU Tensor直接调用orig。对NPU每次读取softmax_aclnn_max_fuse_numel；只有bound>0、可取得size[dim]且width是Python int并严格大于bound时，才尝试保留raw _softmax节点。负dim只按len(sizes)+dim转换；取尺寸异常转width=None，之后交orig。

该阈值源码初值256，判断的是指定归约轴宽度，不是Tensor总元素数，也不是注释中的1024。宽度等于256、符号/未知宽度、bound<=0均走orig；配置为0关闭的是这个宽度分支，不能概括成移除所有原生softmax fallback或撤销其他已安装表项。half_to_float沿原调用参数传递。

对宽行，函数收集共享decompositions、select_decomp_table返回表，以及存在时proxy mode的decomposition_table，按对象id去重；临时pop这几张表中的_softmax.default，再调用aten._softmax生成raw节点。finally只把保存值非None的项写回。get_proxy_mode异常会退为没有mode，但表获取、pop和调用不是全部包在一个统一静默回退中；不能保证任何依赖/追踪错误都自动回orig。

这段临时修改没有本地锁，也不是复制表内容后在私有表上运行。它为选定追踪路线避免递归分解，不认证任意并发或重入场景。安装末尾直接给lowerings[_softmax.default]设置fallback_handler(...,add_to_fallback_set=True)，使留下的raw节点有lowering；与窄行orig分解同时保留，而不是用make_fallback统一删除分解。

## softmax反向和matmul折叠是另外的覆盖

_softmax_backward_data_no_fma通过pw_cast_for_opmath包装，计算new_grad_output=grad_output*output、sum_new_grad=sum(...,keepdim=True)、grad_input=new_grad_output-output*sum_new_grad；grad_output.dtype不等于input_dtype时转回input_dtype，返回contiguous。它把上游FMA路径换成mul/sub表达式，不能仅按实数代数相同宣称所有浮点结果逐位一致；外部opmath装饰器及设备算术仍独立。

matmul should_fold覆盖先取按ndim排序的两个输入；较高rank>=3且较低rank<=2就True，否则委托原should_fold。它没有在这个wrapper里以原始左右位置、连续性或device进一步限流；其自身用_npu_fold_3d_2d标记避免再次包装。True只选择分解中的fold候选，仍不证明reshape/复制/最终mm支持所有形状，也不能把它说成所有batched matmul统一变mm。

末尾本地expm1分解实际为torch.exp(x)-torch.ones_like(x)，不是在这里调用专用expm1原生算法；不由该表达式推断所有小值、dtype或误差特性都已数值验收。其余登记项只按安装顺序记录，不扩展未覆盖的设备数学实现。

排查性能与精度时应分别记录安装前后的表项、safe输入域、有效dtype、NPU门槛、dim/width/阈值、raw节点是否存活、实际fallback lowering、反向表达式与缓存清理是否完成。分解命中、少一串mask算子或减少FMA不能单独替代完整模型精度、梯度与设备性能验证。

## 固定来源

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/decomposition.py)：1–20、609–801、1146–1221；仅所列有界内容。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)：295–311、471–471；仅所列有界内容。

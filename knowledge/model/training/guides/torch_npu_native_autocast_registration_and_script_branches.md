---
type: Guide
title: TorchNPU AMP原生注册：版本策略、状态桥接与脚本分支
description: 对照两版Autocast注册、四个PrivateUse1状态方法与完整Python包装，核对脚本分支和私有容器cast边界。
tags:
- task.implementation
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/AutoCastOps.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/utils/AutocastMode.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/utils/AutocastMode.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/amp/autocast_mode.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/amp/common.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/amp/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/AutoCastOps.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/utils/AutocastMode.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/utils/AutocastMode.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/amp/autocast_mode.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/amp/common.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/amp/__init__.py
  role: implementation
created_at: '2026-11-11T04:36:24Z'
updated_at: '2026-11-11T04:36:24Z'
platforms: []
---

# TorchNPU AMP原生注册：版本策略、状态桥接与脚本分支

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf和发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b，完整读取两版AutoCastOps、AutocastMode.cpp/h及AMP Python autocast/common/导出模块。产品与完整配套待核，保持draft、空平台；没有导入torch_npu、展开外部ATen宏、运行JIT或设备数值测试。公开上下文与产品范围复用[Autocast迁移](torch_npu_autocast_and_custom_autograd.md)。

## Autocast dispatch注册的版本边界

两版都在全局AutocastPrivateUse1注册makeFallthrough，在aten的同一key下注册精度策略。这里的fallthrough没有为所有NPU算子提供新的kernel或全覆盖dtype支持；算子分派、eligibility、实际cast和cache实现还取决于所配ATen。

主线从外部ATen头的AT_FORALL_LOWER_PRECISION_FP、AT_FORALL_FP32、AT_FORALL_FP32_SET_OPT_DTYPE、AT_FORALL_DIFFERENT_REDISPATCH_SIGNATURE、AT_FORALL_PROMOTE构造对应注册，另外显式把cudnn_convolution/cudnn_convolution_transpose注册到lower_precision_fp。该文件没有包含五组宏的完整定义，不能仅据这里给主线展开一份固定所有算子清单，也不能照搬下方发布清单称两版逐项相同。cudnn名称出现只证明该注册代码，不是NPU对应kernel已验证。

发布文件则逐项写KERNEL_PRIVATEUSEONE：34条lower_precision_fp、46条fp32、17条fp32_set_opt_dtype、10条promote，共107条；另有3条norm不同redispatch签名。下面保留本地准确名称和重载后缀，策略名不自动成为所有输入/out/显式dtype组合的运行承诺。

| 发布策略 | 精确本地注册（点后为重载名） |
| --- | --- |
| lower_precision_fp | _convolution.deprecated、_convolution、conv1d、conv2d、conv3d、conv_tbc、conv_transpose1d、conv_transpose2d.input、conv_transpose3d.input、convolution、cudnn_convolution、cudnn_convolution_transpose、prelu、addmm、addmv、addr、matmul、einsum、mm、mv、linear、addbmm、baddbmm、bmm、chain_matmul、linalg_multi_dot、_thnn_fused_lstm_cell、_thnn_fused_gru_cell、lstm_cell、gru_cell、rnn_tanh_cell、rnn_relu_cell、_scaled_dot_product_flash_attention、scaled_dot_product_attention |
| fp32 | acos、asin、cosh、erfinv、exp、expm1、log、log10、log2、log1p、reciprocal、rsqrt、sinh、tan、pow.Tensor_Scalar、pow.Tensor_Tensor、pow.Scalar、softplus、layer_norm、native_layer_norm、group_norm、frobenius_norm.dim、nuclear_norm、nuclear_norm.dim、cosine_similarity、poisson_nll_loss、cosine_embedding_loss、nll_loss、nll_loss2d、hinge_embedding_loss、kl_div、l1_loss、smooth_l1_loss、huber_loss、mse_loss、margin_ranking_loss、multilabel_margin_loss、soft_margin_loss、triplet_margin_loss、multi_margin_loss、binary_cross_entropy_with_logits、dist、pdist、cdist、renorm、logsumexp |
| fp32_set_opt_dtype | prod、prod.dim_int、prod.dim_Dimname、softmax.int、softmax.Dimname、log_softmax.int、log_softmax.Dimname、cumprod、cumprod.dimname、cumsum、cumsum.dimname、linalg_vector_norm、linalg_matrix_norm、linalg_matrix_norm.str_ord、sum、sum.dim_IntList、sum.dim_DimnameList |
| promote | addcdiv、addcmul、atan2、bilinear、cross、dot、grid_sampler、index_put、tensordot、scatter_add |

fp32_append_dtype另外覆盖norm.Scalar、norm.ScalarOpt_dim、norm.names_ScalarOpt_dim，改为附带ScalarType的redispatch签名。源码注释提醒norm不隐式promote；不能将promote和append dtype当作相同策略。发布在显式dtype注释后仍实际注册sum、sum.dim_IntList、sum.dim_DimnameList到fp32_set_opt_dtype，不能按“commenting these out”注释宣布三项已关闭。

两版都把aten::binary_cross_entropy挂到立即AT_ERROR的banned函数。错误说明提及binary_cross_entropy/BCELoss及前置sigmoid场景，提示使用with_logits组合；发布另把binary_cross_entropy_with_logits列入fp32。这个禁止入口与常规dtype策略要分别记录，不能把所有BCE形式合并成同一可用性结论。

## 四个原生状态方法

AutocastMode.cpp返回PyMethodDef表：set_autocast_enabled/set_autocast_dtype为METH_O，is_autocast_enabled/get_autocast_dtype为METH_NOARGS。头文件仅声明导出的autocast_mode_functions，不包含另一份策略表。

enabled setter要求PyBool_Check，并以arg==Py_True把值交at::autocast::set_autocast_enabled(at::kPrivateUse1,...)；不能用“整数可转bool”替代这个本地类型检查。dtype setter要求THPDtype_Check，取scalar_type后交ATen的PrivateUse1 setter，没有在本函数另列只许FP16/BF16的白名单。getter分别读取PrivateUse1开关和当前dtype，后者取得THPDtype并INCREF后返回。

这些类型检查、返回值和选定dispatch设备只证明状态桥接。setter没有增加算子或硬件dtype能力，候选能力列表另见[Autocast状态API](../apis/torch_npu/autocast_state.md)；外部ATen状态与线程/嵌套实现没有在这两个本地文件重新定义。

## Python上下文与脚本化分支

两版autocast_mode.py完整AST相同。autocast继承torch.amp.autocast_mode.autocast，普通构造固定device='npu'，默认enabled=True、dtype=torch.float16、cache_enabled=True；enter/exit/call正常委托super。显式选择BF16仍需实际设备和算子合同，不从模型权重类型推定。

torch._jit_internal.is_scripting为真时，构造只保存_enabled/device/fast_dtype并返回，没有调用super或保存cache_enabled；enter返回self，exit返回None，call直接返回原func。本地脚本分支没有沿普通上下文进出调用链，实际JIT变换仍由外部消费者决定，不能仅据这些Python返回值推断整个脚本模型的真实执行精度。

custom_fwd/custom_bwd由typing_extensions.deprecated标记FutureWarning，直接经functools.partial转发torch.amp对应函数并固定device_type='npu'；forward保留fwd/cast_inputs参数。旧入口存在不代表其本地另实现一套完整前反向cast逻辑。

## 私有_cast的容器及缺NumPy分支

_cast只对浮点、device.type为npu且非float64的Tensor执行.to(dtype)，其余Tensor原样返回。str/bytes和已识别的np.ndarray透传；Mapping递归转换键和值并生成普通dict；list/tuple重建对应类型，其它Iterable返回惰性map，不保证保留原容器类型或立即遍历。

import NumPy成功才设置HAS_NUMPY=True。ModuleNotFoundError分支只令np=None，没有设置HAS_NUMPY=False，因此私有helper处理不是Tensor/str/bytes的输入时会读取这个本地未赋值的全局名。这是已读代码的分支事实，未运行缺NumPy试验；该文件的custom装饰器直接转发torch.amp，没有调用本地_cast，不能把私有helper条件外推为所有公开AMP调用有同一行为。

common.amp_definitely_not_available只返回not torch_npu.npu.is_available()，不是逐dtype/算子支持探针。AMP包__all__导出autocast、GradScaler、custom_fwd、custom_bwd，并从各自模块导入；不包含本卡未全文读的GradScaler实现合同，复用[缩放次序与状态](torch_npu_grad_scaler_contract.md)。

评估时保存实际版本、dispatch key、上下文dtype、算子重载、显式dtype、脚本/普通路径和真实数值验收。本文覆盖本地注册/包装，不把注释、宏名字、候选dtype或没有运行的测试当成验证结果。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/AutoCastOps.cpp)（primary），读取范围 1–61。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/utils/AutocastMode.cpp)（implementation），读取范围 1–62。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/utils/AutocastMode.h)（implementation），读取范围 1–11。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/amp/autocast_mode.py)（implementation），读取范围 1–98。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/amp/common.py)（implementation），读取范围 1–5。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/amp/__init__.py)（implementation），读取范围 1–6。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/AutoCastOps.cpp)（implementation），读取范围 1–159。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/utils/AutocastMode.cpp)（implementation），读取范围 1–73。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/utils/AutocastMode.h)（implementation），读取范围 1–11。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/amp/autocast_mode.py)（implementation），读取范围 1–98。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/amp/common.py)（implementation），读取范围 1–5。
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/amp/__init__.py)（implementation），读取范围 1–6。

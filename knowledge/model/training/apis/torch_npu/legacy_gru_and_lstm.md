---
type: API
title: 旧GRU/LSTM：低层中间输出与单层约束
description: 区分低层六/八输出和nn模块协议，不复制文档中的缺省参数及方向拼写。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_gru.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_lstm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_lstm.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_lstm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GruKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GruKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LstmKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LstmKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GRUKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GRUBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LSTMKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LSTMBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LSTMBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LstmCellKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LstmCellKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LstmKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LstmKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LstmCellKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LstmCellKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/_thnnFusedGruCellNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/_thnnFusedGruCellBackwardNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/_thnnFusedFruCellNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
created_at: '2026-11-09T20:27:55Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
---

# 旧GRU/LSTM：低层中间输出与单层约束

## 固定版本及消费边界

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文与主线d84e9b1d6a558e5f27973cd4329f62968e46fdda实际收录的中英文页。发布对应ascend_26_0_pt28；TorchNPU实现发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b、独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf分别消费，不将两个main当配套发行。

默认平台A2/A3仅指各页所列范围；主线新增产品或参数另明确版本，旧Atlas不自动映射新型号。beta及计划废弃是上游接口状态，知识卡stable不表示推荐新模型使用或运行verified。本卡未做上游导入、模型加载、设备执行、反向或性能实验；注册all_version不是全硬件保证，底层Kernel实现不在本卡结论范围。


## GRU

npu_gru输入input、hx、weight_input、weight_hidden、bias_input、bias_hidden、seq_length，以及has_biases、num_layers、dropout、train、bidirectional、batch_first。文档计划废弃并指向torch.gru；低层使用DynamicGRUV2并返回六份训练相关结果，不是nn.GRU常见的(output,h_n)二元组。门和隐藏中间量、混合dtype及私有格式须按该接口消费，不能直接用元组解包迁移。

输入FP16/NZ，hx为FP16或FP32/NZ；两个weight为FP16/FRACTAL_Z，两个bias为FP16或FP32/ND，seq_length为INT32/ND。六输出依次y、output_h、update、reset、new、hidden_new，列FP16/FP32及NZ。jit_compile=False需把DynamicGRUV2加入NPU_FUZZY_COMPILE_BLACKLIST，不是整个模型可无条件禁JIT；两个schema中的上述bool/int/float仍是必传参数，文档“默认True”等不是Python签名默认值。本卡只静态阅读公开包装，未核对整套GRU内部helper和反向实现。

## LSTM

npu_lstm返回八个结果：y、output_h、output_c、i、j、f、o、tanhct。x/weight/h/c列FP16/FP32及NZ，bias为1D FP16/FP32/ND，seqMask仅FP16/NZ或INT32/ND。旧页限制单层，不支持dropout、双向、batch_first及packed输入等通用nn.LSTM能力；这些限制不能被原型中的开关名字抵消。训练辅助量可采用NZ，非训练路径ND，不把所有返回视作普通ND输出。

文档对物理4D格式的描述和中文样例3D逻辑输入/2D权重分开理解；不据物理存储描述额外改变业务Tensor逻辑rank。主线中文方向BIDIRECTIONAL与英文REDIRECTIONAL拼写冲突，且正文要求bidirectional=False，不能据字符串推断支持双向。迁移须重建权重/门顺序、状态shape、输出数量及反向协议，不能只替换函数名。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_gru.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_lstm.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_lstm.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_lstm.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/GruKernelNpu.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/GruKernelNpu.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LstmKernelNpu.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LstmKernelNpu.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）


- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GRUKernelNpuOpApi.cpp)（primary）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GRUBackwardKernelNpuOpApi.cpp)（primary）
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LSTMKernelNpuOpApi.cpp)（primary）
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LSTMBackwardKernelNpuOpApi.cpp)（primary）
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LSTMBackwardKernelNpuOpApi.cpp)（primary）
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/LstmCellKernelNpuOpApi.cpp)（primary）
- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/LstmCellKernelNpuOpApi.cpp)（primary）
- [固定来源 20](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LstmKernelNpu.cpp)（primary）
- [固定来源 21](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LstmKernelNpu.cpp)（primary）
- [固定来源 22](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/LstmCellKernelNpu.cpp)（primary）
- [固定来源 23](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/LstmCellKernelNpu.cpp)（primary）
- [固定来源 24](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/_thnnFusedGruCellNpuOpApi.cpp)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/_thnnFusedGruCellBackwardNpuOpApi.cpp)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/_thnnFusedFruCellNpuOpApi.cpp)（implementation）
- [固定来源 27](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）

## 反向接线与acl_op旧反向（主线与发布两版本同文）

derivatives.yaml接线（主线172–204、发布167–194行段）：六条前向schema的反向公式。npu_gru六输出仅前两路可微（output_differentiability首两true余false），npu_lstm、npu_lstm_cell、npu_lstm_data仅前三路可微，但反向公式把全部保存输出整包传入——npu_gru_backward消费result0–result5（y、output_h、output_updata（源内拼写）、output_reset、output_new、hidden_new），npu_lstm(_cell/_data)_backward消费result0–result7（含i、j、f、o、tanhc），_lstm_npu反向消费result3–result9（i、j、f、o、h、c、tanhc），主线独有_gru_npu反向消费result2–result6（r、z、n、hn、h）。发布无_gru_npu条目（rg负向核实）。门控中间量既是格式合同也是反向保存量，不能因不可微而丢弃。

npu_gru_backward（GruKernelNpu.cpp 263–329，主线与发布两版本文件字节一致、sha256相同）：grady/gradh未定义时分别按output_y/init_h尺寸补FRACTAL_NZ零张量；gradh已定义时取gradh[input.size(0)-1]（DynamicGRU系列以第0维为时间轴，即最后一步）。六路梯度（grad_w_input、grad_w_hidden、grad_x、grad_b_input、grad_b_hidden、grad_h_prev）中权重/偏置梯度都以input.options()分配、ACL_FORMAT_ND。走旧ACE算子DynamicGRUV2Grad，属性固定UNIDIRECTIONAL、cell_depth=1、keep_prob=1.0、cell_clip=-1.0、num_proj=0、time_major=true、bias_type=no_bias、gate_order=rzh、reset_after=true；签名里的seq_length形参不进命令，命令用的是本地标量零seq_lengths/mask，变长序列梯度不按seq_length截断；bias_type=no_bias与两路偏置梯度输出并存的关系属设备算子语义，host层未解释。

npu_lstm_backward与npu_lstm_data_backward（LstmKernelNpu.cpp主线821–882/949–1013，发布619–650/670–702，同构）：先squeeze hx/cx第0维；grad_h/grad_c未定义补零、已定义取最后时间步；公共helper lstm_backward_out_npu_nocheck（主线437–513、发布340–399）走DynamicRNNGrad：gate_order恒ifjo、direction按flag_direction取UNIDIRECTIONAL/REDIRECTIONAL、cell_depth=0、forget_bias=0.0、wci/wcf/wco恒为零标量（无peephole）；data变体把batch_sizes传入helper，seq_length改用get_mask推导。返回(grad_input, grad_weight, grad_bias, grad_ht, grad_ct)，grad_ht/grad_ct按2D计算后unsqueeze回第0维。

npu_lstm_cell_backward（LstmCellKernelNpu.cpp主线166–221、发布146–172，同构）：三路grad未定义补零；grad_bias按{4*hidden_size}、以i为模板分配；走DynamicRNNV2Grad（cell_depth=1、activation=tanh、recurrent_activation=sigmoid、gate_order=ifjo、stateful=false、merge_mode=concat）。返回的7元组把同一个grad_bias同时填进b_ih与b_hh两个梯度槽位：derivatives为两路偏置各拿到一份相同的合并门偏置梯度，不拆分为两份独立估计。

## 主线opapi反向（aclnnGRUBackward/aclnnLstmBackward）

_gru_npu_backward（GRUBackwardKernelNpuOpApi.cpp 40–155，主线独有；yaml登记op_api all_version、device_check NoCheck）：前向把r/z/n/hn/h逐层stack成单张量并npu_format_cast回ACL_FORMAT_ND（前向161–176注释：at::stack按NPU默认NCHW格式分配，aclnnGRUBackward要求ND），反向先chunk回D*num_layers列表、首维为1的层squeeze掉第0维；hx不切分，aclnnGRUBackward按层/方向内部自切。batch_sizes做两种归一化：空[0]张量还原为nullopt（autograd会把None物化成空张量）、CPU张量搬NPU并contiguous。grad_y/grad_h未定义时补零张量而非传undefined（源注释：aclnn侧CheckNotNull拒undefined、ACLNN_ERR_PARAM_NULLPTR）；补零dy的形状按前向output_y推导（末维D*hidden_size），源注释明确zeros_like(input)在input_size≠D*hidden_size时形状错误。输出(grad_input, grad_h_prev, param梯度列表)。主线yaml另给_gru_npu标tags: nondeterministic_seeded（dropout按非确定性种子标记），反向结果不承诺逐位可复现。

_lstm_npu_backward（LSTMBackwardKernelNpuOpApi.cpp主线33–133全文已读；发布同名文件139行经全文件raw diff核实与主线仅排版差异、逻辑同构）：七组保存量i/j/f/o/h/c/tanhc同样chunk+squeeze回列表；三路grad直传（schema为非可选Tensor，无补零分支，与GRU侧不同）；EXEC_NPU_CMD(aclnnLstmBackward, ...)实参表含一个显式nullptr占位；输出(grad_input, [grad_h_prev, grad_c_prev], param梯度列表)。

## 前向入口与aten模板差异

主线aten::gru覆盖（GRUKernelNpuOpApi.cpp 181–207）：input/hx/params任一bf16或混合浮点dtype即回退acl_op::gru，其余先过DO_COMPATIBILITY(aclnnGRU)再进_gru_npu。DO_COMPATIBILITY（op_api_common.h 94–119）只处理aclnn符号缺席：缺符号时aclnn-only模式直接TORCH_CHECK抛NOT_SUPPORT，非aclnn-only才回退宏内origin调用，不是通用SDK错误重试。packed（data+batch_sizes）路径是独立流程：不做fallback判定、不过DO_COMPATIBILITY，直接调_gru_npu（源注释：acl_op的DynamicGRUV2不支持batch_sizes），packed场景的bf16/混合dtype没有可用旧路径。主线aten::lstm覆盖（LSTMKernelNpuOpApi.cpp 199–269）与发布（同文件发布侧行段，raw diff核实）的差异有三处。其一，主线ShouldFallbackToAclOp多params.size()!=4的TORCH_WARN_ONCE回退门（源码以kSingleLayerBiasParamCount=4与警告文案自述aclnn要求，属host侧判定，设备侧真实约束未核对；发布同名谓词只查bf16/混合dtype）。其二，主线普通输入入口多一道SoC分派：非950时先经该谓词（命中回退acl_op）再DO_COMPATIBILITY(aclnnLSTM)，判定为假且宏通过即进_lstm_npu/aclnnLSTM，aclnnLSTM并非950专属；Ascend950普通入口跳过整个非950块（含params.size()!=4/bf16/混合判定与该入口的DO_COMPATIBILITY）直接调_lstm_npu。其三，packed变体主线与发布两版本都先做谓词+DO_COMPATIBILITY、与SoC无关，自成流程；主线另加op_plugin::utils::check_packed_lstm_args（OpUtils.cpp 420–455：dtype与weight不一致且各autocast全关时报错并按版本给转换建议文案、data必须2D、data.size(1)==weight.size(1)、hx[0]为(layers,batch,w_hh.size(1))、hx[1]为(layers,batch,weight.size(0)/4)），把batch_sizes搬到data设备，并把输出y reshape成(-1,末维)的PackedSequence扁平布局；发布packed变体没有新增的check_packed_lstm_args检查，batch_sizes直接透传且输出不reshape。

thnn融合cell对：主线与发布两版本均注册_thnn_fused_lstm_cell与_thnn_fused_lstm_cell_backward_impl（op_api all_version）。_thnn_fused_lstm_cell做三重dtype一致检查（发布仅fp16/fp32；主线另放行bf16，注释自述否决权在aclnn的SoC dtype支持表），返回(hout,cout,storage)；backward_impl要求cx/cy/workspace全2D且cx/cy同尺寸（PARAM错误），grad_cy缺省物化为空Tensor，grad_bias按{workspace.size(1)}无格式分配，走aclnnThnnFusedLstmCellBackward。aten lstm_cell覆盖：主线DO_COMPATIBILITY后按IsAclnnOnly分流（非aclnn-only走acl_op::lstm_cell），发布侧无条件matmul加_thnn_fused_lstm_cell。GRU cell主线与发布两版本分叉最大：主线注册_thnn_fused_gru_cell与_thnn_fused_gru_cell_backward（op_api [v2.5,newest]），aclnn可用时走aclnnThnnFusedGruCell并产出(B,5H)的workspace（平面r|z|n|hx|gh_n），不可用时按aten同式组合分解、仅grad模式且任一输入requires_grad才构建workspace；backward检查镜像aten checkGRUBackwardSizes（workspace必须2D (B,5H)），has_bias=false时偏置梯度保持undefined（对齐aten CUDA行为），aclnn不可用时按workspace平面组合分解、half/bf16先升fp32做偏置归约再转回。发布侧仅有纯aten组合实现（_thnnFusedFruCellNpuOpApi.cpp，25行，文件名Fru为拼写残留）：返回空workspace保接口兼容，并另在autograd段注册同schema；发布无_thnn_fused_gru_cell_backward注册（rg负向核实），其GRU cell反向依赖组合算子自动微分而非融合反向核。

与aten模板的对照均按源码注释自述（RNN.cpp、RNN.cu行号），本卡未打开aten源逐行核对；本节全部为静态阅读，未执行任何前向/反向，发布与主线的反向数值一致性未验证。

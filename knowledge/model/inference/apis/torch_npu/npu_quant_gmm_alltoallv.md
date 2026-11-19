---
type: API
title: npu_quant_gmm_alltoallv：量化专家计算、反重排与回传
description: 区分发送端专家输入与接收端输出，记录量化 scale、保留通信参数和引擎证据差异。
tags:
- task.lookup
- topic.precision
- topic.parallelism
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_gmm_alltoallv.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantGmmAllToAllvKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_grouped_mat_mul_allto_allv.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_gmm_alltoallv.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_gmm_alltoallv.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantGmmAllToAllvKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_gmm_alltoallv.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_grouped_mat_mul_allto_allv.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
created_at: '2026-11-09T08:36:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# npu_quant_gmm_alltoallv：量化专家计算、反重排与回传

## 版本与产品

依据OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整产品页、Schema、Meta、C++包装和TorchAir `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` Converter。产品页仅声明950DT；不从非量化GMM接口继承A3，也不扩展到950PR。主线中文支持单算子以及T-T/MX图模式（英文仅列T-T；发布转换器另有解包缺陷），文档允许训练和推理场景，但FP4成对输入仅推理；场景支持不等于已证明该融合接口自动提供完整训练反向。主线组合配套未知，不能替换已登记发布基线。

## 量化模式与逻辑类型

路由gmm_x/gmm_weight与共享mm_x/mm_weight的模式组合仅[1,1]或[6,6]，启用共享分支时两分支模式一致。参数默认None不代表可省略：两个C++入口均要求显式给出gmm_x_quant_mode、gmm_weight_quant_mode；共享分支存在时还要求其两个模式及mm_y_dtype。

| 模式 | 路由及共享输入 | scale | 输出 |
| --- | --- | --- | --- |
| T-T，[1,1] | hifloat8成对输入 | FP32，均为[1] | FP16或BF16 |
| MX，[6,6] | E4M3FN/E5M2的四种左右组合，或成对FP4 E2M1 | E8M0的分组scale | FP16或BF16；FP4成对输入仅推理 |

不能从参数段列出多种dtype便组合出T-T FP8或混合FP4/FP8。共享左/右输入分别与路由左/右类型一致，输出mm_y与路由输出保持同dtype。quant_gmm_alltoallv参数段称左右同dtype，但其完整MX表与Converter允许FP8左右E4M3FN/E5M2组合；按模式表核对，不把这条宽泛描述扩成任意混精度。

hifloat8使用字节存储并显式传*_dtype=torch_npu.hifloat8；C++接受uint8/int8存储，图路径应使用其明确的UINT8包装约定。FP4按两个逻辑数打包到UINT8，并传*_dtype=torch_npu.float4_e2m1fn_x2；原生FP8可用自身dtype，显式dtype时需匹配。MX scale的逻辑类型用*_scale_dtype=torch_npu.float8_e8m0fnu标明；字节载体和逻辑E8M0不是同一概念，不能把INT8/UINT8数据数值直接当已经正确编码的scale。不要照抄示例中给FP8 Tensor同时标FP4提示的组合，先核对载体、逻辑类型与布局。

## 共享分支、档位与通信规模

共享分支需同时提供mm_x、mm_weight、mm_x_scale、mm_weight_scale，以及该模式所需dtype提示、两个quant_mode与mm_y_dtype。全部关闭时这些Tensor、模式和dtype提示保持None；C++会拒绝只给一个共享矩阵，GE在任意共享Tensor缺失时要求其余共享属性也为空。签名列为可选不代表任意子集有效。无共享输入时Meta返回None，C++相应输出是未定义Tensor占位，不能假定是可读shape的零元素结果。

send_counts、recv_counts为Host整数list，长度e*ep_world_size，条目非负；按rank与专家顺序展开，不是二维Tensor。send_counts_tensor/recv_counts_tensor当前只支持None，即使实现继续透传也不能据此宣称设备动态计数已受支持。e为1..32，e*EP≤256；EP仅2/4/8/16/32/64/128/256；hcom为长度1..127的通信组名。BSK∈(0,52428800)，H1/N1/N2∈(0,65536)，H2∈(0,12288]；共享路径topK为2..8。256限制专家×rank条目数，不是总token数。

MX使用group_size=[M,N,K]，各项0..65535；0表示按输入和scale形状推导，需满足对应整除关系。文档列出的三维左scale/共享右scale与四维路由右scale组合推导为[1,1,32]。T-T保持None或[0,0,0]，不能把模式代码4/5出现在说明列表当作pergroup/perblock功能可用。

当某rank的全部返回Tensor均为空时，产品页要求显式torch.distributed.barrier()等待其他rank完成通信计算；不能让该rank直接退出，也不因此取消其余输入范围约束。全域总发送量等于总接收量之外，还需逐rank、逐专家匹配通信对；均匀示例的send_counts.copy()不是不均匀路由的通用生成方法。

CCU仅单机UB域，文档的AI CPU路径可跨机UB域。CCU单次通信量≤256M，总量≤16*256MB，具体shape可能更严。C++在comm_mode=None时走旧aclnn入口，显式值改走V2并检查符号，缺失时报错；即使显式ai_cpu与None意图相同，也不能假定依赖相同或自动回退。

## 函数原型

```python
torch_npu.npu_quant_gmm_alltoallv(gmm_x, gmm_weight, gmm_x_scale, gmm_weight_scale, hcom, ep_world_size, send_counts, recv_counts, gmm_y_dtype, *, send_counts_tensor=None, recv_counts_tensor=None, mm_x=None, mm_weight=None, mm_x_scale=None, mm_weight_scale=None, comm_quant_scale=None, gmm_x_quant_mode=None, gmm_weight_quant_mode=None, mm_x_quant_mode=None, mm_weight_quant_mode=None, comm_quant_mode=None, group_size=None, gmm_x_dtype=None, gmm_weight_dtype=None, gmm_x_scale_dtype=None, gmm_weight_scale_dtype=None, mm_x_dtype=None, mm_weight_dtype=None, mm_x_scale_dtype=None, mm_weight_scale_dtype=None, comm_quant_dtype=None, mm_y_dtype=None, comm_mode=None) -> (Tensor, Tensor)
```

## 接口与先计算后通信

关键位置参数依次为gmm_x、gmm_weight、gmm_x_scale、gmm_weight_scale、hcom、ep_world_size、send_counts、recv_counts、gmm_y_dtype；其后为关键字参数。返回(y,mm_y)，不返回GMM/Unpermute中间结果。权重转置通过实际Tensor视图/布局表达，没有公开trans_gmm_weight/trans_mm_weight关键字。

令A=sum(send_counts)，BSK=sum(recv_counts)。输入gmm_x逻辑[A,H1]，gmm_weight逻辑[e,H1,N1]；按专家GMM后Unpermute、AlltoAllv，第一项y=[BSK,N1]。共享mm_x=[BS,H2]和mm_weight=[H2,N2]得到mm_y=[BS,N2]。最终topK加权合并不在此接口中，不能把返回shape等同于模型MoE combine已完成。

MX左scale[A,ceil(H1/64),2]、路由右scale[e,ceil(H1/64),N1,2]；共享左scale[BS,ceil(H2/64),2]、右scale[ceil(H2/64),N2,2]。共享scale参数段写FP32，但完整MX表与实现还列逻辑E8M0；按所选模式核对，不能强行将MX scale转为普通浮点值。

FP4内轴两逻辑数打包到一字节：左输入H1/H2为偶数，权重不转置时N1/N2为偶数、转置时H1/H2为偶数。Meta和C++恢复非转置权重的浮点输出列数；这里不继承前向通信接口独有的H不能为2文字，也不推导未列出的训练支持。

comm_quant_scale、comm_quant_dtype当前暂不支持，保持None；comm_quant_mode只支持0（C++的None也归0）。包装中INT64检查、GE覆盖comm_quant_dtype为0并不构成可启用低比特通信的公开契约，不能用它们调出通信量化。

本页参数段列None/ai_cpu/ccu，约束段却只明确950DT支持CCU；C++与GE有AI CPU/CCU分支，不能据此消除产品文字歧义。CCU是这几处一致明确的选择，AI CPU须先核对具体配套和产品契约，不能将参数枚举写成已获验证的全场景支持。

- [量化路由通信后计算](npu_alltoallv_quant_gmm.md)
- [非量化的专家计算后回传](npu_gmm_alltoallv.md)

## 核验

分别核对原始量化编码、逻辑/物理shape、专家分段、计数匹配、输出dtype与可选项；以分步通信、重排、反量化矩阵乘及共享MM参考比对每个有效返回。图模式还应检查scale布局转换和重编译行为。融合API的存在不证明当前负载获得通信计算重叠或加速。

本次只静态阅读固定来源，未执行上游、NPU、多卡、反向、数值或性能测试。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 发布图能力与主线双语范围

主线中文声明T-T和MX图模式，英文仍只列T-T；主线转换器确有MX分支，但存在实现不能替代具体产品与软件栈的配套验证。TorchAir发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013的转换器只接受T-T，OpPlugin发布的Meta也无条件要求所有已给scale为[1]。发布C++有MX FP8分支，不等于该固定发布组合支持MX图；主线新增FP4处理也不能回推发布。

四个发布Schema/Meta/C++/GE签名均无comm_mode。主线显式模式要求V2及对应GetWorkspaceSize双符号，未指定仍走旧入口；没有可据此推断的最低精确CANN版本。主线GE允许None/ai_cpu/ccu也不取消产品页更窄的明确约束。

## 分支完整性、分组和存储核对

两版C++都要求两个GMM量化模式显式给出，不能把Schema默认None或旧测试“默认T-T”的注释当成Eager契约。主线共享矩阵省略时还要求对应MM量化模式、数据类型与scale类型提示为空；发布对这些提示的检查较弱，不据此放宽共同输入。

主线GE要求四个共享Tensor全部提供或全部None，相应数据和scale底层dtype分别与GMM侧一致，并检查所有已给量化模式相同。主线C++的局部dtype/维数检查、GE条件和Meta输出推导均没有完整覆盖count、K、scale容量、转置和跨rank一致性；缺少检查不等于额外输入合法。

C++分组helper对None或空列表编码0，GE却要求非None列表恰有三项；跨模式使用None或公开合法的三项，不传整数0。主线GE会编码每项0..65535，发布GE却固定group_size=0而忽略该形参，不能声称非默认分组在两版图行为相同。

主线MX图会对路由weight_scale依据布局换轴，FP4输入再经过Bitcast和逻辑形状扩展；位解释不执行数值量化。实际转置视图和尺度布局需一同核对。文档中UINT8再.to(FP8)却标FP4的示例不能作为有效打包步骤；尺度值全1、均匀count或有图代码都不构成非零FP4精度证明。

## 回传转换器的固定缺陷

TorchAir发布转换器的x_list只有8项，后续却解包给9个变量（额外接comm_quant_scale）；按该固定文件的直接控制流，到此不能继续生成GE节点。因此只能说有接口实现及T-T接受条件，不能写成发布T-T图已验证可用，也不能以主线修正推断用户旧包含修复。

主线转换器强制两个GMM模式非None，MM模式可从GMM补齐；C++共享矩阵存在时要求MM模式显式，而无共享时主线拒绝对应模式和类型提示，发布回传C++也至少拒绝无共享却仍给MM模式。文档中无共享的图示例仍填MM模式1，仅可作图入口示意，不是可直接复用于Eager的完整有效调用。

主线C++的共享scale仍只在存在时检查；公开契约及GE要求完整四Tensor组合，不能借局部检查绕过。comm_quant_scale/comm_quant_dtype继续保留None、comm_quant_mode为0；GE把comm_quant_dtype覆盖为0不代表提供了可启用的低比特通信。

两版测试仅空白/EOF不同。多进程入口把10项输入解包到6项，调用又使用未定义mm_x/mm_weight；黄金引用未定义bsk、只返回首行且没有比较路由主输出。后半“异常测试”基例缺必填GMM模式且使用FP16，常在目标条件之前被拒；assertNotIn旧错误文本不等于调用成功或命中目标检查。不能把这些测试作为数值、默认值、MX/FP4、单卡异常拦截或950部署证明，未执行上游代码。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_quant_gmm_alltoallv.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantGmmAllToAllvKernelNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_grouped_mat_mul_allto_allv.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_quant_gmm_alltoallv.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_quant_gmm_alltoallv.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantGmmAllToAllvKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_quant_gmm_alltoallv.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/quant_grouped_mat_mul_allto_allv.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）

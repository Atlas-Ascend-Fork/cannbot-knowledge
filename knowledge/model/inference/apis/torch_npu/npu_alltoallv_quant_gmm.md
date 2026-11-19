---
type: API
title: npu_alltoallv_quant_gmm：量化路由通信、重排与专家计算
description: 说明 950DT 的 T-T/MX 模式、接收计数、共享专家、FP4 返回与空输出 rank 同步。
tags:
- task.lookup
- topic.precision
- topic.parallelism
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_alltoallv_quant_gmm.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllToAllvQuantGmmNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_allv_quant_grouped_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_alltoallv_quant_gmm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_alltoallv_quant_gmm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllToAllvQuantGmmNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_alltoallv_quant_gmm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_allv_quant_grouped_matmul.py
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

# npu_alltoallv_quant_gmm：量化路由通信、重排与专家计算

## 版本与产品

依据OpPlugin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整产品页、Schema、Meta、C++包装和TorchAir `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` Converter。产品页仅声明950DT；不从非量化GMM接口继承A3，也不扩展到950PR。主线中文支持单算子以及T-T/MX图模式（英文仅列T-T，发布图只T-T），文档允许训练和推理场景，但FP4成对输入仅推理；场景支持不等于已证明该融合接口自动提供完整训练反向。主线组合配套未知，不能替换已登记发布基线。

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
torch_npu.npu_alltoallv_quant_gmm(gmm_x, gmm_weight, gmm_x_scale, gmm_weight_scale, hcom, ep_world_size, send_counts, recv_counts, gmm_y_dtype, *, send_counts_tensor=None, recv_counts_tensor=None, mm_x=None, mm_weight=None, mm_x_scale=None, mm_weight_scale=None, gmm_x_quant_mode=None, gmm_weight_quant_mode=None, mm_x_quant_mode=None, mm_weight_quant_mode=None, permute_out_flag=False, group_size=None, gmm_x_dtype=None, gmm_weight_dtype=None, gmm_x_scale_dtype=None, gmm_weight_scale_dtype=None, mm_x_dtype=None, mm_weight_dtype=None, mm_x_scale_dtype=None, mm_weight_scale_dtype=None, mm_y_dtype=None, comm_mode=None) -> (Tensor, Tensor, Tensor)
```

## 接口与先通信后计算

关键位置参数依次为gmm_x、gmm_weight、gmm_x_scale、gmm_weight_scale、hcom、ep_world_size、send_counts、recv_counts、gmm_y_dtype；其后为关键字参数。额外返回开关permute_out_flag=False；本接口没有trans_gmm_weight/trans_mm_weight关键字，权重转置通过实际Tensor视图/布局表达。

令BSK=sum(send_counts)，A=sum(recv_counts)。输入gmm_x逻辑[BSK,H1]，gmm_weight逻辑[e,H1,N1]；先AlltoAllv、Permute，再本卡GMM，第一项gmm_y=[A,N1]。共享mm_x=[BS,H2]、mm_weight=[H2,N2]独立得到mm_y=[BS,N2]。第三项只在permute_out_flag=True时有效，是GMM之前的路由重排值，逻辑[A,H1]，不是已反量化的最终输出；False不跳过必需的内部重排。

MX左scale逻辑[BSK,ceil(H1/64),2]，路由右scale[e,ceil(H1/64),N1,2]；共享左scale[BS,ceil(H2/64),2]、右scale[ceil(H2/64),N2,2]。Tensor的数据轴与scale轴不要一起按压缩字节数缩半。

FP4输入H1及共享H2需偶数且不能等于2；权重不转置时内轴N1/N2为偶数，转置时内轴H1/H2为偶数且不能为2。物理输入/重排返回的内轴按两逻辑数/字节存储；Meta使用gmm_x物理列数分配第三项，GE把逻辑FP4重排值打包回UINT8。C++与Meta对非转置FP4权重的输出列恢复乘2，不能再把浮点输出N1/N2缩半。

输出固定三项；Meta未启用项为None，C++为未定义占位。comm_mode参数及本页约束均明确None/ai_cpu/ccu，None意图为AI CPU；图Converter也限制这两种显式字符串。

- [非量化的先通信后计算](npu_alltoallv_gmm.md)
- [量化专家计算后回传](npu_quant_gmm_alltoallv.md)

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

## 先通信接口的额外版本边界

主线C++在共享矩阵存在时还明确要求两张共享scale都提供；发布仅在scale存在时局部检查，未检查不表示可省。共享分支关闭时主线拒绝MM模式和类型提示，发布先通信包装较宽松。文档TT图示例在共享输入None时仍给MM模式1，不能当作同样参数可走主线Eager的依据。

主线GE在输入检查后把省略模式补1，但检查前至少需要一个非None模式且所有已给模式一致；这与Eager要求两个GMM模式显式不同。MX FP4的第三项在GE中回打包为UINT8，Meta按原始输入物理列数和dtype分配；未启用第三项仍是None/未定义占位。发布没有FP4扩形与回打包，不由同名permute_out推断表示兼容。

两版测试除44行空白/EOF差异一致：引用本文件未定义的TestAlltoAllvGmm，构造参数含未定义scale，又传违背int[]?签名的group_size=0；黄金计算也没有正确反量化参考。不能认定其HiF8、MX、FP4、可选返回、图或性能验证通过。文档均匀示例把recv_counts复制自send_counts，只适用于该构造，不能生成一般不均匀通信对。全部返回项为空rank的显式barrier条件仍按文档保留，没有执行多进程验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_alltoallv_quant_gmm.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllToAllvQuantGmmNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_allv_quant_grouped_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_alltoallv_quant_gmm.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_alltoallv_quant_gmm.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllToAllvQuantGmmNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_alltoallv_quant_gmm.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_allv_quant_grouped_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）

---
type: API
title: CrossCoreSetFlag
description: 核间同步场景中向调度模块上报本核前置pipe流水任务已完成，与CrossCoreWaitFlag配对使用，通过flagId控制核间同步。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/sync_control/inter_core_sync/CrossCoreSetFlag_ISASI.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/basic_api/kernel_operator_block_sync_intf.h
---

# CrossCoreSetFlag\(ISASI\)<a id="ZH-CN_TOPIC_0000001834069637"></a>

## 功能说明<a id="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_block_sync_intf.h"`。

在核间同步场景中，CrossCoreSetFlag接口和[CrossCoreWaitFlag](cross_core_wait_flag_isasi.md)接口配对工作，使用时需传入核间同步的标记ID（flagId），每个ID对应一个用于控制同步的计数器。

- CrossCoreSetFlag：AI Core中的AIC/AIV在完成本核前置位的pipe流水任务后，调用该接口，向调度模块上报本核任务已完成。调度模块收集所有参与核的上报信息，作为全局完成标志。
- CrossCoreWaitFlag：用于阻塞本核后续指令的下发（已下发指令可正常执行），直至调度模块确认所有应调用CrossCoreSetFlag的核均已上报完成，随即解除阻塞，允许该核继续下发指令。

如[图1](#fig37581010773)所示（图中block代表AIC，sub_block代表AIV），同步控制分为以下几种模式：

- 模式0：AI Core核间的同步控制。对于AIC场景，同步所有的AIC核，直到所有的AIC核都执行到CrossCoreSetFlag时，CrossCoreWaitFlag后续的指令才会执行；对于AIV场景，同步所有的AIV核，直到所有的AIV核都执行到CrossCoreSetFlag时，CrossCoreWaitFlag后续的指令才会执行。
- 模式1：AI Core内部，AIV核之间的同步控制。如果两个AIV核都运行了CrossCoreSetFlag，CrossCoreWaitFlag后续的指令才会执行。
- 模式2：AI Core内部，AIC与所有AIV之间的同步控制。在AIC核执行CrossCoreSetFlag之后，两个AIV上CrossCoreWaitFlag后续的指令才会继续执行；两个AIV都执行CrossCoreSetFlag后，AIC上CrossCoreWaitFlag后续的指令才能执行。
- 模式4：AI Core内部，AIC与单个AIV之间的同步控制。当在AIC核执行CrossCoreSetFlag之后，AIV0或者AIV1上CrossCoreWaitFlag后续的指令才会继续执行；AIV0或者AIV1执行CrossCoreSetFlag后，AIC上CrossCoreWaitFlag后续的指令才能执行。

> [!NOTE]说明
> - 不同型号支持的模式不同，具体支持情况请参考[modeId支持的取值说明](#modeId支持的取值说明)。
> - 每个模式的具体执行逻辑与细节可以参考[关键特性说明](key_features.md#ZH-CN_TOPIC_0000002586300741)。

**图1**  同步控制模式示意图<a id="fig37581010773"></a>  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/block_subblock_relationship_3510.png "同步控制模式示意图")

## 函数原型<a id="section620mcpsimp"></a>

```cpp
template <uint8_t modeId, pipe_t pipe>
__aicore__ inline void CrossCoreSetFlag(uint16_t flagId)
```

## 参数说明<a id="section622mcpsimp"></a>

### 模板参数及输入参数说明

CrossCoreSetFlag的模板参数`modeId`和`pipe`均**没有默认值**，其取值用于配置硬件指令，调用接口时必须**显式传入**。与本接口不同，CrossCoreWaitFlag的两个模板参数均具有默认值，且在不同产品和同步模式下的生效情况不同，因此**两个接口对模板参数的传入要求并不相同**。具体请参见[CrossCoreWaitFlag模板参数说明](cross_core_wait_flag_isasi.md#template-parameter-defaults)。

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| modeId | 核间同步的模式，不同产品对同步模式的支持情况请参见[modeId支持的取值说明](#modeId支持的取值说明)。<br>各个模式支持的对应核函数（Kernel）类型请参照[表3](#table3)。 |
| pipe | 标识在哪条流水的前序指令完成后，CrossCoreSetFlag才向调度模块发送通知。支持的流水类型为PIPE_V、PIPE_M、PIPE_MTE1、PIPE_MTE2、PIPE_MTE3、PIPE_FIX，不支持PIPE_S和PIPE_ALL。不同产品对流水类型的支持情况请参见[pipe支持的流水类型说明](#pipe支持的流水类型说明)。 |

**表2**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| flagId | 输入 | 核间同步的标记。不同产品对flagId的取值范围说明请参见[flagId取值范围说明](#flagId取值范围说明)。 |

### modeId支持的取值说明<a id="modeId支持的取值说明"></a>

不同产品对同步模式的支持情况如下：

- 针对Ascend 950PR/Ascend 950DT，支持的同步模式为：模式0、模式1、模式2、模式4。


- 针对如下产品，支持的同步模式为：模式0、模式1、模式2。
    
    - Atlas A3 训练系列产品/Atlas A3 推理系列产品
    
    
    - Atlas A2 训练系列产品/Atlas A2 推理系列产品
    


### pipe支持的流水类型说明<a id="pipe支持的流水类型说明"></a>

- 核间同步的模式为模式0、1、2时，
    - 支持的流水类型为PIPE_V、PIPE_M、PIPE_MTE1、PIPE_MTE2、PIPE_MTE3、PIPE_FIX。
    - 不支持的流水类型为PIPE_ALL、PIPE_S。

- 针对Ascend 950PR/Ascend 950DT，核间同步的模式为模式4时，
    - 支持的流水类型为PIPE_V、PIPE_M、PIPE_MTE1、PIPE_MTE2、PIPE_MTE3、PIPE_FIX、PIPE_S。
    - 不支持的流水类型为PIPE_ALL。


### flagId取值范围说明<a id="flagId取值范围说明"></a>

- 核间同步的模式为模式0、1、2时，支持的取值范围为0-15。

- 针对Ascend 950PR/Ascend 950DT，核间同步的模式为模式4时，支持的取值范围情况如下：
    - AIV0发起的flagId 0-15的CrossCoreSetFlag操作对应AIC CrossCoreWaitFlag中flagId 0-15的操作。
    - AIV1发起的flagId 0-15的CrossCoreSetFlag操作对应AIC CrossCoreWaitFlag中flagId 16-31的操作。
    - AIC发起的flagId 0-15的CrossCoreSetFlag操作对应AIV0 CrossCoreWaitFlag中flagId 0-15的操作。
    - AIC发起的flagId 16-31的CrossCoreSetFlag操作对应AIV1 CrossCoreWaitFlag中flagId 0-15的操作。


此外，当本接口与Matmul高阶API或SyncAll接口同时使用时，开发者自行使用的flagId还需注意避免与这些接口内部已占用的flagId冲突，详见[约束说明](#flagId冲突说明)中的flagId占用情况。

## 返回值说明<a id="section640mcpsimp"></a>

无

## 约束说明<a id="section633mcpsimp"></a>

- 由于当核函数（Kernel）类型为KERNEL_TYPE_AIC_ONLY或KERNEL_TYPE_AIV_ONLY时，硬件不会开启调度模块，也就无法正常进行核间同步，因此不同的同步模式配置[核函数（Kernel）类型](../../kernel_tiling/set_kernel_type.md)或[函数修饰符](../../../../../guides/programming_guide/language_extension/simd_builtin_keywords.md#section1074418132518)的情况如下：
    - 在纯Vector/Cube场景下（模式0或模式1），建议设置核函数（Kernel）类型为KERNEL\_TYPE\_MIX\_AIV\_1\_0或KERNEL\_TYPE\_MIX\_AIC\_1\_0，其它支持的核函数（Kernel）类型请参考表3。
    - 对于Vector和Cube混合场景（模式2和模式4），需根据AI Core中AIC和AIV的比例灵活配置核函数（Kernel）类型，不同模式支持的函数修饰符和核函数（Kernel）类型请参照表3。

        **表3**  模式与支持的核函数（Kernel）类型配置<a id="table3"></a>

        | 模式 | 支持的函数修饰符 | 支持的核函数（Kernel）类型配置 |
        | --- | --- | --- |
        | 0 | \_\_mix\_\_(0, 1)、\_\_mix\_\_(1, 0)、\_\_mix\_\_(1, 1)、\_\_mix\_\_(1, 2) | KERNEL\_TYPE\_MIX\_AIV\_1\_0、KERNEL\_TYPE\_MIX\_AIC\_1\_0、KERNEL\_TYPE\_MIX\_AIC\_1\_1、KERNEL\_TYPE\_MIX\_AIC\_1\_2 |
        | 1 | \_\_mix\_\_(1, 1)、\_\_mix\_\_(1, 2) | KERNEL\_TYPE\_MIX\_AIC\_1\_1、KERNEL\_TYPE\_MIX\_AIC\_1\_2 |
        | 2 | \_\_mix\_\_(1, 1)、\_\_mix\_\_(1, 2) | KERNEL\_TYPE\_MIX\_AIC\_1\_1、KERNEL\_TYPE\_MIX\_AIC\_1\_2 |
        | 4 | \_\_mix\_\_(1, 2) | KERNEL\_TYPE\_MIX\_AIC\_1\_2 |

<a id="flagId冲突说明"></a>

- 以下接口内部实现中使用了CrossCoreSetFlag和CrossCoreWaitFlag会占用一部分flagId，开发者同时使用CrossCoreSetFlag/CrossCoreWaitFlag与以下接口时，需注意避免flagId使用冲突：

    - Matmul高阶API占用的flagId范围与定义的Matmul对象数目相关，假设定义了N个Matmul对象，Matmul高阶API内部占用的flagId范围为\[0, 2 \* N - 1\]。Matmul最多支持定义4个对象，此时flagId占用范围为\[0,7\]。
    - SyncAll硬件同步接口占用的flagId情况请参考[flagId占用情况](sync_all.md#syncall_flagId冲突说明)。

- 用户需要确保配套使用CrossCoreSetFlag和CrossCoreWaitFlag，否则会出现未定义行为。
- 核间同步的模式为模式0、1、2时，模板参数pipe不支持设置为PIPE\_ALL，PIPE\_S。

- 针对Ascend 950PR/Ascend 950DT，核间同步的模式为模式4时，模板参数pipe不支持配置为PIPE\_ALL。

- 一个核连续发出的CrossCoreSetFlag，硬件不保证执行顺序。例如AIV依次发射CrossCoreSetFlag<0, PIPE\_V\>\(0\)，CrossCoreSetFlag<0, PIPE\_V\>\(1\)，实际的执行顺序可能是flagId=1的先执行。
- flagId相关的约束：
    - 对于模式0、1、2，每个AIC和每个AIV都各自有16个flagId，支持的取值范围为0-15。如果flagId的值超出该范围，则截取低4bit（例如，flagId=17时，截取后为1）。
    
    - 针对Ascend 950PR/Ascend 950DT，核间同步的模式为模式4时，AIC有32个flagId，支持的取值范围为0-31，如果flagId的值超出该范围，则截取低5bit（例如，flagId=35时，截取后为3）；AIV有16个flagId，支持的取值范围为0-15，如果flagId的值超出该范围，则截取低4bit（例如，flagId=17时，截取后为1）。
    
    - 每个flagId都对应一个计数器，当调用[CrossCoreWaitFlag](cross_core_wait_flag_isasi.md)时，若计数器值为0则会阻塞后续指令下发，已下发指令可正常执行；当调度模块感知到所有参与同步的核（具体包含哪些核与设置的核间同步模式有关）完成（调用了CrossCoreSetFlag）同步后，会将与设置的flagId对应的计数器的值增加1。此时，计数器值为非0，阻塞解除，并且将对应计数器的值减去1进行还原。具体执行逻辑与细节可以参考[关键特性说明](key_features.md#ZH-CN_TOPIC_0000002586300741)。每一个计数器计数范围为0-15。如果调用CrossCoreSetFlag的次数超过15次，计数器的值超出该范围，则会异常报错，中断流程。
- 核间同步的模式为模式0、1、2时，同一个flagId用于不同核间同步模式的约束：
    - 同一核上，若同一个flagId需用于不同核间同步模式，须在模式切换前完成前一个模式的所有同步操作——即确保该flagId关联的所有CrossCoreSetFlag与配套CrossCoreWaitFlag调用均已执行完毕。
    - 对于不同的核，可以直接将同一flagId用于不同的核间同步模式，具体包括以下2种场景：
        - 多个AI Core之间，使用flagId=0同步所有的AIC（模式0）；单个AI Core内，使用flagId=0同步所有AIV（模式1）。
        - 单个AI Core内，使用flagId=0同步所有AIV（模式1）；另一个AI Core内，使用flagId=0同步AIC与所有AIV（模式2）。
- 使用该接口模式0时，建议开启batchmode模式，使算子独占全部所需核资源，否则可能因满足以下条件导致死锁：
    - 多流并发场景（≥2条执行流）。
    - ≥2个算子并发执行。
    - 所有并发算子的核数总和超过物理核数。
    - ≥2个并发算子使用了核间同步功能。

    具体而言，在多流场景下，某条流的核间同步算子虽分配到n个物理核，但可能仅有n-m个核先被调度执行，而其余m个核因被其他流的核间同步算子抢占而尚未启动。先启动的n-m个核执行到核间同步时等待剩余m核完成，而剩余m核因被其他流的核间同步算子占用而无法释放，形成死锁。
    核函数（Kernel）直调场景下通过[\_\_schedmode\_\_\(mode\)](../../../../../guides/programming_guide/language_extension/simd_builtin_keywords.md)限定符来设置batchmode模式；工程化算子开发场景下，通过TilingContext的SetScheduleMode接口来设置batchmode模式，具体请参考《[基础数据结构和接口](https://gitcode.com/cann/metadef/blob/master/docs/zh/api/README.md)》。

## 调用示例<a id="section837496171220"></a>

**表4**  样例描述

| SCENARIO_NUM取值 | 业务场景 | 使用的同步模式 |
| --- | --- | --- |
| 0 | 纯Vector计算场景（16个AIV） | mode0（AIV全核同步） |
| 1 | 纯Vector计算场景（2个AIV） | mode1 |
| 2 | Cube与Vector融合计算场景 | mode2（AIC等AIV）、mode2（AIV等AIC）、mode0（AIC全核同步） |

如上表所示，当SCENARIO_NUM取不同值时，会分别演示纯Vector计算场景和Cube与Vector融合计算场景下三种同步模式的具体使用方法，下面展示了纯Vector计算场景的部分调用代码：

```cpp
    AscendC::Muls(xLocal, xLocal, float(AscendC::GetBlockIdx()), this->blockLength);
    AscendC::SetFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID0);
    AscendC::WaitFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID0);

    // Unified Buffer（UB）到GM搬运启用原子累加。
    AscendC::SetAtomicAdd<float>();
    // DataCopy属于PIPE_MTE3流水操作。
    AscendC::DataCopy(atomicResultGm, xLocal, this->blockLength);
    // 当本AIV完成前置PIPE_MTE3(DataCopy)流水操作后，通知其他AIV核，本AIV已经完成。
    AscendC::CrossCoreSetFlag<0, PIPE_MTE3>(0);
    // 阻塞本AIV继续往下执行指令，直到其他AIV全部都完成PIPE_MTE3流水操作，才解除阻塞往下执行。
    AscendC::CrossCoreWaitFlag<0>(0);
    // 关闭原子累加。
    AscendC::DisableDmaAtomic();

    if (AscendC::GetBlockIdx() == 0) {
        AscendC::DataCopy(yLocal, atomicResultGm, this->blockLength);
        AscendC::SetFlag<AscendC::HardEvent::MTE2_MTE3>(EVENT_ID0);
        AscendC::WaitFlag<AscendC::HardEvent::MTE2_MTE3>(EVENT_ID0);
        AscendC::DataCopy(atomicResultGm, yLocal, this->blockLength);
        return;
    }
```

完整样例请参考[CrossCoreSetFlag和CrossCoreWaitFlag核间同步样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/05_sync_control/cross_core_set_wait_flag)。


<!-- cannbot:related:start -->
## 相关

- [950 mix(1,2) mode=2 漏 AIV1 flag 致全零](../../../../../runbooks/precision/950_mix_1_2_mode_2_aiv1_flag.md)（`exemplifies`）：950 `__mix__(1,2)` 双 AIV CrossCore 同步必须用 mode=4；不同产品对同步模式的支持情况请参见modeId支持的取值说明。Runbook 实测 mode=2 只路由到 AIV0 并要求 950 双 AIV 改用 mode=4 加 AIV1 偏移，API 卡明确 modeId 与 Kernel 类型按产品选择，是该故障直接依赖的接口边界。
- [CrossCore 反压 flag 方向错致通算流水死锁](../../../../../runbooks/compilation/crosscore_flag.md)（`exemplifies`）：“- CrossCoreSetFlag：AI Core中的AIC/AIV在完成本核前置位的pipe流水任务后，调用该接口，向调度模块上报本核任务已完成。调度模块收集所有参与核的上报信息，作为全局完成标志。”与“为 matmul_reducescatter（MC2 通算融合，4P SHMEM ReduceScatter，Pattern B 先计后通）实现通算流水时，按改造指令给 `MatmulProcess`（AIC）和 `ReduceScatterProcess`（AIV）各加 mLoop 循环，并用 ping-pong 反压：AIC 在 `t >= bufferSize` 后 `CrossCoreWaitFlag<0x2, PIPE_FIX>(t - bufferSize)` 等 AIV 释放旧 buffer，AIV 在 reduce 后 `CrossCoreSetFlag<0x2, PIPE_MTE3>(t - bufferSize)` 通知 AIC。”提供双方正文证据。API 卡给出 SetFlag 向调度模块上报完成的正向语义；runbook 展示反压方向放错后形成循环等待的具体故障，因此后者是前者同步合同的可复现反例与排障实例。
- [双AIV CrossCoreFlag 的 subBlock 契约缺陷](../../../../../runbooks/compilation/aiv_crosscoreflag_subblock_507015.md)（`exemplifies`）：焦点卡定位到“epilogue `localRows<=0` 时仍发 `CrossCoreSetFlag` 再 return”，候选卡规定 SetFlag 会“向调度模块上报本核任务已完成”；该语义解释空分支为何也必须上报，才能解除对端等待。
- [稀疏反卷积精度误差源隔离配方](../../../../../runbooks/precision/cube_simt_fp32_precision_error_source_isolation.md)（`exemplifies`）：“CrossCoreSetFlag<0x4, PIPE_MTE3>(flagId);”是被诊断的 Cube/AIV 混合代码中的上报动作；“CrossCoreSetFlag：AI Core中的AIC/AIV在完成本核前置位的pipe流水任务后，调用该接口，向调度模块上报本核任务已完成。调度模块收集所有参与核的上报信息，作为全局完成标志。”给出其完成语义，可核对 dump 前的数据可见性和同步边界。
- [CrossCoreWaitFlag](cross_core_wait_flag_isasi.md)（`related`）：“在核间同步场景中，CrossCoreSetFlag接口和CrossCoreWaitFlag接口配对工作，具体功能”与“在核间同步场景中，CrossCoreSetFlag接口和CrossCoreWaitFlag接口配对工作，使用时需传入核间同步的标记ID（flagId），每个ID对应一个用于控制同步的计数器。”是双方正文中的具体合同。Wait 卡声明两接口必须成对，Set 卡给出共享 flagId 计数器以及上报/阻塞职责；阅读两端才能闭合核间同步的生产与等待链。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子（部分算子）

展示 10 / 71 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [AddLora A2 ACLNN 算子知识](../../../../../operators/aclnn/math/math/add_lora.md)（`related`）：算子声明的固定版本源码包含对 `CrossCoreSetFlag(...)` 的直接调用（第 271 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/add_lora/op_kernel/add_lora_base.h#L271)
- [ConvDepthwise2d 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/conv_depthwise2d_950.md)（`related`）：算子声明的固定版本源码包含对 `CrossCoreSetFlag(...)` 的直接调用（第 107 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/common/op_kernel/arch35/conv_opt_group_impl.h#L107)
- [BlockSparseAttention 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_950.md)（`related`）：算子声明的固定版本源码包含对 `CrossCoreSetFlag(...)` 的直接调用（第 577 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention/op_kernel/arch35/block_sparse_attention_kernel_arch35_full_quant.h#L577)
- [QuantConvolution 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/conv/quant_convolution_950.md)（`related`）：算子声明的固定版本源码包含对 `CrossCoreSetFlag(...)` 的直接调用（第 107 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/conv/common/op_kernel/arch35/conv_opt_group_impl.h#L107)
- [BlockSparseAttentionGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_grad.md)（`related`）：算子声明的固定版本源码包含对 `CrossCoreSetFlag(...)` 的直接调用（第 443 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention_grad/op_kernel/arc22/block_sparse_attention_grad_kernel.h#L443)
- [ForeachNorm A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/foreach/foreach_norm.md)（`related`）：算子声明的固定版本源码包含对 `CrossCoreSetFlag(...)` 的直接调用（第 277 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/foreach/foreach_norm/op_kernel/foreach_norm.h#L277)
- [BlockSparseAttentionGrad 950 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/block_sparse_attention_grad_950.md)（`related`）：算子声明的固定版本源码包含对 `CrossCoreSetFlag(...)` 的直接调用（第 163 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/block_sparse_attention_grad/op_kernel/arc35/block_sparse_attention_grad.h#L163)
- [DualLevelQuantMatmulWeightNz 950 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/dual_level_quant_matmul_weight_nz_950.md)（`related`）：算子声明的固定版本源码包含对 `CrossCoreSetFlag(...)` 的直接调用（第 158 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/dual_level_quant_batch_matmul/op_kernel/arch35/dual_level_quant_batch_matmul_basic_block.h#L158)
- [ChunkGatedDeltaRule A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/chunk_gated_delta_rule.md)（`related`）：算子声明的固定版本源码包含对 `CrossCoreSetFlag(...)` 的直接调用（第 304 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/chunk_gated_delta_rule/op_kernel/chunk_gated_delta_rule_stage1.h#L304)
- [FusedLinearCrossEntropyLossGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/fused_linear_cross_entropy_loss_grad.md)（`related`）：算子声明的固定版本源码包含对 `CrossCoreSetFlag(...)` 的直接调用（第 152 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/fused_linear_cross_entropy_loss_grad/op_kernel/fused_linear_cross_entropy_loss_grad_high_perf.h#L152)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->

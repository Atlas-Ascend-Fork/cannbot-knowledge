---
type: Guide
title: vLLM Ascend SiTU量化接入：INT8与MX输出、分组尾部及文档差异
description: 区分DequantSituQuant的INT32/BF16动态INT8与SituMxQuant的BF16到FP8/E8M0路线；核对注册和旧协议差异、每专家count与容量尾部、整行UB门禁、MX双缓冲及分块scale布局、SiTU舍入和Meta弱校验，衔接MoE GMM1融合与fallback。
aliases:
- torch.ops._C_ascend.dequant_situ_quant
- torch.ops._C_ascend.situ_mx_quant
- ValidateInt32Contract
- CheckInputShapesBF16
- Tiling4SituMxQuant
- SituMxQuantRegbaseTiling
- DequantSituQuantK3Kernel
- SituMxQuantAxisLast
- ComputeVfSitu
- ComputeScaleLast
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.mixture_of_experts
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_situ_quant/dequant_situ_quant_torch_adpt.h
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_situ_quant/docs/aclnnDequantSituQuant.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_situ_quant/op_host/dequant_situ_quant_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_situ_quant/op_host/dequant_situ_quant_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_situ_quant/op_host/dequant_situ_quant_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_situ_quant/op_kernel/dequant_situ_quant.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_dequant_situ_quant.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/situ_mx_quant_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/docs/aclnnSituMxQuant.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_host/situ_mx_quant_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_host/situ_mx_quant_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_host/arch35/situ_mx_quant_tiling_arch35.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_kernel/situ_mx_quant_apt.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/single_node/ops/singlecard_ops/test_situ_mx_quant.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a8/w4a8.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w4a8/w4a8_mxfp4.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_host/arch35/situ_mx_quant_tiling_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_host/config/ascend950/situ_mx_quant_binary.json
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_kernel/arch35/situ_mx_quant_axis_last.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_kernel/arch35/situ_mx_quant_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_kernel/arch35/situ_mx_quant_tiling_data.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_kernel/arch35/situ_mx_quant_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_kernel/inc/kernel_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/situ_mx_quant/op_kernel/inc/platform.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_situ_quant/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_situ_quant/op_graph/dequant_situ_quant_proto.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_situ_quant/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_situ_quant/op_host/dequant_situ_quant_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/dequant_situ_quant/op_kernel/dequant_situ_quant.cpp
  role: implementation
created_at: '2026-11-03T01:59:47Z'
updated_at: '2026-11-03T04:58:04Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend SiTU量化接入：INT8与MX输出、分组尾部及文档差异

## 先识别量化路线

本卡处理GMM1之后的SiTU及重新量化，不接管checkpoint布局和加载。普通[整数W4A8](vllm_ascend_w4a8_moe_weight_contract.md)消费INT8输出与每行FP32 scale；[W4A8_MXFP](vllm_ascend_mxfp4_weight_reload_contract.md)消费FP8输出与E8M0分块scale。两条路线均含SiTU，输入、scale和平台合同仍然不同。

Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2。两族API文档、adapter、OpDef和InferShape均全文读取，MX tiling339行、APT入口53行、Device axis-last280行和common500行，以及本卡新增的两族CMake、POD、key、注册配置和入口均全文读取。Dequant tiling712行及Device1059行已补为全文阅读；Dequant E2E仍仅读1–142/230–278/389–446，MX E2E98行全文。共享W4A8方法、注册和Meta只读原指定caller范围，保留原owner。

本卡蒸馏Host、分组、UB、搬运与量化实现的集成合同。所读Device技术体已提取到下文，仍未按独立Operator生产要求闭合CANN原语、共享tiling框架、生成的ACLNN或完整同步/数值验证，不标记Operator/source_closed完成。未执行上游、E2E、图、NPU或性能实验；平台文档只作为有版本限制的证据，不将其写成本卡verified支持，保持draft与空平台。

## 当前注册与旧API文档存在差异

Dequant API文档描述INT8输入、2–8维及static/dynamic模式，其示例使用旧dequantScale/dequantBias签名。当前OpDef却只注册INT32和BF16，C++及Torch schema增加weight_scale、activation_scale、bias、quant_scale、quant_offset和group_index；当前Meta也限定INT32/BF16二维。tiling和InferShape仍保留INT8实现分支，不能由这些遗留代码推导当前注册入口已支持该旧组合。

当前模型接入应对照实际Torch schema、OpDef与caller，不复制文档示例的参数顺序去调用新包装，更不能绕过注册直接宣称INT8旧路径可用。Dequant OpDef只列ascend910b/ascend910_93，文档也将950列为不支持；SituMxQuant OpDef只列ascend950，文档声明950PR/950DT。后者范围不能移植到[GMM+SiTU融合](vllm_ascend_gmm_situ_quant_host_contract.md)仅950PR的README边界。

这一区分也体现在构建：Dequant的Host CMake只在ascend910b/ascend910_93中至少命中一个时加入编译列表；MX的Host CMake要求ASCEND_COMPUTE_UNIT包含ascend950，binary配置只列BF16→E4M3FN/E5M2加E8M0组合。两者均启用cce-auto-sync，BUILD_OPEN_PROJECT和BUILD_OPS_RTY_KERNEL控制Host源及模块加入；构建条件不是运行成功或性能证据。父级CMake仅在ENABLE_TEST或BENCHMARK时保留tests子目录，不能由仓库存在测试推导包已包含测试或算子二进制。

Dequant的proto注释还把beta/linear_beta/activate_left写死为4/25/true，并称BF16的group_index必须缺省；当前Host仅拒绝beta=0，且Host和K3 Device明确接受BF16分组。这里按真实校验与执行路径描述，不把这些更窄的注释当成当前强制检查，也不据此扩大已验证模型配置。

## Dequant INT32与BF16输入不可混配参数

记x为`[rows,2H]`。输出固定INT8 `[rows,H]`与FP32 `[rows]`，要求偶数尾宽。当前注册两类均只接受dynamic；beta只在Host检查非零，linear_beta≤0不启用up的tanh变换，activate_left控制哪一半作为gate。

| 输入 | 必需参数 | 可选与禁止项 |
| --- | --- | --- |
| INT32累加结果 | weight_scale、activation_scale | bias可选；quant_scale/quant_offset禁止 |
| 已反量化BF16 | 无反量化参数 | weight_scale/activation_scale/bias/quant_scale/quant_offset均必须缺省 |

INT32无group_index时weight_scale为`[2H]`或`[1,2H]`；有group_index[E]时必须`[E,2H]`。bias若有，遵循相同布局合同。activation_scale为每行一个FP32值，可为`[rows]`或`[rows,1]`。反量化参考为x转FP32后乘weight_scale、再乘该行activation_scale，最后加可选bias；bias不再乘activation_scale，不能直接套旧文档的单scale参数。

BF16表示GMM已经完成反量化，若又把weight/activation scales传入，会触发明确拒绝而不是自动识别并跳过。当前W4A8 SiTU caller先以`[E,1,N]` per-channel scale调用GMM，再向Dequant入口传空反量化参数和每专家counts；整数W4A8的补偿bias与这里的可选FP32 bias不是可互换的同一字段。

Dequant adapter只先检查x二维，然后分配输出；rows=0直接返回，未进入其余Host合同校验。这一空行短路不证明同样的非空输入参数合法，也不保证其他单独API入口都接受空Tensor。

## group_index是count，跳过尾部不等于初始化尾部

INT32/BF16的group_index都可选；存在时Host要求非空一维INT64，每专家行连续。W4A8方法将type0累计group_list先用首项加diff转为type1，再转INT64交入；不能把累计边界直接当counts。

所读K3 Device group循环以groupOffset推进：每项≤0按零处理，正值超过remainingRows会截断。未提供group_index则扫描全部rows；提供的有效counts总和不足rows时，只处理前缀，输出容量尾部可能未写。调用方必须保留有效行边界，不把未初始化y或scale交给下一GMM，也不能把clamp当作专家映射或错误计数的修复器。

这里与融合GMM controller不同：后者把count直接转uint64，不提供同样的负值/clamp逻辑。两族共享group_list名字不代表异常输入行为一致，应始终在模型侧产生非负counts、正确专家顺序和一致容量。

### 整行UB、分组参数复用与INT8舍入

Dequant的INT32/BF16路线不沿列拆分：baseRowLen=1、baseColLen=H，usedCoreNum取min(rows,AIV核数)，Host分别选key30000/40000、workspace=0。rows=0时Host blockDim仍至少1，但Device usedCoreNum≤0会返回；Torch adapter的更早短路仍应单独看待。

按输入宽W=2H，INT32的Host预算为`4W+4W+(有bias时4W)+4W+(H+32)+1024`字节；BF16为`2W+4W+4W+(H+32)+1024`。不足时拒绝，不自动改走列分块。K3 Device的x、weight_scale、可选bias及out队列深度均为1；INT32就地把输入累加值Cast成FP32，BF16另用W个FP32的dequantBuf，另有W个FP32临时区。Host将isDoubleBuffer写为1不改变这些队列的实际深度，不能套用MX的双缓冲成本。

每个专家在各核上用ceil(groupRows/usedCoreNum)划连续行；INT32专家scale和bias先入队，DeQue后复用于该核全部本地行，最后FreeTensor。输入行队列经过Cast、SiTU、动态量化后释放；输出先EnQue/DeQue，再分别DataCopyPad写H字节INT8和一个FP32 scale后释放。scale在本地输出区的偏移是ceil(H/4)个float，而非H个float，不能按旧INT8模板的局部布局解释K3输出。

K3动态scale取整行SiTU绝对值最大值除127，scale≤0时置1；除scale后采用FP32→INT32的CAST_RINT、INT32→FP16的CAST_ROUND、FP16→INT8的CAST_TRUNC，并在各阶段使用PIPE_V屏障，在读取归约值前执行V_S事件。它不是单次FP32直接cast到INT8。实现的额外最终WholeReduceMax固定使用64个FP32元素，而Host只检查偶数尾宽；任意小H的归约安全与数值结果仍需单独验证，不能由shape校验通过证明。

遗留INT8模板在动态列分块时先遍历所有列重算SiTU求全行scale，再次遍历重算并量化，只在首块写scale；TBuf参数复制另有V_MTE2/MTE2_V事件，两轮间和输出复用存在MTE3相关事件。该成本解释仅用于识别旧技术体，当前INT32/BF16入口不采用它，也不能由旧入口检查workspace非空推导当前K3需要16MiB workspace。

## MX路线输出FP8与分块E8M0

`situ_mx_quant` adapter要求BF16、至少一维、偶数尾宽、beta>0，dst_type仅35=E5M2或36=E4M3FN；它固定axis=-1。输出y为原shape尾宽折半，mxscale为原前导维加`[ceil(H/64),2]`，最后的2是MX块的对齐布局，不是两个独立per-token FP32 scale。

MX InferShape限制1–7维，允许将正axis规范化为最后轴；真实tiling却要求字面axis=-1。Torch入口已经固定-1，直接底层caller不能用InferShape接受正轴的结果证明launch也接受。真实tiling拒绝empty输入，adapter没有Dequant那样rows=0的提前返回。

MX Meta检查dtype、beta和dst_type，却没有adapter的尾宽偶数检查；odd shape可能在Meta被整数折半后才由实际入口拒绝。Dequant Meta则虽然检查偶数和INT32/BF16，却忽略scale、group_index、beta及quant_mode合同。因此二者Meta通过都不能作为完整Host验收。

### MX分块、UB与有效尾部

MX tiling以256输出元素为基本尾轴块，前导维折叠为M行。POD的inputDim2保存输出N=H，inputDim0固定1；不能按结构体的输入命名再除一次2。M方向核数取min(M,AIV核数)，剩余核预算才分给ceil(N/256)个N块；Device将行余数及N块余数分给前面的核。hasLinearBeta和dstTypeIndex共同组成模板key，分别决定是否编译up的tanh及E4M3FN/E5M2分支；activate_left、beta和linear_beta仍经POD传递。Host workspace为0，非使用核在Process开头返回。

设F=maxBasicNumUbDim1×maxBasicNumUbDim2，每基本块含256输出、512输入元素。Device实际缓冲字节如下；align32/64表示向上补齐到相应字节边界。

| 缓冲 | 深度/实际分配字节 |
| --- | --- |
| 输入BF16队列 | 2份，每份1024F |
| 输出FP8队列 | 2份，每份256F |
| 输出E8M0队列 | 2份，每份align64(8F) |
| SiTU BF16中间区 | 512F |
| maxExp及halfScale | 各align32(16F) |

Host每基本块预算3120字节，先从平台UB减32+128字节保留量，再选择能容纳的块数；当整行块数可放入时才增加行因子。实际分配存在独立对齐，不能把FP8的1字节输出成本误当成整个融合操作的UB成本。Host在可用块数不足1时仍将N因子设为1，代码未提供二次容量拒绝；极小或错误平台UB信息的安全性未验证。

CopyIn对两半输入分别DataCopyPad，行stride来自2N，第二半在UB中的起点按完整tile容量确定。末N块只搬真实currentN，计算行宽补齐至64；尾部Cast采用ZEROING掩码，后续补齐区域写零后参与分块指数归约。CopyOut只写真实N列FP8，scale按alignedN/32字节写出、每行stride为ceil(N/64)×2；因此不足64的尾部仍占成对scale位置，不应裁掉最后一个scale字节后喂给GMM。队列分配、入出队和释放承担搬运阶段关联；不能删除队列或只保留裸TBuf后假定相同同步成立。

MX SiTU把BF16输入转FP32计算：tanh在|x|<0.6时用带FMA的九次多项式，否则采用2/(1+exp(-2x))−1；结果先按CAST_RINT舍回BF16，再进入MX量化。指数归约每32输出元素一组；E4/E5分别使用0x0400/0x0780指数阈值，生成E8M0字节及内部BF16倒scale，随后在BF16域相乘、转FP32，再饱和RINT到FP8。zero/特殊指数另有分支，不能用FP32直接量化参考宣称逐位相等，也不能把E8M0按普通FP8浮点数做torch.to转换来替代位布局。

arch3510的Init另设置FLOAT_OVERFLOW_MODE_CTRL位；本文件未给出相应恢复动作。该源级副作用、NaN/Inf与溢出、图内重放、尾部精度和真实队列同步仍需在目标CANN/设备验证，不能由cce-auto-sync选项或Host零workspace得出已经安全或更快的结论。

## 模型caller与测试的实际证明边界

W4A8_MXFP融合条件不满足时，先用GMM产生BF16中间结果，再调用MX SiTU，当前caller显式activate_left=True、dst_type=E4M3FN，并归一化输出scale布局。它不把INT8 Dequant的FP32 scale改名后拿来复用，也没有给MX SiTU传入group_index的接口。旧expanded buffer尾部如何消费必须结合当前GMM与有效行合同检查。

Dequant E2E定义INT32累加和FP32参考、每专家scale/bias、BF16已反量化路线及counts尾部比较；所读断言将INT8误差容差设1 LSB，并分别比较FP32 scale。名为exceeding_rows的case实际含负首项，后续正count超过remainingRows；不能只据名称宣称它覆盖了所有非负计数、总和越界或任意专家分布。MX E2E98行主要断言若干共享/路由shape与dtype，不是完整FP8数值参考验证。本次均未执行。

Agent应先选INT32→INT8、BF16→INT8或BF16→MX路线，再分别验证scale/bias顺序、激活左右半部、beta、有效counts与容量尾部。以固定版本高精度参考比较输出和scale，覆盖零行、零专家、极端激活、布局与图生命周期，最后才比较融合、非融合及量化准备成本。已有Host合同和测试文件不构成模型全精度、硬件支持或性能结论。

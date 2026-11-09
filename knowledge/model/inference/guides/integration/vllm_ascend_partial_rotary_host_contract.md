---
type: Guide
title: vLLM Ascend Partial RoPE接入：原位别名、混合精度与Host分派
description: 沿Partial RoPE原位入口、Host与Device分派核对切片、4D广播、逆旋转、FP32位置表、950模式及A2/A3对齐/填充；记录mixed模式计算、队列所有权与拷贝容量的静态差异，保留executor与设备数值待验。
aliases:
- inplace_partial_rotary_mul_npu
- BaseDeviceAdaptor.apply_partial_rotary_inplace
- Tiling4RotaryPositionEmbedding
- Tiling4InplacePartialRotaryMul
- InplacePartialRotaryMulTiling
- RopeRegBaseTilingClass.JudgeSliceInfo
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.precision
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_host/inplace_partial_rotary_mul_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_host/inplace_partial_rotary_mul_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_host/inplace_partial_rotary_mul_tiling.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_host/inplace_partial_rotary_mul_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_host/inplace_partial_rotary_mul_a3_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_host/rope_regbase_tiling_base.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/inplace_partial_rotary_mul.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_op.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_host/rope_regbase_tiling_a_and_b.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_host/rope_regbase_tiling_ab.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_host/rope_regbase_tiling_aba_and_ba.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_host/rope_regbase_tiling_bab.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/apply_rotary_pos_emb_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/inplace_partial_rotary_mul.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/inplace_partial_rotary_mul_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotary_position_embedding_reg_a_and_b.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotary_position_embedding_reg_a_and_b_mixed.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotary_position_embedding_reg_ab.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotary_position_embedding_reg_ab_mixed.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotary_position_embedding_reg_aba_and_ba.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotary_position_embedding_reg_aba_and_ba_mixed.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotary_position_embedding_reg_bab.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotary_position_embedding_reg_bab_mixed.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotate_interleaved_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotate_interleaved_split_bs.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotate_interleaved_split_bs_pad.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotate_interleaved_split_bsn.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotate_interleaved_split_bsn_pad.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotate_interleaved_split_s.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/inplace_partial_rotary_mul/op_kernel/rotate_interleaved_split_s_pad.h
  role: implementation
created_at: '2026-11-03T01:58:58Z'
updated_at: '2026-11-03T05:25:41Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Partial RoPE接入：原位别名、混合精度与Host分派

## 接入目标与证据范围

新模型的部分head维旋转、inverse RoPE或FP32位置表接入时，需要核对模式、旋转区间、广播、真实原位对象及平台Host分派。本卡固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2；全文读取OpDef/proto、顶层dispatcher、A2/A3 tiling、共同regbase检查、数据结构、device dispatcher及两份CMake，另读Torch binding/Meta与DeviceAdaptor明确片段，随后补齐四个950专门Host tile共916行，总计16来源3096行。

950四个专门Host tile已全文读取，本次又逐份读取21个Device/辅助头：18个当前执行链来源、3个未被当前dispatcher包含的旧RotateHalf实现；以完整结构投影和同族完整差异审阅保留所有代码分支。生成aclnn executor、SDK公共库、编译环境与运行时同步仍没有完整闭包。本卡只生产框架Guide，不作为Operator或source_closed结论。未导入或执行上游、UT、模型、NPU、编译、图或性能实验，保持draft和空平台。

[交错RoPE选型](../../runbooks/precision/interleaved_rope_npu_op_selection.md)保留此前具体算子的布局与数值观测；本卡自定义算子有显式mode参数，不能把那些算子的限制机械移植过来。[CP/O投影](vllm_ascend_cp_oproj_weight_protocol.md)维护inverse RoPE前后的head交换与通信，[图lowering排障](../../runbooks/precision/custom_op_graph_lowering_converter_meta_correctness.md)维护跨版本的Meta/converter经验。

## Torch入口：副作用与静默返回

Torch schema为inplace_partial_rotary_mul(Tensor(a!) x, r1, r2, str rotary_mode, int[] partial_slice, bool negate_sin=False)->()。调用修改x并返回None，不能把返回值当旋转后的新Tensor；图需要保留x的mutation/alias语义，也不能在capture后换成无关storage再假定原引用跟随。

C++把half/interleave/quarter/interleave-half分别映为0/1/2/3。未知字符串直接return，既不报错也不启动设备算子；例如拼写错误可留下未旋转数据而无异常。合法字符串才检查x为4D并调用aclnn。schema中有mode不代表每个平台实际Host都接受全部模式。

同名Meta是void no-op，未验证dtype、shape、slice或模式。这是无额外输出的副作用接口，不应凭fake执行成功推定真实tiling已经通过。新模型至少检查已捕获图是否保留mutation，并比较原位结果；本次没有执行这类验证。

OpDef使用AutoContiguous，而Torch把原对象作为原位参数；实际executor的contiguous与写回链未在本卡闭合，不能从标记推导任意strided view与外部别名都安全。保存原shape、stride、storage和alias所有者后再进行图/布局优化。

## Python适配与逆旋转

BaseDeviceAdaptor.apply_partial_rotary_inplace将2D x先unsqueeze(-2)，再将3D工作Tensor unsqueeze(1)为4D view，目标不因这两个操作被显式复制；返回原x。它不为cos/sin自动增加同样的轴，不是任意输入rank或广播的统一校验器。

适配器固定rotary_mode=interleave并传[start,end]。inverse为真且支持INPLACE_PARTIAL_ROTARY_MUL_NEGATE_SIN能力时，保持sin并传negate_sin=True；不具备能力时创建-sin Tensor并省略该关键字。两条路线的临时分配和Host参数不同，不能仅删除负号或同时取负并置flag。

顶层Host在950明确拒绝negate_sin=True。能力门禁与真实平台分派必须一致，不能直接把另一平台调用的flag传到950；Python的负sin路线也需要实际dtype、地址寿命和图/eager数值验收。逆旋转的sin符号合同不负责CP中head重排或权重通信。

## partial_slice与dtype的接入检查

接入侧应先保证partial_slice恰有两个元素、0<=start<end<=完整head宽D，且旋转宽R=end−start与cos/sin末维一致，并满足实际模式的配对整除条件。已读C++不检查列表长度；A2/A3 Host直接读前两个元素，不能把缺少校验当作对短列表、负offset、越界或奇数旋转宽的支持。

共同950检查把x/cos/sin/输出约束为4D，cos与sin同shape/同dtype、输出与x同shape/dtype、维度为正；dtype接受同精度FP16/BF16/FP32，或低精度x配FP32 cos/sin。它按完整D校验<=1024以及mode的2或4整除关系，再检查slice非空、在D范围内、cos/sin末维=R。slice校验与完整D整除不是同一条件，不能推定所有R的设备配对规则都已由共同函数检查。

空列表在共同950解析中表示[0,D]；非空[0,0]会得到R=0并失败，二者语义不同。proto缺省[0,0]不能当成所有路径的自动全维旋转。共同代码没有把cos末维强制等于完整D，实际要求是等于旋转区间宽，不能为对齐旧注释而错误扩展位置表。

proto说明A2/A3支持half和interleave、D<=896，但当前A2/A3实际tiling显式只接受mode==1。采用实际Host可达路径，并把说明与实现差异保留为版本边界；不要由字符串映射成功宣告half已可执行，也不因某些Host缺少相同上限检查就宣布已扩大支持。

## A2/A3：FP32位置表只进入特殊tile

顶层Host识别低精度x配FP32 cos/sin且SoC为910B或910_93时，直接走A2/A3 tiling。它要求x/cos/sin均4D，cos/sin同shape、cos/sin类型相同且与x同dtype或为FP32；实际区间宽等于cos末维，cos第0维须等于x第0维，cos第2维须为1。

special路径还需要cos第1维为1、x第1或第2维为1、R按输入dtype对齐（FP16/BF16为16元素，FP32为8），R<=64且UB容纳该批head tile。使用key1/2区分广播情形，FP32位置表再加10得到11/12。以上只是实际判断条件，不能把“对齐且R64”简化成任意batch/head一定可用。

special tiling失败且是FP32混合位置表时，Host直接返回GRAPH_FAILED，没有转普通split fallback。非混合情况才以2000为基数，按dtype、是否padding和SplitS/BS/BSN组织fallback；其归一化后的batchSizeOut必须为1。代码存在多个布局分支，也不代表每个分支都能越过前置shape检查和最终batch门禁。

该Host按UB容量先尝试一次处理S，再不足时进一步拆B/N；记录真实R、完整D、head数、UB容量、使用core数及key。两类A2/A3路径都申请16MiB系统workspace，不能用“旋转原位”推导零工作区，也不能把固定workspace直接写成实测额外峰值。

## 950候选顺序、布局与失败传播

950按AAndB、AB、ABAAndBA、BAB顺序调用候选DoTiling。每个候选先读取共同shape/attr和平台信息，再判断IsCapable；只有GRAPH_PARAM_INVALID才试下一个，其他状态包括GRAPH_FAILED立即返回。后选路径不会自动恢复前一路的真实失败。

共同布局识别根据cos前3维与x的相等/广播关系选择NO_BROADCAST、BROADCAST_BSN、BSND、SBND、BNSD，并可能合并1SND维度。布局名称不是调用者自由标注的字符串；同shape下轴含义与head归属仍须来自实际模型。共同检查通过也不等于某个专门tile的UB划分已经可用。

四个专门Host tile已补齐，其候选条件和key如下。这里的layout是共同函数计算结果，不是仅按注释猜测输入轴。

| 950候选 | IsCapable条件 | 同精度key | BF16 x/FP32 cos；FP16 x/FP32 cos |
| --- | --- | --- | --- |
| AAndB | NO_BROADCAST或BROADCAST_BSN | A=20040，B=20041 | A=20140/20240，B=20141/20241 |
| AB | SBND | 20030 | 20130/20230 |
| ABAAndBA | BNSD；cosb==1选BA，否则ABA | BA=20011，ABA=20010 | BA=20111/20211，ABA=20110/20210 |
| BAB | BSND且cosb==1 | 20020 | 20120/20220 |

各tile按旋转区间R和mode的dSplitCoef分别计算x与cos/sin的32字节对齐宽；混合精度不能只按x的2字节预算。AAndB将B/N/S合并为行；全不广播时每行同精度约8×dSizeX，混合精度为4×(dSizeX+dSizeCosSin)的队列预算，全广播另扣独立cos/sin开销。UB不足返回失败，ubFactor还受4095/dSplitCoef的拷贝块数限制。这里是Host队列账，未验证全部实际Device资源。

AB先对B×S分核，工作量较小时再拆N，用ubFactorBS/ubFactorN平衡x与位置表；ABA/BA优先尝试B或S整除核数，否则比较两种分核得到的使用核数，再分配S/N/B的UB tile。BAB先算UB，再比较“使用核数×可处理S因子”的两种分核方案，并检查最终核数不超平台core数。不能只把更多core或更大ubFactor当作跨形状最佳配置。

四个Host候选均申请16MiB workspace，并写入slice、rotaryMode、布局和core/UB字段；不是每个字段在每个route都活跃，未设置字段也不能当作该route的活跃tile。全部候选返回不适用后的membase类DoOpTiling当前只返回SUCCESS，没有通用计算与tiling保存；这不能当成所有未知layout都有安全fallback。新模型必须观察实际选择的key和非空tiling，而不能只凭上层成功码认定设备已旋转。

Device dispatcher按__DAV_C310__区分regbase同/混合精度模板与另一组interleave模板。前者有200xx/201xx/202xx key，后者有1/2、11/12及2000系列；本次已补读对应模板的搬运、局部保留区间、原位写入和尾部实现，但没有执行generated executor与真机。未知key也没有在该dispatcher统一抛错，不能忽略Host与binary配对。

## Device模式、广播与数值路径

以下是固定源码的执行机制，不是四种模式在所有dtype/layout上均已通过的声明。同精度regbase将低精度加载到FP32向量寄存器计算，再以RINT、NO_SAT转换回输入类型；cos/sin由调用者提供，不在核内重算三角函数。

| mode | 当前同精度计算与输出布局 | 适配时的区别 |
| --- | --- | --- |
| HALF=0 | 旋转区间分为两半；前半为x0*c0−x1*s0，后半为x1*c1+x0*s1 | cos/sin逐坐标保留，不能假设两半表值相同 |
| INTERLEAVE=1 | 相邻偶/奇元素解交错，交换并对奇支取负，再交错回原布局 | 与half分组不是同一个位置排列 |
| QUARTER=2 | 四分区的0/1、2/3分别成对旋转 | 不等于整个区间首尾两半配对 |
| DEEPSEEK_INTERLEAVE=3 | 读相邻配对输入，输出分成两段half布局 | 对外输出布局区别于普通interleave |

950 AAndB可整行广播同一位置表，AB把B×S工作项的位置表复用于N，ABA/BA通过B/N/S循环步长区分逐B与B广播，BAB在S位置间移动并复用于B/N。实际GM地址包含sliceStart，输出仅写旋转区间；未旋转区间依赖原位x保留，不能把未写的独立输出buffer当完整结果。

混合精度模板的float位置表有独立对齐宽，不能复用低精度x的字节预算。其计算分派不与同精度对称：AAndBMixed、ABMixed、ABAAndBAMixed最终直接调用InterleaveModeVFMixed或BatchInterleaveModeVFMixed，未按HALF/QUARTER切换相应数学函数；BABMixed对INTERLEAVE/HALF/QUARTER三个条件都调用InterleaveModeVFMixed，并没有DEEPSEEK_INTERLEAVE的Compute分支。共同Host接受四种mode并按dtype选择mixed key，因此要逐一检查实际可达模式与参考布局；不能由Host接受mode推定mixed等价，也不能在未运行前断言已复现数值失败。BatchInterleaveModeVFMixed的TX步进还包含float/TX字节比例，需按实际slice和迭代宽验证。

另有两处静态资源/所有权差异应优先验收：同精度ABA/BA在B广播分支从cos/sin队列取出的两个Tensor，释放时分别交给sin/cos的相反队列；非广播与mixed对应代码按原队列释放。AB的DEEPSEEK_INTERLEAVE拷贝分支使用完整D的blockLen，而队列预算依旋转R；partial slice下要核对实际拷贝容量。这些是源码风险，未证明SDK一定抛错或NPU已经发生越界。

## A2/A3 Device：special与Split/Pad差异

special的1/2和11/12路径只做interleave；FP32表配低精度x时先将x转FP32，按相邻元素gather与交替符号计算，再RINT回写。negateSin改变交替符号，不是第二次生成位置表；输出DataCopyPad保留完整D与R之间的目标stride。

普通SplitS以S片段覆盖batch/head；SplitBS对同一S拆batch，SplitBSN再拆head。三者有tail时主循环少一次，再以真实tail计数执行，不能按完整UB tile回写。同一cos缓冲会再用于sin，代码在覆盖前等待V_MTE2，在搬入后等待MTE2_V；不能因输入和输出原位就删除这些事件。

Pad版本将旋转R按FP16/BF16的16元素、FP32的8元素对齐为headDimAlign，x/sin/cos/输出及FP32临时区均按此宽预算。GM拷贝只搬真实R，通过源/目标stride跳过完整D中未旋转区域；向量运算、gather和广播使用对齐宽，最后只回写R。SplitSPad逐batch拷贝，BSPad逐batch tile，BSNPad逐head tile，三者GM offset不可互换。位置表copy自动padding后扩到各head；BF16广播中的half reinterpret是按位搬运，不是数值转换。

同精度FP32路径直接计算；低精度普通fallback用三份FP32临时buffer完成乘加，再RINT回写。当前dispatcher没有包含rotate_half.h、rotate_half_bf16.h、rotate_half_base.h这三份旧RotaryPositionEmbeddingTilingData模板；它们已全文审阅但不作为当前HALF可达实现计入sources，避免把目录存在旧代码等同当前binary接线。

## 构建、图与新模型验收

当前Host CMake经add_modules_sources的aclnn入口收集源码，开启cce-auto-sync、relocatable kernel binary等选项。注释中的旧target_sources清单不是当前有效构建流程，实际选择的SoC、generated API与动态库仍需与安装版本核对；编译选项不构成完整同步或图捕获证明。

先固定模式、切片、full/R宽、x/cos/sin dtype和前3维广播，核对目标storage及模型中未旋转区间保持；再检查正向/逆向、相同/混合精度、对齐/非对齐、special成功/拒绝、950候选及未知字符串。覆盖eager与图的输出、输入别名、sin临时值寿命和错误传播，正确后再测Host开销、分配与端到端性能。

出现静默不旋转、错误key、slice或UB不符时，先回到明确匹配的版本与原模型参考，不通过改位置表dtype、删除广播轴或缩小模型head宽掩盖。以上已读Device机制仍需runtime executor、数值和平台验收；本卡未运行Lint、上游测试或真机。

---
type: Guide
title: vLLM Ascend Attention公共执行层：前缀、页尺度与缓冲所有权
description: 适配Attention模板时核对common的B项累计长度、Q/K padding、页面/scale地址与BF16位拷贝，区分三套Buffer和3510锁/5102分支；串接MX加载、在线softmax及FD合并的精度、尾部和资源门禁。
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.model_adaptation
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/CopyInL1.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/FixpipeOut.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/arch35/vf/vf_basic_block_aligned128_no_update_sfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/arch35/vf/vf_basic_block_aligned128_update_sfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/arch35/vf/vf_basic_block_unaligned128_no_update_sfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/arch35/vf/vf_basic_block_unaligned128_update_sfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/arch35/vf/vf_basic_block_unaligned64_no_update_sfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/arch35/vf/vf_basic_block_unaligned64_update_sfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/arch35/vf/vf_basic_block_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/arch35/vf/vf_flash_decode_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/arch35/vf/vf_flashupdate_new.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/arch35/vf/vf_mul_sel_softmaxflashv2_cast_nz_sfa.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/attn_buffer.h
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/attn_buffer_manager.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/buffer.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/buffer_manager.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/buffer_mix_core.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/buffers_policy.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/init_output.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/matmul.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/memcopy/fa_gm_tensor.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/memcopy/fa_l1_tensor.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/memcopy/gm_coord.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/memcopy/gm_layout.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/memcopy/offset_calculator_v2.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/memcopy/parser.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/common/op_kernel/offset_calculator.h
  role: implementation
created_at: '2026-11-03T05:51:30Z'
updated_at: '2026-11-03T05:51:30Z'
platforms: []
aliases:
- AttentionCommon::InitOutput
- ActualSeqLensParser::GetMxVscaleTBase
- OffsetCalculatorImpl
- fa_base_matmul::ResetIdCounter
- MatmulKMx
- FaVectorApi::ComputeScaleValue_VF
scope:
  any_of:
  - all_of:
      framework:
      - vllm
  schema: model.inference.v1
---

# 适用范围与调用方责任

固定 Main `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2`，逐份读取 `csrc/attention/common/op_kernel` 的27个执行/布局/VF文件。读取采用全文结构投影，以及相对已读 [SharedKV局部执行层](vllm_ascend_sharedkv_metadata_contract.md) 的完整新行/上下文差异。公共模板的实现机制已经提取，不等于每个调用算子实际实例化、安装SDK或NPU精度/性能都已验证。`csrc/common/include/kernel`是另一组helper，不由本卡替代。

[自有SparseMLA](vllm_ascend_sparse_mla_host_dispatch_contract.md)和其它Attention族需先确认实际include路径、宏与模板实参。几个目录都有同名`buffer.h`、`offset_calculator.h`及头文件guard；include次序可能使另一份定义先占guard。不能把函数名字相同、同为arch35或同样数据类型当作ABI相同。

## 长度、padding与地址单位

| 入口 | 本公共层的实际协议 | 容易混淆的边界 |
|---|---|---|
| ACCUM parser | B项累计结束值；batch0起点为0，b>0起点取arr[b−1]，长度为相邻差 | 与SharedKV局部helper的B+1、显式首零数组不同 |
| BY_BATCH parser | 无长度使用default；一个元素广播；多个元素按batch取 | 不检查数组值域、batch匹配或容量 |
| TND Q/KV地址 | 由上述GetTBase加本批token坐标，再乘layout stride | 直接传B+1前缀会产生偏移差一批 |
| MX V scale起点 | 累加此前每批`ceil(actualLen/64)` | 不是总token起点除64，短batch各自占完整scale块 |
| padded Q/KV | 加`storageS − paddingSize − actualLen`再取线性offset | 无防下溢；padding和长度必须与真实storage相容 |

`FaGmTensor`默认实际长度类型为uint64，调用方可以显式选其它类型；parser不做数值转换式校验。负int32若转成无符号、非单调累计值、空ACCUM数组、超过storage长度都必须在上层拒绝。PSE的BN2GS1S2地址也采用Q padding偏移，不能只修Q指针而保留旧PSE坐标。

GmLayout按编译枚举建立连续逻辑stride：BSNGD/BNGSD/NGBSD、TNGD/NGTD/NTGD、BSND/BNSD、SBNGD等只重排轴，默认不是任意外部view。PA_BnBsND/PA_BnNBsD先查`blockTable[b*capacity+logicalBlock]`再算页内位置；PA_NZ再拆D1/D0。返回offset以该GlobalTensor元素为单位，block table的值不经过范围校验。空的通用layout/category主模板也不提供“任意枚举自动支持”。

Scale专用布局不同：PA_NZ_K_SCALE固定把页内token拆成16个bs0，物理页跨度由bs1、D和bs0构成；ANTIQ_ND忽略batch/token，只按head/D；BS2/BNS2按batch/token或head/token；NGD用于post-quant。ANTIQ_BnBs/BnNBs的代码使用`GetStrideBlockSize()`作除数，而连续layout该stride为1；应核对实际调用/期望，不能仅从名字把它视为完整分页索引器。V_SCALE_TND specialization存在也不等于所有GmFormat已经映射到它。

## GM→L1：数据和尺度不要互换

常规ND→NZ在16元素行边界对齐；310/310R6/5102编译分支下FP8/HiFloat8/INT8采用32元素C0对齐。PA拷贝按页边界拆分，支持BNBD、BBH和NZ地址；带RoPE的`NoContinue`版本允许NoPE/RoPE分别传pageStride覆盖默认连续页跨度，而同名普通版本不采用该覆盖。选择错误helper会把非连续页当连续页读。

尺度拷贝常用BF16重解释把两个8位scale打包搬运，ND与DN各有nValue/stride除2的约定；它不是将E8M0数值转BF16。`GmScaleCopyInToL1PAForND`另在取源时用offset*2，DN分支采用自己的步幅，不能从普通KV copy照搬元素偏移。调用方必须保证scale轴、偶数打包、物理容量和scale/data所指同一页。

## 三套buffer及资源所有权

| 头/分支 | 事件与初始化 | 集成限制 |
|---|---|---|
| buffer.h | 内核内构造顺序产生mod11跨核ID；内部事件只在AIC初始化；C2另有映射 | 与SharedKV局部mod16不同，不能混用计数器与flags |
| attn_buffer.h | 增加ResetIdCounter、INTERNAL/EXTERNAL ID和SET_WAIT/LOCK_UNLOCK | EXTERNAL仅借用ID；UnInit不能按内部所有者重复释放 |
| buffer_mix_core.h | 5102时由manager选入；内部事件不再限制AIC | 删除C2/后向跨核接口，不能当上面模板的完整替代 |

LOCK_UNLOCK的Alloc/Release/Lock/Unlock只在`__NPU_ARCH__==3510`编译；其它分支可能没有这套互斥动作，不能认为换SyncMode就自动建立屏障。ATTN的Set/Wait把producer/consumer pipe映射到Mutex，直接Lock/Unlock又带显式pipe；二者要与调用路线一致。

跨核mode4用16偏移区分两个AIV，UB、GM、L1及BACKWARD/BOTH方向采用不同Set/Wait pipe；isReuse还把部分Vector同步切换到MTE3。invalid ID=16是未使用方向标记，不能被当作随意可等待的有效事件。资源创建顺序、方向、初始credit及最后drain需要成套维护。

BufferManager将字节offset单调累加，FreeBuffer为空，没有容量验证或回收；ATTN还允许从local地址0直接构造固定内存视图。调用者必须证明各段容量和对齐，总分配不重叠，且不会跨并行请求共享临时区。DB与3buff分别维护分配/复用游标，4buff的head/tail/used以及Matrix2×2的mExtent有非空/非零前提，不是带保护的通用容器。

`AttentionCommon::InitOutput`只在AIV执行，按vecCoreNum均分GM范围、先检查offset，再用固定UB块写整块/尾部；可选锁或MTE事件只保护该UB写出。vecCoreNum与POP_BUF_ELE_SIZE均须非零，UB地址/大小必须由调用者保留。这个函数本身没有全核/Host stream完成屏障，调用后是否可读要由上层执行链建立依赖。

## Matmul与量化的实际分支

LoadData按310/310R6/5102与旧架构分别建立2D/3D转置和fractal步幅；FP8/INT8部分转置用两步M切片补奇数dstStride。MX加载同时取数据与E8M0尺度，部分地址把data的L1offset右移5作为scale偏移；FP4x2/HiFloat4x2还采用32/64分组及packed存储专门公式。不能把packed元素数量直接当原始逻辑K。

MatmulFull/K/N/KM及MX变体有各自选定切分轴、tail和L0C偏移。M=1会将实际Mmad M扩为16，realM可以覆盖M，但不会自动扩大输入/output物理容量。Mmad是否清初值主要由isOutKFisrt与当前K块决定；MMParam中cmatrixInitVal字段存在不保证每条helper都消费它。Kbias首块从bias初始化、后续累加；它与普通清零路径不同。

这些helper只在若干L0类型上提供MX分支，一些模板未匹配的类型不加载数据；某些MatmulK/N路径的A/B事件顺序也与Full或独立SharedKV不同。Agent应核对真实实例与buffer策略，不把通用C++模板接受类型推断为数值正确、已实例化或性能更好。Fixpipe支持row-major UB/GM与NZ配置，dualDst/stride按实际消费布局选取。

## 在线softmax、量化PV与FD合并

六个SFA VF模板分别覆盖128列、1–64列、65–127列，以及第一次/更新前一max。输入必须FP32，概率支持FP16/BF16，按ROUND/SAT压缩并以NZ交错布局写出。尾部masked reduce或极小负值策略各异，不应统一替换为全部128列有效。公共层比SharedKV局部BF16-only wrapper更宽，但调用Host仍可更窄。

FlashUpdate先以exp(max_old−max_new)重标定旧PV，必要时分别乘当前/前一V反量化尺度，再加本块；最后除sum。full-quant会恢复每行P尺度，并按E4M3=448、INT8=127、HiFloat8=32768的倒数缩放。通用非64整除D路径与固定块路径参数不同，部分full-quant参数只在固定块路径消费；LastDiv/InvalidLine的若干循环按D>>6运行，不能自动外推任意尾D。

FD归并先跨split取max，再将每份sum乘exp(localMax−globalMax)，归一化得到合并权重，最后对partial output加权求和；第一份初始化、后续累加。它假设partial output、sum/max及split数量是同一行、同一归一化约定，不能把未归一化PV和已归一化partial混合。行数wrapper仅分≤8与9–16，超过16没有通用fallback；reduce headDim也按64块处理。

sinks可在合并分母加入exp(sink−globalMax)，也有GS-fused半精度sink转FP32形式；需保证每行只加一次。LSE通常为log(sum)+max，但普通FlashUpdate的无效max sentinel是0xFF7FFFFF，FD helper使用0xFF167699并将相等的无效行LSE改为正无穷表达式，RowInvalid可把相应输出置零。这些是不同局部约定，不是通用NaN/Inf清理；不能套用SharedKV空LSE=0。

## 供模型适配与性能诊断Agent记录

排错记录应包含实际include/宏、长度类型及B/B+1协议、layout/stride单位、scale打包与页身份、buffer容量/事件所有者、切分轴和归约精度。跨batch一致性要比真正的归约分组，性能要测实际Host/Device时间与内存；源码常量、缓冲个数和async flags都不是测量结果。本次未运行编译、上游测试、NPU或服务，平台保持未知；各调用Operator的输入门禁、最终队列提交、graph寿命和数值验收仍须沿自己的执行链闭合。

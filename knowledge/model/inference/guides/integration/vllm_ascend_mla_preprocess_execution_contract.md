---
type: Guide
title: vLLM Ascend MLA预处理融合的Host、量化管线与Cache写入合同
description: 聚合 MlaPreprocess 的Torch适配、Host tiling、AIC/AIV同步、四种Device变体和本地迭代器，界定MLAPO新模型维度、量化与跨块stride适配。
aliases:
- MlaPreprocess
- MlaPreprocessTiling
- PpMatmulTilingApi
- MLAPO_BF16_INNER
- MLAPO_BF16_NQ
tags:
- task.implementation
- task.optimization
- topic.attention
- topic.precision
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/CMakeLists.txt
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/mla_preprocess_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_host/mla_preprocess_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_host/mla_preprocess_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_host/mla_preprocess_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/common_func.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/hardware.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/iterator.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/iterators/gm_to_l1_iterator.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/iterators/gm_to_ub_iterator.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/iterators/l0c_to_gm_iterator.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/iterators/l0c_to_l1_iterator.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/iterators/l0c_to_ub_iterator.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/iterators/l1_to_bt_iterator.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/iterators/l1_to_fb_iterator.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/iterators/l1_to_l0_iterator.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/iterators/l1_to_ub_iterator.inc
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/kernel_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/layout.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/mem.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/mma.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/set_fpc.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/simd.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/kernel/utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/mla_preprocess.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/mla_preprocess.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/mla_preprocess_mix_bf16.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/mla_preprocess_mix_bf16_nq.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/mla_preprocess_mix_bf16_qdown.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/mla_preprocess_mix_fp16.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/mla_preprocess/op_kernel/mla_preprocess_tiling_data.h
  role: implementation
created_at: '2026-11-03T05:50:03Z'
updated_at: '2026-11-03T05:50:03Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend MLA预处理融合的Host、量化管线与Cache写入合同

## 版本和接入层次

固定 Main ceac 的 csrc/mla_preprocess 33 个来源，包含全部Host文本与Device可执行结构；BF16基础和三变体以全体代码及完整差异对应阅读，未将投影视为raw全文。未编译、执行CANN/torch、启动NPU或运行精度/性能测试。OpDef只注册 ascend910b/ascend910_93；不据本地ArchType枚举推广到310P/950。

[既有MLAPO优化规则](../../optimizations/rules/mlapo_fused_preprocess_w8a8_non_cp_gate.md)描述特定SFA接入的逐层W8A8/非CP/decode门禁；本卡解释底层算子接受面，存在BF16 no_quant实现不自动解除上层接入门禁。新模型必须同时核对生产者权重/scale、实际调用和以下Host/Device分派。

## Torch参数与Cache布局

cache_mode 默认 krope_ctkv=1，kvcache=0、int8_nzcache=2、nzcache=3；quant_mode 默认 per_token_quant_symm=1，per_tensor_quant_asymm=0、per_token_quant_asymm=2、no_quant=3。解析字符串成功只保证映射存在，不表示所有组合都有Device分支。

cos/sin必须同时提供或同时None；缺失时enableRope=false，两套sin/cos参数使用同一输入。enable_inner_out默认false。slotmapping的int64会转int32，未在此做值域/溢出校验；不能把自动转换当任意slot安全。kv_cache与RoPE cache允许dim0正stride扩大，内轴除size=1轴须compact；stride单位是对应tensor元素，进入Device后由类型解释，不是通用字节stride。

物理NZ判断是cache mode 2/3、rank4且size(2)!=1，RoPE维按size(1)×size(3)推导，否则取最后一维。kv_lora_rank取wuk最后维；只对 rank=512、RoPE dim=64声明fully supported，其他值warning_once后继续，并未硬拒绝。可执行不等于精度支持，尤其内层仍有块/向量对齐与固定资源假设。

Torch函数返回传入的五个输出引用，经EXEC_NPU_CMD调用aclnnMlaPreprocess；不是自动新分配、完整检查shape或所有可选scale/bias组合。OpDef对两量化投影权重列FRACTAL_NZ、slot INT32，cache IgnoreContiguous与adapter的具体stride校验配合，不能只以全tensor.contiguous检查排除合法跨块布局。

## Host验证、tiling key和工作区

Host检查hidden rank2、wuk逻辑rank3、gamma至少一维、cache最小rank，token/模型维度须正uint32且token<=1024；cache/quant mode各0..3、两个stride>0。hidden只FP16/BF16，per-token-symm强制BF16。平台AIC/AIV/UB/L0C非0，并不完整检查每个输出、可选指针或所有矩阵乘积溢出。

实际模型尺寸从hidden/gamma/wuk和cache推导，mm1输出=qRank+kvRank+ropeDim，mm2输出=heads×(nope+rope)，mm3输出=kvRank，RMS avg=1/qRank。tiling里仍混用固定L1=512KiB、L0C=128KiB和部分UB常量，不能仅因查询了PlatformInfo就称所有硬件自适应。

PpMatmulTilingApi在16起步、倍增至512的M/N tile中筛L0C与反量化N<=256，再按带宽/转置启发式成本挑tile，生成swizzle、ping-pong K tile。成本函数不是实测时间。某些对齐/UB分母可变0时没有全面兜底；扩大维度前验证tile、headPerLoop和所有中间积，不能用正uint32单维检查替代。

CANN入口的SetTilingKey恒0，真正的内部key在MlaTilingData：inner<<9 | isBF16<<8 | quantMode<<3 | cacheMode。ABI中cacheBlockSize与两个stride用uint64，不能改成不同宽度而保持旧二进制。Host加system workspace与user workspace并检查相加溢出；Device用GetUserWorkspace，不能将系统区当s1覆写。

user区每个主要stage预留max(输入int8、上投影半精度、下投影半精度、FP32暂存)×N；量化BF16/per-token分支为4份加2N个float scale，其他3份。s1..s5有不同阶段别名与复用，不能同时当五个独立等大持久张量。编译使用混合AIC1:AIV2任务与auto-sync，未编译证明对应SDK ABI成立。

## 明确的Device分派集合

| hidden/模式 | 内部key | 实际变体 |
| --- | --- | --- |
| FP16、quant0、cache0/1、inner=false | 0/1 | MLAPO_FP16，int8投影+Cube反量化 |
| BF16、quant0、cache0/1/3 | 256/257/259，另可加512 | BF16基础或INNER |
| BF16、quant1、cache0/1/2/3 | 264/265/266/267，另可加512 | BF16动态per-token量化，cache2还量化NoPE输出 |
| BF16、quant3、cache1、inner=false | 281 | BF16_NQ，半精度三次矩阵乘，不走int8量化 |

quant2没有对应switch case；FP16的其他cache/quant/inner、no_quant的其他组合也不能由范围检查推导可执行。default仅break，没有错误或reference fallback。Agent生成配置先用整个tuple查分派表，不能逐字段合法就报告算子兼容。

## BF16管线、数值与同步

Vector先量化hidden→s1，通知AIC_MM1_START；Cube做MM1。quant0路径AIV加int32 bias、乘per-channel descale、转BF16后供split/RMS；quant1路径MM1 int32经FP32×channel×token scale在RMS/Cache生产处反量化，再转BF16。Q低秩部分做RMS+gamma+可选beta并量化，通知MM2；同时KV低秩RMS及RoPE写cache。MM2反量化完才通知MM3，Q RoPE与NoPE Einsum分别输出。

RMS epsilon固定1e-6，不从模型config传入；量化的per-token scale为maxabs/127，所读代码没有maxabs=0的clamp，因此全零/极小值必须专项验证。per-tensor输入scale先取倒数，最终经half中间值和int8饱和/舍入；BF16恢复用CAST_RINT，不能将之等同全程FP32参考。

Cache2对KV NoPE按ctkv_scale量化、Q NoPE按q_nope_scale量化；RoPE仍半精度，不能把cache2解读为所有输出INT8。INNER在第二次RMS+beta之后、量化之前将BF16低秩Q写inner_out，额外stream同步与workspace使用必须计算在内，不是外部随意选择的中间stage。

跨核flags包括QUANT1/MM1/MM2/RMSNORMQUANT2/MM2OUT/EINSUM等，不是单一全局barrier。W8A8 AIC/AIV按每5轮的计数节流，空核也参与等待/通知；修改tile/core数或提前return须验证每个flag生产消费配对，auto-sync不能替代逻辑一致。

FP16变体通过L1 bias、Fixpipe scale与uint64反量化位表示执行，不与BF16的float scale向量随意互换。BF16_NQ移除量化与token-scale阶段，三次半精度矩阵乘仍依赖QUANT1/AIC_MM2_START/EINSUMOUT等交接。不同文件同名class不表示workspace、数值路径和flags可通用替换。

## RoPE、slot和物理Cache写入

RoPE在FP32重排两半、符号翻转并计算q*cos+rotate(q)*sin，转回半精度；enableRope=false复制原始Q/K RoPE片段，仍需有效输出布局。cache0拼KV低秩+RoPE，cache1分开ND，cache2用NoPE int8 C0=32与RoPE半精度C0=16，cache3两者C0=16的NZ。

ND地址=slot/blockSize×stride0+slot%blockSize×innerSize；NZ则块内offset乘C0并按blockSize×C0跨度分段写。只跳过slot==-1，其他负值会转换成无符号地址，并未做cache容量检查；重复slot也须由调度/生产者保证不会竞争。保存真实block size、dim0 stride、slot范围及输出别名，不能只核对总元素数。

RoPE tail tiling算出lCoreRun却赋值nlCoreRun，Device同时使用专门tail loop字段；它是需要结合实际N/head/core复验的静态差异，不据此宣称已复现越界。Einsum Quant记录colTail但主乘scale循环仅遍历colLoop，扩大kvRank非64/128对齐时不得凭参数存在宣称尾列数值覆盖。

## 本地kernel工具不能继承同名公共头的结论

该目录自带kernel/include、九套GM/L1/UB/L0/Fixpipe iterator、SIMD及buffer封装，会遮蔽其他目录同名头。模板主版本部分为空，只有匹配specialization才实际搬运或Mmad；ArchType含V200/M200不等于有等价实现。HardwareInfo给固定资源大小，AsdopsBuffer按Cube/Vector宏初始化不同本地存储。

iterator的burst/gap有32字节、元素与矩阵fractal多种单位，ND/NZ/ZN变换不能只用同字节数替代。65536 stride阈值会改为逐行/逐段搬运；ND→ZN大stride分支循环未推进源/目的，尚不能据未实例化工具推导实际主路径出错。新的layout实例先核specialization与地址，再测结果。

SIMD float→BF16为RINT，其他conv默认NONE，convr显式RINT；kernel_utils的int8 clamp/round、不同RMS精度/Gemma分支和归约宏各有条件，不把通用函数名当所有dtype完整实现。Common CeilDiv、kernel_utils CeilDiv与Host CeilDiv对除0/溢出的返回值并不相同，输入约束必须由具体调用层维持。

## 交给Agent的适配与性能验证

先确定上层gate、完整mode tuple、权重NZ与scale/bias表示、q/kv/nope/rope维、cache layout与stride，再逐stage对照FP32参考，覆盖0值、边界slot、padding、1024 token边界、partial core、INNER和no-RoPE。对固定模型先用rank512/RoPE64建立基线，任何扩大范围保持未验证状态直到有目标设备精度证据。

以相同输出/缓存内容对照未融合路径后，才测kernel时间、launch数、workspace/HBM与端到端TTFT/TPOT；warmup、编译和capture单独记录。存在kernel、Host返回成功、配置解析或一次请求成功都不等于所有硬件/模型适配与优化完成。

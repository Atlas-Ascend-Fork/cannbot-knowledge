---
type: Operator
title: "SGL 稀疏 FlashAttention 950 ACLNN 算子知识"
description: "说明 aclnnSglSparseFlashAttention 在950上的公开语义、Host/POD、逐key MIX流水、内存/同步与精度；实际MM2复用K而非独立V，SharedParams及本地地址字段有未初始化读取，索引越界/空KV路径无安全保证，为未经运行验证的draft源码知识。"
tags: [task.implementation, task.lookup, topic.data_movement, topic.memory, topic.precision, topic.programming_model]
status: draft
sources:
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/en/operators/attention/sparse_flash_attention.md
    role: primary
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/README.md
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
    role: supporting
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/CMakeLists.txt
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/operators.cmake
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/cann_ops.cmake
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/domains.cmake
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/aclnn_torch_adapter/aclnn_runtime.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/sparse_flash_attention.py
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/CMakeLists.txt
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/torch_adapter.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_def.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_infer.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_tiling.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_tiling.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/ops_err.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention.cpp
    role: implementation
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention_template_tiling_key.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention_tiling_data.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_common_arch35.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_kernel_mla.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_cube_mla.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_vector_mla.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_kvcache.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/util_regbase.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/buffer_manager.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/buffer.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/buffers_policy.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/matmul.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/FixpipeOut.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/CopyInL1.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/offset_calculator.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/fa_gm_tensor.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/fa_l1_tensor.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/gm_coord.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/gm_layout.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/parser.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/offset_calculator_v2.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_utils.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_aligned128_no_update_sfa.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_aligned128_update_sfa.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned64_no_update_sfa.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned64_update_sfa.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned128_no_update_sfa.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned128_update_sfa.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_mul_sel_softmaxflashv2_cast_nz_sfa.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_flashupdate_new.h
    role: header
  - resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/kernel/util.h
    role: header
created_at: "2026-11-09T08:53:33Z"
updated_at: "2026-11-09T08:53:33Z"
platforms: ["950"]
cann_versions: ["9.1.0"]
---

# SGL 稀疏 FlashAttention 950 ACLNN 算子知识

## 算子速览

| 项目 | 内容 |
|---|---|
| 实际入口 | aclnnSglSparseFlashAttentionGetWorkspaceSize / aclnnSglSparseFlashAttention；SglSparseFlashAttention OpDef |
| 计算语义 | 公开目标为稀疏索引所选的 softmax(scale*(Q512*K512ᵀ+Qrope64*Krope64ᵀ))*V512；当前950实际MM2使用收集K的前512维，独立value形参未绑定Device读取 |
| 输入输出 | FP16/BF16 Q/K/V/RoPE；INT32索引/actual长度/页表；D512+Dr64、KV头1、Q头1..64或128；out同Q，optional max/sum为FP32 |
| 执行类型 | 单sgl_sparse_flash_attention，MIX_AIC_1_2：AIC_CUBE两次矩阵乘；AIV_VECTOR负责聚合、softmax、在线更新、最终cast；950为RegBase VF；无独立SIMT/通信节点 |
| Kernel 路线 | R-001–R-024逐payload key与dtype/G/layout/template展开；原始key低16位与dtype位16分别解析；没有FlashDecode Host producer |
| 核心资源 | 3×128×576×2 B/coreGroup GM cache，512KiB L1 manager实际504KiB，L0与跨核UB+私有UB共220672B |
| 来源闭包 | source_closed：公开API→Python/torch adapter→ACLNN pair→OpDef/Infer→Parser/Checker/Tiling→Host宏序列化/Device显式POD→router→两侧当前body及本地helper/Matmul/VF→CMake闭合；generated bridge与通用SDK指令为边界 |
| 复用风险 | draft。实际MM2复用K而非独立V，SharedParams及本地地址字段有未初始化读取，索引越界/空KV路径无安全保证；下文body为控制流到达且前置字段有效时的符号化分析，不表示全部公开输入正确/安全 |
| 验证状态 | 已完成源码闭包检查；本次知识提取未执行编译、真机、数值或性能测试 |

## 接口与语义

### 计算语义

N2=1，G=N1/N2∈{1..64,128}。对query token s及其G个头，将 sparse_indices[s,0,k]*sparse_block_size 加块内offset展开为选中KV位置；-1表示有效索引前缀终点。公开语义忽略不可见位置；mode0可见长度为actualKV，mode3为右下对齐因果边界actualKV−actualQ+s+1。pre_tokens/next_tokens仅INT64_MAX，不支持自定义窗口。先计算512维NoPE与64维RoPE点积相加，再乘FP32 scale，softmax沿选中的KV行，最后与512维V相乘。无RoPE现场生成、量化scale或额外激活。

在线softmax的数学递推为 m'=max(m,max(score))，alpha=exp(m−m')，l'=alpha*l+sum exp(score−m')，o'=alpha*o+exp(score−m')*V，最后out=o/l。950按此FP32 alpha递推，低精概率送MM2，最终CAST_ROUND。softmax_max与softmax_sum分别保存max和sum，而不是LSE；自然对数LSE为max+log(sum)。950针对mode0且returnSoftmaxLse的全无本地索引行，会先清out/max/sum为0并跳过计算，max0+log(sum0)=−∞。其它全空/哨兵尾块语义须按各body的写入与初始化判断，不把未生产workspace当有效零值。

**公开目标与实际数据源必须分开。** InitGlobalBuffer接收value却只绑定key/keyRope/indices/table；Vec0收集key512+keyRope64为row576；MM2右矩阵取同L1前512维，概率覆盖原rope区域。固定源码没有其它独立V producer。因此任意K!=V的独立V语义不能从这些路线获得正确性保证；没有“调用了value参数所以必然参与MM2”的推论。C/V是同一逻辑算子的实现路线，此处记录源可见缺陷，不另造数学独立算子。

### 输入、输出与属性

| 参数 | shape/layout | dtype | 约束、默认值与语义 |
|---|---|---|---|
| query | BSND[B,S1,G,512] 或 TND[T1,G,512] | FP16/BF16 | NPU；C++ adapter自动contiguous；B>0，TND T1>0；G1..64或128 |
| key | BSND[B,S2,1,512]、TND[T2,1,512]、PA[Bn,Bs,1,512] | 与query相同（公开契约） | 512维NoPE；分页block物理存储 |
| value | 与key同shape | 与query相同 | C++要求必选且非空；native无value=nullptr→key替换；实际MM2数据源按Route限定 |
| sparse_indices | BSND[B,S1,1,K] 或 TND[T1,1,K] | INT32 | 有效非负前缀后跟-1；K为shape末轴；adapter要求numel>0；Host未逐值校验 |
| block_table | PA[B,maxBlocks] | INT32可选 | PA必须存在、2D、第二轴>0；非PA必须None；实际physical ID范围由调用者保证 |
| actual_seq_lengths_query | [B] | INT32可选 | TND必需，是累计结束位置，**不含额外0元素**；BSND可省略用S1，提供时为有效长度 |
| actual_seq_lengths_kv | [B] | INT32可选 | TND为累计结束位置；PA/BSND为每请求有效长度；PA与TND KV必须提供；Host检查shape元素数，不检查设备值单调/范围 |
| query_rope | 与Q存储轴相同，末64 | query dtype | MLA必须提供；Host在设置shape时已解引用，不能将缺失值视为安全fallback |
| key_rope | 与K存储轴相同，末64 | key dtype | 必须提供 |
| scale_value | scalar | Python double→C++ float→POD float32 | softmax之前缩放；未见有限性检查 |
| sparse_block_size | scalar | int64 | 950仅1；PA要求整除Bs |
| layout_query | string | 默认BSND | BSND/TND |
| layout_kv | string | 默认BSND | BSND/TND/PA_BSND；非PA必须与Q布局相同 |
| sparse_mode | scalar | int64，默认3 | 0或3 |
| pre_tokens | scalar | int64，默认INT64_MAX | 必须保持INT64_MAX |
| next_tokens | scalar | int64，默认INT64_MAX | 必须保持INT64_MAX |
| attention_mode | scalar | int64，默认2 | 仅2，MLA分离RoPE |
| return_softmax_lse | scalar | bool，默认false | true输出max/sum；当前native Host没有“PA禁止true”检查，不能继承其它入口版本限制 |
| attention_out | 同Q shape | query dtype | out由at::empty分配，只有实际Device写入/清零过的行有值 |
| softmax_max | BSND[B,1,S1,G] 或 TND[1,T1,G] | FP32 | true有效；false为有1元素storage的narrow空view以保留非空数据指针 |
| softmax_sum | 同max | FP32 | 同上；不是logsumexp成品 |

### 入口与版本

本卡仅覆盖固定kernel repo公开Sgl pair。Python auto/ascendc注册到torch.ops.npu.sparse_flash_attention，不可用即报错；torch_native为另一个PyTorch实现，不是native失败fallback，未执行。现有[同源API](../../../../apis/sgl_kernel_npu/sgl_sparse_flash_attention.md)描述公开契约；[另一公开入口A2/A3实现](../../../../../../ops/ascendc/operators/aclnn/transformer/attention/sparse_flash_attention.md)和[其950实现](../../../../../../ops/ascendc/operators/aclnn/transformer/attention/sparse_flash_attention_950.md)属于ops-transformer固定源的aclnnSparseFlashAttention，不能把value空替换、临时TensorHolder、旧POD宏缺失或PA返回限制搬入本Sgl入口。

公开EN API表列arch22(2201)、arch35(3510) ascendc Supported；python README与architectures.json将2201对应ascend910b/ascend910_93（A2/A3），3510对应ascend950。CMake SUPPORTED_ARCHS2201/3510与真实Host/Device同向。CANN9.1.0来自固定README/CI镜像；本任务未实际运行任何版本。legacy csrc/sparse_flash_attention保持不改，native构建使用csrc/attention/sparse_flash_attention的当前复制实现与局部框架适配；只以active include/selector为来源。

## Host/Launcher 执行流程

### 参数校验与前处理

Python原样分发。C++先对所有tensor/optional做contiguous，随后拒Q/K/V/indices numel0，检查indices与metadata INT32，Q/K/V dtype一致、RoPE与对应Q/K dtype一致，逐tensor同设备/连续。MakeOutputs要求Q为NPU FP16/BF16、layout_query BSND/TND及对应rank；分配out同Q、LSE按Q/K头数构造，false时分配一元素storage再narrow长度0。DeviceGuard覆盖输出/descriptor/query/execute过程。输入CPU或错误dtype/shape为TORCH_CHECK，无后继kernel。

Host TilingSglSparseFlashAttention检查context/platform后：Parser::Parse按GetOpName→GetNpuInfo→GetOpParaInfo→required存在→dtype/layout→SetSFAShape→N1/N2/G/B/T/S/D/PA信息→actual-shape信息→GenerateInfo；Checker::Process按单参数→存在/RoPE→feature→多参数shape/dtype/输出/actual/table；之后DoOpTiling。支持NpuArch DAV_2201/DAV_3510；PA Bs∈(0,1024]、%16==0且%sparseBlockSize==0；G域1..64或128，KV头1，D512/Dr64。actual长度仅检查dtype及shape元素数==B，不读取索引/长度设备值。缺省按静态S，TND读取前缀差。

Parser required只列部分attrs，对pre/next/attentionMode/return等后续解引用依赖OpDef默认补全；不应据此推导手造缺失描述符/属性的raw ACLNN调用一定安全失败。OpDef/Infer与CANN generated bridge是框架接线边界，当前owned Host检查不足不会由猜测的框架行为补齐。

### 参数、Workspace 与生命周期

adapter构造所有aclTensor共享descriptor，静态加载query/execute符号，layout字符串以可写std::string.data交给generated签名。query失败TORCH_CHECK，workspaceSize≤INT64_MAX后at::empty Byte分配（**没有Compressor的zeros行为**）。当前stream record_stream输入、临时contiguous副本、输出、workspace、optional；lambda捕获tensor集合、descriptor集合、布局字符串、workspace、executor与stream，保证延迟Host任务期间存储。execute失败TORCH_CHECK；executor生命周期为CANN框架边界，无本仓手写复用/销毁。

Host内部GetWorkspaceSize已经包含libapiSize；外层TilingSglSparseFlashAttention仍令 workspace[0]=platform.GetLibApiWorkSpaceSize()+tiling.GetWorkspaceSizeBytes()，因此当前公开query预算是**2*libapiSize+operator user预算**。entry的GetUserWorkspace移除一份系统前缀；多出的libapi字节是保守闲置尾部，不能误写为Device额外计算slice。Device user offsets见各代下节。POD用SaveToBuffer序列化并设置raw data size；Device获取同一GM地址，950 AIV另复制完整144B到本地，AIC只从SSBUF读取其AIV发布的CVSharedParams。

### 启动图与失败传播

一个AICORE CANN注册节点：Host Parse/Check/Tiling→POD、workspace、CalcTschBlockDim(2*usedAIC,usedAIC,2*usedAIC)→sgl_sparse_flash_attention，KERNEL_TYPE_MIX_AIC_1_2。没有SplitKV/FlashDecode额外launch；splitKVFlag初始false且无置true producer。Host任何GRAPH_FAILED/GRAPH_PARAM_INVALID在adapter query失败终止；execute返回失败立即终止，没有后继算子自动补算。

```text
Host query -> Infer/Parser/Checker -> InitParams/Split/Fill/Workspace/Key
 -> outer CANN key0 + baseParams.dispatchKey
 -> one MIX entry
    2201: SparseFlashAttentionMla<SFAType<...>>::Init/Process
    3510: SparseFlashAttentionKernelMla<CubeService-or-Dummy,VectorService-or-Dummy>
      AIV publishes SharedParams to SSBUF and flag15(mode4 PIPE_S)
      AIC waits and copies SharedParams; same launch body stages
unknown low16 dispatch key: default break => no output writer/no Trap
```

## Route 与参数设计

### 分核与资源计算

Parser根据BSND/TND/PA读取原始轴；TND B=actualQ.shape元素数、qSeqSize=T1、seqSize=T2；PA seqSize=maxBlocks*Bs（容量，不是实际KV）。Host InitParams先用**原始**S2与sparseBlockSize选择V1/C0，再ZeroTensorProcess将S2=0改写1024（注释“kernel使用真实0”与实际POD赋值冲突）；其后CalcInnerSize sInner=min(改写后S2,512)，align32；splitKVFlag=false，FD分支不命中。

Mcap=min(G*S1,128)，M16=align16(Mcap)，mmRes=S2a*M16，bmm2Res=512*M16，qPreProc字节0。Host inner.mBaseSize=G，inner.s2BaseSize=sInner，usedCoreNum=AIC数。A2 Device按actualQ总token数均衡分query基本任务（每任务G行），无任务core退出；每个AIC配两个AIV按M的16行边界分半，G≤16时第二AIV可0行。950忽略Host inner tile定64行M/128列S2，G128用相邻AIC各64头并共享cache，coreNum/2参与分query；两AIV各约M/2行，Vec0按S2二段或splitG四段。

950 GetWorkspaceSize内部=libapiSize+3*128*576*2*AICeff，其中AICeff=G128?floor(AIC/2):AIC；外层再加libapiSize，最终2*libapiSize+442368*AICeff。Device GM按coreGroup*442368+taskSlot*147456切三槽row576。L1 manager512KiB，right三槽各144KiB、Q72KiB共504KiB，余8KiB未分配。right每槽前128*512*2=128KiB为K、后128*64*2=16KiB为RoPE，MM1后后者alias为≤64*128*2的P。crossUB manager96KiB，先bmm2 64KiB@0，再bmm1两16KiB@64KiB/80KiB；各AIV私有122368B，合计220672B。L0A/B manager各64KiB，A的DB只占2*16KiB，B2*32KiB，C manager/DB256KiB。无Host容量检查替代这些字节账。

### Route 选择

| 顺序 | Route | Key/模板 | 精确选择条件与优先级 | 不适用去向 |
|---:|---|---|---|---|
| 1 | R-001 SWA数值0空KV BSND/BSND FP16 G1..64 | payload0，low16=0，mode0，split0 | raw原S2=0、block1、非PA；Torch拒空；Q=BSND，KV=BSND，FP16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 2 | R-002 SWA数值0空KV BSND/BSND FP16 G128 | payload16384，low16=16384，mode0，split1 | raw原S2=0、block1、非PA；Torch拒空；Q=BSND，KV=BSND，FP16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 3 | R-003 SWA数值0空KV BSND/BSND BF16 G1..64 | payload65536，low16=0，mode0，split0 | raw原S2=0、block1、非PA；Torch拒空；Q=BSND，KV=BSND，BF16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 4 | R-004 SWA数值0空KV BSND/BSND BF16 G128 | payload81920，low16=16384，mode0，split1 | raw原S2=0、block1、非PA；Torch拒空；Q=BSND，KV=BSND，BF16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 5 | R-005 SWA数值0空KV TND/TND FP16 G1..64 | payload68，low16=68，mode0，split0 | raw原S2=0、block1、非PA；Torch拒空；Q=TND，KV=TND，FP16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 6 | R-006 SWA数值0空KV TND/TND FP16 G128 | payload16452，low16=16452，mode0，split1 | raw原S2=0、block1、非PA；Torch拒空；Q=TND，KV=TND，FP16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 7 | R-007 SWA数值0空KV TND/TND BF16 G1..64 | payload65604，low16=68，mode0，split0 | raw原S2=0、block1、非PA；Torch拒空；Q=TND，KV=TND，BF16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 8 | R-008 SWA数值0空KV TND/TND BF16 G128 | payload81988，low16=16452，mode0，split1 | raw原S2=0、block1、非PA；Torch拒空；Q=TND，KV=TND，BF16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 9 | R-009 CFA BSND/BSND FP16 G1..64 | payload1024，low16=1024，mode1，split0 | 原S2>0，block1；Q=BSND，KV=BSND，FP16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 10 | R-010 CFA BSND/BSND FP16 G128 | payload17408，low16=17408，mode1，split1 | 原S2>0，block1；Q=BSND，KV=BSND，FP16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 11 | R-011 CFA BSND/BSND BF16 G1..64 | payload66560，low16=1024，mode1，split0 | 原S2>0，block1；Q=BSND，KV=BSND，BF16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 12 | R-012 CFA BSND/BSND BF16 G128 | payload82944，low16=17408，mode1，split1 | 原S2>0，block1；Q=BSND，KV=BSND，BF16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 13 | R-013 CFA BSND/PA_BSND FP16 G1..64 | payload1154，low16=1154，mode1，split0 | 原S2>0，block1；Q=BSND，KV=PA_BSND，FP16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 14 | R-014 CFA BSND/PA_BSND FP16 G128 | payload17538，low16=17538，mode1，split1 | 原S2>0，block1；Q=BSND，KV=PA_BSND，FP16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 15 | R-015 CFA BSND/PA_BSND BF16 G1..64 | payload66690，low16=1154，mode1，split0 | 原S2>0，block1；Q=BSND，KV=PA_BSND，BF16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 16 | R-016 CFA BSND/PA_BSND BF16 G128 | payload83074，low16=17538，mode1，split1 | 原S2>0，block1；Q=BSND，KV=PA_BSND，BF16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 17 | R-017 CFA TND/TND FP16 G1..64 | payload1092，low16=1092，mode1，split0 | 原S2>0，block1；Q=TND，KV=TND，FP16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 18 | R-018 CFA TND/TND FP16 G128 | payload17476，low16=17476，mode1，split1 | 原S2>0，block1；Q=TND，KV=TND，FP16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 19 | R-019 CFA TND/TND BF16 G1..64 | payload66628，low16=1092，mode1，split0 | 原S2>0，block1；Q=TND，KV=TND，BF16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 20 | R-020 CFA TND/TND BF16 G128 | payload83012，low16=17476，mode1，split1 | 原S2>0，block1；Q=TND，KV=TND，BF16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 21 | R-021 CFA TND/PA_BSND FP16 G1..64 | payload1158，low16=1158，mode1，split0 | 原S2>0，block1；Q=TND，KV=PA_BSND，FP16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 22 | R-022 CFA TND/PA_BSND FP16 G128 | payload17542，low16=17542，mode1，split1 | 原S2>0，block1；Q=TND，KV=PA_BSND，FP16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 23 | R-023 CFA TND/PA_BSND BF16 G1..64 | payload66694，low16=1158，mode1，split0 | 原S2>0，block1；Q=TND，KV=PA_BSND，BF16，G1..64；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |
| 24 | R-024 CFA TND/PA_BSND BF16 G128 | payload83078，low16=17542，mode1，split1 | 原S2>0，block1；Q=TND，KV=PA_BSND，BF16，G128；全局checks已通过 | 其他tuple继续；不支持Host失败；unknown key entry break |

```text
all Host interface/shape/platform checks pass
mode = (originalS2!=0 && sparse_block_size<=4) ? 1 : 0
if originalS2==0: info.S2=1024  # chosen mode remains0
page = KVlayout==PA_BSND
base = (BSND/BSND:0, BSND/PA:130, TND/TND:68, TND/PA:134)
splitG = G>64  # public admitted value only128
payload = base | mode<<10 | splitG<<14 | (Q_BF16?1<<16:0)
outer CANN key=0; router reads low16 and dtype16 separately
```

A2的splitG位未传给SFAType，仍逐key列明G128的实际M域；950将其传给service模板，改变配对核、共享workspace与flag15平衡。raw ACLNN可能绕过Torch非空限制：当前Host未检查BSND S1>0或S2>0，因此列出源可见的零容量路径；不等同公开推荐输入或运行安全。特别950 mode0只可能来自原S2=0（sparseBlockSize已被限定1），其body仍可追溯，不能隐去或把它声称正常CFA保证。

### 模板/实现执行矩阵

| Route | key/selector | dtype/shape/platform 完整命中条件 | 执行族与 kernel 节点 | 实际模板/body | 内存与同步特征 | tail/fallback |
|---|---|---|---|---|---|---|
| R-001 | 0 | 950，SWA数值0空KV BSND/BSND FP16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA0,Q0,KV0,template0,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；raw零KV不安全；VF六子selector见下文 |
| R-002 | 16384 | 950，SWA数值0空KV BSND/BSND FP16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA0,Q0,KV0,template0,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；raw零KV不安全；VF六子selector见下文 |
| R-003 | 65536 | 950，SWA数值0空KV BSND/BSND BF16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA0,Q0,KV0,template0,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；raw零KV不安全；VF六子selector见下文 |
| R-004 | 81920 | 950，SWA数值0空KV BSND/BSND BF16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA0,Q0,KV0,template0,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；raw零KV不安全；VF六子selector见下文 |
| R-005 | 68 | 950，SWA数值0空KV TND/TND FP16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA0,Q1,KV1,template0,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；raw零KV不安全；VF六子selector见下文 |
| R-006 | 16452 | 950，SWA数值0空KV TND/TND FP16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA0,Q1,KV1,template0,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；raw零KV不安全；VF六子selector见下文 |
| R-007 | 65604 | 950，SWA数值0空KV TND/TND BF16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA0,Q1,KV1,template0,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；raw零KV不安全；VF六子selector见下文 |
| R-008 | 81988 | 950，SWA数值0空KV TND/TND BF16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA0,Q1,KV1,template0,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；raw零KV不安全；VF六子selector见下文 |
| R-009 | 1024 | 950，CFA BSND/BSND FP16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA0,Q0,KV0,template1,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-010 | 17408 | 950，CFA BSND/BSND FP16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA0,Q0,KV0,template1,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-011 | 66560 | 950，CFA BSND/BSND BF16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA0,Q0,KV0,template1,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-012 | 82944 | 950，CFA BSND/BSND BF16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA0,Q0,KV0,template1,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-013 | 1154 | 950，CFA BSND/PA_BSND FP16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA1,Q0,KV2,template1,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-014 | 17538 | 950，CFA BSND/PA_BSND FP16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA1,Q0,KV2,template1,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-015 | 66690 | 950，CFA BSND/PA_BSND BF16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA1,Q0,KV2,template1,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-016 | 83074 | 950，CFA BSND/PA_BSND BF16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA1,Q0,KV2,template1,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-017 | 1092 | 950，CFA TND/TND FP16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA0,Q1,KV1,template1,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-018 | 17476 | 950，CFA TND/TND FP16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA0,Q1,KV1,template1,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-019 | 66628 | 950，CFA TND/TND BF16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA0,Q1,KV1,template1,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-020 | 83012 | 950，CFA TND/TND BF16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA0,Q1,KV1,template1,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-021 | 1158 | 950，CFA TND/PA_BSND FP16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA1,Q1,KV2,template1,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-022 | 17542 | 950，CFA TND/PA_BSND FP16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<half,same,float,same,false,PA1,Q1,KV2,template1,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-023 | 66694 | 950，CFA TND/PA_BSND BF16 G1..64；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA1,Q1,KV2,template1,split0>,对应VecService> | GM三cache，L1 rope→P复用，UB交接 | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |
| R-024 | 83078 | 950，CFA TND/PA_BSND BF16 G128；D512/Dr64/N2=1，mode0/3，窗口INT64_MAX，PA guard及全局域 | 单sgl_sparse_flash_attention MIX_CV，AIV Vec0→AIC MM1→AIV V1→AIC MM2→AIV V2 | KernelMla<SFAMatmulService<bf16,same,float,same,false,PA1,Q1,KV2,template1,split1>,对应VecService> | GM三cache，L1 rope→P复用，UB交接，邻AIC共享cache | actualQ/S2与索引mask；无FD fallback；VF六子selector见下文 |

950每条Route另展开S2 VF子selector：第一次S2块isUpdate=false，后续true；s2Real=128、0<s2Real≤64、64<s2Real<128三种范围，分别映射aligned128、unaligned64、unaligned128的no_update/update六body。isFd=false、fullQuant=false，FP8/INT8 helper未实例化；没有偷偷合入量化算子。

### 隐藏性能 Guard

| Guard | Host/Tiling 条件 | Device/资源原因 | 影响 Route | 不满足时去向 | 源码符号 |
|---|---|---|---|---|---|
| D/Dr/G | D512，Dr64，KV头1，G1..64或128 | 手写576宽投影、512输出、至多128头 | 全部 | Host失败 | CheckFeatureMlaNoQuantShape |
| SFA block | 1..128幂二；950仅1 | C直接拷块或V聚合；950只处理token索引 | 全部 | Host失败 | CheckSingleParaSparseBlockSize |
| C/V | 原S2!=0 && block<=4→1；否则0 | 小块先AIV收集；大块AIC直接取 | 全部 | 另一模板；zero KV保留风险 | InitParams/ZeroTensorProcess |
| PA | Bs正且≤1024、16对齐、整除block；table/actualKV必选 | physical页映射和页尾分段 | PA Route | Host失败 | GetMaxBlockNumPerBatch/CheckFeatureMlaNoquantPa |
| 合并DMA | pair源stride在[0,INT32_MAX)，A2另检查整块不越visible边界 | blockCount2两位置批量搬运 | V/CFA | 两次CopyInSingleKv | CopyInKv/CopyInKvSparse |
| Gsplit | G>64只对应128 | 950邻AIC各64头、共享3cache；A2仅key变化 | split1 Route | split0 | GenTilingKey/CalSparseCalSize |
| 固定片上资源 | L1 manager512KiB/used504KiB；L0A64/B64/C256KiB；AIV220672B | 右矩阵三拍、Q驻留、UB直交接与私有VF/在线输出 | 所有非空实际任务 | 本仓没有更小tile资源fallback | InitBuffers/InitMMResBuf/InitLocalBuffer |
| VF范围 | s2Real==128 / ≤64 / 64..127；first/update | tail mask与在线max/sum的真实specialization | 950 | 对应另VF，s2Real0应跳计算 | ProcessVec1Vf |
| 原始空KV | Torch拒key/value numel0；Host没有S2>0检查 | zero→1024与GM实际空容量冲突 | mode0原S2=0 | 无安全fallback；draft源码终点 | MakeOutputs/InitParams/ZeroTensorProcess |
| 未知key | 非4个base加mode/split组合 | switch没有default computation | 全部 | default break，无写输出 | sgl_sparse_flash_attention |

### POD/ABI

Device显式alignas(8)POD是本仓可见真实结构，含size static_assert；Host tiling.h仍使用CANN宏定义setter/SaveToBuffer。Host宏实现属于框架ABI边界，本次未编译测量其buffer；下表Device offset按声明的uint64/int64对齐8静态推导，不能把框架序列化自动声称本次ABI实测。Base sizeof104/align8、SplitKV16/align8、SingleCore8/align8、TensorSize8/align8、Inner8/align8、整体144/align8。Host setter顺序与Device字段顺序一致；dispatchKey新字段不能丢。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| SparseFlashAttentionBaseParamsMla | batchSize | uint32/32 | offsetof=0 | batch | FillTilingBaseParamsMla: bSize | actual请求循环 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | seqSize | uint32/32 | offsetof=4 | token容量 | FillTilingBaseParamsMla: s2Size（zero时已改1024） | kvSeqSize/shared.s2Size | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | qSeqSize | uint32/32 | offsetof=8 | token容量 | FillTilingBaseParamsMla: s1Size，TND为T1 | Q/输出pitch | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | blockSize | int64/64 | offsetof=16 | token/page | FillTilingBaseParamsMla: key.dim1(Bs)，非PA0 | PA地址/页尾 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | maxBlockNumPerBatch | uint32/32 | offsetof=24 | 页表列 | FillTilingBaseParamsMla: table.dim1，非PA0 | page表pitch | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | scaleValue | float/32 | offsetof=28 | 标量 | FillTilingBaseParamsMla: float attr | A2 ElewiseCompute/950 softmaxScale | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | nNumOfQInOneGroup | uint32/32 | offsetof=32 | head | FillTilingBaseParamsMla: N1/N2 | G行数/分核 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | actualLenDimsQ | uint32/32 | offsetof=36 | metadata元素 | FillTilingBaseParamsMla: actualQ.shapeSize或0 | A2绑定GM长度；950兼容 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | actualLenDimsKV | uint32/32 | offsetof=40 | metadata元素 | FillTilingBaseParamsMla: actualKV.shapeSize或0 | A2绑定GM长度；950兼容 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | outputLayout | uint32/32 | offsetof=44 | enum | FillTilingBaseParamsMla: outLayout0BSND/1TND | 输出地址/shared.layoutType | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | sparseMode | uint32/32 | offsetof=48 | enum | FillTilingBaseParamsMla: attr0/3 | visible threshold | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | preTokens | int64/64 | offsetof=56 | token | FillTilingBaseParamsMla: attr INT64_MAX | A2常量元数据；950窗口常量自行赋 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | nextTokens | int64/64 | offsetof=64 | token | FillTilingBaseParamsMla: attr INT64_MAX | 同上 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | attentionMode | uint32/32 | offsetof=72 | enum | FillTilingBaseParamsMla: attr2 | MLA常量元数据 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | returnSoftmaxLse | uint32/32 | offsetof=76 | bool flag | FillTilingBaseParamsMla: attr bool | max/sum写guard/950mode0前缀裁剪 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | sparseBlockSize | int64/64 | offsetof=80 | token/index | FillTilingBaseParamsMla: attr block | A2索引展开；950固定1 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | sparseBlockCount | uint32/32 | offsetof=88 | index槽 | FillTilingBaseParamsMla: indices末轴 | 稀疏循环/前缀容量 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | isActualLenDimsNull | uint32/32 | offsetof=92 | bool flag | FillTilingBaseParamsMla: actualQ tensor ?0:1 | 950缺省长度路径；A2实际看dims | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | isActualLenDimsKVNull | uint32/32 | offsetof=96 | bool flag | FillTilingBaseParamsMla: actualKV tensor ?0:1 | 950缺省KV路径 | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionBaseParamsMla | dispatchKey | uint32/32 | offsetof=100 | bitfield | FillTilingBaseParamsMla: DoOpTiling:低16 key | BF16<<16 | entry完整dispatch | 顶层base+0；公开shape/attr域；字段窄化见限制 |
| SparseFlashAttentionSplitKVParamsMla | s2 | uint32/32 | offsetof=0 | 份数 | FillTilingSplitKVMla: splitKVFlag=false→0 | FD消费者inactive | 顶层104+本偏移；必须保留0，不生成FD route |
| SparseFlashAttentionSplitKVParamsMla | accumOutSize | uint32/32 | offsetof=4 | FP32元素 | FillTilingSplitKVMla: AIC*2*N2*128*512 | 仅FD分支 | 顶层104+本偏移；非零预算字段但FD不读 |
| SparseFlashAttentionSplitKVParamsMla | logSumExpSize | uint32/32 | offsetof=8 | FP32元素 | FillTilingSplitKVMla: 2*AIC*2*N2*128*(32/4) | 仅FD分支 | 顶层104+本偏移；同上 |
| SparseFlashAttentionSingleCoreParamsMla | usedCoreNum | uint32/32 | offsetof=0 | AIC core | FillTilingSingleCoreParamsMla: AIC | Init/actualQ总任务减少active数 | 顶层120，尾pad4 |
| SparseFlashAttentionSingleCoreTensorSizeMla | mmResUbSize | uint32/32 | offsetof=0 | 元素 | CalcUbBmm→FillTiling: S2a*align16(min(G*S1,128)) | arch22 mm1/prob WS | 顶层128；950不依它分配当前buffer |
| SparseFlashAttentionSingleCoreTensorSizeMla | bmm2ResUbSize | uint32/32 | offsetof=4 | 元素 | CalcUbBmm→FillTiling: 512*align16(min(G*S1,128)) | arch22 mm2 WS | 顶层128；950不依它分配当前buffer |
| SparseFlashAttentionInnerSplitParams | mBaseSize | uint32/32 | offsetof=0 | 行/token | SplitBalanced: G | arch22每query任务G行 | 顶层136；950当前固定M64/S2=128 |
| SparseFlashAttentionInnerSplitParams | s2BaseSize | uint32/32 | offsetof=4 | 行/token | SplitBalanced: min(改写S2,512) | arch22稀疏S2 tile | 顶层136；950当前固定M64/S2=128 |
| SparseFlashAttentionTilingDataMla | baseParams | SparseFlashAttentionBaseParamsMla | offsetof=0 | 嵌套字节 | FillTiling/DoOpTiling | entry与Init | extent=104；顶层144/align8，raw capacity≥Host GetDataSize |
| SparseFlashAttentionTilingDataMla | splitKVParams | SparseFlashAttentionSplitKVParamsMla | offsetof=104 | 嵌套字节 | FillTiling/DoOpTiling | entry与Init | extent=16；顶层144/align8，raw capacity≥Host GetDataSize |
| SparseFlashAttentionTilingDataMla | singleCoreParams | SparseFlashAttentionSingleCoreParamsMla | offsetof=120 | 嵌套字节 | FillTiling/DoOpTiling | entry与Init | extent=8；顶层144/align8，raw capacity≥Host GetDataSize |
| SparseFlashAttentionTilingDataMla | singleCoreTensorSize | SparseFlashAttentionSingleCoreTensorSizeMla | offsetof=128 | 嵌套字节 | FillTiling/DoOpTiling | entry与Init | extent=8；顶层144/align8，raw capacity≥Host GetDataSize |
| SparseFlashAttentionTilingDataMla | innerSplitParams | SparseFlashAttentionInnerSplitParams | offsetof=136 | 嵌套字节 | FillTiling/DoOpTiling | entry与Init | extent=8；顶层144/align8，raw capacity≥Host GetDataSize |

950另有AIV→SSBUF→AIC共享ABI（不是Host POD）：kernel成员sharedParams没有{}初始化；逐字段producer如下。两个端由同一Device TU定义解释，但bitfield跨基础类型的具体packing由编译器决定，不能编造offsetof。发布按sizeof(CVSharedParams)/4逐uint32写SSBUF0，再mode4 PIPE_S flag15；AIC等待后同样word copy。padding/未写字段不能当成0。

| 结构 | 字段 | 类型/位宽 | ABI 布局 | 单位 | Host/launcher producer | Device consumer | 边界 |
|---|---|---|---|---|---|---|---|
| CVSharedParams | s1BaseSize | uint32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 未赋值 | AIV本地及AIC SSBUF副本：当前ConstInfo预置64，不读此字段 | inactive |
| CVSharedParams | s2BaseSize | uint32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 未赋值 | AIV本地及AIC SSBUF副本：当前ConstInfo预置128，不读此字段 | inactive |
| CVSharedParams | bSize | uint32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: base.batchSize | AIV本地及AIC SSBUF副本：batch循环 | B |
| CVSharedParams | n2Size | uint32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 1 | AIV本地及AIC SSBUF副本：head固定 | 1 |
| CVSharedParams | gSize | uint32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: base.nNumOfQInOneGroup | AIV本地及AIC SSBUF副本：分G/输出地址 | 1..64或128 |
| CVSharedParams | s1Size | uint32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: base.qSeqSize | AIV本地及AIC SSBUF副本：Q容量/packedT | 字段窄化 |
| CVSharedParams | s2Size | uint32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: base.seqSize | AIV本地及AIC SSBUF副本：KV容量 | zero可能已改1024 |
| CVSharedParams | dSize | uint32 bitfield/10 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 512 | AIV本地及AIC SSBUF副本：ComputeConstexpr/Matmul K | 512 |
| CVSharedParams | dSizeVInput | int64 bitfield/12 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 512 | AIV本地及AIC SSBUF副本：ComputeConstexpr | 512 |
| CVSharedParams | needInit | uint32 bitfield/4 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: returnLSE&&mode0，或任batch S1>S2/BSND actualQ<staticS1 | AIV本地及AIC SSBUF副本：CleanOutput/SyncAll | 0/1 |
| CVSharedParams | layoutType | uint32 bitfield/4 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: base.outputLayout | AIV本地及AIC SSBUF副本：ConstInfo布局 | 0/1 |
| CVSharedParams | isActualSeqLengthsNull | uint32 bitfield/1 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: base.isActualLenDimsNull | AIV本地及AIC SSBUF副本：defaultQ | 0/1 |
| CVSharedParams | isActualSeqLengthsKVNull | uint32 bitfield/1 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: base.isActualLenDimsKVNull | AIV本地及AIC SSBUF副本：defaultKV | 0/1 |
| CVSharedParams | sparseBlockCount | uint32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: base.sparseBlockCount | AIV本地及AIC SSBUF副本：sparse循环 | K |
| CVSharedParams | softmaxScale | float/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: base.scaleValue | AIV本地及AIC SSBUF副本：VF缩放 | 未限finite |
| CVSharedParams | cmpRatio | uint32 bitfield/9 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 1 | AIV本地及AIC SSBUF副本：ComputeConstexpr | 不压缩 |
| CVSharedParams | dSizeRope | uint32 bitfield/11 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 64 | AIV本地及AIC SSBUF副本：字段携带；ConstInfo硬编码64 | 64 |
| CVSharedParams | oriMaskMode | uint32 bitfield/6 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: base.sparseMode | AIV本地及AIC SSBUF副本：mode0/3 | 0/3 |
| CVSharedParams | cmpMaskMode | uint32 bitfield/6 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 未赋值 | AIV本地及AIC SSBUF副本：未命中compressed路径 | inactive |
| CVSharedParams | oriWinLeft | int32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: −1 | AIV本地及AIC SSBUF副本：ComputeConstexpr | 固定 |
| CVSharedParams | oriWinRight | int32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 0 | AIV本地及AIC SSBUF副本：ComputeConstexpr | 固定 |
| CVSharedParams | tileSize | uint32 bitfield/8 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 未见赋值 | AIV本地及AIC SSBUF副本：ComputeConstexpr读sharedParams.tileSize | source-visible未初始化读取；不推定值 |
| CVSharedParams | oriBlockSize | uint32 bitfield/12 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: isPa时base.blockSize | AIV本地及AIC SSBUF副本：GetkeyOffset/CalSparse | 非PA不消费 |
| CVSharedParams | cmpBlockSize | uint32 bitfield/12 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 未赋值 | AIV本地及AIC SSBUF副本：当前非compressed分支不读 | inactive |
| CVSharedParams | oriMaxBlockNumPerBatch | uint32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: isPa时base.maxBlockNumPerBatch | AIV本地及AIC SSBUF副本：PA表pitch | 非PA不读 |
| CVSharedParams | cmpMaxBlockNumPerBatch | uint32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: 未赋值 | AIV本地及AIC SSBUF副本：当前compressed路径不读 | inactive |
| CVSharedParams | usedCoreNum | uint32/32 | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: singleCore.usedCoreNum | AIV本地及AIC SSBUF副本：actualQ分核 | AIC数量 |
| CVSharedParams | returnSoftmaxLse | bool | 混合bitfield ABI实现相关，固定源码未给sizeof/数值offset/align保证 | 业务标量 | InitCubeVecSharedParams: base.returnSoftmaxLse | AIV本地及AIC SSBUF副本：max/sum与mode0 prefix裁剪 | bool |

### Route 源码闭包

| Route | Key/selector | Host/Tiling producer | POD/参数 | Kernel entry/router | Kernel body/直接依赖 | 构建接线 |
|---|---|---|---|---|---|---|
| R-001 | payload0 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(0)→Run<0,0,0,0,0,0,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-002 | payload16384 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(0)→Run<0,0,0,0,0,1,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-003 | payload65536 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(0)→Run<0,0,0,0,0,0,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-004 | payload81920 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(0)→Run<0,0,0,0,0,1,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-005 | payload68 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(68)→Run<0,0,1,1,0,0,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-006 | payload16452 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(68)→Run<0,0,1,1,0,1,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-007 | payload65604 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(68)→Run<0,0,1,1,0,0,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-008 | payload81988 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(68)→Run<0,0,1,1,0,1,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-009 | payload1024 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(0)→Run<0,0,0,0,1,0,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-010 | payload17408 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(0)→Run<0,0,0,0,1,1,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-011 | payload66560 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(0)→Run<0,0,0,0,1,0,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-012 | payload82944 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(0)→Run<0,0,0,0,1,1,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-013 | payload1154 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(130)→Run<0,1,0,2,1,0,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-014 | payload17538 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(130)→Run<0,1,0,2,1,1,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-015 | payload66690 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(130)→Run<0,1,0,2,1,0,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-016 | payload83074 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(130)→Run<0,1,0,2,1,1,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-017 | payload1092 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(68)→Run<0,0,1,1,1,0,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-018 | payload17476 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(68)→Run<0,0,1,1,1,1,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-019 | payload66628 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(68)→Run<0,0,1,1,1,0,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-020 | payload83012 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(68)→Run<0,0,1,1,1,1,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-021 | payload1158 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(134)→Run<0,1,1,2,1,0,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-022 | payload17542 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(134)→Run<0,1,1,2,1,1,false> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-023 | payload66694 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(134)→Run<0,1,1,2,1,0,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |
| R-024 | payload83078 | SFAInfoParser/SFATilingCheck→SFAMlaTiling::DoOpTiling/InitParams/GenTilingKey | Host tiling.h setter→Device tiling_data.h 144B；AIV CVSharedParams→SSBUF→AIC | sparse_flash_attention.cpp SFA_CASE(134)→Run<0,1,1,2,1,1,true> | arch35/kernel_mla/service_cube_mla/service_vector_mla；kvcache/util_regbase+common MatmulK/N/buffer/memcopy/六VF | CMakeLists ID sparse_flash_attention，ARCH3510，common+utils/kernel include，auto-sync off/VF membar保留 |

## Kernel 实现

### 公共执行流程

entry9输入顺序query,key,value,sparseIndices,blocktable,actualSeqQ,actualSeqKV,queryRope,keyRope，随后attentionOut,softmaxMax,softmaxSum,workspace,tiling。payload低16四布局base+mode/split，位16为BF16；Q/K/输出类型均按此dtype实例化。AIC pass选择真实Cube/VectorDummy并不接收本地tiling指针，AIV pass选择CubeDummy/真实Vector并逐uint32复制144B；AIV subblock0发布CVSharedParams到SSBUF0，AIC mode4 PIPE_S wait15后复制。未初始化共享字段的C++读构成静态风险终点，后续段落只保留字段有效时的符号化body。本卡无外部自有核心算子调用；手写Mmad/本地MatmulK/N与六VF body可见。AscendC DataCopy/ND2NZ/LoadData/Mmad/Fixpipe/Vector/MicroAPI、CANN executor/生成bridge是标注的通用原语边界，不以此跳过本算子的地址、资源、同步或tail分析。


### Route R-001：SWA数值0空KV BSND/BSND FP16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；Q=BSND，KV=BSND，FP16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=0（低16=0，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(0)/RunSparseFlashAttention | 低16=0+0*1024+0*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::SWA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,0,0,0,0,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=b*S2+logical；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；payload0 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,0,0,0,0,false> | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::SWA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-002：SWA数值0空KV BSND/BSND FP16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；Q=BSND，KV=BSND，FP16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=16384（低16=16384，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(0)/RunSparseFlashAttention | 低16=0+0*1024+1*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::SWA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,0,0,0,1,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=b*S2+logical；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；payload16384 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,0,0,0,1,false> | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::SWA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-003：SWA数值0空KV BSND/BSND BF16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；Q=BSND，KV=BSND，BF16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=65536（低16=0，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(0)/RunSparseFlashAttention | 低16=0+0*1024+0*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::SWA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,0,0,0,0,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=b*S2+logical；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；payload65536 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,0,0,0,0,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::SWA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-004：SWA数值0空KV BSND/BSND BF16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；Q=BSND，KV=BSND，BF16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=81920（低16=16384，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(0)/RunSparseFlashAttention | 低16=0+0*1024+1*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::SWA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,0,0,0,1,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=b*S2+logical；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；payload81920 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,0,0,0,1,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::SWA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-005：SWA数值0空KV TND/TND FP16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；Q=TND，KV=TND，FP16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=68（低16=68，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(68)/RunSparseFlashAttention | 低16=68+0*1024+0*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::SWA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,1,1,0,0,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=(b?actualKV[b-1]:0)+logical；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；payload68 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,1,1,0,0,false> | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::SWA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-006：SWA数值0空KV TND/TND FP16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；Q=TND，KV=TND，FP16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=16452（低16=16452，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(68)/RunSparseFlashAttention | 低16=68+0*1024+1*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::SWA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,1,1,0,1,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=(b?actualKV[b-1]:0)+logical；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；payload16452 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,1,1,0,1,false> | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::SWA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-007：SWA数值0空KV TND/TND BF16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；Q=TND，KV=TND，BF16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=65604（低16=68，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(68)/RunSparseFlashAttention | 低16=68+0*1024+0*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::SWA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,1,1,0,0,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=(b?actualKV[b-1]:0)+logical；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；payload65604 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,1,1,0,0,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::SWA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-008：SWA数值0空KV TND/TND BF16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；Q=TND，KV=TND，BF16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=81988（低16=16452，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(68)/RunSparseFlashAttention | 低16=68+0*1024+1*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::SWA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,1,1,0,1,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=(b?actualKV[b-1]:0)+logical；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2=0、sparseBlockSize=1、非PA；仅raw ACLNN Host可见，Torch入口拒绝；payload81988 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,1,1,0,1,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::SWA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-009：CFA BSND/BSND FP16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=BSND，KV=BSND，FP16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=1024（低16=1024，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(0)/RunSparseFlashAttention | 低16=0+1*1024+0*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,0,0,1,0,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=b*S2+logical；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload1024 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,0,0,1,0,false> | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-010：CFA BSND/BSND FP16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=BSND，KV=BSND，FP16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=17408（低16=17408，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(0)/RunSparseFlashAttention | 低16=0+1*1024+1*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,0,0,1,1,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=b*S2+logical；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload17408 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,0,0,1,1,false> | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-011：CFA BSND/BSND BF16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=BSND，KV=BSND，BF16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=66560（低16=1024，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(0)/RunSparseFlashAttention | 低16=0+1*1024+0*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,0,0,1,0,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=b*S2+logical；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload66560 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,0,0,1,0,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-012：CFA BSND/BSND BF16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=BSND，KV=BSND，BF16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=82944（低16=17408，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(0)/RunSparseFlashAttention | 低16=0+1*1024+1*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,0,0,1,1,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=b*S2+logical；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload82944 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,0,0,1,1,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::BSND,SFA_LAYOUT::BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-013：CFA BSND/PA_BSND FP16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=BSND，KV=PA_BSND，FP16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=1154（低16=1154，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(130)/RunSparseFlashAttention | 低16=130+1*1024+0*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,true,SFA_LAYOUT::BSND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,1,0,2,1,0,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  先按block_table把logical页映射physical页
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=table[b*maxBlocks+floor(logical/Bs)]*Bs+logical%Bs；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["页表→GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 页表ID合法，页尾拆段，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload1154 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,1,0,2,1,0,false> | BaseApi::SFAMatmulService<half,half,float,half,false,true,SFA_LAYOUT::BSND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-014：CFA BSND/PA_BSND FP16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=BSND，KV=PA_BSND，FP16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=17538（低16=17538，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(130)/RunSparseFlashAttention | 低16=130+1*1024+1*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,true,SFA_LAYOUT::BSND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,1,0,2,1,1,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  先按block_table把logical页映射physical页
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=table[b*maxBlocks+floor(logical/Bs)]*Bs+logical%Bs；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["页表→GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 页表ID合法，页尾拆段，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload17538 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,1,0,2,1,1,false> | BaseApi::SFAMatmulService<half,half,float,half,false,true,SFA_LAYOUT::BSND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-015：CFA BSND/PA_BSND BF16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=BSND，KV=PA_BSND，BF16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=66690（低16=1154，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(130)/RunSparseFlashAttention | 低16=130+1*1024+0*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,true,SFA_LAYOUT::BSND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,1,0,2,1,0,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  先按block_table把logical页映射physical页
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=table[b*maxBlocks+floor(logical/Bs)]*Bs+logical%Bs；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["页表→GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 页表ID合法，页尾拆段，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload66690 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,1,0,2,1,0,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,true,SFA_LAYOUT::BSND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-016：CFA BSND/PA_BSND BF16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=BSND，KV=PA_BSND，BF16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=83074（低16=17538，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(130)/RunSparseFlashAttention | 低16=130+1*1024+1*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,true,SFA_LAYOUT::BSND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,1,0,2,1,1,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=b*S1
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  先按block_table把logical页映射physical页
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=table[b*maxBlocks+floor(logical/Bs)]*Bs+logical%Bs；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["页表→GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 页表ID合法，页尾拆段，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload83074 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,1,0,2,1,1,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,true,SFA_LAYOUT::BSND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-017：CFA TND/TND FP16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=TND，KV=TND，FP16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=1092（低16=1092，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(68)/RunSparseFlashAttention | 低16=68+1*1024+0*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,1,1,1,0,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=(b?actualKV[b-1]:0)+logical；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload1092 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,1,1,1,0,false> | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-018：CFA TND/TND FP16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=TND，KV=TND，FP16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=17476（低16=17476，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(68)/RunSparseFlashAttention | 低16=68+1*1024+1*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,1,1,1,1,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=(b?actualKV[b-1]:0)+logical；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload17476 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,1,1,1,1,false> | BaseApi::SFAMatmulService<half,half,float,half,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-019：CFA TND/TND BF16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=TND，KV=TND，BF16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=66628（低16=1092，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(68)/RunSparseFlashAttention | 低16=68+1*1024+0*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,1,1,1,0,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=(b?actualKV[b-1]:0)+logical；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload66628 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,1,1,1,0,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-020：CFA TND/TND BF16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=TND，KV=TND，BF16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=83012（低16=17476，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(68)/RunSparseFlashAttention | 低16=68+1*1024+1*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,0,1,1,1,1,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  连续KV按batch或packed前缀偏移
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=(b?actualKV[b-1]:0)+logical；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["连续GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 逻辑值域正确，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload83012 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,0,1,1,1,1,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,false,SFA_LAYOUT::TND,SFA_LAYOUT::TND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-021：CFA TND/PA_BSND FP16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=TND，KV=PA_BSND，FP16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=1158（低16=1158，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(134)/RunSparseFlashAttention | 低16=134+1*1024+0*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,true,SFA_LAYOUT::TND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,1,1,2,1,0,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  先按block_table把logical页映射physical页
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=table[b*maxBlocks+floor(logical/Bs)]*Bs+logical%Bs；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["页表→GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 页表ID合法，页尾拆段，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload1158 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,1,1,2,1,0,false> | BaseApi::SFAMatmulService<half,half,float,half,false,true,SFA_LAYOUT::TND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-022：CFA TND/PA_BSND FP16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=TND，KV=PA_BSND，FP16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=17542（低16=17542，dtype位=0） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(134)/RunSparseFlashAttention | 低16=134+1*1024+1*16384 | BaseApi::SFAMatmulService<half,half,float,half,false,true,SFA_LAYOUT::TND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,1,1,2,1,1,false>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  先按block_table把logical页映射physical页
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<half,half,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到half，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<half,half,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | half ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=table[b*maxBlocks+floor(logical/Bs)]*Bs+logical%Bs；每行512/512/64元素 | visible/physical容量 | half ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ half | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | half fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | half fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与half/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["页表→GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | half | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 页表ID合法，页尾拆段，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | half NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→half | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload17542 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,1,1,2,1,1,false> | BaseApi::SFAMatmulService<half,half,float,half,false,true,SFA_LAYOUT::TND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-023：CFA TND/PA_BSND BF16 G1..64

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=TND，KV=PA_BSND，BF16，1<=G<=64，全局shape/dtype/mode/PA检查成功 | dispatchKey=66694（低16=1158，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(134)/RunSparseFlashAttention | 低16=134+1*1024+0*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,true,SFA_LAYOUT::TND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,1,1,2,1,0,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  先按block_table把logical页映射physical页
  两AIV各自发布当前部分
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；无splitG配对平衡
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=table[b*maxBlocks+floor(logical/Bs)]*Bs+logical%Bs；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC); group=aicIdx; cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["页表→GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 页表ID合法，页尾拆段，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload66694 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,1,1,2,1,0,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,true,SFA_LAYOUT::TND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,false> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=aicIdx，query任务按AIC均衡；实际M=G，S2 tile128；Vec0 两AIV以2token pair为粒度分两段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

### Route R-024：CFA TND/PA_BSND BF16 G128

#### 适用条件

##### 选择证据

| 层级 | 文件 | 符号 | 源码谓词/参数 | 结果/下一跳 |
|---|---|---|---|---|
| Host | op_host/sparse_flash_attention_tiling.cpp | InitParams/GenTilingKey | 原S2>0且sparseBlockSize=1；Q=TND，KV=PA_BSND，BF16，G128，全局shape/dtype/mode/PA检查成功 | dispatchKey=83078（低16=17542，dtype位=1） |
| Router | op_kernel/sparse_flash_attention.cpp | SFA_CASE(134)/RunSparseFlashAttention | 低16=134+1*1024+1*16384 | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,true,SFA_LAYOUT::TND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| 当前body | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/Process | 单MIX，flashDecode=false | AIC与AIV同图；split位进入两侧service的真实模板 |

#### Device 数据流

##### 函数级调用链

```text
sgl_sparse_flash_attention -> RunSparseFlashAttention<0,1,1,2,1,1,true>
 -> SparseFlashAttentionKernelMla<CubeService,VectorService>::Init
 -> AIV InitCubeVecSharedParams -> SSBUF0/flag15 -> AIC复制；InitMMResBuf -> InitCalcParamsEach
 -> ProcessMainLoop -> ComputeParamBatch/ComputeS1LoopInfo/ComputeParamS1/ComputeS2LoopInfo
 -> current task ProcessVec0 / IterateBmm1SFA
 -> previous task ProcessVec1 / IterateBmm2SFA
 -> task-2 ProcessVec2 -> final cast/GM max,sum and out
 -> tail flush 2 stages / release local event credits
```

##### 源码等价伪码

```text
# 源码等价伪码；初始化读到未定义成员或空GM越界时，不推定后续必执行
schedule: AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M
queryBase=(b?actualQ[b-1]:0)
queryAddr=((queryBase+s)*G+head)*512，qRope同式末轴64
visible = mode0 ? actualKV : actualKV-actualQ+s+1
selected sparse positions expand index*block+intra，-1是终止标记
for assigned query task:
 if returnLSE && mode0: binary search nonnegative sparse prefix，shorten s2End/loopEnd，0则skip（CleanOutput已清零）
 for each 128-position S2 tile:
  Vec0: pair-copy key512/keyRope64 -> privateUB row576 -> triple GM cache
  先按block_table把logical页映射physical页
  四AIV写互不重叠quarter，mode0 flag15配对屏障后发布GM与L1ready
  AIC: wait GM/L1 credits; cache row576 ND2NZ -> L1 right；firstS2载Q512+RoPE64到L1 Q，以后复用Q
  MM1 MatmulK<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,actualS2,576,false,true)
       K循环128,128,128,128,64；LoadData2DV2；FP32 Mmad
  FixpipeC310 ROW_MAJOR dualDstCtl1 -> 两AIV BMM1 UB，各M/2行
  V1: scale/softmax first或update，S2=128/<=64/65..127三特化，FP32 max/sum
      cast到bfloat16_t，blockStride33、repeatStride1存NZ；copy概率到同right L1的rope区offset128*512元素
      更新alpha/max/sum，末tile可写max/sum
  MM2 MatmulN<bfloat16_t,bfloat16_t,float,64,128,128,MK,KN>，MMParam(M,512,actualS2,false,false)
      P在rope区，右矩阵是same L1前512维K；N切4个128；Fixpipe dualDstCtl1 -> BMM2 UB
  V2: first拷到stage2；中间alpha*previous+current；last还除sum；单tileLastDiv
      CAST_ROUND -> GM有效M行；概率/输出不作量化
 drain task-1/task-2；补齐maxS2LoopCnt，用mode0 flag15平衡配对核
```

#### 内存与数据搬运

##### 资源与搬运表

| 层级/缓冲区 | offset/地址公式 | extent/容量公式 | dtype/layout | producer | consumer | owner/lifetime | 对齐/复用 |
|---|---|---|---|---|---|---|---|
| GM Q/RoPE | ((queryBase+s)*G+g)*512/64 | 每任务G或64头 | bfloat16_t ND | caller | Cube copy | caller至stream完成 | contiguous；Q两部分拼接点积 |
| GM K/V/RoPE | physical=table[b*maxBlocks+floor(logical/Bs)]*Bs+logical%Bs；每行512/512/64元素 | visible/physical容量 | bfloat16_t ND | caller | AIV聚合（只K/RoPE） | caller | physical ID与索引值域由调用方保证 |
| GM workspace | workspace_user=3*128*576*2*(AIC/2); group=floor(aicIdx/2); cache offset=(group*3+taskId%3)*147456 bytes；row stride576元素 | 每组3*147456 B | row576 K+RoPE | AIV Vec0 | AIC | execute user workspace | Host多出libapi与reserved correction空间不作为计算片 |
| L1 | right3槽各147456B，Q从442368B起73728B；P alias right+131072B | manager524288B，实际504KiB | NZ bfloat16_t | ND2NZ/概率copy | LoadData | AIC TPipe/跨族L1 | 先MM1消费rope再覆写为P，MM2后回收slot |
| L0A | slot*16KiB | manager64KiB，policy2*16KiB=32KiB有效片 | bfloat16_t fractal | LoadData | Mmad | 每MM tile | pingpong M/MTE1 |
| L0B | slot*32KiB | 2*32KiB=64KiB | bfloat16_t fractal | LoadData | Mmad | 同上 | BMM1转置语义由MMParam right=true；BMM2 false |
| L0C | slot*128KiB | 2*128KiB=256KiB | FP32 NZ | Mmad | Fixpipe | K累加到最后tile | FIX/M event |
| AIV UB | crossUB: bmm2@0 65536B，bmm1@65536两16384B；private另分配 | cross98304+private122368=220672B | FP32与bfloat16_t/INT32 | Fixpipe/GMcopy/VF | Vector/VF/MTE3 | 各AIV TPipe全launch | stage0两18432B；stage1两8448B；stage2 65536B |
| 寄存器 | 64个FP32/256B RegTensor、128个B16；tail mask=originN或originN-64 | 编译器分配 | FP32为主 | softmax/online更新 | store/cast | 单VF/Vector段 | S2三范围*first/update六实现 |
| SSBUF | offset0，sizeof(CVSharedParams)/4 words | 结构大小依bitfieldABI，数值未编译测量 | uint32 word copy | AIV subblock0 | AIC | Init到参数被复制 | flag15 mode4 PIPE_S |

##### 分层内存布局

```mermaid
flowchart LR
  Q["GM Q512 + RoPE64"] --> QL["L1 Q"]
  K["页表→GM K/RoPE"] --> V0["AIV聚合UB"] --> CACHE["GM 三槽row576"] --> KL["L1 K"]
  QL --> MM1["L0A/B -> MM1 FP32 L0C"]
  KL --> MM1
  MM1 --> SCORE["双目标AIV UB"]
  SCORE --> SOFT["AIV softmax / 概率cast"]
  SOFT --> P["L1 rope区复用为P"]
  P --> MM2["L0A/B -> MM2 FP32 L0C"]
  KL --> MM2
  MM2 --> O["AIV UB"]
  O --> LAST["AIV在线更新 / 除sum / cast"] --> OUT["GM有效输出及max/sum"]
```

```mermaid
block-beta
  columns 3
  IN["stage0 ping/pong 2×18K"]
  SOFT["BMM1 crossUB2×16K + stage1 2×8448B"]
  STATE["6×256B softmax + 3×512B辅助"]
  MM2["BMM2 crossUB64K"]
  ACC["stage2 float64K"]
  OUTPUT["cast 后GM输出"]
```

##### 字节账、交接边与复用顺序

```text
workspace_total=2*libapiSize+3*128*576*2*(AIC/2)
L1 reserved512KiB / used504KiB；L0A reserved64KiB/policy32KiB；L0B64KiB；L0C256KiB
AIV crossUB96KiB；private=6*256+3*512+2*18432+2*8448+65536=122368B；total220672B
本Host未查询/比较逐buffer UB/L1/L0可用上界，不能给出已执行的UB_total<=平台可用UB保证；
该不等式是迁移前必须满足的资源条件。没有同source低资源fallback。
```

| 边/复用子区 | producer | offset/extent | dtype/layout | consumer | ordering/sync | owner/lifetime | 安全条件 |
|---|---|---|---|---|---|---|---|
| 收集K→MM1 | ProcessVec0 | group3slot,row576 | bfloat16_t | MM1 | GM id6/7/8双AIV发布，AIC MTE2等id/id+16；L1 id0/1/2 | 到MM1与MM2读完 | 页表ID合法，页尾拆段，未填cache不当零值 |
| MM1→V1 | Fixpipe | BMM1 crossUB @65536+db*16384，每AIV32*128float | FP32 ND | ProcessVec1 | UB id4/5，AIC FIX set，AIV V wait，返回consumer credit | task slot到softmax读完 | S2有效mask与M半片一致 |
| V1→MM2 P | softmax cast/copy | L1 right+128*512*2，≤16KiB | bfloat16_t NZ/ND | MM2 | L1 id0/1/2发布，AIC MTE1等待双AIV | task同right slot/双buffer | 必须MM1已用完原RoPE区 |
| MM2→V2 O | Mmad/Fixpipe | BMM2 crossUB@0 64KiB | FP32 | ProcessVec2 | UB id3 AIC FIX→AIV V；AIV处理后归还 | 到last/update读完 | MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| 线上状态/最终输出 | V1/V2 | max/sum按query槽，alpha按task%2；out按queryBase/G/512 | FP32→bfloat16_t | 下一S2/V2/GM | LocalMemBar + queue/event；stage2 MTE3_V保护 | query所有S2块至末块 | 仅最后块输出；全空/zero风险不从式子推定 |
| local buffer | InitBuffers/BufferManager | 上述slice | 多dtype | pipe | mode4：L1 slots ID0/1/2；bmm2 UB ID3；bmm1 UB ID4/5；GM聚合slots ID6/7/8；AIC等待两AIV时分别id与id+16；SSBUF flag15 mode4 PIPE_S；splitG另用flag15 mode0 PIPE_MTE3 | TPipe至entry结束 | 本仓当前Process无显式policy Uninit调用，不能虚构手动释放；TPipe管理底层分配 |

#### 同步、精度与尾块

##### 同步与数值边界表

| 阶段 | primitive/机制 | producer | consumer/等待点 | 保护对象 | 精度/尾块 |
|---|---|---|---|---|---|
| Cube当前实例 | MatmulK/MatmulN；LoadData2DV2；M==1升16避免GEMV | L1搬运 | Mmad | L0A/B与C | FP16/BF16乘，FP32累加；K576末64、N512四个128，Fixpipe mAlign2/nAlign8、dualDst1 |
| softmax | 六VF范围×first/update；SAT CAST_ROUND，NZ块stride33 | score | 概率与max/sum | FP32状态/低精概率 | originN≤64以mask限制归约；65..127后64尾置−FLT_MAX |
| 在线O | FlashUpdateNew/LastNew<512,false,false>，8次64float寄存器 | V1/MM2 | V2 | 累积O | alpha=exp(oldMax-newMax)，last除sum；单块LastDiv |
| output | Cast(CAST_ROUND)原地复用stage2地址 | FP32 O | GM | attentionOut/max/sum | 只halfMRealSize行，max/sum DataCopyPad |
| 任务尾 | 两个drain拍、actualQ/KV/索引终止 | scheduler | 所有在途stage | slot生命周期 | -1前缀与可见范围依实际body；raw零KV/不合法值没有安全fallback |

#### 关键实现

##### 符号证据表

| 阶段 | 文件 | 符号/模板实例 | 实现事实 |
|---|---|---|---|
| Host/Tiling producer | op_host/sparse_flash_attention_tiling.cpp | InitParams/CalcInnerSize/FillTiling/GenTilingKey | 原S2>0且sparseBlockSize=1；payload83078 |
| Kernel entry/router | op_kernel/sparse_flash_attention.cpp | RunSparseFlashAttention<0,1,1,2,1,1,true> | BaseApi::SFAMatmulService<bfloat16_t,bfloat16_t,float,bfloat16_t,false,true,SFA_LAYOUT::TND,SFA_LAYOUT::PA_BSND,SFATemplateMode::CFA_TEMPLATE_MODE,true> |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_kernel_mla.h | Init/InitMMResBuf/InitCalcParamsEach/ProcessMainLoop | AIC idx=pair*2+half，G起点0/64，query任务按AIC/2个pair均衡；实际M=64，S2 tile128；Vec0 四AIV按ceil前半/后半再分四段，V1/V2每AIV ceil(M/2)与余M |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_cube_mla.h | IterateBmm1SFA/IterateBmm2SFA | 当前两MM路径及MM2从聚合的K NoPE平面/前512维取右矩阵；本Route无独立V GM读取 |
| Device body/helper | op_kernel/arch35/sparse_flash_attention_service_vector_mla.h | ProcessVec0/1/2/InitCubeVecSharedParams | 当前聚合、精度与同步；所有实际body已读取 |

## 算子特定优化


### Trick T-001：MM1后用RoPE的L1区保存概率

#### 触发与源码依据

- 适用 Route：本卡满足下列触发条件的全部Route。
- 触发条件：950当前mode1及源可见mode0；D512、Dr64、M≤64、S2≤128
- Golden 来源：[csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_cube_mla.h:294–309](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_cube_mla.h#L294-L309)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
        static_cast<uint32_t>(runInfo.mRealSize),    // singleM
        static_cast<uint32_t>(constInfo.dSizeNope),  // singleN
        static_cast<uint32_t>(runInfo.s2RealSize),   // singleK
        0,                                           // isLeftTranspose
        0                                            // isRightTranspose
    };
    MatmulN<Q_T, Q_T, T, s1BaseSize, s2BaseSize, dBaseMatmulSize, ABLayout::MK, ABLayout::KN>(
        inputRightBuf.GetTensor<Q_T>(s2BaseSize * constInfo.dSizeNope),  // 左矩阵P 来自rope位置
        inputRightBuf.GetTensor<Q_T>(),                                  // 右矩阵V nope
        mmL0ABuffers, mmL0BBuffers, mm2ResL0C.GetTensor<T>(), param);

    inputRightBuf.SetCrossCore();  // bmm2才释放KV，在这里释放

    mm2ResL0C.Set<HardEvent::M_FIX>();   // 通知
    mm2ResL0C.Wait<HardEvent::M_FIX>();  // 等待

```

#### 机制与设计原因

L1 right一槽128*576*2=144KiB，前512维仍供MM2右矩阵，末64维原RoPE在MM1消费后被P覆盖。P最多64*128*2=16KiB，恰好落原RoPE区；AIV以NZ stride33写，AIC MatmulN取offset128*512元素处概率。此节也证实MM2右矩阵实际为K非独立V。

#### 迁移边界

- 适用：同平台和同语义的MM1后用RoPE的L1区保存概率。
- 前提：L1生产/消费顺序、实际M64/S2128上界、crosscore ready与right槽直到MM2读完才释放。
- 失效：不满足guard时遵循当前源码后继实现或失败返回，不能单独扩大本specialization的shape域。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；删除同步/slot或改变数据源后的正确性、性能没有本次运行证据，不得声称安全收益。

### Trick T-002：三槽task ring覆盖两次MM与在线更新

#### 触发与源码依据

- 适用 Route：本卡满足下列触发条件的全部Route。
- 触发条件：taskId%3三槽，当前/前一/前两任务三拍，query尾补2拍
- Golden 来源：[csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_kernel_mla.h:595–623](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_kernel_mla.h#L595-L623)

**官方源码（固定 Commit 连续逐字摘录）**：

```cpp
            for (int64_t s2LoopCount = 0; s2LoopCount <= s2LoopLimit; ++s2LoopCount) {
                if (notLastTwoLoop) {
                    RunInfo &runInfo1 = runInfo[taskId % 3];
                    this->SetRunInfo(runInfo1, runParam, taskId, s2LoopCount, s2LoopLimit, multiCoreInnerIdx);
                    if ASCEND_IS_AIC {
                        this->cubeBlock.IterateBmm1(this->bmm1Buffers.Get(), this->l1RightBuffers.Get(),
                                                    v0ResGmBuffers.Get(), runInfo1, this->constInfo);
                    } else {
                        this->vecBlock.ProcessVec0(this->l1RightBuffers.Get(), v0ResGmBuffers.Get(), runInfo1,
                                                   this->constInfo, 0);
                    }
                } else {
                    if ASCEND_IS_AIV {
                        if constexpr (IS_SPLIT_G) {
                            if (maxS2LoopCnt > 0) {
                                maxS2LoopCnt--;
                                CrossCoreSetFlag<0, PIPE_MTE3>(15);
                                CrossCoreWaitFlag<0, PIPE_MTE3>(15);
                            }
                        }
                    }
                }
                if (taskId > 0 && notLast) {
                    auto &runInfo2 = runInfo[(taskId + 2) % 3];
                    if ASCEND_IS_AIV {
                        this->vecBlock.ProcessVec1(this->l1RightBuffers.GetReused(), this->bmm1Buffers.Get(), runInfo2,
                                                   this->constInfo);
                    } else {
                        RunInfo &runInfo2 = runInfo[(taskId + 2) % 3];
```

#### 机制与设计原因

当前Vec0聚合/BMM1，滞后Vec1/BMM2，再滞后Vec2；BMM1 UB两槽、BMM2 UB一槽在crosscore credit下交接。splitG的四AIV先合成一个共享GM cache，后续相邻AIC各处理64头，额外flag15交换补齐循环数。

#### 迁移边界

- 适用：同平台和同语义的三槽task ring覆盖两次MM与在线更新。
- 前提：L1 3×144KiB+Q72KiB、GM3槽、taskId与G配对索引一致；所有真实初始字段与合法索引前提。
- 失效：不满足guard时遵循当前源码后继实现或失败返回，不能单独扩大本specialization的shape域。
- 未验证：本次知识提取未执行编译、真机、数值或性能测试。

#### 错误做法

固定仓未提供可验证反例；删除同步/slot或改变数据源后的正确性、性能没有本次运行证据，不得声称安全收益。

## 模板与实现对比

| 对比维度 | CFA1非空KV | SWA数值0原空KV（raw Host） | 设计选择依据 |
|---|---|---|---|
| 命中条件/优先级 | 原S2>0、block1 | 原S2=0、block1、非PA；Torch拒绝 | 原S2先选择，再zero改写；layout/dtype/G另逐key展开 |
| 执行族/节点图 | AIV聚合/BMM1→V1/BMM2→V2 | 当前同一组可见body，但源GM容量与POD冲突 | 都为单MIX，topology与执行族分开 |
| M/N/K、tile 与 scheduler | M64、S2128，G128邻核各64 | 同样固定tile，不是空域安全实现 | 专用D512+Dr64，无通用维度fallback |
| workspace/L1/L0/UB | 3cache/coreGroup；L1used504K；UB220672B | 预算仍按改写1024，不能据此让空GM变有效 | Host预算与Device实际切片须分开 |
| AIC/AIV 或 kernel 交接 | mode4 buffer ID0..8+SSBUF15；Gsplit加mode0 15 | 当前同协议，但不承诺有效输入数据 | 双buffer/三或四cache的owner不同 |
| 同步、精度与 tail | 六VF分支、FP32更新、Round输出 | 无可验证数值保证 | CPU参考不具备这些舍入/累积顺序 |
| fallback/失败边界 | 参数不支持Host失败；unknown key无写 | 原空KV不安全，无fallback | 不造隐式torch fallback或FD launch |

## 平台差异

| 项目 | A2 | A3 | Ascend 950 |
|---|---|---|---|
| 支持状态 | EN API arch22 Supported，2201→ascend910b | EN API arch22 Supported，2201→ascend910_93 | EN API arch35 Supported，3510→ascend950；本卡仅950，A2/A3另卡 |
| Host/Launcher | DAV_2201，block1..128幂二 | 同A2；本固定body未额外区分两产品 | DAV_3510，block1；G128邻AIC配对 |
| Kernel/资源 | arch22 C/V、GM中间结果与atomic指数位校正 | 同A2 | arch35 RegBase，GM三cache，L1复用P，跨核UB Fixpipe，SSBUF参数 |

## 限制与失败边界

- draft表示当前源码存在可复用正确性/安全风险；source_closed只证明可追溯。本次未编译、真机、数值、性能或内存安全测试，不承诺这些问题是否在特定编译器中被优化消除、是否触发或运行输出为何值。
- **实际V源偏差**：全部Host非空KV CFA路线及source-visible mode0 body的InitGlobalBuffer都未绑定value，Vec0从key/keyRope打包，IterateBmm2SFA从right L1前512维取K；value参数没有当前producer/consumer。公开API目标与当前计算路径冲突，不能推荐K/V不同的输入沿这些路线安全复用。非量化参数中的同名key/value不自动意味着地址alias。
- metadata与索引/页表内容不在Host检验；调用者应提供单调合法的TND累计结束位置、对应实际容量的长度、有效非负索引前缀和-1尾、无越界physical页ID。schema shape正确不构成设备地址安全证明。
- 950 GetkeyOffset只拒负token，没有检查token>=actualKV/因果visible上界；ProcessSparseKv按候选个数而不是逐token可见性构造cache。除了mode0且returnLSE的二分非负前缀裁剪，-1提前遇到时未填满的cache没有统一zero/mask producer，可能读到workspace未生产行。调用者按实际visible范围给有效非负前缀是额外实现前提；不能将公开‘超长位置忽略’表述作为当前body保证。
- CVSharedParams成员没有{}，InitCubeVecSharedParams未赋tileSize但ComputeConstexpr读取它；shared中未生产字段不能推为0。RunParamStr部分qBOffset/qRopeBOffset及ConstInfo的s1D/gS1D等没有当前赋值，却在LoopSOuterOffsetInit的AIC分支生成暂存query偏移；Cube当前实际地址另走OffsetCalculator，不能把未定义暂存值编成某个确定地址。这里把可见未初始化C++读取列为风险终点，后续调度/资源仅符号化描述已可见body，不承诺一定执行。
- 原始S2=0：Torch wrapper拒绝，但Host selector仍可能产生mode0，再把POD seqSize改1024；注释称保留真实0与实际赋值不一致。原GM仍空却按1024继续的路径没有安全fallback，不推定正确清零。950 mode0/PA因PA正Bs/maxBlocks与block1 guard不可能由Host正常生成；只列非PA原空KV的mode0，其他编译键为dormant。
- raw BSND Q的S1=0也未单独被feature拒绝，Device可能得到totalBaseNum0/used0并不提交数学输出；不把Torch拒空逻辑当作raw ACLNN通用检查。支持范围以公开契约与正文约束为准，不扩大成空tensor安全推荐。
- 32/64位维度、shape乘积、sparseBlockCount、actual长度、threshold有缩窄或有符号/无符号转换；极大B/T/K与负metadata无法从有限H/D约束推定安全。scale无finite检查，softmax全无效行行为受初始化/mask/body影响。
- Host query重复加libapi导致保守额外分配；Device实际user片只偏移一份系统区。A2 Host预留nUpdate/sum额外GM预算而当前Device直接alias mm2 INT32，不应虚构两个实际独立slice。950中buffer管理只顺序分配、没有capacity bounds check；当前Process未显式Uninit各policy，不补造调用。
- splitKVFlag没有置true producer，FlashDecode/FD workspace及合并节点不构成当前Route；FP8/INT8/fullquant、sinks helper没有公开输入/当前实例，不合并进本算子。unknown low16key只default break，可能无输出写，非Trap和非fallback。
- generated ACLNN bridge、CANN宏SaveToBuffer、SDK ND2NZ/LoadData/Mmad/Fixpipe/Vector/VF等是明确框架/指令边界；当前owned selector、所有真正可达body及本地helper已闭合，不存在以未找到核心body替代的摘要。

## 源码索引

### 链路索引

| 链路阶段 | 文件 | 关键符号 | 支撑内容 |
|---|---|---|---|
| 公开API | [docs/api/en/operators/attention/sparse_flash_attention.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/en/operators/attention/sparse_flash_attention.md) | Hardware support/Signature/Description | 公开支持与契约 |
| 平台 | [python/sgl_kernel_npu/README.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md) | arch22/arch35 | 产品映射 |
| 平台接线 | [csrc/cmake/architectures.json](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json) | 2201/3510 | compute_units |
| 任务版本 | [README.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/README.md) | CANN9.1.0 | 固定版本证据 |
| CI版本 | [.github/workflows/pr-test-kernels.yml](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml) | CANN9.1.0 image | 未运行的固定CI配置 |
| 公开包装 | [python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/sparse_flash_attention.py](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/attention/sparse_flash_attention.py) | sparse_flash_attention/_ascendc_impl | 无隐式fallback |
| ACLNN adapter | [csrc/attention/sparse_flash_attention/torch_adapter.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/torch_adapter.cpp) | sgl_sparse_flash_attention/MakeOutputs | contiguous、query/execute、capture与stream |
| Runtime原语 | [csrc/aclnn_torch_adapter/aclnn_runtime.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/aclnn_torch_adapter/aclnn_runtime.h) | op_api_symbol/tensor_descriptor | 动态符号与descriptor所有权 |
| OpDef | [csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_def.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_def.cpp) | SglSparseFlashAttention | dtype/输入/属性/输出注册 |
| Infer | [csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_infer.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_infer.cpp) | InferShape/InferDataType | out/max/sum形状 |
| Host | [csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_tiling.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_tiling.cpp) | SFAInfoParser/SFATilingCheck/SFAMlaTiling/TilingSglSparseFlashAttention | 检查、selector、预算与字段 |
| Host ABI | [csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_tiling.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/sparse_flash_attention_tiling.h) | BEGIN_TILING_DATA_DEF/SFATilingInfo | 宏序列化producer |
| Host错误 | [csrc/attention/sparse_flash_attention/op_host/ops_err.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_host/ops_err.h) | OP_CHECK_IF/Log | 错误终止 |
| Device POD | [csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention_tiling_data.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention_tiling_data.h) | SparseFlashAttentionTilingDataMla | 显式144B/align8 |
| Key | [csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention_template_tiling_key.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention_template_tiling_key.h) | GET_TPL_TILING_KEY | 低16编码 |
| Router | [csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention.cpp](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/sparse_flash_attention.cpp) | sgl_sparse_flash_attention/RunSparseFlashAttention/SFA_CASE | 真实template实例/dtype16 |
| Device | [csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_common_arch35.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_common_arch35.h) | TEMPLATE_INTF/Traits | 当前body/地址/同步/资源 |
| Device | [csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_kernel_mla.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_kernel_mla.h) | SparseFlashAttentionKernelMla | 当前body/地址/同步/资源 |
| Device | [csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_cube_mla.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_cube_mla.h) | SFAMatmulService | 当前body/地址/同步/资源 |
| Device | [csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_vector_mla.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_service_vector_mla.h) | SFAVectorService | 当前body/地址/同步/资源 |
| Device | [csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_kvcache.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/sparse_flash_attention_kvcache.h) | ComputeParamBatch/ComputeParamS1/ComputeS2LoopInfo | 当前body/地址/同步/资源 |
| Device | [csrc/attention/sparse_flash_attention/op_kernel/arch35/util_regbase.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/arch35/util_regbase.h) | CVSharedParams/ConstInfo/RunInfo/RunParamStr | 当前body/地址/同步/资源 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/buffer_manager.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/buffer_manager.h) | BufferManager::Init/AllocBuffer | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/buffer.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/buffer.h) | Buffer::WaitCrossCore/SetCrossCore | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/buffers_policy.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/buffers_policy.h) | BuffersPolicyDB/BuffersPolicy3buff | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/matmul.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/matmul.h) | MMParam/MatmulK/MatmulN/LoadDataToL0A/LoadDataToL0B | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/FixpipeOut.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/FixpipeOut.h) | PFA_CFG_ROW_MAJOR_UB | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/CopyInL1.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/CopyInL1.h) | CopyToL1Nd2Nz | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/offset_calculator.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/offset_calculator.h) | OffsetCalculatorImpl | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/fa_gm_tensor.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/fa_gm_tensor.h) | FaGmTensor | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/fa_l1_tensor.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/fa_l1_tensor.h) | FaL1Tensor | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/gm_coord.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/gm_coord.h) | GmCoord | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/gm_layout.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/gm_layout.h) | GmLayout<BSNGD/TNGD> | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/parser.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/parser.h) | ActualSeqLensParser | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/offset_calculator_v2.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/memcopy/offset_calculator_v2.h) | OffsetCalculatorImpl | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_utils.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_utils.h) | castTraitZero/One/Rint | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_aligned128_no_update_sfa.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_aligned128_no_update_sfa.h) | ProcessVec1NoUpdateImpl/GeneralImpl | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_aligned128_update_sfa.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_aligned128_update_sfa.h) | ProcessVec1UpdateImpl/GeneralImpl | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned64_no_update_sfa.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned64_no_update_sfa.h) | ProcessVec1NoUpdateImpl/GeneralImpl | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned64_update_sfa.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned64_update_sfa.h) | ProcessVec1UpdateImpl/GeneralImpl | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned128_no_update_sfa.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned128_no_update_sfa.h) | ProcessVec1NoUpdateImpl/GeneralImpl | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned128_update_sfa.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_basic_block_unaligned128_update_sfa.h) | ProcessVec1UpdateImpl/GeneralImpl | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_mul_sel_softmaxflashv2_cast_nz_sfa.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_mul_sel_softmaxflashv2_cast_nz_sfa.h) | ProcessVec1Vf/SFAUpdateExpSumAndExpMax | 命中的specialization；未实例化量化/其他layout跳过 |
| Device直接依赖 | [csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_flashupdate_new.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/op_kernel/common/arch35/vf/vf_flashupdate_new.h) | FlashUpdateNew/FlashUpdateLastNew/LastDivNew | 命中的specialization；未实例化量化/其他layout跳过 |
| Device公用数学 | [csrc/utils/kernel/util.h](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/kernel/util.h) | CeilDiv/Min/Align | 当前工具函数 |
| 构建 | [csrc/attention/sparse_flash_attention/CMakeLists.txt](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/attention/sparse_flash_attention/CMakeLists.txt) | sgl_register_operator | ARCH2201/3510及auto-sync off/VF membar选项 |
| 注册 | [csrc/cmake/operators.cmake](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/operators.cmake) | sgl_register_operator/sgl_resolve_operator | 固定域注册 |
| CANN构建 | [csrc/cmake/cann_ops.cmake](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/cann_ops.cmake) | sgl_generate_cann_interfaces/sgl_add_cann_kernels | 生成bridge/平台entry |
| 域构建 | [csrc/cmake/domains.cmake](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/domains.cmake) | sgl_add_operator_domains/sgl_discover_operators | attention构建 |
| 根接线 | [csrc/CMakeLists.txt](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/CMakeLists.txt) | CANN operator build | 注册框架入口 |

每行一个文件，均列sources并固定40位commit；不使用另一仓同名实现替换本entry的约束、POD或body。

### 实现复用检查

| 检查项 | 可复用事实 | 不得改变的约束 | 源码符号 |
|---|---|---|---|
| ABI/POD | 显式144B Device POD与Host各setter；950另有CVSharedParams | dispatchKey/dtype位、嵌套对齐、FD inactive；bitfield跨端同TU但不能编造packing，未写字段不得当0 | tiling_data.h/tiling.h/util_regbase.h |
| 调用顺序 | query→empty workspace→同stream execute；单MIX三拍 | contiguous副本/descriptor capture、record_stream；两拍flush | torch_adapter/Process |
| workspace/内存 | 当前slice、owner与L1/UB复用 | 保守预算≠实际offset；L1原RoPE→P alias只在MM1后；G128 workspace组数减半 | GetWorkspaceSize/Init/InitMMResBuf |
| 同步 | mode4 id0..8、id+16，SSBUF15，splitG mode0 15 | ID/pipe/初始化credit、tail轮次和参与核必须一致 | PreloadPipeline/Buffer/ProcessMainLoop |
| 精度与尾块 | FP32累加/softmax，低精概率，在线更新后输出 | first/update×3S2范围，NZ33stride，last除sum与输出Round | Cube/Vector/VF current bodies |
| 失败边界 | 真实Host错误、raw空KV风险、实际V偏差、初始化/索引风险 | 不把可见缺陷改称缺源，不伪造运行验证或安全fallback | Parser/Checker/entry/body |

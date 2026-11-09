---
type: Guide
title: vLLM Ascend 3164实验模型QSA：分组索引、FIA/GBSA与HC数值合同
description: 固定3164实验模型QSA辅助链，核对四token分组和残余、FIA位掩码共享workspace、GBSA整数准备与ACLNN/Meta桥、Gemma RMSNorm/MRoPE和HC舍入，保留外部CANN Device边界。
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.attention
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/qwen4_exp/qsa.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/aclnn_torch_adapter/gbsa_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/torch_binding.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/torch_binding_meta.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/docs/qwen4_exp_qsa_dispatch.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/linearnorm/qsa_rmsnorm_mrope.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/qwen4_exp/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/qwen4_exp/fia.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/qwen4_exp/gbsa.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton/qwen4_exp/hc.py
  role: implementation
created_at: '2026-11-03T06:52:43Z'
updated_at: "2026-11-04T02:54:15Z"
platforms: []
aliases:
- prepare_qsa_gbsa_inputs
- build_qsa_fia_mask
- triton_qsa_rmsnorm_mrope
- hc_combine_norm
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# QSA辅助链的接入合同

## 版本、用途与待闭合部分

本卡只覆盖固定Main3164adc8fe75892fbf7f99f524bb72fddf1e6efd相对ceac新增的QSA/FIA/GBSA/HC辅助实现及Torch注册delta；新源码以完整AST/程序投影阅读，未import、编译或运行。模块namespace是qwen4_exp，__init__文案称实验Qwen3.8 Flash-Next，不据目录名推导所有Qwen模型通用。完整模型调度/权重/网络与外部CANN GenericBlockSparseAttention Device仍需其来源；本卡是框架集成facet。

来源dispatch文档声明：token TopK2048、压缩比4，prefill按scheduler chunk起点的cached prefix<24K走FIA，后续chunk走GBSA，decode总是GBSA；跨24K的整个chunk维持原路线，4096-token与64MiB预算属于文档给定部署。当前所读辅助kernel不实现这个高层调度判定，也不能用这些数值直接约束任意模型。源码作者的A3 HACC/515-lane及测试声明不是本次验证，需按实际编译器/平台重新验。

## 紧凑分组与压缩状态环

pack_qsa_group_indices_npu输出[T,token_topk/ratio+ratio-1]，T是本次query token行数，ratio是压缩组内token数，token_topk是按token计的选择预算。前段是LI选出的完整group ID、尾段是当前未完整group的逻辑token；不能把整个row都当token ID或都当group ID。helper令`BLOCK_TOPK=token_topk//ratio`，每行按query position、sequence length和该容量截完整group数量，再重建最多ratio-1个可见残余；无效为-1。

本模型的2048/4部署ABI因此是512个group加3个残余槽，512不是这个可复用pack helper的硬编码上限；其他几何仍须分别满足下游FIA/GBSA合同，不能由helper可分配推导完整模型支持。

wrapper核NPU/Triton、整除与形状，可用caller out，但不替caller检查每个source ID、buffer dtype或部分重叠。

qsa_compress_groups_with_ratio把当前token行与持久compressor-state ring共同组成一个完整group，FP32累加后除ratio，结果存回raw dtype。当前chunk内位置从raw读取，前缀从request-owned状态页position%state_size读取；第一token的三轴RoPE position也从raw或独立INT64 position ring选择，无ring则用逻辑首位。源request/table/row边界有mask，非法来源取0但不构成错误恢复；caller必须在覆盖ring前完成历史读取，并只消费已完成group的compressed_slots。

qsa_store_cache_rows尊重cache/rows元素stride，cache需[pages,page_size,1,width]且非空；实际写入数取min(slot数,rows数)，负/超capacity槽跳过。它不是“数量不匹配报错”，不能静默裁短后当整步成功；有效目的slot唯一性和输入同设备/顺序由框架保证。压缩状态、position状态与压缩KV的slot域分别记录，不用同shape替代请求身份。

## FIA掩码：四字节word和进程共享存储

FIA mask为bool且True屏蔽、False可见；初始化INT32 0x01010101使四token均mask，完整group选择写0，残余group用按residual*8移位后的word保留未可见字节。groups>=512且有残余时，会在全选满情况下移除最后有效完整group，给残余保留总容量；不能把残余算成额外第513个完整group。

workspace按str(device)进程全局缓存，首次分配storage、words、INT64 indices、INT32 updates及selected；后续容量不足直接ValueError，不自动扩容。view的row stride为mask_words+update_width，宽变窄时仍按真实view stride；不是把最大宽连续内存直接当紧凑小row。scatter把无效group的更新导向mask区之后的scratch列，避免越入其他row。空选择行设置dummy可见word供FIA计算，最终copy_qsa_fia_output依据selected把该行输出置0。

共享workspace跨layer/step复用依赖实际stream/图调用顺序，源码没有建立多请求并发租约；不能让两个并发graph写同一设备缓存，或在capture后替换storage地址。mask构建不是原地修改caller TopK，selected也必须与本轮FIA结果配对；输出copy尊重目标三轴stride。

## GBSA准备：整数单位、残余容量与页表

prepare_qsa_gbsa_inputs接紧凑groups+3 row，仅消费前groups的完整ID并按可见长度筛选。request负ID加requests_count是Python式负索引映射；其后没有再统一边界guard，producer必须确保仍合法，不把-1当无请求padding。position/length取INT32，故INT64输入的极大逻辑坐标不能自动承诺安全。

若有效group已为紧凑前缀，直接按序存；中间洞则tl.cumsum压紧有效项、把无效项置于后部。每KV head复制同一选择，输出count限定有效前缀；残余group为visible//4，当groups<512可多分配一项，512满容量时替换末项而非扩容。每query独立成为一个cu_query长度1请求，gather其真实128-token页表行；输出全部新分配，没有全局tensor cache或CPU回读。空rows只把cu_query归零。

这种GBSA稀疏块是4token组，block table是128-token kernel pages，和[SFA](vllm_ascend_sfa_selection_execution_contract.md)的token TopK、B项query长度及Selection status均不是一套ABI。残余explicit residual_block_mode=0与is_consistent_topk等属性必须和实际ACLNN metadata生成一致。

## GenericBlockSparseAttention桥接与Meta

新增Torch schema/PrivateUse1与Meta各注册metadata及attention两入口。metadata输出1024个INT32，原样把稀疏indices/counts、cu/used长度、head几何、block_shape、layout、mask/quant/window/residual/consistent属性交aclnnGenericBlockSparseAttentionMetadata；不是直接可替换为别族1024-word metadata。

attention adapter拒绝空Q/K/V/indices/counts与block_shape长度!=2；quant_mode非0必须显式attention_out_dtype，否则沿Q dtype。attention输出shape直接取Q，LSE开关True时按TND[T,N,1]、BNSD[B,N,S,1]或其他按[B,N,S,1]重排轴生成FP32，False空[0]。不会在metadata=None时自动生成正确metadata，也没有在此完成所有shape/layout/scale合法性校验。两个局部std::string在同步宏调用范围内活着；外部executor是否复制属性仍属于宏/SDK边界，不能从指针签名保证异步寿命。

Meta只分配对应shape/dtype，metadata固定1024；它不算稀疏索引、mask或真实kernel准入。新增注册、fake impl成功和量化参数出现在schema不等于目标硬件/量化模式已实现。

## Gemma RMSNorm、MRoPE与HC舍入

qsa_rmsnorm_mrope只收[T,H,D] BF16与匹配1D BF16 weight、内维连续，cache为2D或3D且rope_dim正偶数<=D。RMS在FP32，仿射为(1+weight)，先转BF16后再RoPE；旋转的每次乘、加减又显式回BF16，不能以一段FP32融合替换而声称同误差。MRoPE用offset%3及h/w section选择三轴，不是把整个轴块连续切片；未旋转尾部保留norm结果。wrapper不把所有同设备、position范围、section数值均完整核验，需模型合同。

HC提供五个opaque op，NPU走Triton，非NPU走Torch参考，fake仅empty shape。grouped Gemma norm按group独立FP32 RMS，weight可共享group宽或全hidden；HC SiLU先除stream数；gate mix为各stream sigmoid(gate)*x求均值；combine为residual+block*[2*sigmoid(injection/HC)]（无injection为1）。combine_norm先把combined转residual dtype并物化，再升FP32做group norm，不能在未舍入FP32 combined上直接norm。

这些kernel尊重row stride但要求inner stride1，部分wrapper仅核shape而非全部dtype/device。权重连续、HC>0、group整除、injection[rows,HC]与可选指针模板都是编译/数值合同；没有CUDA PDL hook不代表NPU stream可以无依赖复用。先验证各中间tensor、BF16舍入、残余边界、不同mask宽复用与图地址，再测融合减少的launch与搬运；本卡不声称新实验模型整体精度或吞吐通过。

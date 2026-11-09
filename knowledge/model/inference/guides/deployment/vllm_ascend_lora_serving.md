---
type: Guide
title: vLLM Ascend LoRA 服务：适配器选择、MoE 布局与单槽路径
description: 在 A2/A3/310P 核对基础模型和 adapter 的命名、rank、堆叠专家权重及运行时加载，区分单槽融合、通用 BGMV 和 fully-sharded 路径。 补充 packed 权重刷新、捕获选路、输出累加语义与 W8A8 MoE token/专家映射边界。；补BGMV/SGMV Device数值、长度分片、负索引不写与半精度launch边界。
tags:
- task.implementation
- topic.model_serving
- topic.model_adaptation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/lora.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/lora.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/lora/utils.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/lora/fused_moe.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/lora/quant_moe.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/lora/lora_ops.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/lora/punica_npu.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/kernels/bgmv_expand.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/kernels/bgmv_shrink.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/kernels/sgmv_expand.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/kernels/sgmv_shrink.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/kernels/math_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/kernels/types.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/kernels/utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/lora_linear.md
  role: supporting
created_at: '2026-10-29T09:42:28Z'
updated_at: '2026-11-03T05:56:49Z'
platforms:
- a2
- a3
- 310p
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- PunicaWrapperNPU
- AscendFusedMoEWithLoRA
- QuantMoELoRAImpl
- _try_single_lora_linear_triton
- BGMVExpand
- BGMVShrink
- SGMVExpand
- SGMVShrink
---

# vLLM Ascend LoRA 服务：适配器选择、MoE 布局与单槽路径

## 适用范围

来源明确支持 Atlas 300I Duo、A2、A3；不由此推导950。Dense 与 MoE 均有入口，MoE 只声明非量化/W8A8 dynamic 的 TP AllGather 与 EP All-to-All。其他 MoE 量化、Fused MC2、dynamic EPLB 不支持。PCP 的额外排除见[CP 指南](../integration/vllm_ascend_context_parallel_topology.md)。

## 注册与选择契约

同时设置 enable-lora 与 lora-modules。adapter 目录需 adapter_config.json 和权重，name 是客户端 model 值；base_model_name 是训练基座信息，不能代替请求名称。基础模型请求使用 served-model-name，二者共享冻结的 base 权重。

max-lora-rank 必须取8/16/32/64且不小于 adapter 的 r；max-loras 是每 batch 活跃 adapter 上限，不是磁盘可存数量。fused PEFT MoE 的堆叠专家权重用 is_3d_lora_weight=true，逐专家 keys 用 false；非 MoE 忽略该字段。

## 执行路径与性能判断

A2/A3 的 single-slot fast path 要求 max-loras=1、fully-sharded 关闭、BF16、支持 rank、token数<=128。shrink split-K，expand 融合 partial reduction、mask、scale 与增量输出。不能把 BF16 的单槽条件扩大成所有 FP16/多 adapter 组合。fully-sharded 对全 TP 计算分片，适合候选长序列/高 rank/大 TP，但不使用上述融合路径。

通用 BGMV 机制与旧版本 kernel 约束见[多 LoRA 规则](../../optimizations/rules/multi_lora_bgmv_ascendc_vector_kernel.md)，该卡固定旧提交；不能用旧 Host 检查替代本版本服务配置或宣称950已支持。

## 动态加载、验收与回退

enable-lora 并设置 VLLM_ALLOW_RUNTIME_LORA_UPDATING 后可调用 load/unload endpoint；在受控服务环境核对 adapter name/path 与请求路由。分别测试 base、adapter、同 batch 多 adapter、卸载后选择失败和 base 继续可用，比较浮点参考、峰值和时延。HTTP200 仅说明服务请求完成，不证明 adapter 数值正确或 fast path 生效。失败卸载目标 adapter、恢复 base，关闭新路径。本次未运行 LoRA 或内核测试。


## 中文PO对照与平台条件分层

固定lora.po共43条有效非空翻译，0obsolete/fuzzy；42条msgid与当前英文精确匹配，剩余MoE表头使用Expert parallel，而当前英文为Expert parallelism。该措辞变化不表示新增并行模式；非量化/W8A8 dynamic的两列支持及其他MoE量化、Fused MC2、dynamic EPLB限制仍按当前主指南核对。

译文保留is_3d_lora_weight、adapter_config.json中的rank、注册name/base_model_name区别、动态load/unload与single-slot条件。不能因本卡整体包含310P平台，就把仅A2/A3声明的BF16单槽融合扩到310P；也不能因fully-sharded可作为性能候选，就宣称它使用同一融合kernel或对所有序列/TP都有收益。

中文“成功调用返回200和非空内容”只提供接口smoke信号。适配器是否真正被选择、增量数值正确、MoE堆叠专家布局以及卸载后在途请求状态还需独立验证。状态stable与既有平台枚举本批保持原来源范围，没有新增verified或本环境LoRA/NPU测试结果；剩余实现/Device/并发知识继续生产。


## 固定源码中的单槽打包、选路与输出语义

本节补入 ceac1a2 的五个 Python 实现文件；这是框架执行合同，未运行 NPU、Triton、图捕获或外部算子。原平台声明不变，不能据此扩展到950或任意量化组合。

`utils.py` 的 packed A 将各 slice 的 rank 串接，packed B 在 `[max_loras, 1, n_slices*rank, sum(output_slices)]` 中按 rank/output slice 写块对角，其余位置为零。set_lora 同时刷新原堆叠权重和打包副本，reset 清两者；修改原权重后是否及时刷新副本要沿调用方核对。MergedColumn/MergedQKV 分别要求精确的层类型、2/3 个 packed modules、max_loras=1、非 fully-sharded；子类或改名不自动满足 exact-type 检查。3D 输入和输出先展平前两维、计算后复原。

`PunicaWrapperNPU` 仅在 A2/A3、max_loras=1 且非 fully-sharded 时选择单槽模式；BF16 是后续 Triton 条件，并非该初始化判断。缺少 LORA_CUSTOM_OPS 或 max_lora_rank>=128 转 Native torch_ops；这不扩展上文发布文档的 rank 支持承诺。普通 prefill 走 SGMV，310P 在图捕获时走 BGMV；decode 的 no_lora 会依据当前 mapping 重算，不能缓存成初始化常量。

Triton 还要求正在捕获、x/y 为 BF16、输入/权重/输出连续、token<=128、slice rank 为8/16/32/64；多 slice 要提供一致的 packed A/B 和输出宽度。输出>=8192时 token 超过32（rank<=16）或64将回退；输出>=5120、rank>=16、token>64也回退。因此“小 batch + 单槽”不足以断言融合路径生效。workspace 是按 total rank 缓存的 FP32 `[4,128,rank]`，split-K=4、block-K=256，shrink 的分块累加后由 expand 归并、应用 adapter mask/scale，再加至 y；并不代表实测该硬件上的最优形状。

`add_inputs` 的语义需按分支检查：单槽 matmul 回退按该参数选择 add/copy；Triton 分支始终加到 y，其接口没有传入该参数；通用 Ascend expand 包装也没有向底层传递该选项。重用输出 buffer 前必须明确是否已含 base 输出，不能把所有分支都当覆盖写。logits 输出小于 rank 时用 FP32 bmm；FP32 base 输出的通用 expand 先在权重 dtype 工作区计算 delta 再转换相加。`apply_lora_full_linear` 则走 FP32 einsum 并 copy 最终结果。

## MoE token/专家映射与 W8A8 动态量化顺序

`fused_moe.py` 按真实 token 截断 adapter mapping、补 -1，并在 TP 下按 MoE 自身的 tp_size/rank 分片；EP 使该 TP 大小归一，不能再用全局 TP 重复分片。AllGather 路径用 expanded_row_idx 的绝对值排序求逆排列，再整除 top_k 恢复 token 来源；All-to-All 路径需使用同样 split/group 交换 adapter 索引，等待 handle 后恢复 dtype。group_list 在这里是每专家数量，通过 repeat_interleave 展开；把累计前缀传进来会改变行数及专家映射。

w13 的 LoRA 增量发生在激活之前，w2 增量发生在 base down GMM 后。无 routed token 的局部 delta 可跳过，但不因此取消调用链外层的集合通信。源码对 dynamic EPLB 和 Fused MC2 明确拒绝；局部索引在 w2 后删除，本模块没有提供异常路径 finally 清理保证。为兼容上游字符串比较而设置 class.__name__，不代表实际类身份或 GPU 构造过程相同。

`quant_moe.py` 当前注册的是 W8A8 动态量化实现，重复注册报错、未知 QuantType 拒绝。它在路由前拒绝已经量化成 int8 的 hidden states 和外传 dynamic_scale，以保留浮点 LoRA 边界；仅接受 ALLGATHER/ALLTOALL，并检查展开索引、权重/scale、单一 expert tensor。fused scale-bias、antiquant offsets 等分支不能由该实现推导支持。

实际顺序是浮点输入→dynamic quant→GMM1回到输入 dtype→w13 LoRA→原模型激活→top-k scale→dynamic quant→GMM2→w2 LoRA。把两个增量都移到激活之后会改变结果。SWIGLUOAI、clipped/uninterleaved、SWIGLUSTEP、GELU/GELUTANH 和普通 SwiGLU 有独立处理，适配新模型必须保留训练配置中的 gate/up 次序和限幅参数。返回的 event 创建在 GMM2 前，不能当整层完成或性能测量结束事件。

## 图捕获与资源生命周期的验证边界

MoE LoRA 用 `(adapter_slot*num_experts+expert_id)` 把权重前两维展平，关闭的 adapter 映射为 -1；adapter_enabled 的索引只有 clamp_min，没有上界防护，调用方仍须保证 ID 合法。实现避免通过 unique/nonzero 的数据值决定输出形状，只消除一种捕获障碍，不证明整体图可捕获。fully_sharded 参数在该局部路径未参与算法，不构成 fully-sharded MoE 的实现证据。

全局 wrapper 字典持有强引用、单槽 workspace 缓存以及打包权重副本均有独立生命周期；这些文件未提供卸载后自动移除 wrapper、跨流重入或并发热更新安全保证。Agent 验收应覆盖 base/adapter 混合 mapping、adapter 重载后副本刷新、零 token、TP/EP 专家映射、不同 add_inputs 输出语义及捕获/回放一致性；未执行测试不能把静态门限或源码注释转换为吞吐结论。


## BGMV/SGMV Device实现的数值、分片与跳过合同

本节完整阅读 csrc/kernels 的七个固定来源，不代表编译、ABI或真机通过。Python wrapper、权重转换和Device分支必须一起满足，不能用一个launcher名证明任意rank/hidden size可用。

| 阶段 | Device实际计算与数据类型 | 适配边界 |
| --- | --- | --- |
| BGMV shrink | 每token从int64索引选LoRA，FP16/BF16输入与权重转FP32，11776元素tile做乘积/reduce累加，再乘scale，输出FP32 | hidden超过tile走incremental分支；常量旁“optimal”注释不是新硬件最优参数证明 |
| SGMV shrink | 数值同shrink，但每token从各sequence length逐项减去定位请求LoRA | seqLen是逐请求长度，不是累计offset；未覆盖token得到-1；长度/索引数与非负性须上游保证 |
| BGMV/SGMV expand | FP32 shrink结果与半精度权重相乘，FP32归约后加原y，CAST_RINT转回半精度，写sliceOffset开始的outputHiddenDim | supported ranks只有8/16/32/64四条归约分支，不能从接受maxLoRARank实参推导其他rank有正确结果 |

expand按8192权重元素、4096输出元素分片，64个FP32元素一repeat；rank8直接BlockReduce，16/32用不同次数PairReduce，64再BlockReduce。尾片按剩余权重的完整repeat数计算，hidden/rank/对齐必须由调用层满足；这里没有通用任意尾长度validator，不能自行扩大接受集合。

四kernel按 ceil(batchSize/numTokensPerCore) 启核，单核处理连续token并截到batch；numTokensPerCore必须为正，不能以Device实现没有报错证明该值已验证。索引小于0直接continue，不写shrink/expand结果，也不把yIn复制到独立yOut。因此无LoRA行需要调用者预初始化/保留输出，若改成不同输出buffer不能假定负索引行自动正确。

launcher只处理AscendType::FP16/BF16，BF16有 __CCE_AICORE__>=220 编译条件；enum中存在FP32不等于launcher支持FP32，其他type直接return。共同utils的AccType<half>=half也不改变这四kernel显式的FP32累加。RoundUp模板要求有效正roundVal，local_mem_copy按256字节repeat及tail复制；它们是工具语义，不是独立的新硬件支持或速度保证。

Agent验证时保存实际dtype、rank、hidden维度、slice/full输出stride、indices/seqLen和token分片，覆盖无LoRA、不同请求共batch、tile边界/尾片、别名与独立输出buffer，再对照参考线性计算和真实服务。不能只比较有LoRA行或只看kernel launch返回就报告完整适配通过。


## Triton LoRA说明页的量化验收与路由边界

固定 docs/lora_linear.md 明确dense单slot、A2/A3、非fully_sharded且ACL graph capture才选择Triton，其他eligible路径可回packed matmul，多adapter等仍Punica，不能将Device的通用SGMV/BGMV实现与单slotTriton资格混同。split-K=4的FP32暂存容量128 token，支持rank8/16/32/64；两至四packed slice且每slice rank>=32才用跳过B非对角零块的sliced expand。

文档按输出宽度与token阈值回packed matmul：output>=8192时rank8/16超过32 token、rank32/64超过64；另output>=5120且rank>=16、token>64也回退。它是形状策略，不是跨设备性能定理。来源测试用Qwen3.5-27B的O/QKV/QKVZ本地shape、token1/31/128，数值标准相对L2<0.5%，base-only mask行则bit-exact保持y。正确验收同时检查两种标准与残差原位语义，不能只看整体误差掩盖base行改写。文档与已有实读实现互证，未在此运行这些测试。

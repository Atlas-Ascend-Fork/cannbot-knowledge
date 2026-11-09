---
type: Guide
title: vLLM Ascend 批次不变性（Batch Invariance）：构建、Host注册与确定性验收
description: 按 VLLM_BATCH_INVARIANT 和 block_size=128 核对批次不变性中文模型表、batch_invariant_ops 安装与 HCCL init 前的 Host 注册；限定 A2/A3/950，分开验收构建、运行、抢占与性能。；补Triton实际tile/包装重载、mean dtype传递与FP32归约边界。
tags:
- task.testing
- topic.precision
- topic.reinforcement_learning
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/batch_invariance.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/rl.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/batch_invariance.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/batch_invariant.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/attention_v1.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/v1/worker/gpu/attn_utils.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_batch_invariance_support.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/batch_invariant/matmul.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/batch_invariant/mean.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/batch_invariant/rmsnorm.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/batch_invariant/softmax.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/linear_persistent.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/matmul_bias_persistent.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/triton/docs/mean.md
  role: supporting
created_at: '2026-10-29T09:42:28Z'
updated_at: '2026-11-03T05:56:49Z'
platforms:
- a2
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- matmul_persistent
- linear_persistent
- mean_batch_invariant
- softmax_batch_invariant
---

# vLLM Ascend 批次不变性（Batch Invariance）：构建、Host注册与确定性验收

## 范围和保证边界

Beta 功能的上游指南声明覆盖 A2/A3/950，中文模型支持表按同一固定英文主表核对：

| 模型 | A2 | A3 | 950 |
| --- | --- | --- | --- |
| Qwen3-1.7B | 支持 | 支持 | 支持 |
| Qwen3-8B | 支持 | 支持 | 支持 |
| Qwen3-30B-A3B | 支持 | 支持 | 支持 |
| Qwen3-235B-A22B | 支持 | 支持 | 支持 |
| Qwen3.5-35B-A3B | 支持 | 支持 | 不支持 |

表格是上游功能声明，不是本环境的已执行验证；不能把“其他模型可能工作”升为全模型保证。determinism依赖完整kernel、通信与调度条件，seed相同本身不够。

## 构建期和运行期分别验证

源码构建需要 COMPILE_CUSTOM_KERNELS=1 与 VLLM_BATCH_INVARIANT=1，先装 AscendC run package，再装 batch_invariant_ops wheel。预构建 wheel 不带 csrc，安装 wheel 时加变量不会重编译算子。手动构建必须取与已装版本匹配的源码，芯片参数按 A2/A3/950 分别选 ascend910b/ascend910_93/ascend950。

先检查扩展可导入和 npu_matmul_batch_invariant 注册，再在运行时设置 VLLM_BATCH_INVARIANT=1 或受支持 RL 子配置。Docker 构建安装过算子不表示运行开关已保留。RL enable_batch_invariant 还设 HCCL_DETERMINISTIC=strict、LCCL_DETERMINISTIC=1，不代替算子安装。

## 调度前提和失效信号

chunked prefill、prefix caching、抢占后重算均不支持。前两者不自动关闭，显式禁用，并随禁用 chunked prefill 设置 block_size=128。抢占重算把已生成 token 放入 Prefill，无法与原 Decode 计算对齐；通过并发、最大长度、输出上限和合理缓存预算降低抢占风险，不能把“降低概率”当成已消除。

## 验收与回退

固定模型权重/版本/seed/采样，分别改变 batch size、请求次序、混合流量，比较 token 与需要的 logprob/数值容差；监控 KV usage、preemption 和实际 deterministic kernels。覆盖长度边界，记录生效配置及性能代价。出现抢占或不支持组合时停止确定性结论，恢复基线再定位。本次未构建算子或运行模型，不新增已验证事实。


## Host初始化顺序与两条算子路线

固定Worker的所读分布式初始化片段先调用init_batch_invariance，再init_distributed_environment(HCCL)。init读取vllm.envs中的VLLM_BATCH_INVARIANT；至少一种实现可用才进行环境/算子覆写，否则warning并skip。模块能被导入或环境变量存在，均不证明本次注册已成功；也不能靠运行中更改字符串就认定现有worker已切换模式。

override_envs_for_invariance把AscendConfig.weight_nz_mode设0、HCCL_DETERMINISTIC设strict、LCCL_DETERMINISTIC设1，并调用torch.use_deterministic_algorithms(True,warn_only=True)。warn_only意味着不由这一调用证明所有算子都已有确定性实现；这些全局设置与真实通信/NPU结果分别验收。

| 条件 | 固定Host注册 | 不能推导 |
| --- | --- | --- |
| HAS_TRITON | addmm、bmm、softmax/_softmax注册NPU实现 | 安装了Triton不证明每个模型/shape已通过 |
| HAS_ASCENDC_BATCH_INVARIANT | mm/matmul优先注册AscendC；直接替换torch_npu.npu_fused_infer_attention_score、torch_npu.npu_add_rms_norm及torch.sum/Tensor.sum | import检查只捕获ImportError；外部op符号/ABI/执行仍可另失败 |
| 无AscendC但有Triton | mm/matmul/linear走Triton路线 | 不等于也安装了上行FIA、AddRmsNorm、sum覆写 |

Torch Library保存在进程全局_batch_invariant_LIB，直接Python函数替换也影响该进程其他模型，不能当每请求或每实例独立开关。已读模块没有完整的重复初始化guard/undo流程；关闭变量不会自动恢复这些函数、配置与确定性设置，恢复基线需核对进程真实状态。

## reduce_sum与模型接口差异

模块先保存torch_sum避免常规递归。reduce_sum把axis映射到dim，同时给dim/axis会报TypeError；仅一维x且未给dim时改为-1。只有NPU、FP16/FP32/BF16、末维（-1或x.dim()-1）且未显式dtype时才调用npu_reduce_sum_batch_invariant；其他维度/tuple/全量归约、CPU、其他dtype或显式dtype转调保存的native torch_sum。这是所读分支，不保证任意torch.sum重载参数或新模型归约都已有同一确定性kernel。

add_rms_norm（AddRmsNorm）覆写拆为x+residual再npu_rms_norm，返回(norm_result,None,new_residual)。FIA为直接函数绑定，不只靠aten dispatcher。新模型应检查实际调用的是Python函数、aten还是其他自定义op，以及返回/alias/归约/图路径；本批只生产Host接口，不把这些调用当Device实现已穷尽。

## Backend能力声明与实际确定性

固定原生v0.32的init_attn_backend在选定KV组/层循环中，VLLM_BATCH_INVARIANT开启而backend.supports_batch_invariance()为False时拒绝。所读普通AscendAttentionBackend返回True；UT还枚举其他backend及310P/C8子类期待True，本次未执行且未逐个读取其全部实现。

能力flag是这条初始化门禁，不是每个shape、量化/草稿/图、数学结果或整个310P功能支持证明。硬件/模型范围仍遵守本卡主指南表，不因继承返回True而扩到310P。特别是950上的Qwen3.5-35B-A3B仍按主表的不支持项保留。

## 中文资料与安装排障

batch_invariance.po的53条有效非空译文已全文对照英文，0obsolete/fuzzy且msgid均匹配；PO覆盖其中部分表行/叙述，不能仅靠译文条目数推导完整模型表或代码示例。来源的tested/verified为上游声明，不是本环境新复核事件，既有stable/平台范围保留且不新增verified。

两阶段安装的skip、失败日志与completed判据见[安装完成但算子不可用](../../runbooks/runtime/vllm_ascend_batch_invariant_install_false_success.md)。Dockerfile与Dockerfile.a5所读stanza仅在构建RUN中export开关，不能替代运行期设置。所有注册、构建、CPU/NPU测试与模型对照本次均未执行。


## Triton Device路径：固定tile与完整框架接受面分开

补读batch_invariant下matmul/mean/rmsnorm/softmax四个完整Python程序结构及三份算子文档，仍未运行NPU。matmul_persistent是二维输出grid、固定128×128×64 tile，载入显式FP32、allow_tf32=False、可融合一维bias；名字persistent不意味着固定1D常驻grid。linear_persistent则接受weight[N,K]，不物化转置，固定vectorcore//2程序遍历输出tile，但M/N启发式会改变BLOCK_M/N，BLOCK_K通常256、FP32为128。不能由同名batch_invariant推出两者tile策略、舍入或跨batch bit-exact已证明。

mm/bmm/addmm/matmul包装器只实现所列2D/3D/4D组合，bmm用Python循环后stack，4D按实际batch×heads展平；没有任意PyTorch广播或所有空batch等价合同。addmm仅alpha=beta=1且1D input时融合bias，其余再做scale/add；linear bias也在GEMM后另加。复制contiguous、reshape、Python循环与额外launch都计入真实性能，不由kernel时间外推服务收益。

加权RMS采用FP32两遍1024列chunk归约/回写，weight必需、输入和weight连续化，grid按row数与vectorcore上界。它不是[Q-RMS融合指南](vllm_ascend_triton_norm_rope_activation_contract.md)中无weight的另一实现。softmax包装器是Torch amax→exp→sum→divide链，dtype参数还兼容bool True转float；全-inf/NaN、溢出、特殊dtype和每层替换的完整确定性需测试，不能因稳定softmax形式就宣布所有异常值有限。

mean_dim先按dtype转换输入，默认FP16；dtype=None才保留浮点输入或将整数升FP32。mean_batch_invariant自身默认FP16却assert仅None/FP32，显式单dim分支调用mean_dim时没有转发dtype，因此即使包装器传FP32也可能使用内层FP16默认。多dim改走torch.sum(fp32)并除元素数；空dim列表表示全维度。源码接受/转换与文档泛称“FP32确定性”分别解释，不用精度容差测试替代不同batch下逐token一致性测量。

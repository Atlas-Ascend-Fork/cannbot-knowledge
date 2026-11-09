---
type: Guide
title: vLLM Ascend 启动预热：JIT 键覆盖、后台线程与捕获时序
description: 按 rejection、penalty、RMS、indexer 和 DSpark 核对有限 JIT 变体，区分早期线程与正式预热，检查 NZ 初始化、超时和真实冷启动收益。
aliases:
- start_early_kernel_warmup
- join_early_kernel_warmup
- warm_nz_format_cast
- collect_warmup_rejection_block_sizes
- collect_triton_rms_warmup_block_m_values
- JitWarmupRegistry AscendTritonJitKernel
- register_v1_sampling_warmup _prune_unlaunchable_registrations
tags:
- task.implementation
- task.optimization
- topic.graph_execution
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/warmup/kernel_warmup.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/warmup/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/warmup/dspark_swa_indices_warmup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/warmup/early_kernel_warmup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/warmup/indexer_triton_warmup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/warmup/nz_warmup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/warmup/penalties_triton_warmup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/warmup/rejection_sampler_triton_warmup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/warmup/rms_triton_warmup.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/model_executor/warmup/kernel_warmup.py
  role: primary
created_at: '2026-11-03T04:57:14Z'
updated_at: '2026-11-03T06:39:58Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 启动预热：JIT 键覆盖、后台线程与捕获时序

## 来源与启动阶段

固定 Main ceac1a2 的 warmup 包九个 Python 文件完整读取，未导入或执行上游。__init__ 只导出 kernel_warmup；正式入口受 HAS_TRITON 门禁，依次调用 rejection_sampler、penalties、rms、indexer、dspark_swa_indices 并记录耗时。它本身没有 try/except 吞掉各项失败，不能把早期线程中的容错机制套用到正式预热。

早期 kernel 线程由 ascend_warmup_config.enable_early_kernel_warmup 控制，设计目的是与权重 I/O 重叠。start 先在主线程完成相关 import，避免注册期间并发遍历 sys.modules；随后创建仅持配置、无 runner 的 shim，在线程设置相同 NPU device。MRv2 分支明确不做 V1 rejection/penalty，只尝试 RMS。正式 kernel_warmup 本函数没有同样的 MRv2 skip 判断；其是否被调用须继续沿 worker 调用方核对，不能只凭早期模块注释推导所有 runner 的顺序。

## 预热应覆盖 constexpr，而非穷举请求数

| 项目 | 固定实现覆盖策略与边界 |
| --- | --- |
| Rejection | 按 cal_grid_and_block_size 的不同 BLOCK_SIZE 选代表 batch，并确保最大 batch；不是照 capture sizes 逐项重复。prepare_inputs 的请求数不专门化，仅一次；expand 覆盖 int32/FP32，greedy 覆盖 is_greedy=None/张量。 |
| Draft probability | ngram/ngram_gpu 或 PP<=1 只暖 NO_DRAFT_PROBS=True；模型 draft 且 PP>1 覆盖有/无概率两种。block verify 要开关且 spec len>=3；entropy 依当前配置决定 ori_target_probs 与阈值专门化。 |
| Penalty | 本地 vocab=max(1,全局vocab//TP)，FP32 logits，历史长度 min(257,max_batched_tokens)，末位放 vocab 哨兵；覆盖跨256计数块，但上限不足时不声称跨块已经覆盖。 |
| RMS | 正式阶段仅 AscendDSABackend 使用时预热；early 用 assume_used=True。head_dim>2048 跳过。BLOCK_M 只需1/2/4/8/16，shape 用 BLOCK_M×vectorcores、head_num=1，epsilon 从模型读。 |
| V4.1 indexer | 仅 is_deepseek_v41，实际层 compress_ratios 去零去重。sort 预算128KiB、8缓冲、topk补2幂推导 max_block_rows；挑跨每个 tile 桶的 token 数，并按 max_batched_tokens 截止。 |
| DSpark SWA | 要 drafter、DSA metadata builder、device-metadata 开启与支持的 block/table width；滑窗用 cropped clone 宽度，其他用该 KV group 实际表宽。query count、index width、持久输出和 int32 元数据都要与运行时一致。 |

DSpark 的零 dummy 元数据只触发编译和容量 grid，没有执行实际 gather/store，不能当索引数值测试。rejection 的小 vocab dummy 以专门化标志为目的，不证明真实全词表内存或每个目标模型的概率正确。配置、dtype、设备架构、编译器或 constexpr 改变时需重新确认 cache 命中，不能根据一次“warmup complete”推所有运行时变体无 JIT。

## 线程状态、join 与 NZ 初始化

early 状态是进程全局 started/thread/done。获取不到 current config 时不标 started，允许稍后启动；一旦标记后启动失败，源码没有复位重试逻辑。线程内单项失败只警告并继续，正式预热会补编译。join 避开当前线程，最多等待600秒，超时仅警告，没有取消后台任务；done 也不表示每项成功。内存 profiling 前是否真的 join 完成，应看调用方和线程状态，不把函数返回当完成屏障。

NZ 单独由 enable_early_nz_warmup 控制，使用256×256 int8 scratch 调 maybe_trans_nz 并 synchronize，线程绑定当前设备。_NZ_WARMED 在操作前就置真，异常后不会自动重试；thread_started 同样是全局一次性标志。它的 join 也是600秒警告式等待。源码注释中的首次15–19秒是来源经验，非本环境观测，也不是任意模型/版本都能节省的时间。

## 给适配与性能 Agent 的验收信号

分别记录权重 I/O、早期线程启动/结束、正式各项 warmup、内存 profiling、capture 和 ready 时间；比较开关前后的进程到 ready、首次请求和稳态时延。必须报告缓存冷/热、编译器、模型/量化、TP/PP/spec配置及所有 ranks，避免把编译缓存复用误算为代码优化。改变运行时 shape 后观察是否再次 JIT；异常、join 超时或只暖未用 RMS 时不能声称收益。


## 3164 版本迁移：声明式 JIT 注册取代脚本清单

固定增量 `ceac1a2→3164adc8fe75892fbf7f99f524bb72fddf1e6efd`；完整变化与必要上下文静态读取，不标目标全文FULL，未执行upstream/JIT/NPU/图/通信/性能测试。

该提交删除early/DSpark/indexer/penalty/rejection/RMS六个独立warmup脚本，kernel_warmup改为统一JitWarmupRegistry。删除的是旧实现路径，历史ceac知识仍保留；不能在新版本继续按文件名调用，也不能将脚本删除解释为完全不预热。

AscendTritonJitKernel在Runner模型构造的registry窗口声明需求，统一展开每kernel/key pair，在ACL capture前编译。v1 sampling显式注册penalties/bincount/prepare_inputs/rejection，窗口外register是no-op，避免v2平白编译v1栈。DSpark需在input batch与draft group完成后late register：只对DSAMetadataBuilder的device-metadata路径、存在index_width的组，table宽从sliding adapter或实际group table取，不取尚为None的builder.block_table。

编译前prune非Ascend wrapper注册，规避Native RejectionSampler带入CUDA-only核；这是具体版本兼容策略，不是证明任意未知注册无关。HAS_TRITON=False或kernel_config.enable_jit_warmup=False直接返回，registry空时warn并允许lazy compile；warmup异常记录后重新抛出，不吞成成功。启动日志与registry数量不能替代目标key确实覆盖capture shapes及compile cache隔离的验证。

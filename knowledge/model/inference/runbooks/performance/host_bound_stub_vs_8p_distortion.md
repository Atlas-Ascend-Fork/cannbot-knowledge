---
{
  "type": "Runbook",
  "title": "vllm-ascend host bound 优化中单卡打桩（DSL stub）与 8 卡真实 profiling 的分布失真判别",
  "description": "host bound 优化用单卡打桩容器（kernel_shim 把 DSL 算子 stub 成零张量）测 host 开销时，优化优先级必须以 8 卡真实 profiling 分布为准；本卡给出打桩环境的可用/不可用边界。",
  "tags": [
    "task.debugging",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# vllm-ascend host bound 优化中单卡打桩（DSL stub）与 8 卡真实 profiling 的分布失真判别

- knowledge_form: diagnostic_rule | route: inference | area: performance

## 适用场景

适用于在 vllm-ascend 上做 DSV4.1 host bound 优化、需要用"单卡/少卡打桩容器（kernel_shim stub 掉 NPU 算子）"替代 8 卡真机来迭代 host 侧逻辑的工程师：何时可以信打桩数据、何时必须回 8 卡真机定值，以及如何识别打桩分布与真实 profiling 的系统性偏差。

## 触发与观测

- 触发：打桩环境的 host_cost_probe 分布与 8 卡真实 profiling 的优先级结论矛盾，用户要求以 profiling 分布为准（见机制与判别工件的问题描述，45bbc5c8）。

## 探针与操作

实际执行的探针链（45bbc5c8 会话，远程容器 + cProfile/torch profiler/trace_view 解析）：

1. 打桩容器可行性探针：P0-1 用 8 进程共享单卡验证 set_device+算子全部成功（9475）；TP=2 单卡打桩最小 vLLM init 跑 4 steps（per_token ~15ms），并以 `metadata build: calls>0`（worker 落盘 build-<pid>.txt）作为测量有效判据（18163/18164）。
2. 打桩 prof 归因：cProfile 拆 _prepare_inputs/_build_attention_metadata/triton jit run（27870/27871）。
3. 1104 对照：解析 8 卡真实 profiling trace_view.json 中 private_circle_pool/build_c2_decode_metadata/_apply_dsv4_rope/_store_standard_swa_kv/combine_hidden_states 等函数的调用数与总时长（35140/35141）。
4. 打桩增强版（SIM_DSL）tottime 分布读取（51310/51311）。
5. 单项量化：build_private_circle_step_vectors / private_circle_step_vector_to_device 在 1104 的每次耗时与在 _build_attention_metadata 窗口内的出现次数（43553/43554）。

## 机制与判别

方法论修正工件（优化 log 条目原文，读自 ，已 git commit；账本机制片段：，映射存留来源结论）：

```
## 2026-11-09 · 方法论修正：优化优先级必须以 profiling 分布为准

> **问题**：之前用打桩环境的 host_cost_probe 分布（prepare_inputs 最大 4740~6602us）制定优先级，
> 但**这是打桩失真的结果**。用户指出：profiling(1104) 里 `_build_attention_metadata` 才是大头。

### 失真根因
- `_build_attention_metadata` 5.03ms(1104) 的构成 = **submit() 2.35ms(DSL AICpu launch 链) + 6× group build ~2.3ms**
- 这些是**真实 DSL 算子下发的 host 开销**（构造 launch 参数、DSL 调度、getRawStream）
- **kernel_shim 把 DSL 算子 stub 成零张量快速返回** → 打桩下 build 的 host 成本被严重低估
- 而 `_prepare_inputs` 的 numpy/triton 逻辑（private_circle_ring_table 等）打桩下照跑 → 相对变大
- → **打桩环境 host 分布失真：build 被低估、prepare 被高估**

### 修正后的优化优先级（以 1104 profiling 为准，聚焦单 batch）

| 优先级 | 项 | 1104 耗时 | 打桩可测性 |
|---|---|---|---|
| P0 | `_build_attention_metadata`.submit() DSL launch 链 | **2.35ms** | ❌ stub 不可测 → 需 8P |
| P1 | `_build_attention_metadata`.6× group build | **2.3ms** | ⚠️ 纯 host 记账可测、DSL 调用不可 |
| P2 | `_prepare_inputs` | 1.58ms | ✅ 打桩相对可测 |
| P3 | `_update_states`/`_preprocess`/`compute_logits`/`release` | <1ms | ✅ |

### 打桩环境的正确用法（修正）
1. **不能测 build 绝对耗时**（DSL stub 低估）——优化收益需 8P 真机确认
2. **可测**：build 内纯 host 记账的相对 A/B + 重构等价性（digest 三道门禁）
3. **可测**：prepare_inputs 的 numpy/triton 部分相对 A/B
```

## 验证信号

来源结论（方法论结论与打桩环境可用性前置）：

方法论结论（已录入优化 log 并 git commit）：优化优先级必须以 1104 真实分布为准——P0 submit() DSL launch 链 2.35ms（打桩不可测、需 8P 真机）、P1 6×group build 2.3ms（纯 host 记账可测、DSL 调用不可）、P2 _prepare_inputs 1.58ms（打桩相对可测）、P3 update_states/preprocess/compute_logits/release <1ms。打桩环境的正确用法：不能测 build 绝对耗时；可测 build 内纯 host 记账的相对 A/B 与重构等价性（digest 三道门禁）；可测 prepare_inputs 的 numpy/triton 部分相对 A/B。打桩环境可用性前置：TP=2 单卡打桩 4 steps 全过（per_token ~15ms）、8 进程共享单卡全部 set_device+算子成功（P0-1 通过）；主进程 build 统计 calls=0 是因为 build 在 worker 子进程执行、统计落盘在 build-<pid>.txt（主进程打屏口径无效，需以 worker 落盘为准）。


客观信号清单：优化 log 落盘 + git commit（48538/48539）。

## 适用与失效边界

适用：host bound 优化的优先级制定、打桩环境的能力边界声明、DSL launch 开销的归因口径。失效/不适用：打桩不能测 build 内 DSL 算子下发的绝对 host 耗时（stub 成零张量快速返回）——P0 级优化收益必须 8P 真机定值；打桩主进程打屏的 build 统计恒为 0（build 在 worker 子进程），必须以 worker 落盘 build-<pid>.txt 为准；本卡数字为该次 DSV4.1 单 batch 负载的实测分布，跨负载不可直接搬用，应重走对账流程。

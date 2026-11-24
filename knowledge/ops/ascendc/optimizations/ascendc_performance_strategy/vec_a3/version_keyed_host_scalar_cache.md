---
type: Optimization
title: version-keyed host 标量缓存（device 标量的跨调用记忆化，D2H 仅冷失效时发生）
description: 以tensor对象身份和version为键缓存host标量，避免值未变化时每次调用都执行D2H读取。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-version-keyed-host-scalar-cache.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：version-keyed host 标量缓存（device 标量的跨调用记忆化，D2H 仅冷失效时发生）

> 单一优化点：算子 host 层需要读取 device 上的 fp32 标量输入（如优化器的 `state_steps`/`grad_scale`/`found_inf`）才能构造 kernel 参数时，不要每次调用都做 D2H 同步读——用 `TensorImpl*`（对象身份）+ `_version` 计数器做键缓存读到的值。任何 in-place 修改必然 bump version → 缓存自动失效重读；跨调用不变的标量（训练循环中两次 step 之间、评测迭代之间）全部命中，**热路径零 D2H、零同步**。

**融合说明**：本卡吸收早期轮次的负面知识（kernel 内裸读 GM 标量的间歇性 stale 读、MTE2 队列读的崩溃、`intrusive_ptr::reclaim` 堆损坏）作为正确性红线的反例。

---

## 1. 原理

- **调用模式假设**：训练/推理循环中，标量状态 tensor（optimizer 的 step 计数、缩放因子、标志位）在两次算子调用之间通常不变（或仅通过 in-place op 更新）。逐调用 D2H（`.cpu().item()`）每次付出 30-100us 的 pageable 拷贝 + 流同步税。
- **版本计数器保证正确性**：PyTorch 每个 `TensorImpl` 携带 `version_counter`，任何 in-place 写（`add_`/`fill_`/`copy_`）都会递增它。因此「同一 TensorImpl + 同一 version ⇒ 值未变」是框架级不变量，缓存不可能读到陈旧值。
- **对象身份防地址复用（ABA）**：缓存条目持有一份 `at::Tensor` 值拷贝（refcount +1），被缓存的 `TensorImpl` 永不析构 ⇒ 其地址不会被新 tensor 复用 ⇒ 键永远无歧义。持有一个 0-dim tensor 的成本是 ~指针级，缓存设上限（如 128）溢出清空即可。
- 实测（910B3）：热路径命中后单 case host 开销从 ~157us 降至 ~35us；与「标量参数直传 kernel（消除 tiling H2D）」叠加后，10 case geo speedup 从 2.17x 提到 9.05x（aten 原生基线口径）。

## 2. 性能问题模式

满足以下模式时考虑本策略：

1. host 层为构造 kernel 参数/分支判断，必须知道某个 **device 上的标量 tensor** 的值（`.cpu().item()` / `ReadScalar` 形态）；
2. 该标量在**调用之间语义上可变**（不能写成编译期常量或调用参数），但**单次调用内只读一次、且跨调用经常不变**（优化器 step、动态缩放因子、跳过标志）；
3. profiling 显示端到端时间被这次 D2H 同步主导（小/中 shape case 的 kernel 时间 ≪ elapsed）。

**profiling 特征**：`elapsed_us - t_hw_us` 每次调用恒定 ~50-100us 与 shape 无关；msprof 里 kernel 本身 <22us。

**不适用**：
- 标量每次调用必然改变且无 in-place 语义保障的场合（缓存永远 miss，白付缓存开销）；
- 标量本来就在 CPU 上（直接读即可，无需缓存）；
- 并发多线程写同一 tensor 的场景（version 仍正确，但读-判-用之间有 TOCTOU：读到的值可能与后续 kernel 看到的 tensor 内容不一致——需要在调用入口持流锁）。

## 3. 正确性红线

- **键必须同时含对象身份与 version**：只用地址做键会被 tensor 释放-复用打穿（ABA）；条目必须**持有 tensor 引用**使地址不可复用。
- **禁止 `c10::intrusive_ptr<TensorImpl>::reclaim(impl)`**：reclaim 是"接管裸指针所有权"，对已被 Tensor 持有的 impl 调用会 double free（实测 `corrupted double-linked list` 堆损坏崩溃）。正确做法是条目存 `at::Tensor` 值。
- **version API**：`impl->version_counter().current_version()`（不是 `impl->version()`）。
- **不要试图把读取下沉到 kernel 内裸读 GM 标量来替代本策略**（910B3 / CANN 9.0.0 / bisheng -xasc 实测）：
  - `(__gm__ float*)ptr[0]` 与 `volatile` 读均出现**间歇性 stale 值**（单跑复现不了、顺序跑间歇触发；表现为仅依赖该标量的输出（如 bias-correction 项）错误，其余输出全部正确）；
  - 用 MTE2 队列（DataCopyPad 32B + DeQue 后 GetValue）读：在 `Init()` 内做会 507035 崩溃（AllocTensor 先于 InitBuffer）；挪到 Process 开头仍崩溃；
  - 单标量 4B 的 DataCopyPad 违反 MTE 32B 最小事务。
  - host 读 + 标量 kernel 参数 100% 稳定。
- 缓存需要 mutex 保护（torch op 可能并发）。

## 4. 泛化条件

**适用**：
- 任何「host 需要读 device 标量才能 launch」的算子（优化器类 `fused_adamw`/`adam`/`sgd`、loss scale 系、found_inf/skip 类标志、动态阈值）；
- 评测/训练热循环中该标量跨调用不变或低频变化；
- 已把 tiling/超参标量化为 kernel 参数（配合 host-reduce-sync-gate），D2H 是剩余唯一同步点。

**不适用**：
- 标量由本算子每次调用前被调用方原地重写（永远 miss）；
- CPU 标量输入；
- 需要 zero-copy 强一致（写后立刻读的流水）场景。

## 5. 实施步骤

1. 定位 host 层逐调用的 `tensor.cpu().item()`（或等价 ReadScalar）点，确认该 tensor 是 0-dim/1 元素标量且调用间低频变化；
2. 写缓存（C++，op 入口处）：
   ```cpp
   struct Entry { at::Tensor keepAlive; uint32_t version; float value; };
   std::mutex mu; std::unordered_map<const void*, Entry> cache;  // key = TensorImpl*
   float ReadScalarCached(const at::Tensor &t) {
     auto *impl = t.unsafeGetTensorImpl();
     uint32_t ver = impl->version_counter().current_version();
     { std::lock_guard<std::mutex> l(mu);
       auto it = cache.find(impl);
       if (it != cache.end() && it->second.version == ver) return it->second.value; }
     float v = t.cpu().item<float>();               // D2H only on miss
     std::lock_guard<std::mutex> l(mu);
     if (cache.size() >= 128) cache.clear();
     cache[impl] = {t, ver, v};
     return v;
   }
   ```
3. 把所有逐组读取替换为 `ReadScalarCached`；多组列表各自读（不必 stack）；
4. 验证失效语义：对同一 tensor 做 `fill_(新值)` 后再调用，输出必须反映新值（version bump → miss → 重读）；
5. 全量精度 ×3（间歇性问题必须多次跑）+ 双源计时回归。

## 6. LLM 前置问题（实施前自检）

- 这个标量的所有可能修改路径都是 in-place op（会 bump `_version`）吗？有没有绕过 version 的写法（C 层裸指针写）？
- 缓存条目是否用 `at::Tensor` 持有（而不是 intrusive_ptr::reclaim）？
- 是否多线程可达？加锁了吗？
- 该标量是不是每次调用都变（如迭代计数每轮 +1 的 step）——是的话本策略只剩"每轮 miss"的等价开销，需评估是否仍值得（组数多时批量读仍优于逐组读）。

## 7. 验收标准

- build + 精度全过；实测（910B3）：热路径命中后单 case host 开销从 ~157us 降至 ~35us；与「标量参数直传 kernel（消除 tiling H2D）」叠加后，10 case geo speedup 从 2.17x 提到 9.05x（aten 原生基线口径）。失效语义验证：对同一 tensor 做 `fill_(新值)` 后再调用，输出必须反映新值；全量精度 ×3（间歇性问题必须多次跑）+ 双源计时回归。

## 检索卡（短卡）

动作：以tensor对象身份和version为键缓存host标量，避免值未变化时每次调用都执行D2H读取。
适用：host需读取device标量才能launch，且该0维或单元素tensor在调用间低频变化。
限制：缓存键必须同时包含对象身份和version；条目须持有tensor引用，禁止仅用地址键。
范围：算子host层读取0维或单元素device标量的路径。
检索词：version-keyed、host标量缓存、device标量、D2H、cpu().item()、ReadScalar、ABA
机会：host为构造kernel参数或判断分支，每次调用均通过cpu().item()或ReadScalar读取device标量。

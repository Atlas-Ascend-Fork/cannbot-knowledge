---
{
  "type": "Runbook",
  "title": "GE 执行图中间态 FreeMemory 双重释放致非确定性 SIGBUS：WirePendingFrees 按 root alloc 去重并关闭图内中间态 frees 改由 executor 池回收",
  "description": "gert::kernel::FreeMemory 内虚函数调用跳转 0x1 造成非确定性 SIGBUS（gdb 栈 #0 0x1 → FreeMemory → SequentialExecuteWithCallback）。根因一：alias/view 结果可为同一 root AllocMemory 挂多个 FreeMemory，第二次 Free 在已析构的 GertMemBlock 上调用；根因二：fallback 输出内存由 torch 侧持有，图内 FreeMemory 与 FreeArgsGuarder 双重释放（torch 引用计数/GC 时机决定谁先，故非确定性）。仅去掉 fallback 图内 frees 会引入异步 UAF（不可采用）。最终修复：WirePendingFrees 用 freed_allocs 集合去重 + 关闭图内中间态 frees 改由 executor 池回收；落地后 rerun9 无宿主崩溃、记录到271次 AF kernel launch，运行仍以507057结束。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "910"
  ]
}
---
# GE 执行图中间态 FreeMemory 双重释放致非确定性 SIGBUS：WirePendingFrees 按 root alloc 去重并关闭图内中间态 frees 改由 executor 池回收

## 适用场景

- 框架/栈：GE 执行图构建（fx_converter `src/exe_graph/execute_graph_builder.cc` 的 `WirePendingFrees`/`WireFreeIntermediateMemory`）+ gert 运行时（`ge_new/runtime/v2/kernel/memory/memory_kernel.cc` 的 `FreeMemory`，本地构建 libgert.so）+ torch fallback 降级路径（`torch_fallback_op_lowering.cc` 的 `mem_to_free` 挂接）。
- 平台：Atlas 910B3（rt2 模式，ModelV2Runner），动态 T5 + AutoFuse 工作负载。
- 触发面：图内中间态（AllocMemory）挂 FreeMemory 的构建逻辑，以及 fallback 输出内存的双重所有者（torch bridge 侧 + 图内 FreeMemory）。
- 缺失信息：GE 提交记录为本地工作区修改（未上游）；executor 池回收的精确实现位置未在轨迹内阅读。

## 触发与观测

- 故障（事件 2136，gdb 批处理捕获的原始栈）：
  ```
  Thread 1 "python" received signal SIGBUS, Bus error.
  #0  0x0000000000000001 in ?? ()
  #1  ... in gert::kernel::FreeMemory(gert::KernelContext*) () from .../lib64/libgert.so
  #2  ... in SequentialExecuteWithCallback () from .../lib64/libgert.so
  #3  ... in ModelV2Runner::Execute(...) () from .../fx_converter/lib/libmrt_fx_converter.so
  ```
  SIGBUS **非确定性**复现（不同 run 崩溃点/形态不同），机制判读（事件 2194）：`GertTensorData::Free() → gert_mem_block_->Free()`（虚函数调用）→ mem block 对象已损坏/被释放 → 跳转 0x1，属双重释放或提前释放。
- FreeMemDiag 探针（事件 2384 注入到 `memory_kernel.cc` 的原文）：

```
  fprintf(stderr, "[FreeMemDiag] addr=0x%llx size=%llu stream=%ld this=%p memblock=%p\n",
          static_cast<unsigned long long>(reinterpret_cast<uintptr_t>(gert_tensor_data->GetAddr())),
          static_cast<unsigned long long>(gert_tensor_data->GetSize()),
          static_cast<long>(gert_tensor_data->GetStreamId()),
          static_cast<void *>(gert_tensor_data),
          static_cast<void *>(gert_tensor_data->GetGertMemBlock()));
  fflush(stderr);
  return gert_tensor_data->Free();
```

## 探针与操作

判别实验（事件 2252，TEMP EXPERIMENT，写入 `torch_fallback_op_lowering.cc`）：把 fallback 输出的 `result->mem_to_free = nullptr`（fallback 输出内存由 bridge 侧分配、经 FreeArgsGuarder/EagerArgsHandler 释放，不再挂图内 FreeMemory）。修复前挂接代码（事件 2250 原文）：`result->mem_to_free = stage.source_alloc != nullptr ? stage.source_alloc : stage.alloc;`（多输出路径同理，见事件 2250 第二段）。

实验结果（事件 2258/2261）：SIGBUS 消失（进程改为以 `RuntimeError: npuSynchronizeDevice ... SUSPECT REMOTE ERROR, error code is 507057` 收敛），948 个 FreeMemDiag 正常打印；但该实验改动随后被还原（事件 2284）——它暴露了另一半真相（见边界）。

最终修复 1（事件 2928，写入 `execute_graph_builder.cc` 的原文，已用 reader 复核）：

```
void WirePendingFrees(std::unordered_map<std::string, PendingFree> *pending_frees, BuiltExecuteGraph *built,
                      std::vector<ge::FastNode *> *kernel_nodes, ge::FastNode *last_launch) {
  // One in-graph FreeMemory per AllocMemory node. Alias/view results can add the
  // SAME root alloc under several tags; a second FreeMemory on an already-freed
  // block crashes in GertMemBlock::Free (dangling vtable, nondeterministic
  // SIGBUS) once the first free has destroyed the block.
  std::unordered_set<ge::FastNode *> freed_allocs;
  for (auto &kv : *pending_frees) {
    PendingFree &pending = kv.second;
    if (pending.alloc_mem == nullptr || !freed_allocs.insert(pending.alloc_mem).second) {
      continue;
    }
```

最终修复 2（事件 2948/2951，写入 `execute_graph_builder.cc` 的原文）：

```
    // TEMP: intermediate in-graph frees disabled — the first such free crashes in
    // GertMemBlock::Free on an already-released block (dangling vtable SIGBUS);
    // memory is reclaimed by the executor pool / graph teardown instead.
    (void)after;
    (void)built;
    (void)kernel_nodes;
    continue;
```

即去重之外整体关闭图内中间态 frees（挂在 WireFreeIntermediateMemory 之前短路），内存改由 executor 池/图销毁回收。

## 机制与判别

- 结论：gert::kernel::FreeMemory 的虚函数调用跳转 0x1 导致非确定性 SIGBUS（gdb 栈：#0 0x1、#1 gert::kernel::FreeMemory、#2 SequentialExecuteWithCallback、#3 ModelV2Runner::Execute）；alias/view 结果可为同一 root AllocMemory 挂多个 FreeMemory，第二次 Free 在已析构的 GertMemBlock 上做虚函数调用。
- 双重所有者判别（事件 2231/2248）：fallback 算子输出由 torch 侧持有（bridge 分配），converter 又为其挂图内 FreeMemory → torch GC/引用计数释放 + 图内释放 = 双重释放；释放先后由 torch 引用计数/GC 时机决定 → 完美解释非确定性（第二个释放者拿到已析构的 GertMemBlock → 虚表垃圾 → SIGBUS）。
- 结论：把 fallback 输出的 mem_to_free 置空（不挂图内 FreeMemory）后 SIGBUS 消失、948 个 FreeMemory 正常执行，支持双重释放假设，但未独立证明全部所有权关系；但该做法会引入异步 UAF（FreeArgsGuarder 在 host 侧 launch 后立即释放 torch 张量而设备侧 kernel 未执行 → MTE），不能作为最终修复，实验改动已还原。
- 结论：最终修复为 WirePendingFrees 以 freed_allocs 集合对 AllocMemory 去重（每个 alloc 只挂一个 FreeMemory），并关闭图内中间态 frees 改由 executor 池/图销毁回收；该修复与 AdoptedDrainGuard 入口同步尝试（该尝试未闭合本次图执行与drain的顺序）等共同落地后，rerun9 无宿主崩溃、271 个 AF kernel 全部 launch。
- 未验证推断：去重（事件 2928）与关闭 frees（事件 2948）两步的独立贡献未分别验证（最终 rerun9 为联合状态）；"executor 池回收"的内存正确性依赖 GE 侧既有机制，轨迹内仅观察到该次联合运行无宿主崩溃及271次launch记录；这不证明全部kernel已完成或内存生命周期正确。

## 验证信号

- 事件 2258（判别实验，单次 gdb 运行）：无 SIGBUS，进程以 npuSynchronizeDevice RuntimeError 收敛（SUSPECT REMOTE ERROR 507057）——支持双重释放假设，设备错误仍存在。
- 事件 2261：FreeMemDiag 计 948 条正常执行（记录了这些FreeMemory路径执行，不能外推整体回收正确）。
- 事件 3212（rerun9，最终联合状态）：`grep -ac "AFLaunchDiag"` = 271（271 个 AF kernel 全部 launch），aicore error `pc start: 0x124400333e28` 恒定（仍有设备错误；是否与释放路径独立需继续定位）。
- 事件 3209（rerun9）：进程以 Python 异常（SUSPECT REMOTE ERROR @ npuSynchronizeDevice）结束，无 Bus error/core dumped。
- 证据等级：910B3 + CANN 9.2.0 + 私有 fxrt/GE 构建的运行日志观测；判别实验单次、最终状态单次（rerun9）；**混杂变量**——最终 rerun9 同时包含 AdoptedDrainGuard 入口同步尝试（该尝试未闭合本次图执行与drain的顺序）（事件 2705）与 bridge 异常提取（事件 2564），无宿主崩溃不能单独归因本修复。

## 适用与失效边界

- 适用：GE 执行图对中间态挂 FreeMemory + alias/view 复用 root alloc 的构建逻辑；fallback 输出内存所有权跨 torch/GE 双侧的场景；症状为非确定性 SIGBUS 于 `gert::kernel::FreeMemory`（跳转 0x1）。
- 明确不可采用的路线：仅置空 `mem_to_free`（去掉 fallback 图内 frees）——实测引入异步 UAF（host 侧释放早于设备侧消费 → MTE，事件 2283）；FreeMemDiag 等 fprintf 探针仅为诊断用，不应留驻生产路径。
- 失效边界：整体关闭图内中间态 frees 依赖 executor 池/图销毁回收，若上游 GE 不提供等价回收机制则不可照搬；去重逻辑按 `ge::FastNode*` 指针等值判重，若 alloc 节点被重建（指针变化）判重失效。
- 回退条件：若 GE 侧修复 GertMemBlock 生命期（Free 幂等/延迟析构），可恢复图内 frees + 去重的最小方案；PyErr/FreeMemDiag 类探针可随诊断结束移除。

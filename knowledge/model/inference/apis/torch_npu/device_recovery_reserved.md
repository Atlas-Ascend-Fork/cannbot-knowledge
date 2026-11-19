---
type: API
title: NPU设备恢复预留接口：UCE分类、停止与重建
description: 保留暂不支持提示及产品表冲突，区分资源重建、脏Tensor与训练状态恢复；补csrc绑定层、分配器块安全账与生成wrapper检查面。
tags:
- task.lookup
- task.debugging
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-check_uce_in_memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-check_uce_in_memory.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-check_uce_in_memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-restart_device.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-restart_device.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-restart_device.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-stop_device.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-stop_device.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-stop_device.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_recovery.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_recovery.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPURecoveryBindings.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPURecoveryBindings.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPURecovery.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPURecovery.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPURecovery.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPURecovery.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/NPURecovery.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/InitNpuBindings.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/custom_functions.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/npu/test_recovery.py
  role: implementation
created_at: '2026-11-09T19:31:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# NPU设备恢复预留接口：UCE分类、停止与重建

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 文档状态与调用风险

check_uce_in_memory、stop_device和restart_device两版本均有“预留、暂不支持”Notice，主线又列A2/A3/950DT等产品支持表。由于来源内部矛盾，本卡保持draft，记录接口意图而不提供已获支持的恢复操作配方。Python实现存在不能解决产品/发行支持承诺。

check_uce_in_memory(device_id)文档返回0无UCE、1非PyTorch内存、2PyTorch临时内存、3PyTorch常驻内存，要求开启内存复用、不能配置PYTORCH_NO_NPU_MEMORY_CACHING=1。类别0也不是设备、模型数值或分布式全链路健康证明。

stop_device(device_id)意图停止并清理未执行计算，后续该卡计算报错，文档结果0成功/1失败。固定Python包装还置force-stop异常标志并停止现有NPU ProcessGroup watchdog；不是纯查询。

## restart的参数与副作用

发布文档拼写rebuild_all_resource=False且称预留无功能，发布实际包装已用复数`rebuild_all_resources`并实现标脏Tensor、开unsafe检查和恢复流。主线文档/包装为`restart_device(device_id, rebuild_all_resources=False, disable_tensor_unsafe_check=False)`；第二项True恢复流并默认标脏现存NPU Tensor，第三项True才跳过标脏，且仅在资源重建时有效。**跳过检查不证明原Tensor数据正确**。

两固定包装都继续调用底层restart、清force-stop、清PG workmeta并恢复watchdog；未停止设备也可请求此接口的描述不能变成每步训练常规操作。恢复设备状态不恢复模型、优化器、RNG、数据进度、所有rank一致性或检查点，未执行停止、重启、恢复或故障注入。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-check_uce_in_memory.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-check_uce_in_memory.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-check_uce_in_memory.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-restart_device.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-restart_device.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-restart_device.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-stop_device.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-stop_device.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-stop_device.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_recovery.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_recovery.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/utils.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)（implementation）

## 恢复链的 csrc 绑定层与分配器块安全账

本节覆盖 Python 包装之下的 csrc 层，依据两 pin `torch_npu/csrc/core/npu/NPURecovery.{h,cpp}`、主线 `NPURecoveryBindings.{h,cpp}`，以及 `InitNpuBindings.cpp`/`NPUCachingAllocator.cpp`/torchnpugen 的定向行段。文件组织两版不同、绑定面相同：发布把 `bind_npu_recovery_functions` 内联在 `NPURecovery.cpp` 末尾（:110-134，`#ifndef BUILD_LIBTORCH`），主线拆到 `core/npu/NPURecoveryBindings.cpp`（:1-29，同样 `#ifndef BUILD_LIBTORCH`）并由 `InitNpuBindings.cpp:271` 统一挂载；六个 `m.def` lambda 体两 pin 语义一致（发布 `_get` 一处缩进不同）。主线另有 `csrc/npu/NPURecovery.h`（13 行）仅是 `GetRecoveryLogger`/`TORCH_NPU_RECOVERY_LOGI` 双宏日志头，无逻辑；两 pin `core/npu/NPURecovery.{h,cpp}` 的 check/update 重载集一致。

六个 `torch_npu._C` 绑定的实际落点：

| 绑定 | csrc 落点 | 失败/版本边界 |
| --- | --- | --- |
| `_check_npu_data_ptr(Storage)` | `NPUCachingAllocator::checkBlockIsSafe(obj.data_ptr())`（NPUCachingAllocator.cpp:3808-3818） | 空指针或非本分配器 deleter 的 ptr 直接返回 True（视为安全）；非空且属本分配器但查不到分配块时 `TORCH_INTERNAL_ASSERT(block != nullptr)` 失败（:3815-3816）；命中块返回 `is_safe` |
| `_mark_all_npu_data_ptr_unsafe(int device)` | 设备级 `markAllBlockUnsafe`（:3820-3822 → 设备实现 :1185-1189） | 把该 device 全部 active_blocks 置 `is_safe=false`，不区分块来源 |
| `_update_npu_data_ptr(Storage)` | `updateBlockToSafe`（:3824-3836） | 非空且属本分配器但查不到分配块时同样 `TORCH_INTERNAL_ASSERT` 失败（:3831-3832）；命中块置 `is_safe=true`（:3836），内存日志仅在原 `is_safe=false` 时记录（:3833-3835）；空/外来 ptr 静默返回 |
| `_set_npu_data_unsafe_flag(bool)` / `_get_npu_data_unsafe_flag()` | `NPURecovery.cpp` 进程级 `NPU_DATA_UNSAFE_FLAG`（shared_mutex 读写锁；主线 :11-26、发布 :16-32） | 进程级开关，随 set 记 ASCEND 日志；不随 device 隔离 |
| `_recovery_all_npu_stream(int)` | `NPUStream` 的 `recovery_all_npu_streams` | 语义已由[原生流队列卡](../../guides/optimization/torch_npu/torch_npu_native_stream_queue_drain_and_synchronization.md)闭合，此处不重复 |

UCE 自动标脏：`checkUceInMemPool`（:1134 起）遍历 memUceInfo 故障地址区间与全部分配块，重叠时置该块 `is_safe=false`，并在全局 unsafe flag 尚未置位时置 true（:1163-1166），随后回写 mem_uce_info——即除 Python 手动 mark_all 外，还有这条按故障地址自动标块的路径；其调用方（NPUQueue 错误分类的 checkUceErrAndRepair）已在[原生 Repository 环形队列卡](../../guides/optimization/torch_npu/torch_npu_native_repository_ring_and_host_drain.md)记录。

执行面在 torchnpugen 代码生成，但被检查的形参集合是**选定链**而非全部形参：custom_functions.py 的候选链是 `self_arg + out + flat_positional`（:128-132），utils.py 的是 `self_arg + out + flat_positional`（:289-293），各自再经 `is_tensor_like` 过滤——keyword-only 形参不在这条安全检查链内（custom_functions.py :147 起另有包含 kwarg_only 的 device guard 链，是另一条检查，不在本卡范围）。模板把 `if (c10_npu::get_npu_data_unsafe_flag()) { c10_npu::check_npu_tensor_is_safe(<选中 tensor 形参>); }` 织入生成 wrapper（custom_functions.py:137-146；utils.py:304-315）；无选中 tensor 形参时两个模板分别写 `// No unsafe tensor check`（custom_functions.py:138）与 `// No data check.`（utils.py:301-302）注释占位，文案不同。unsafe flag 置位后，经此模板生成的 wrapper 对选中 tensor 形参逐个检查，命中不安全块抛 `TORCH_CHECK("There is unsafe data in the input tensor.")`（NPURecovery.cpp:33/:42，非 NPU tensor 直接跳过检查）——这是模板覆盖面的陈述，不是全库 wrapper 或 keyword-only 形参的保证。`wrapper_NPU__copy_`/`wrapper_NPU___foreach_copy_` 特例改用 `check_and_update_npu_tensor_for_copy(self, src)`——该 C++ helper（NPURecovery.cpp:82-90 及 TensorList 重载）只做「检查 src(s) 安全、把 dst(s) 标为安全」的**标志位操作**，本身不拷贝/重建数据、不校验拷贝结果；目标块被标安全不等于数据已修复。生成 wrapper 中该检查块与实际 copy 执行的先后、失败时标志是否回滚，不在本卡范围（模板层已核对，wrapper 实际执行未验证）。`test/npu/test_recovery.py:16-43` 是静态的正常路径样例：mark_all 后 `tensor_a + tensor_b` 抛上述错误、del 后重新分配的新块安全、`copy_` 后目标块恢复安全；本卡未运行测试，也不把标志位更新当作数据修复成功的证明。

与 Python 面的对齐：两 pin `npu/_recovery.py` 的六个同名包装（TypedStorage/UntypedStorage 类型门 + pta_error）逐字对应上表；`restart_device(rebuild_all_resources=True)` 默认 mark_all + set flag + `_recovery_all_npu_stream`，主线第三参 `disable_tensor_unsafe_check=True` 只跳过 mark_all/set flag（恢复流仍执行）。另有消费点：`utils/_dynamo.py:219` 打补丁的 torch.compile wrapper 在 backend 解析为 "mlir" 时，于 `register_inductor_npu` + `_lazy_inductor_setup` 之后调用 `_recovery_all_npu_stream(current_device)`；源码未注释该调用意图，本卡不臆测其与设备恢复流程的关系。

本节不改变 draft 判断与产品支持边界：接口「预留暂不支持」的文档冲突仍以上文为准，csrc 实现存在不构成支持承诺，也不补写任何运行 verified。

## csrc 与 torchnpugen 来源

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPURecoveryBindings.h)（primary）：1–11 行全文。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPURecoveryBindings.cpp)（primary）：1–29 行全文。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPURecovery.h)（primary）：1–17 行全文。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPURecovery.cpp)（primary）：1–94 行全文。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPURecovery.cpp)（primary）：1–135 行全文。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPURecovery.h)（primary）：1–20 行全文。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/NPURecovery.h)（implementation）：1–13 行全文（日志宏头）。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/InitNpuBindings.cpp)（implementation）：210–280 行段（绑定挂载与 initModule）。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation）：1134–1200 与 3803–3845 行段（checkUceInMemPool 标块、markAllBlockUnsafe、checkBlockIsSafe/updateBlockToSafe 覆盖层）。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py)（implementation）：205–230 行段（mlir 分支的 _recovery_all_npu_stream 调用）。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/custom_functions.py)（implementation）：130–150 行段（unsafe 检查织入模板）。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/utils.py)（implementation）：295–320 行段（copy_ 特例与 check_and_update 织入）。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/npu/test_recovery.py)（implementation）：1–50 行段（API 行为静态佐证，未运行）。

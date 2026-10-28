---
type: Runbook
title: Kernel printf 无输出诊断
description: 按平台与模式、头文件与命名空间、dump 开关、容量及执行路径五类原因排查 AscendC::printf 无输出，再用短字符串复验。
tags:
- task.debugging
- topic.implementation.debugging
- topic.programming_model.execution_model.simd
status: stable
sources:
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/printf.md
  role: primary
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/diagnosis_workflow.md
  role: supporting
- resource: https://gitcode.com/cann/asc-devkit/blob/e680c34c09ba6919b3cebd2b7ec027f4ff6f0f22/.agent/skills/ascendc-api-kernel-debug/references/platform_matrix.md
  role: constraint
created_at: '2026-10-23T01:30:00Z'
updated_at: '2026-10-23T01:30:00Z'
platforms:
- '950'
- a3
- a2
---

# Kernel printf 无输出诊断

`AscendC::printf` 在 Kernel 中编译通过却在运行期没有任何文本输出时，按下面的顺序定位。排查时先排除**调用形式与目标平台/编程模式不匹配**、**被 dump 开关关闭**、**输出容量超限**或**语句根本不在执行路径上**。

## 触发条件

- Kernel 编译、上板或仿真运行成功，但预期出现调试文本的位置没有输出；
- 换用其他接口（`assert`、`asc_dump`、`asc_time_stamp`）排查时表现不一致；
- 现象与核数、Block 数或线程过滤条件相关。

## 处置步骤

### 1. 固定上下文

在动手改代码前先确认六项事实，它们决定后续判定分支：SoC/产品与 `__NPU_ARCH__` 或编译架构；当前是 SIMD、SIMT、SIMT VF 还是 SIMD VF；运行在 CPU 调试、仿真还是 NPU 上板；走直接调用还是算子入图；CANN/AscendC 版本、编译命令与相关 `acl.json` 配置；期望观测的是文本、张量内容、异常还是周期数据。

### 2. 依次排除五类原因

1. **平台与模式支持**：先确认目标平台和当前编程模式支持该调用形式。公开 tuning 文档中 `printf` 的支持面为 Ascend 950 的 SIMD/SIMT/SIMT VF/SIMD VF、A3 与 A2 的 SIMD；310P/310B 与 910/Kirin 在当前文档中不支持。A2/A3 的"主要为 SIMD"表示公开文档没有承诺 SIMT 或 VF 变体，不能由产品名称推断所有形式都可用。
2. **头文件与命名空间**：调用形式为 `#include "utils/debug/asc_printf.h"` 配合 `AscendC::printf(...)`，并按工程样例补充 `kernel_operator.h`；确认没有误用 CPU-only 的 `printf`，也没有落到错误的地址空间重载。
3. **dump 开关**：确认没有定义 `ASCENDC_DUMP=0`——该开关会同时关闭 `printf`、断言与 dump 输出。
4. **容量与 FIFO 配置**：SIMD 场景单次调用的打印总量默认约 30 KB，可用 `simd_printf_fifo_size_per_core` 配置，但该 SIMD 配置不支持 PyTorch/算子入图场景；SIMT 场景默认约 2 MB FIFO，可用 `simt_printf_fifo_size` 在 1 MB–64 MB 间配置，不能把这一缓存口径当成 SIMD 单次限制。SIMD VF 中 `printf` 与 `assert`/`ascendc_assert`/`asc_dump` 共享预留的 UB 空间，单条记录必须能完整放入；FIFO 过小会表现为部分数据不输出。
5. **执行路径与过滤**：确认打印语句所在分支真的被执行、没有被 Block/线程条件过滤掉，且 Kernel 没有在到达该语句前提前失败。

五类原因排查后，用一条无参数的短字符串做最小复验，确认通路成立，再逐步加回格式参数。

### 3. 输出不全或顺序异常时的额外判定

区分 SIMD FIFO、SIMT FIFO、SIMD VF reserved UBUF 与每核 dump 上限这四类容量约束；减少 Block/线程输出、缩短单条消息。使用 `asc_dump` 时要按 **32B 补齐后的容量**估算，而不是有效元素字节数。多核输出不要假设全局顺序，需要顺序时写回带索引的 GM 缓冲区，或用 `desc`、Block/线程 ID 与阶段标签建立来源关系。

### 4. 与相邻症状分流

- **断言未触发、算子继续执行**：区分条件本身为真、代码路径未执行、`NDEBUG`、`ASCENDC_DUMP=0` 和场景不支持；先用一个确定失败的最小输入验证断言宏是否生效，再恢复原条件。
- **断言或 Trap 导致算子失败**：保留失败日志与返回码；`__trap` 只负责中断，需要在触发前用少量输出或可观测数据记录上下文。
- **周期结果异常**：把打印移出测量区，确认 `start` 与 `end` 位于同一线程、同一逻辑阶段，并检查同步、冷启动、编译优化与测量次数；`clock` 不是 profiling 采集器。

## 验证方式

按"接口能编译 → 语句确实执行 → 输出或异常符合预期 → 扩大到真实数据与多核 → 关闭或删除调试代码"的顺序逐级验证。每一步只增加一个变量，出现回归时回到上一级。

## 失效边界

- 卡片结论来自 asc-devkit 仓库内核调试 Skill 的参考资料（固定到 40 位 commit），平台支持面最终以目标 CANN 版本的公开 API 文档、公开头文件与实际编译验证为准；内部资料与公开文档不一致时以公开文档为准。
- 不覆盖 CPU 侧调试手段与算子入图框架自身的日志通道。
- 不解决"打印内容正确性"问题：文本打印只提供局部观测，**不能替代功能校验**，也不能证明数据搬运或同步逻辑正确。
- 调试完成后应删除打印语句，或按工程要求关闭 `ASCENDC_DUMP`；保留大量多核打印会显著改变执行时间。

---
type: API
title: 线程绑核API：闭区间、多区间与恢复
description: 区分发布单区间与主线多区间，限定CPU_AFFINITY_CONF模式和当前线程恢复行为；主线另增bind_irq设备中断亲和链。
tags:
- task.lookup
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/affinity.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/affinity.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUAffinityController.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUAffinityController.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_module.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_module.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/api_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/utils/test_affinity.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUInterruptAffinity.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUInterruptAffinity.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/impl/NPUGuardImpl.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/InitNpuBindings.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/GetAffinityCPUInfo.h
  role: implementation
created_at: '2026-11-09T19:09:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 线程绑核API：闭区间、多区间与恢复

## 固定版本与产品

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5的中文页及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文页。A2/A3在本卡指训练系列，主线新增950DT确认不回推到发布版，不扩到950PR。旧Atlas产品只保留来源条目，不自动映射其他新型号。

发布配对PyTorch提交为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf时单独指出，两个main不构成自动配套。以下为静态合同，没有编译、导入、加载模型、设备运行或性能测量。


## 声明与硬件

```text
set_thread_affinity(core_range=None) -> None
reset_thread_affinity() -> None
```

命名空间为torch_npu.utils。两页同时列A2/A3训练与推理、旧Atlas训练/推理；主线另列950DT。这个API的产品表不扩大npu_affine子模式或每流队列细粒度绑核的独立限制。

## 参数形状与版本

发布core_range为List[int]，例如[0,3]是包含端点的0、1、2、3号CPU核。主线支持`list[int] | list[list[int]] | None`，可用[[0,3],[5,7]]指定多个闭区间；不能把主线多区间参数回推发布实现。

发布包装只对长度2及端点非负做显式检查；主线检查区间列表、整数端点、start>=0且start<=end，再展开、去重、排序成核列表传底层。主线None的docstring称reset to default，公开接口页称按非主线程自动绑核；两者都走(-1,-1)底层入口，不能据这句把None等同于reset_thread_affinity恢复主线程范围。

## 时机与前提

只在CPU_AFFINITY_CONF mode=1或2生效。一般先set当前线程的期望范围，再创建继承亲和性的子线程，随后在当前线程reset回主线程区间。reset不表示对子线程逐一重绑，也不自动处理任意异常路径。

实际OS/Cgroup允许核、NUMA与线程竞争仍须检查；见[CPU绑核指南](../../guides/optimization/torch_npu/torch_npu_cpu_affinity.md)。本文没有修改亲和性或启动线程实验，样例编号不是目标机器配置。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/torch_npu-utils.reset_thread_affinity.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-utils/torch_npu-utils.set_thread_affinity.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/affinity.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/affinity.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/__init__.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/__init__.py)（implementation）

## 原生绑定：两整数或核列表

主线 `torch_npu._C._npu_set_thread_affinity`（METH_VARARGS）先按两个 int 解析：`core_start == -1` 走 OTHER_THREAD 绑定，否则把闭区间展开为核列表走列表路径。两 int 解析失败再退回单个 list 参数：逐项 `PyLong_Check`（bool 是 int 子类，能通过检查并被当作 0/1 使用），元素插入有序集合自动去重后绑定。两种形态都失败才报 "Expected either two integers (core_start, core_end) or a list of integers"。发布版绑定只接受两个 int（`PyArg_ParseTuple "ii"`），list 或非 int 形态直接 TypeError——主线多区间包装依赖新增的 native 列表入口，不能回推发布。

native 公共行为：两版本控制器所有入口都先过 `needToSetThreadAffinity()` 门控（首次调用静态求值 CPU_AFFINITY_CONF；mode 0/未设或亲和性冲突检查失败时全程 no-op），Python 调用正常返回不等于实际改了亲和性。

| 版本 | 用户区间路径 | 越界核处理 | 线程类型标记 |
| --- | --- | --- | --- |
| 主线 | `SetThreadAffinity(CoreIdList)` 直接绑定给定核集合 | 剔除 `>= sysconf(_SC_NPROCESSORS_ONLN)` 的核 id，告警不报错 | 置 USER_THREAD；此后按 device 的自动绑核对当前线程跳过，直到下一次 ThreadType 入口改写 |
| 发布 | `SetThreadAffinity(int,int)` 把 start/end 各 `min(, 在线核数)` 截断成单个区间绑定 | 端点截断，区间可能仍为空 | 同样置 USER_THREAD |

发布包装允许 start>end（无顺序检查）：截断后得到空区间；按 POSIX 语义推断，空 mask 的 pthread 绑定**可能**失败——这是外部推断而非本地运行结果，本卡未复现；若失败，控制器仅记错误日志（`ASCEND_LOGE`），Python 层不抛异常；主线包装的 `start <= end` 检查在 Python 层就拒绝。ThreadType 入口（`(-1,-1)` 的 OTHER_THREAD 与 reset 的 MAIN_THREAD）会先 `GetDevice` 取当前设备来选核表，再改写线程类型并绑定；reset 置位主线程绑定标记并把当前线程绑回 main_thread 核表，不是恢复 OS 默认。

仓内单测（主线 `test/utils/test_affinity.py`，mock C 入口）对应包装语义：`[2,5]` 展开为 `[2,3,4,5]`；`[[2,5],[7,9]]` 展开为 `[2,3,4,5,7,8,9]`；重叠区间 `[[2,7],[4,9]]` 合并为 `[2..9]`；`None` 传 `(-1,-1)`；长度不为 2 或含负值抛 ValueError。

## 仓内自动消费者：DataLoader 迭代器初始化

torch_npu 默认替换 `torch.utils.data.dataloader._MultiProcessingDataLoaderIter.__init__`（`_apply_module_patch`）：每次多进程 DataLoader 建立 worker 迭代器时，先 try `torch_npu.npu.synchronize()`（异常仅 print），再调 `_npu_set_thread_affinity(-1,-1)`（OTHER_THREAD），执行原 `__init__`（fork/spawn 的 worker 继承此刻亲和性），最后 `_npu_reset_thread_affinity()`（MAIN_THREAD）。原始 initializer 与前后两个绑核调用都不在 try/finally 内：若原 `__init__` 抛异常，末尾的 reset 不可达，当前线程的 OTHER_THREAD 标记与亲和性不保证恢复。

| 版本 | 安装链 | 触发条件 |
| --- | --- | --- |
| 主线 | PatchManager "api" 组（api_patches → `_apply_module_patch`）在 import torch_npu 时应用 | `ASCEND_RT_VISIBLE_DEVICES` 设为空字符串时跳过包装直接走原 init；未设或非空都包装 |
| 发布 | `torch_npu/__init__.py` import 后直接调用 `_apply_module_patch()` | 无条件包装 |

含义：默认环境（未设 `ASCEND_RT_VISIBLE_DEVICES`）下两版本都会在每个 DataLoader 迭代器初始化时触发一次 synchronize 加两次绑核入口；其中只有两次绑核入口受 CPU_AFFINITY_CONF 门控（mode 0/未设或冲突时为 no-op），`torch_npu.npu.synchronize()` 不受该门控——只要 wrapper 实际执行（`ASCEND_RT_VISIBLE_DEVICES` 未设为空字符串），mode 0 下该 wrapper 仍会真实同步，并非完全 no-op。用户手动 set 之后再创建 DataLoader，当前线程的类型标记会被该路径改写（OTHER_THREAD→MAIN_THREAD），排查绑核行为时应把这条自动包装纳入观测；模式与 NUMA 语义仍见[CPU绑核指南](../../guides/optimization/torch_npu/torch_npu_cpu_affinity.md)。

## 原生绑定与自动消费者来源

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)（implementation，1947–1992、2365–2366）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/npu/Module.cpp)（implementation，1978–2006、2400–2401）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUAffinityController.cpp)（implementation，全文 1–601）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUAffinityController.cpp)（implementation，185–215、255–340）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_module.py)（implementation，269–289）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/utils/_module.py)（implementation，360–375、524）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/api_patches.py)（implementation，全文 1–22）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation，1–80、173）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/utils/test_affinity.py)（implementation，全文 1–76）

## 主线 IRQ 中断亲和链

主线独有：`bindIrqAffinity`/`stopIrqbalance`/`restartIrqbalance`（`csrc/core/npu/NPUInterruptAffinity.cpp`/`.h`）把指定 NPU 设备的 MSI 中断绑到指定核并托管 irqbalance 服务。发布 pin `f3ecfe4a` 无这两个文件；发布 `NPUAffinityController.cpp`（383 行）与 `InitNpuBindings.cpp` 内 rg `bind_irq|irqbalance|InterruptAffinity` 零命中（negative evidence）——`CPU_AFFINITY_CONF` 的 `bind_irq` 子项与整条 IRQ 链只在主线存在，不能按发布版文档或本节内容配置发布版。

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| `CPU_AFFINITY_CONF` 含 `bind_irq:1` 且进程 euid=0（root） | 解析在首次 `needToSetThreadAffinity()` 时执行一次（`NPUAffinityController.cpp:428-431` static）：`parseBindIrqMode`（:159-183）在 root 前提下按设备划分——核数 > `kIrqCoreOffset=2` 的设备恰好把有序核列表（`CoreIdList = std::set`，`GetAffinityCPUInfo.h:7`）最前 2 个核移入 `kDevicesIrqCores[i]` 并从线程绑核列表移除，每设备至多 2 个 | 非 root 在任何划分发生前就告警 "IRQ binding requires root privilege, skipped" 并把 `kBindIrq` 置 false，全部核保留给线程；设备核数 ≤2 的设备不划分并告警，整组核保留给线程——两种例外都不扣核 |
| 设备切入门（`NPUGuardImpl::uncheckedSetDevice` → `StartMainThreadBind`，`impl/NPUGuardImpl.cpp:63`、`NPUAffinityController.cpp:525`） | 进程级 `static std::once_flag bind_irq_flag` 的 `std::call_once`（:537-560）整进程只执行一次：`kBindIrq` 为真时，若 `RANK` env 为 0 或未设（`OptionsManager::GetRankId`，`OptionsManager.cpp:342-346`，未设返回 -1）则 `stopIrqbalance()`；随后取当前设备（:548），`kDevicesIrqCores[device]` 非空时才调 `bindIrqAffinity(device, kDevicesIrqCores[device])`（:550）——只绑定这一次触发时机的当前设备，不做设备遍历，此后本进程内切换设备不会再绑其他设备的 IRQ | 非 0 rank 不停 irqbalance，但仍尝试绑定；绑定失败告警"2 CPU cores remaining unused... set bind_irq=0"——核已从该设备线程预算扣除而 IRQ 未绑上，源码告警把关闭 bind_irq 作为建议处置给出（告警文本写作 `bind_irq=0`，而解析器 regex 实际匹配的是冒号分隔写法，给出具体语法时应写 `bind_irq:0`），不是已验证的唯一处置。该进程级 once 与每线程一次的 `bind_main_executed` 标志（:531-535）相互独立：后者只控制主线程绑核不重入 |
| `bindIrqAffinity`（`NPUInterruptAffinity.cpp:265-330`） | 取 irq 核列表前两个为 sq/cq 核（:276-279）；`AclrtGetLogicDevIdByUserDevId` 取逻辑 id 并按注释假定非容器场景物理 id=逻辑 id（:282-291）；DCMI 查 PCIe BDF（A3 系列 card=physical/2、die=physical%2；A2 系列 card=physical；其他 SoC 直接 `TORCH_CHECK` 报错，:91-100）；读 `/sys/bus/pci/devices/<BDF>/msi_irqs` 枚举 MSI IRQ（:139-160）；扫 `/proc/interrupts` 匹配 `sq_send_trigger_irq` 行（进程内 static 缓存只扫一次，:164-198）；求交集定位本设备 sq_irq（:203-210），cq_irq=sq_irq+1；把核号转 16 进制掩码写入 `/proc/irq/<n>/smp_affinity`（:46-61、:63-82、:214-243） | 任一步失败（DCMI 查询失败、msi_irqs 为空、无 sq_send_trigger_irq、交集为空、写 smp_affinity 失败）都返回 false 并告警，无部分回滚；SoC 在两个半开区间 `[Ascend910_9391, Ascend950)` 与 `[Ascend910B1, Ascend310B1)` 之外（源码用 `>=` 下界、`<` 上界比较，Ascend950/Ascend310B1 端点被排除，不表示这两型受支持）在取 BDF 时 `TORCH_CHECK` 直接报错 |
| 进程退出（`InitNpuBindings.cpp:103-106`） | `RANK` 为 0 或未设时调 `restartIrqbalance()`（`NPUInterruptAffinity.cpp:362-379`，仅在本进程成功停止过服务时执行 `systemctl restart irqbalance`） | `stopIrqbalance`（:332-360）三查 systemctl 可用性/服务安装/active 后才 stop；源码头注释与停止告警均声明：异常退出（kill/coredump）时服务需用户 `sudo systemctl restart irqbalance` 手动恢复；容器内无法停宿主机 irqbalance 的限制来自头文件注释（`NPUInterruptAffinity.h:11-14`），未做环境实测 |

含义：只有 euid=0、`bind_irq:1` 且该设备核数 >2 同时成立时，该设备的线程核预算才恰好减少 2 个（sq/cq 各一）；非 root 或核数 ≤2 的设备不扣核。线程亲和与中断亲和共享同一 `CPU_AFFINITY_CONF` 核池；IRQ 绑定由进程级 `std::call_once` 只对首次满足时机的当前设备执行一次，不是按设备遍历；irqbalance 停止/重启只发生在 rank 0 或未设 `RANK` 的进程。全链为主线 C++ 源码静态直读（关键行锚见 IRQ 中断亲和链来源），未在物理机验证 root 权限、容器、DCMI 查询或 smp_affinity 写入效果；核区间划分语义（npu0:0-1 等）与 mode 门控仍以本卡上文为准。

## IRQ 中断亲和链来源

- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUInterruptAffinity.cpp)（implementation，全文 1–380）
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUInterruptAffinity.h)（implementation，全文 1–29）
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/impl/NPUGuardImpl.cpp)（implementation，50–70）
- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/InitNpuBindings.cpp)（implementation，95–112）
- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation，342–346）
- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/GetAffinityCPUInfo.h)（implementation，1–11，末行无换行）

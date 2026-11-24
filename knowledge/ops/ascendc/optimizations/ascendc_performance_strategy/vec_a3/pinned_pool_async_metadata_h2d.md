---
type: Optimization
title: pinned 池 + aclrtMemcpyAsync 消除 per-call 元数据同步 H2D
description: 将每次小元数据同步H2D改为pinned池配合aclrtMemcpyAsync异步传输。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-pinned-pool-async-metadata-h2d.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：pinned 池 + aclrtMemcpyAsync 消除 per-call 元数据同步 H2D

> 单一优化点：直 launch 扩展每次调用都要把小尺寸 tiling/元数据（几十~几百字节）送上 device。若用「每次 `at::empty`(CPU) + `.to(device)`」，每次付出 CPU 分配 + **阻塞式** H2D（host 停到拷贝完成）。改为**进程级 pinned 池**（slot 轮换的 host/device buffer 对）+ `aclrtMemcpyAsync`，host 填充后立即提交 launch，全程零阻塞。每个 slot 必须记录拷贝完成事件，复用前等待该事件；仅轮换槽数不构成完成保证。

## 1. 原理

- 小尺寸同步 H2D 的代价不在带宽而在**延迟与阻塞**：同步拷贝把 host 线程挂起直至 device 确认，实测每次 ~40-70us；对小/中 shape 算子，这是端到端固定地板的主要成分（各 case 耗时收敛于与数据量无关的 ~100us 地板的主体）。
- pinned（`aclrtMallocHost`）内存可被 DMA 直接访问，`aclrtMemcpyAsync` 提交后立即返回，拷贝与后续 kernel 在同一 stream 上按序执行。
- 池化消除每次 `at::empty` 的分配器往返；slot 轮换只避免立即复用，每个 slot 必须记录完成事件并在复用前等待，不能仅靠深度 ≥4 保证「在飞拷贝的 host 源不被覆写」。

## 2. 性能问题模式

- **代码形态**：launch 路径存在 per-call `at::empty(cpu) → 填 tiling → .to(device)` 或等价 `aclrtMemcpy`（同步）。
- **bench 特征**：
  - 各 case 耗时收敛在与数据量无关的固定地板（1MB 与 16MB case 同耗时）；
  - wall-clock 明显大于 NPU event 时间（wall-event 差 = host 提交+阻塞路径，方向一致）；
  - 换算：固定地板 ≈ N_launch × (同步 H2D + 提交) + 绑定层开销。
- **不适用**：元数据尺寸大（>64KB，异步收益被拷贝时间淹没）；调用侧本来就要同步等待结果。

## 3. 正确性红线

- **slot 轮换 + 完成事件是必须的**：async 拷贝的 host 源在 device 确认完成前不可覆写。仅增加槽数只是推迟复用，不保证完成；必须按槽记录 event 并在复用前等待（或限制 host 提交深度并同步 stream）。单 slot 在「调用 k+1 填充时调用 k 的拷贝还在队列里」场景下产生数据竞争——深度 ≥2 轮换（建议 4）只是降低概率，不能替代事件等待。
- **跨 stream 复用必须同步**：池被多个 stream 使用时，记录 lastStream，stream 变化先 `aclrtSynchronizeStream(old)`（或按 stream 分池）。
- **保留同步回退路径**：池分配失败时回退 `.to(device)` 同步拷贝，功能不失效。
- CANN 9.0 API 签名：`aclrtMemcpyAsync(dst, destMax, src, count, kind, stream)` 是 **6 参**（含 destMax）；`aclrtMalloc` 是 3 参——按本机头文件核对，勿凭旧记忆写。
- 进程生命周期管理：池在析构时 `aclrtFreeHost`/`aclrtFree`；容量不足时先等待所有在途拷贝完成，再全部释放并按新容量重分配。

## 4. 泛化条件

- **适用**：一切「直 launch + per-call 小元数据 H2D」的算子扩展（自定义 op 的 tiling/参数表/指针表），高频小 shape 调用收益最大。
- **不适用**：元数据可完全内嵌 kernel 参数的场合（更彻底）；一次 H2D 后跨调用不变的元数据（应做缓存而不是池化）。

## 5. 实施步骤

1. 定义 `MetaPool{ host[kDepth], dev[kDepth], events[kDepth], capacity, slot, lastStream }`，`Ensure(bytes)` 惰性扩容（先等待在途事件，再全释放重分配）。
2. launch 路径：Ensure → 取 `slot`（推进）→ 若该 slot 有记录 event，先等待完成 → 填 host pinned → `aclrtMemcpyAsync(dev, host, bytes, H2D, stream)` → 记录该 slot 的 event → launch。
3. stream 变化保护 + slot event 等待 + 失败回退同步路径。
4. 验证：bench 各 case 的固定地板应塌缩（本例 ~90us → ~20-30us，geo +276%）；连续提交次数超过槽深时不得出现覆盖或精度回退。

## 6. LLM 前置问题（实施前自检）

- 每个 slot 是否有完成 event？复用前是否等待该 event？仅靠槽深是否足够？
- 多 stream 场景的 lastStream 同步是否实现？
- 本机 CANN 版本的 aclrtMemcpyAsync 参数个数核对了吗？
- 分配失败回退路径还能跑通精度吗？扩容时是否等待了所有在途事件？

## 7. 验收标准

- build + 精度全过；实测收益（910B3）：bench 各 case 固定地板 ~90us → ~20-30us，geo 0.448 → 1.687（+276%）；全量精度通过；连续提交次数超过槽深的压力用例不得出现 host 源覆盖或精度回退。

## 检索卡（短卡）

动作：将每次小元数据同步H2D改为pinned池配合aclrtMemcpyAsync异步传输。
适用：直launch且每次传输小型tiling、参数表或指针表的算子扩展，尤其高频小shape调用。
限制：必须轮换 slot 并按槽等待完成事件；device 确认异步拷贝完成前不得覆写 host 源；仅加深槽数不构成保证。
范围：自定义op的tiling、参数表和指针表传输。
检索词：MetaPool、pinned池、aclrtMemcpyAsync、小元数据H2D、slot轮换。
机会：launch路径每次创建CPU元数据并同步.to(device)，或调用同步aclrtMemcpy。

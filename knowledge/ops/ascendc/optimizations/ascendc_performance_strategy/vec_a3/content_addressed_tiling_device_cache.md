---
type: Optimization
title: 内容寻址 tiling device buffer 缓存（消除每帧常量 H2D 重传）
description: 按常量内容寻址缓存 tiling device buffer，替代每次 CPU 分配、填充和传至 device。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.tiling
- topic.implementation.synchronization
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A3/00-content-addressed-tiling-device-cache.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- a3
---

# 性能优化策略：内容寻址 tiling device buffer 缓存（消除每帧常量 H2D 重传）

> 单一优化点：host launcher（torch plugin / 直启工程）每次调用都为**内容不变的小常量结构体**（tiling 描述符、launch 参数块）重新分配 CPU tensor 并做 pageable 同步 H2D 拷贝。对给定 (shape, 标量参数, 切分策略) 这些内容逐帧完全相同，重传纯属浪费。以内容为 key 缓存 device buffer（命中即零拷贝直传 device 指针），把每帧 ~60-90us 的同步 H2D 从热路径整体消除。

---

## 1. 原理

**问题泛型**：AscendC 直启型工程的 host 层常见结构——`每次 forward: at::empty(CPU) → 填 tiling → tensor.to(device) → launch`。`.to(device)` 对 pageable 内存是**同步阻塞**拷贝（host 等待拷贝完成），单次几十微秒；而 elementwise 类 kernel 本体往往只有 5-60us。结果是端到端时间被这坨固定开销主导：**所有 case 的 E2E 几乎恒定、与数据量脱钩**（例如 6MB 与 96MB 的 case E2E 同为 ~105us）。

**为什么缓存有效**：tiling 内容是 `(shape, scale, tile 策略, 核数策略)` 的纯函数——同输入组合必然逐帧相同。第一次上传后 device buffer 即为**只读常量**：
- 写入仅发生一次（pageable `.to()` 阻塞至完成，返回时数据已就绪）；
- 之后任何 stream 上的 kernel 都只读它 → 跨 stream 并发安全，无需同步；
- 命中路径 = 一次 hash 查表 + 指针返回，纳秒级。

**收益结构**：稳态（同 shape 重复调用，推理/训练的绝大多数场景）热路径零 H2D；shape 每帧变化时退化为原路径（每帧一次 miss 上传），**不劣于基线**。实例（910B3）：E2E 104us → 23us，host 开销占比 74% → ~5us；geo speedup 0.963x → 4.470x。

## 2. 性能问题模式

满足以下特征时考虑本策略：

1. **代码形态**：host launcher 每次调用执行「小 CPU tensor 分配（≤64B 量级）→ 填常量字段 → `.to(device)`/`aclrtMemcpy`」，且字段全部由 (输入 shape/dtype, 标量属性, 固定策略) 决定，与数据**内容**无关。
2. **profiling 特征**：端到端时间与数据量严重脱钩（数据量差 10× 以上而 E2E 几乎不变）；「E2E − 纯 kernel 时间」差值大（>30%）且不随 shape 增长；msprof kernel 时间远小于 wall-clock。
3. **对照特征**：torch 原生等价实现的耗时随数据量正常缩放，而本算子 E2E 平坦。

不适用（任一）：
- tiling/参数块**依赖张量内容**（如按数据 max 动态定标）——内容变了 key 不变会返回错 buffer，此为本策略唯一正确性风险点；
- 标准 ACLNN 框架算子（tiling 由 runtime 机制管理，host 不经手）；
- 每帧 shape 都不同的极端场景（缓存永远 miss，只剩 hash 开销，此时应改用 pinned+async H2D 而非本策略）。

## 3. 正确性红线

- **key 必须覆盖全部字节**：结构体每个字段（含 padding 后的对齐字节如有）都要进 key；漏一个字段 = 同 key 不同内容 = 错误结果。int32-only 结构体最安全（无 padding）。
- **key 必须含 device index**：多卡进程下不同 device 的 device 地址空间不同，漏掉会在卡间串用非法指针。
- **float 字段走位模式**：浮点 key 用 IEEE-754 位模式（memcpy 到 int32）比较，不能 hash 浮点值本身（-0.0/+0.0、NaN 位模式差异）。
- **写入可见性**：首次上传必须阻塞完成（pageable `.to()` 天然满足；若改 async 拷贝必须 stream sync 后才算就绪）。
- **缓存上界**：加条目上限（如 1024）防御 shape 海量变化的慢性泄漏；超限走不缓存的慢路径，而非清空重传。
- **缓存对象生命期**：缓存 at::Tensor（storage 持有 device 内存）而非裸指针，进程退出统一释放；避免 eviction 设计（常量语义无失效问题）。

## 4. 泛化条件

适用（全部满足）：
- host 每帧上传的常量块内容由 (shape, dtype, 标量属性) 完全决定，可构造全字段 key；
- 调用模式存在同参数重复（推理循环、benchmark、训练 step）；
- 常量块小（KB 级以内，缓存多份无内存压力）。

不适用：见 §2「不适用」。

## 5. 实施步骤

1. **量化 host 占比**：对比「端到端 wall-clock」与「msprof 纯 kernel 时间」，确认差值主导；检查 E2E 是否对数据量平坦（本模式指纹）。
2. **定义 key**：枚举 tiling/参数块全部字段 + device index；浮点转位模式；写 hash 与 `operator==`。
3. **实现缓存查询**：`static std::unordered_map<Key, at::Tensor, Hash> + std::mutex`；未命中走原上传路径后 emplace；命中直接返回 `storage().data()`。
4. **替换热路径**：launch 处以缓存指针替代每帧上传；删掉每帧的 CPU tensor 分配。
5. **顺带缓存进程级单例查询**：如 `PlatformAscendCManager::GetInstance()->GetCoreNumAiv()` 这类每帧调用改 `static const` 一次性初始化；python wrapper 侧的 pad 查询等 pybind 小调用同理缓存。
6. **实现变体**（按场景择一）：
   - 轻量单条目：仅 `static` 缓存**上次** tiling（全字段 memcmp + device index 校验），命中即复用——shape 切换少的场景最简。
   - 哈希键：tiling 序列化后 FNV-1a 哈希 + device index 作 uint64 key。
   - 粗粒度键：key=(元素总数, dtype 类)，字段少且同键必同内容时可用。
   - pinned 异步刷新：`unordered_map<shapeKey, {pinnedCpu, deviceTensor}>`，miss 时分配并 `.to(device, non_blocking=true)`，命中时填 pinned → `aclrtMemcpyAsync` 异步刷新（适合 tiling 含低频变化字段的场景）。
7. **验证**：精度全量 case + 多 shape 混跑（验证缓存多条目正确性）+ 双源计时（event/wall 一致）。

## 6. LLM 前置问题（实施前自检）

1. tiling 的每个字节是否都进了 key？有没有依赖张量内容的字段？
2. 多卡场景 key 是否含 device index？
3. 浮点字段是否用位模式比较？
4. 首次上传是否阻塞完成？缓存条目是否有上界？
5. E2E 对数据量平坦的特征是否确认（而非 kernel 本身慢）？

## 7. 验收标准

- build + 精度全过；实测（910B3）：E2E 104us → 23us，host 开销占比 74% → ~5us；geo speedup 0.963x → 4.470x。多 shape 混跑验证缓存多条目正确性，双源计时（event/wall）一致。

## 检索卡（短卡）

动作：按常量内容寻址缓存 tiling device buffer，替代每次 CPU 分配、填充和传至 device。
适用：常量块由 shape、dtype、标量属性完全决定，且调用中重复相同参数。
限制：缓存 key 必须覆盖结构体全部字段及 padding 对齐字节。
范围：torch plugin 或直启工程的 host launcher。
检索词：内容寻址、tiling、device buffer、at::empty、tensor.to、aclrtMemcpy。
机会：每次上传不变的小常量块，且端到端耗时对数据量平坦。

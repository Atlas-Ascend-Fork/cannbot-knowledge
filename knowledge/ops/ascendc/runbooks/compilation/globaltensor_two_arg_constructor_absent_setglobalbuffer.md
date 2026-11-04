---
type: Runbook
title: "GlobalTensor 无两参构造：改用 SetGlobalBuffer"
description: "kernel 里 `GlobalTensor<T> g(ptr, count)` 编译报 no matching constructor；CANN 9.1.0 上须先默认构造再用 SetGlobalBuffer(ptr, count) 绑定。"
tags: [task.debugging, topic.implementation.api_layer.basic_api, topic.compilation]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/GlobalTensor_constructor.md
    role: primary
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/data_structures/GlobalTensor/SetGlobalBuffer.md
    role: primary
created_at: "2026-10-28T09:52:17Z"
updated_at: "2026-10-28T09:52:17Z"
platforms: ["310p"]
---

# GlobalTensor 无两参构造：改用 SetGlobalBuffer

## 现象

310P 迁移的首版 kernel 里，按"指针 + 长度"直觉初始化全局张量：

```cpp
// ✗
GlobalTensor<float> gLse(reinterpret_cast<__gm__ float*>(lseT), count);
```

`bash build.sh` 报：

```
kernel/<generic>.cpp:<line>:25: error: no matching constructor for initialization of 'GlobalTensor<float>'
```

错误集中在 kernel 开头的若干 `GlobalTensor` 声明行（日志里是连续的多行区间），与同一轮出现的 `SymbolOverrideAdd` 是两批独立错误。当时代码刚从"照抄同代算子"进入自写阶段，GlobalTensor 用了 `(ptr, size)` 构造。

## 适用场景

- 工程形态：Kernel 直调 raw-launch；kernel 形参拿到的都是 `GM_ADDR`（`void*`），需要自行绑成 `GlobalTensor`。
- API 路径：Ascend C `GlobalTensor` 初始化，CANN 9.1.0 basic_api。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002）+ CANN 9.1.0。
- 适用粒度：`platform_wide`。
- 路线优先级：`recommended_fastpath`。
- 不适用/未验证：其它 CANN 版本是否存在 `(ptr, count)` 便捷构造未验证。

## 根因

本工具链的 `GlobalTensor<T>` 没有 `(ptr, count)` 两参构造函数。工程内已验证的写法是**默认构造 + `SetGlobalBuffer`**（同代已通过算子即此形）。这点在写代码时容易被 `LocalTensor`/原生指针的习惯带偏：`GlobalTensor` 的构造语义在本版本只有默认构造可用。

## 解决配方

```cpp
// ✓ 声明（可批量声明）+ 逐个绑定
GlobalTensor<float> gLse2, gDlt2, gMask;   // A 域 host 物化
gLse2.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(lse2),
                      static_cast<int64_t>(unitsA) * M64 * C64);
gDlt2.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(dlt2),
                      static_cast<int64_t>(unitsA) * M64 * C64);
gMask.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(maskA),
                      static_cast<int64_t>(unitsA) * nKT * M64 * C64);
```

pointer 形参都是 `void*`（`GM_ADDR`），kernel 侧用 `reinterpret_cast<__gm__ T*>` 转型是自由且零成本的——同一块 GM 在不同分支里可以被绑成不同元素类型（例如同一个 mask 缓冲既可绑 `float` 也可绑 `half`）。

## 判别方法

- 看到 `no matching constructor for initialization of 'GlobalTensor<T>'`，先确认是不是把"指针 + 元素数"直接塞进了构造参数；本版本没有这个重载。
- 若同一轮还有 `SymbolOverrideAdd` 类错误，按两条独立成因分别修：构造错误走默认构造 + `SetGlobalBuffer`，偏移错误走 `operator[]`，不要试图用一次改动同时解释两类报错。

## 设计决策

- 选"默认构造 + `SetGlobalBuffer`"而不是寻找/伪造两参构造：这是工程内同代已通过算子的稳定形态，且 `SetGlobalBuffer` 的语义明确（绑定 GM 基址与元素数）。
- 元素数统一用 `int64_t` 显式转型计算，避免大 shape 下 int32 溢出。

## 系统信息

- SOC：Ascend310P3（DAV_2002）。
- 工具链：CANN 9.1.0，torch-extension 工程，`bash build.sh` 产出 `build/lib<generic>_ops.so`。
- 相关文件：`kernel/<generic>.cpp`（GlobalTensor 声明/绑定段）。

## 完整代码

改前（无匹配构造函数）：

```cpp
// ✗
GlobalTensor<float> gLse(reinterpret_cast<__gm__ float*>(lseT), count);
```

改后（默认构造 + 逐个绑定）：

```cpp
// ✓ 声明（可批量声明）+ 逐个绑定
GlobalTensor<float> gLse2, gDlt2, gMask;   // A 域 host 物化
gLse2.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(lse2),
                      static_cast<int64_t>(unitsA) * M64 * C64);
gDlt2.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(dlt2),
                      static_cast<int64_t>(unitsA) * M64 * C64);
gMask.SetGlobalBuffer(reinterpret_cast<__gm__ float*>(maskA),
                      static_cast<int64_t>(unitsA) * nKT * M64 * C64);
```

## 预防

- 新建 kernel 时直接从同代已通过算子拷 `GlobalTensor` 声明/绑定段，不要手写构造。
- 元素个数（第二参）用 `int64_t` 显式转型计算，避免大 shape 下 int32 溢出。

## 验证信号

来源：一次 310P 迁移会话的首轮编译失败→改为默认构造 + `SetGlobalBuffer`→重建。

- 修复前 `bash build.sh` 报 `error: no matching constructor for initialization of 'GlobalTensor<float>'`（来源平台：310P；证据等级：tool_observed）。
- 同批改写完成后 `bash build.sh` 退出码 0，打印 `BUILD_OK: build/lib<generic>_ops.so`（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- `SetGlobalBuffer` 的第二个参数是**元素个数**，不是字节数；传字节数不会报错但会越界读写。
- 只在 CANN 9.1.0 实测；其它版本未验证。

## 坏实践

- 用 `GlobalTensor<float> g; g.SetGlobalBuffer(...)` 之外的花样（如先 `reinterpret_cast` 成别的容器再强转）绕过——没必要且引入未定义行为。

## 误诊

无（报错文本直接指明缺失匹配构造函数，未出现归因发散；直接按“默认构造 + `SetGlobalBuffer`”改写即通过）。

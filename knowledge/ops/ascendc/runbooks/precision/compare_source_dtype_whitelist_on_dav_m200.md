---
type: Runbook
title: Compare 源只收 half/float；Duplicate 不收 int8
description: 310P 上想把掩码压成 int8/int16 省带宽，连续撞 Duplicate 与 Compare 的 dtype 白名单；最终只能落 half。附各 API 的实际白名单与三处编译陷阱。
tags: [task.debugging, topic.precision, topic.implementation.api_layer.basic_api, topic.implementation.masking]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/impl/basic_api/dav_m200/kernel_operator_vec_cmpsel_impl.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/impl/basic_api/dav_m200/kernel_operator_vec_duplicate_impl.h
    role: implementation
created_at: "2026-10-28T09:51:16Z"
updated_at: "2026-10-28T09:51:16Z"
platforms: ["310p"]
---

# Compare 源只收 half/float；Duplicate 不收 int8

## 现象

Ascend310P3 的注意力反向算子想把 A 域掩码从 f32 压到 int8（省 4× 带宽、免 f32 物化核）。改完连续撞四个互不相同的编译/静态断言错误，每一个都把方案往回推一档：

```
kernel/kernel_entry.cpp:255:5: error: no matching function for call to 'Duplicate'
kernel/kernel_entry.cpp:206:17: error: no member named 'Reinterpret' in 'AscendC::LocalTensor<short>'
dav_m200/kernel_operator_vec_cmpsel_impl.h:38:27: error: the 2nd parameter maybe need a type '__ubuf__ half *'
dav_m200/kernel_operator_vec_duplicate_impl.h:28:5: error: static assertion failed due to requirement
    'SupportType<signed char, half, short, unsigned short, int, unsigned int, float>()'
```

注意最后一条：**报错里列出的白名单本身就不含 `signed char`**——`Duplicate` 的 `int8` 不是“漏了某个重载”，是被静态断言明确拒绝。

## 适用场景

- 工程形态：kernel 直调；把 0/1 掩码或小整数常量搬到 UB 后参与 `Compare`/`Select`/算术。
- API 路径：`Duplicate(dst, scalar, count)`、`Compare(dst, src0, src1, CMPMODE, count)`、`LocalTensor` 的换型视图。
- 验证过的平台与 CANN 版本：Ascend310P3（dav-m200 / DAV_2002）+ CANN 9.1.0。
- 适用粒度：`platform_wide`（本代际 `Duplicate`/`Compare` 的 dtype 实例化集合）。
- 路线优先级：`safety_fallback`（掩码统一用 half）。
- fallback 声明：当 `Compare` 源或 `Duplicate` 的 dtype 白名单不允许窄类型时，回退到 half 掩码；half 相对 f32 仍有 2× 带宽收益，且 0/1 在 f16 上无损。只有在确认目标代际白名单更宽时才改用更窄类型。
- 明确不适用 / 未验证场景：其它代际白名单可能不同，须按本机头文件核对。

## 判别方法

**根因**：dav_m200 的两个向量 API 白名单不同，且都窄于直觉：

- `Compare` 的**源**只实例化 `SupportType<T, half, float>()`（头文件 `kernel_operator_vec_cmpsel_impl.h` 第 156/164 行附近）；int8/int16/int32 一律编译失败，报错文案是误导性的 `the 2nd parameter maybe need a type '__ubuf__ half *'`。
- `Compare` 的**目的**可以是 int8——B 域一直在用 `Compare(keepM_int8, f32src, f32src, LE)` 且逐位正确。所以“Compare 不能用于 int8”是错的说法，准确说法是“**源**不能是 int8”。
- `Duplicate` 实例化 `half / int16 / uint16 / int32 / uint32 / float`，**没有 int8**。

叠起来的效果：想给 `Compare` 一个窄源 → int8 不行、int16 也不行 → 只剩 half（float 也行但更宽）。而 half 能同时满足 `Duplicate`（造零张量）与 `Compare`（源），所以 half 是唯一自洽的窄掩码类型（0/1 在 f16 上无损）。

三处语法陷阱：

1. `LocalTensor` 没有 `Reinterpret<T>()` 成员（该工具链的 `LocalTensor<short>` 上不存在此方法）；同一 `TBuf` 用 `buf.Get<另一种T>()` 取换型视图即可。
2. 本 kernel 里半精度类型名是 `half`，**不是** `half_t`（`error: unknown type name 'half_t'; did you mean 'half'`）。
3. 常量要显式同型，否则模板推导失败：`Duplicate(zeroH, (half)0, N)`，写裸 `0` 会因 `T` 同时出现在 dst 与 scalar 参数上而推导冲突。

判别步骤：直接读 `SupportType<...>` 那一行，不要按报错文案字面猜测；分别核对源侧与目的侧白名单。

## 解决配方

**after（掩码统一 half：Duplicate 造零、Compare 出 sel，verbatim）**：

```cpp
// ✓ 掩码统一 half：Duplicate 造零、Compare 出 sel
GlobalTensor<half> gMaskI;                       // lean: f16 keep 掩码
gMaskI.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(maskA), elems);
...
pipe.InitBuffer(maskI8Buf, M64 * C64 * sizeof(half));
pipe.InitBuffer(z16Buf, 2 * M64 * C64 * sizeof(half));
LocalTensor<half> maskH = maskI8Buf.Get<half>();
LocalTensor<half> zeroH = z16Buf.Get<half>();
Duplicate(zeroH, (half)0, M64 * C64);            // Duplicate 无 int8，half 可
...
Compare(keepM, maskH, zeroH, CMPMODE::NE, M64 * C64);   // 源须 half/float
Select(z, keepM, z, negOneM, SELMODE::VSEL_TENSOR_TENSOR_MODE, M64 * C64);
```

**before（三步都不行，别浪费时间）**：

```cpp
// ✗ 三步都不行
Duplicate(zeroI8M, 0, M64 * C64);        // int8 不在白名单 → static_assert
zeroI16.Reinterpret<int8_t>();           // LocalTensor 无 Reinterpret 成员
Compare(keepM, maskI16, zeroI16, CMPMODE::NE, N);   // 源 int16 也不行
```

换型视图的正确写法（同一 `TBuf` 取不同 T）：

```cpp
LocalTensor<half> zeroH = z16Buf.Get<half>();   // 同块内存，换 T 视图；非 Reinterpret
```

## 设计决策

- 停在 half 而不是继续找 int8 表示：`Compare` 源白名单是硬约束，绕开它等于放弃“硬件 Compare 生成 sel”（那又回到 host 手搓编码的坑）。half 相对 f32 已有 2× 收益，且无需 host 侧 permute。
- host 侧只做一次 `keepT.to(torch::kHalf)`，不做 permute/contiguous：跨行 strided 装载由 kernel 的 `DataCopyParams(srcStride)` 承担。
- 路线优先级：safety_fallback。

## 系统信息

- 平台：Ascend310P3（dav-m200 / DAV_2002），CANN 9.1.0。
- 相关头文件：`dav_m200/kernel_operator_vec_cmpsel_impl.h`（Compare 源白名单）、`dav_m200/kernel_operator_vec_duplicate_impl.h`（Duplicate 白名单）。
- 相关文件：`kernel/kernel_entry.cpp`（掩码段）、`host/host_stage.cpp`（`keepT.to(torch::kHalf)`）。

## 完整代码

half 掩码路径的完整因果单元：

```cpp
GlobalTensor<half> gMaskI;
gMaskI.SetGlobalBuffer(reinterpret_cast<__gm__ half*>(maskA), elems);

pipe.InitBuffer(maskI8Buf, M64 * C64 * sizeof(half));
pipe.InitBuffer(z16Buf, 2 * M64 * C64 * sizeof(half));
LocalTensor<half> maskH = maskI8Buf.Get<half>();
LocalTensor<half> zeroH = z16Buf.Get<half>();
Duplicate(zeroH, (half)0, M64 * C64);
Compare(keepM, maskH, zeroH, CMPMODE::NE, M64 * C64);
Select(z, keepM, z, negOneM, SELMODE::VSEL_TENSOR_TENSOR_MODE, M64 * C64);
```

## 性能影响

half 掩码相对 f32 掩码有 2× 带宽收益；相对 int8 方案多一倍带宽，但 int8 不可用于 `Compare` 源，无法成立。本卡未做受控 A/B，只记录方向。

## 预防

- 看报错文案字面意思去猜（`__ubuf__ half *` 会被误读成“指针类型问题”），应当直接读 `SupportType<...>` 那一行。
- 按“先 int8 不行就换 int16”的顺序试：两个都不在 `Compare` 源白名单里，白烧两轮编译。
- 用 `Reinterpret` 做换型（该工具链无此成员）；`TBuf::Get<T>()` 才是可用手段。
- 跨版本时先核对本机头文件的白名单，不要外推。

## 验证信号

来源说明：一次 Ascend310P3 注意力反向迁移会话，逐个编译错误 + 头文件读取 + 回归对拍。

- `Duplicate` 传 int8 时静态断言列出白名单 `half/int16/uint16/int32/uint32/float`（无 `signed char`）（来源平台：310P；证据等级：tool_observed）。
- `Compare` 源为 int8 与 int16 时均报 `the 2nd parameter maybe need a type '__ubuf__ half *'`；读头文件确认 `SupportType<T, half, float>()`（来源平台：310P；证据等级：tool_observed）。
- 改 half 后编译通过（`BUILD_OK`），且 B 域“`Compare` 目的为 int8 + f32 源”始终可用，说明限制只在源侧（来源平台：310P；证据等级：tool_observed）。
- half 掩码路径最终 9 例回归与参考逐位相同（与另一处 tile 偏移修正同轮）（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- 结论绑定 CANN 9.1.0 的 dav_m200 实现；白名单以本机头文件为准，跨版本需重查。
- half 掩码只能在 0/1（或 f16 可精确表示的小整数）场景用；若掩码要表达大整数阈值，f16 会丢精度。
- `Duplicate` 的 int16 支持**不能**外推到 `Compare`——两者白名单不同，这是本卡最容易踩错的一处。
- 未决项：`Compare` 源白名单在更晚版本是否放宽未验证。

## 坏实践

- 看报错文案字面意思去猜而不读 `SupportType<...>`。
- 按“先 int8 不行就换 int16”的顺序试，白烧两轮编译。
- 用 `Reinterpret` 做换型；`TBuf::Get<T>()` 才是可用手段。

## 误诊

- 误诊：把 `Compare` 的源类型白名单当成与 `Duplicate` 相同（agent_reported）；两者 `SupportType` 不同，`Duplicate` 支持 int16 不能外推到 `Compare`。

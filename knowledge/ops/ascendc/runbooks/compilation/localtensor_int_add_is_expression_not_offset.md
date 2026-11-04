---
type: Runbook
title: "LocalTensor 加整数不是偏移：报 SymbolOverrideAdd"
description: "AscendC kernel 里用 `tensor + offset` 当指针算术，编译报 could not match 'LocalTensor' against 'SymbolOverrideAdd'；偏移一律改写 `tensor[offset]`。"
tags: [task.debugging, topic.implementation.api_layer.basic_api, topic.compilation]
status: stable
sources:
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/include/basic_api/kernel_tensor.h
    role: header
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/impl/basic_api/kernel_operator_symbol_override_impl.h
    role: implementation
  - resource: https://gitcode.com/cann/asc-devkit/blob/8746f7ced6cef47e3fd7abd64c0eb827e28e2b56/docs/zh/api/SIMD-API/basic_api/data_structures/LocalTensor/operator.md
    role: supporting
created_at: "2026-10-28T09:52:17Z"
updated_at: "2026-10-28T09:52:17Z"
platforms: ["310p"]
---

# LocalTensor 加整数不是偏移：报 SymbolOverrideAdd

## 现象

把某 attention 类算子按 Ascend C 直调（torch-extension raw-launch）形态迁移到 310P，第一次写完整 kernel 后执行 `bash build.sh`，编译失败。日志里同一批出现两类错误，其中主因这一类报在向量算子与 DataCopy 调用上：

```
/usr/local/Ascend/cann-9.1.0/aarch64-linux/asc/include/basic_api/../../impl/basic_api/kernel_operator_vec_binary_scalar_intf_impl.h:179:24: note:
      candidate template ignored: could not match 'LocalTensor' against 'SymbolOverrideAdd'
__aicore__ inline void Adds(const LocalTensor<T>& dst, const LocalTensor<T>& src, const U& scalarValue,
                       ^
error: invalid operands to binary expression ('SymbolOverrideAdd<float>' and 'int')
error: no matching function for call to 'DataCopy(...)'      // 同一处连带报错
```

也就是说：传给 `Adds`/`DataCopy` 的那个实参**根本不是 LocalTensor**，而是 `LocalTensor + int` 求值出来的 `SymbolOverrideAdd<float>` 表达式对象。编译器的重载诊断把这层"实参是表达式模板"暴露了出来。

诱发写法（读出/写回阶段常见的指针风格偏移）：

```cpp
// ✗ 以为 tensor + off 是"首地址 + off 个元素"
Adds(z + r * C64, src, 0.0f, C64);
DataCopy(gDq[base], z + r * C64, DataCopyParams(1, 4, 0, 0));
stripsA(a16ds + 64, l1aP0, 2 * M64 * C64);
```

## 适用场景

- 工程形态：Kernel 直调（torch-extension raw-launch，`TORCH_LIBRARY_FRAGMENT(npu)` + host 侧 `doLaunch`）。
- API 路径：Ascend C basic API（`LocalTensor`/`GlobalTensor` 重载的向量算子与 `DataCopy`），CANN 9.1.0 的 basic_api 头。
- 验证过的平台与 CANN 版本：Ascend310P3（DAV_2002 / dav_m200）+ CANN 9.1.0（`/usr/local/Ascend/cann-9.1.0`）。
- 适用粒度：`platform_wide`（这是 `LocalTensor` 的运算符重载语义，不限于本算子）。
- 路线优先级：`recommended_fastpath`（写入即用 `operator[]`）。
- 不适用/未验证：CANN 其它版本是否同样把 `+` 重载为逐元素加未验证（推断同源实现行为一致，未验证）。

## 根因

`LocalTensor` 上定义了 `operator+`，它是**逐元素加法表达式模板**（`SymbolOverrideAdd`），返回的不是 tensor 而是惰性表达式对象；它不表示"地址后移"。因此 `tensor + off` 在任何接受 `const LocalTensor&` 的接口里都类型不匹配：向量算子的模板推导失败（打印 `could not match 'LocalTensor' against 'SymbolOverrideAdd'`），`DataCopy` 则是没有能吃掉表达式对象的重载。

Ascend C 的偏移语义只有一种写法：`tensor[offset]`（返回以该元素为起点的视图），与工程内同代已通过算子的用法一致。

## 解决配方

先把所有 `tensor + off` 全量改写为 `tensor[off]`（含多维偏移，先长模式后短模式，避免长模式被短模式先替换掉）：

```cpp
// ✓ 修复后
Adds(z[r * C64], src, 0.0f, C64);
DataCopy(gDq[base], z[r * C64], DataCopyParams(1, 4, 0, 0));
stripsA(a16ds[64], l1aP0, 2 * M64 * C64);
```

同一轮里另有一类独立错误（`GlobalTensor` 两参构造不存在），见同 area 的 GlobalTensor 构造卡；两类都修完后 `bash build.sh` 打印 `BUILD_OK: build/lib<generic>_ops.so`。

## 判别方法

- 编译报 `SymbolOverride*` / `invalid operands to binary expression ('SymbolOverrideAdd<...>' and ...)` 时，先回到实参的构造处，确认它是不是 `tensor + 数字/变量` 的求值结果，而不是怀疑被测 API 的签名。
- 同一文件里若 `Adds`/`DataCopy` 同时报"参数类型不匹配"，用 `grep -nE '\b[a-zA-Z_][a-zA-Z0-9_]* *\+' kernel/*.cpp` 把所有"张量名 + 运算"扫一遍，通常能一次找齐同类写法。

## 设计决策

- 选"全量改写为 `operator[]`"而不是逐个报错点打补丁：同类写法在 kernel 里有十几处，漏一处会继续编译失败；一次性替换后残差检查才可控。
- 不选"给 `operator+` 结果做显式类型转换/重载适配"：表达式对象没有稳定的内存语义，转换只会把编译期问题推迟成运行期问题。

## 系统信息

- SOC：Ascend310P3（DAV_2002 / dav_m200）。
- 工具链：CANN 9.1.0（basic_api 头），torch-extension 工程，`bash build.sh` 产出 `build/lib<generic>_ops.so`。
- 相关文件：`kernel/<generic>.cpp`（向量算子与 DataCopy 的偏移写法）。
- 编译日志：`<build-dir>/build.log`（失败与成功两轮）。

## 完整代码

改前（错误写法）：

```cpp
// ✗ tensor + off 求值为 SymbolOverrideAdd 表达式
Adds(z + r * C64, src, 0.0f, C64);
DataCopy(gDq[base], z + r * C64, DataCopyParams(1, 4, 0, 0));
stripsA(a16ds + 64, l1aP0, 2 * M64 * C64);
```

改后（可编译写法）：

```cpp
// ✓ 偏移用 operator[]，返回以该元素为起点的视图
Adds(z[r * C64], src, 0.0f, C64);
DataCopy(gDq[base], z[r * C64], DataCopyParams(1, 4, 0, 0));
stripsA(a16ds[64], l1aP0, 2 * M64 * C64);
```

## 预防

- 写 kernel 前把工程里已跑通的同代算子通读一遍：它们全篇用 `tensor[off]`，从不出现 `tensor + off`。
- 批量替换后做残差检查：`grep -nE '\b(z|dp|dst|src|a16|tD|t2) *\+' kernel/*.cpp`，确认没有"tensor 名 + 数字/变量"残留。
- 编译报 `SymbolOverrideAdd` / `SymbolOverride*` 时，先找该实参的构造处，而不是怀疑 API 签名。

## 验证信号

来源：一次 310P 迁移会话中，新写 kernel 首轮编译失败→改写偏移写法→重建成功的完整闭环。

- 修复前 `bash build.sh` 失败，`<build-dir>/build.log` 同时列出 `could not match 'LocalTensor' against 'SymbolOverrideAdd'` 与 `invalid operands to binary expression ('SymbolOverrideAdd<float>' and 'int')`（来源平台：310P；证据等级：tool_observed）。
- 改写后同一命令 `exit=0`，末尾打印 `BUILD_OK: build/lib<generic>_ops.so`（来源平台：310P；证据等级：tool_observed）。

## 失效边界

- `tensor[off]` 是**元素**偏移，不是字节偏移；跨数据类型混用（同一 UB 缓冲用不同 `T` 取视图）时需要自行按元素个数换算，否则会得到"看起来偏移了但数值错位"的静默错误。
- 本结论只在 CANN 9.1.0 的 `asc/include/basic_api` 上实测；其它 CANN/编译器的重载集合未验证。

## 坏实践

- 用 `reinterpret_cast<LocalTensor<T>&>(tensor + off)` 强行绕过编译错误——表达式对象没有对应内存布局，绕过后行为未定义。
- 逐个报错点打补丁而不做全量 `grep`：同类写法在 kernel 里有十几处，漏一处就继续编译失败。

## 误诊

无（`SymbolOverrideAdd` 报错已直接指向“`tensor + int` 构造了表达式对象”，未出现归因发散）。

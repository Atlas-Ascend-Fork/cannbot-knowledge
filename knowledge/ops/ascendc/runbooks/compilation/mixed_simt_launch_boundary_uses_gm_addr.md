---
type: "Runbook"
title: "混合 SIMT 启动边界用 GM_ADDR 承接地址空间"
description: "混合 SIMT 的 host launch 实参先以 GM_ADDR 穿过 __global__ wrapper，再在 device 侧恢复具体 __gm__ 指针，避免地址空间类型转换失败。"
tags: ["task.implementation", "topic.implementation.api_layer.simt_api"]
status: stable
sources: []
created_at: "2026-08-14T03:13:06Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# 混合 SIMT 启动边界用 GM_ADDR 承接地址空间

## 现象

在 Ascend950 Flash 工程中编写混合 SIMT kernel：host 侧用 `<<<numBlocks, nullptr, aclStream>>>` 启动 `__global__ __aicore__ __vector__` wrapper，wrapper 再调用 `asc_vf_call`。执行远端 CMake 构建时，Bisheng 在每个 dtype 实例化上重复报告：

```text
candidate function template not viable: no known conversion from
'__gm__ uint8_t *' to '__gm__ int64_t *' for 4th argument
error: no matching function for call to 'gather_kernel'
19 errors generated.
```

当时代码已经把 host tensor 地址显式转成 `GM_ADDR`，但 `gather_kernel` 形参仍直接写成 `__gm__ int64_t*`、`__gm__ X_T*` 等具体类型，因此错误发生在 host launch ABI 到 device wrapper 的边界，而不是 VF 内部计算。

## 适用场景

- 工程形态：Ascend C kernel 直调，host C++ 扩展通过 `<<<>>>` 启动混合 SIMT wrapper；
- API 路径：`at::Tensor::data_ptr()` → `GM_ADDR` → `__global__ __aicore__ __vector__` → `asc_vf_call`；
- 验证过的平台与版本：Ascend950 / dav-3510，CANN 9.0.1；与 frontmatter `platforms` 一致；
- 适用粒度：`platform_wide`，针对该工具链下 host/device 混合编译边界的地址空间 ABI；
- 路线优先级：`recommended_fastpath`，这是本轨迹中唯一通过编译验证的启动边界类型形态，不代表已证明性能最优；
- 明确不适用：纯 device 内部函数之间已经处于同一 `__gm__` 地址空间的调用；未验证其他 CANN 版本对 typed `__gm__` wrapper 形参的接受程度。

## 根因

混合编译的 `<<<>>>` host launch 边界按 `GM_ADDR`（`__gm__ uint8_t*`）封送地址，而 wrapper 形参提前收窄成具体 `__gm__ T*`，Bisheng 不在该边界隐式转换不同 pointee 类型的地址空间指针。

## 解决配方

让 host launch 和 `__global__` wrapper 的全部地址形参都保持 `GM_ADDR`；进入 device wrapper 后，再显式恢复 VF 所需的具体 `__gm__ T*` 类型。

以下代码均 verbatim 来自开发会话对 `operators/gather/gather.asc` 的完整写入快照；轨迹未提供这些中间快照的独立 Git revision 或 blob URL。

### before

路径：`operators/gather/gather.asc`；symbol：`gather_kernel<X_T, INDICES_T>`；revision：开发会话修复前写入快照。

```cpp
template <typename X_T, typename INDICES_T>
__global__ __aicore__ __vector__ void gather_kernel(
    uint64_t count,
    int32_t dim,
    int32_t ndim,
    __gm__ int64_t* xStride,
    __gm__ int64_t* outStride,
    __gm__ X_T* x,
    __gm__ INDICES_T* index,
    __gm__ X_T* y)
{
    asc_vf_call<gather_vf<X_T, INDICES_T>>(
        dim3(GATHER_THREADS),
        count, dim, ndim, xStride, outStride, x, index, y);
}
```

路径：`operators/gather/gather.asc`；symbol：`launch_gather<X_T, INDICES_T>`；revision：开发会话修复前写入快照。

```cpp
template <typename X_T, typename INDICES_T>
static inline void launch_gather(int64_t numBlocks, aclrtStream aclStream,
    uint64_t count, int32_t dim, int32_t ndim,
    __gm__ int64_t* xStrideDev, __gm__ int64_t* outStrideDev,
    const at::Tensor& x, const at::Tensor& index, const at::Tensor& y)
{
    gather_kernel<X_T, INDICES_T><<<numBlocks, nullptr, aclStream>>>(
        count, dim, ndim,
        (GM_ADDR)xStrideDev, (GM_ADDR)outStrideDev,
        (GM_ADDR)x.data_ptr(), (GM_ADDR)index.data_ptr(), (GM_ADDR)y.data_ptr());
}
```

### after

路径：`operators/gather/gather.asc`；symbol：`gather_kernel<X_T, INDICES_T>`；revision：开发会话修复后写入快照。

```cpp
template <typename X_T, typename INDICES_T>
__global__ __aicore__ __vector__ void gather_kernel(
    uint64_t count,
    int32_t dim,
    int32_t ndim,
    GM_ADDR xStride,
    GM_ADDR outStride,
    GM_ADDR x,
    GM_ADDR index,
    GM_ADDR y)
{
    asc_vf_call<gather_vf<X_T, INDICES_T>>(
        dim3(GATHER_THREADS),
        count, dim, ndim,
        (__gm__ int64_t*)xStride,
        (__gm__ int64_t*)outStride,
        (__gm__ X_T*)x,
        (__gm__ INDICES_T*)index,
        (__gm__ X_T*)y);
}
```

路径：`operators/gather/gather.asc`；symbol：`launch_gather<X_T, INDICES_T>`；revision：开发会话修复后写入快照。

```cpp
template <typename X_T, typename INDICES_T>
static inline void launch_gather(int64_t numBlocks, aclrtStream aclStream,
    uint64_t count, int32_t dim, int32_t ndim,
    GM_ADDR xStrideDev, GM_ADDR outStrideDev,
    const at::Tensor& x, const at::Tensor& index, const at::Tensor& y)
{
    gather_kernel<X_T, INDICES_T><<<numBlocks, nullptr, aclStream>>>(
        count, dim, ndim,
        xStrideDev, outStrideDev,
        (GM_ADDR)x.data_ptr(), (GM_ADDR)index.data_ptr(), (GM_ADDR)y.data_ptr());
}
```

## 设计决策

- 选择把类型恢复放在 device wrapper 内，因为 `GM_ADDR` 是 host launch 已实际使用的封送类型；这让 ABI 边界保持统一，同时保留 VF 内部的具体类型访问。
- 放弃“host 侧继续传 `GM_ADDR`、wrapper 直接声明 typed `__gm__ T*`”的写法；编译器已用 19 个模板实例化错误证明该边界不做隐式转换。
- 当前方案归为 `recommended_fastpath`：它是正确的 ABI 基线；轨迹没有对不同 wrapper 形态做性能比较。

## 系统信息

- Toolchain：CANN 9.0.1，Bisheng，目标架构 dav-3510；
- 平台：Ascend950；
- 相关文件：`operators/gather/gather.asc`；
- 相关符号：`GM_ADDR`、`gather_kernel`、`launch_gather`、`asc_vf_call`。

## 预防

- 审查混合 SIMT 直调代码时，把 `<<<>>>` 两侧单独当作 ABI 边界检查，不要把 device 内部可接受的 typed `__gm__` 指针规则外推到 host launch。
- host tensor 地址若已经转成 `GM_ADDR`，wrapper 形参也保持 `GM_ADDR`；只在进入 VF 前恢复具体类型。
- 遇到同一 `no known conversion from '__gm__ uint8_t *'` 在多个 dtype 模板上成批出现，先查 wrapper 形参，不要逐个改 dtype dispatch。

## 验证信号

来源说明：这条知识来自一次 Ascend950 Flash kernel 直调开发会话中的远端 CMake/Bisheng 构建；修复前和修复后都由同一远端构建入口实测。

- 修复前构建对多个 dtype 实例化累计报告 `19 errors generated`，核心信号为 `no known conversion from '__gm__ uint8_t *' to '__gm__ int64_t *'`（来源平台：950；证据等级：tool_observed）。
- 改成 wrapper/launch 全部使用 `GM_ADDR` 后，下一次构建不再出现该地址空间转换错误，而推进到独立的 `dim3` 名称解析错误（来源平台：950；证据等级：tool_observed）。
- 后续同时修复独立的 `asc_vf_call` 头文件问题后，同一代码路径完成 `Linking ASC shared library libop_gather.so` 和 `Built target op_gather`（来源平台：950；证据等级：tool_observed）。

## 失效边界

- 该配方只处理 host launch ABI 的地址空间类型，不解决 VF 启动重载、线程配置或索引地址公式问题。
- A2/A3 未验证；不同 CANN 版本可能改变 host/device 混合编译规则，未验证，推断可迁移。
- 如果报错发生在纯 device 函数调用内部，应按实际 pointee 类型和地址空间重新定位，不能机械套用 `GM_ADDR`。

## 坏实践

- 在 host 调用点强转为 `GM_ADDR` 后，仍让 `__global__` wrapper 直接接收 `__gm__ T*`，期待编译器跨 ABI 边界自动恢复 pointee 类型。
- 把同一根因产生的多 dtype 模板错误当成多个独立问题逐一修补。

## 误诊

- 该错误不是 `int8/int32/int64` dtype dispatch 缺分支；不同实例化只是重复暴露同一个 wrapper 形参问题。
- 它也不是 `asc_vf_call` 参数数量问题；修复地址空间边界后出现的 `dim3`/参数数量错误属于另一根因。

<!-- cannbot:related:start -->
## 相关

- [CANN 9.0.1 SIMT 入口类型无法派生—改混合 VF](mixed_simt_requires_vector_shell_and_simt_vf.md)（`related`）：《CANN 9.0.1 SIMT 入口类型无法派生—改混合 VF》明确“CANN 9.0.1 的混合 ASC 动态库中，纯 SIMT 全局入口无法稳定完成 kernel 类型派生；改用 Vector 入口承载 SIMT VF 和三参数 launch。”；它与《混合 SIMT 启动边界用 GM_ADDR 承接地址空间》的“混合 SIMT 的 host launch 实参先以 GM_ADDR 穿过 __global__ wrapper，再在 device 侧恢复具体 __gm__ 指针，避免地址空间类型转换失败。”在实际调用参数、数据流或结果校验上直接衔接。
- [Device helper 必须保留 GM 地址空间](device_helper_preserves_gm_address_space.md)（`related`）：混合 launch 边界先用 GM_ADDR 封送、进入 device 后恢复 typed __gm__；focal 则要求恢复后的 typed __gm__ 继续穿过 helper 和成员，两卡首尾衔接。
- [SIMT 核类型推导失败 — 补 __vector__](direct_launch_kernel_requires_vector_qualifier.md)（`related`）：SIMT 核类型推导失败 — 补 __vector__：故障的直接修复是为承载 asc_vf_call 的 shell补 __vector__；混合 VF与空 kernel卡复现同一 kernel-type推导机制，官方限定符页给出合法调用层级，header/GM_ADDR卡补齐启动边界。 目标卡《混合 SIMT 启动边界用 GM_ADDR 承接地址空间》补充：混合 SIMT 的 host launch 实参先以 GM_ADDR 穿过 __global__ wrapper，再在 device 侧恢复具体 __gm__ 指针，避免地址空间类型转换失败。
- [dim3 未声明：显式引入 SIMT 公共头](asc_vf_call_launch_config_requires_simt_header.md)（`related`）：《dim3 未声明：显式引入 SIMT 公共头》处理“混合 SIMD/SIMT 核函数调用 asc_vf_call 时，显式包含 common_functions.h 以暴露 dim3 别名和正确重载。”。《混合 SIMT 启动边界用 GM_ADDR 承接地址空间》明确“混合 SIMT 的 host launch 实参先以 GM_ADDR 穿过 __global__ wrapper，再在 device 侧恢复具体 __gm__ 指针，避免地址空间类型转换失败。”，可直接用于核对dim3 类型可见性、SIMT 公共头、__vector__ 入口与混合 VF 启动边界。
- [纯 SIMT kernel 形参 __gm__ 导致编译失败](pure_simt_parameters_do_not_use_gm_qualifier.md)（`related`）：两卡共同划清执行模型边界：纯 SIMT 入口移除 __gm__，而混合 __global__ Vector wrapper 必须以 GM_ADDR 穿过 Host launch 后在 device 内恢复 __gm__ 指针。
- [随机 Gather 每元素 DMA 过慢—改 SIMT 直访 GM](../performance/random_gather_per_element_dma_should_switch_to_simt_direct_gm.md)（`related`）：若采用 focal 示例中的 Vector wrapper+SIMT VF，Host launch 必须先用 GM_ADDR 过 ABI 边界，再在 wrapper 内恢复 __gm__ T*；否则多 dtype 实例都会地址空间转换失败。
- [GM_ADDR 标量不可解引用为 tiling 结构体指针](gm_addr_tiling.md)（`same_topic`）：GM_ADDR 标量不可解引用为 tiling 结构体指针 与《混合 SIMT 启动边界用 GM_ADDR 承接地址空间》的实质衔接是：GM_ADDR 在该入口是 __gm__ uint8_t 标量而非结构体指针；typed __gm__ tiling 指针、Kernel Tiling/GET_TILING_DATA 和地址空间案例给出正确入口与强转边界。
- [dav-3510 GM_ADDR static_cast 编译失败](gm_addr_cast_from_void_uses_toolchain_cast.md)（`same_topic`）：《dav-3510 GM_ADDR static_cast 编译失败》明确“dav-3510 ASC 编译器拒绝 void* 到 __gm__ 地址空间指针的 static_cast；direct-launch host 入口改用 GM_ADDR C 风格转换。”；它与《混合 SIMT 启动边界用 GM_ADDR 承接地址空间》的“混合 SIMT 的 host launch 实参先以 GM_ADDR 穿过 __global__ wrapper，再在 device 侧恢复具体 __gm__ 指针，避免地址空间类型转换失败。”在实际调用参数、数据流或结果校验上直接衔接。
<!-- cannbot:related:end -->

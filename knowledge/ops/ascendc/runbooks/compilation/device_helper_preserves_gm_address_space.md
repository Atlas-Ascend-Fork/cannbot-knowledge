---
type: "Runbook"
title: "Device helper 必须保留 GM 地址空间"
description: "Ascend C kernel 入口把 __gm__ int64_t* 传入 device helper 的 plain const int64_t* 时触发地址空间类型错误；参数与持久成员均保留 __gm__ 后恢复构建。"
tags: ["task.debugging", "topic.programming_model.language_extension", "topic.data_movement.memory_access"]
status: stable
sources: []
created_at: "2026-08-14T03:54:37Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["a3"]
---

# Device helper 必须保留 GM 地址空间

## 现象

在 A3/dav-2201 的 classic Ascend C direct-launch 工程中，Stage-2 `gather.asc` 已包含 `__global__ __vector__` 入口、device helper class 与 torch_npu host 注册。执行：

```text
cmake -S . -B build -DCMAKE_ASC_ARCHITECTURES=dav-2201
cmake --build build --parallel "$(nproc)"
```

bisheng 在 `gather_kernel<T>` 调用 `KernelGather<T>::Init` 时拒绝形参转换；各 dtype 模板实例重复报同一错误：

```text
error: cannot initialize a parameter of type 'const int64_t *'
       with an lvalue of type '__gm__ int64_t *'
op.Init(..., outShape, xShape, xStrides, ...);
             ^~~~~~~~
note: passing argument to parameter 'outShape' here
6 errors generated.
make: *** [Makefile:91: all] Error 2
```

kernel 入口的 shape/stride 参数已经是 `__gm__ int64_t*`，但 helper 的形参与成员退化成普通 C++ 指针，形成了两个不同地址空间的类型。

## 适用场景

- 工程形态：classic Ascend C 直调 kernel 的编译、链接或运行工程。
- API 路径：`__gm__`、`cce_global`、`bisheng`、`address_space` 所在的 kernel、host 或构建接口链。
- 验证平台与版本：平台 a3；CANN：unknown。
- 适用粒度：`exact_task`，只覆盖相同直调入口、helper 签名和 GM 元数据传递链。
- 路线优先级：`recommended_fastpath`。
- 不适用/停止边界：错误信号、API 契约或数据路径与本卡不一致时停止套用；修复后未闭合原信号则回到根因诊断。

## 根因

bisheng 把 `__gm__ int64_t*` 与 plain `const int64_t*` 视为不同地址空间类型，helper 在形参和成员处丢失 `__gm__`，因此入口实参不能隐式降级。

## 解决配方

同时修正 `Init` 的三个输入表形参和对应三个持久成员；只改形参会让赋值到 plain 成员时再次丢失地址空间。

### before

```cpp
template <typename T>
class KernelGather {
public:
    __aicore__ inline KernelGather() {}

    // ndim <= 8 (cases cover 1..5). Strides are in elements, int64 to avoid overflow on big tensors.
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR index, GM_ADDR y,
                                int64_t outNumel,         // total output elements (= index.numel)
                                int64_t elemSize,         // sizeof(T) in bytes
                                int32_t dim,              // gather axis
                                int32_t ndim,
                                const int64_t *outShape,  // == index.shape, length ndim
                                const int64_t *xShape,     // x.shape, length ndim
                                const int64_t *xStrides,  // x strides in elements, length ndim
                                int64_t perBlock) {       // output elements per block
        elemSize_ = elemSize;
        dim_ = dim;
        ndim_ = ndim;
        outShape_ = outShape;
        xStrides_ = xStrides;
        xShape_ = xShape;

        xGm_.SetGlobalBuffer((__gm__ T *)x);
        indexGm_.SetGlobalBuffer((__gm__ uint8_t *)index);  // index dtype varies; read raw bytes
        yGm_.SetGlobalBuffer((__gm__ T *)y);

        uint32_t blockIdx = GetBlockIdx();
        start_ = static_cast<int64_t>(blockIdx) * perBlock;
        count_ = (perBlock < outNumel - start_) ? perBlock : (outNumel - start_);
        if (start_ >= outNumel) {
            count_ = 0;
        }
    }

    __aicore__ inline void Process() {
        // Stage 2 skeleton: no-op (kernel compiles; correctness filled in Stage 6).
    }

private:
    GlobalTensor<T> xGm_;
    GlobalTensor<uint8_t> indexGm_;
    GlobalTensor<T> yGm_;
    int64_t elemSize_;
    int32_t dim_;
    int32_t ndim_;
    const int64_t *outShape_;
    const int64_t *xShape_;
    const int64_t *xStrides_;
    int64_t start_{0};
    int64_t count_{0};
};
```

### after

```cpp
template <typename T>
class KernelGather {
public:
    __aicore__ inline KernelGather() {}

    // ndim <= 8 (cases cover 1..5). Strides are in elements, int64 to avoid overflow on big tensors.
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR index, GM_ADDR y,
                                int64_t outNumel,         // total output elements (= index.numel)
                                int64_t elemSize,         // sizeof(T) in bytes
                                int32_t dim,              // gather axis
                                int32_t ndim,
                                __gm__ const int64_t *outShape,  // == index.shape, length ndim
                                __gm__ const int64_t *xShape,    // x.shape, length ndim
                                __gm__ const int64_t *xStrides, // x strides in elements, length ndim
                                int64_t perBlock) {       // output elements per block
        elemSize_ = elemSize;
        dim_ = dim;
        ndim_ = ndim;
        outShape_ = outShape;
        xStrides_ = xStrides;
        xShape_ = xShape;

        xGm_.SetGlobalBuffer((__gm__ T *)x);
        indexGm_.SetGlobalBuffer((__gm__ uint8_t *)index);  // index dtype varies; read raw bytes
        yGm_.SetGlobalBuffer((__gm__ T *)y);

        uint32_t blockIdx = GetBlockIdx();
        start_ = static_cast<int64_t>(blockIdx) * perBlock;
        count_ = (perBlock < outNumel - start_) ? perBlock : (outNumel - start_);
        if (start_ >= outNumel) {
            count_ = 0;
        }
    }

    __aicore__ inline void Process() {
        // Stage 2 skeleton: no-op (kernel compiles; correctness filled in Stage 6).
    }

private:
    GlobalTensor<T> xGm_;
    GlobalTensor<uint8_t> indexGm_;
    GlobalTensor<T> yGm_;
    int64_t elemSize_;
    int32_t dim_;
    int32_t ndim_;
    __gm__ const int64_t *outShape_;
    __gm__ const int64_t *xShape_;
    __gm__ const int64_t *xStrides_;
    int64_t start_{0};
    int64_t count_{0};
};
```

## 设计决策

1. `const` 只限制写入，不表达 GM/UB/host 地址空间；因此必须写成 `__gm__ const T*`，不能只保留 `const`。
2. 限定从 kernel 入口贯穿 helper 形参和持久成员，避免在任一中间层丢失地址空间。
3. 不用 `reinterpret_cast<const int64_t*>` 强压编译；它会掩盖真实存储位置，属于 `banned` 路线。

## 系统信息

- Toolchain：CANN 9.2.0、bisheng；
- 平台：A3，SocVersion `Ascend910_9362`、NpuArch `dav-2201`；
- 工程：`gather.asc` + torch_npu `TORCH_LIBRARY` direct-launch；
- 构建：`cmake --build build --parallel "$(nproc)"`；
- 证据限制：该 skeleton 快照没有 40 位 Git revision。

## 完整代码

`## 解决配方` 已内联完整 `KernelGather<T>` class before/after，覆盖受影响的 `Init` 与全部指针成员。

## 预防

- 对进入 device 代码的每个 pointer table，在入口、helper 参数、成员和局部别名四处逐级检查地址空间。
- 看到 bisheng 同时打印 plain pointer 与 `__gm__` pointer 时，优先检查类型限定，不要先改 shape 或数据内容。
- 修复后必须让所有模板实例完成 `.asc` compile/link；单个 dtype 的静态检查不足。

## 验证信号

以下信号均来自本次开发会话修复前后的实际构建、运行或评测输出。

- 修复前：设备编译报不能用 __gm__ int64_t* 初始化 const int64_t*。（来源平台：a3；证据等级: tool_observed）。
- 修复后：仅余 4 条 warning，libop_gather.so 链接并完成 built target。（来源平台：a3；证据等级: tool_observed）。

## 失效边界

- 仅验证 a3/dav-2201、CANN 9.2.0 的 classic Ascend C 编译路径。
- `__gm__` 不能机械加到 host 指针、UB `LocalTensor` 或普通 CPU 容器上；限定必须与真实存储空间一致。
- host 编译阶段出现的 `cce_global attribute ignored` warning 与本卡 device 参数错误不同，不能混为同一根因。

## 坏实践

- 用 C 风格 cast 抹掉 `__gm__`，只为让编译器放行。
- 只修改 `Init` 形参，却继续把它存入 plain 成员。
- 把地址空间错误误诊为 int64 宽度、stride 数值或模板 dtype 问题。

## 误诊

报错发生在类型绑定阶段，尚未读取 shape/stride 内容；修改表中数值、元素数量或输入 dtype 都不能修复地址空间不匹配。

<!-- cannbot:related:start -->
## 相关

- [__cvta_generic_to_global](../../apis/simt_api/address_space_conversion_functions/_cvta_generic_to_global.md)（`exemplifies`）：《__cvta_generic_to_global》的任务是“将输入的指针转换为其指向的Global Memory内存空间的地址值并返回。”。《Device helper 必须保留 GM 地址空间》具体提供“Ascend C kernel 入口把 __gm__ int64_t* 传入 device helper 的 plain const int64_t* 时触发地址空间类型错误；参数与持久成员均保留 __gm__ 后恢复构建。”，它直接用于generic 指针转 Global 地址、反向转换和 GM 地址空间验证。
- [__cvta_global_to_generic](../../apis/simt_api/address_space_conversion_functions/_cvta_global_to_generic.md)（`exemplifies`）：《__cvta_global_to_generic》处理“将Global Memory内存空间的地址值转换为对应的指针并返回。”。《Device helper 必须保留 GM 地址空间》明确提供“Ascend C kernel 入口把 __gm__ int64_t* 传入 device helper 的 plain const int64_t* 时触发地址空间类型错误；参数与持久成员均保留 __gm__ 后恢复构建。”，其参数、调用或验证步骤直接接入global/generic 指针互转、GM 地址空间判定与 GlobalTensor 地址帮助器。
- [地址空间转换函数](../../apis/simt_api/address_space_conversion_functions/address_space_conversion_functions.md)（`exemplifies`）：《地址空间转换函数》处理“SIMT API地址空间转换函数汇总，提供generic与Global、UBuf、Local间指针与地址值的双向转换能力。”。《Device helper 必须保留 GM 地址空间》提供“Ascend C kernel 入口把 __gm__ int64_t* 传入 device helper 的 plain const int64_t* 时触发地址空间类型错误；参数与持久成员均保留 __gm__ 后恢复构建。”，其具体合同或探针直接接入SIMT 地址空间转换与谓词验证、helper 形参地址限定合同。
- [GetPhyAddr const __gm__ 返回不可去 const](getphyaddr_const_gm_const.md)（`related`）：focal 保留 __gm__ 之外还需保留 const；该卡证明 GlobalTensor::GetPhyAddr 返回 const __gm__ pointer，强转为可写指针会独立触发 casts-away-qualifiers。
- [混合 SIMT 启动边界用 GM_ADDR 承接地址空间](mixed_simt_launch_boundary_uses_gm_addr.md)（`related`）：混合 launch 边界先用 GM_ADDR 封送、进入 device 后恢复 typed __gm__；focal 则要求恢复后的 typed __gm__ 继续穿过 helper 和成员，两卡首尾衔接。
- [纯 SIMT kernel 形参 __gm__ 导致编译失败](pure_simt_parameters_do_not_use_gm_qualifier.md)（`related`）：纯 SIMT 模式会把 __gm__ 解释成不合法 attribute，恰好给出 focal 规则的停止边界：先判编程模型，再决定 helper/入口是否使用地址空间限定。
- [GM_ADDR 标量不可解引用为 tiling 结构体指针](gm_addr_tiling.md)（`same_topic`）：GM_ADDR 卡说明 tiling 入口必须先恢复为 typed __gm__ 结构指针，helper 卡进一步要求该 __gm__ 地址空间在调用链形参中持续保留；两者闭合同一 GM 指针类型合同。
- [__ubuf__ 指针传普通形参导致编译失败](ubuf_pointer_preserves_address_space.md)（`same_topic`）：__ubuf__ 指针传普通形参导致编译失败 与《Device helper 必须保留 GM 地址空间》的实质衔接是：__ubuf__ 是指针类型的一部分，helper 形参、Load/Store、ReinterpretCast、地址空间转换与谓词必须保留相同 qualifier，不能隐式退化为普通 T*。
<!-- cannbot:related:end -->

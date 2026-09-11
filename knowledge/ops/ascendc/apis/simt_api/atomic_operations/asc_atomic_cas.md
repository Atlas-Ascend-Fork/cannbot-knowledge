---
type: API
title: asc_atomic_cas
description: 对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。
tags:
- task.lookup
- topic.implementation.atomic
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMT-API/atomic_operations/asc_atomic_cas.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/simt_api/device_atomic_functions.h
- include/simt_api/asc_fp16.h
- include/simt_api/asc_bf16.h
---

# asc\_atomic\_cas

## 功能说明

对Unified Buffer（UB）或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。

## 函数原型

```cpp
inline float asc_atomic_cas(float *address, float compare, float val)
```

```cpp
inline int32_t asc_atomic_cas(int32_t *address, int32_t compare, int32_t val)
```

```cpp
inline uint32_t asc_atomic_cas(uint32_t *address, uint32_t compare, uint32_t val)
```

```cpp
inline int64_t asc_atomic_cas(int64_t *address, int64_t compare, int64_t val)
```

```cpp
inline uint64_t asc_atomic_cas(uint64_t *address, uint64_t compare, uint64_t val)
```

```cpp
inline half2 asc_atomic_cas(half2 *address, half2 compare, half2 val)
```

```cpp
inline bfloat16x2_t asc_atomic_cas(bfloat16x2_t *address, bfloat16x2_t compare, bfloat16x2_t val)
```

## 参数说明

**表1**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| address | 输出 | UB或Global Memory的地址。 |
| compare | 输入 | 源操作数，做比较的值。 |
| val | 输入 | 源操作数，用于赋值的值。 |

不同数据类型支持的内存范围说明如下：

**表2**  不同数据类型支持的内存范围

| 参数数据类型 | 支持的内存空间 |
| --- | --- |
| int32_t、uint32_t、float、half2、bfloat16x2_t | UB、Global Memory |
| int64_t、uint64_t | Global Memory |

## 返回值说明

UB或Global Memory上的初始数据。

## 约束说明

-   原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。使用`asc_atomic_cas`实现抢占逻辑时，可保证最多一个线程抢占成功，但不保证固定由哪个线程抢占成功。
-   本接口的性能受以下因素影响，相关原理请参见[原子操作机制](atomic_operations_intro.md#原子操作机制)。
    -   内存空间：UB的访问路径比Global Memory短，通常具有更低的访问开销。当使用的数据类型支持UB（即int32\_t、uint32\_t、float、half2、bfloat16x2\_t）时，建议优先在UB中完成原子操作。
    -   返回值：该接口无对应的性能优化指令，对于所有数据类型，程序中是否使用该接口返回值，接口性能基本一致。
    -   地址分布：Global Memory原子操作经过L2 Cache处理，L2 Cache以512B Cache Line为缓存管理单位，每条Cache Line包含4个128B扇区（Sector），Global Memory原子操作以128B Sector为处理粒度。目标地址集中在同一个Sector内时，处理效率较低；目标地址分布在更多Sector内时，处理效率较高。因此，业务允许时，建议将原子操作的目标地址分散到更多Sector中。

## 需要包含的头文件

使用除half2、bfloat16x2\_t类型之外的接口需要包含`simt_api/device_atomic_functions.h`头文件，使用half2类型接口需要包含`simt_api/asc_fp16.h`头文件，使用bfloat16x2\_t类型接口需要包含`simt_api/asc_bf16.h`头文件。

```cpp
#include "simt_api/device_atomic_functions.h"
```

```cpp
#include "simt_api/asc_fp16.h"
```

```cpp
#include "simt_api/asc_bf16.h"
```

## 调用示例

完整样例请参考[InsertHashTable算子样例](https://gitcode.com/cann/asc-devkit/blob/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/03_simt_api/02_features/01_api_features/00_memory_access/insert_hash_table/README.md)。

简单示例场景为：多个线程尝试抢占同一个任务，任务初始拥有者ID为0。使用`asc_atomic_cas`接口实现只有一个线程抢占成功，其它线程读到非0后抢占失败。输入输出参数说明如下：

| 名称 | 说明 |
| --- | --- |
| `worker_ids` | 每个元素表示一个工作者ID。 |
| `owner` | Global Memory中的任务拥有者，0表示无人占用。 |
| `claim_result` | 保存每个线程是否抢占成功。 |
| `n` | 参与抢占的线程数。 |

核心代码实现如下：

-   SIMT编程场景：

    ```cpp
    __global__ __launch_bounds__(256) void claim_task(uint32_t *owner,
                                                      uint32_t *claim_result,
                                                      uint32_t *worker_ids,
                                                      uint32_t n)
    {
        uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= n) {
            return;
        }

        uint32_t old_owner = asc_atomic_cas(owner, 0U, worker_ids[idx]);
        claim_result[idx] = (old_owner == 0U) ? 1U : 0U;
    }
    ```

-   SIMD与SIMT混合编程场景：

    SIMD与SIMT混合编程场景，需要显式使用地址空间限定符表示地址空间：`__gm__`表示Global Memory内存空间，`__ubuf__`表示UB内存空间。

    ```cpp
    __simt_vf__ __launch_bounds__(1024) inline void claim_task(__gm__ uint32_t *owner,
                                                               __gm__ uint32_t *claim_result,
                                                               __gm__ uint32_t *worker_ids,
                                                               uint32_t n)
    {
        uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= n) {
            return;
        }

        uint32_t old_owner = asc_atomic_cas(owner, 0U, worker_ids[idx]);
        claim_result[idx] = (old_owner == 0U) ? 1U : 0U;
    }
    ```

输出结果示例如下：

```
worker_ids: 101, 102, 103
owner before: 0
owner after: 101/102/103中的一个 // 表明只有一个线程抢占成功
claim_result: 仅一个元素为1
```


<!-- cannbot:related:start -->
## 相关

- [原子操作（AI Core SIMT编程）](../../../guides/programming_guide/programming_model/ai_core_simt_programming/atomic_operations.md)（`explains`）：“对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。”；“原子操作不保证多个线程到达该原子操作的先后顺序，也不是线程同步屏障。”。指南解释 CAS 的并发语义和不提供线程顺序/屏障的边界，直接支撑接口的正确使用。
- [ScatterMax 950 ACLNN 算子知识](../../../operators/aclnn/nn/index/scatter_max_950.md)（`related`）：“重复 `indices` 或并发命中同一元素时，CAS retry loop 把每次最大值更新串行化到该 GM 地址；固定源码没有给出重复索引的确定执行次序保证。”；“原子操作保证对同一地址的读改写过程具有原子性，但不保证多个线程之间的执行顺序。”。CAS API 合同直接解释 ScatterMax 重复索引的同步保证与非确定顺序边界。
- [ScatterMin 950 ACLNN 算子知识](../../../operators/aclnn/nn/index/scatter_min_950.md)（`related`）：“Kernel 对同一目标元素的并发更新使用 CAS 重试；越界 `indices［m］` 直接 `continue`。”与“对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。”提供双方正文证据。ScatterMin 以 CAS 重试保护同一目标元素的并发最小值更新，API 卡定义比较相等才写入并返回旧值的原子合同，解释了重试循环的正确性基础。
- [ScatterMul 950 ACLNN 算子知识](../../../operators/aclnn/nn/index/scatter_mul_950.md)（`related`）：“更新是原地的，Kernel 的 `y` 参数不被读取或写入。重复索引通过 CAS 重试串行化相同目标元素的 read-modify-write；不同线程的成功次序不固定，因此浮点重复乘法的舍入次序也不固定。”与“对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。”提供双方正文证据。ScatterMul 卡明确用 CAS 重试实现重复索引下的原地乘法更新，asc_atomic_cas 卡定义比较成功才写入的原子原语；后者直接解释前者避免同地址更新丢失的机制。
- [AscAtomicCas](../../simd_api/c_api/atomic/scalar_atomic/asc_atomic_cas.md)（`same_topic`）：对Global Memory中address指向的元素执行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。；对Unified Buffer或Global Memory上address的数值进行原子比较赋值操作，如果address上的数值等于指定数值compare，则对address赋值为指定数值val，否则address的数值不变。两卡定义同一 compare-and-swap 决策，分别给出 Scalar C API 的缓存同步合同与 SIMT 的线程竞争合同。
<!-- cannbot:related:end -->

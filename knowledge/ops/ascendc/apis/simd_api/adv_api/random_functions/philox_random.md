---
type: API
title: PhiloxRandom
description: 基于Philox随机数生成算法，给定随机数种子，生成若干的随机数。 Philox随机数生成的核心算法是一个基于记数的伪随机数生成算法，输入为一个128bit的记数器C，两个32bit的key（k0和k1），输出为4个32bit的整数。
tags:
- task.lookup
- topic.implementation.api_layer.high_level_api
- topic.compute.random_sampling
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/random_functions/PhiloxRandom.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
source_headers:
- include/adv_api/math/philox.h
---

# PhiloxRandom

## 功能说明

基于Philox随机数生成算法，给定随机数种子，生成若干的随机数。

Philox随机数生成的核心算法是一个基于记数的伪随机数生成算法，输入为一个128bit的记数器C，两个32bit的key（k0和k1），输出为4个32bit的整数。

## 函数原型

-   连续模式

    ```
    template <uint16_t Rounds = 7, typename T>
    __aicore__ inline void PhiloxRandom(const LocalTensor<T>& dstLocal, const PhiloxKey& philoxKey, const PhiloxCounter& philoxCounter, uint16_t count)
    ```

-   stride模式

    ```
    template <uint16_t Rounds = 7, typename T>
    __aicore__ inline void PhiloxRandom(const LocalTensor<T>& dstLocal, const PhiloxKey& philoxKey, const PhiloxCounter& philoxCounter, const PhiloxRandomParams& params)
    ```

## 参数说明

**表1**  模板参数说明

| 参数名 | 描述 |
| --- | --- |
| Rounds | Philox算法内部实现迭代次数，支持取值7或10。 |
| T | 目的操作数数据类型，支持的数据类型为：uint32_t、int32_t、float。<br><br>其中uint32_t/int32_t为数据类型范围内的均匀分布，float为0-1范围内的均匀分布。 |

**表2**  参数说明

| 参数名 | 输入/输出 | 描述 |
| --- | --- | --- |
| dstLocal | 输出 | 目的操作数。<br><br>类型为[LocalTensor](../../basic_api/data_structures/local_tensor/index.md)，支持的TPosition为VECIN/VECCALC/VECOUT。<br><br>LocalTensor的起始地址需要32字节对齐。 |
| philoxKey | 输入 | 随机数种子。两个32bit的key，定义如下：<br>using PhiloxKey = uint32_t[2]; |
| philoxCounter | 输入 | 随机数种子。一个128bit的记数器C（由4个32bit组成），定义如下：<br>using PhiloxCounter = uint32_t[4]; |
| count | 输入 | 生成目的操作数的元素个数。 |
| params | 输入 | stride模式计算所需的参数信息。PhiloxRandomParams类型，定义如下方代码所示，其中参数的含义为：<br>stride：两行元素之间的间隔。<br>row：表示生成的行数。<br>column：表示生成的每一行的元素个数。<br>请注意：<br>row * column大于0，不大于LocalTensor的大小。<br>column % 4 == 0，stride % 4 == 0，stride >= column。 |

```
struct PhiloxRandomParams {
    uint32_t stride;
    uint32_t row;
    uint32_t column;
};
```

**图1**  PhiloxRandom示意图  
![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/philoxrandom_diagram.png "PhiloxRandom示意图")

上图是一个生成随机数的示意图。

-   连续模式下使用philoxCounter=\{0, 0, 0, 0\}，count=32来生成32个随机数。
-   stride模式下可按列分两次生成，调用两次接口。第一次调用参数为philoxCounter=\{0, 0, 0, 0\}，stride=8，row=4，column=4；第二次调用参数为philoxCounter=\{1, 0, 0, 0\}（每次记数器C自增会生成128bit的随机数），stride=8，row=4，column=4。

## 返回值说明

无

## 约束说明

无

## 调用示例

完整算子样例请参考[philoxrandom样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/04_advanced_api/09_random/philoxrandom)。

```
// dstLocal：存放计算结果的Tensor
// philoxKey={0,0}, philoxCounter={0,0,0,0}

// stride模式，生成32*32个元素
PhiloxRandom<10>(dstLocal, philoxKey, philoxCounter, params);
// 连续模式，生成1024个元素
PhiloxRandom<10>(dstLocal, philoxKey, philoxCounter, 1024);
```

结果示例如下：

```
[0.31179297 0.8263413  0.6849456 ... 0.10521233 0.29894042 0.96700084]
```


<!-- cannbot:related:start -->
## 相关

- [PhiloxRandom 默认 7 rounds 与原生 10 不匹配](../../../../runbooks/precision/philoxrandom_7_rounds_10.md)（`exemplifies`）：基于Philox算法生成随机数，支持生成half/float/int32_t类型的随机数。通过seed和subsequence初始化随机数生成器，可在counter基础上生成指定数量的随机数。；自定义 kernel 调用 `AscendC::PhiloxRandom` 时沿用了 CANN 公共头文件 `philox.h` 的模板默认值 `Rounds=7`，但原生 `aclnnSimThreadExponential` 实际使用 PyTorch 标准 **Philox-4x32-10**（10 rounds）。rounds 数直接决定 Philox 单轮轮函数的迭代次数，7 vs 10 产出的 32 位输出完全不同，因此即使 seed/offset/counter 完全相同，单次调用也 0% 匹配。。API 卡提供 PhiloxRandom 的 seed/subsequence/counter 使用面，runbook 给出与原生 exponential 对齐时必须显式选择 10 rounds 的已验证排障边界。
- [Uint32ToFloat 须用 IEEE754 位操作而非位移乘法](../../../../runbooks/precision/uint32tofloat_ieee754.md)（`exemplifies`）：**API 路径**：AscendC kernel 内 uint32 随机数 → float 转换；对标 CANN `StatelessRandomUniformV2::Uint32ToFloat`（`stateless_random_uniform_v2.h`，arch35 opp 子目录）。；基于Philox算法生成随机数，支持生成half/float/int32_t类型的随机数。通过seed和subsequence初始化随机数生成器，可在counter基础上生成指定数量的随机数。；API 生产由 seed/subsequence/counter 决定的随机流，焦点规定要求 bit-exact 时 uint32 消费到 float 的转换方式。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [SimThreadExponential 950 ACLNN 算子知识](../../../../operators/aclnn/math/random/sim_thread_exponential_950.md)（`related`）：算子声明的固定版本源码包含对 `PhiloxRandom(...)` 的直接调用（第 593 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/random/random_common/op_kernel/arch35/random_kernel_base.h#L593)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->

---
type: API
title: Sort32
description: 一次迭代内对32个数按score域降序排列，结果以score和index的结构存储在目的张量中。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.compute.ordering
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/memory_vector_compute/sort_and_merge_ISASI/Sort32.md
  role: primary
created_at: '2026-09-03T08:52:46Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
source_headers:
- include/basic_api/kernel_operator_proposal_intf.h
---

# Sort32<a name="ZH-CN_TOPIC_0000001487536634"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_operator_proposal_intf.h"`

Sort32接口实现一次迭代内对32个数的降序排列操作。

如下图所示，src0和src1分别表示待排序的数据score和对应RP的索引index，排序完成后以（score, index）的结构存储在dst中。

src1固定为uint32\_t类型，无论src0是float还是half类型，dst中的（score, index）结构总是占据8B空间。其中：

- 当src0为float类型时，dst中的index存储在高4B，score存储在低4B；
- 当src0为half类型时，dst中index存储在高4B，score存储在低2B，中间的2B保留。

**图1**  Sort32排序示意图

![](https://raw.gitcode.com/cann/asc-devkit/raw/885973fe9fd42a600e3551af9bc11a279e6f183b/docs/zh/api/figures/sort32.png)<a id="图1-Sort32排序示意图"></a>

## 函数原型<a name="section620mcpsimp"></a>

```cpp
template <typename T>
__aicore__ inline void Sort32(const LocalTensor<T>& dst, const LocalTensor<T>& src0, const LocalTensor<uint32_t>& src1, const int32_t repeatTime)
```

## 参数说明<a name="section622mcpsimp"></a>

**表1**  模板参数说明

| 参数名 | 描述 |
|---|---|
| T | 操作数数据类型。|

**表2**  参数说明

| 参数名称 | 输入/输出 | 说明 |
|---|---|---|
| dst | 输出 | 目的操作数。<br> 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT<br> LocalTensor的起始地址需要32字节对齐。 |
| src0 | 输入 | 源操作数。<br> 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT<br> LocalTensor的起始地址需要32字节对齐。 |
| src1 | 输入 | 源操作数。<br> 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT<br> LocalTensor的起始地址需要32字节对齐。<br> **注：src1的数据类型固定为uint32_t。** |
| repeatTime | 输入 | 重复迭代次数。每次迭代完成32个元素的排序，下次迭代src0跳过128字节空间，src1跳过128字节空间，dst跳过256字节空间。每次迭代输入src0要求128字节对齐，src1要求128字节对齐，输出dst要求256字节对齐。repeatTime∈[0, 255]。 |

## 数据类型

**表3**  数据类型组合情况

| src0数据类型 | src1数据类型 | dst数据类型 | 
|---|---|---|
| half | uint32_t | half |
| float | uint32_t | float |

## 约束说明<a name="section633mcpsimp"></a>

- 地址对齐约束参考[通用地址对齐约束](../../../general_description_and_constraints.md)。

- 当参数repeatTime取值为0时，该接口的行为如下：
    
    - 针对如下型号，当参数repeatTime取值为0时，不会执行计算操作，不会对目的操作数进行写入，该接口将被视为NOP（空操作）。
       
       - Atlas A3 训练系列产品/Atlas A3 推理系列产品
       
       
       - Atlas A2 训练系列产品/Atlas A2 推理系列产品
       
    
    
    - 针对Ascend 950PR/Ascend 950DT，该接口通过VF调用[Reg矢量计算](../../reg_vector_compute/index.md)API实现兼容，当参数repeatTime取值为0时，不保证该接口被视为NOP（空操作）。
    


- 如果存在score\[i\]==score\[j\]并且i\>j，将优先选取score\[j\]排在前面。
- 每次迭代内的数据会进行排序，不同迭代间的数据不会进行排序。
- 每次迭代输入src0要求128B\(float\)/64B\(half\)对齐，src1要求128B对齐，输出dst要求256B对齐。

## 调用示例<a name="section642mcpsimp"></a>

完整示例请参考[Sort32样例](https://gitcode.com/cann/asc-devkit/tree/885973fe9fd42a600e3551af9bc11a279e6f183b/examples/01_simd_cpp_api/03_basic_api/01_memory_vector_compute/mrg_sort)。

```cpp
AscendC::LocalTensor<float> srcLocal0 = inQueueSrc0.DeQue<float>();
AscendC::LocalTensor<uint32_t> srcLocal1 = inQueueSrc1.DeQue<uint32_t>();
AscendC::LocalTensor<float> dstLocal = outQueueDst.AllocTensor<float>();
// repeatTime = 4,对128个数分成4组进行排序，每次完成1组32个数的排序
AscendC::Sort32<float>(dstLocal, srcLocal0, srcLocal1, 4);
outQueueDst.EnQue<float>(dstLocal);
inQueueSrc0.FreeTensor(srcLocal0);
inQueueSrc1.FreeTensor(srcLocal1);
```


<!-- cannbot:related:start -->
## 相关

- [MrgSort](mrg_sort.md)（`related`）：Sort32 卡说明“Sort32接口实现一次迭代内对32个数的降序排列操作。”；MrgSort 卡规定“将已排序的最多4条队列合并为1条队列，结果按score域由大到小排序，通常处理Sort32预处理的数据。”，形成先局部 32 元素排序、后最多四路归并的流水线。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 2 / 2 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [Sort 950 ACLNN 算子知识](../../../../../operators/aclnn/math/math/sort_950.md)（`related`）：算子声明的固定版本源码包含对 `Sort32(...)` 的直接调用（第 204 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-math/165d41f02a43a62324b434cb6bda7c533b14da3e/math/sort/op_kernel/arch35/sort_merge_sort.h#L204)
- [MoeGatingTopKSoftmax 950 Direct Invoke 算子知识](../../../../../operators/direct/transformer/moe/moe_gating_top_k_softmax_950.md)（`related`）：算子声明的固定版本源码包含对 `Sort32(...)` 的直接调用（第 356 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/moe/moe_gating_top_k_softmax/op_kernel/arch35/moe_gating_top_k_softmax_fullload_generalized_regbase.h#L356)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->

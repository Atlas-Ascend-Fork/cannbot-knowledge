---
type: API
title: HasTensorInQue
description: 查询Que中目前是否已有入队的Tensor，不支持Tensor原地操作场景。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TQue/HasTensorInQue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
- a2
- a3
- 310p
- '910'
- kirin_x90
- kirin_9030
source_headers:
- include/basic_api/kernel_tpipe.h
---

# HasTensorInQue<a name="ZH-CN_TOPIC_0000001500187481"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_tpipe.h"`。

查询Que中目前是否已有入队的Tensor。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline bool HasTensorInQue()
```

## 参数说明<a name="section622mcpsimp"></a>

无

## 约束说明<a name="section633mcpsimp"></a>

该接口不支持[Tensor原地操作](../../../../../guides/programming_guide/appendix/common_operations/tensor_inplace_performance.md)，即TQue的depth设置为0的场景。

## 返回值说明<a name="section640mcpsimp"></a>

-   true - 表示Queue中存在已入队的Tensor
-   false - 表示Queue为完全空闲

## 调用示例<a name="section642mcpsimp"></a>

```cpp
// 根据VacantInQue判断当前que中是否有已入队的Tensor，当前que的深度为4，无内存Enque动作，返回为false
AscendC::TPipe pipe;
AscendC::TQue<AscendC::TPosition::VECOUT, 4> que;
int num = 4;
int len = 1024;
pipe.InitBuffer(que, num, len);
bool ret = que.HasTensorInQue();
```


<!-- cannbot:related:start -->
## 相关

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [NsaCompress A2 ACLNN 算子知识](../../../../../operators/aclnn/transformer/attention/nsa_compress.md)（`related`）：算子声明的固定版本源码包含对 `HasTensorInQue(...)` 的直接调用（第 213 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-transformer/be33d95bb755cedec3108f70805c1874d1792540/attention/nsa_compress/op_kernel/nsa_compress.h#L213)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->

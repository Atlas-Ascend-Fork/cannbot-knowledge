---
type: API
title: Init
description: 用于内存和同步流水事件EventID的初始化。
tags:
- task.lookup
- topic.implementation.api_layer.basic_api
- topic.implementation.memory_management
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/resource_management/TPipe/Init.md
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

# Init<a name="ZH-CN_TOPIC_0000001717287036"></a>

## 功能说明<a name="section618mcpsimp"></a>

头文件路径为：`"basic_api/kernel_tpipe.h"`。

用于内存和同步流水事件EventID的初始化。

## 函数原型<a name="section620mcpsimp"></a>

```cpp
__aicore__ inline void Init()
```

## 约束说明<a name="section633mcpsimp"></a>

-   Tpipe对象复用时，要与[Destroy](destroy.md)接口成对使用，每次复用需要先Destroy释放资源，再调用init重新初始化。
-   Tpipe构造函数内部已调用Init，无需在Tpipe对象初始化后再额外调用。

## 返回值说明<a name="section640mcpsimp"></a>

无

## 调用示例<a name="section642mcpsimp"></a>


```cpp
// 实例化一个浮点型的自定义算子对象
KernelTPipeInit<float> op;
uint32_t srcSize = 128;

// 构造一个Tpipe对象
AscendC::TPipe tpipe;

// 第一次执行流程
op.Init(x, z, srcSize, &tpipe);
op.Process();
tpipe.Destroy();  // 重复使用需要先Destory，再进行Init

// 第二次执行流程：复用算子对象和tpipe管道对象
tpipe.Init();
op.Init(x, z, srcSize, &tpipe);
op.Process();
tpipe.Destroy();  // 销毁tpipe管道资源
```


<!-- cannbot:related:start -->
## 相关

- [Destroy](destroy.md)（`related`）：Tpipe对象复用时，要与Destroy接口成对使用，每次复用需要先Destroy释放资源，再调用init重新初始化。；约束：用于重复申请释放tpipe，创建tpipe对象后，可调用Destroy手动释放资源。。Init 明确规定复用前先 Destroy，Destroy 则提供手工释放资源的对应动作，两者共同定义 TPipe 重复申请释放的生命周期。
- [Reset](reset.md)（`related`）：完成资源的释放与eventId等变量的初始化操作，恢复到TPipe的初始化状态。；用于内存和同步流水事件EventID的初始化。；Reset 释放当前资源并恢复 Init 建立的内存与 EventID 状态，两接口构成 TPipe 资源生命周期。

<!-- cannbot:api-operator:start -->
### 源码中使用此 API 的算子

展示 1 / 1 个已匹配算子；每个 API 最多展示 10 个自动关联。
范围为算子卡声明的固定版本源码文件中的直接调用，不代表所有编译分支均执行，也不保证覆盖间接调用。

- [FusedLinearCrossEntropyLossGrad A2/A3 ACLNN 算子知识](../../../../../operators/aclnn/nn/matmul/fused_linear_cross_entropy_loss_grad.md)（`related`）：算子声明的固定版本源码包含对 `Init(...)` 的直接调用（第 48 行）；不表示所有编译分支均执行该调用。 [源码](../../../../../../../../cann-ops-raw/ascendc/ops-nn/955f8b33985b6d72989ebff341bb9c2c564a51bc/matmul/fused_linear_cross_entropy_loss_grad/op_kernel/fused_linear_cross_entropy_loss_grad_high_perf.h#L48)

<!-- cannbot:api-operator:end -->
<!-- cannbot:related:end -->

---
type: API
title: AscUnlock
description: 用于同步AI Core内部异步流水的指令，在当前流水的前序指令执行完成后根据mutex_id释放对应Mutex。须与asc_lock成对使用。
tags:
- task.lookup
- topic.implementation.synchronization
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/c_api/sync/asc_unlock.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-09-08T03:31:04Z'
platforms:
- '950'
---

# asc_unlock

## 功能说明

用于同步AI Core内部异步流水的指令，直到当前流水的前序指令执行完成后，根据mutex_id释放对应Mutex。

相对于[asc_sync_notify](asc_sync_notify.md)/[asc_sync_wait](asc_sync_wait.md)同步机制，使用asc_lock/asc_unlock接口有以下优势：

- 内聚性更强，使用时与其它流水线解耦，可以简化反向同步。以PIPE_MTE2与PIPE_V之间同步为例，对比如下：

    ```cpp
    // asc_sync_notify/asc_sync_wait机制
    For i=0:100
        if i > 0:
            asc_sync_wait(PIPE_V, PIPE_MTE2, EVENT_ID0)
        endif
        // MTE2指令
        asc_sync_notify(PIPE_MTE2, PIPE_V, EVENT_ID0)
        asc_sync_wait(PIPE_MTE2, PIPE_V, EVENT_ID0)
        // PIPE_V指令
        if i < 99:
            asc_sync_notify(PIPE_V, PIPE_MTE2, EVENT_ID0)
        endif
    endFor

    // asc_lock/asc_unlock机制
    For i=0:100
        asc_lock(PIPE_MTE2, 0)
        // MTE2指令
        asc_unlock(PIPE_MTE2, 0)
        asc_lock(PIPE_V, 0)
        // PIPE_V指令
        asc_unlock(PIPE_V, 0)
    endFor
    ```
    其中EVENT_ID0为同步ID，取值范围为[0, 7]；mutex_id取值范围为[0, 31]。
- 可以使用更多的同步信号量。

## 函数原型

```cpp
enum ascMutexExecuteMode {
    ASC_LOCK_BLOCK = 0,
    ASC_LOCK_NON_BLOCK = 1
};

__aicore__ inline void asc_unlock(pipe_t pipe, uint8_t mutex_id)
__aicore__ inline void asc_unlock(pipe_t pipe, uint8_t mutex_id, const ascMutexExecuteMode mode)
```

## 参数说明

**表1** 参数说明

| 参数名 | 输入/输出 | 描述 |
| :---  | :--- | :--- |
| pipe | 输入 | 该指令的执行流水线。 |
| mutex_id | 输入 | mutex标号。取值范围[0, 31]。|
| mode | 输入 | 可选参数，用于指定是否阻塞流水线，默认值为ASC_LOCK_BLOCK。<br>&bull; ASC_LOCK_BLOCK：该指令等待pipe所对应的流水线中所有前置指令完成后执行。<br>&bull; ASC_LOCK_NON_BLOCK：该指令等待pipe所对应的流水线中所有前置指令完成且相同mutex_id的所有asc_unlock指令执行完成后执行。 |

## 返回值说明

无

## 流水类型

PIPE_S

## 约束说明

- 必须与asc_lock搭配使用，且需要使用相同的mutex_id与mode。此外，asc_unlock必须始终插在对应的asc_lock指令之后，否则会出现未定义的硬件行为。
- 具有相同mutex_id的asc_lock与asc_unlock组合，无论pipe与mode是否相同，均不得在编程顺序中嵌套，否则硬件行为将不可预测。
- 对于程序顺序中连续出现的，具有相同pipe与mutex_id的指令对，后一个asc_lock将不再阻塞流水线运行，若需实现同一流水线的依赖关系，则必须使用指令[asc_sync_pipe](asc_sync_pipe.md)。

## 调用示例

asc_unlock与asc_lock必须成对使用，调用示例请参见[asc_lock的调用示例](asc_lock.md#调用示例)。


<!-- cannbot:related:start -->
## 相关

- [AscLock](asc_lock.md)（`related`）：asc_lock与asc_unlock必须严格成对使用，并使用相同的mutex_id与mode。；必须与asc_lock搭配使用，且需要使用相同的mutex_id与mode。。两端相互声明同一 mutex_id/mode 的成对协议：asc_lock 获取并阻塞流水，asc_unlock 在前序指令完成后释放；联合阅读才能确定合法同步序列。
<!-- cannbot:related:end -->

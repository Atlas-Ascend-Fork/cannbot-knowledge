---
type: Guide
title: 异步执行（编译与执行）
description: 当开发者完成一个Kernel核函数的编写后，需要通过特定的下发/启动语法将其提交到指定的Stream（计算流）上执行。例如：
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/compilation_and_execution/async_execution.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 异步执行

当开发者完成一个Kernel核函数的编写后，需要通过特定的下发/启动语法将其提交到指定的Stream（计算流）上执行。例如：
这些核Kernel核函数都是通过CANN Runtime完成Kernel的加载与运行。CANN Runtime是CANN软件栈中负责驱动硬件执行与管理AI计算任务的核心组件，它通过提供Device、Memory、Context、Stream、Kernel管理等API，使得上层应用和框架能够高效利用AI处理器的硬件计算资源。
完成Kernel加载和运行的主要流程分以下几步：
在这个过程中我们提到了Stream创建与销毁，内存申请与拷贝，异步调用与同步等待。在本节的其余部分，我们将解释这些CANN Runtime的元素和对应的API。
##  Stream管理
Stream（计算流）本质上是一个有序的任务队列，为开发者提供了一种表示“先序执行”的抽象机制，程序可向队列中提交各类操作，例如内存拷贝、核函数下发等，所有任务将按入队顺序依次执行。单个计算流内，队列头部任务优先执行，执行完成后自动出队；后续队列任务依次前移，等待调度执行。同一个计算流中的任务具备串行执行特性，严格遵循入队先后顺序运行。
应用程序可同时创建并使用多个计算流。多流场景下，运行时会根据AI处理器的硬件资源占用状态，从存有待处理任务的计算流中择优调度任务执行。开发者可为计算流配置优先级，该优先级将作为运行时调度的参考依据，用以调整任务调度策略，但无法强制保证固定的执行顺序。
绑定在指定计算流内的API接口调用、核函数下发操作，相对于主机CPU线程均为异步执行。
应用程序可通过等待目标计算流清空所有任务完成流级同步，也可在整个设备维度完成全局同步。
CANN Runtime内置默认计算流，所有未显式指定计算流的运算操作、核函数下发任务，都会默认排入该流中执行。绝大多数未手动指定计算流的业务代码，都在隐式使用默认计算流。
- 创建与销毁Stream： aclrtCreateStream(&stream)与aclrtDestroyStream(stream)。
- 指定Stream执行核函数： kernel>>(...)。
- 指定Stream异步拷贝： aclrtMemcpyAsync(..., stream)。
- 指定Stream同步：aclrtSynchronizeStream(stream)。
##  Memory（内存）管理
在异构计算架构中，系统由主机（Host）和设备（Device）组成。Host和Device各自拥有独立的内存，Host内存是指AI处理器所在服务器的主机内存（即CPU内存），而Device内存则是指AI处理器自带的设备内存。
内存管理中要做好的两件事是：
1. 可以访问内存：Runtime提供了一套内存管理API，使开发者能够高效便捷地编写应用程序中的内存管理代码。由于Host和Device的内存相互独立，Runtime提供了专门的接口来分别申请和释放Host内存及Device内存。例如，申请和释放Host内存的接口为aclrtMallocHost和aclrtFreeHost，而申请和释放Device内存的接口为aclrtMalloc和aclrtFree。

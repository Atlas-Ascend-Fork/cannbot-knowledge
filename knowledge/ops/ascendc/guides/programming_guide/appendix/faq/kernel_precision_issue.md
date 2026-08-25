---
type: Guide
title: 核函数运行验证时算子存在精度问题
description: 在进行算子NPU域的运行验证时，实际数据和真值数据不一致，算子存在精度问题。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/guide/programming_guide/appendix/faq/kernel_precision_issue.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# 核函数运行验证时算子存在精度问题

## 现象描述
在进行算子NPU域的运行验证时，实际数据和真值数据不一致，算子存在精度问题。
## 问题根因
算子出现精度问题，一般是由于算子的实现逻辑有误。
## 定位步骤
Ascend C提供孪生调试的功能，通过CPU域的功能验证、gdb单步调试、printf数值打印来定位算子的实现逻辑问题。本样例仅展示了可能会出现的场景，便于演示定位步骤。实际使用过程中，请根据代码情况进行调试。
1.  进行CPU域的功能验证，观察是否有日志报错。
参考基于样例工程完成Kernel直调章节，编写CPU侧的运行验证代码，并进行运行验证，发现CPU域的精度比对也存在不一致的问题。
观察打屏日志中是否有报错信息，可搜索关键词"failed"。比如，下图的报错示例指示，错误出现在代码中调用LeakyRelu接口的地方。
通过上述报错日志，一般只能定位到报错的代码行，无法明确具体错误，接下来需要通过gdb调试的方式或者printf打印的方式进一步精确定位。
2.  gdb调试。下面的样例展示了拉起leakyrelu算子CPU侧运行程序的样例，该样例程序会直接抛出异常，直接gdb运行，查看调用栈信息分析定位即可。其他场景下您可以使用gdb打断点等基本操作进行调试。使用gdb调试Ascend C程序的详细内容请参考CPU域孪生调试。
1.  使用gdb拉起待调试程序，进入gdb界面进行debug。
2.  单独调试一个子进程。
3.  运行程序。
4.  通过bt查看程序调用栈。
5.  查看具体层的堆栈信息，打印具体变量的值。本示例中，打印了tileLength为1024，该程序中表示需要处理1024个half类型的数，大小为1024*sizeof(half)=2048字节；输入Tensor xLocal的值，其中dataLen表示LocalTensor的size大小为1024字节，只能计算1024字节的数据。可以看出两者的长度不匹配，由此可以定位问题。
3.  printf打印。在合适的位置增加变量打印。样例代码如下：
可以看到有如下打屏日志输出，打印了tileLength为1024，该程序中表示需要处理1024个half类型的数；输入Tensor xLocal的size大小，为512，表示只能计算512个half类型的数。可以看出两者的长度不匹配，由此可以定位问题。

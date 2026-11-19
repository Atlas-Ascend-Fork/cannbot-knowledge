---
type: API
title: MSTX线程范围与annotate：LIFO配对和异常收尾
description: 限定主线新增入口的A2/A3范围，保存层级返回、上下文message及装饰器默认。
tags:
- task.lookup
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-annotate.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-annotate.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-range_pop.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-range_pop.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-range_push.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-range_push.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/mstx.py
  role: implementation
created_at: '2026-11-09T19:31:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# MSTX线程范围与annotate：LIFO配对和异常收尾

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 新增入口的范围

range_push、range_pop和annotate只在本固定OpPlugin主线有独立页，列A2/A3训练/推理及旧Atlas，未列950；不由基础range_start/end新增950补齐。PyTorch发布mstx.py也没有这三个实现。

range_push(message,stream=None,domain='default')在线程范围栈压入，返回从0开始的嵌套级别，正常失败-1；range_pop(domain='default')弹出最近范围，返回匹配级别，无匹配-1。它们同线程LIFO、不接range_id，不能代替可跨线程的start/end。异常装饰器还可能返回None，不把所有错误限定为-1。

## annotate两种使用方式

`mstx.annotate(message='',stream=None,domain='default')`实际主线构造默认空串，英文同此、中文原型message必填。作为with上下文应显式传非空message；装饰函数时若为空，__call__将message设为函数名。MSPTI仍限255字节，stream=None为Host，domain默认default。

主线decorator用functools.wraps并在finally中range_end，即使业务函数异常仍尝试结束；上下文__exit__也结束已记录ID并清空range_id。实例存一个range_id，不能从这几行推定同对象并发/任意重入安全。旧mstx_range缺finally，与本入口分别判断。

文档装饰器样例函数my_code又调用自身，为递归示意且缺真实业务，不作可运行调优例子。API收尾成功不等于Profiler已捕获事件或记录了设备完成时间，本次未运行采集。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-annotate.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-annotate.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-range_pop.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-range_pop.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-range_push.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/torch_npu-npu-mstx-range_push.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/mstx.py)（implementation）

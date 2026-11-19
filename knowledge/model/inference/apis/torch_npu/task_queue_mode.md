---
type: API
title: TaskQueue动态模式API：有效优先级与切换阻塞
description: 限定主线set/get入口，保存0/1/2含义、纯推理条件和无并发提交责任。
tags:
- task.lookup
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_task_queue_enable.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-get_task_queue_enable.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_task_queue_enable.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-set_task_queue_enable.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
created_at: '2026-11-09T19:31:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TaskQueue动态模式API：有效优先级与切换阻塞

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 主线入口

本固定OpPlugin主线新增`set_task_queue_enable(mode)`和`get_task_queue_enable()->int`，发布快照没有对应页面，配对TorchNPU发布utils也没有这两个定义。产品表列A2/A3训练、相关推理及旧Atlas、950DT；不因此宣称任何已安装发布包可调用。

0关闭队列、主线程同步下发路径，1一级优化且为环境缺省，2二级优化。独立TorchNPU主线docstring明确2为最高吞吐的**纯推理**模式；环境页还限定二进制场景，不是训练可任意追求吞吐的开关。

## 切换与有效状态

ASCEND_LAUNCH_BLOCKING=1优先使有效值始终0；其次动态API，再是TASK_QUEUE_ENABLE环境默认1。getter应查询实际生效值，配置值与有效值区分。

Python主线setter会将str转int，再检查属于0/1/2，否则RuntimeError；无效字符串在int转换时也可能ValueError，不能把所有错误硬写为同一种。docstring说明底层先emptyAllNPUStream排空待下发操作，可能显著阻塞；调用者应确保切换时没有并发NPU活动，不在热路径反复调用。无需重启进程不表示无等待、无状态边界或可与其他线程安全竞争。

排空Host任务仍不等于所有设备计算完成，具体等待范围按底层实际实现核对；未切换模式或操作队列。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-get_task_queue_enable.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-get_task_queue_enable.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_task_queue_enable.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-set_task_queue_enable.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)（implementation）

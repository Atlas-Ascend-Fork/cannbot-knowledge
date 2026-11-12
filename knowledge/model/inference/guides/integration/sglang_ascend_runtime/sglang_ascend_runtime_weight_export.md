---
type: Guide
title: SGLang NPU权重导出的HCCL组与模块显式导出守卫
description: 说明远程导出按TP端口构组、nccl到hccl替换、逐参数broadcast、组销毁和模型显式weight_export_error拒绝行为。
tags:
- task.implementation
- topic.model_serving
- topic.parallelism
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/model_runner_components/weight_exporter.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/nemotron_h.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/models/nemotron_h_nvfp4_layout.py
  role: supporting
created_at: '2026-11-08T12:10:39Z'
updated_at: '2026-11-09T04:33:52Z'
platforms: []
---

# SGLang NPU权重导出的HCCL组与模块显式导出守卫

WeightExporter先遍历所有模块检查_weight_export_error，任一存在就拒绝建发送组、远程发送、保存或按名读取；该机制只消费模块显式声明的拒绝原因，不判断布局是否可逆。例如Nemotron NVFP4 phase layout设置拒绝标记，但其布局类仍实现正向与逆向转换；拒绝导出不等于打包不可逆，不能绕过模块守卫把运行时布局当通用权重发布。

发送组要求默认组已初始化、非空group_name、逗号端口数恰等TP size。每TP rank选择独立端口，组名追加端口/rank，NPU仅把传入backend==nccl替换hccl，device_type用npu；其他backend参数不自动改。建组后barrier，前后清设备allocator缓存。

send_weights按named_parameters顺序逐个broadcast(src=0)，双端必须有一致顺序、shape与dtype；成功只表示本轮传输调用完成，不替对端执行量化/NZ后处理。结束删除缓存条目并destroy_process_group，即使发送捕获异常也做清理，不是可原地重试的长驻组或权重事务。

验收区分连接、数据传输、后处理和模型输出，覆盖打包导出拒绝、端口/TP错配及中途失败。恢复使用完整checkpoint和新进程，避免半更新参数继续服务。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。

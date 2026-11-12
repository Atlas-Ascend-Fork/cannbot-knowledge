---
type: Guide
title: SGLang NPU输出投影微基准的stride、图重放与在线更新校验
description: 说明DSV4 wo_a einsum和F.linear比较的共享输入/独立层权重、事件计时中位数、真实stride及图内原地权重更新验证范围。
tags:
- task.testing
- topic.performance.analysis
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/dsv4/bench_npu_wo_a.py
  role: primary
created_at: '2026-11-08T12:20:23Z'
updated_at: '2026-11-08T12:20:23Z'
platforms: []
---

# SGLang NPU输出投影微基准的stride、图重放与在线更新校验

该脚本模拟DSV4 Flash TP8一个local输出组，比较einsum(tgd,grd→tgr)与直接F.linear。默认43个独立层权重，输入dim4096、o_lora_rank1024，batch1/8；输入先分配[tokens,8,dim]再取[:, :1, :]保留跨token stride，避免用完全连续输入掩盖真实切片布局。

两个变体共享同一批输入/权重，辅助流预热3次后捕获NPUGraph(auto_dispatch_capture=True)。NPU事件计时每轮100次replay，5轮轮换测量顺序取median；ms_per_iteration为全部43层总时，us_per_layer再除层数，不能将总时直接写单层延迟。

精度assert_close rtol/atol均0.016。捕获后原地neg_首层权重，要求data_ptr不变、输出确实变化且等于原输出取负，再恢复权重；这检查图是否读取在线更新，而非两个可能同时陈旧的graph仅互比。可选profiler检查转置与任务。

它不计模型加载、通信、KV或服务调度，不是全模型TP8实测。脚本未附本次运行产物，不能给出F.linear固定加速比；验收应保存所有轮样本、stride、精度、设备/库版本，并另测端到端TTFT/TPOT。

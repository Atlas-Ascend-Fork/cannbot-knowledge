---
{
  "type": "Runbook",
  "title": "GRPO 32-rank HCCL 建链接收超时的观测与未决归因",
  "description": "来源 plog 报等待 12 字节、已接收 0 字节、600s 超时及 HCCL_E_TIMEOUT。remote pid=0 不证明对端从未发起建链；业务负载失衡是分析器假设，缺少全 rank 时间线与通信域闭环，未定案。",
  "tags": [
    "task.debugging",
    "topic.reinforcement_learning"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# GRPO 32-rank HCCL 建链接收超时的观测与未决归因


## 适用场景

rl_qwen3_32b 32-die GRPO 训练失败的多分析器 RCA：首报错为 HCCL 建链等待超时——plog errNo[0x5000013] Wait timeout for sockets recv size[12 Byte] recvSize[0 Byte] timeout[600 s]，hcclRet=9（HCCL_E_TIMEOUT，hcomm/include/hccl/hccl_types.h:33），对端 remote userrank[24] pid[0] 仅说明该次等待尚未收到预期握手数据；不证明对端从未发送，也未排除网络丢包、进程中途失败或调用顺序差异。GE/HCCL/PTA 三分析器 matched=false 且 suspected_root_cause 交叉一致指向业务侧（verl 性能采集同步点 megatron_workers.py:710→performance.py:236）。DRV/GE 二轮对抗复核收敛为 Non_CANN；报告因 P9 工具组合风险（vllm-ascend 0.14.0rc1 × torch-npu dev 构建 pip 冲突）与 verl 源码未归档未终裁 confirmed，llm_verdict=unresolvable、转人工介入——业务侧负载失衡为多分析器一致指向的假说而非已定根因。

## 触发与观测

触发：problem_id rl_qwen3_32b_32die_grpo（Scheduler/训练失败日志）。探针：RCA 工作流多分析器并行扇出（HCCL/PTA/non-CANN/DRV/GE）+ plog/execute_log 交叉核验 + 既有历史运行比对。观测：plog 首报错为 HCCL RaSocket 建链等待超时（登记机制片段：）；DRV 域 912+ 条 ERROR 全部标签为 HCCL/APP、DRV 标签 ERROR=0。

## 探针与操作

关键探针与修复操作。证据角色覆盖：trigger, probe, observation, discrimination。

## 机制与判别


> 判别与终局：GE/HCCL/PTA 三分析器 matched=false 且 suspected_root_cause 交叉一致指向业务侧（verl 性能采集同步点 megatron_workers.py:710→performance.py:236），DRV/GE 二轮对抗复核收敛（DRV 域 912+ 条 ERROR 全部标签为 HCCL/APP，DRV 标签 ERROR=0，failure_mode=none）；最终报告 44799 字节落盘，但因 P9 工具组合风险（vllm-ascend 0.14.0rc1 × torch-npu dev 构建 pip 冲突无法终裁）与 verl 源码未归档（AllGather 通信域 log-code 闭环未完成），llm_verdict=unresolvable、human_intervention_needed=true，解释完整性 0.89<1.0 禁止 confirmed。


```
[Recv][RaSocket]errNo[0x5000013] Wait timeout for sockets recv, size[12 Byte], recvSize[0 Byte] timeout[600 s]. Peerrank did not send the data in time. Check whether the peerrank is abnormal. + call trace: hcclRet -> 9（recv空等而非connect拒绝——TCP可建立、对端握手数据永不抵达）
```

## 验证信号

RL 训练（GRPO/多 TP 组 rollout）出现 HCCL_E_TIMEOUT=9/errNo 0x5000013 且对端 rank 无报错时的定界：同时核对全 rank 到达时间、负载分布、通信域/序号、进程错误及网络状态；不能只因超时或分析器一致就先排除 CANN/网络侧。


## 适用与失效边界

适用：RL 训练（GRPO/多 TP 组 rollout）出现 HCCL_E_TIMEOUT=9/errNo 0x5000013 且对端 rank 无报错时的定界：同时核对全 rank 到达时间、负载分布、通信域/序号、进程错误及网络状态；不能只因超时或分析器一致就先排除 CANN/网络侧。失效边界：RCA 为分析器工作流产物，非人工复现实验；因工具链冲突与 verl 源码缺失未终裁 confirmed，处置建议（业务侧改 shuffle/超时）未实施验证。

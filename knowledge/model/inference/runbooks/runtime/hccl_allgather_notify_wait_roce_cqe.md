---
{
  "type": "Runbook",
  "title": "候选卡片：HCCL AllGather 执行失败：NOTIFY WAIT 互等对（localRank:4↔remoteRank:5）",
  "description": "大规模 SP/TP/EP 混合并行推理（prefill_k2_rank_32_32sp_32tp_32ep_a8w8，CANN 8.3.RC1.alpha003）中 HCCL AllGather 执行失败：NOTIFY WAIT 互等对（localRank:4↔remoteRank:5）；本卡给出等待关系串联与网络侧快速定界的 grep 排查路径。",
  "tags": [
    "task.debugging",
    "topic.parallelism"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 候选卡片：HCCL AllGather 执行失败：NOTIFY WAIT 互等对（localRank:4↔remoteRank:5）


## 适用场景

在昇腾上跑大规模 SP/TP/EP 混合并行（如 prefill_k2_rank_32_32sp_32tp_32ep_a8w8）推理/训练并使用 HCCL 集合通信的团队。当日志出现 HCCL AllGather Exec op fail、hcclRet -> 9、TaskException NOTIFY WAIT 时适用本卡。

## 触发与观测

触发条件与客观观测（引自案例 CASE-ISSUE-cann-recipes-infer-48 的 device 日志原文，CANN 8.3.RC1.alpha003）：

- 来源结论：cann-recipes-infer prefill_k2_rank_32_32sp_32tp_32ep_a8w8（CANN 8.3.RC1.alpha003）配置下 HCCL AllGather 执行失败：algName[AlignedAllGatherDoubleRingFor91093Executor]、通信域 group_name_2，WaitFinishWhileLoop hcclRet -> 9、WaitTaskFinish failed，TaskException type:NOTIFY WAIT 呈 localRank:4↔remoteRank:5 的等待对（同一 device-4 日志内多条 NOTIFY WAIT 记录）。


- 来源结论：排查路径：以 HCCL TaskException 维测日志的 localRank/remoteRank 串联等待关系、找互等 rank 对（A→B→A 成环），并在 plog/device 日志执行 grep -e "error cqe" -e "Heartbeat Lost Occurred" -e "sdma error" -e "type:SDMA, localRank" -rn 快速定界网络侧错误。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${DEVICE_LOG_ROOT}`：故障设备日志根目录。


1) 在 plog/device 日志检索 HCCL TaskException 维测日志（关键词 TaskException/run failed, base info），抽取 localRank/remoteRank 串联等待关系，找互等 rank 对（A→B→A 成环）。
2) 对同一 device 的全部日志执行：
   grep -e "error cqe" -e "Heartbeat Lost Occurred" -e "sdma error" -e "type:SDMA, localRank" -rn
3) 核对 Exec op fail 行的 tag/algName/通信域（AllGather_group_name_2NHRAlignedAllGatherDoubleRingFor91093Executor_device / group_name_2）以确认失败的集合通信算子与通信域。

## 机制与判别

机制与判别：
- AllGather 执行失败 + WaitFinishWhileLoop hcclRet -> 9 → 多个 NOTIFY WAIT（localRank:4↔remoteRank:5 及 remoteRank:4294967295 的广播等待）构成互等等待。

关键原文工件：

工件：

```text
${DEVICE_LOG_ROOT}/device-4/device-1417203_20251105153204683.log:6:[ERROR] HCCL(22346,aicpu_scheduler):2025-11-05-15:32:01.404.349 [aicpu_communicator.cc:2995] [22357][TaskException]base is streamId:986, sqid:90, head:31, tail:290, type:NOTIFY WAIT, localRank:4, remoteRank:5, taskId:31, notifyId:4441, length:0, addr1High:0x0, addr1Low:0x0, addr2High:0x0, addr2Low:0x0.
```

工件：

```text
grep -e "error cqe" -e "Heartbeat Lost Occurred" -e "sdma error" -e "type:SDMA, localRank" -rn
```

## 验证信号

验证层级：source_read（离线日志定界；本案例会话在收尾检索阶段被截断，无最终结论输出，也无现场复跑）。
- extract_0.txt:4-6：Exec op fail（tag/algName/identifier）+ TaskException NOTIFY WAIT 等待对。
- 参考命中：Notify Wait Timeout 排查等待关系方法（PCASE-031）。

## 适用与失效边界

适用：HCCL 集合通信失败伴 NOTIFY WAIT 的等待关系串联与网络侧错误定界。
边界：
- 本卡只到定界层级：单 rank 设备侧/交换机/光模块等具体链路根因需网络侧与 device 侧联合取证（轨迹内未完成）。
- 无 gold 结论核对：会话在诊断中段结束，最终根因声明未交付。

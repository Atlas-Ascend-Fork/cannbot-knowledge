---
{
  "type": "Runbook",
  "title": "npugraph_ex 的 gather 报 507011：区分 tiling 日志线索与待证根因",
  "description": "GLM-5.2 offload Scheme B 的 npugraph_ex 故障诊断：保留 gather 的 tilingKey=0/blockDim=1 原始观测与主流预取组合修改后的单次 smoke 结果；实际产品未确认，batchSize_==0 和 capture shape 解析失败仍待补证。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-24T08:05:12Z",
  "platforms": []
}
---

# npugraph_ex 的 gather 报 507011：区分 tiling 日志线索与待证根因

## 适用场景

GLM-5.2 KVCache offload Scheme B 在 npugraph_ex（capture/replay）下运行时，gather 相关节点报 507011 / `VEC supports illegal configurations`。本例是 11 层裁剪模型的 bring-up；日志记录 world_size=4、batch_size=4、batch_size_per_rank=1、input_max_len=256、max_new_tokens=16（source 0 seq 1/220/256）。CANN 环境路径为 9.1.0-beta.1；构建目标为 ascend910_93，实际产品未确认，不能据此指定 A3 平台。

本卡用于整理故障节点、输入与 tiling 的补证顺序；没有建立从某个 tiling 数值组合到框架根因的通用规则。

## 触发与观测

- 同一会话先运行 kernel-side scatter 版本：eager 日志有 `model run success` 和 decode 文本（source 0 seq 216-217）；随后 npugraph_ex 日志出现 507011 / VEC illegal，未显示 decode 结果（seq 219-220）。后者虽回显 `EXIT=0`，仍应按日志中的执行失败判读，不能单凭启动脚本退出值报成功。
- 当次 plog 的直接观测（source 0 seq 224-225，保留关键原文）：

```text
Aicore kernel execute failed, device_id=0, stream_id=141, report_stream_id=46, task_id=51, flip_num=0, fault kernel_name=GatherSelectionKvCache_707a2446a5edc15f7d875c87115bd834_2
errorStr: VEC supports illegal configurations in commands.
subErrType:4.
GetArgsInfo:tilingKey = 0, print 3 Times totalLen=(45*8), argsSize=360, schemMode=0, blockDim=1
```

- 这些字段定位了这一次报错的 gather 节点及其 stream/tiling 参数。`tilingKey=0, blockDim=1` 本身不证明 `batchSize_==0`、空输入、非法二进制或 capture 无法解析 shape；`stream_id=141` 也不能独立证明该节点属于哪条 Python 侧流。

## 探针与操作

1. 保留故障运行的应用日志和对应时间窗口内的 plog，按进程、任务与 kernel 名核对同一次故障，记录 stream_id、tilingKey、blockDim 及完整错误，而不是只搜某个数值组合。
2. **待补证**：取得故障时实际加载的算子与框架版本，核对同版本 Host tiling 源码的 key 分支、默认值、提前返回条件及 kernel dispatch；同时采集该次调用的真实输入 shape、dtype、stride 和 Host tiling 字段。未取得这些配套记录前，不把源码注释或助手诊断当作分支已执行的证明。
3. **待验证**：固定输入、加载的二进制、图缓存状态及其余配置，分别控制流切换、事件依赖和输入张量派生方式，比较 Host tiling 与故障日志。已有成功运行只能作为组合改动的对照，不能取代这些受控实验。

本轨迹实际做过的组合修改（source 0 seq 231/241-250）为：

- `prefetch_full` 从侧流切换块改为在主流直接调用 gather，去掉对应的 wait_stream、record_event；arrival 分支去掉配套 wait_event。
- 同时不再构造 `full_seq = actual_seq_lengths_kv.to(torch.int32).clone()`，gather 改为直接接收 `actual_seq_lengths_kv`；保留既有 kernel-side scatter 与从 status 读取 actual_seq 的路径。
- 修改后清理该例模型的 compile_cache，再分别运行 eager 与 npugraph_ex smoke（seq 252-256）。这段经历不是“只改 stream”的单变量实验，也没有提供修后 tilingKey 的实测值。

这些操作描述本例已有尝试，不要求遇到同类错误就删除副流、事件或缓存。清理缓存只属于本次记录的步骤，未单独验证其必要性。

## 机制与判别

- **确定观察**：报错节点名称是 GatherSelectionKvCache，应用日志为 VEC illegal / 507011；上述组合修改后的单次 npugraph_ex 运行显示成功。它支持继续检查 gather 所在的流、依赖和输入路径，不能唯一归因到其中某一项。
- **待证假设**：侧流节点的跨流输入/输出依赖影响了 capture 的 shape 或 tiling 绑定。原会话的助手分析与新增代码注释提出了“图终值 → shape 解析失败 → batchSize_==0 → key0/blockDim1 → 非法指令”的链条（seq 226/232/237/240-241）；本卡不把这些同源解释计为独立验证。缺少与本次故障绑定的 Host 输入、tiling 分支和二进制 dispatch 记录，不能确认这条链。
- **未排除**：实际输入异常、上游写入、地址/生命周期、同步或算子实现问题。故障节点不是新 scatter 的名字，不等于已经排除 scatter 对后续输入的影响；也不能仅凭错误类别排除 NaN/token 数据、status-read/view 或其他潜在分支。

## 验证信号

- 修改后 eager 与 npugraph_ex 分别回显 `EXIT=0`、`model run success`（source 0 seq 253/256）；两次输出中展示的 decode 文本相同，且与修改前 eager 的展示文本一致（seq 217）。这是该 smoke 的日志观测，没有独立的完整输出文件字节比较、张量精度测试或全数据集等价性证明。
- 对这一次 npugraph_ex **应用日志**检索 `507011|illegal|fault kernel|EE9999|EZ9999|RuntimeError`，计数为 0（seq 258-259）。这不等于逐设备 plog 全量无错，也不证明所有 rank 的全部日志都没有故障。
- 结论限于一个短输入 smoke 的组合修改后成功；未采样多次 replay、不同 batch 的稳定性，也未做单变量根因消融或性能收益验证。

## 适用与失效边界

- 仅将相似日志作为补证入口，不把 key0/blockDim1 当作 batchSize_==0 或框架 shape 解析失败的通用指纹。实际产品未确认，继续保持 draft 与空 platforms，不增加 verified。
- 同样的报错可能需要不同调查路径；现有证据不足以排除其他非法指令、地址或输入问题，也不足以宣布必须放弃副流或增加主流重算。
- 不外推 GE/torchair 行为，不声称修后 tiling 已恢复为某个 key；主流执行对重叠和性能的影响未量化。需要保留副流时，须完成相应依赖、输入与稳定性验证后再判断方案。

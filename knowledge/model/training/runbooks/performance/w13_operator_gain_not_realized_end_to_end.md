---
{
  "type": "Runbook",
  "title": "W13 profiling 区间差分与 Add 归属：先绑定反向调用链再解释收益",
  "description": "W13离线profiling中等待总和与标记区间elapsed都减少，但后续host/device关联把指定Add定位到反向MatmulBackward0/aten::add_。保留原区间统计，撤回前向共享专家合并及等待移出窗口的确定归因。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": []
}
---
# W13 profiling 区间差分与 Add 归属：先绑定反向调用链再解释收益

## 适用场景

Kimi K3训练MoE的w1/w3合并为w13后，对比基线与优化profiling。分析脚本以first Add、first MoeEpDispatch等事件作为区间标记，需要验证区间是否真的对应共享专家重算，及其等待是否位于关键路径。

## 触发与观测

来源按所选标记区间得到如下离线统计：

| 指标 | baseline | W13-new | 差值 |
| --- | ---: | ---: | ---: |
| 区间内EVENT_WAIT总和 | 997.570ms | 324.526ms | 673.044ms |
| 按该标记划定的elapsed | 1756.880ms | 1052.209ms | 704.671ms |

等待总和差约为elapsed差的95.5%，这是两项区间差分的比值。标记的语义、重叠及统计窗口尚须核对，不能将其直接解释为共享专家重算或端到端收益的贡献率。

## 探针与操作

1. 在kernel_details/TASK中用时间、stream与task身份定位设备事件，再用connectionId关联实际host launch；仅凭算子名和相邻事件不判定调用点。
2. 联查trace中的CANN API、aten操作与autograd父区间，确认是前向输出合并还是反向原地累加。
3. 重新按已确认语义划定两侧一致的测量边界，分别统计区间elapsed、等待总和和端到端step wall；区间内求和不替代关键路径测量。

## 机制与判别

最初助手把一个201.204us的`aclnnAdd_AddAiCore_Add`解释为第64层前向`output + shared_output`，并把它前面的6.7ms等待解释为`main_stream.wait_stream(shared_stream)`。后续工具关联为：

- 同一设备kernel的startNs为1793226432583044701、stream为61、connectionId为1762754。
- 该connectionId关联的host launch上游为`aclnnInplaceAdd`。
- 对应`aten::add_`位于`autograd::engine::evaluate_function: MatmulBackward0`区间内，附近有matmul_backward与AccumulateGrad。

这条链支持该Add属于反向执行区间的原地累加，而不是已确认的前向共享专家合并。**撤回此前的Add身份、等待来源及“Add后移把等待移出共享专家recompute窗口”的确定归因。** 单凭这些关联也不能把全部6.7ms等待进一步归到某一反向源码行。

## 验证信号

原始工具返回支持上述TASK/connectionId/host操作关联，也支持所选区间内的数值统计。脚本py_compile只证明语法。来源未完成按更正后的Add身份重新归类全部区间与端到端收益的闭环；原统计数值可保留为待重新解释的观测。

## 适用与失效边界

本卡是profiling事件身份核验与统计边界排查，不构成W13共享专家收益定论。改变采集版本或区间规则后应重新绑定host/device事件；不能用旧区间标签、相邻kernel或助手总结替代调用链证据。

---
{
  "type": "Runbook",
  "title": "GE PrunePass 修复：9 类帧传值骨架类型移出保活闭包收集与 rescue，引擎归属保护优先（IsFrameSkeletonRescued=IsProtectedEngineNode）",
  "description": "822becb4d 重构 PrunePass（空闲节点误连边剪除+分层保活）后 310Brc Transformer INT8 冒烟用例上板超时。修复方案是把 9 类帧传值骨架类型（Enter/Switch/Merge/NextIteration 及 ref 变体）移出保活闭包收集与 rescue，但引擎归属保护优先：IsFrameSkeletonRescued=IsProtectedEngineNode，引擎已分配且属保护引擎（RTS/GeLocal/HCCL）的降级骨架仍保活。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# GE PrunePass 修复：9 类帧传值骨架类型移出保活闭包收集与 rescue，引擎归属保护优先（IsFrameSkeletonRescued=IsProtectedEngineNode）

## 适用场景

822becb4d 重构 PrunePass（空闲节点误连边剪除+分层保活）后 310Brc Transformer INT8 冒烟用例上板超时。修复：新增 kFrameSkeletonOpTypes（Enter/Switch/Merge/NextIteration 及 ref 变体共 9 类），引擎未分配（Round1/2 原生帧形态）的不可达帧骨架不作闭包起点、不 rescue、落入删除；引擎已分配且属保护引擎（RTS 等 Stage1_3 降级骨架）时尊重引擎感知保活（IsFrameSkeletonRescued=IsProtectedEngineNode）。


## 触发与观测


PrunePass 将帧传值骨架从保活闭包移除的初版未区分引擎归属，构建成功但测试 `engine_assigned_rts_skeleton_keep_alive_and_ai_core_dead_chain_pruned` 失败：应保留的 Enter 节点变为 nullptr。该反例要求先保留已经分配到保护引擎的骨架。

## 探针与操作

- 修复方案是把 9 类帧传值骨架类型（ENTER/REFENTER/SWITCH/REFSWITCH/SWITCHN/MERGE/REFMERGE/NEXTITERATION/REFNEXTITERATION）移出保活闭包收集与 rescue，但引擎归属保护优先：IsFrameSkeletonRescued=IsProtectedEngineNode，引擎已分配且属保护引擎（RTS/GeLocal/HCCL）的降级骨架仍保活——首次迭代因未区分引擎归属而破坏既有用例 engine_assigned_rts_skeleton_keep_alive_and_ai_core_dead_chain_pruned，修正后通过。

## 机制与判别

机制片段：

```
// 帧传值骨架类型：Enter/Switch/Merge/NextIteration及ref变体。此类节点的执行意义在帧内
// （向帧内传值/分支选择/汇聚/回边）；从图出口不可达 ⟺ 帧内无任何活消费者 ⟺ 骨架已无执行
// 意义。引擎未分配（第1/2轮时点，parser产生的原生帧形态）时不可达帧骨架保活只会产生输出
// 悬空的帧节点，并经输入闭包复活上游死链（如Variable→ReadVariableOp→Enter链），悬空骨架
// 随产物下发曾引发V1动态执行Await超时，故按死节点处置；引擎已分配且属保护引擎（RTS等，
// Stage1_3降级产生的骨架形态）时尊重引擎感知保活语义，可达帧骨架不受本判定影响。
const std::unordered_set<std::string> kFrameSkeletonOpTypes = {ENTER,
                                                               REFENTER,
                                                               SWITCH,
                                                               REFSWITCH,
                                                               SWITCHN,
                                                               MERGE,
                                                               REFMERGE,
                                                               NEXTITERATION,
                                                               REFNEXTITERATION};

bool IsFrameSkeletonNode(const NodePtr &node) {
  if ((node == nullptr) || (node->GetOpDesc() == nullptr)) {
    return false;
  }
  return kFrameSkeletonOpTypes.count(node->GetType()) > 0UL;
}

// 帧骨架是否按保活处置：引擎归属保护优先（引擎已分配且属保护引擎的降级骨架形态）；
// 引擎未分配（原生帧形态）时不可达即死帧，不保活
bool IsFrameSkeletonRescued(const NodePtr &node) {
  return IsProtectedEngineNode(node->GetOpDesc());
}

// 保活节点不可达时，沿入边反向收集输入闭包一并保活（不补控制边）；
// 引擎未分配的不可达帧骨架不作闭包收集起点（帧内无活消费者，保活无意义，
// 见kFrameSkeletonOpTypes注释）
void CollectKeepAliveClosure(const std::unordered_set<NodePtr> &all_nodes,
                             const std::unordered_set<NodePtr> &nodes_seen, std::unordered_set<NodePtr> &keep_closure) {
  for (const auto &node_ptr : all_nodes) {
    if ((nodes_seen.count(node_ptr) != 0UL) || (keep_closure.count(node_ptr) != 0UL) ||
        !IsKeepAliveNode(node_ptr) ||
        (IsFrameSkeletonNode(node_ptr) && !IsFrameSkeletonRescued(node_ptr))) {
      continue;
    }
```

```
    // 保活节点因消费者全死而不可达时，救援并补控制边；
    // 帧骨架（Enter/Switch/Merge/NextIteration等）引擎未分配时不可达 ⟺ 帧内无活消费者，
    // 保活只会悬空并复活输入死链（V1动态执行Await超时回归），不rescue、落入删除；
    // 引擎已分配且属保护引擎的降级骨架形态维持引擎感知保活
    if (IsKeepAliveNode(node_ptr) &&
        (!IsFrameSkeletonNode(node_ptr) || IsFrameSkeletonRescued(node_ptr))) {
      if (rescue_with_ctrl_edge) {
        GE_CHK_STATUS_RET(AddCtrlEdgeToOutNode(node_ptr, out_nodes[0]),
                          "Failed to add control edge between keep-alive node and out node.");
      }
      continue;
    }
```

## 验证信号


初版 `build=0, run=1`，上述保护引擎用例失败。修订后工具报告 `build=0, run=0`，30 项用例通过，另一组 58 项通过。这里不采用助手总结中的更大测试数或“所有执行路径零影响”断言。

## 适用与失效边界

适用：GE 编译器 PrunePass/保活白名单引发的 While 循环 V1 动态执行（IsTaskSink=0）Await 超时类问题。失效边界：仅"引擎未分配的不可达帧骨架"按死帧处置；引擎已分配且属保护引擎（RTS/GeLocal/HCCL）的降级骨架仍走引擎感知保活；含子图节点（IF/WHILE/CASE/FOR/PARTITIONEDCALL）不可套用（删父等于删子图）；确需保活某不可达骨架可用 _force_skip_prune 属性或 SetTargets。验证层级为 UT/ST/真实 atc 图对比（无 310Brc 真机复现；AI 报告的"RTS 控制边被剪"机理已被 DUMP_GE_GRAPH 对比否定，310B 特有结构可能性遗留）。

---
{
  "type": "Runbook",
  "title": "GE 内存图融合 pass 改写残差结构的两个陷阱与修复：DataConsumers 端口语义误判、模式链式依赖需顺序处理",
  "description": "GE 内存图 pass 把 Add→LayerNorm 子图改写为 AddLayerNorm 时连续踩两个改写 bug：(1) DataConsumers 返回的 port 是消费者输入端口，多输出节点（LayerNorm mean/var）被误改线报 RemoveEdge failed；(2) 残差 Add 链式依赖（block k 的 Add 是 block k+1 模式的输入臂）使两阶段'先收集后改写'引用已删节点报 input 0 is not linked。修复后 48/49 模式融合成功，avg 5.99→5.845ms（-2.4%）、verify max_abs 0.00126459 优于融合前。",
  "tags": [
    "task.debugging",
    "topic.compilation",
    "topic.model_serving",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "910"
  ]
}
---

# GE 内存图融合 pass 改写残差结构的两个陷阱与修复：DataConsumers 端口语义误判、模式链式依赖需顺序处理

## 适用场景

- 模型/框架：onnx 图经 GE Session v2 加载后的 GE 内存图改写 pass（本例把 ViT 的 `Add(x1,x2)→LayerNormalization` 子图改写为 AddLayerNorm，M400/ViT-L/14，48/49 模式）；任何需要「删节点+改接线」的 GE GNode/Graph API 使用者。
- 平台/版本：Ascend 910B 单卡，CANN 9.1.0（aarch64），GE C++ API（ge::Graph/ge::GNode，gnode.h）。
- 目标与工作负载：消除 GE parser 把 LayerNormalization 降级为 Identity/Shape/BroadcastTo(γ)/BroadcastTo(β)/LayerNorm 五件套带来的 98 个 broadcast 微 kernel（γ/β 被物化为 [1,581,1024] 全量张量）；单卡推理 batch=1 串行。
- 缺失信息：未在其它 CANN 版本上复核 DataConsumers 端口语义（依据为 9.1.0 行为与错误日志）。

## 触发与观测

背景（事件 711/713）：GE parser 把 LayerNormalization 降级为五件套，γ/β 被物化为 [1,581,1024] 全量张量（每 iter 约 116MB 纯广播流量，iter2 画像 LN 族 988us/16.9%）。onnx 侧 48/49 个 LN 由 Add 供给、每个 Add 恰有 2 个消费者（事件 722），ge LayerNorm 节点带可读 `epsilon` 属性（事件 726）。

第一次失败（事件 762/765）：`[LN-PASS] fused 48 Add->LayerNorm pattern(s) into AddLayerNorm` 后 warmup 失败，plog：

```
[ERROR] GE(3558371,GEsession_test_acl):2026-10-15-12:30:15.925.444 [graph_utils.cc:252]3558371 RemoveEdge: ErrorNo: 4294967295(failed)[Remove][Edge] Failed.
[ERROR] GE(3558371,GEsession_test_acl):2026-10-15-12:30:15.925.452 [graph.cc:355]3558371 RemoveEdge: ... between [PartitionedCall_/backbone/blocks/blocks.0/norm2/LayerNormalization_LayerNorm_42] and [PartitionedCall_/backbone/blocks/blocks.0/norm2/LayerNormalization_Adds_46] failed.
[ERROR] GE(3558371,GEsession_test_acl):2026-10-15-12:30:15.925.464 [anchor.cc:503]3558371 LinkTo: ErrorNo: 4294967295(failed)[Check][Param] dest anchor is nullptr or the peerAnchors is not empty.
```

第二次失败（事件 772/775，端口修复后）：仍 warmup 失败，plog：

```
[ERROR] GE(3563052,GEsession_test_acl):2026-10-15-12:32:01.267.975 [node_utils_ex.cc:94]3563214 IsInputsValid: ErrorNo: 4294967295(failed)[Check][Param] operator AddLayerNorm_pass_1's input 0 is not linked.
```

## 探针与操作

Bug 1（DataConsumers 端口误判）修复（事件 768，newString 原文）：

```cpp
    graph.AddDataEdge(*p.x1, p.x1_port, ln_node, 0);
    graph.AddDataEdge(*p.x2, p.x2_port, ln_node, 1);
    graph.AddDataEdge(*p.gamma, p.gamma_port, ln_node, 2);
    graph.AddDataEdge(*p.beta, p.beta_port, ln_node, 3);
    // LN.out0（y）消费者 -> AddLayerNorm.out0(y)；mean/var 路径（out1/2）随 LN 删除由 DCE 清理
    for (int32_t out_i = 0; out_i < static_cast<int32_t>(p.ln->GetOutputsSize()); ++out_i) {
      if (out_i != 0) continue;
      auto cs = p.ln->GetOutDataNodesAndPortIndexs(out_i);
      for (auto &c : cs) {
        graph.RemoveEdge(*p.ln, out_i, *c.first, c.second);
        graph.AddDataEdge(ln_node, 0, *c.first, c.second);
      }
    }
    // Add 的其他消费者（除 id_x 外）-> AddLayerNorm.out3(x1+x2)
    for (auto &c : DataConsumers(*p.add)) {
      if (SameNode(c.first, p.id_x)) continue;
      graph.RemoveEdge(*p.add, 0, *c.first, c.second);
      graph.AddDataEdge(ln_node, 3, *c.first, c.second);
    }
    fused++;
```

Bug 2（模式链式依赖）修复：把「先收集全部模式再统一改写」重构为逐个「匹配→立即改写」（事件 784，newString 原文节选）：

```cpp
  // 顺序处理（非两阶段）：残差 Add 链式依赖后继模式（block k 的 Add 是 block k+1 模式的输入臂），
  // 必须逐个「匹配->立即改写」，后继模式在改写后的当前图上匹配（x1/x2 可能已是前一个 AddLayerNorm.out3）
  std::vector<std::string> ln_names;
  for (auto &n : graph.GetAllNodes()) {
    if (!IsType(n, "LayerNorm")) continue;
    std::string nm;
    if (GetName(n, &nm)) ln_names.push_back(nm);
  }
  if (ln_names.empty()) {
    std::cout << "[LN-PASS] no LayerNorm node found (graph unchanged)" << std::endl;
    return 0;
  }

  int fused = 0;
  std::set<std::string> removed_names;
  for (auto &ln_name : ln_names) {
    // 按名重取节点（图已因前序改写变化）
    GNodePtr ln;
    for (auto &n : graph.GetAllNodes()) {
      std::string nm;
      if (GetName(n, &nm) && nm == ln_name) {
        ln = std::make_shared<ge::GNode>(n);
        break;
      }
    }
    if (ln == nullptr) continue;  // 已被前序 DCE 波及
```

修后运行（事件 788）：`[LN-PASS] fused 48 Add->LayerNorm pattern(s) into AddLayerNorm` + `inference finished: success`。

## 机制与判别

结论一（逐字）：

GE 图 API 的 `DataConsumers` 返回 (node, port) 中 port 是消费者输入端口而非生产者输出端口；对多输出节点改线必须先按生产者输出端口枚举（`GetOutDataNodesAndPortIndexs(out_i)`）再改接，否则 LayerNorm 的 mean/var 路径（out1/out2）会被误当作 y 消费者改线，报 `RemoveEdge ... failed` 与 `dest anchor is nullptr or the peerAnchors is not empty`。

判别依据：RemoveEdge 失败的边是 `LayerNormalization_LayerNorm_42 → LayerNormalization_Adds_46`（LN 的 out1/out2 下游链，即 mean/var 的 Adds/Rsqrt 侧），不是 y 主路径——说明遍历消费者的方式把非 y 端口的消费者也当成 y 改线对象。

结论二（逐字）：

残差链式依赖（block k 的残差 Add 是 block k+1 模式的输入臂）使「先收集全部模式再统一改写」的两阶段设计失效：后继模式引用已被删除的节点，报 `operator AddLayerNorm_pass_1's input 0 is not linked`；重构为逐个「匹配→立即改写」的顺序处理（按名重取节点、后继模式在改写后的当前图上匹配）后 48/49 个 Add→LayerNorm 融合成功执行。

判别依据：报错节点是 `AddLayerNorm_pass_1`（第二个融合节点）的 input 0 未链接——第一个模式改写删掉了它的输入臂节点（残差 Add），两阶段缓存的 GNodePtr 悬空。`block0/norm1`（Concat 喂入而非 Add）保持原样，48/49 为预期覆盖。

顺序处理还带来一个语义变化：改写后 block k+1 的 x1/x2 可能已是前一个 AddLayerNorm 的 out3（additional_output=true 输出原始和供残差链复用），这正是 residual 链正确复用和的方式。

## 验证信号

- 事件 765/775：两处失败的 plog 客观报错（Ascend 910B / CANN 9.1.0）。
- 事件 788：修复后 48/49 融合 + 推理 success（单次运行）。
- 事件 792：双门禁（fp16+FA 叠加配置）：

结论三（逐字）：

第 4 轮双门禁通过：AddLayerNorm 融合后 verify PASS（max_abs=0.00126459，优于融合前 fp16 口径的 1.57e-3），同口径 avg 5.99→5.845ms（-2.4%，复测 5.844/5.845 与 5.97～5.99 分布明显分离）。

（基线信号：事件 623 avg 5.993/5.992/5.975ms；候选信号：事件 792 iter=500 avg 5.844ms、iter=1000 avg 5.845ms。均为单次 1000-iter 运行。）
- 事件 800：iter3 msprof 画像确认 kernel 实例 407→310/iter、AddLayerNorm 717.4us/iter、LN 族（49 LN+98 broadcastto）从 988us 降为残余（LayerNormalization_Layer 1 处 15.0us + broadcastto 2 处 11.6us）。
- 事件 977：全关开关回归（基线口径）verify PASS。

## 适用与失效边界

- 端口语义与「顺序处理」结论来自 CANN 9.1.0 GE C++ API 实测；升级版本须复核（`GetOutDataNodesAndPortIndexs`/`DataConsumers` 行为）。
- 顺序处理模式适用于「模式之间有共享节点/链式依赖」的图改写；对互不重叠的独立模式两阶段仍可用，但顺序处理是无害的一般化。
- 48/49 覆盖的边界：非 Add 喂入的 LN（如 CLS/Concat 路径）不匹配、保持原样，是设计行为而非遗漏。
- additional_output=true 依赖 AddLayerNorm 算子提供原始和输出（out3）；换用其它融合变体（如 PostLayerNorm）时残差复用方式不同。
- 残差链上 mean/var 下游的 Adds/Rsqrt/Cast 孤立链依赖 pass 内置本地 DCE 清理（Const/Identity/Shape/BroadcastTo/Adds/Rsqrt/Cast/GatherV2/UnsqueezeV3/ConcatD/Fill 类型白名单）。

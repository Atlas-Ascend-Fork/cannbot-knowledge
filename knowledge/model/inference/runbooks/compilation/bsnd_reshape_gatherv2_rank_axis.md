---
{
  "type": "Runbook",
  "title": "FA BSND 布局重构：预分头 Reshape 用 3×GatherV2(rank-0 标量索引, axis=2) 直切 q/k/v，吸收双 Transpose（SplitV 动态输出路线不可用）",
  "description": "消除 attention 两侧 Transpose 族（iter3 合计约 455us/8.1%）的 GE 内存图改法：从预分头 Reshape [B,S,3,H,D] 用 3 个 GatherV2(标量索引, axis=2) 一步直切 q/k/v [B,S,H,D]（BSND 输入布局），FA(BSND) 输出直连尾 Reshape。OperatorFactory 创建的 SplitV 工厂节点无静态输出锚点、UpdateOutputDesc 也无法扩展动态输出，SplitV+SqueezeV3 路线不可采用。落地后 avg 5.845→5.653ms（-3.3%）、verify PASS，最大误差与 BNSD 的记录相同（未直接逐元素比较两版输出）。",
  "tags": [
    "task.implementation",
    "topic.compilation",
    "topic.model_serving",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "910"
  ]
}
---
# FA BSND 布局重构：预分头 Reshape 用 3×GatherV2(rank-0 标量索引, axis=2) 直切 q/k/v，吸收双 Transpose（SplitV 动态输出路线不可用）

## 适用场景

- 模型/框架：fused-qkv 形态的 ViT attention（qkv 投影 → Reshape [B,S,3,H,D] → 预分头 Transpose → SplitV → SqueezeV3×3 → q/k/v），GE Session v2 内存图 pass（GE_FA_QKV_LAYOUT=BSND 分支）。
- 平台/版本：Ascend 910B 单卡，CANN 9.1.0（aarch64），FlashAttentionScore 支持 input_layout=BSND。
- 目标与工作负载：消除 attention 两侧 Transpose 族（iter3 画像两个 Transpose 族 233.2+221.9us，合计约 455us/8.1%）；单卡推理 batch=1 串行，叠加已落地的 fp16 全图 + FA 融合 + AddLayerNorm 融合。
- 缺失信息：仅验证 fp16 全图执行（fp32 原生下未单独测 BSND 分支收益）。

## 触发与观测

观测（事件 800，iter3 msprof kernel 族表）：`other:Transpose_Transpose_#` 233.2us/iter（4.14%）+ `other:Transpose_#_Transpose_#` 221.9us/iter（3.94%）为可消除候选；LayerScale Mul 升为独立 kernel 283us。

失败路线（不可采用）：先用「新建 SplitV(dim=2) + SqueezeV3×3」实现 BSND 直切，两次尝试均在 warmup 失败——

事件 877：

```
[ERROR] GE(3593210,GEsession_test_acl):2026-10-15-12:44:54.695.987 [node.cc:482]3593210 GetOutDataAnchor: ErrorNo: 4294967295(failed)[Check][Param] Op[FAbsnd_0_splitv] doesn't have index[0]'s out_data_anchor which optype is SplitV.
```

尝试用 `UpdateOutputDesc` 扩展 3 个输出（事件 880）后仍失败（事件 887）：

```
[ERROR] GE(3593210,GEsession_test_acl):2026-10-15-12:46:35.909.545 [op_desc.cc:730]3597342 UpdateOutputDesc: ErrorNo: 4294967295(failed)[Check][Param] The index is invalid. index[0]
```

结论一（逐字）：

OperatorFactory 工厂创建的 SplitV 节点没有静态输出锚点：`AddDataEdge` 报 `doesn't have index[0..2]'s out_data_anchor`，尝试 `UpdateOutputDesc` 扩展动态输出也报 `The index is invalid. index[0..2]`——SplitV 路线不可采用。

## 探针与操作

改用 3×GatherV2（rank-0 标量索引）替代（事件 894，newString 原文；`ge::Shape({})` 后因重载歧义编译错误被 sed 修正为 `ge::Shape()`，见下）：

```cpp
    // BSND：从预分头 Reshape [B,S,3,H,D] 用 3 个 GatherV2(标量索引, axis=2) 直切 q/k/v [B,S,H,D]
    GNodePtr bsnd_sq[3] = {nullptr, nullptr, nullptr};
    if (use_bsnd) {
      static int bseq = 0;
      std::string btag = "FAbsnd_" + std::to_string(bseq++);
      GNodePtr axis_const = MakeConstNode(graph, btag + "_axis", ge::DT_INT64, {}, {2});
      {
        ge::TensorDesc d(ge::Shape({}), ge::FORMAT_ND, ge::DT_INT64);
        axis_const->UpdateOutputDesc(0, d);
      }
      for (int i = 0; i < 3; ++i) {
        GNodePtr idx_const = MakeConstNode(graph, btag + "_idx" + std::to_string(i),
                                           ge::DT_INT64, {}, {i});
        {
          ge::TensorDesc d(ge::Shape({}), ge::FORMAT_ND, ge::DT_INT64);
          idx_const->UpdateOutputDesc(0, d);
        }
        GNodePtr gv = MakeUnaryNode(graph, btag + "_g" + std::to_string(i), "GatherV2");
        std::string gvt;
        if (!GetType(*gv, &gvt) || gvt != "GatherV2") {
          std::cout << "[FA-PASS][ERROR] create GatherV2 failed" << std::endl;
          return -1;
        }
        {
          ge::TensorDesc xd(ge::Shape({-1, -1, 3, static_cast<int64_t>(p.heads), -1}),
                            ge::FORMAT_ND, ge::DT_FLOAT);
          ge::TensorDesc idd(ge::Shape({}), ge::FORMAT_ND, ge::DT_INT64);
          ge::TensorDesc axd(ge::Shape({}), ge::FORMAT_ND, ge::DT_INT64);
          ge::TensorDesc od(ge::Shape({-1, -1, static_cast<int64_t>(p.heads), -1}),
                            ge::FORMAT_ND, ge::DT_FLOAT);
          gv->UpdateInputDesc(0, xd);
          gv->UpdateInputDesc(1, idd);
          gv->UpdateInputDesc(2, axd);
          gv->UpdateOutputDesc(0, od);
        }
        graph.AddDataEdge(*p.qkv_reshape, 0, *gv, 0);
        graph.AddDataEdge(*idx_const, 0, *gv, 1);
        graph.AddDataEdge(*axis_const, 0, *gv, 2);
        bsnd_sq[i] = gv;
      }
    }
```

实现细节修正：事件 898 编译报 `call of overloaded 'Shape(<brace-enclosed initializer list>)' is ambiguous`，事件 901 用 sed 将 `ge::TensorDesc d(ge::Shape({}), ...)` 统一改为 `ge::TensorDesc d(ge::Shape(), ...)` 后编译通过。dtype 依据：图内现有 SqueezeV3 axes 与 SplitV size_splits 的 Const 为 DT_INT64、split_dim 为 DT_INT32（事件 815）。

修后运行（事件 902）：`GE_FA_QKV_LAYOUT=BSND` 下 24 层 FAS + 48 LN 融合照常，`inference finished: success`。

## 机制与判别

结论二（逐字）：

从预分头 Reshape [B,S,3,H,D] 用 3 个 GatherV2(rank-0 标量索引, axis=2) 可一步直切出 q/k/v [B,S,H,D]（BSND 输入布局），无需 SplitV+SqueezeV3；iter3 画像中两个 Transpose 族合计约 455us（233.2+221.9us），iter4 确认 Transpose 族清零、新增 GatherV2 397.3us。

机制与判别：
- SplitV 工厂节点（ops-info 标 output0 为 `dynamic`）没有预创建的输出锚点，GE GNode API 无法为动态输出补锚点——这是与「静态输出算子工厂创建」的根本差异；GatherV2 输出静态（1 个），工厂创建即可用。
- GatherV2(rank-0 索引, axis=2) 在语义上等价于按 dim2 取第 i 个切片并去维，一步完成 SplitV(port i)+SqueezeV3；图内已有 rank-0 索引的 GatherV2 先例（GatherElements pass）。
- FA(BSND) 输出 [B,S,H,D] 直连尾 Reshape，替代原「AV 后 Transpose_2 → Reshape_1」路径；预分头 Transpose 被吸收（qkv_reshape 直连 GatherV2）。
- 未验证推断：GatherV2 397.3us 中若改用一次 Split 语义的更优算子或融合 kernel 理论仍有空间（qkv-split 单算子自定义 kernel 在收口动作表中列为 P2）。

## 验证信号

- 事件 877/887：SplitV 路线的客观失败（两次 warmup 失败，plog）。
- 事件 902：GatherV2 路线融合执行成功（单次运行）。
- 事件 906：双门禁（fp16+FA+LN 叠加配置）：

结论三（逐字）：

第 5 轮双门禁通过：BSND 重构后 verify PASS、max_abs=0.00126459，与 R4（BNSD）记录的最大误差相同；该摘要指标不证明两版输出逐位一致，同口径 avg 5.845→5.653ms（-3.3%）。

（基线信号：事件 792 avg 5.845ms；候选信号：事件 906 iter=1000 avg 5.653ms。均为单次 1000-iter 运行。）
- 事件 910：iter4 msprof 画像确认 Transpose 族消失（族表中无 Transpose 行）、`other:FAbsnd_#_g#` 72.4 实例 397.3us/iter。

## 适用与失效边界

- 前提：attention 为 fused-qkv 形态（一次投影 → Reshape [B,S,3,H,D]）且 FA 算子支持 BSND input_layout；先分头后投影（q/k/v 三路独立投影）形态不适用本模式。
- SplitV 动态输出限制适用于 GE GNode 工厂创建路径；若图内已存在 parser 生成的 SplitV（有锚点）可直接复用其输出，不必新建。
- `ge::Shape({})` 与 `ge::Shape()` 的重载歧义是 CANN 9.1.0 头文件行为，跨版本需复核。
- 收益条件：Transpose 族占可见比例（本例 8.1%）；GatherV2 本身有 397us 开销，净收益取决于被吸收 Transpose 与 SplitV+Squeeze 的规模。
- 仅在本轨迹 fp16 全图 + BNSD→BSND 切换的同口径对比中验证；其它精度/布局组合未测。

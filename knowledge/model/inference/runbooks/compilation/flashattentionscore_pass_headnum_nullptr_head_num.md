---
{
  "type": "Runbook",
  "title": "FlashAttentionScore 融合 pass 的算子签名适配修复：headNum nullptr 报错定位到 head_num 属性名与 attention_out 输出端口 3",
  "description": "GE 图融合 pass 创建 FlashAttentionScore 节点时沿用 PromptFlashAttention 的属性名（num_heads/pre_tokens）会在 infershape 阶段报 headNum is nullptr!。依据 aic-ascend910_93-ops-info-transformer.json 修正为 head_num/pre_tockens/next_tockens（CANN 原文拼写），锚点消费者改接输出端口 3（attention_out）后 24 层融合成功：verify max_abs=0.00148183 与不融合基线对 golden 的最大误差接近，同口径 avg 11.77→9.45ms（-19.7%）。",
  "tags": [
    "task.debugging",
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
# FlashAttentionScore 融合 pass 的算子签名适配修复：headNum nullptr 报错定位到 head_num 属性名与 attention_out 输出端口 3

## 适用场景

- 模型/框架：fp32 原生 onnx ViT（本例 M400，ViT-L/14，24 层，16 头，581 token），GE Session v2 内存图 pass（graph_fusion_pass.cc）将 attention 链（qk BMM + scale Mul + Softmax + av BMM + k^T Transpose）融合为 FlashAttentionScore。
- 平台/版本：Ascend 910B 单卡（卡 0），CANN 9.1.0（aarch64），算子定义依据 `aic-ascend910_93-ops-info-transformer.json`。
- 工作负载：单卡推理，batch=1，THREAD_NUM=1 串行，circle=1000，随机输入 seed=20240101，onnxruntime golden。
- 缺失信息：FAS 的 fp16/bf16 路径属性差异未单独验证（本例 fp32 原生后随 R2 全图转 fp16）。

## 触发与观测

故障（事件 550/557）：pass 沿用 PromptFlashAttention 的属性名创建 FAS 节点后，图编译在 infershape 阶段失败：

```
[ERROR] OP(3434744,GEsession_test_acl):2026-10-15-11:46:50.118.480 [flash_attention_score_infershape.cpp:54][OPS_BASE][InferShapeFlashAttentionScore][3434963] OpName:[FlashAttentionScore_pass_0] headNum is nullptr!
[ERROR] GE(3434744,GEsession_test_acl):2026-10-15-11:46:50.118.770 [base_pass.cc:479]3434963 RunPassesGraphRepass: ErrorNo: 4294967295(failed)[Process][Passes] on node FlashAttentionScore_pass_0 type FlashAttentionScore failed, error code:4294967295
```

查 ops-info（事件 567）：FAS 的 attr 列表为 `scale_value,keep_prob,pre_tockens,next_tockens,head_num,input_layout,inner_precise,sparse_mode,pse_type,seed,offset,out_dtype,softmax_out_layout`，其中 `attr_head_num` 为 required int；`attr_input_layout` 为 required str。查输入/输出签名（事件 571）：仅 query/key/value 为 required 输入；output0/1/2/3 依次为 softmax_max/softmax_sum/softmax_out/attention_out。

结论一（逐字）：

FlashAttentionScore 的必填属性名为 `head_num`（非 num_heads）、`pre_tockens`/`next_tockens`（CANN 原文拼写如此）、`input_layout`；输出端口 0/1/2/3 依次为 softmax_max/softmax_sum/softmax_out/attention_out，改线时锚点消费者须接 attention_out=端口 3；漏设 head_num 时 GE infershape 阶段直接报 `headNum is nullptr!`（flash_attention_score_infershape.cpp:54）。

## 探针与操作

修复前（失败态，事件 557）：`GE_FA_FUSION_PASS=1 GE_FA_OP_TYPE=FlashAttentionScore bash run.sh 400 --circle 1 --info`，plog 报 headNum nullptr。

修复：按 ops-info 修正属性名并区分 FAS/PFA 分支（事件 574，newString 原文）：

```cpp
    int32_t inner_precise = 1;
    const char *ip_env = std::getenv("GE_FA_INNER_PRECISE");
    if (ip_env != nullptr) inner_precise = std::atoi(ip_env);
    float scale = p.scale;
    ge::AscendString layout(p.layout);
    fa_node.SetAttr(ge::AscendString("input_layout"), layout);
    fa_node.SetAttr(ge::AscendString("scale_value"), scale);
    fa_node.SetAttr(ge::AscendString("sparse_mode"), sparse);
    fa_node.SetAttr(ge::AscendString("inner_precise"), inner_precise);
    if (fa_op_type == "FlashAttentionScore") {
      // FAS 属性名（ascend910_93 ops-info）：head_num / pre_tockens / next_tockens / keep_prob；
      // 输出端口：0=softmax_max 1=softmax_sum 2=softmax_out 3=attention_out
      int64_t head_num = heads;
      fa_node.SetAttr(ge::AscendString("head_num"), head_num);
      int64_t pre_tockens = no_causal;
      fa_node.SetAttr(ge::AscendString("pre_tockens"), pre_tockens);
      int64_t next_tockens = no_causal;
      fa_node.SetAttr(ge::AscendString("next_tockens"), next_tockens);
      float keep_prob = 1.0F;  // 无 dropout
      fa_node.SetAttr(ge::AscendString("keep_prob"), keep_prob);
    } else {  // PromptFlashAttention（M200 验证路径）
      fa_node.SetAttr(ge::AscendString("num_heads"), heads);
      fa_node.SetAttr(ge::AscendString("pre_tokens"), no_causal);
      fa_node.SetAttr(ge::AscendString("next_tokens"), no_causal);
    }
```

锚点消费者改接 FA 输出端口（事件 577，newString 原文）：

```cpp
    // 锚点消费者改接 FA 输出（FAS: attention_out=端口3；PFA: 端口0）
    int32_t fa_out_port = (fa_op_type == "FlashAttentionScore") ? 3 : 0;
    for (auto &c : DataConsumers(*p.rout)) {
      graph.RemoveEdge(*p.rout, 0, *c.first, c.second);
      graph.AddDataEdge(fa_node, fa_out_port, *c.first, c.second);
    }
```

途中另有一个编译期小坑（事件 539/542）：`SetAttr("keep_prob", 1.0F)` 字面量不能绑定 `float32_t&` 非常量引用（旧二进制被误跑），修复为具名左值 `float keep_prob = 1.0F;`。

修后运行（事件 581）：`[FA-PASS] fused 24 attention block(s) into FlashAttentionScore` + `inference finished: success`。

## 机制与判别

- 报错层级判别：`headNum is nullptr` 来自算子侧 infershape 回调（flash_attention_score_infershape.cpp），说明节点已建、属性未按算子定义提供——与 engine 选择失败（见 compilation/promptflashattention_fp32_engine_warmup_failed.md）是不同层级。
- 端口判别：FAS 四个输出全部 required，但语义上只有 attention_out 承接原链输出；PFA 的输出在端口 0。两分支用 `fa_out_port` 三目区分。
- keep_prob 属性是 FAS 必填（默认 1），无 dropout 场景设 1.0F 即可。

结论二（逐字）：

M400 第 1 轮双门禁通过：24 层 attention 链融合为 FlashAttentionScore（fp32/BNSD，q/k/v 直连 SqueezeV3 输出）后 verify PASS（max_abs=0.00148183，对 golden 的最大误差与不融合基线 0.00148179 接近）；GE_FA_FUSION_PASS= 空值关闭后回归 verify PASS（max_abs=0.00148179，与基线记录的最大误差相同；未直接比较两版输出数组）。

## 验证信号

- 事件 557：修复前 infershape 失败（headNum is nullptr）。
- 事件 567/571：ops-info 属性名与输入/输出签名（CANN 9.1.0 安装目录 JSON 实测）。
- 事件 581：修复后 24 层融合成功、推理 success（单次运行）。
- 事件 588/592：干净闭环 verify PASS，max_abs=0.00148183（门禁 rtol=1e-2/atol=2e-3）。
- 事件 599：GE_FA_FUSION_PASS= 空值 off-switch 回归 verify PASS，max_abs=0.00148179，与基线记录的最大误差相同；未直接比较两版输出数组。
- 性能（同会话同口径、fp32 对 fp32、单次 circle=1000）：

结论三（逐字）：

同口径复测（fp32、batch=1、THREAD_NUM=1、circle=1000、卡 0）：FA 融合后 avg 11.77→9.45ms（-19.7%）、TP99 11.99→9.64ms（-19.6%）、串行 QPS 84.9→105.8（+24.6%）。

（基线信号：事件 133 GE PROGRESS iter=400/600/800 avg 11.768/11.770/11.772ms、iter=1000 11.814ms；候选信号：事件 595 iter=1000 avg 9.454ms、TP99 9.641ms、Qps 105.76。均为单次 1000-iter 运行的汇报值。）

## 适用与失效边界

- 属性名/端口结论绑定 CANN 9.1.0 的 ascend910_93 ops-info；版本升级后以 ops-info JSON 复核为准（`pre_tockens`/`next_tockens` 拼写尤其易随版本变动）。
- 本例 BNSD 布局、无 mask、无 dropout、keep_prob=1、inner_precise=1；带 atten_mask/pse 的场景需补齐对应 optional 输入。
- inner_precise=0 的性能影响为负（见 performance/geluv2_approximate_none_erf_inner_precise.md）。
- 收益条件：attention 链为小 K BMM + 中间量物化主导（本例基线 attention 链约 39%）；纯 GEMM 主导的模型收益有限。

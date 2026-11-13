---
{
  "type": "Runbook",
  "title": "LayerScale 常量折叠进 proj/fc2 权重：Mul(Add(MatMul(x,W),b),ls)→W·ls/b·ls 原地改写 Const（GE parser 将 MatMul 映射为 BatchMatMulV2）",
  "description": "GE 内存图 pass 把 timm LayerScale 的 Mul(Add(MatMul(x,W),b),ls) 折叠为 Add(MatMul(x,W·ls),b·ls)（ls 逐通道 Const，数值等价原地改写权重/偏置 Const，删 48 个 Mul）。两个实现要点：GE parser 将 onnx MatMul 映射为 BatchMatMulV2，匹配器须同时接受两种类型；pass 循环内误用 return fail(...) 会中止整个 pass，须改 continue。落地后 avg 5.653→5.368ms（-5.0%）、verify PASS、全关回归与基线口径一致。",
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
# LayerScale 常量折叠进 proj/fc2 权重：Mul(Add(MatMul(x,W),b),ls)→W·ls/b·ls 原地改写 Const（GE parser 将 MatMul 映射为 BatchMatMulV2）

## 适用场景

- 模型/框架：timm/DINOv2 风格 ViT 的 LayerScale 结构（`Mul(Add(MatMul(x, W), b), ls)`，ls 逐通道 [C] 可训练乘子），onnx 图经 GE Session v2 加载，GE 内存图 pass（GE_LS_FOLD_PASS=1）。
- 平台/版本：Ascend 910B 单卡（卡 0），CANN 9.1.0（aarch64），fp16 全图 + FA(BSND) + AddLayerNorm 叠加配置。
- 目标与工作负载：单卡推理 batch=1 串行（THREAD_NUM=1、circle=1000）；消除 AddLayerNorm 融合后浮出的 48 个独立 LayerScale Mul kernel（iter3 画像 283us）。
- 缺失信息：仅验证 fp16 口径；fold 后权重 Const 的 dtype 具体改写实现（DT_FLOAT 值域内乘法）未逐行复核。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发（事件 800，iter3 msprof 族表）：`other:Mul` 48.2 实例 283.1us/iter——AddLayerNorm 融合后 LayerScale Mul 变为独立 kernel。

设计（事件 913，头文件注释原文）：

```
// LayerScale 折叠（GE_LS_FOLD_PASS=1，默认关闭）：
//   Mul( Add(MatMul(x, W), b), ls )  ->  Add(MatMul(x, W*ls), b*ls)
// （timm LayerScale：ls 逐通道 [C]，W 列缩放数值等价；Const value 原地改写，删 Mul）
// 返回折叠数量；-1 表示错误
int RunLayerScaleFold(ge::Graph &graph);
```

第一个 bug（事件 931/933）：LS-PASS 无 folded 输出，debug 仅一条 fail 后即停止：

```
[FA-PASS] fused 24 attention block(s) into FlashAttentionScore
[LN-PASS] fused 48 Add->LayerNorm pattern(s) into AddLayerNorm
[LS-PASS][dbg] fail at arms (/backbone/Mul)
```

第二个 bug（事件 943，continue 修复后仍 folded 0）：ls 链匹配挂在 add-arm-type；dump 图定位（事件 959）：

```
ge:Add   /backbone/blocks/blocks.0/attn/proj/Add   in=['backbone.blocks.0.attn.proj.bias_Initial<-ge:Const', 'MatMul<-ge:BatchMatMulV2']
```

## 探针与操作

Bug 1 修复（事件 939，仅限 RunLayerScaleFold 函数体的正则替换，原文）：

```
python3 - << 'EOF'
import re
p = '${LOCAL_PATH_1}'
src = open(p).read()
# 只在 RunLayerScaleFold 函数体内替换（从 "int RunLayerScaleFold" 到其后第一个 "\n}\n"）
start = src.index('int RunLayerScaleFold')
end = src.index('\n}\n', start)
body = src[start:end]
# return fail(...); -> { fail(...); continue; }
body2 = re.sub(r'return fail\("([^"]+)"\);', r'{ fail("\1"); continue; }', body)
src = src[:start] + body2 + src[end:]
open(p, 'w').write(src)
print("replaced:", len(re.findall(r'\{ fail\(".*"\); continue; \}', body2)))
EOF
```

事件 940 输出 `replaced: 15`。

Bug 2 修复（事件 962，newString 原文）：

```cpp
    // Add 两臂：MatMul/BatchMatMulV2 输出 + Const(bias)
    GNodePtr mm = nullptr, bias_node = nullptr;
    for (int i = 0; i < 2; ++i) {
      auto arm = x_node->GetInDataNodesAndPortIndexs(i);
      if (arm.first == nullptr) { fail("add-arm-null"); continue; }
      std::string at;
      GetType(*arm.first, &at);
      if (at == "MatMul" || at == "BatchMatMulV2") {
        mm = arm.first;
      } else if (at == "Const") {
        bias_node = arm.first;
      } else {
        { fail("add-arm-type"); continue; }
      }
    }
```

修后运行（事件 969）：`[LS-PASS] folded 48 LayerScale into MatMul weights/bias`。

## 机制与判别

结论一（逐字）：

GE parser 将 onnx 的 MatMul 投影映射为 `BatchMatMulV2`（dump 图中 attn/proj/Add 的两臂为 Const(bias) + MatMul<-ge:BatchMatMulV2）；LayerScale 折叠匹配器必须同时接受 `MatMul` 与 `BatchMatMulV2`，否则 48 条 ls 链全部 fail at add-arm-type。

判别依据（事件 959）：dump 图（PreRunBegin 阶段）显示 proj/fc2 的 Add 两臂分别为 `ge:Const`（bias）与 `ge:BatchMatMulV2`（MatMul）——onnx MatMul 在 GE 图中的类型名与原始 op_type 不同，匹配器不能按 onnx 类型名匹配。

结论二（逐字）：

LS 折叠 pass 在循环里误用 `return fail(...)` 会使首个不匹配的 Mul 直接中止整个 pass（debug 仅输出一条 fail 后停止、无 folded 计数）；改为 `{ fail(...); continue; }`（共替换 15 处）后继续匹配，48 条 LayerScale 折叠成功。

判别依据（事件 933→943→969）：修复前 debug 输出仅一条 `fail at arms (/backbone/Mul)` 后停止（pass 被首个不匹配 Mul 中止）；continue 化后 debug 输出恢复逐 Mul 枚举（/backbone/Mul、act/Mul 等结构性 fail 均被跳过），BatchMatMulV2 匹配修正后 folded 48。

数值等价机制：`Mul(Add(MatMul(x,W),b),ls) = Add(MatMul(x,W·ls),b·ls)`（ls 逐通道 [C]，按 W 列缩放）；W/b 为 Const 节点，值域内原地改写、删 Mul，模型文件（onnx）零改动。fold 后 fp16 下的 max_abs 变化（1.26e-3→1.51e-3）判读为权重先乘 ls 再进入 fp16 GEMM 的舍入顺序差异，仍在门禁内。

## 验证信号

- 事件 959：dump 图 BatchMatMulV2 证据（单次 dump）。
- 事件 940/969：替换 15 处、folded 48（各单次运行）。
- 事件 973：双门禁（fp16+FA(BSND)+LN 叠加配置）：

结论三（逐字）：

第 6 轮双门禁通过：LayerScale 折叠（ls 乘子原地折进 proj/fc2 权重与 bias、删 48 个 Mul）后 verify PASS max_abs=0.00150873，同口径 avg 5.653→5.368ms（-5.0%）、串行 QPS 186.2；全关开关回归（基线口径）verify PASS max_abs=0.00148197。

（基线信号：事件 906 avg 5.653ms；候选信号：事件 973 iter=1000 avg 5.368ms、Qps 186.23。均为单次 1000-iter 运行。）
- 事件 977：全关开关回归（FORCE_16=False GE_FA_FUSION_PASS= GE_LN_FUSION_PASS= GE_LS_FOLD_PASS=，基线口径）verify PASS max_abs=0.00148197。
- 事件 1014：最终端到端复测（默认全开配置）`[LS-PASS] folded 48 ...`、avg 5.372ms、verify PASS max_abs=0.00150873（与 973 一致）。

## 适用与失效边界

- 适用条件：ls 为逐通道 [C] Const 且 W/b 为 Const 的 LayerScale 结构；ls 非常量（如依赖输入）或 W 非 Const 不可折叠。
- 类型边界：匹配必须覆盖 GE parser 类型映射（MatMul→BatchMatMulV2）；其它 onnx 类型（如 Gemm 头投影）映射不同，需另行 dump 图确认。
- `return fail()` vs `continue` 是所有「图遍历 + 部分匹配」pass 的通用陷阱：单个节点不匹配应跳过而非中止。
- 精度边界：fp16 下折叠改变权重缩放顺序，max_abs 由 1.26e-3 升至 1.51e-3（仍过 atol=2e-3 门禁）；对更紧门禁需评估。
- 收益条件：LayerScale Mul 在融合 LN 后变为独立 kernel 时收益明确（本例 48 Mul ≈283us，折叠净收益 -5.0%）；若 Mul 已被其它融合吸收则收益有限。
- 回退条件：GE_LS_FOLD_PASS=（空值关闭）；全关配置回归 verify PASS，max_abs=0.00148197（事件 977）；这不是与原基线输出的逐位比较。

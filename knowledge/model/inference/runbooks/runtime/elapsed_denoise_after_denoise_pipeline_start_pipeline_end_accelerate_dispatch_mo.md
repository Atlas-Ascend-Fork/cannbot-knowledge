---
{
  "type": "Runbook",
  "title": "MiniMax-H3 TP2+SP2 失败路线：约492s坏输出版本不能作为并行加速成果",
  "description": "区分失败运行、正常退出但黑屏/NaN的版本及后续修订；核对广播dtype和TokenRefiner归约，修正rank计时与text_encoder约9.6%的占比。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---


# MiniMax-H3 TP2+SP2 失败路线：约492s坏输出版本不能作为并行加速成果

## 适用场景

- 平台范围依据：source 0 seq 120的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型：`models/minimax_h3` 多模态生成模型（视频/音频生成，ModularPipeline，denoise 49-50 步，fl2va 工作负载）；Transformer 33.6B，BF16 权重 62.6 GiB。
- 基线状态：`accelerate.dispatch_model` 单进程顺序模型并行——按层切到 4 卡，同一时刻只有 1 卡计算，其余 3 卡空闲。
- 平台：Atlas NPU 4 卡（本例设备 5,6,10,14，每卡可用 HBM ~61 GiB），HCCL/torch_npu，diffusers 结构（Attention to_q/to_k/to_v 分立投影，FeedForward net[0]=SwiGLU(28672×5376)、net[2]=Linear(14336→5376)）。
- 约束：只允许修改项目目录内代码。

## 触发与观测

- 历史日志统计（source 0 seq42/44）给出顺序MP的denoise记录：未加融合补丁10条记录均值1277.564s；融合补丁版本20条记录均值1207.386s。这里只沿用日志统计，不把条数自动算成独立复现数。
- 第一轮TP2+SP2运行：4 rank的denoise为491.612–491.686s（source 0 seq1743）；这次运行随后在decode.video因 `wraps_fa` 参数缺失而失败（seq1738）。
- 修正该异常后重新启动：denoise492.092s；同一摘要输出pipeline 614.342s和621.224s两个值，包含rank0视频解码的摘要为621.224s，video decode66.409s（source 0 seq1825/1831）。进程结束与出片记录见seq1826/1831，不能与第一轮失败记录拼成一次成功运行。
- 后续排查轨迹（source 1 seq1/443/755/875）报告该TP+SP版本输出全黑和NaN，定位到接收端硬编码bf16，以及TokenRefiner缺少TP all-reduce。约492s属于正确性修复之前的配置。

## 探针与操作

改造内容（本项目 infer 脚本内实现，多进程 torch.distributed）：

1. **进程组**：TP 组 (0,1)(2,3) 切权重；SP 组 (0,2)(1,3) 切序列；world_size=4。
2. **权重切分**：Attention QKV/output 按 head（56→28 per rank）；FFN SwiGLU/down 按 inner_dim 对半；每 rank ~43 GiB transformer + 10 GiB VAE ≈ 53.3 GiB，可放入 61 GiB。
3. **文本编码器**（66GB）单卡放不下：rank 0 执行 + embeds 广播（广播前把张量移到 NPU）。
4. **VAE**：encoder 仅 rank 0（0.8s，不值得并行）；decode 仅 rank 0，且先把 transformer 移回 CPU 腾出 HBM。
5. 阶段化加载：文本编码 → 释放 → VAE/transformer 加载；这只是历史改造布局，不构成正确性证明。

以上为失败版本的实现思路记录。接收端不能硬编码广播张量dtype，TokenRefiner的TP输出还必须核对归约；本卡不提供可直接采用的完整修复实现。

## 机制与判别

- 多进程TP/SP能改变设备并行执行结构，但只有输出语义与精度合格的配套版本，才能作为优化收益候选。源码缺陷导致黑屏/NaN时，较短耗时不构成有效模型加速。
- 后续来源已把问题定位到dtype广播契约及TokenRefiner归约缺失；不能继续概括为“SP通信引入的收敛性问题”。其中接收端硬编码来自source 0 seq1574；后续修订见source 1 seq755/875。
- 新版本text_encoder耗时59.458s、含rank0解码的pipeline621.224s，占约9.6%；不能沿用基线的低占比或宣称开销可忽略。
- source 1 seq875区分修复前约492s与后续约370s，但没有在本卡合并成新的可比基线和精度验收；本卡不采纳370s为已验证加速。

## 验证信号

- 约491.6s的失败运行和重跑492.092s分别保留，不合成“单次运行四rank为491.6–492.1s”。
- 重跑621.224s的pipeline日志、保存文件和正常退出只说明执行链路完成，不说明输出正确；另一rank/摘要的614.342s须与含rank0视频解码口径区分。
- 后续用户报告黑屏与记录中的NaN否定该版本作为有效优化成果；1207/492≈2.45仅是历史坏输出配置与旧日志数值的比值，不是通过精度门禁的模型加速比。

## 适用与失效边界

- 用于单机多卡多模态生成模型并行改造的失败路线识别：先对齐广播dtype、各TP模块的归约与完整输出验收，再比较性能。
- 同一问题的前后轨迹必须按源码版本、运行批次、rank与计时范围关联。失败运行、成功退出但坏输出、正确性修复后的运行属于不同证据单元。
- 原来源未形成修复后的同负载、同口径、精度合格A/B闭环，不能从本卡直接采用2.45×或后续370s作为收益承诺。

## 附：断言存档

- TP2+SP2的历史约492s记录对应后续发现黑屏/NaN的版本；接收端dtype与TokenRefiner TP all-reduce缺陷应在性能比较之前解决。
- 分开记录491.6s失败运行、492.092s重跑和包含rank0解码的621.224s pipeline；正常退出不等于模型正确。

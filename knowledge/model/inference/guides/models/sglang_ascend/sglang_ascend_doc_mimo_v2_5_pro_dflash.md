---
type: Guide
title: MiMo-V2.5-Pro 的 MXFP4 与 DFlash PD 参考配置
description: 记录A3固定v0.5.18-cann9.0.0-a3镜像下MiMo FP4/DFlash的DP2/TP8、device_urma与分角色验证要求。
tags:
- task.implementation
- task.optimization
- topic.model_serving
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/mimo_v2_5_pro.mdx
  role: primary
created_at: '2026-11-08T11:58:59Z'
updated_at: '2026-11-09T04:34:03Z'
platforms:
- a3
---

# MiMo-V2.5-Pro 的 MXFP4 与 DFlash PD 参考配置

## 适用边界

来源给出MiMo-V2.5-Pro-FP4-DFlash的PD参考脚本，checkpoint为MXFP4，draft位于权重的`dflash/`子目录。页面明确给出 A3 每卡双die的部署背景，并冻结脚本与镜像 `quay.io/ascend/sglang:v0.5.18-cann9.0.0-a3`，要求使用完全相同版本，后续版本不在覆盖范围。平台据此限定A3，仍保持draft与本次未复测边界；`device_urma`与TP8不能单独证明950或其他Ascend产品支持。页面没有性能数值或独立重复信息。

## 配置契约

1P1D两个节点均TP8/DP2并启用DP attention/DP LM head、ascend attention和SWA/full ratio0.3。P是DeepEP normal、chunk8192、prefill graph disabled，long-seq dispatch为10轮×4096且combine long-seq关闭；D是low_latency、DFLASH、8 draft tokens和decode graph1/2/4/8/12/16。

D端开启overlap plan stream隐藏draft/target准备，并用`SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1`容许draft声明的更长context；该开关不证明任意长请求安全或增加目标模型能力。P/D静态比例0.90/0.88以及buffer2500/1200均是配方值，须核对HBM后调整。

KV传输用ascend后端、MemFabric store指向P、协议device_urma。来源worker为10001/20001、bootstrap8996、router6688；router示例没有显式传bootstrap端口，部署前须核对路由器版本与实际bootstrap参数，不假设默认8998可通。

## 测量方法

来源提供RANDOM输入16000，output1测TTFT、output1000测TPOT，均128请求/并发32，前者rate0.4、后者inf，并启用tokenize-prompt。它们是待执行命令，页面没有数值结果。验收需记录实际精度、draft加载与接受长度，再测正确性、延迟和峰值内存；本次未执行上游代码。

## Evidence

- [sglang：docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/mimo_v2_5_pro.mdx](https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/model-deployment/best-practices/mimo_v2_5_pro.mdx)（primary）

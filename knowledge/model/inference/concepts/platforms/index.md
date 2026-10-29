# 平台

- [Ascend 950 (950PR / 950DT)机制](ascend_950.md)：Ascend 950（950PR/950DT）是 cann-recipes-infer 面向新代际昇腾的部署平台，DeepSeek-V4、HunyuanVideo 和 Pangu-7B 等已有适配。相较 A3，其 V4 路径支持 FP8/MXFP4，并可用 Histograms 加速 LI 精确 Top-k；在 S_k=16384、k=512、uint32 条件下理论约 7296 cycle，对比 A3 排序路径约 28375 cycle。SAS 在 950 使用含反量化的五阶段伪量化流水，Tiling 可取 256³ 基本块，weightNZ 则关闭。950PR 偏 Prefill、950DT 偏 Decode，但配置统一使用 platform_version="950"，代码未区分两者；950 的 CV 核比和 L0 容量字节数仍缺直接证据。
- [Atlas A3](atlas_a3.md)：Atlas A3 是昇腾训练与推理产品系列之一。本页汇总知识库中明确声明适用于 A3 的模型实践；是否支持 A3 仍以各模型卡及其固定来源为准，不能由仓库归属统一推断。

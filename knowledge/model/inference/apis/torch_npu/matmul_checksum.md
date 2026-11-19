---
type: API
title: matmul_checksum：布尔异常标记、写回与主线ABFT路径
description: 区分文档dtype范围、旧校验的结果修改和主线一次探测，不把False当硬件无故障证明；并给出 aten 内部 _npu_matmul_abft_verify
  的主线独有包装合同：packed字节输出与FP32-c硬约束。
tags:
- task.lookup
- topic.model_serving
- topic.memory
- topic.precision
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-matmul_checksum.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-matmul_checksum.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-matmul_checksum.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-matmul_checksum.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/asd/checksum.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/asd/checksum.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/_exports.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulAbftVerifyKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-10T03:38:40Z'
updated_at: '2026-11-14T08:44:18Z'
platforms:
- a2
- '950'
aliases:
- torch_npu.matmul_checksum
- AI Core 矩阵乘硬件检测
---

# matmul_checksum：布尔异常标记、写回与主线ABFT路径

## 固定版本与复核边界

文档为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda各自收录页；发布对应ascend_26_0_pt28。实现分别为TorchNPU发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b和独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf，不把独立main当已配套发行。

产品逐接口/版本限定；950条目如仅DT便不扩PR，旧Atlas不自动映射新型号。静态阅读不表示已调用设备、图捕获、回调、文件解析或性能验证；stable不表示运行verified。本次没有执行上游或加载任何模型、检查点和dump数据。


## 输入和返回

matmul_checksum(a,b,c)以原生matmul输入a/b及已有输出c检查AI Core计算异常，返回NPU BOOL标量，True为检出异常。不是matmul输出，也不能据False证明任意硬件/数值路径都无故障。英文功能段“raises an error”不改变这里BOOL返回合同。

发布文档只NPU BF16，产品A2训练及旧Atlas训练；主线增加950DT，并仅CANN>=9.2且a/b/c均2D时文档允许BF16/FP32，其余仍BF16。未确认A3或950PR。独立TorchNPU main的Python类型检查更宽地接受BF16/FP32，不能据此取消文档的CANN/rank条件或把两main当配套。

## 发布与主线回退会修改c

旧算法以FP32求c行和及a乘b行和，按c最大值/均值比选择估计门限：比值最小值>5时按max*2^-8*sqrt(n)，否则mean*2^-8*n，再比较误差。结果初判异常时实际执行matmul(a,b,out=c)，重新比较行均值；c会被写回，不是纯读取诊断。

main保留该Python回退，门限仍含旧精度常数，不将更宽dtype校验当FP32门限已充分校准或任意shape安全。依赖c原始数据进行故障复盘时，应先明确这条副作用与对照需求；本次没有做故障注入或数值实验。

## 主线ABFT分支及缓存

ABFT要求a/b/c均非退化2D、a/b同BF16或FP32、c为a同dtype或FP32且矩阵shape匹配，随后还需实际私有_npu_matmul_abft_verify可用。可用性用一次小矩阵调用探测，RuntimeError/AttributeError/TypeError失败缓存False；代码没有简单按CANN字符串直接保证可用。

ABFT输入连续化、c转FP32，e_max为BF16 .001、FP32 .00002。行校验按每字节8行、低位在先，置1表示正确，尾部无效位须mask掉；ones及mask缓存到64项后清空。ABFT分支只返回异常flag，没有这里旧算法的out=c重算，但转换/探测/缓存同样有成本。主线私有算子符号与具体Runtime能力须在真实配套环境核验，不能用静态源码证明已走优化路径。

## 已有 OpPlugin 7.3.0 文档与版本边界

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 矩阵乘 AI Core 硬件校验：torch_npu.matmul_checksum

### 用途与语义

对 matmul 的计算过程进行校验，用于定位 AI Core 硬件故障；校验通过不代表整网数值精度通过。

### 输入、输出与行为

该接口基于 `torch.matmul` 和 `Tensor.matmul` 做 AI Core 硬件故障检测。校验误差超过实时门限时，按该检测机制判定 AI Core 错误；这与整网精度容差不是同一判据。

### 文档签名

```text
torch_npu.matmul_checksum(a, b, c) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-matmul_checksum.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-matmul_checksum.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-matmul_checksum.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-matmul_checksum.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/asd/checksum.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/asd/checksum.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/core/_exports.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation）

## aten内部_npu_matmul_abft_verify：主线独有的包装合同（增补）

上文ABFT分支消费的私有aten入口在OpPlugin主线有独立包装文件；发布快照零登记、零文件（yaml与`op_plugin/ops/`全树rg负向核实）。主线yaml登记`_npu_matmul_abft_verify(Tensor a, Tensor b, Tensor c, Tensor checksum_weight, *, float e_max=0.001) -> Tensor`仅`op_api: all_version`（7596–7597行）——无acl_op条目，包装体也没有DO_COMPATIBILITY回退，直接单次`EXEC_NPU_CMD(aclnnMatmulAbftVerify, a, b, c, checksum_weight, e_max, comp_row)`；aclnn符号缺失时的行为由EXEC/分发层决定，不在本卡来源内。

| 实际门槛→动作（包装层TORCH_CHECK，全部host侧） | 失败/版本边界 |
| --- | --- |
| 形状：a/b/c均2D、checksum_weight 1D；a.size(1)==b.size(0)（K对齐）；c=[M,N]由a/b推导；checksum_weight=[N] | 报错原文如“a must be a 2D tensor, but got ...D.”“c must have shape [M, N] = ...”“checksum_weight must have shape [N] = ...”（PARAM） |
| dtype：c必须Float32；a/b/checksum_weight三者同dtype且∈{Half,BFloat16,Float}；e_max>=0 | c的FP32是包装层硬拒（TYPE）：上文Python消费面预检允许“c为a同dtype或FP32”，但消费代码随后把c转FP32再调用，包装只见到FP32——直连调用者传非FP32的c在本层报错；a/b的FP16允许面比Python消费路径（BF16/FP32）宽，是否被任何消费面实际用到未在来源中确认 |
| 布局：四输入均contiguous且FormatHelper::IsBaseFormatType（ND base格式） | 非连续/非base格式在本层拒绝（PARAM）；FormatHelper内部不在本卡来源内；上文消费面的“输入连续化”与该约束对应 |
| 输出：comp_row一维UInt8，长度=ceil(M/8)*ceil(N/256)（文件常量ROW_PACK=8、SPLIT_N=256；源注释自述“8 row-segment verdicts packed per byte”“column split granularity”），`apply_tensor_without_format`申请 | 上文消费面“每字节8行、低位在先”的解包在包装层得到每字节8行的对应；N/256列分段维度是包装层新增事实；“低位在先”“置1表示正确”与尾部mask是消费侧解释，包装层不解释位含义，两者互不推导 |

e_max缺省0.001（yaml登记值）；上文消费面对BF16用.001、FP32用.00002，是消费侧选择而非包装约束。本节静态口径：aclnnMatmulAbftVerify内核语义、位编码细则与非950 SoC可用性不在本卡来源内；该主线专有文件（2026版权头）不外推到发布栈，发布环境沿上文Python回退/探测合同评估。

### _npu_matmul_abft_verify 增补证据

- [MatmulAbftVerifyKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MatmulAbftVerifyKernelNpuOpApi.cpp)（implementation）：1–94；完整本地小文件，主线专有（发布树无此文件，负向核实）。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：7596–7597；_npu_matmul_abft_verify条目完整字段；发布yaml同名rg零命中。

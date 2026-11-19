---
type: API
title: 分组矩阵乘后 AlltoAllv 融合（torch_npu.npu_gmm_alltoallv）
description: torch_npu.npu_gmm_alltoallv：分组矩阵乘后 AlltoAllv 融合。MoE网络中，执行路由专家GroupedMatMul、AlltoAllv融合并执行与共享专家MatMul并行融合，先计算后通信。 区分专家端输入行数与回传输出行数，说明共享专家、计数和图通信模式约束。
tags:
- task.lookup
- topic.parallelism
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_gmm_alltoallv.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gmm_alltoallv.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GmmAllToAllvNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_allto_allv.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_gmm_alltoallv.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gmm_alltoallv.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_gmm_alltoallv.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GmmAllToAllvNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_gmm_alltoallv.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_allto_allv.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
created_at: '2026-11-10T03:38:43Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a3
- '950'
aliases:
- torch_npu.npu_gmm_alltoallv
---


# npu_gmm_alltoallv：专家矩阵乘、反重排与路由回传

## 版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 完整产品页、Schema、Meta和C++包装，另审阅TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` Converter。产品仅A3与950DT，限推理、单算子和TorchAir图模式；不扩展A2、950PR或训练反向。两主线来源的组合仍需独立配套核对，未获得设备运行验证。

## 输入、专家与计数

路由输入为FP16/BF16二维ND，gmm_weight为同dtype三维[e,H1,N1]；trans_gmm_weight=True时按实际转置存储[e,N1,H1]解释，输出列由weight第1轴取得，否则取第2轴。共享专家mm_x/mm_weight需同时提供，形状[BS,H2]与[H2,N2]，trans_mm_weight独立控制共享权重转置，不能混用两个转置开关。

send_counts/recv_counts是Host Python整数list，每项表示对应发送/接收token数，列表长度e*ep_world_size≤256；此256是专家×rank条目规模限制，不能误当BSK总token上限。设备send_counts_tensor/recv_counts_tensor虽在签名、包装和Converter中存在，产品页明确当前不支持，均保持None。不能传Tensor就认为实现了动态计数无Host同步。

A3的EP size仅8/16/32/64/128，950DT为2/4/8/16/32/64/128/256；仍需e≤32且e*EP≤256。hcom长度1..127；H1/N1/N2∈(0,65536)，H2∈(0,12288]，topK∈[2,8]，BSK∈(0,52428800)。这些约束不构成单个样例可外推到所有专家负载的证明。

## 通信引擎与版本分支

A3列None/ai_cpu，950DT另可ccu，None使用AI CPU。A3页面还称“传任意值都使用AI CPU”，但主线TorchAir Converter明确拒绝非None且非ai_cpu的值；图模式采用共同明确的None/ai_cpu，不能将该句推广成ccu可用。

C++ comm_mode=None调用旧aclnn入口，显式值则检查并调用V2；缺V2不会回退。显式ai_cpu与None可能有不同软件依赖，即使通信意图相同。950DT CCU限单机UB域、AI CPU可跨机UB域；CCU单次通信量≤256M，总量≤16*256MB，实际shape可能更严。A3要求单卡通信量≥2MB，950DT未给这项最小量约束，不代表没有其他容量限制。

## 接口与先计算后通信

```text
torch_npu.npu_gmm_alltoallv(gmm_x, gmm_weight, hcom, ep_world_size, send_counts, recv_counts, *, send_counts_tensor=None, recv_counts_tensor=None, mm_x=None, mm_weight=None, trans_gmm_weight=False, trans_mm_weight=False, comm_mode=None) -> (Tensor, Tensor)
```

gmm_x=[A,H1]，本方向A=sum(send_counts)。先按专家执行GMM，再Unpermute回通信需要的顺序并AlltoAllv；最终y=[BSK,N1]，BSK=sum(recv_counts)。C++和Meta都按recv_counts总和分配最终行数，不能把前一接口的“BSK是发送量”直接沿用到本接口。

共享专家mm_y=[BS,N2]只在mm_x/mm_weight同时存在时计算；本接口不返回路由GMM的中间结果或Unpermute结果，也不执行最终topK加权还原。要把返回token还原成模型输出，仍需按模型路由索引和权重完成后续步骤，不能只依据返回shape认定MoE combine已完成。

两个接口在完整MoE流程中可分担专家前后通信，但实际send/recv列表、分段、权重和专家序号随数据流确定，不能默认使用同一对列表就构成彼此逆变换。跨rank总token守恒并不保证本卡输出token顺序正确。

无共享输入时Meta返回第二项None，C++返回未定义Tensor占位；只传mm_x时Meta会继续访问mm_weight，不能依赖C++分配条件来保证该不完整组合可入图。共同有效路径为两项同时提供或同时None。

- [先通信后专家计算](npu_alltoallv_gmm.md)

## 核验

同时检查输入行数与本方向send/recv计数总和、真实专家分段和rank对应顺序；全域总发送量等于总接收量只是必要条件，不能替代各通信对与各专家段匹配。以分步通信、重排、GMM和共享MM参考验证每个返回项，再测同负载稳态性能。Converter将Host计数列表继续传给GE节点，计数变化是否重编译或重新匹配须检查实际图产物，不能仅因dynamic=True就视为已动态化。

本次仅静态审阅，未运行上游代码、多卡、NPU、数值或性能测试；底层融合有共享专家分支不等于实测证明计算通信已经充分重叠。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 发布计数文字与产品差异

发布中文页仅列A3推理、单算子和图模式，没有950或comm_mode；四层发布签名也都缺少该关键字。主线中文列950DT至256卡，英文仅列至64；两个薄包装和Meta不做完整卡数校验，保留两种文本而不把未报错当作256卡支持证据。中文的CCU单次256M、总量16*256MB也不因英文省略而失效。

发布页把send_counts/recv_counts长度写成ep_world_size、条目写成e*ep_world_size，与主线说明及示例按每专家每rank展开的e*ep_world_size条目不一致。共同调用采用完整扁平计数列表，并按当前回传方向分别匹配输入发送量与最终接收量；不能把该文字错误变成仅按rank的设备计数方案。两张发布公式只表达GMM→Unpermute→AlltoAllv及共享MM。

主线显式comm_mode需要V2与相应GetWorkspaceSize两个符号；None走旧入口。发布没有该形参，转换器存在不等于已支持主线的显式通信控制。

## 回传参考测试为什么不能作为黄金结果

两版测试仅空白/EOF不同，名义配置A3/950八卡FP16均衡路由，但子入口在gmmX赋值前读取它，又误调用返回三项的npu_alltoallv_gmm并只接两项；黄金函数仍有未定义gmmX与torch.tenser。返回参考只取gmmYGolden[0]的一行，主输出也没有真正逐项比较。未选中的非均衡分支还有np.random.multinominal拼写错误。

这些是固定文件的静态缺口，不能据测试装饰器或函数名称认定回传、非均衡路由、共享MM、转置、BF16或图模式已经验收。文档两种示例也没有独立准确性或性能测量。未执行上游测试。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 分组矩阵乘后 AlltoAllv 融合：torch_npu.npu_gmm_alltoallv

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

MoE网络中，执行路由专家GroupedMatMul、AlltoAllv融合并执行与共享专家MatMul并行融合，先计算后通信。

### 文档签名

```text
torch_npu.npu_gmm_alltoallv(gmm_x, gmm_weight, hcom, ep_world_size, send_counts, recv_counts, *, send_counts_tensor=None, recv_counts_tensor=None, mm_x=None, mm_weight=None, trans_gmm_weight=False, trans_mm_weight=False) -> (Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_gmm_alltoallv.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gmm_alltoallv.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/GmmAllToAllvNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_allto_allv.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_gmm_alltoallv.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_gmm_alltoallv.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_gmm_alltoallv.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/GmmAllToAllvNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_gmm_alltoallv.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul_allto_allv.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）

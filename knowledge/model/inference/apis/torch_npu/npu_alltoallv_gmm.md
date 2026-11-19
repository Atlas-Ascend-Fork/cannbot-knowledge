---
type: API
title: AlltoAllv 后分组矩阵乘融合（torch_npu.npu_alltoallv_gmm）
description: torch_npu.npu_alltoallv_gmm：AlltoAllv 后分组矩阵乘融合。MoE（Mixture of Experts，混合专家模型）网络中，执行路由专家AlltoAllv、Permute、GroupedMatMul融合并执行与共享专家MatMul并行融合，先通信后计算。 记录接收 token 输出、Host 计数、共享专家配对和 Permute 可选输出。
tags:
- task.lookup
- topic.parallelism
- topic.mixture_of_experts
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_alltoallv_gmm.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_alltoallv_gmm.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllToAllvGmmNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_allv_grouped_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_alltoallv_gmm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_alltoallv_gmm.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_alltoallv_gmm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllToAllvGmmNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_alltoallv_gmm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_allv_grouped_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
created_at: '2026-11-10T03:38:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a3
- '950'
aliases:
- torch_npu.npu_alltoallv_gmm
---


# npu_alltoallv_gmm：路由接收、重排与专家矩阵乘

## 版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 完整产品页、Schema、Meta和C++包装，另审阅TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` Converter。产品仅A3与950DT，限推理、单算子和TorchAir图模式；不扩展A2、950PR或训练反向。两主线来源的组合仍需独立配套核对，未获得设备运行验证。

## 输入、专家与计数

路由输入为FP16/BF16二维ND，gmm_weight为同dtype三维[e,H1,N1]；trans_gmm_weight=True时按实际转置存储[e,N1,H1]解释，输出列由weight第1轴取得，否则取第2轴。共享专家mm_x/mm_weight需同时提供，形状[BS,H2]与[H2,N2]，trans_mm_weight独立控制共享权重转置，不能混用两个转置开关。

send_counts/recv_counts是Host Python整数list，每项表示对应发送/接收token数，列表长度e*ep_world_size≤256；此256是专家×rank条目规模限制，不能误当BSK总token上限。设备send_counts_tensor/recv_counts_tensor虽在签名、包装和Converter中存在，产品页明确当前不支持，均保持None。不能传Tensor就认为实现了动态计数无Host同步。

A3的EP size仅8/16/32/64/128，950DT为2/4/8/16/32/64/128/256；仍需e≤32且e*EP≤256。hcom长度1..127；H1/N1/N2∈(0,65536)，H2∈(0,12288]，topK∈[2,8]，BSK∈(0,52428800)。这些约束不构成单个样例可外推到所有专家负载的证明。

## 通信引擎与版本分支

A3列None/ai_cpu，950DT另可ccu，None使用AI CPU。A3页面还称“传任意值都使用AI CPU”，但主线TorchAir Converter明确拒绝非None且非ai_cpu的值；图模式采用共同明确的None/ai_cpu，不能将该句推广成ccu可用。

C++ comm_mode=None调用旧aclnn入口，显式值则检查并调用V2；缺V2不会回退。显式ai_cpu与None可能有不同软件依赖，即使通信意图相同。950DT CCU限单机UB域、AI CPU可跨机UB域；CCU单次通信量≤256M，总量≤16*256MB，实际shape可能更严。A3要求单卡通信量≥2MB，950DT未给这项最小量约束，不代表没有其他容量限制。

## 接口与先通信后计算

```text
torch_npu.npu_alltoallv_gmm(gmm_x, gmm_weight, hcom, ep_world_size, send_counts, recv_counts, *, send_counts_tensor=None, recv_counts_tensor=None, mm_x=None, mm_weight=None, trans_gmm_weight=False, trans_mm_weight=False, permute_out_flag=False, comm_mode=None) -> (Tensor, Tensor, Tensor)
```

gmm_x=[BSK,H1]，BSK=sum(send_counts)，先AlltoAllv再按本卡专家重排成连续分段，随后GMM。令A=sum(recv_counts)，路由输出gmm_y=[A,N1]；共享输出mm_y=[BS,N2]独立计算。两类token数通常不同，不能使用输入行数代替接收后输出行数。

permute_out_flag=True时第三项为[A,H1]，它是AlltoAllv之后、GMM之前的Permute结果，不是最终专家输出。False只取消额外返回，不跳过内部必需的重排。未融合共享专家时mm_y无有效结果，不能拿路由输出代替。

Meta把未提供共享输入的mm_y、关闭的permute_out设为None；C++对应输出为未定义Tensor占位，Schema仍列三个Tensor。关闭项应按实际运行返回协议处理，不能假定一定为0元素Tensor并读取shape。Meta只要mm_x不None就访问mm_weight，而C++仅两者都存在才分配共享输出；因此必须配对提供，不能只传一项来禁用共享分支。

- [先计算后回传](npu_gmm_alltoallv.md)：输入/输出计数方向不同。

## 核验

同时检查输入行数与本方向send/recv计数总和、真实专家分段和rank对应顺序；全域总发送量等于总接收量只是必要条件，不能替代各通信对与各专家段匹配。以分步通信、重排、GMM和共享MM参考验证每个返回项，再测同负载稳态性能。Converter将Host计数列表继续传给GE节点，计数变化是否重编译或重新匹配须检查实际图产物，不能仅因dynamic=True就视为已动态化。

本次仅静态审阅，未运行上游代码、多卡、NPU、数值或性能测试；底层融合有共享专家分支不等于实测证明计算通信已经充分重叠。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 发布范围与双语通信规模

OpPlugin发布快照dedc316708372c9a8bfde4527abd2a94b74840f5的中文页仅声明A3推理、单算子和图模式；其C++、Schema、Meta与对应TorchAir发布转换器都没有comm_mode形参。主线增加的950DT与显式模式不回推发布，950PR始终没有该页产品声明。

主线中文列950DT的EP为2/4/8/16/32/64/128/256，英文仅列至64；这是固定来源间的缺口。两个浮点薄包装与Meta没有完整校验卡数、计数、专家规模或通信容量，不能据“未拒绝256”消除该差异。中文另给CCU单次256M及总量16*256MB，英文未列不等于解除限制。两张发布公式分别表达AlltoAllv→Permute→GMM和共享MM，不包含最终topK归并或自动训练反向。

主线显式模式的符号检查同时要求V2执行入口及对应GetWorkspaceSize存在；错误提示升级CANN没有给出可据此推出的最低精确版本。None使用旧入口，缺少某个V2符号时显式模式不会自动退回None路径。

## 参考代码缺口与验收边界

两版测试仅空白与末尾换行不同，配置A3/950八卡、FP16、均衡路由、e=32、共享分支关闭及permute_out=True；实际黄金计算含torch.tenser拼写错误，不能作为可运行证明。未启用的真实转置分支还使用错误的三参数Tensor.transpose形式。测试没有覆盖BF16、非均衡、共享MM、关闭第三项、图或V2。

文档示例只打印均匀八卡FP16结果，图样例dynamic=False，没有数值断言或吞吐证据。计数必须按rank与专家匹配；只检查总发送等于总接收仍不足。本次仅静态审阅，未运行这些设备或分布式代码。

## 已有 OpPlugin 7.3.0 文档与版本边界

### AlltoAllv 后分组矩阵乘融合：torch_npu.npu_alltoallv_gmm

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

MoE（Mixture of Experts，混合专家模型）网络中，执行路由专家AlltoAllv、Permute、GroupedMatMul融合并执行与共享专家MatMul并行融合，先通信后计算。

### 文档签名

```text
torch_npu.npu_alltoallv_gmm(gmm_x, gmm_weight, hcom, ep_world_size, send_counts, recv_counts, *, send_counts_tensor=None, recv_counts_tensor=None, mm_x=None, mm_weight=None, trans_gmm_weight=False, trans_mm_weight=False, permute_out_flag=False) -> (Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_alltoallv_gmm.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_alltoallv_gmm.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AllToAllvGmmNpuOpApi.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_allv_grouped_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_alltoallv_gmm.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_alltoallv_gmm.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_alltoallv_gmm.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AllToAllvGmmNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_alltoallv_gmm.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/allto_allv_grouped_matmul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）

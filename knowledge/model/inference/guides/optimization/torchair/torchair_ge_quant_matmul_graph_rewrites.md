---
type: Guide
title: GE量化矩阵乘改图：View、NZ与转置归一
description: 区分GroupedMatmul主线view/NZ检查和两版graph_pass量化转置路线，保留架构、scale、消费者与输入位置条件。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/grouped_matmul_pass.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/graph_pass.py
  role: implementation
created_at: '2026-11-10T10:53:20Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE量化矩阵乘改图：View、NZ与转置归一

## 固定版本与范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的grouped_matmul_pass.py，以及该主线与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的graph_pass.py。发布没有同一grouped_matmul_pass.py路径，仅记路径事实，不否定其他入口。本文限定GE图重写和校验，不替代GroupedMatmul、量化类型或NZ的kernel支持矩阵；产品范围未知，保持draft与空平台，未运行上游或设备实验。

## 从view缓存找路径，不是任意Transpose消除

主线normalize_grouped_matmul_view从view_operator_map中只收集key为(源GE Tensor,torch.Tensor Meta)、value为GE Tensor的项。_find_view_path最多回溯12层，只通过Bitcast/Cast/Reshape/Transpose/TransposeD的第0输入找已记录view；_bypass_view改写路径最靠近view的消费者输入，保留中间其他处理，不能概括为删除全部Cast或Transpose。

末两轴转置要求Meta秩>=2、stride[-2]=1、stride[-1]=size[-2]，批维连续，且末两维不全为1；单位轴变体还要求其中一维为1。packed scale检查末3轴stride及批维连续，per_token_scale只识别2D普通或3D packed形式。

只处理x和weight首个描述符同属HIFLOAT8/E5M2/E4M3FN集合，或同属两种FP4集合的GroupedMatmul。FP8的group_type=2且只有一个x输入、该x为单位轴转置时旁路view，按条件处理首个per_token_scale，再写transpose_x=True并结束这个节点的后续归一；不是所有split-K都转同一路线。

权重/scale归一要求group_type为-1或0，所有相关输入都能回溯到view。FP4允许“每个权重末维为1的单位轴转置”或“group_list_type=1且动态权重转置、scale布局匹配”；其他FP8只取后一条件。权重和scale分别旁路后写transpose_weight=True。

FP4精确路径GroupedMatmul→Transpose→Reshape→Bitcast→Transpose会额外改Bitcast及GMM输入，并把相关Shape输入重定向到源Tensor；不匹配该链时走普通旁路。这里没有直接删除所有失去消费者的节点，也不认证任意共享节点都安全。

## NZ检查只看特定入口和架构分支

validate_grouped_matmul_weight_nz只在存在GroupedMatmul且is_arch35()为真时检查。它从weight0沿Bitcast/Identity/Reshape/TensorMove/Transpose/TransposeD第0输入回到Data/RefData，带循环和控制边终止条件；这份祖先名单没有Cast，不能与前述view回溯名单混用。

仅当该祖先output_desc[0].attr['format_for_int']等于FRACTAL_NZ才应用限制：group_type=2拒绝；x0和weight0各须在INT8、E4M3FN、两种FP4、FP16、BF16集合。若两者均E4M3FN，或两者各为FP4集合成员，则per_token_scale与scale0必须均E8M0，缺字段取Undefined也不满足。

此函数没有对所有weight列表项逐一追祖先，没有把dtype名单变成完整算子配套表；normalize_grouped_matmul_view自身也没有同一is_arch35门槛。通过检查不等于真实NZ布局、数值和设备执行已验证。

## graph_pass中的量化转置重写：主线与发布分开

两版move_transpose_into_mm都按精确节点类型和固定输入位置匹配Bitcast→Transpose→Const，再把Transpose语义移入矩阵乘属性；发布GMM只有权重与antiquant scale配对，QuantBatchMatmulV4只有两路Bitcast配对。

主线新增非arch35 A4W4分支，以x上游节点和weight Bitcast的input_desc[0].dtype均INT32识别；权重置换必须确为末两轴交换、Transpose只有一个消费者，scale满足时一并处理。共享permutation Const仅无消费者时删除。这个更强检查没有自动覆盖下面所有通用分支。

主线通用GMM另支持scale输入3配对，两个通用条件是独立if；不能当成互斥分支或有统一共享节点保护。QuantBatchMatmulV4新增输入4直接Transpose+Const路线，注释称二维scale，但该匹配处没有独立检查秩为2；另一路is_scalar_scale最多回溯8层到Data，只检查shape秩为1，一维不等于单元素。

主线还有GroupedMatmulFinalizeRouting的transpose_w、GroupedMatmulSwigluQuantV2权重/scale双模式匹配。后者两路都匹配才删除对应Reshape/Transpose/Const并写transpose_weight；没有所有消费者/置换条件的统一验证，需核对共享节点与精确输入位置。

主线move_mm_weight_transpose_after_bitcast对QuantBatchMatmulV3把Bitcast→Transpose改接为Transpose→Bitcast的输入关系，保留Transpose节点，不能描述成转置已消除。发布没有同一函数。

## 验证

核对精确快照、proto dtype、输入描述符名字/位置、view缓存、shape/stride、量化scale、祖先NZ标志与消费者；保存改图前后边和属性，再验证数值、存储及性能。本次只读实现，未执行任何重写或真机测试。

- [GE View物化与mapsym](torchair_ge_view_materialization.md)
- [GE矩阵乘Converter](torchair_ge_matmul_lowering.md)
- [GE输入重写](torchair_ge_input_rewrites.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/grouped_matmul_pass.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/graph_pass.py)（implementation）

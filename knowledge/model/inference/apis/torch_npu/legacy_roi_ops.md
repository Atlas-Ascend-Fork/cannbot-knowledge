---
type: API
title: 旧ROI算子：PS池化布局与ROIAlign参数缺省冲突
description: 区分物理NC1HWC0、五列ROI与原生模块的显式转换，不把临时cast当实际计算；另含交叉命名的 RoiAlign 文件（opapi
  反向名文件承载前向、aclops 反向名文件承载 roi_alignbk）。
tags:
- task.lookup
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_ps_roi_pooling.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_ps_roi_pooling.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_ps_roi_pooling.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_roi_align.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_roi_align.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_roi_align.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PsRoiPoolingKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PsRoiPoolingKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RoiAlignKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RoiAlignKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RoiAlignKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RoiAlignKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RoiAlignBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RoiAlignBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RoiAlignBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RoiAlignBackwardKernelNpu.cpp
  role: implementation
created_at: '2026-11-09T20:42:31Z'
updated_at: '2026-11-14T01:59:28Z'
platforms:
- a2
- a3
---

# 旧ROI算子：PS池化布局与ROIAlign参数缺省冲突

## 固定版本与产品边界

依据OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5中文、独立主线d84e9b1d6a558e5f27973cd4329f62968e46fdda中英文及各自实现。发布归ascend_26_0_pt28，main不是与其他仓main自动配套的发行。

平台只按实际产品页；950新增项严格另列主线PR/DT，旧Atlas不自动映射新型号。计划废弃、不维护、schema注册及实际运行能力分别判断；stable不表示推荐新模型采用或运行verified。这里只静态阅读，未导入上游、运行设备、反向、数值或性能实验，底层Kernel算法不由框架包装引用视为全覆盖。


## PS ROI Pooling

npu_ps_roi_pooling(x,rois,spatial_scale,group_size,output_dim)计划废弃且不维护。x为NC1HWC0，rois为(B,5,R)，每框batch_id及非负xyxy；group_size整数1..127、output_dim>0。主线补充C0是通道分块；文档C1=(int(output_dim+15)/C0)*group_size关系不是普通逻辑NCHW通道维。

两固定公开包装检查rois至少3维，返回(B*R,output_dim,group_size,group_size)。反向helper按(rois.size(0),group_size²*output_dim,H,W)分配，不能把文档一次group_size的C1表达式自行修为全逻辑shape规则；需分别核对物理/逻辑布局。模块构造还有pooled_height/width必须等于group_size的额外检查，见[contrib模块](contrib_roi_pooling_and_align.md)。

## ROIAlign

npu_roi_align(features,rois,spatial_scale,pooled_height,pooled_width,sample_num,roi_end_mode)，features为4D，输出(N,features.C,pooledH,pooledW)。发布与主线正文写rois(N,4)，主线样例实际改(N,5)含batch index，与contrib和常用ROI协议一致；不复制发布缺一列的样例。

sample_num=0为自适应采样，非0为H/W每输出元素采样频率。旧页sample_num默认2、roi_end_mode默认1；主线中文删去缺省、英文仍保留，而两版注册这两个都是必传，不能省略。页面明确相对CUDA反向有精度问题，不承诺跨设备逐位一致。

ACL Op包装虽创建self_cast/rois_cast临时FP32变量，实际调用仍传原self/rois，输出先按NC1HWC0分配，任一Half又转Half；不能据未消费临时变量声称这里始终FP32计算。contrib forward显式.float()属于另一入口。名为RoiAlignKernelNpuOpApi.cpp的文件实际定义roi_alignbk反向包装，roi_end_mode可空时取1；不能用文件名补造公开forward的默认值或执行路径。

## 交叉命名的 RoiAlign 反向/前向文件

上文 ROIAlign 节已指出文件名与内容存在交叉；本节补齐另两个相关文件（均两 pin 语义等价，全文读毕）。`RoiAlignBackwardKernelNpuOpApi.cpp`（35 行）虽以 Backward 命名，实际定义**前向 `npu_roi_align`**：TORCH_CHECK `rois.dim()>=1`、`self.dim()>=2`；输出 `{rois.size(0), self.size(1), pooled_height, pooled_width}` 以 `apply_tensor_without_format` 分配；`spatial_scale` double 显式转 float 后 `EXEC_NPU_CMD(aclnnROIAlign, ...)`，`DO_COMPATIBILITY` 回退 `acl_op::npu_roi_align`。`RoiAlignBackwardKernelNpu.cpp`（77 行，aclops）定义**反向 `npu_roi_alignbk`**：发 ACE `ROIAlignGrad`，xdiff 按 self 形状以 `ACL_FORMAT_NC1HWC0` 请求（`apply_tensor_with_format`）。消费面：torch_npu 发布 pin `contrib/module/roi_align.py` 的 `grad_input = torch_npu.npu_roi_alignbk(...)`。两命令设备侧语义与 NC1HWC0 转换成本未核验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_ps_roi_pooling.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_ps_roi_pooling.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_ps_roi_pooling.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_roi_align.md)（primary）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/（beta）torch_npu-npu_roi_align.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/(beta)torch_npu-npu_roi_align.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PsRoiPoolingKernelNpu.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PsRoiPoolingKernelNpu.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RoiAlignKernelNpu.cpp)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RoiAlignKernelNpu.cpp)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RoiAlignKernelNpuOpApi.cpp)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RoiAlignKernelNpuOpApi.cpp)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [RoiAlignBackwardKernelNpuOpApi.cpp 两 pin](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RoiAlignBackwardKernelNpuOpApi.cpp)（implementation）：全文 35 行；发布仅排版差。
- [RoiAlignBackwardKernelNpu.cpp 两 pin](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RoiAlignBackwardKernelNpu.cpp)（implementation）：全文 77 行；发布去空白等价。

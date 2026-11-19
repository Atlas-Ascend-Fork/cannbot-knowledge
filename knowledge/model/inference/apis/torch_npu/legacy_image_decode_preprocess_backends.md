---
type: API
title: 设备侧图像解码与预处理后端：decode_jpeg等5个custom注册的门槛与host合同
description: 记录decode_jpeg、img_to_tensor、crop_and_resize、image_normalize(_)五个无文档页custom注册的输出dtype/形状推导、host检查、NormalizeV2硬编码三通道形状与v2.1单版本门，并给出与Host侧增强包装的分界。
tags:
- task.lookup
- topic.data_pipeline
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DecodeJpegKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/DecodeJpegKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ImgToTensorKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ImgToTensorKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CropAndResizeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CropAndResizeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ImageNormalizeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ImageNormalizeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/core_tests/torch_npu_OpApi_schema_all.json
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/core_tests/torch_npu_OpApi_schema_all.json
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/core_tests/test_compatibility.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/core_tests/test_compatibility.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/gen_op_plugin_functions.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/gen_op_plugin_functions.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/op_codegen_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/op_codegen_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/gencode.sh
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/gencode.sh
  role: implementation
created_at: '2026-11-12T10:34:04Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 设备侧图像解码与预处理后端：decode_jpeg等5个custom注册的门槛与host合同

## 版本与范围

本卡覆盖 OpPlugin 两固定 pin（主线 d84e9b1d6a558e5f27973cd4329f62968e46fdda、发布 dedc316708372c9a8bfde4527abd2a94b74840f5）`op_plugin_functions.yaml` custom 段的五个图像解码/预处理 schema：decode_jpeg、img_to_tensor、crop_and_resize、image_normalize(_)。四份 aclops 内核全文逐字读毕（46/35/49/86 行；发布侧两份与主线字节相同、一份空白归一等值、一份见版本边界节），共享输出尺寸 helper 与版本门证据链为定向行段读。五入口在两 pin 的 docs/zh、docs/en 全树检索均无页面，deprecated.yaml、derivatives.yaml、`op_plugin/python/meta/_meta_registrations.py` 亦零命中，两 pin 测试树无任何功能用例（唯一 normalize 命中为无关的 npu_normalize_batch）；canonical 的 model/common 域对五个名字零命中（crop_and_resize 命中仅在 ops/ascendc 设备内核卡，另一域、另一层）。本卡将这五个入口成组覆盖，不逐入口拆卡。消费方（torchvision-npu 等 Python 入口与调用顺序）不在两 pin 源内，本卡不断言任何 Python 可调用面存在；也不归属任何模型，不承诺整模型推理或预处理收益。全部为静态源码审阅，未执行任何上游或设备测试。

## 接口与注册面

```text
decode_jpeg(Tensor self, int[] image_shape, int channels=3, bool try_recover_truncated=False) -> Tensor
img_to_tensor(Tensor self) -> Tensor
crop_and_resize(Tensor self, float[]? boxes, int[] box_index, int[] crop_size, float extrapolation_value=0, str method="bilinear") -> Tensor
image_normalize(Tensor self, float[]? mean, float[]? variance, int dtype=0) -> Tensor
image_normalize_(Tensor(a!) self, float[]? mean, float[]? variance, int dtype=0) -> Tensor(a!)
```

- yaml 登记（主线 5771–5793、发布 5531–5553，五条目逐字相同）：均仅 `acl_op: v2.1`——无 op_api 路径、无 gen_opapi、无 exposed 标注；实现文件只有 aclops 四份（opapi 目录 find/rg 零命中）。
- **v2.1 是单版本门，不是"自 v2.1 起"**：按两 pin 内置生成链（`gencode.sh` 按 PyTorch 版本生成 `op_plugin/config/v2r1/…` 配置，再喂给注册码生成），`torchnpugen/gen_op_plugin_functions.py` 对每条目取 `get_version(acl_op)` 后以 `version in (acl_op_sup_ver + …)` 做成员过滤；`op_codegen_utils.py` 的 `get_version`（297–310，两 pin 字节相同）对裸字符串 `v2.1` 返回单元素列表 `['v2.1']`。因此就这条已读生成链而言，五条目只进入 PyTorch v2.1 构建的过滤后 backend config，v2.2+ 构建的过滤后 config 不含它们；下游 `torchnpugen/gen.py` 与 `gen_op_backend` 的注册生成不在已读来源内，已发布 wheel 的实际注册面未核验，不把该成员事实外推成“一切 v2.2+ 绑定必然缺席”。schema 兼容基线 `test/core_tests/torch_npu_OpApi_schema_all.json` 两 pin 同记五条 `"version": ["v2.1"]`（`test_compatibility.py` 的 test_op_func_compatibility 按当前 torch 版本过滤基线），与该读法互相印证。未执行任何构建，发布产物实际版本面未核验（静态口径）。
- 本地包装层不定义 backward、不接 derivatives；schema 文本即注册面全部输入输出声明。

## 实际门槛与动作（host 实检）

以下行号均为主线 pin（发布对应文件行号不同但逻辑等值，见版本边界节）；"未显式检查"只覆盖本地包装函数体，OpCommand 下发/框架层校验不在已读来源内，不断言其缺席。

| 入口 | 实际门槛（host 实检） | 动作 | 失败/版本边界 |
| --- | --- | --- | --- |
| decode_jpeg | 包装内无 TORCH_CHECK；输出尺寸 helper 要求 image_shape 恰 3 元（KernelNpuOutputSize.cpp 1636），channels==0 时取 {C,H,W}、否则 {channels,H,W}（1642–1646） | `apply_tensor_with_format(output_size, kByte, ACL_FORMAT_ND)` 分配 uint8 ND 输出（28–29）；单次 ACE `DecodeJpeg` 命令（32–42）：self 以 `"string"` 类型标签作为输入（33），属性 channels、ratio=1、fancy_upscaling=true、try_recover_truncated（透传）、acceptable_fraction=1.0、dct_method=""、dst_img_format="CHW" | 输出为 JPEG 解码字节（uint8、CHW 由 dst_img_format 属性与输出尺寸共同表达）；解码语义、截断恢复真实行为、ratio/dct_method 固定值的设备侧含义不在源内；`"string"` 输入标签的 ACE 层处理未核验 |
| img_to_tensor | 包装内无任何检查 | `apply_tensor(self, kFloat)` 分配同形 float32 输出（26）；单次 ACE `ImgToTensor`：Input(self)、Output(result)，无属性（28–31） | uint8→float 的数值映射（是否 /255）不在源内，不能从名字推断；输入非 uint8 时的行为未核验 |
| crop_and_resize | TORCH_CHECK boxes 必选（29，VALUE）；helper 要求 self.dim()==4 且 crop_size 恰 2 元（1624–1625） | 输出 {N=box_index.size(), C=self.size(1), H=crop_size[0], W=crop_size[1]}（1626–1631，NCHW）；`apply_tensor(self, output_size)` 沿用 self dtype（31）；单次 ACE `CropAndResizeV2`：boxes 以 {boxes->size()/4, 4} 形状 float 输入（33/38）、box_index/crop_size 以 int 输入（39–40）、属性 extrapolation_value、method、dtype=result.scalar_type()（42–44） | host 侧 `boxes->size()/4` 整除本身已读（33/38，无整除性防护），长度非 4 的倍数时下游 Input 构造对该长度失配的处理未核验；method 合法值集合不在源内；输出 dtype 恒等于 self dtype（host 层） |
| image_normalize | out_nocheck：TORCH_CHECK mean/variance 均必选（32–34，VALUE）、dtype ∈ {0,1} "output data type should be float16 or float32"（35–37，TYPE）；image_normalize_ 另要求 self ∈ {float32,float16}（74–76，TYPE） | 单次 ACE `NormalizeV2`：mean/variance 以硬编码 {1,3,1,1} 形状 float 输入（38/42–43）、属性 dtype（40–46）；functional 版按 dtype==0→float32 / else→float16 新建输出后写入（59–64）；inplace 版在本地 npu_utils::check_match(&self) 匹配检查未通过时先 format_contiguous 得副本、在副本原地执行、再 format_fresh_view 挂回 self（77–83），该匹配谓词不止连续性（Storage 描述等匹配条件见 [输出准备指南](../../guides/optimization/torch_npu/torch_npu_out_preparation_resize_and_overlap.md)） | **mean/variance 被硬编码重整为 [1,3,1,1]**：非 3 元 mean/variance 的行为在未核验的 Input 构造层，不臆断；functional 版不检查 self dtype；inplace 版结果视图挂回语义与 aclops 家族共用模式，其存储别名可观察性未运行验证 |

## 失效与版本边界

- 两 pin 等值情况逐文件如实：ImgToTensor（35 行）与 ImageNormalize（86 行）发布与主线**字节相同**（sha256 一致，主线全文读覆盖发布字节）；DecodeJpeg 发布 49 行经全文件 raw diff + 空白归一字符流相等（仅缩进/花括号/链式调用换行重排）；CropAndResize 发布 48 行 diff 中唯一非空白差异是主线具名 `std::string method_str(method)`（34/43）换成发布内联临时 `std::string(method).data()`——同一构造与传参方式，diff 级判断语义等价，未编译验证。
- 共享 helper：发布 KernelNpuOutputSize.cpp 1436–1448/1450–1465 与主线 1620–1633/1635–1649 逻辑相同（仅排版）；yaml 五条目文本逐字相同；schema JSON 五条 `["v2.1"]` 两 pin 一致；test_compatibility.py 两 pin 仅 203 行尾随空白差异；gen_op_plugin_functions.py 发布 98 行相对主线 103 行只少 dvm 特性行与一个 O_TRUNC 标志，版本过滤逻辑相同；op_codegen_utils.py 两 pin 字节相同；gencode.sh 两 pin 全文读（79/73 行），仅 newest_minor_version 16/12 之差。
- 版本门边界：v2.1 单版本门是**生成链静态事实**（gencode.sh → gen_op_plugin_functions.py → get_version + schema 基线 JSON 互证）；`torchnpugen/gen.py` 的 parse_native_yaml 与 gen_op_backend 生成的注册命名空间（aten::/npu:: 具体挂载点）不在已读来源内，本卡不断言 Python 侧命名空间；哪些实际发布轮子携带该注册未核验。
- 五入口无 derivatives 反向、无 deprecated 登记、无文档页、无仓内功能用例——这些是两 pin 的静态缺席事实；不据此断言"永不支持训练"或"已废弃"。
- 与 [contrib ROI池化与对齐](contrib_roi_pooling_and_align.md)、[旧ROI算子](legacy_roi_ops.md) 同属视觉算子/预处理注册面但无 schema 重叠，互为邻接导航；设备内核层的 crop_and_resize 优化事实见另一域的 [A3到A5 UB驻留移植决策](../../../../ops/ascendc/guides/cross_gen_migration_guide/a3_to_a5_ub_residency_is_the_port_decision.md) 与 [256除法转乘法FP32精度安全](../../../../ops/ascendc/optimizations/ol_256_divs_to_muls_fp32_precision_safe.md)，本卡不复制其设备结论。contrast：torch_npu.contrib 的 [FusedColorJitter旧接口](../../../training/apis/torch_npu/contrib_fused_color_jitter.md) 是 Host PIL/NumPy 路径，与本卡设备侧 ACE 命令分属两层，选型时不能互相替代。
- 静态口径：未运行任何用例与设备验证；无模型归属。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DecodeJpegKernelNpu.cpp)（primary，1–46 全文逐字阅读）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/DecodeJpegKernelNpu.cpp)（primary，49 行发布对应文件经全文件 raw diff 与空白归一等值复验，仅排版差异，无独立逐行读）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ImgToTensorKernelNpu.cpp)（primary，1–35 全文逐字阅读）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ImgToTensorKernelNpu.cpp)（primary，与主线字节相同（sha256 一致），主线全文读覆盖发布字节）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CropAndResizeKernelNpu.cpp)（primary，1–49 全文逐字阅读）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CropAndResizeKernelNpu.cpp)（primary，48 行发布对应文件 raw diff 复验：排版差异 + method_str 具名临时改内联临时（同一构造语义，diff 级判断），无独立逐行读）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ImageNormalizeKernelNpu.cpp)（primary，1–86 全文逐字阅读）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ImageNormalizeKernelNpu.cpp)（primary，与主线字节相同（sha256 一致），主线全文读覆盖发布字节）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation，1620–1649 crop_and_resize/decode_jpeg 输出尺寸 helper 定向读；其余 2795 行不在本卡阅读范围）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation，1436–1465 对应 helper 定向读，逻辑与主线相同）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（header，1 行 all_version 头与 5771–5793 五条目定向读）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（header，1 行 all_version 头与 5531–5553 五条目定向读）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/core_tests/torch_npu_OpApi_schema_all.json)（implementation，1270–1287 五条目定向读）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/core_tests/torch_npu_OpApi_schema_all.json)（implementation，1183–1200 五条目定向读）
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/core_tests/test_compatibility.py)（implementation，101–107 与 150–327 定向读：test_op_func_compatibility 的版本过滤逻辑）
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/core_tests/test_compatibility.py)（implementation，与主线 raw diff 仅 203 行尾随空白差异，主线读覆盖发布语义）
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/gen_op_plugin_functions.py)（implementation，1–103 全文逐字阅读）
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/gen_op_plugin_functions.py)（implementation，98 行发布对应文件 raw diff 复验：仅少 dvm 特性行与 O_TRUNC 标志，版本过滤逻辑相同）
- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/op_codegen_utils.py)（implementation，297–310 get_version 定向读）
- [固定来源 20](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/torchnpugen/op_codegen_utils.py)（implementation，与主线字节相同（sha256 一致），主线读覆盖发布字节）
- [固定来源 21](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/gencode.sh)（implementation，1–79 全文逐字阅读）
- [固定来源 22](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/gencode.sh)（implementation，1–73 全文逐字阅读）

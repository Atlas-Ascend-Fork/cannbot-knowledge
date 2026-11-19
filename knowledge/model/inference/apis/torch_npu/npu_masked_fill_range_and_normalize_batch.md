---
type: API
title: npu_masked_fill_range与npu_normalize_batch：区间掩码填充与变长batch归一化
description: 成组记录两无文档页旧入口的host检查矩阵与错误类别、文档模板维度标注缺陷、属性下发细节（normalize_type映射与epsilon=1e-5）、用例跳过状态与覆盖边界。
tags:
- task.lookup
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaskedFillRangeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/NormalizeBatchKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaskedFillRangeKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/NormalizeBatchKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/codegen/templates/_op_plugin_docs.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/codegen/templates/_op_plugin_docs.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_masked_fill_range.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_masked_fill_range.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_normalize_batch.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_normalize_batch.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_v2r2_ops/test_normalize_batch.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_v2r2_ops/test_normalize_batch.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_v1r11_ops/test_normalize_batch.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_v1r11_ops/test_normalize_batch.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/onnx/wrapper_onnx_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/onnx/wrapper_onnx_ops.py
  role: implementation
created_at: '2026-11-12T08:30:08Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npu_masked_fill_range与npu_normalize_batch：区间掩码填充与变长batch归一化

## 版本与范围

本卡覆盖 OpPlugin 两固定 pin（主线 d84e9b1d6a558e5f27973cd4329f62968e46fdda、发布 dedc316708372c9a8bfde4527abd2a94b74840f5）中两个无官方文档页的注册入口：`npu_masked_fill_range`（区间掩码填充）与 `npu_normalize_batch`（按变长 seq_len 的 batch 归一化）。两份 aclops 包装全文（57/56 行，发布侧经全文件 diff 与空白归一等值核对）、yaml 登记、codegen 文档模板与四份基线用例。两 pin 的 docs/zh、docs/en 全树检索均无页面，deprecated.yaml、derivatives.yaml、`op_plugin/python/meta/_meta_registrations.py` 均零命中。canonical 固定树内 rg：`npu_masked_fill_range` 全树零命中；`normalize_batch` 仅在[matmul 执行路径](../../../training/guides/torch_npu_matmul_execution_paths.md)以内部函数 `normalize_batch1_stride` 同名出现，与本算子无关。两个入口均为变长序列输入的预处理 glue，不归属任何模型。相邻旧接口卡只链接不重复：切片/补零见[旧切片与补零](legacy_indexing_and_padding.md)，形状变换见[旧形状变换](legacy_shape_transforms.md)——两者登记的是有文档页的废弃迁移清单项，本卡两入口不在 deprecated.yaml，不并入其迁移口径。全部为静态源码与官方用例审阅，未执行任何上游或设备测试。

## npu_masked_fill_range：区间掩码填充

```text
npu_masked_fill_range(Tensor self, Tensor start, Tensor end, Tensor value, int axis=-1) -> Tensor
```

仅 `acl_op: all_version` 注册（主线 6503–6504、发布 6225–6226，登记原文逐字相同）；无 exposed 标注。实际门槛（C++ host 实检 29–50）：

| 检查项 | 事实 | 错误类别 |
| --- | --- | --- |
| axis 范围 | `axis ∈ [-x_dim, x_dim-1]`（x_dim=self.dim()，负值 Python 风格可用）；报错文案 `axis overfloaw the range...`，`overfloaw` 拼写如此 | VALUE |
| start 形状 | `start.ndimension() == 2` 且 `start.sizes() == end.sizes()`；报错文案 `Expected noempty 2D start tensor...`（`noempty`、`start'` 拼写如此） | PARAM |
| 行数对齐 | `start.size(0) == value.size(0)`，文案 `Expected value.length equal start loop num` | VALUE |
| dtype 一致 | `self.scalar_type() == value.scalar_type()`，报错含两侧 dtype 原文 | TYPE |

动作：`apply_tensor(self)` 沿用 self 的 sizes/options 分配同形输出；start/end/value 作为设备输入（用例中 start/end 为 NPU int32，value 与 self 同 dtype）随单次旧 ACE `OpCommand("MaskedFillRange")` 下发，axis 以 int 属性传入。start/end 在本地包装无显式 dtype 白名单（int32 只是文档与用例口径）；value 没有独立 dtype 枚举检查，但第四道检查要求它与 self 同 dtype——不暗示 value 恒为 int32（用例跨 fp32/fp16/int32/int8 传与 self 同 dtype 的 value）。区间合法性（start≤end、不越界轴界）无本地拦截，由设备侧定义；apply_tensor/OpCommand 下游不在本卡来源范围，不断言全部 host/框架校验缺席。

文档模板缺陷（两 pin 相同块）：start/end 标注「shape为(num,N)的int32 **3D**张量」、value 标注「shape为(num,)的…**2D**张量」——维度称呼与括号形状自相矛盾，与本地显式检查（start 2D、start/end 同形、start.size(0)==value.size(0)）不符，以代码为准；value 一维只是文档/用例口径，不是显式本地 rank 检查，其他 rank 无支持担保。self 标注「1D (D,)、2D (N,D)或3D (N,D)」中 3D 仍写作 (N,D) 亦属笔误口径，不按文字推断合法 shape 集。

基线用例（test_base_ops/test_masked_fill_range.py，两 pin 仅一行行尾空白差异）：输入 (32,64,1688) 3D、axis=2，start (1,32) int32 取 0..31、end (1,32) 取 6..37、value (1,) 与 self 同 dtype；float32/float16/int32/int8 四组逐一对拍。CPU 金标语义：对 start 的每个 (i,j) 与 k∈[start[i,j], end[i,j])，在 dim=3/axis=2 路径写 `out[j,:,k]=value[i]`；金标函数另有 dim=1/2 与其他 axis 的分支，但没有任何用例走到，其他组合的行为不外推。用例无 skip 装饰、无 SupportedDevices 门；其测试方法名 `test_normalize_batch` 是复制残留，命名与断言内容无关。

## npu_normalize_batch：变长batch归一化

```text
npu_normalize_batch(Tensor self, Tensor seq_len, int normalize_type=0) -> Tensor
```

仅 `acl_op: all_version` 注册（主线 6712–6713、发布 6512–6513，登记原文逐字相同）；无 exposed 标注。实际门槛（C++ host 实检 24–40）：

| 检查项 | 事实 | 错误类别 |
| --- | --- | --- |
| seq_len 维度 | `seq_len.dim() == 1`，报错含实际 sizes 原文 | PARAM |
| batch 对齐 | `seq_len.size(0) == self.size(0)`；文案把两个长度直接拼接无分隔（`...seq_len length 32self num 32`），`self' num` 拼写如此 | PARAM |
| normalize_type | `∈ [0, 1]`，报错含实际值 | VALUE |

动作：`apply_tensor(self)` 分配同形输出；`normalize_type == 0 ? "per_feature" : "all_features"` 映射为字符串属性，`constexpr float EPSILON = 1e-5` 以 `epsilon` 属性随单次 ACE `OpCommand("NormalizeBatch")` 下发，seq_len 作为设备输入。文档模板（两 pin 相同块）与实现一致：self float32 (n,c,d)、seq_len int32 (n,)「每批次标准化数据量」、0=per_feature、1=all_features。

基线用例：test_base_ops 与 test_v1r11_ops 两份副本整体 `@unittest.skip("skip test_normalize_batch now")`；test_v2r1_ops/test_v2r2_ops 副本（两副本字节相同，v2r1 未另读）的源文件无 skip 装饰——CI 选择与运行状态未观察，不据无装饰推断用例当前实际执行。金标语义：type 0 逐 (batch,feature) 在 `[:seq_len[i]]` 有效步上取 mean/std 后 `(x-mean)/std`，type 1 每 batch 标量；两侧 `x_std += 1e-5` 与包装 epsilon 属性对应。shape (32,3,6)/(16,6,1000) float32、seq_len int32 取 [3,T) 随机、两种 normalize_type 各覆盖。覆盖边界：仅 float32（文档亦只声明 float32）；金标 `torch.std` 为 PyTorch 默认口径，设备侧统计公式是否有偏/无偏未验证，不作一致承诺。v1r11 副本用旧 `torch.npu_normalize_batch` 绑定调用，其余用 `torch_npu.*`。

## 失效与版本边界

- 两 pin 行为一致：yaml 登记原文逐字相同；两 cpp 全文件 raw diff 后空白归一字符流完全相等（发布仅缩进与签名/链式调用换行重排）；文档模板目标块 diff 相同；normalize_batch 四份用例两 pin 字节相同，masked_fill_range 用例仅一行行尾空白差异。
- 注册面无 derivatives 接线、无 deprecated.yaml 登记、无 Meta 注册；TorchNPU 包装层（两固定 pin 的 wrapper_onnx_ops.py，`torch_npu.npu_masked_fill_range/npu_normalize_batch = _wrapper_*`）为只定义 forward 与 symbolic 的 autograd.Function，ONNX symbolic 产出 `npu::NPUMaskedFillRange(self, start, end, value, axis_i=axis)` 与 `npu::NPUNormalizeBatch(self, seq_len, normalize_type_i=normalize_type)`，绑定存在性与导出口子由此证明，converter 侧支持与运行时反向行为不裁定。torchair 两固定 pin 对两入口无显式同名 converter/引用；名字扫描不排除通用回退或自定义图路由，不据此断言全部图模式行为缺席。
- 设备侧 MaskedFillRange/NormalizeBatch 语义（dtype 支持矩阵、start≥end 或区间越界行为、std 归一化公式细节）不在本卡固定来源范围；apply_tensor 分配路径与 OpCommand 下发链同样不在来源范围，本卡所有「未显式检查」的缺席结论只覆盖本地包装函数体。
- 静态口径：未运行任何用例；无模型归属，不承诺整模型训练或精度收益。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MaskedFillRangeKernelNpu.cpp)（primary，1–57 全文逐字阅读）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/NormalizeBatchKernelNpu.cpp)（primary，1–56 全文逐字阅读）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MaskedFillRangeKernelNpu.cpp)（primary，68 行发布对应文件经全文件 raw diff 与空白归一与主线等值，仅缩进/换行重排）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/NormalizeBatchKernelNpu.cpp)（primary，59 行发布对应文件同上复验）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（header，6503–6504 与 6712–6713 两 schema 登记定向读）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（header，6225–6226 与 6512–6513 同两 schema 定向读）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/codegen/templates/_op_plugin_docs.py)（primary，2906–2938 与 3252–3281 两个文档模板块定向读）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/codegen/templates/_op_plugin_docs.py)（implementation，2792–2824 与 3138–3167 对应块与主线 diff 相同复验）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_masked_fill_range.py)（example，1–79 全文逐字阅读）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_masked_fill_range.py)（example，与主线仅第 11 行行尾空白差异，全文件 diff 复验）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_normalize_batch.py)（example，1–63 全文逐字阅读）
- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_normalize_batch.py)（example，与主线字节相同（sha256 一致），主线全文读覆盖发布字节）
- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_v2r2_ops/test_normalize_batch.py)（example，1–61 全文逐字阅读，无 skip 装饰副本；运行状态未观察）
- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_v2r2_ops/test_normalize_batch.py)（example，与主线字节相同（sha256 一致）；test_v2r1_ops 副本与 v2r2 字节相同，未另读）
- [固定来源 15](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_v1r11_ops/test_normalize_batch.py)（example，1–77 全文逐字阅读，带 skip 的旧绑定副本）
- [固定来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_v1r11_ops/test_normalize_batch.py)（example，与主线字节相同（sha256 一致））
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/onnx/wrapper_onnx_ops.py)（implementation，368–382/455–505/1115–1180/1320–1336 绑定与 ONNX 包装定向读）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/onnx/wrapper_onnx_ops.py)（implementation，对应区段与主线 diff 相同复验；test_public_bindings.py 两名均在两 pin 列表中，绑定存在性证据）

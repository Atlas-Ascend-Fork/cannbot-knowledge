---
{
  "type": "Runbook",
  "title": "Qwen3.5 导出报 PadV3 non-negative padding 的根因定位",
  "description": "Qwen3.5 导出报 PadV3 non-negative padding 的根因：负 pad 唯一来自 modeling_qwen3_5.py:490（pad=conv_kernel_size−prefill_seq_len，默认 4−32=−28），经 aten 映射透传后被 GE C++ builder 拒绝。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# Qwen3.5 导出报 PadV3 non-negative padding 的根因定位

## 适用场景
- cann-executorch / GE AOT 编译链路上导出 Qwen3.5（GDN/线性注意力结构，含 depthwise Conv1D conv state）时报 `PadV3 supports non-negative padding only`。
- 任何 transformers 模型在导出时把"裁剪语义"（负 padding）传给只接受非负 padding 的 PadV3 builder 检查的场景。
- 需要区分"重跑环境变了"还是"导出参数变了"导致此前能跑通的流程现在报错的排查。

## 触发与观测
- 触发：用户之前跑通过 Qwen3.5 完整流程（导出→GE 编译→打包→NPU 推理），重跑导出时报 `PadV3 supports non-negative padding only`；错误来自 runtime/src/ge_aot_compiler.cpp:5863 的 C++ builder 检查（不是 GE 本身）。
- 观测：负 pad 数值可由配置直接算出——prefill 分支 pad = conv_kernel_size − prefill_seq_len，默认参数下为 4−32 = −28。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${PYTHON_SITE_PACKAGES}`：发生问题的 Python 环境的 site-packages 目录。

- 读模型配置确认 kernel 维度：
````text
linear_conv_kernel_dim= 4
layer_types count= 24
max_position_embeddings= 262144
````
- 对照导出 CLI 默认值：qwen3_5_static_kv_gate.py 的 main() 默认 `--prefill-seq-len 32 --max-seq-len 1024`。

## 机制与判别
- 负 pad 唯一来源（transformers 源码，事件 115 原文）：
````text
- 文件：`${PYTHON_SITE_PACKAGES}/transformers/models/qwen3_5/modeling_qwen3_5.py`
- **第 490 行**：
  ```python
  new_conv_state = F.pad(mixed_qkv, (self.conv_kernel_size - mixed_qkv.shape[-1], 0))
  ```
- **第 385 行**：`self.conv_kernel_size = config.linear_conv_kernel_dim`，对 Qwen3.5-0.8B 实测 = **4**。
````
- 报错点：
````text
3. C++ builder 拒绝负值：`runtime/src/ge_aot_compiler.cpp:5862-5864`
   ```cpp
   if (before < 0 || after < 0) {
     throw std::invalid_argument("PadV3 supports non-negative padding only");
   }
   ```
````
- 分支行为：prefill 分支 mixed_qkv.shape[-1]=prefill_seq_len → pad=4−prefill_seq_len（>4 即负）；decode(seq_len=1) 走 causal_conv1d_update 不经 F.pad（安全）；chunked decode(seq_len>1) 先 cat 后 pad=4−(4+seq_len)=−seq_len（>1 即负）。
- 映射链：aten.constant_pad_nd.default → PadV3（ge_ir_plan.py:76）→ pad 属性透传不校验正负（lowering_plan.py:469-471）→ C++ builder 拒绝（上述 cpp）。
- 结论：PadV3 负 padding 的唯一来源是 modeling_qwen3_5.py:490 的 new_conv_state = F.pad(mixed_qkv, (self.conv_kernel_size - mixed_qkv.shape[-1], 0))：prefill 分支 mixed_qkv.shape[-1]=prefill_seq_len，Qwen3.5-0.8B 的 linear_conv_kernel_dim 实测为 4（layer_types 24 层、max_position_embeddings 262144），因此 prefill_seq_len>4 即产生负 pad（CLI 默认 --prefill-seq-len 32 → pad=4-32=-28），经 aten.constant_pad_nd→PadV3 映射透传后被 GE C++ builder 的非负校验拒绝；chunked decode（seq_len>1）分支 pad=4-(4+seq_len)=-seq_len 同样为负。

## 验证信号
- 配置探针输出：linear_conv_kernel_dim= 4（见上文工件）。
- 注意：本会话为只读调研，未实际重跑导出验证。

## 适用与失效边界
- 适用：Qwen3.5/Qwen3-next 类 GDN 模型在 GE AOT 导出链路的 PadV3 负 padding 报错；判别式 pad = linear_conv_kernel_dim − prefill_seq_len < 0。
- 失效边界：prefill_seq_len ≤ conv_kernel_size（0.8B 为 4）才能避开负 pad（判别式见上），需要更大 prefill 窗口的业务需上游另行处理负 pad 改写。
- 边界条件：结论基于 Qwen3.5-0.8B 的 linear_conv_kernel_dim=4；其他 checkpoint 需重测该值。
- 不确定项：本轨迹未验证 chunked decode（seq_len>1）在 PadV3 检查之外是否还有其它阻塞。

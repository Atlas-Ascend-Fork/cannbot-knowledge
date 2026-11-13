---
{
  "type": "Runbook",
  "title": "MLA Prolog Quant 单点超阈时核对 golden 与实现的 epsilon 差异",
  "description": "来源用例出现一个 kv 误差点，并发现 golden 的 rms_norm 未加 epsilon，而实现使用 1e-5。记录中应用了 golden 修改，但没有修后精度结果；应先按算子规格确认参考语义，不能仅为贴合实现而修改 golden。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# MLA Prolog Quant 单点超阈时核对 golden 与实现的 epsilon 差异

## 适用场景


MLA Prolog Quant 的参考实现与被测实现数值语义核对。该记录不证明设备 kernel 已修复。

## 触发与观测


CANN 9.2.0 编包后的 test_b64_s64k2_pa_nd_bf16_d 在 kv 张量出现 1 个超阈误差点：0.00390625 大于阈值 0.00341797，error_count_threshold=0。源码比较发现参考端没有 epsilon，而实现使用 epsilon=1e-5。

## 探针与操作


分别核对 golden 与实现中的归约轴、归约方式和 epsilon，然后回到算子规格确认应采用的数学定义。下文是来源中已应用的 golden 修改片段；它不是修后通过证据。

## 机制与判别

机制片段：

```
def rms_norm(x, gamma, epsilon=1e-5):
    x_dtype = x.dtype
    mean_coff = 1.0 / x.shape[-1]

    x_f32 = x.to(torch.float32)
    square = x_f32 * x_f32
    mean_res = square * mean_coff

    reduce_sum = torch.sum(mean_res, dim=-1, keepdims=True)
    reduce_sqrt = torch.sqrt(reduce_sum + epsilon)
    res_div = x_f32 / reduce_sqrt

    res = res_div * gamma

    if x_dtype != torch.float32:
        res = res.to(x_dtype)
    return res
```

## 验证信号


记录包含 golden 修改落盘，没有修后设备精度通过结果。需要依据规格确认 epsilon，再运行相同输入、相同阈值的对照；不得因修改参考后更接近实现就认定实现正确。

## 适用与失效边界


仅能确认两条路径存在 epsilon 差异及来源采用的修改。没有独立规格依据和修后结果时，应保留诊断，不声称已修复单点误差。

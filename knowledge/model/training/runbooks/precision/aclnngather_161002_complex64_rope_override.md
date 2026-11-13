---
{
  "type": "Runbook",
  "title": "aclnnGather error 161002 DT_COMPLEX64：ComplexRoPE complex64 cache 走 torch.gather 的定位",
  "description": "torchtitan-npu deepseek_v3_2 模型 ComplexRoPE 路径在 NPU 上 gather complex64 cache 的算子 dtype 支持缺陷定位，面向真实训练启动排障。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# aclnnGather error 161002 DT_COMPLEX64：ComplexRoPE complex64 cache 走 torch.gather 的定位

torchtitan-npu deepseek_v3_2 的 ComplexRoPE 路径对 complex64 cache 走 torch.gather，触发 aclnnGather error 161002。本卡记录调用链定位。

## 适用场景

torchtitan-npu deepseek_v3_2（ComplexRoPE 路径）训练启动即报 aclnnGather 不支持 complex64 的诊断场景；也可用其检查流程核对其他 dtype，但不能推导所有非 float 输入都不支持。route=training，area=precision。

## 触发与观测

触发：报错 aclnnGather failed, error code 161002 Tensor self not implemented for DT_COMPLEX64, should be in dtype support list [DT_FLOAT,DT_INT32,DT_FLOAT16,...]。

## 探针与操作

探针：grep 定位 ComplexRoPE（pip torchtitan rope.py:181）与 torch.gather 调用点（rope.py:390；另有注释声称两输入同 dtype，但该注释不能替代实际接口契约）；override/common/rope.py 中 _reshape_for_broadcast 的 cos/sin float cache 调用对照；调用链逐层核对（dataloader positions 恒非 None → positions.size(0)>1 → gather 分支）。

## 机制与判别

deepseek_v3_2 训练（local_batch_size=4，dataloader 总是输出非 None positions）在 ComplexRoPE 路径触发 aclnnGather error 161002（Tensor self not implemented for DT_COMPLEX64, should be in dtype support list [DT_FLOAT,DT_INT32,DT_FLOAT16,...]）：positions.size(0)>1 时 _reshape_for_broadcast 走 torch.gather 分支（rope.py:390），对 torch.polar 生成的 complex64 cache 做 gather，而 该环境 aclnnGather 的支持列表不含 DT_COMPLEX64；列表实际还含 DT_INT32，不能概括为仅支持 float；源码注释所称“both operands same type”不能作为接口契约，输入 dtype 与索引 dtype 应分别核对。

失败路径：

```
    else:
        # *** FAILURE PATH ON NPU ***
        # Per-batch positions use torch.gather on the complex64 cache
        positions = positions.expand(bsz, -1)
        rope_cache_expanded = rope_cache[None, :, None, :].expand(bsz, -1, -1, -1)
        rope_cache = torch.gather(                      # <-- LINE 390
            rope_cache_expanded,                       # complex64 tensor!
            dim=1,
            index=positions.view(bsz, seqlen, 1, 1).expand(bsz, seqlen, 1, cache_width),
        )
        return rope_cache
```


## 验证信号


采用的是 ComplexRoPE 源码、positions 分支及所报 DT_COMPLEX64 错误的对照。没有 NPU 修复后复跑；仅凭源码旁的注释不能建立 torch.gather 的通用 dtype 契约。

## 适用与失效边界

边界：触发依赖 positions.size(0)>1（per-batch positions）；positions 为 None 或 singleton 时走切片/索引安全路径不触发。

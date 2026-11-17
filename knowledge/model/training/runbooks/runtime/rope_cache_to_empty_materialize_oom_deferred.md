---
{
  "type": "Runbook",
  "title": "RoPE cache 初始化峰值：分别检查 to_empty 与 init_states 的存储身份",
  "description": "CPU 生命周期探针显示 to_empty 后多份存储、init_states 后重新共享；meta data_ptr 为零不能单独证明 alias，长序列 OOM 幅度仍是估算。",
  "tags": [
    "task.debugging",
    "topic.memory"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# RoPE cache 初始化峰值：分别检查 to_empty 与 init_states 的存储身份

## 适用场景

torchtitan 的大 buffer/cache 经 meta→to_empty→init_states 初始化，pool 可能只在最后一步合并存储。

## 触发与观测

cache pool 已降低常驻重复，但加载峰值仍大；需要检查完整生命周期而非只看最终对象。

## 探针与操作

分别检查对象身份/存储、shape 和设备，在 CPU 小例上走完整初始化顺序。meta 指针全为零没有真实存储，不能用它证明共享。

原始小例的存储观测摘要；不由 meta 零指针推导 alias：

```text
meta ptrs [0, 0, 0]
after to_empty: three different CPU data_ptr values
after init_states: three equal CPU data_ptr values
```

## 机制与判别

探针中 to_empty 后三个 CPU data_ptr 不同，init_states 后相同，说明最终合并并不能排除中途独立分配。meta 阶段一元素占位是记录中的候选修正，用来推迟大 cache 的物化。

## 验证信号

原始小例输出 after to_empty alias False 和三个不同 CPU 指针，随后 init_states 恢复相同指针。它没有对 1M 序列真实加载进行端到端显存复测。

## 适用与失效边界

约 63GiB 峰值来自给定 shape/实例数的估算，不作为设备实测。完整 cache 的首次创建仍可能有临时峰值；模型、注册 buffer 和初始化钩子均需匹配。

---
{
  "type": "Runbook",
  "title": "DSV4 CP 块对齐切分：区分边界几何与索引探针的前提",
  "description": "文档内按块边界切分只证明几何条件；另造的非对齐段不满足索引探针前提，不据其结果裁定真实 aligned shard 的成败。",
  "tags": [
    "task.implementation",
    "topic.parallelism"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": [
    "agnostic"
  ]
}
---
# DSV4 CP 块对齐切分：区分边界几何与索引探针的前提

## 适用场景

DSV4 Context Parallelism，压缩比 r=4 与 r=128，块边界以文档起点为原点。

## 触发与观测

均匀 headtail 切分可能把同一压缩块分到不同 rank，增加边界借入和交换逻辑。

## 探针与操作

检查每个文档内部切分点的偏移是否为 ratio 倍数，记录实际 (start,end) 而非继续假设等长 shard。算法描述如下，不是可直接执行的 Python。

几何与索引检查单元；不作为后续版本单测的实现工件：

```text
输入：seq、文档区间、cp、压缩 ratio；这是检查清单，不是已验收实现。
构造 2*cp 个 headtail chunk 的内部目标边界。
保留首端 0 和末端 seq；非整除长度也必须覆盖尾部。
将内部目标点吸附到所在文档的起止点或文档内合法块边界。
检查边界单调、全集覆盖、空 shard、索引映射和 attention 数值。
对齐 True 只验收几何。另造长度 50 的非对齐段不满足 identity 参考预期；其 51 bad 不裁定实际 aligned shard 的成败。
```

## 机制与判别

吸附候选点取文档边界和该文档内的压缩块边界；对这里的 4/128 两种 ratio，按 128 对齐同时满足两者。该几何性质不单独保证注意力数值或分布式通信等价。

## 验证信号

早期 CPU 输出报告实际切分的 all chunk edges on block boundaries: True。另造的长度 50、末端未对齐的段报告 51 bad，但不满足 aligned identity 的参考预期，不能作为实际 aligned shard 失败的反例。后续版本的 9/264 passed 也不拼接为所示检查单元的验收。

## 适用与失效边界

真实 NPU/CP 数值验收未完成。文档尾块、短文档、非整除长度、空 shard 和负载倾斜需单独覆盖；切分终点必须覆盖 seq，不能把 seq 非整除时向下取整后遗漏的尾部丢弃。未来 ratio 组合不能一律用 max 代替 lcm。

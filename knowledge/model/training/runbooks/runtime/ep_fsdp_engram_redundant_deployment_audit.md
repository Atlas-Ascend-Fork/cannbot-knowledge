---
{
  "type": "Runbook",
  "title": "EP×eFSDP 的 engram 部署审计：分片行数、组关系与指纹观测",
  "description": "EP4×eFSDP2 探针显示四种分片及两份副本组关系；指纹是 sum，不可据其相同就宣称所有字节相同。",
  "tags": [
    "task.debugging",
    "topic.parallelism"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# EP×eFSDP 的 engram 部署审计：分片行数、组关系与指纹观测

## 适用场景

torchtitan-npu DSV4.1 host engram 表，八进程探针只执行 build、parallelize、init_states 与结果聚合。

## 触发与观测

dp_shard=8、ep=4 时，需要确认表按哪条 mesh 轴分片，而不是只看全局进程数。

## 探针与操作

逐 rank 记录 local_rows、ep_rank、checkpoint suffix、replica_ranks 与指纹算法；以 EP8 配置作对照。需要字节等价时另做完整内容哈希或逐元素比较。

原始探针的分片/副本关系摘要；sum 指纹不证明字节相同：

```text
logical rows = 6264; padded physical rows = 8192
EP4 / eFSDP2: rows per rank = 2048; total rows = 16384; physical deployment ratio = 2
replica groups: [0,4], [1,5], [2,6], [3,7]
EP8 / eFSDP1: rows per rank = 1024; total rows = physical rows = 8192
replica_ranks = None
```

## 机制与判别

所测表 logical=6264 行、padding 后 physical=8192 行。EP4×eFSDP2 每 rank 2048 行、合计 16384 行，部署倍数 16384/8192=2 的分母是物理表；组关系和 suffix 对应四种分片。配对 rank 的 sum 指纹相同只是观测，不能证明字节身份。

## 验证信号

原表报告 rank0/4、1/5、2/6、3/7 的 replica 关系和相同 sum；另一次 EP8 对照每 rank 1024 行、总行数等于 physical=8192，logical 仍为 6264，replica_ranks=None。

## 适用与失效边界

不含训练态梯度通信、完整权重内容一致性或更大并行规模实测。修改分片轴还需 checkpoint resharding、恢复和数值验证，不能从静态部署直接承诺消除通信收益。

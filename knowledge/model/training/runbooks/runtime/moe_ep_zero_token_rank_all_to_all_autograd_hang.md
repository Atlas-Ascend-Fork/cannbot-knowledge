---
{
  "type": "Runbook",
  "title": "MoE 0-token rank 的 CPU collective 梯度对照与 NPU hang 边界",
  "description": "torchtitan-npu MoE 专家并行训练在 token dispatch 后 0-token rank 卡死的机制判别与上游修复解读，服务真实 EP 训练排障。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# MoE 0-token rank 的 CPU collective 梯度对照与 NPU hang 边界

torchtitan-npu MoE 专家并行训练在 token dispatch 后 0-token rank 集合通信卡死。本卡记录 all_to_all_single_autograd 反向集合通信的 CPU 对照判别与上游修复解读。

## 适用场景

torchtitan-npu MoE 专家并行（EP）训练在小 batch / 专家负载不均导致某 rank 本地 0 token 时出现集合通信卡死（hang）的诊断场景；也适用于评估『autograd 集合通信在空张量 rank 上是否安全』这类机制判别。route=training，area=runtime。

## 触发与观测

触发条件：MoE EP 训练中某 rank 经 token dispatch 后本地 token 数为 0，旧实现使用 all_to_all_single_autograd 参与反向，表现为集合通信阶段无响应卡死（0817_master 分支由 commit 04d428d『fix moe zero token case』修复）。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${SCRATCH_DIR}`：由复现者创建的本次实验临时目录。


可执行探针：

```bash
cat > ${SCRATCH_DIR}/opencode/test_a2a_contrast3.py <<'EOF'
import os, torch, torch.distributed as dist
import torch.multiprocessing as mp

def worker(rank, q):
    os.environ["MASTER_ADDR"]="127.0.0.1"; os.environ["MASTER_PORT"]="29613"
    dist.init_process_group("gloo", rank=rank, world_size=2)
    from torch.distributed._functional_collectives import all_to_all_single, all_to_all_single_autograd
    # rank0 has 4 tokens: keeps 2, sends 2 to rank1. rank1 has 0 tokens.
    if rank == 0:
        x = torch.randn(4, 3, requires_grad=True)
        in_splits = [2, 2]   # send: 2 to r0, 2 to r1
        out_splits = [2, 0]  # recv: 2 from r0, 0 from r1
    else:
        x = torch.randn(0, 3, requires_grad=True)
        in_splits = [0, 0]
        out_splits = [2, 0]  # recv: 2 from r0, 0 from r1(self)
    mode = os.environ["A2A_MODE"]
    fn = all_to_all_single if mode == "plain" else all_to_all_single_autograd
    out = fn(x, out_splits, in_splits, dist.GroupMember.WORLD)
    loss = (out * 1.0).sum()
    try:
        loss.backward()
        q.put((rank, "OK", "grad_is_None=%s" % (x.grad is None), "out_rows=%d" % out.shape[0]))
    except Exception as e:
        q.put((rank, "BACKWARD_ERR", str(e)[:120]))
    dist.destroy_process_group()

if __name__ == "__main__":
    mp.set_start_method("spawn")
    for mode in ["plain", "autograd"]:
        ctx = mp.get_context("spawn")
        q = ctx.SimpleQueue()
        os.environ["A2A_MODE"] = mode
        ps = [ctx.Process(target=worker, args=(r, q)) for r in range(2)]
        [p.start() for p in ps]
        [p.join(45) for p in ps]
        print("MODE=%s exitcodes=%s" % (mode, [p.exitcode for p in ps]))
        while not q.empty():
            print("  ", q.get())
EOF
python ${SCRATCH_DIR}/opencode/test_a2a_contrast3.py 2>&1 | grep -E "MODE=|OK|ERR"
```


观测输出：MODE=plain 两 rank 均 grad_is_None=True（无反向集合通信）；MODE=autograd 两 rank grad_is_None=False（反向梯度回流）。

## 机制与判别


CPU/gloo 两种 API 的对照均退出 0，未复现 hang。plain 调用中 x.grad 为 None、autograd 调用中梯度回流，只区分了反向梯度路径。不能由此证明“存在反向 collective 就足以在 0-token rank 上 hang”，也不能称 plain API 永远不会卡住。来源上游修订使用自定义 autograd.Function、plain collective 和 wait_tensor，并在反向梯度为 None 时物化零梯度；该修订的意图是让各 rank 继续参与匹配的反向通信。

## 验证信号


已运行的是两 rank CPU/gloo 梯度对照，两个分支均退出 0。读取了上游修订说明与 diff，但未在 NPU/HCCL 上重放原始 hang 或验证该修订消除故障。

## 适用与失效边界


CPU 参考实验只能帮助理解梯度路径，不能等价于 HCCL 训练复现。实际还需核对所有 rank 的参与、splits、collective 次序、空组行为和目标代码修订；零梯度物化本身不能单独保证这些条件。

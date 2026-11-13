---
{
  "type": "Runbook",
  "title": "诊断规则 · vllm-ascend FIA 算子图模式卡死根因：混合模型 attn_backend 误派发到 SFA 的 no-op update_graph_params",
  "description": "VLLM_ASCEND_DOTS3_USE_FIA=1 且非 enforce-eager 时服务在首个 decode 图重放卡死（sample_tokens RPC 超时）。先用日志插桩定位到 update_full_graph_params 被调用但 mla_v1.update_graph_params 从未执行（MLA_UPDATE_ENTRY=0），再确认混合模型 model-level attn_backend 是 AscendSFABackend 且其 update_graph_params 为 no-op，FIA graph task 句柄由 MLA backend 捕获，update_full_graph_params 派发到 SFA 后句柄永不绑定执行，下一次图重放永久阻塞。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# 诊断规则 · vllm-ascend FIA 算子图模式卡死根因：混合模型 attn_backend 误派发到 SFA 的 no-op update_graph_params

## 适用场景

vllm-ascend 上使用 FIA（Flash Inference Attention）算子图模式（`VLLM_ASCEND_DOTS3_USE_FIA=1` 且非 `--enforce-eager`）服务 dots3 note / xdg_moe_mla 类混合模型（同时有 SFA 稀疏层与 MLA/SWA 层、config 含 index_topk → use_sparse=True 且 use_mla=True）的场景。


## 触发与观测
触发：首个 decode 图重放后 `sample_tokens` RPC 超时（`TimeoutError: RPC call to sample_tokens timed out`），bench 10/10 Internal Server Error、吞吐 0；进程态特征：NPU AICore 0%、TP0 worker 用户态 94.9% CPU 自旋（RT_RECYCLE 线程 + worker 线程），最后日志停在 `acl_graph.py:257 Replaying aclgraph`。FIA=0、FIA=1+enforce-eager、独立 fia_golden_graph.py 图模式测试均正常。

## 探针与操作
1) 日志插桩（acl_graph replay 前后、_update_full_graph_params_if_needed 入口/出口、mla_v1.update_graph_params 入口/出口、_propose 里程碑），重启复现后 grep 计数：UPDATE_GRAPH_ENTRY=16 但 MLA_UPDATE_ENTRY=0 → update 被调用却从未到达 mla_v1。2) 读部署代码确认派发链：`update_full_graph_params` 经 `self.attn_backend` 的 impl_cls 派发；`get_attn_backend` 的 backend_map[(use_mla, use_sparse, use_compress)] 中 (True, True, False) → AscendSFABackend；而 `sfa_v1.py` 的 `update_graph_params` 是 `pass`。3) 参考环境对照：参考环境模型走纯 MLA 后端所以不挂——同一份 platform/backend 选择逻辑，差异在模型 config 是否触发 use_sparse。

## 机制与判别
机制：FIA 的 graph task 在图捕获期由 mla_v1 的 `_forward_decode` 记录句柄，运行期必须由 `update_graph_params` 在 update_stream 上 `graph_task_update_begin/end` 真正执行并 `event.record(update_stream)`，主图靠捕获期 `event.wait(stream)` 等待；句柄不被更新 → FIA 算子永不执行 → 流上事件不置位 → 下一次 replay 的 synchronize 永久阻塞。

### 补充机制片段
```
    @staticmethod
    def update_graph_params(
        update_stream,
        forward_context,
        num_tokens,
        vllm_config=None,
        speculative_config=None,
        num_dcp_pcp_tokens=None,
        draft_attn_metadatas=None,
    ):
        # sfa does not need to update graph params
        pass
```

## 验证信号
验证信号：根因定位的插桩与代码读取（SFA update_graph_params 为 pass、混合模型 backend 解析为 AscendSFABackend，见机制片段：与来源结论）。注意轨迹后段在同服务的图像+MTP 混合步上仍残留另一个 stream 46 挂死（mm-encoder 相关、未解决），与本卡根因正交。

### 结论与证据边界

  FIA 图模式卡死的最终根因是后端误派发：dots3 note 混合模型（use_sparse=True 且 use_mla=True）的 model-level attn_backend 解析为 AscendSFABackend，其 update_graph_params 是 no-op（pass）；FIA graph task 句柄由 MLA backend 捕获，update_full_graph_params 派发到 SFA 后句柄永不绑定执行，FIA 算子不在 update_stream 上运行，下一次图重放永久阻塞在 stream synchronize（表现为 sample_tokens RPC 超时、NPU AICore 0% 且 worker 用户态自旋）。

## 适用与失效边界
适用：混合 SFA+MLA 模型 + FIA 图模式。失效/边界：图模式的 update 链依赖 acl_graph FULL 模式的同步屏障语义，enforce-eager 下不可复现。

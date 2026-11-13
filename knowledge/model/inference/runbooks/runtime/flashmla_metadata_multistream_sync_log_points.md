---
{
  "type": "Runbook",
  "title": "vllm-ascend MLA metadata 多流同步移植的分级日志定位点设计",
  "description": "向 vllm-ascend v0.30 mla 分支移植 v0.27 的 FlashMLA metadata 多流同步时，在 5 个文件增加启动/首次构建/capture 级别日志（不刷热路径），覆盖层初始化→PA_NZ 校验→group 构建→KV 规划→KV view→metadata builder→多流→metadata 构建→decode→attention 全链路，可用 grep -E \"\\[PA_NZ\\]|\\[FlashMLA\\]|K3 PA_NZ\" 快速过滤，从日志直接判读 async metadata 是否生效及在哪一层失效。",
  "tags": [
    "task.implementation",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# vllm-ascend MLA metadata 多流同步移植的分级日志定位点设计

## 适用场景

向 vllm-ascend v0.30 mla 分支移植 v0.27 的 FlashMLA metadata 多流同步时，在 5 个文件增加启动/首次构建/capture 级别日志（不刷热路径），覆盖层初始化→PA_NZ 校验→group 构建→KV 规划→KV view→metadata builder→多流→metadata 构建→decode→attention 全链路，可用 grep -E "\[PA_NZ\]|\[FlashMLA\]|K3 PA_NZ" 快速过滤，从日志直接判读 async metadata 是否生效及在哪一层失效。


把 vllm-ascend v0.27 的 FlashMLA metadata 多流同步（异步 metadata）移植到 v0.30 mla 分支后，需要在不刷热路径的前提下定位 async metadata 是否生效、在哪一层失效；适用于 MLA/PA_NZ 特性移植与回归定位。

## 触发与观测

移植完成但缺少可观测性；或 eager 与 capture 两条路径行为不一致需要区分；需要快速过滤关键日志。

## 探针与操作

用统一前缀过滤：grep -E "\[PA_NZ\]|\[FlashMLA\]|K3 PA_NZ"；按层初始化→PA_NZ 校验→group 构建→KV 规划→KV view→metadata builder→多流→metadata 构建→decode→attention 的顺序读日志定位第一个异常阶段。

## 机制与判别

分级日志定位点：


| 阶段 | 日志前缀/内容 |
| --- | --- |
| 层初始化 | `[MLA] layer=... layout=... requested_pa_nz=... draft/pcp/dcp/use_flashmla ...` |
| PA_NZ 校验 | `[PA_NZ] layer=... validated: heads/kv_lora/dtype/spec/kv_transfer`（ops 加载成功） |
| group 构建 | `[MLA] flashmla state: layout=... async=... reserved_pages=...`；混合 layout 会单独打印 |
| KV 规划 | `K3 PA_NZ planner: num_blocks/reserved/page_bytes`、`bucket: layout/page/layers/tuple_count`、`tensor: layout/tuple/layer_stride/size`、`reserved pages fallback -> 2` |
| KV view | `[PA_NZ][kv] layer=... blocks/reserved/view=...`、`single raw backing: transfer/component_major_pd/contiguous` |
| metadata builder | `[FlashMLA] metadata builder: layout/heads/dcp/async/reserved`、`first build`、`capture buffers` |
| 多流 | `[FlashMLA] async metadata start (eager)`、`[FlashMLA] capture metadata schedule`、`[FlashMLA] model hook started metadata: layer=... async=...` |
| metadata 构建 | `[MLA] first external FlashMLA metadata: decodes/...`、`[MLA] capture external FlashMLA metadata: ...` |
| decode | `[PA_NZ] decode layer=... tokens/actual/q_len/cache/block/reserved/hidden_page/scratch_page/prolog_slots/async`；DCP 首次进入单独一行 |
| attention | `[FlashMLA] external attention: layer=... q=... cache=... schedule=...`（每层首次） |

**结论要点：**

- 日志定位点全链路覆盖且不刷热路径：在 5 个文件（vllm_ascend/attention/flashmla.py +51 行、attention/mla_v1.py +93 行、models/kimi_k3.py +7 行、patch/platform/patch_kv_cache_utils.py +44 行、worker/v2/attn_utils.py +22 行，合计 215 insertions/2 deletions）增加启动/首次构建/capture 级别日志，py_compile 与 diff --check 通过；阶段覆盖层初始化、PA_NZ 校验、group 构建、KV 规划、KV view、metadata builder、多流、metadata 构建、decode、attention。


## 验证信号

5 个文件共 215 insertions/2 deletions（flashmla.py +51、mla_v1.py +93、kimi_k3.py +7、patch_kv_cache_utils.py +44、attn_utils.py +22），py_compile OK、diff-check OK；日志均为启动/首次构建/capture 级别、不刷热路径。

## 适用与失效边界

日志改动本身仅通过静态检查，未在 NPU 上验证输出（移植的 NPU 验证由后续进行）；定位点覆盖 PA_NZ/FlashMLA 链路，不覆盖 prolog 与 attention kernel 内部；若需热路径级观测应另用 profiler 而不是加日志。

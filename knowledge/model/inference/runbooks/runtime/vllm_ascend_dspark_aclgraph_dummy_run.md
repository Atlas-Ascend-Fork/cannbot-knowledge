---
{
  "type": "Runbook",
  "title": "vllm-ascend v1 路径 DSpark 草稿器 ACLGraph 支持迁移：宽度门控与 dummy_run FULL 捕获（本次实现，未做 NPU 运行验证）",
  "description": "将 cann-recipes-infer 的 Kimi K3 DSpark 图模式（npugraph_ex 整图 forward_spec_decode）迁移为 vllm-ascend v1 路径的 ACLGraph 支持：以两道门控替代 AscendDSparkProposer 的强制 eager（草稿查询宽度须等于 uniform_decode_query_len、builder 须支持 ChunkedPrefill 图捕获），dummy_run 新增逐 KV-cache group 的 FULL 捕获分支并把锚点 KV 预填充算子纳入捕获图。10 文件 +514/-18 提交 b480cfb 推送到 k3-dspark-cudagraph 分支；11 个单测已写入但未运行（无 pytest），NPU e2e 验证未做。用户侧 ruff 报 3 项中仅 F821（重写 import 块误删 get_layers_from_vllm_config）为真实缺陷，已修复推送 e3440ec。",
  "tags": [
    "task.implementation",
    "topic.graph_execution",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "agnostic"
  ]
}
---

# vllm-ascend v1 路径 DSpark 草稿器 ACLGraph 支持迁移：宽度门控与 dummy_run FULL 捕获（本次实现，未做 NPU 运行验证）

## 适用场景

- 框架/模型：vllm-ascend（v1 路径，`VLLM_USE_V2_MODEL_RUNNER` 未设置时的默认路径）上的 Kimi K3 DSpark 投机解码（块草稿器，`forward_spec_decode` 含 Markov 采样循环）。
- 迁移源：cann-recipes-infer 的 Kimi K3 样例——`runner_kimi_k3.py:210-242` 用 `torch.npu.npugraph_ex.inference.cache_compile(...)`（backend="npugraph_ex"）将 `forward_spec_decode` 整图编译执行，输入张量以 `torch._dynamo.mark_static` 标记。
- 目标仓状态：GitCode `wangtao43/vllm-ascend` 分支 `k3-dspark-cudagraph`（基线 main `9bbec317`）；工作环境为 Windows + PowerShell，本机无 vllm/pytest/ruff、无网络。
- 缺失信息：无 NPU 环境，全部验证为静态检查。

## 触发与观测

迁移前的客观状态（T81 逐字，dspark_proposer.py L72-73）：

```
72:         # DSpark runs eager only (Ascend cudagraph unsupported on this path).
73:         self.use_cuda_graph = False
```

即 **vllm-ascend v1 路径的 AscendDSparkProposer 原为强制 eager（dspark_proposer.py L72-73 "DSpark runs eager only (Ascend cudagraph unsupported on this path)."），Kimi-K3 教程因此要求 DSpark 配置 enforce_eager: true。**对照：v2 路径的 `AscendDSparkSpeculator` 已继承上游 DFlash 全图路径；v1 的 `_propose` 中 DSpark FULL 图 padding 逻辑（llm_base_proposer.py:1085-1097）已预埋；DFlash 的 `dummy_run` 有完整的 `build_for_graph_capture` 参考实现。

用户确认方案后（T191）实施迁移。

## 探针与操作

实施（`vllm_ascend/spec_decode/dspark_proposer.py` 为主，10 文件 +514/-18）：

1. 宽度门控（C384 逐字）：

```
        # DSpark joins the merged target/draft ACLGraph only when its query
        # block width matches the target's uniform decode query length, which
        # is the width the shared cudagraph dispatcher, the FIA query-length
        # padding helpers, and the captured draft graph are keyed by.
        # Anchor-sampled drafts query K tokens per request while the target
        # verify step uses K + 1, so their token buckets never line up and the
        # draft keeps running eager (the historical behavior).
        uniform_decode_query_len = getattr(runner, "uniform_decode_query_len", None)
        if self.use_cuda_graph and (
            uniform_decode_query_len is None or self.num_query_per_req != uniform_decode_query_len
        ):
            logger.warning(
                "DSpark drafts that sample from the anchor (query width %d) do "
                "not align with the target's uniform decode query length (%s) "
                "and run in eager mode. Graph mode requires a draft whose "
                "query width matches the target verify width.",
                self.num_query_per_req,
                uniform_decode_query_len,
            )
            self.use_cuda_graph = False
```

2. builder 能力门控（initialize_attn_backend 末尾，C395 逐字）：

```
        # Graph capture builds draft metadata through
        # ``build_for_graph_capture`` with a ChunkedPrefill state, which only
        # matches the eager drafting build for backends that derive their
        # metadata from the common attention metadata alone (GQA/MLA).
        # Backends with a specialized drafting build (DSA, ...) stay eager.
        if getattr(self, "use_cuda_graph", False) and not all(
            getattr(attn_group.get_metadata_builder(), "supports_chunked_prefill_graph_capture", False)
            for attn_group in self.draft_attn_groups
        ):
            logger.warning(
                "DSpark draft attention backends without ChunkedPrefill graph "
                "capture support run in eager mode."
            )
            self.use_cuda_graph = False
```

3. capability 类属性（mla_v1.py / attention_v1.py，C412 逐字）：

```
    # Graph capture with a ChunkedPrefill state (block-drafter query blocks)
    # goes through the same build() as eager drafting, so captured and eager
    # draft metadata stay identical. See build_for_graph_capture.
    supports_chunked_prefill_graph_capture = True
```

配套扩展 `AscendMLAMetadataBuilder.build_for_graph_capture` 接受 `AscendAttentionState.ChunkedPrefill`（均匀草稿查询块按 decode 分类，与 eager drafting 构建一致）；DSA/SFA/DCP builder 不声明该标志故保持 eager，DCP 变体（mla_cp.py / attention_cp.py）显式排除（未验证组合）。

4. dummy_run FULL 捕获分支（dspark_proposer.py:447-513）：逐 KV-cache group 构建 `AscendCommonAttentionMetadata` + `build_for_graph_capture(ChunkedPrefill)`；`_maybe_update_metadata`；replay 后 `_update_full_graph_params`（捕获期跳过）。

5. 自审发现并修复的三处捕获正确性缺陷（会话内代码级推理发现，非运行触发）：
   - 捕获时 `_context_slot_mapping_buffers` 为 None（仅由 set_inputs_first_pass 填充）→ 物化 per-layer context slot mapping，保证锚点 KV 预填充算子进入捕获图（C569）。
   - `_dflash_num_context` 在首次 dummy_run 时可能未初始化（`_pad_draft_buffers` 先读后赋）→ `__init__` 中初始化为 0（C577）。
   - 赋值时机（C581 逐字）：

```
        self.token_indices_to_sample.fill_(0)
        # Set the context count before padding: _pad_draft_buffers marks the
        # context slot-mapping tail beyond _dflash_num_context as padding
        # (-1), while the anchor-token KV prefill inside the captured graph
        # reads slots[:_dflash_num_context] and must not see padding ids.
        self._dflash_num_context = num_input_tokens
        self._pad_draft_buffers(num_query_total, num_input_tokens)
```

总结论：**迁移实现以两道门控替代强制 eager：宽度门控要求草稿查询宽度 num_query_per_req == runner.uniform_decode_query_len（sample_from_anchor=false 的草稿，宽度 K+1）才加入目标/草稿合并图，anchor 采样草稿（宽度 K）自动回退 eager；builder 能力门控要求全部草稿注意力 builder 支持 ChunkedPrefill 图捕获，DSA/SFA/DCP 保持 eager。**以及 **dummy_run 新增 FULL 捕获分支：逐 KV-cache group 构建 AscendCommonAttentionMetadata 并调用 build_for_graph_capture(ChunkedPrefill)，物化 per-layer context slot mapping 缓冲并把 _dflash_num_context 的赋值提前到 _pad_draft_buffers 之前，保证锚点 KV 预填充算子进入捕获图且不读到 -1 padding 槽位。**

6. 文档与测试：Kimi-K3.md §5.2 与 speculative_decoding.md 移除 enforce_eager 要求、说明图模式条件与 anchor 回退；单测见验证信号。

7. 上传：本机非 git 仓库且无网络，从原始 zip 提取 10 个文件基线核对差异后，经用户提供的 GitCode 访问令牌克隆远端、覆盖 10 个修改文件（LF 行尾，规避 autocrlf 噪音）、提交推送。

## 机制与判别

- 宽度门控的架构依据（会话内深度分析结论，未运行验证）：v1 共享 cudagraph dispatcher 与 FIA query-length padding 按目标 verify 宽度（K+1）键控图，anchor 采样草稿查询宽度为 K，K 与 K+1 的 token 桶无法对齐，故不能进合并图（v2 用草稿专属 graph manager 解决此约束）。
- builder 门控的语义依据：捕获构建走 `build_for_graph_capture(ChunkedPrefill)`，只有"捕获构建与 eager drafting 构建语义一致"的 backend（GQA/MLA，元数据仅由 common attention metadata 派生）才可捕获；有专用 drafting 构建的 backend（DSA 等）保持 eager。
- F821 真伪判别（用户侧 ruff check 报 3 项）：核查方法是把当前文件与原始 zip 基线做 import 符号审计（正则解析全部 import 名并求差集，T779 客观输出）：

```
LOST in vllm_ascend/spec_decode/dspark_proposer.py: get_layers_from_vllm_config
IMPORT AUDIT DONE
```

结论：**用户侧 ruff check 报 3 项中仅 F821 为真实缺陷：迁移重写 import 块误删 get_layers_from_vllm_config（dspark_proposer.py:158 引用未导入名），已修复并推送为提交 e3440ec；UP035/UP042 相对本仓为误报（setup.py 声明 python_requires>=3.10，typing.Self 与 enum.StrEnum 均 3.11+，且 (str, Enum)→StrEnum 会改变 str() 序列化行为）。**判别要点：F821 的后果是 `initialize_attn_backend` 运行时 NameError 且 UT 的 `monkeypatch.setattr("...dspark_proposer.get_layers_from_vllm_config", ...)` 因属性不存在失败；后两项不在本 MR 改动集内、CI（pre-commit 固定 ruff v0.14.0 + pyproject line-length 120）在 main 上是绿的，照改会破坏 3.10 环境，根治应在 pyproject 加 `target-version = "py310"`（单独提交）。修复本身一行恢复（C783 逐字）：

```
from vllm.config import CUDAGraphMode, VllmConfig, get_layers_from_vllm_config
```

## 验证信号

本轨迹内实际观测到的信号（全部静态/工件级）：

- T81：改前 dspark_proposer.py L72-73 强制 eager 原文。
- T504/T540/T599/T620：多轮 `python -m py_compile` 输出 COMPILE OK / ALL COMPILE OK。
- T507：`import vllm` 失败（本机无 vllm/pytest）；T511/T515：ruff 不可用且无法安装（无网络）。
- T627/T630：行长检查发现 158 字符超限行（pyproject line-length=120）并修复；T638：空白检查 WS CHECK DONE。
- T738：补丁 diff `10 files, +514/-18`；T745：提交 `b480cfb` 创建成功；T749/T755：推送 `k3-dspark-cudagraph` 成功且 API 验证分支指向。
- T767/T768/T779：F821 证据（当前文件 :158 引用 / 原始 zip import 行 / import 符号审计 LOST）。
- T787：修复后 COMPILE OK；T795：提交 `e3440ec` 推送成功（1 file changed, 1 insertion(+), 1 deletion(-)）；T799：API 验证分支 sha=e3440ec8df319df5f399888f8e8c1a9bafa36d77。
- 测试工件：**本次迁移写入 11 个单测（宽度门控 4 + dummy_run 捕获 5 + backend 门控 2）与 MLA ChunkedPrefill 捕获元数据测试，并更新 Kimi-K3.md 与 speculative_decoding.md 移除 enforce_eager 要求；推送为 k3-dspark-cudagraph 分支的提交 b480cfb（10 文件 +514/-18）。**（T642 可见 `TestDSparkAclGraphGate` 等测试类；A647 汇总）

未观测到的信号：**验证边界：本环境无 vllm/pytest/ruff 且无网络，仅完成 py_compile、行长（≤120）与空白检查；全部单测未运行，NPU e2e 验证未做。**建议在开发环境运行 `pytest -sv tests/ut/spec_decode/test_dspark_proposer.py tests/ut/attention/test_mla_v1.py`、`ruff check vllm_ascend/ tests/ut/`、`bash format.sh ci`，并参照 `tests/e2e/pull_request/one_card/spec_decode/test_dspark.py` 增加 NPU e2e 用例。

## 适用与失效边界

- 适用：vllm-ascend v1 路径 DSpark 块草稿器（K3 等）；`sample_from_anchor=false`（查询宽度 K+1）+ GQA/MLA builder 的组合。
- 失效/回退边界：
  1. anchor 采样草稿（宽度 K）不支持图模式，自动回退 eager 并告警——这是 v1 架构约束，非缺陷；需要图模式时换 `sample_from_anchor=false` 的草稿或走 v2 路径。
  2. DSA/SFA/DCP attention builder 不支持本迁移的图捕获（捕获构建与 eager drafting 语义不一致），保持 eager；DCP + 草稿图捕获是显式排除的未验证组合。
  3. 全部正确性结论（三处捕获缺陷修复、门控语义）为代码级推理 + py_compile，未经单测与 NPU e2e 验证；接受长度变化、profile 行为、图捕获覆盖率均未测量。
  4. 版本耦合：改动基于 main 基线 `9bbec317`，`uniform_decode_query_len`、`supports_chunked_prefill_graph_capture`、`build_for_graph_capture` 签名随上游演进可能变化。
  5. 小瑕疵：修复提交 e3440ec 的 message 开头带 UTF-8 BOM（PowerShell 写文件所致），建 MR 时 squash 掉即可。

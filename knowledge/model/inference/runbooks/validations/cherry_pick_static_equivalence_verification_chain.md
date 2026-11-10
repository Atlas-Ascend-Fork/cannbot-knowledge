---
type: Runbook
title: vllm-ascend 跨分叉分支 cherry-pick 框架 PR 的静态等价性验证链：merge-base/hunk 预判加四层验证（内容行、字节级、三方合并 SHA256、py_compile）
description: "把 vllm-project/vllm-ascend PR #14374（Support Omni-EPLB，7 提交 13 文件 +156/-31）cherry-pick 到含大量本地改动的 KV offload 特性分支时的完整可复核验证链：先核 merge-base（3da28f9414583d2d0b672a8f06d1fae142404bda 恰为 PR 首提交父节点且为目标分支祖先）并用 hunk 区域比对确认本地改动区（ascend_config.py、model_runner_v1.py +476/-28）与 PR 改动区（505-535、3738-3760）不重叠，7 提交零冲突落地；再用四层静态验证确认等价：13 文件 +/- 内容行与 PR 净 diff 逐字一致、11 个本地未改动文件与 PR head 字节级一致、2 个本地改动文件用 git merge-file 三方合并独立重算且 SHA256 与 cherry-pick 结果一致、py_compile 全部通过；推送 36d8a343..bd4eed1a 并经远端 ls-remote 验证 head=bd4eed1a。边界：全程静态等价性，ruff（PyPI 不可达）与 torch UT（无 torch）未执行，推送成功与远端 [PASSED] hooks 不等价于功能验证。"
tags:
- task.migration
- task.testing
- topic.quality.compatibility.version_migration
status: draft
sources: []
created_at: '2026-10-29T16:39:00Z'
updated_at: "2026-11-04T09:23:45Z"
platforms: []
---

# vllm-ascend 跨分叉分支 cherry-pick 框架 PR 的静态等价性验证链：merge-base/hunk 预判加四层验证（内容行、字节级、三方合并 SHA256、py_compile）

## 适用场景

- 适用框架与任务：vllm-ascend（vLLM 的昇腾 NPU 插件）跨分叉/跨特性分支移植上游或第三方 PR 的提交序列——本例把 vllm-project/vllm-ascend PR #14374 "Support Omni-EPLB"（CConory fork 的 eplb 分支，7 提交、13 文件 +156/-31，base rfc/vllm_cann，观察时 open 未合并）cherry-pick 到一个已有本地改动（layerwise KV offload，自 merge-base 起 233 文件 +30494/-2713，其中与 PR 重叠的文件只有 2 个）的分支 layerwise-offload-finalization。
- 目标：在不引入手工改动的前提下让 PR 变更精确落地，并用可机器复核的静态证据确认 cherry-pick 结果与 PR 净变更等价。
- 环境：Windows + git 2.55.0.windows.5；无 torch、无 NPU，验证手段限于 git、PowerShell 哈希计算与 py_compile。draft、平台未知（无设备参与）。

## 触发与观测

用户要求将 PR #14374 "代码以及功能准确无误" 地 cherry-pick 到 GitCode 上的对应分支。落地前先取得两项客观预判观测：

- merge-base 与 PR 提交覆盖观测（git merge-base HEAD pr-14374 及 git branch --contains 核查输出）：

```text
3da28f9414583d2d0b672a8f06d1fae142404bda
3da28f94 change state cache block to 16 to opt memory (#13686)
```

（PR 的 7 个提交 393a2dc2、113f6395、25bf6002、e3560c8f、6215908b、be80d5d0、87045319 均为 not-in-branch；merge-base 3da28f9414583d2d0b672a8f06d1fae142404bda 恰为 PR 最早提交 87045319 的父节点，也是目标分支的祖先。）

- 本地改动重叠观测（git diff --stat 3da28f94..HEAD -- <PR 涉及的 13 个文件>）：

```text
 vllm_ascend/ascend_config.py          |  56 +++--
 vllm_ascend/worker/model_runner_v1.py | 448 +++++++++++++++++++++++++++++++++-
 2 files changed, 476 insertions(+), 28 deletions(-)
```

即 13 个 PR 涉及文件中本地分支只改过 2 个（ascend_config.py 的 AscendConfig 区域、model_runner_v1.py 的 layerwise-offload 区域）；PR 的 hunks 位于 model_runner_v1.py 的 505-535 与 3738-3760 行及 ascend_config.py 的 EplbConfig 类（约 803 行起），与本地改动区域不重叠。

## 探针与操作

本轨迹实际执行的关键命令原文（自 PowerShell 包装中摘出）：

```text
git merge-base HEAD pr-14374
git cherry-pick -x 87045319
python -m py_compile $files
```

- cherry-pick 按提交时间从旧到新依次执行 87045319、be80d5d0、6215908b、e3560c8f、25bf6002、113f6395、393a2dc2（均带 -x 保留溯源）。第一个提交的落地输出：

```text
Auto-merging vllm_ascend/ascend_config.py
Auto-merging vllm_ascend/worker/model_runner_v1.py
[layerwise-offload-finalization 8a9d5efb] feat(eplb): integrate OmniPlanner two-stage initialization
 Author: kuang.wenwei <${PRIVATE_EMAIL_1}>
 Date: Sun Aug 16 09:02:51 2026 +0800
 4 files changed, 42 insertions(+), 2 deletions(-)
```

- 三方合并交叉验证对 2 个本地改动文件（ascend_config.py、model_runner_v1.py）独立重算，三方分别为 ours=本地基线 36d8a343、base=merge-base 3da28f94、other=PR head pr-14374，命令核心：

```text
git merge-file -p -L ours -L base -L other
```

（完整命令把 git show 导出的三方文件经 git merge-file 合并后与实际 cherry-pick 结果做 SHA256 比对。）

## 机制与判别

- cherry-pick 预判链成立并零冲突落地：PR #14374 的 merge-base 3da28f9414583d2d0b672a8f06d1fae142404bda 恰为 PR 首提交的父节点且是目标分支祖先；13 个 PR 涉及文件中本地分支仅改动 ascend_config.py 与 model_runner_v1.py（+476/-28），改动区域与 PR hunks 不重叠；7 个提交按序 git cherry-pick -x 全部干净应用。
- 四层静态等价性验证全部通过：13 个文件的 +/- 内容行与 PR 净 diff 逐字一致（CONTENT-IDENTICAL）；本地未改动的 11 个文件与 PR head 字节级一致（FILE-IDENTICAL-TO-PR）；2 个本地改动文件用 git merge-file 三方合并独立重算，SHA256 与 cherry-pick 结果一致（MATCH-NO-CONFLICT）；py_compile 13 个文件全部通过。

第一层：逐文件比对 PR 净 diff（3da28f94..pr-14374）与 cherry-pick 实际引入 diff（36d8a343..HEAD）的 +/- 内容行（原输出为 Windows CRLF 行尾）：

```text
CONTENT-IDENTICAL  vllm_ascend/ascend_config.py
CONTENT-IDENTICAL  vllm_ascend/eplb/adaptor/vllm_adaptor.py
CONTENT-IDENTICAL  vllm_ascend/eplb/core/eplb_utils.py
CONTENT-IDENTICAL  vllm_ascend/eplb/eplb_updator.py
CONTENT-IDENTICAL  vllm_ascend/eplb/omni_eplb_updator.py
CONTENT-IDENTICAL  vllm_ascend/model_loader/rfork/rfork_loader.py
CONTENT-IDENTICAL  vllm_ascend/quantization/methods/w4a16.py
CONTENT-IDENTICAL  vllm_ascend/quantization/methods/w4a16_mxfp4.py
CONTENT-IDENTICAL  vllm_ascend/quantization/methods/w4a4_mxfp4.py
CONTENT-IDENTICAL  vllm_ascend/quantization/methods/w4a8.py
CONTENT-IDENTICAL  vllm_ascend/quantization/methods/w4a8_mxfp4.py
CONTENT-IDENTICAL  vllm_ascend/quantization/methods/w8a8_dynamic.py
CONTENT-IDENTICAL  vllm_ascend/worker/model_runner_v1.py
```

第二层：本地未改动的 11 个文件与 PR head 逐字节比对（CRLF）：

```text
FILE-IDENTICAL-TO-PR  vllm_ascend/eplb/adaptor/vllm_adaptor.py
FILE-IDENTICAL-TO-PR  vllm_ascend/eplb/core/eplb_utils.py
FILE-IDENTICAL-TO-PR  vllm_ascend/eplb/eplb_updator.py
FILE-IDENTICAL-TO-PR  vllm_ascend/eplb/omni_eplb_updator.py
FILE-IDENTICAL-TO-PR  vllm_ascend/model_loader/rfork/rfork_loader.py
FILE-IDENTICAL-TO-PR  vllm_ascend/quantization/methods/w4a16.py
FILE-IDENTICAL-TO-PR  vllm_ascend/quantization/methods/w4a16_mxfp4.py
FILE-IDENTICAL-TO-PR  vllm_ascend/quantization/methods/w4a4_mxfp4.py
FILE-IDENTICAL-TO-PR  vllm_ascend/quantization/methods/w4a8.py
FILE-IDENTICAL-TO-PR  vllm_ascend/quantization/methods/w4a8_mxfp4.py
FILE-IDENTICAL-TO-PR  vllm_ascend/quantization/methods/w8a8_dynamic.py
```

第三层输出（2 个本地改动文件均无冲突且合并结果哈希与实际一致）：

```text
MATCH-NO-CONFLICT  vllm_ascend/ascend_config.py
MATCH-NO-CONFLICT  vllm_ascend/worker/model_runner_v1.py
```

第四层输出：`PY_COMPILE: ALL 13 FILES OK`

- 判别要点：完整 diff 的一次性整体 SHA256 比对会因上下文行号偏移不同而不一致（本轨迹首次整体比对即得到 DIFFERENT，属预期差异），不能据此判定 cherry-pick 失败；判别必须落到逐文件 +/- 内容行比对与独立三方合并重算。
- 推送 36d8a343..bd4eed1a 到 GitCode 成功，git ls-remote 验证远端 head 为 bd4eed1abafce94684058c849c89afc943f4d122；cherry-pick 保留原作者署名并附 (cherry picked from commit 393a2dc212462f419b590c22ca04045da48488bc) 溯源。溯源标注原文（git log -1 --format 输出）：

```text
kuang.wenwei <${PRIVATE_EMAIL_1}>
support A5 omni-eplb

(cherry picked from commit 393a2dc212462f419b590c22ca04045da48488bc)
```

推送输出：

```text
To https://gitcode.com/AlwinZzz/vllm-ascend-layerwise-offload.git
   36d8a343..bd4eed1a  layerwise-offload-finalization -> layerwise-offload-finalization
```

远端核验输出（git ls-remote）：

```text
bd4eed1abafce94684058c849c89afc943f4d122	refs/heads/layerwise-offload-finalization
```

## 验证信号

（全部为本轨迹内真实观测；平台：Windows 静态 git/py_compile；证据等级：tool_observed；单条轨迹单次观测）

- git merge-base 返回 3da28f9414583d2d0b672a8f06d1fae142404bda；PR 的 7 个提交均 not-in-branch。
- git diff --stat 显示本地分支在 13 个 PR 文件中仅改 2 个（+476/-28）；hunk 区域比对显示 PR hunks（505-535、3738-3760）与本地改动区不重叠。
- 7 个 cherry-pick 提交全部干净应用（Auto-merging 后无冲突标记），落地为 8a9d5efb、1de5581c、2682c49c、cc1db7e6、9e763d04、c2f643ef、bd4eed1a。
- 13 个文件逐项 CONTENT-IDENTICAL；11 个文件 FILE-IDENTICAL-TO-PR；2 个文件三方合并 MATCH-NO-CONFLICT 且 SHA256 相等；py_compile 返回 PY_COMPILE: ALL 13 FILES OK。
- git push 输出 36d8a343..bd4eed1a；git ls-remote 返回 bd4eed1abafce94684058c849c89afc943f4d122（哈希与 refs/heads/layerwise-offload-finalization 以制表符分隔，见上方原文块）。
- 未观测到的信号：ruff lint（PyPI 不可达，两次安装尝试分别 120000 ms、300000 ms 超时）、torch 单元测试（本机无 torch）、NPU 设备端功能与性能（无设备）。

## 适用与失效边界

- 适用前提：目标分支与 PR 存在共同 merge-base，且 PR 改动区与本地改动区不重叠（可先用本页的重叠预判命令核实）；满足时 cherry-pick 可零冲突落地，四层验证全部可机器复核。
- 失效条件：无共同祖先、改动区重叠需要手工合并、或三方合并出现冲突（MERGE-CONFLICT）时，本验证链不适用，必须人工审阅每个冲突解决，此时"内容行一致/字节一致"类判据不再可得。
- 语义边界：四层验证只证明 cherry-pick 引入的内容与 PR 净变更静态等价、语法可编译，不证明运行时功能、精度或性能正确；上游 PR 自身的功能正确性同样未被验证。宣称"功能准确无误"前必须补 torch UT 与 NPU 设备端验证。
- 版本边界：本页具体 hash（merge-base 3da28f9414583d2d0b672a8f06d1fae142404bda、基线 36d8a343、PR head 393a2dc212462f419b590c22ca04045da48488bc、结果 bd4eed1a）仅在对应代码线有意义；PR #14374 观察时为 open 未合并，采用前应核对上游最新状态。

---
{
  "type": "Runbook",
  "title": "npugraph_ex 捕获期 tagged event 报错与多图事件命名隔离（LongCat-Flash aclgraph 迁移）",
  "description": "在 Ascend NPU 上以 torch_npu/torchair 的 `npugraph_ex`（aclgraph capture & replay）后端运行带**多流并行**（注意力主流 + MoE/共享专家副流，经 `npu_stream_switch` / tagged event 同步）的 MoE 模型（本例 LongCat-Flash，含主模型 + MTP 双份 decode 图），从 reduce-overhead 形式迁移到 npugraph_ex 时。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-20T14:17:03Z",
  "platforms": []
}
---

# npugraph_ex 捕获期 tagged event 报错与多图事件命名隔离（LongCat-Flash aclgraph 迁移）

## 适用场景

在 Ascend NPU 上以 torch_npu/torchair 的 `npugraph_ex`（aclgraph capture & replay）后端运行带**多流并行**（注意力主流 + MoE/共享专家副流，经 `npu_stream_switch` / tagged event 同步）的 MoE 模型（本例 LongCat-Flash，含主模型 + MTP 双份 decode 图），从 reduce-overhead 形式迁移到 npugraph_ex 时，捕获阶段报 tagged event 断言错误的诊断与修复。迁移动机（用户报告）：reduce-overhead 叠加多流存在精度问题。环境：python3.10 + torch_npu/torchair（`torch_npu/dynamo/npugraph_ex`、`torch_npu/dynamo/torchair/ops/_tagged_event.py`）。

## 触发与观测

两类设备端报错（用户粘贴的 rank0 追溯，ERR99999 UNKNOWN application exception）：

1. 捕获期断言失败（两次复现，时间 21:01 与 21:14）：
```
File ".../torch_npu/dynamo/npugraph_ex/_acl_concrete_graph/acl_graph.py", line 1176, in capture
    captured_outputs = self.fx_forward(*args_list, node_info=self._updated_node_infos, is_capturing=True,
File ".../torch_npu/dynamo/torchair/ops/_tagged_event.py", line 35, in record_impl
    raise AssertionError(f"tagged event is None while tag is {tag}, ")
AssertionError: tagged event is None while tag is graph_2_arg0_1, tagged event record failed, please make sure you have created tag graph_2_arg0_1 with npu_create_tagged_event API.
```
崩溃点在 MTP warm-up 的 decode 捕获（`acl_graph.py capture → fx_forward → record_impl`）。

2. 改为按层创建事件后，MTP 模型构建时直接抛重复标签（21:34）：
```
File ".../torch_npu/dynamo/torchair/ops/_tagged_event.py", line 138, in _npu_create_tagged_event
    raise ValueError(f"tagged event tag {tag} is already in use")
ValueError: tagged event tag model_layers_0_moe_launch is already in use
```

## 探针与操作

- 全仓检索事件创建与记录点是否配对（rg 输出，逐字）：
  - `multi_stream_events = [tng.ops.npu_create_tagged_event(tag=f"longcat_ms_tag_{i}") for i in range(256)]`（模块级全局创建，modeling_longcat_flash.py:62）
  - `tng.ops.npu_record_tagged_stream(hidden_states_norm, "1")`（本仓 longcat，:1374）
  - `tng.ops.npu_record_tagged_stream(hidden_states, "11")`（参考实现 deepseek-v3.2-exp，:421）
- 对照参考实现 deepseek_r1 的按层事件模式（sed 输出，逐字）：
```
            if use_npugraph_ex_event:
                tng.ops.npu_record_tagged_stream(hidden_states, "11")
                tng.ops.npu_tagged_event_record(events[self.layer_idx])
```
- 失败路线（不可采用）：仅给记录点换别名张量（`hidden_states_norm_moe = hidden_states_norm`）不创建配对事件——第二次报错证明无效。
- 修复（两步）：
  1. 删除全局 `longcat_ms_tag_{i}` 事件表，改为每 DecoderLayer 按模块前缀派生创建：`self.moe_launch_event = tng.ops.npu_create_tagged_event(tag=f"{event_tag_prefix}_moe_launch")`（及对应的 moe_finish_event），并以 `use_npugraph_ex_event = self.enable_npugraph_ex and (self.enable_multi_stream > 0) and not self.enable_afd` 门控记录/等待调用。
  2. 主模型与 MTP 两套图会以相同 `model.layers.*` 前缀建层，触发重复标签；引入图级命名空间：`self.graph_event_namespace = kwargs.get("graph_event_namespace", "main")`，事件前缀改为 `f"{self.graph_event_namespace}_{prefix.replace('.', '_')}"`，MTP 侧传入不同命名空间。

## 机制与判别

- 捕获期 tag 被改写：dynamo 捕获把 `npu_record_tagged_stream(x, "1")` 的字符串标签重写为 `graph_<图id>_arg<参数序>_<原tag>` 形式（本例 `graph_2_arg0_1`）；`_tagged_event.py record_impl` 按改写后的 tag 查注册表，查不到即抛 AssertionError。因此 eager 下能跑的"任意字符串 tag + 独立事件表"写法在 npugraph_ex 捕获下必然失配——这与"事件对象是否存在"无关，别名张量方案无效的原因也在此。
- 重复标签：`_npu_create_tagged_event` 对同名 tag 全局去重；主模型与 MTP 模型各自实例化同前缀的层，第二个实例创建即抛 ValueError。命名空间前缀使两图的标签空间不相交。
- 可区分解释的取舍：deepseek 系参考实现"没报错"的原因是它们的记录点 tag 与事件创建按层配对（deepseek_r1 用 `events[self.layer_idx]` + 固定 tag "11"，主/MTP 不共享前缀），而不是它们仍在 reduce-overhead——`graph_utils.py` 与 `docs/cann/npu_graph_optimization.md` 均确认 npugraph_ex 是当前图模式路线，`acl_graph` 是待清理的历史命名。
- 未验证推断：tag 改写规则 `graph_2_arg0_1` 的精确编号语义（图序号/参数序号）由报错样本归纳，未读 torch_npu 源码确认。

## 验证信号

- 设备端错误原文（两次捕获断言 + 一次重复标签），用户粘贴的 rank0 追溯（等级：用户提供的运行日志）。
- 源码观测（工具输出）：事件创建/记录点 rg 配对结果、deepseek_r1 与 deepseek-v3.2-exp 参考片段（等级：源码读取）。
- 修改后 `python3 -m py_compile models/longcat-flash/models/modeling_longcat_flash.py` 通过（无输出，等级：静态检查）。
- **本轨迹内没有成功运行输出**：命名空间修复后未见新的运行验证；reduce-overhead+多流的精度问题（迁移动机）也未验证。

## 适用与失效边界

- 适用：npugraph_ex 捕获 + `npu_record_tagged_stream`/`npu_tagged_event_record`/`npu_tagged_event_wait` 多流同步的迁移场景；主模型与 MTP（或任何同前缀双图）共用 tagged event 的命名冲突。
- 失效/风险：tag 改写规则可能随 torch_npu 版本变化；修复仅静态验证，运行级（捕获成功 + 多流精度）尚未闭合，采用前必须板上重跑；eager 多流原语义（`npu_wait_tensor` 等）在 LongCat 侧被用户指出不可用，本文不覆盖 eager 侧等价写法。

## 附：断言存档

- npugraph_ex 捕获期 npu_record_tagged_stream(x, "1") 的字符串 tag 被 dynamo 改写为 graph_<图id>_arg<参数序>_<原tag>（本例 graph_2_arg0_1）；torch_npu/dynamo/torchair/ops/_tagged_event.py record_impl 按改写后 tag 查注册表，未用该 tag 调 npu_create_tagged_event 注册即抛 AssertionError: tagged event is None while tag is graph_2_arg0_1（两次复现，最终 ERR99999）。
- 首个迁移尝试失败的直接原因是全局事件表与记录点 tag 不匹配：模块级创建 256 个 longcat_ms_tag_{i} 事件，而记录点用字面量 "1"；eager 下可跑的任意字符串 tag 写法在 npugraph_ex 捕获下必然失配，仅给记录点换别名张量（hidden_states_norm_moe = hidden_states_norm）无效。
- 主模型与 MTP 两套模型实例用相同 model.layers.* 前缀按层创建事件时，_npu_create_tagged_event 抛 ValueError: tagged event tag model_layers_0_moe_launch is already in use；须以图级命名空间隔离（graph_event_namespace 默认 "main"，MTP 传不同值，事件前缀 f"{namespace}_{prefix.replace('.', '_')}"）。
- 可行修复参照 deepseek_r1 的按层事件配对模式（npu_record_tagged_stream(hidden_states, "11") + npu_tagged_event_record(events[self.layer_idx])）：为 LongCat 每层创建 prefix 派生的 moe_launch_event/moe_finish_event，并以 use_npugraph_ex_event = enable_npugraph_ex and (enable_multi_stream > 0) and not enable_afd 门控记录/等待。

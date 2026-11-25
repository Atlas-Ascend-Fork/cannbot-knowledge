---
{
  "type": "Runbook",
  "title": "Qwen3.5 enable_mm_all_reduce_base 触发 attn_tp_group KeyError：register_group 缺 return_name=True 致 HCCL 名未存储",
  "description": "Qwen3.5 35B MoE 推理（cann-recipes-infer），昇腾 A3 平台，TP4（qwen3_5_35b_tp4.yaml），eager 模式，分支 enable_mm_all_reduce。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# Qwen3.5 enable_mm_all_reduce_base 触发 attn_tp_group KeyError：register_group 缺 return_name=True 致 HCCL 名未存储

## 适用场景

- 平台范围依据：source 0 seq 4、source 0 seq 11的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

Qwen3.5 35B MoE 推理（cann-recipes-infer），昇腾 A3 平台，TP4（qwen3_5_35b_tp4.yaml），eager 模式，分支 enable_mm_all_reduce。在 yaml custom_params 配置 `enable_mm_all_reduce_base: True`（用 npu_mm_all_reduce_base 融合 TP matmul 与 all_reduce）后 warm-up prefill 阶段即报错。

## 触发与观测

- 执行 `bash executor/scripts/infer.sh –model qwen3_5 –yaml qwen3_5_35b_tp4.yaml`，warm-up prefill 阶段在 models/qwen3_5/models/modeling_qwen3_5_moe.py 第 106 行抛出（source 0 seq 4，用户粘贴日志）：

  `KeyError: “Communication group ‘attn_tp_group’ has no stored HCCL name. Groups with HCCL name: []”`

- `Groups with HCCL name: []` 表明 CommManager 的 `_group_names` 字典完全为空。

## 探针与操作

- 源码定位链（全部 tool_observed）：
  1. 第 106 行 `hcom = comm_manager.get_group_name(group_name)` 位于 `qwen3_5_prefill_mm_all_reduce`，被 `out_proj`/`o_proj`（传 `attn_tp_group`）与 `down_proj`（传 `shared_tp_group`）三处 prefill 调用点使用（source 0 seq 9/46/49/51/53）。
  2. `executor/core/config/comm_manager.py` `_register_group`（source 0 seq 41，逐字）：

     ```
         425	    def _register_group(self, group_config: CommGroupConfig) -> None:
         426	        """Run the config through build/reuse and stash the result under its logical name."""
         427	        group, hccl_name = self._get_or_create_group(group_config)
         428	        self._groups[group_config.name] = group
         429	        if group_config.return_name:
         430	            self._group_names[group_config.name] = hccl_name
     ```

  3. `init_parallel_comm_group`（source 0 seq 46，逐字节选）：attn_tp_group 注册不带 `return_name`；moe_ep_group/moe_ep_group_mc2 注册带 `return_name=True`：

     ```
             # Attention TP group
             self.comm_manager.register_group(
                 name="attn_tp_group",
                 group_num=self.world_size // self.attn_tp_size,
                 group_size=self.attn_tp_size,
             )
     ```

     ```
                 self.comm_manager.register_group(
                     name="moe_ep_group",
                     group_num=moe_ep_group_num,
                     group_size=self.moe_ep_size,
                     group_stride=moe_ep_group_num,
                     return_name=True,
                     group_type=moe_ep_group_type,
                 )
     ```

- 修复（source 0 seq 66/71 落盘、seq 76 回读确认）：给 attn_tp_group 与 shared_tp_group 两处 register_group 追加 `return_name=True`，其余注册不动。

## 机制与判别

- 机制：`_group_names` 只在 `return_name=True` 时写入；`get_group_name()` 依赖该字典。fused mm_all_reduce 路径是全仓仅有的两处 `get_group_name` 消费者之一（source 0 seq 56，逐字）：

  ```
  106:    hcom = comm_manager.get_group_name(group_name)
  2320:        moe_ep_group_name = self.comm_manager.get_group_name("moe_ep_group_mc2")
  ```

- 判别：`moe_ep_group_mc2` 注册时带 `return_name=True`，所以 mc2 通信域查询正常；只有新启用的 fused 路径查询未带 `return_name` 的 attn_tp_group/shared_tp_group 才崩溃——解释了"仅开 enable_mm_all_reduce_base 才报错"。
- 未验证推断：修复后代码已回读确认（seq 76），但轨迹内未复跑推理；return_name=True 路径会走 `init_comm_group_by_ranks(..., return_name=True)` 返回 HCCL 名（seq 41 源码可见），预期闭环但无运行证据。

## 验证信号

- 报错原文：用户粘贴日志（user_reported）；根因链路与修复：源码读取与编辑回读（tool_observed）。
- 无修复后运行验证；validation 层次为 source_read + 编辑回读，非端到端。

## 适用与失效边界

- 适用于 cann-recipes-infer 中使用 CommManager + npu_mm_all_reduce_base 融合的模型接入：任何需要 `get_group_name()` 取 HCCL 通信名的消费方，其通信组注册必须带 `return_name=True`。
- 修复仅覆盖 attn_tp_group/shared_tp_group；若后续 fused 路径扩展到 embed_tp/lmhead_tp/moe_tp，同样需要补 return_name（未验证）。
- 轨迹内未运行验证；采纳前应复跑 warm-up prefill 确认 KeyError 消失且精度正常。

## 附：断言存档

- Qwen3.5（cann-recipes-infer，A3 平台，tp4）在 yaml 配置 enable_mm_all_reduce_base: True 后，warm-up prefill 阶段于 modeling_qwen3_5_moe.py:106 抛 KeyError：Communication group 'attn_tp_group' has no stored HCCL name. Groups with HCCL name: []。根因：init_parallel_comm_group 注册 attn_tp_group/shared_tp_group 时未传 return_name=True，而 CommManager._register_group 只在 group_config.return_name 为真时才把 HCCL 名写入 _group_names 字典（executor/core/config/comm_manager.py:425-430），qwen3_5_prefill_mm_all_reduce 里 get_group_name("attn_tp_group") 查不到即 KeyError（触发与报错为用户粘贴日志，根因链路为源码 tool_observed）。
- 判别证据：全仓仅两处 get_group_name 调用——modeling 第 106 行（fused mm_all_reduce 路径，取 attn_tp_group/shared_tp_group）与第 2320 行（取 moe_ep_group_mc2）；moe_ep_group 与 moe_ep_group_mc2 注册时带 return_name=True，其余 attn_tp/embed_tp/lmhead_tp/shared_tp/moe_tp 均未带。这解释了为何只有开启 enable_mm_all_reduce_base 的 fused 路径报错、mc2 通信域正常（源码 tool_observed）。
- 修复：给 attn_tp_group 与 shared_tp_group 两处 register_group 追加 return_name=True（编辑落盘并回读确认最终代码）；轨迹内未复跑推理验证修复效果（validation 缺口，属于源码级修复未运行闭合）。

```text
106:    hcom = comm_manager.get_group_name(group_name)
2320:        moe_ep_group_name = self.comm_manager.get_group_name("moe_ep_group_mc2")
```

```text
425	    def _register_group(self, group_config: CommGroupConfig) -> None:
426	        """Run the config through build/reuse and stash the result under its logical name."""
427	        group, hccl_name = self._get_or_create_group(group_config)
428	        self._groups[group_config.name] = group
429	        if group_config.return_name:
430	            self._group_names[group_config.name] = hccl_name
```

```text
2824	        # Attention TP group
2825	        self.comm_manager.register_group(
2826	            name="attn_tp_group",
2827	            group_num=self.world_size // self.attn_tp_size,
2828	            group_size=self.attn_tp_size,
```

```text
2865	            self.comm_manager.register_group(
2866	                name="moe_ep_group",
2867	                group_num=moe_ep_group_num,
2868	                group_size=self.moe_ep_size,
2869	                group_stride=moe_ep_group_num,
2870	                return_name=True,
2871	                group_type=moe_ep_group_type,
```

```text
报错信息是KeyError: “Communication group ‘attn_tp_group’ has no stored HCCL name. Groups with HCCL name: []”
```

```text
2824	        # Attention TP group
2825	        self.comm_manager.register_group(
2826	            name="attn_tp_group",
2827	            group_num=self.world_size // self.attn_tp_size,
2828	            group_size=self.attn_tp_size,
2829	            return_name=True,
```

```text
2846	        # Shared Expert TP group
2847	        if self.shared_tp_size > 1:
2848	            self.comm_manager.register_group(
2849	                name="shared_tp_group",
2850	                group_num=self.world_size // self.shared_tp_size,
2851	                group_size=self.shared_tp_size,
2852	                return_name=True,
```

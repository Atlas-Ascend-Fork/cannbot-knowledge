---
type: Runbook
title: recipes专用：主模型与草稿的专家通信域隔离
description: 仅适用于 recipes/CANN Executor 的 DSpark MC2/MegaMoE 隔离策略：核对禁止物理复用、实际通信对象及按模型角色选择的消费者。
tags:
- task.debugging
- topic.parallelism
- topic.speculative_decoding
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:37:06Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：主模型与 DSpark 独立 EP 域
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# recipes专用：主模型与草稿的专家通信域隔离

## 适用性与框架边界

本卡创建独立专家通信域的具体步骤仅适用于 recipes/CANN Executor 的 DSpark MC2/MegaMoE 分支，不能据此要求原生 vLLM 为主模型与草稿各建一套物理域。

通用原则：逻辑通信组名、rank 成员、实际 communicator 对象与配套 buffer 的归属是不同维度，应按目标后端的资源合同核对。

必要条件：下文操作以采用该 CommManager 缓存和 MC2/MegaMoE 消费路径为前提。两个模型是否需要独占 communicator 或 buffer 取决于实际后端、并发和生命周期合同；相同成员不自动要求隔离，也不自动允许共享。

recipes 专属操作：`allow_physical_reuse=False`、DSpark 专属组、MC2 的 HCCL 名称/buffer 与 MegaMoE context 选择共同实现这里选定的缓存及资源隔离策略，不是“两模型必须两组”的通用原则。

vLLM 读者应查自身分布式组创建/复用、MoE 通信参数和图执行准备的资源生命周期职责，依据其后端合同决定共享或隔离。不要照搬本卡禁用物理复用；没有 vLLM 接入、通信运行或版本兼容验证。

## 现象

token 是分词后的序列元素，hidden 是模型在该位置的特征向量。MoE（混合专家）层先由 router 为每个 token 的 hidden 向量选择专家，再把 token 发到持有该专家的设备，执行专家计算后把结果送回原 token 行。专家并行（EP）分的是专家集合；张量并行（TP）分的是一个专家内部的矩阵轴。EP dispatch/combine 的数据通常带有 token、专家编号和恢复行顺序的路由信息，不能只看普通 hidden 张量尺寸。

DSpark 是该 recipes/CANN Executor 适配的草稿模型。推测解码中草稿产生候选，主模型负责验证与接受流程；两套模型可能在同一批设备进程上运行各自的 MoE。rank 是进程编号，参与通信的 rank 列表定义成员；通信域则还包含实际后端 communicator 及配套资源。两个逻辑名称即使不同，通信管理器也可能按相同成员和属性复用同一个物理对象。

本卡的触发是核对 recipes 已选定的主模型/草稿专家通信隔离策略是否贯穿注册与消费者。固定源码为 DSpark 的 MC2（专家 dispatch/combine 通信路径）和 MegaMoE（另一 MoE 后端）创建独立域，并按模型角色选用。没有本次硬件死锁或错误返回记录；这里不能把“需要核对隔离”升级为已经复现并修好的 hang。

## 适用场景

仅用于 recipes/CANN Executor 当前 V4.1 的 DSpark EP 组注册、MC2 参数和 MegaMoE context 静态排查。目标 Ascend 950 的 MC2 group_type 为 3；low_latency_tp 路径不使用该 MC2 dispatch/combine，因此跳过它的组创建。MegaMoE 专属 EP 组只在 enable_mega_moe 且 moe_ep_size>1 时注册。

源码目标平台 Ascend 950，CANN 运行版本未知；适用粒度 exact_task，路线 recommended_fastpath，仅指遵守现有隔离契约。可迁移的是区分逻辑组名、物理通信对象和资源所有者的检查方法；其它框架是否复用 communicator、是否需独占缓冲区，必须读其后端契约。

## 判别方法

在这条 recipes 路径中找三个入口：MoE dispatch/combine 的参数构造、通信组/communicator 创建与缓存、草稿模型构造。沿“注册→解析→消费者”记录模型角色、逻辑名、成员顺序、TP/EP 编号、后端通信标识及 buffer 归属。

1. 先确认走的是 EP 通信路径。若是 low_latency_tp 的基础 MoE TP，不能用本卡的独立 MC2 组去解释它的输出问题。确认 MegaMoE 开关与 EP 度之后，再查相应组是否应存在。
2. 检查 recipes 选定的注册参数与缓存策略。此处 DSpark 两组都显式 allow_physical_reuse=False；MC2 还请求真实 HCCL 名称、计算出的 buffer 大小和平台 group_type。只有改逻辑名称而继续按成员/属性命中缓存，不满足当前隔离选择。
3. 检查消费者。MC2 的 set_mc2_kwargs 按层的 is_mtp（此实现中标记草稿/提案层的内部标志）选择主模型/草稿组，将解析后的通信标识同时写入 dispatch 与 combine；MegaMoE 构造时也按模型角色传 ep_group_name。注册正确但消费者仍取主组，隔离没有生效。
4. 检查创建顺序与生命周期。所有 world rank 应按相同顺序参与子组创建，各 rank 只保留自己所属组。记录实际 communicator 标识，排除“只打印组名”的假隔离；再检查资源释放、流依赖与 token 行恢复。本卡只证实创建/选择分支，不提供这些运行结论。

**教学推演（非 NPU 实测）**：仅演示分组算术：设 4 个进程，专家内部 TP=2、EP=2；这不是已验证的部署配置。按本实现 stride=2 的布局，EP 成员是 [0,2] 与 [1,3]；global rank 2 的 EP 编号为 2//2=1、TP 编号为 2%2=0。主模型与草稿可以都在 [0,2] 上发 token；在这里选定的 recipes 隔离策略下，消费者仍须分别解析各自通信域。其它后端可依据自身合同选择共享。若缓存键只由相同成员及 HCCL 属性组成，给草稿改一个业务名称仍可能取回主模型对象；本实现的禁止复用参数让该分支重新创建。该推演解释对象隔离，不能证明共享一定导致死锁，也不能证明独立域消除所有通信问题。

复验应先比对注册成员和消费者实际标识，再在目标环境分别运行主模型与草稿的 dispatch→专家→combine，核对 token 行与路由结果；再验证二者一起运行时的资源生命周期。若已独立且单独路径仍失败，转查路由、buffer 容量、集体通信顺序及流同步。以下仅是 recipes 原仓可选导航：

```bash
rg -n 'init_parallel_comm_group' models/deepseek_v4_1/models/modeling_dspark.py
```

## 完整代码

以下仅为 recipes/CANN Executor 的完整源码对照；保留逐块导读用于核验，外部框架无需采用其目录、类名或配置结构。

<details>
<summary>展开 recipes 参考实现：完整代码与逐块导读</summary>

以下保留固定源码中的完整函数或因果块；块外导读说明它们怎样连接。

`init_parallel_comm_group` 先建公共组，再建 Markov 组及两类草稿 EP 组。本卡关注后半部分：group_num=moe_tp_size、group_size=moe_ep_size、group_stride=moe_tp_size 共同决定每个 EP 子组成员；allow_physical_reuse=False 决定物理对象不从缓存取回。

```python
    def init_parallel_comm_group(self):
        super().init_parallel_comm_group()
        markov_lmhead_tp_size = int(
            self.infer_config.speculative_config.markov_lmhead_tp_size
        )
        if markov_lmhead_tp_size <= 0 or self.world_size % markov_lmhead_tp_size != 0:
            raise ValueError(
                f"markov_lmhead_tp_size={markov_lmhead_tp_size} must be positive "
                f"and divide world_size={self.world_size}."
            )
        if markov_lmhead_tp_size > 1:
            self.comm_manager.register_group(
                name="markov_lmhead_tp_group",
                group_num=self.world_size // markov_lmhead_tp_size,
                group_size=markov_lmhead_tp_size,
                platform_version=self.platform_version,
            )

        # create independent ep group for dspark megamoe and mc2
        platform_version = self.platform_version
        if not self.low_latency_tp:
            moe_ep_mc2_group_type = None if self.platform_version != PlatformVersion.ASCEND_950 else 3
            is_full_mesh_v2 = self.platform_version != PlatformVersion.ASCEND_950
            hccl_buffer_size = calc_moe_hccl_buffer_size(
                self.infer_config, self.config, is_full_mesh_v2=is_full_mesh_v2
            )
            self.comm_manager.register_group(
                name="dspark_moe_ep_group_mc2",
                group_num=self.moe_tp_size,
                group_size=self.moe_ep_size,
                group_stride=self.moe_tp_size,
                return_name=True,
                allow_physical_reuse=False,
                hccl_buffer_size=hccl_buffer_size,
                group_type=moe_ep_mc2_group_type,
                platform_version=platform_version,
            )
        if self.enable_mega_moe and self.moe_ep_size > 1:
            self.comm_manager.register_group(
                name="dspark_megamoe_ep_group",
                group_num=self.moe_tp_size,
                group_size=self.moe_ep_size,
                group_stride=self.moe_tp_size,
                return_name=True,
                allow_physical_reuse=False,
                platform_version=platform_version,
            )
```

`set_mc2_kwargs` 把模型角色转换成 MC2 使用的后端名称，并构造 dispatch_kwargs/combine_kwargs。`ep_rank_id=global_rank//moe_tp_size` 是专家分片坐标，`tp_rank_id=global_rank%moe_tp_size` 是专家内部矩阵分片坐标。`quant_mode/y_dtype` 控制通信负载表示，不改变组的所有权；两次通信必须拿到相配的域与编号。

```python
    def set_mc2_kwargs(self):
        global_rank = dist.get_rank()
        mc2_group_name = "dspark_moe_ep_group_mc2" if self.is_mtp else "moe_ep_group_mc2"
        moe_ep_group_name = self.comm_manager.get_group_name(mc2_group_name)
        if self.gmm_quant_mode not in self.dispatch_quant_mode:
            quant_mode = self.dispatch_quant_mode["w16a16"]
        else:
            quant_mode = self.dispatch_quant_mode[self.gmm_quant_mode]
        enable_smooth_scale = False
        self.dispatch_kwargs = {
                "x_active_mask": None,
                "expert_shard_type": 0,
                "shared_expert_rank_num": self.shared_expert_rank_num,
                "moe_expert_num": self.n_routed_experts,
                "global_bs": 0,
                "scales": self.experts.smooth_scale_1 if enable_smooth_scale else None,
                "quant_mode": quant_mode,
                "group_ep": moe_ep_group_name,
                "ep_world_size": self.moe_ep_size,
                "ep_rank_id": global_rank // self.moe_tp_size,
                "group_tp": moe_ep_group_name,
                "tp_world_size": self.moe_tp_size,
                "tp_rank_id": global_rank % self.moe_tp_size,
            }
        if self.gmm_quant_mode == "w4a4mxfloat4":
            self.dispatch_kwargs['y_dtype'] = torch_npu.float4_e2m1fn_x2
        elif quant_mode in (self.dispatch_quant_mode["w8a8float8"], self.dispatch_quant_mode["w8a8mxfloat8"]):
            self.dispatch_kwargs['y_dtype'] = torch.float8_e4m3fn
        self.combine_kwargs = {
                "x_active_mask": None,
                "expert_shard_type": 0,
                "shared_expert_rank_num": self.shared_expert_rank_num,
                "moe_expert_num": self.n_routed_experts,
                "global_bs": 0,
                "group_ep": moe_ep_group_name,
                "ep_world_size": self.moe_ep_size,
                "ep_rank_id": global_rank // self.moe_tp_size,
                "group_tp": moe_ep_group_name,
                "tp_world_size": self.moe_tp_size,
                "tp_rank_id": global_rank % self.moe_tp_size
            }
        if self.platform_version != PlatformVersion.ASCEND_950:
            self.dispatch_kwargs["comm_alg"] = "fullmesh_v2"
```

MegaMoE context 构造块以 ep_group_name 连接模型角色与后端资源。输入还有最大本地 prefill token 数；返回 context/backend 供层使用，不能只在注册处看到 dspark 名称就假定这里也选对了。

```python
        self.megamoe_context = None
        self.megamoe_backend = None
        self.selected_op_kernels = {}
        if self.enable_mega_moe:
            self.update_op_kernel_dict(("megamoe",))
            self.megamoe_context, self.megamoe_backend = OpKernel.megamoe(
                config,
                get_max_local_prefill_tokens(self.infer_config, config.sliding_window),
                self.comm_manager,
                ep_group_name="dspark_megamoe_ep_group" if is_mtp else "megamoe_ep_group",
            )
            kwargs["megamoe_backend"] = self.megamoe_backend
```

`CommManager.register_group` 将业务名和拓扑参数变成 CommGroupConfig，再交给实际注册。若同名已注册会直接返回原对象，因此复验还要排除名称重复导致的旧配置残留。自定义 subgroups 直接决定成员，否则由数量/大小/stride 生成。

```python
    def register_group(
        self,
        name: str,
        group_num: Optional[int] = None,
        group_size: Optional[int] = None,
        group_stride: int = 1,
        start_ranks: Optional[List[int]] = None,
        subgroups: Optional[List[List[int]]] = None,
        hccl_buffer_size: Optional[int] = None,
        group_type: Optional[int] = None,
        return_name: bool = False,
        allow_physical_reuse: bool = True,
        platform_version: Optional[PlatformVersion] = None,
    ) -> Optional[dist.ProcessGroup]:
        """Register a model-specific communication group.

        This may be called directly by model constructors.  The default process
        group signature is cached during ``CommManager`` construction so
        world-sized business groups can physically reuse it.
        ``subgroups`` may be supplied directly for custom topologies.  Otherwise
        ``group_num`` / ``group_size`` / ``group_stride`` generate subgroups.
        ``start_ranks`` may be supplied for custom regular-stride topologies
        such as DP/PP/TP rank layouts.
        """
        if name in self._groups:
            logger.info(
                f"CommManager: group '{name}' already registered, "
                "skip duplicate registration"
            )
            return self._groups[name]

        if subgroups is None:
            if group_num is None or group_size is None:
                raise ValueError(
                    f"{name}: either subgroups or both group_num and group_size must be provided"
                )
            if group_num * group_size != self.config.world_size:
                raise ValueError(
                    f"{name}: group_num * group_size must equal "
                    f"world_size={self.config.world_size}, got "
                    f"{group_num} * {group_size}"
                )
            subgroups = self._build_strided_subgroups(
                group_num=group_num,
                group_size=group_size,
                group_stride=group_stride,
                start_ranks=start_ranks,
            )

        group_config = CommGroupConfig(
            name=name,
            subgroups=subgroups,
            hccl_buffer_size=hccl_buffer_size,
            group_type=group_type,
            platform_version=platform_version or self.platform_version,
            world_size=self.config.world_size,
            return_name=return_name,
            allow_physical_reuse=allow_physical_reuse,
        )
        self._register_group(group_config)
        return self._groups[name]
```

`_get_or_create_group` 遍历子组并根据成员与 HCCL 属性计算缓存键。`can_reuse` 决定是否读写 _physical_cache；禁止复用时仍创建物理组，包括退化的单 rank 情况。`chosen_group/chosen_name` 只保留当前 global_rank 所在子组的结果，返回给后续消费者。

```python
    def _get_or_create_group(
        self, group_config: CommGroupConfig
    ) -> Tuple[Optional[dist.ProcessGroup], Optional[str]]:
        """Resolve the ProcessGroup (and optional HCCL comm name) for this config.

        Two-stage flow:
            Stage 1  Materialization: decide whether a real HCCL group is
                    needed at all.  Single-rank subgroup -> None.  World
                    subgroup with default HCCL params -> shortcut to
                    ``default_pg``.  Otherwise fall through to stage 2.
            Stage 2  Physical reuse: ``allow_physical_reuse=False`` bypasses
                    the cache (mc2 always fresh).  Otherwise consult
                    ``_physical_cache`` by signature.

        Collective protocol: every world rank iterates ``subgroups`` in the
        same order and participates in every ``new_group`` call.  Each rank
        only keeps the ProcessGroup corresponding to the subgroup it belongs
        to.

        Returns a ``(group, hccl_name)`` pair; ``hccl_name`` is ``None``
        unless the config requested it and the group was actually built.
        """
        global_rank = self.config.global_rank

        chosen_group: Optional[dist.ProcessGroup] = None
        chosen_name: Optional[str] = None

        for ranks in group_config.subgroups:
            group = None
            hccl_name = None
            key = self._compute_physical_key(ranks, group_config)
            can_reuse = group_config.allow_physical_reuse
            # Ordinary single-rank logical groups do not need a real HCCL
            # ProcessGroup. Exclusive groups (MC2) still materialize so they
            # can own a dedicated communicator even when their ranks list is
            # degenerate.
            needs_physical_group = not can_reuse or len(ranks) > 1

            # Reusable physical groups are keyed by ranks + HCCL attributes.
            # Cache misses and exclusive groups share the same creation path.
            if needs_physical_group and can_reuse and key in self._physical_cache:
                group = self._physical_cache[key]
                hccl_name = (
                    get_group_name(group, global_rank)
                    if group_config.return_name and global_rank in ranks
                    else None
                )
            elif needs_physical_group:
                result = init_comm_group_by_ranks(
                    ranks,
                    global_rank=global_rank,
                    group_name=group_config.name,
                    hccl_buffer_size=group_config.hccl_buffer_size,
                    group_type=group_config.group_type,
                    platform_version=group_config.platform_version.value,
                    return_name=group_config.return_name,
                )
                group, hccl_name = (
                    result if group_config.return_name else (result, None)
                )
                if can_reuse:
                    self._physical_cache[key] = group

            if global_rank in ranks:
                chosen_group = group
                chosen_name = hccl_name

        return chosen_group, chosen_name
```

</details>

## 设计决策

当前实现以独立通信对象分隔主模型与草稿的 MC2/MegaMoE 资源，并让消费者显式选择。这是一项缓存/资源隔离策略选择，不能推导所有主模型与草稿必须使用两套物理域。新增通信域需要额外通信/缓冲资源，本卡没有容量或时延对比。is_mtp 是复用代码的内部草稿标志，不表示 V4.1 支持原生 MTP backend。

## 系统信息

草稿注册在 `models/deepseek_v4_1/models/modeling_dspark.py`，MoE 消费在 `models/deepseek_v4_1/models/modeling_deepseek.py`，缓存与物理创建在 `executor/core/config/comm_manager.py`。三处构成同一条资源所有权链。

## 预防

为每种 MoE 后端同时保留模型角色、业务名、成员顺序、实际通信标识和资源生命周期记录。并行布局变化后重新创建/核对组；不得用“两个业务名不同”代替物理隔离检查。

## 验证信号

固定源码核对覆盖 DSpark 专属组注册、MC2 按角色选名、MegaMoE context 选域，以及 CommManager 的注册与物理缓存分支。它证实当前实现主动禁止复用，尚未测量通信、对称缓冲区或并发运行行为。（来源平台：源码目标 950；证据等级：artifact_verified。）

## 失效边界

未执行 950 EP、MC2、MegaMoE 或 SymmBuffer。没有本次 hang 复现、NPU 推理、跨 rank 通信或内存/性能结果；独立域不证明所有生命周期、流依赖和路由错误均已消除。基础 MoE TP 路径不使用本卡的 EP 通信，其他框架的资源隔离要求也未验证。

## 坏实践

在该 recipes 隔离策略下只新增逻辑字符串却复用主模型物理域；只改注册不改 dispatch/combine 消费者；按全局 rank 直接充当 EP 组内 rank；把 is_mtp 标志当成原生 MTP 功能支持；将静态隔离分支说成已修复硬件 hang。

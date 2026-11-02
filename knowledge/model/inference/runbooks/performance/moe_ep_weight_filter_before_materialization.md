---
type: Runbook
title: Kimi K3 EP 权重加载缓慢：在 safetensors 读取前过滤远端专家
description: 检查专家权重是否在 get_tensor 后才被跳过；按当前 EP rank 的专家区间提前过滤，保留非专家权重并用实际读取键集合验收。
tags:
- task.debugging
- task.optimization
- topic.memory
- topic.mixture_of_experts
status: stable
sources: []
created_at: '2026-10-30T03:14:37Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
---

# Kimi K3 EP 权重加载缓慢：在 safetensors 读取前过滤远端专家

## 现象

Kimi K3 使用 EP 分配专家后，每个 rank 最终只保存自己负责的专家，但启动时仍可能从 safetensors 读取并物化远端专家的权重和 scale。表现是模型参数看起来已正确切分，加载耗时、Host 内存或 I/O 却没有按预期减少。此时只统计模型中的参数数量会错过问题：丢弃张量发生得再晚，也不能撤销已经完成的 `get_tensor()` 读取。

## 适用场景

- 目标平台为 950PR/DT，问题发生在 K3 checkpoint 加载阶段，与 Prefill/Decode 执行模式无关。
- 权重入口为 safetensors 迭代器，模型能提供当前 EP rank 的静态专家半开区间 `[local_expert_start, local_expert_end)`。
- 部署可能使用公共 `DefaultModelLoader`，也可能使用 K3 本地 loader；必须沿实际 `get_model_loader` 和 `get_all_weights` 查清当前入口。CANN/torch_npu 具体版本不是本次已确认的过滤条件，不能据此推导通用性能收益。
- 不处理动态 EPLB 重映射、非连续专家所有权或其他 checkpoint 格式的读取；这些情况必须按真实分配方式重新定义过滤器。

## 根因与调用链

有效切入点是 `safe_open()` 后枚举名称、`get_tensor(name)` 前作决定。正常链路为：模型 `should_load_weight(name)` → loader 取得 callable → 每个主/附加权重 source 传给 iterator → iterator 先判断 name → 只为保留的 name 调用 `get_tensor()` → yield 给模型加载逻辑。

`should_load_weight` 的判断依赖**模型 EP 组内的专家分配**，不是全局进程 rank。Tensor 本身尚未读取，因此这里只能依据名称和已知分配作决定；不能在过滤器内先读张量检查内容。

## 判别方法

1. 在实际 safetensors 对象的 `get_tensor` 边界记录调用键集合，另外记录 iterator yield 集合和最终入模集合。这三层分别回答“读了哪些”“向上游交了哪些”“模型用了哪些”。本卡要求远端专家在第一层就消失。
2. 核对实际模型对象上存在可调用的 `should_load_weight`；若 `getattr(..., None)` 得到空值，整个链路会按未过滤路径执行。
3. 对主权重和 `secondary_weights` 分别检查是否传递同一个 filter，防止只优化主 source。
4. 检查名称形态：正则匹配路径中的 `.experts.<整数>.` 或开头 `experts.<整数>.`。`shared_experts`、attention、embedding 等不匹配的名称必须保留；不能使用简单包含 `expert` 的规则删除共享专家。
5. 对本地区间两端、远端专家、嵌套模型前缀、每个本地专家的 weight/scale 成组检查。过滤错误可能先表现为缺 scale，而非立即缺 weight。

## 完整机制代码

以下是读取前过滤的完整匹配单元，所在模块已有 `re` 导入。正则中的点是路径分隔符，不是匹配任意字符；数字专家 ID 采用左闭右开判断：

```python
_EXPERT_WEIGHT_PATTERN = re.compile(r"(?:^|\.)experts\.(\d+)\.")


def is_local_expert_weight(name: str, expert_start: int, expert_end: int) -> bool:
    """Keep non-expert weights and experts owned by this EP rank."""
    match = _EXPERT_WEIGHT_PATTERN.search(name)
    if match is None:
        return True
    return expert_start <= int(match.group(1)) < expert_end
```

模型向 loader 暴露的完整方法如下。`local_expert_start/end` 应在模型构造时由实际 EP 分配确定；不要把调用端的全局 rank 临时代入：

```python
def should_load_weight(self, name: str) -> bool:
    return is_local_expert_weight(
        name, self.local_expert_start, self.local_expert_end
    )
```

原 iterator 会对所有 key 立即执行读取：

```python
def safetensors_weights_iterator(
    hf_weights_files: List[str],
    use_tqdm_on_load: bool,
) -> Generator[Tuple[str, torch.Tensor], None, None]:
    """Iterate over the weights in the model safetensor files."""
    for st_file in tqdm(
            hf_weights_files,
            desc="Loading safetensors checkpoint shards",
            disable=not enable_tqdm(use_tqdm_on_load),
            bar_format=_BAR_FORMAT,
    ):
        with safe_open(st_file, framework="pt") as f:
            for name in f.keys():
                param = f.get_tensor(name)
                yield name, param
```

加入可选 callable 后，过滤发生在 `get_tensor` 前，保持无 filter 时的行为：

```python
def safetensors_weights_iterator(
    hf_weights_files: List[str],
    use_tqdm_on_load: bool,
    weight_filter: Optional[Callable[[str], bool]] = None,
) -> Generator[Tuple[str, torch.Tensor], None, None]:
    """Iterate over the weights in the model safetensor files."""
    for st_file in tqdm(
            hf_weights_files,
            desc="Loading safetensors checkpoint shards",
            disable=not enable_tqdm(use_tqdm_on_load),
            bar_format=_BAR_FORMAT,
    ):
        with safe_open(st_file, framework="pt") as f:
            for name in f.keys():
                if weight_filter is not None and not weight_filter(name):
                    continue
                param = f.get_tensor(name)
                yield name, param
```

这些函数依赖所在模块的 `List`、`Optional`、`Callable`、`Generator`、`Tuple`、`torch`、`tqdm` 和 `safe_open`，应放回相应 loader 实现中使用，不能单独复制一个函数便宣称模型已经接通过滤。

## 处理步骤与版本分支

公共 loader 路线要同时改通 `get_all_weights()` 和 `_get_weights_iterator()`：前者从模型取得 filter，对 primary 和 secondary source 传递；后者把 filter 交给 `safetensors_weights_iterator`。loader 给名称添加 `source.prefix` 的位置在 iterator 之后，因此要核对过滤器收到的是当前 source 内的原始 key。

K3 本地 loader 路线把同一机制收敛在模型目录，避免要求所有共享 loader 的模型都具备 K3 专家命名。其读取方法如下，展示无 filter 时回到父类、有 filter 时在读取前判断的完整分支：

```python
def _get_weights_iterator(self, source, weight_filter=None):
    if weight_filter is None:
        yield from super()._get_weights_iterator(source)
        return

    _, weight_files, _ = self._prepare_weights(
        source.model_or_path,
        source.revision,
        source.fall_back_to_pt,
        source.allow_patterns_overrides,
    )
    if self.counter_before_loading_weights == 0.0:
        self.counter_before_loading_weights = time.perf_counter()
    for weight_file in tqdm(
        weight_files,
        desc="Loading safetensors checkpoint shards",
        bar_format="{desc}: {percentage:3.0f}% Completed | {n_fmt}/{total_fmt} "
                   "[{elapsed}<{remaining}, {rate_fmt}]\n",
    ):
        with safe_open(weight_file, framework="pt") as checkpoint:
            for name in checkpoint.keys():
                if weight_filter(name):
                    yield source.prefix + name, checkpoint.get_tensor(name)
```

部署时选择已经存在的那条入口完成传递，不同时引入两套重叠改造。`get_model_loader(with_ckpt)` 若选择 dummy loader，本卡的 checkpoint 过滤逻辑没有执行机会，dummy 启动成功也不是读取过滤的证据。

## 验证信号与验收步骤

已经核对代码中的正则、半开区间、可选 filter 和 `get_tensor` 的先后关系；现有测试定义用假 `safe_open` 累计 `loaded` 名称，并同时断言实际读取键与 yield 键。这是可复用的判别方法，不是本次执行过测试的声明；本轮未运行上游 CPU 测试或 NPU 加载 benchmark。

在部署版本中执行以下验收并保存真实输出：

| 检查 | 应满足的信号 | 失败时回查 |
| --- | --- | --- |
| 区间边界 | start 保留，end 排除，区间外专家排除 | EP 区间计算、正则和 key 前缀 |
| 共享与非专家权重 | shared expert、attention 等全部保留 | 误用包含 `expert` 的宽泛匹配 |
| 真实读取 | 远端专家不出现在 `get_tensor` 调用集合 | filter 未进入真实 loader、判断位置过晚 |
| 组内完整性 | 所有本地专家 weight/scale 和其他必需张量齐全 | 权重命名差异、secondary source 传递 |
| 数值与启动资源 | 原精度条件下模型正确，再比较加载耗时与峰值 | 缺失键、错误 EP 分配、测量窗口差异 |

## 设计决策与坏实践

过滤器只接受名称，避免为了做决定先物化 Tensor；无 filter 时保持原迭代语义，便于回退和兼容其他模型。用实际读取集合验收，能区分“迭代器真的没读”与“模型后来没用”。

不要在 `yield` 后过滤，也不要只在模型赋值处 `continue`；这两种方式都已付出读取代价。不要认为每个 safetensors 文件都不再打开：该实现仍遍历文件和 key，只跳过被排除 key 的 `get_tensor`，它不是按文件裁剪或网络下载优化。

## 回退与失效边界

禁用 filter 可以恢复全量读取，再由原模型加载逻辑挑选参数；这样便于分离“过滤错了”与“原来就不能加载”，代价是恢复多余 I/O。回退后仍要做缺失键与精度检查，不能只以不再报错为准。

尚未确认的边界包括非连续/动态专家映射、不同 checkpoint key 规则、附加 source 的特殊前缀语义，以及当前环境的真实耗时和内存收益。缺少这些实测时，只能采用读取集合层面的结论，不能给出提速数字。

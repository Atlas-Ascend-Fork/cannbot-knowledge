---
{
  "type": "Runbook",
  "title": "gpt_oss 离线接入 LongBench 修复：datasets 缓存目录执行导致 __file__ 相对路径失效（data/data 双层路径）",
  "description": "datasets 库（3.6.0）把 LongBench.py 拷贝到 ${HF_CACHE_ROOT}/modules/ 缓存目录后执行，基于 __file__ 的相对 data 目录失效并叠加 data/data 双层路径，FileNotFoundError 被包装为 DatasetGenerationError。修复：_split_generators 的 data_dir 改为数据集绝对路径并去掉双层拼接；修复后 load_dataset 生成成功、120B TP8 样例重跑 PASS（两条轨迹独立闭环）。",
  "tags": [
    "task.debugging",
    "task.testing",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a3"
  ]
}
---
# gpt_oss 离线接入 LongBench 踩坑修复：datasets 缓存目录执行导致 `__file__` 相对路径失效（data/data 双层路径）

## 适用场景

- 模型/框架：cann-recipes-infer `models/gpt_oss`（GPT-OSS-120B bf16，218GB 15 分片，8 卡 TP，LongBench narrativeqa），统一入口 `executor/scripts/infer.sh`；数据集脚本 `dataset/LongBench/LongBench.py`（HF datasets 加载脚本，`load_dataset(..., trust_remote_code=True)` 链路，datasets==3.6.0）。
- 平台/版本：Atlas A3（Ascend 910_9362 ×16）宿主机直跑，CANN 9.2.0，Python 3.11.15，transformers 5.0.0；两条轨迹分别在 2026-10-14（观测来源 1）与 2026-10-16（观测来源 2）独立踩坑并修复。
- 工作负载：按 README 指引"在 LongBench.py 中修改数据集加载路径"实现离线数据接入。

路径约定：`${HF_CACHE_ROOT}` 为本地 Hugging Face 缓存根，保留 `modules/datasets_modules` 等缓存布局；`${RECIPES_ROOT}` 为 cann-recipes-infer 源码根；`${DATASET_ROOT_1}` 为第 1 个本地 LongBench 数据目录（不同编号不假定同一位置）。`${LOCAL_PATH_1}` 等为原文中其余本地文件或目录的替换位置，按调用用途设置，代码字符串也须显式替换。观测来源编号仅用于本卡区分实验，不是公开会话标识。

## 触发与观测

故障（failure，观测来源 2 T 182 复现，工具结果全文逐字）：

```
FileNotFoundError: [Errno 2] No such file or directory: '${DATASET_ROOT_1}/704574c7dd9b4c7e31c1605c87a617bbeb4d368fe6b5112e874d61072a242d34/data/data/narrativeqa.jsonl'
The above exception was the direct cause of the following exception:
Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "${LOCAL_PATH_1}", line 2084, in load_dataset
    builder_instance.download_and_prepare(
  File "${LOCAL_PATH_2}", line 925, in download_and_prepare
    self._download_and_prepare(
  File "${LOCAL_PATH_2}", line 1649, in _download_and_prepare
    super()._download_and_prepare(
  File "${LOCAL_PATH_2}", line 1001, in _download_and_prepare
    self._prepare_split(split_generator, **prepare_split_kwargs)
  File "${LOCAL_PATH_2}", line 1487, in _prepare_split
    for job_id, done, content in self._prepare_split_single(
  File "${LOCAL_PATH_2}", line 1644, in _prepare_split_single
    raise DatasetGenerationError("An error occurred while generating the dataset") from e
datasets.exceptions.DatasetGenerationError: An error occurred while generating the dataset
```

首次故障出现在 gpt_oss_120b_8tp 样例第一次执行（观测来源 2 T 178、观测来源 1 T 178，推理进程在 LongBench 加载阶段即失败，未进入权重加载；框架层最终打印 `ERR99999 UNKNOWN applicaiton exception`）。根因线索：报错路径位于 `${HF_CACHE_ROOT}/modules/datasets_modules/datasets/LongBench/<hash>/data/data/narrativeqa.jsonl`（缓存目录 + data/data 双层），而非用户配置的仓库目录。

## 探针与操作

修改前（before，观测来源 2 T 186 读取 LongBench.py 原文，行 100-112——基于 `__file__` 的相对路径 + data/data 双层拼接的踩坑写法）：

```
100:     def _split_generators(self, dl_manager):
101:         data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
102:         task_name = self.config.name
103:         return [
104:             datasets.SplitGenerator(
105:                 name=datasets.Split.TEST,
106:                 gen_kwargs={
107:                     "filepath": os.path.join(
108:                         data_dir, "data", f"{task_name}.jsonl"
109:                     ),
110:                 },
111:             )
112:         ]
```

修改后（after，观测来源 2 C 188 edit 事件的参数原文逐字，newString 为绝对路径 + 单层 data）：

```
{"filePath": "${RECIPES_ROOT}/dataset/LongBench/LongBench.py", "newString": "    def _split_generators(self, dl_manager):\n        data_dir = \"${RECIPES_ROOT}/dataset/LongBench/data\"\n        task_name = self.config.name\n        return [\n            datasets.SplitGenerator(\n                name=datasets.Split.TEST,\n                gen_kwargs={\n                    \"filepath\": os.path.join(\n                        data_dir, f\"{task_name}.jsonl\"\n                    ),\n                },\n            )\n        ]", "oldString": "    def _split_generators(self, dl_manager):\n        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), \"data\")\n        task_name = self.config.name\n        return [\n            datasets.SplitGenerator(\n                name=datasets.Split.TEST,\n                gen_kwargs={\n                    \"filepath\": os.path.join(\n                        data_dir, \"data\", f\"{task_name}.jsonl\"\n                    ),\n                },\n            )\n        ]"}
```

（等价可读形式：newString 把 `data_dir` 改为 `${RECIPES_ROOT}/dataset/LongBench/data`，并把 `os.path.join(data_dir, "data", f"{task_name}.jsonl")` 改为 `os.path.join(data_dir, f"{task_name}.jsonl")`。观测来源 1 C 185 为等价修改。）

## 机制与判别

- 结论 1：gpt_oss 离线接入 LongBench 时，datasets 库（3.6.0）会把 LongBench.py 拷贝到 `${HF_CACHE_ROOT}/modules/datasets_modules/datasets/LongBench/<hash>/` 缓存目录后执行，脚本内基于 `__file__` 的相对 data 目录失效（`__file__` 指向缓存目录），叠加 `os.path.join(data_dir, "data", ...)` 后形成 `data/data/narrativeqa.jsonl` 双层路径，触发 FileNotFoundError，并被包装为 `DatasetGenerationError` 抛出。
  - 证据：观测来源 2 T 182（缓存目录路径 + 双层 data 的 FileNotFoundError 原文）；T 178 / 观测来源 1 T 178（首次运行即失败于数据集生成阶段）。
  - 判别：报错路径前缀 `${HF_CACHE_ROOT}/modules/...` 与用户配置的仓库路径无关，可直接区分"数据文件缺失"（用户目录下确实存在 dataset/LongBench/data/narrativeqa.jsonl，拷贝自 ${LOCAL_PATH_3}）与"脚本执行目录漂移"（缓存机制）两种解释——观测支持后者。
- 结论 2：修复为把 `_split_generators` 的 data_dir 改为数据集所在绝对路径（并去掉 data/data 双层拼接）；修复后 `load_dataset` 生成成功（`Generating test split: 200 examples`，观测来源 2 T 192），gpt_oss_120b_8tp 样例重跑 PASS（8 rank 正常完成、LongBench narrativeqa 首条样本返回摘要文本（仅确认加载与执行完成，未做摘要精度评分）），观测来源 1 修复后同样重跑成功。
  - 修后验证信号：观测来源 2 T 192（数据集生成 200 examples）、T 196（120B 重跑 decode 序列正常，A 198 确认 decode 平均 44.98ms）；观测来源 1 T 189（120B 重跑成功，decode 平均 44.62 ms/token）。
- 关联约束（诊断）：README 第 99 行仅说"在LongBench.py中修改数据集加载路径"，未说明必须绝对路径与缓存机制——两条轨迹在同一点独立踩坑（各 1 次），说明该指引不充分。

## 验证信号

- 失败：观测来源 2 T 178（首次运行失败）、T 182（FileNotFoundError/DatasetGenerationError 全文）；观测来源 1 T 178（首次运行失败）、T 182（从 res 日志 grep 出 DatasetGenerationError 根因）。
- before/after：观测来源 2 C 188（edit 参数含修改前后完整函数体，逐字如上）；观测来源 1 C 185（等价 edit）。
- 修后验证：观测来源 2 T 192（`Generating test split: 200 examples [00:00, 1704.75 examples/s]`）、T 196（120B 8 卡重跑进入正常 decode）；观测来源 1 T 189（120B 8 卡重跑 decode 42.29ms 序列，A 191 确认 decode 平均 44.62 ms/token、8 rank 正常完成）。
- 平台与证据等级：Atlas A3 宿主机；以上均为工具结果原文；修复→重跑验证在两条轨迹各完整闭环 1 次。

## 适用与失效边界

- 适用：datasets==3.6.0 + trust_remote_code 数据集脚本（LongBench.py 类）+ 离线数据目录接入；判读规则：DatasetGenerationError 内层 FileNotFoundError 指向 `${HF_CACHE_ROOT}/modules/...` 即为脚本缓存执行导致的路径漂移，修复方向是 `_split_generators` 改绝对路径（不是去补缓存目录的文件）。
- 边界/未知：
  - 绝对路径与仓库绑定（换机器/换目录需同步改）；更通用的免改脚本方案（框架支持 data_dir 参数或改用 jsonl 直读）未在轨迹内验证；
  - 修复后需注意 datasets 缓存仍会复用缓存目录中的脚本副本（验证时曾 `rm -rf` 清缓存重测，观测来源 2 C 191），不清缓存时行为未单独观测；
  - 仅验证 narrativeqa 子集与 120B TP8 负载；其他子集/模型未逐一验证（机制与子集无关，为推断）；
  - 该修复是用户侧绕行，上游 README/框架修复（给出绝对路径示例或支持配置化 data_dir）未实施。

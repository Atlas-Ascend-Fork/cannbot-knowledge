---
{
  "type": "Runbook",
  "title": "gpt_oss requirements.txt 钉死 safetensors==0.4.0 与 transformers==5.0.0 冲突：pip 安装必然 ResolutionImpossible",
  "description": "gpt_oss requirements.txt 同时钉死 transformers==5.0.0 与 safetensors==0.4.0，而 transformers 5.0.0 要求 safetensors>=0.4.3，pip 依赖求解必然报 ResolutionImpossible（两条轨迹独立复现）。失败边界仅限新环境按 README 安装路线；预装环境（safetensors 0.8.0/0.6.2）推理不受影响。",
  "tags": [
    "task.debugging",
    "task.testing",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "a3"
  ]
}
---

# gpt_oss requirements.txt 钉死 safetensors==0.4.0 与 transformers==5.0.0 冲突：pip 安装必然 ResolutionImpossible（负向结果）

## 适用场景

- 模型/框架：cann-recipes-infer `models/gpt_oss/requirements.txt`（声明 torch==2.8.0、transformers==5.0.0、safetensors==0.4.0 等）。
- 平台/版本：Atlas A3（Ascend 910_9362 ×16）宿主机直跑环境，CANN 9.2.0，Python 3.11.15（conda 环境 recipes_infer_py311），transformers 5.0.0 已预装；两条轨迹分别为 2026-10-14（来源记录，torch 2.10.0+cpu / torch_npu 2.10.0.post7.dev20260924）与 2026-10-16（来源记录，torch 2.10.0+cpu / torch_npu 2.10.0.post7.dev20261016）。
- 工作负载：新环境按 README 依赖安装步骤（`pip3 install -r requirements.txt`，实际操作时过滤 torch 系包）部署 gpt_oss 推理环境。

## 触发与观测

尝试（attempt）：按 README 执行依赖安装（两条轨迹均用 python 过滤 torch/torch_npu 行后 `pip3 install -r /dev/stdin`）。

失败（failure，来源记录 T 99，工具结果全文逐字）：

```
ERROR: Cannot install safetensors==0.4.0 and transformers==5.0.0 because these package versions have conflicting dependencies.
The conflict is caused by:
    transformers 5.0.0 depends on safetensors>=0.4.3
Additionally, some packages in these conflicts have no matching distributions available for your environment:
2. remove package versions to allow pip to attempt to solve the dependency conflict
ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
```

来源记录 T 131 独立复现同一失败（同命令同冲突，输出截断至 `ERROR: Cannot install safetensors==0.4.0 and transformers==5.0.0 because these package versions have conflicting dependencies.` + `The conflict is caused by:`）。

requirements.txt 原文（来源记录 T 79，`cat models/gpt_oss/requirements.txt` 输出逐字）：

```
torch==2.8.0
transformers==5.0.0
datasets==3.6.0
numpy==1.26.4
protobuf==6.31.0
decorator==5.2.1
scipy==1.15.3
attrs==25.3.0
psutil==7.0.0
compressed-tensors==0.6.0
accelerate==1.0.1
einops==0.8.0
safetensors==0.4.0
tqdm==4.66.0
```

## 探针与操作

安装命令（来源记录 C 98 与 来源记录 C 130 同型）：

```
python3 -c "
import re, sys
lines = open('models/gpt_oss/requirements.txt').readlines()
filtered = [l for l in lines if not re.match(r'^torch(_npu|vision|audio)?[=><]', l.strip())]
sys.stdout.writelines(filtered)
" | pip3 install -r /dev/stdin 2>&1 | head -30
```

（过滤 torch 系包是因为环境已装 torch 2.10.0+cpu；冲突与 torch 过滤无关——报错仅指向 safetensors 与 transformers 两个包。）

## 机制与判别

- 结论 1：gpt_oss requirements.txt 同时钉死 `transformers==5.0.0` 与 `safetensors==0.4.0`，而 transformers 5.0.0 的依赖要求 `safetensors>=0.4.3`，二者直接矛盾，任何环境执行该安装都报 `ResolutionImpossible`（两条独立轨迹复现，失败条件确定且与硬件/网络无关）。
  - 信号：来源记录 T 99（完整报错）、来源记录 T 131（同型报错头）。
- 结论 2：该冲突的失败边界限于"新环境按 README 安装依赖"这一路线；已预装依赖的环境不受影响——实测环境中 safetensors 为 0.8.0（来源记录 T 103 `safetensors 0.8.0`）/ 0.6.2（来源记录 T 135 pip list），满足 transformers 5.0.0 的 >=0.4.3 要求，两轨迹的 20B 单卡与 120B TP8 推理全部通过（来源记录 T 166/T 196、来源记录 T 163/T 189）。
  - 判别：报错由 pip 依赖求解器产生（版本约束矛盾），不是镜像源缺包或架构不匹配——`Additionally, some packages in these conflicts have no matching distributions available` 为附带提示，主冲突明确列出 `transformers 5.0.0 depends on safetensors>=0.4.3`。
- 未验证推断（轨迹内未实施修复）：放宽为 `safetensors>=0.4.3`（或删除该行由 transformers 决定）可解除冲突；两条轨迹报告均如此建议，未在轨迹内执行修复后安装验证。

## 验证信号

- 失败：来源记录 T 99（ResolutionImpossible 全文）；来源记录 T 131（同型报错，输出被命令的 head -30 截断）。
- 失败条件原文：来源记录 T 79（requirements.txt 逐字内容，`safetensors==0.4.0` 与 `transformers==5.0.0` 并存）。
- 边界（预装环境可运行）：来源记录 T 103（safetensors 0.8.0）；来源记录 T 135（pip list 含 safetensors 0.6.2）；推理成功信号 来源记录 T 166/T 196 与 来源记录 T 163/T 189。
- 平台与证据等级：Atlas A3 宿主机；工具结果原文；每条轨迹各 1 次安装尝试（共 2 次，均失败于同一冲突），安装失败的"必然性"由版本约束矛盾推导（transformers 5.0.0 元数据要求 >=0.4.3，与钉死 0.4.0 不可同时满足）。

## 适用与失效边界

- 适用（失败条件）：任何执行 `pip3 install -r models/gpt_oss/requirements.txt` 且要求按文件钉死版本解析的环境（不限于 A3/ARM）；2026-10-14/16 两个不同 torch_npu 构建的环境复现，说明与推理框架版本无关。
- 边界（不影响运行）：预装或手工装好 safetensors>=0.4.3 + transformers 5.0.0 的环境推理不受影响（两轨迹 4 个样例 PASS 为证）。
- 不可采用路线：按 requirements.txt 原样安装必然失败，不要在离线环境反复重试；绕行方式为依赖环境预装（README 的 Docker 路径或手工装包），轨迹内采用的是"预装环境直接运行"路线。
- 未知：修复（放宽版本约束）未验证；`torch==2.8.0` 与宿主 torch 2.10.0 的冲突因轨迹内过滤了 torch 行而未触发，其原样安装行为未知。

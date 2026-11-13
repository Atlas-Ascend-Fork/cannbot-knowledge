---
{
  "type": "Runbook",
  "title": "qwen3_8b notebook 环境自检报'当前 Python 环境不可写'：8 个版本 pin 未满足触发自动 pip install 分支，而 root 拥有的系统 Python site-packages 不可写",
  "description": "02_baseline_inference.ipynb Cell 1 的 ensure_npu_environment 自检抛 RuntimeError: 当前 Python 环境不可写：/usr/local/bin/python。请切换到可写的 Jupyter kernel。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# qwen3_8b notebook 环境自检报'当前 Python 环境不可写'：8 个版本 pin 未满足触发自动 pip install 分支，而 root 拥有的系统 Python site-packages 不可写


## 适用场景

02_baseline_inference.ipynb Cell 1 的 ensure_npu_environment 自检抛 RuntimeError: 当前 Python 环境不可写：/usr/local/bin/python。请切换到可写的 Jupyter kernel。定位为两级门控：requirements.txt 统一版本 pin 有 8 个不满足（setuptools/torchvision/torchao/transformers/compressed-tensors/pandas/einops/wheel），unmet 非空触发自动 pip install 分支；而 Jupyter 内核 /usr/local/bin/python 软链到 root 所有的 /opt/buildtools/Python-3.11.4，其 site-packages 对 uid 1000 不可写（os.access(purelib, os.W_OK) 为假）才抛错。

## 触发与观测

触发：notebook Cell 1 RuntimeError '当前 Python 环境不可写'。探针：读 notebook cell 输出 traceback（environment_check.py:40）、读 environment_preflight.py 的 unmet/写权限两级门控代码、逐包比对 23 个 pin、检查内核解释器归属与权限、确认 sudo/venv 可用。观测：8 个 pin 不满足 + site-packages root 所有不可写。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${PYTHON_ENV_ROOT}`：用于复现的 Python 虚拟环境根目录。


关键探针与修复操作。证据角色覆盖：trigger, probe, observation, discrimination。

## 机制与判别


> 触发：notebook Cell 1 的环境自检主动抛 RuntimeError: 当前 Python 环境不可写：/usr/local/bin/python。请切换到可写的 Jupyter kernel（cell 输出 traceback：environment_check.py:40 ensure_npu_environment ← Cell In[2] line 63），不是推理代码本身的 bug。


> 机制：两级门控——find_unmet_requirements(pins) 比对 23 个统一版本 pin 后 unmet 非空（8 个不满足：setuptools 82.0.1≠81.0.0、torchvision 0.22.1≠0.23.0、torchao 未装≠0.13.0、transformers 4.57.6≠5.0.0、compressed-tensors 未装、pandas 3.0.6≠2.2.3、einops 0.8.1≠0.8.2、wheel 0.47.0≠0.45.1），进入自动 pip install 分支；该分支先检查 os.access(purelib, os.W_OK)，而内核 /usr/local/bin/python 软链到 root 拥有的 /opt/buildtools/Python-3.11.4（755），其 site-packages 对 uid 1000 不可写 → 抛错。包版本全对时直接返回、根本不看写权限。


```
unmet = find_unmet_requirements(pins)
if not unmet:                     # 包版本全对 → 直接返回，根本不看写权限
    print("...跳过安装")
    return False
if not os.access(purelib, os.W_OK):   # 需要装包时，才要求 site-packages 可写
    raise RuntimeError("当前 Python 环境不可写...")
```


```
${PYTHON_ENV_ROOT}/bin/pip install -U pip ipykernel -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn 2>&1 | tail -n 15
```

## 验证信号

Jupyter notebook 环境自检（ensure_npu_environment 类）报'当前 Python 环境不可写'：先查统一版本 pin 的 unmet（触发自动安装分支），再查内核 site-packages 写权限；修复用用户可写 venv 注册 kernel。


## 适用与失效边界

适用：Jupyter notebook 环境自检（ensure_npu_environment 类）报'当前 Python 环境不可写'：先查统一版本 pin 的 unmet（触发自动安装分支），再查内核 site-packages 写权限；修复用用户可写 venv 注册 kernel。失效边界：诊断链与修复方向有代码级依据，但 notebook 最终跑通的输出未在已读事件中（超长会话中段未全读）；venv 方案执行细节在会话中段。

---
{
  "type": "Runbook",
  "title": "LingBot-VA NPU 推理样例 PR 复现阻塞定界（依赖钉死不存在版本 + 社区权重缺子目录）",
  "description": "LingBot-VA 推理样例按来源文档安装时被依赖与权重装配问题阻塞；patch 的 install/assert_report 注册检查报告 11/11。没有完成 rollout 和 NPU 数值验证，因此不能据注册成功排除适配代码缺陷。",
  "tags": [
    "task.testing",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# LingBot-VA NPU 推理样例 PR 复现阻塞定界（依赖钉死不存在版本 + 社区权重缺子目录）
## 适用场景
昇腾社区任务 PR 复核场景：cann-recipes-embodied-ai 新增模型推理样例（LingBot-VA：自回归视频-动作世界模型 + LIBERO 四套件闭环评测）后，需在 NPU 容器内复现验证其文档路径。适用于任何"文档声称可复现、实为依赖/权重装配阻塞"的样例 PR 定界。
## 触发与观测
- 对 cann-recipes-embodied-ai PR #229（LingBot-VA 昇腾 NPU 推理样例 + LIBERO 四套件评测）的复核结论为 BLOCKED：5 项 P1 全部是文档路径上的启动/安装阻塞（B1–B5），尚未取得核心模型数值正确性的验证结论。
触发：按 PR 文档执行模型侧安装（pip install -r requirements.txt）即失败（B1，事件 423）。

```
title : 模型侧 requirements.txt 钉死不存在的 msgpack-numpy==0.6.2，安装必失败
file : manipulation/lingbot-va/infer_with_torch/requirements.txt:25
reproduce : pip install -r requirements.txt -> ERROR: No matching distribution found for msgpack-numpy==0.6.2（当时安装器列出的可用版本最高为 0.4.8）
expected : requirements.txt 可解析安装（模型侧实际使用上游 vendored msgpack_numpy.py，不依赖该 pip 包）
evidence_path : raw/validation/model_requirements_install.log
fix : 删除 msgpack-numpy==0.6.2 行（或改钉 0.4.8），实装 pip install -r requirements.txt 验证
```

完整的 P1 阻塞清单：

```
- **P1（BLOCKED，5 项，均为文档路径上的启动/安装阻塞）**：
  - B1 `requirements.txt:25` 钉死不存在的 `msgpack-numpy==0.6.2`（当时安装器列出的可用版本最高为 0.4.8）→ 该次模型侧安装失败
  - B2 两侧 requirements 同时钉 `numpy==1.26.4` 与 `opencv-python==4.12.0.88`（py3.9+ 要求 numpy>=2）→ 解析必冲突
  - B3 模型侧缺 `accelerate` → server 加载 transformer 时 `from_pretrained` 必抛 ValueError
  - B4 仿真侧缺 `msgpack`/`websockets` → `eval_harness._load_client_policy` 启动即 ModuleNotFoundError
  - B5 三个社区套件权重目录无 vae/text_encoder/tokenizer，README 未说明装配 → 三套件（1500/2000 rollout）按文档无法启动
```

## 探针与操作
- B1：requirements.txt:25 钉死不存在的 msgpack-numpy==0.6.2（当时安装器列出的可用版本最高为 0.4.8），pip install -r requirements.txt 复现 ERROR: No matching distribution found for msgpack-numpy==0.6.2，该次模型侧安装失败；而模型侧实际使用上游 vendored 的 msgpack_numpy.py，不依赖该 pip 包，修复建议是删除该行。
探针：在隔离 worktree 建 venv 分别安装模型侧/仿真侧依赖并留日志（raw/validation/model_requirements_install.log 等 16 份）；克隆上游 lingbot-va 固定提交 7c6ffa9b 逐项核对 patch/harness 引用的文件、行号与语义；对全部新增 .py 做 py_compile；在 8×910B4 NPU 上跑 patch 的 install()+assert_report 自证；用合成 2000 条明细验证 recompute 可复算性。
## 机制与判别
- B1：requirements.txt:25 钉死不存在的 msgpack-numpy==0.6.2（当时安装器列出的可用版本最高为 0.4.8），pip install -r requirements.txt 复现 ERROR: No matching distribution found for msgpack-numpy==0.6.2，该次模型侧安装失败；而模型侧实际使用上游 vendored 的 msgpack_numpy.py，不依赖该 pip 包，修复建议是删除该行。
- B2–B5 阻塞链：numpy==1.26.4 与 opencv-python==4.12.0.88 同时钉死（opencv 4.12 在 py≥3.9 要求 numpy≥2）导致解析必冲突；模型侧缺 accelerate 使 diffusers 0.36.0 的 from_pretrained 抛 ValueError；requirements-sim.txt 缺 msgpack / websockets 使 eval_harness 启动即 ModuleNotFoundError；三个社区套件权重目录缺 vae / text_encoder / tokenizer 子目录且 README 未说明装配，上游 VA_Server.__init__ 强制加载四子目录，导致 1500/2000 rollout 无法按文档启动。
- 阻塞已确认当前启动阻塞在依赖/装配路径，NPU 适配数值正确性仍未知：实际跑在 NPU（8×910B4，torch+torch_npu 2.9.0）上的验证只有 lingbot_va_npu_patch.py 的 install()+assert_report 自证（11/11 installed:true）；完整 2000 rollout 与正式 SR / 性能在本次复核中未验证，如实记录为未验证项。
定界逻辑：五条阻塞（B1 依赖钉死不存在版本、B2 numpy/opencv 冲突、B3 缺 accelerate、B4 仿真依赖缺失、B5 社区权重缺子目录）全部位于文档/装配路径，而 NPU 侧代码自证通过（见验证信号），据此把"无法复现 2000 rollout"的当前阻塞定位到依赖与装配，但未排除同时存在 NPU 适配问题；按严格阻塞原则停止依赖该路径的后续实验并标 BLOCKED，不以替代路径绕过。
## 验证信号
事件 368 复核执行情况原文：

```
- 通过：py_compile 7/7；test_rope_shim 5/5（max_abs_err=2.384e-07，与 PR 声明一致）；test_kv_book 3/3（693 淘汰覆盖）；patch `install+assert_report` 本机 NPU（torch+torch_npu 2.9.0, 8×910B4）11/11 installed:true；recompute 在合成 2000 条明细上复现 Avg 96.10%/SR/唯一键；pre-commit 全过；权重/配置哈希与文档一致；diff 与冻结输入 sha256 一致。
```

其中 NPU 上实际执行的验证为 lingbot_va_npu_patch.py 的 install()+assert_report（11/11 installed:true，torch+torch_npu 2.9.0，8×910B4）。
## 适用与失效边界
边界：完整 2000 rollout、正式 SR、性能与内存长稳未验证（长时任务按 skill 应由人工黑盒入口代跑）；test_env_determinism 因仿真栈无法按文档安装未运行；成功率口径存在任务书内部矛盾（正文 1 节与 test_cases 写 ≥98.0%，3 节验收表写 ≥96.0%，PR 声称 96.10% 介于两者之间）。本规则不判断 NPU 数值正确性，只定界复现阻塞。

## 补充机制片段
### 机制片段
```
- **P1（BLOCKED，5 项，均为文档路径上的启动/安装阻塞）**：
  - B1 `requirements.txt:25` 钉死不存在的 `msgpack-numpy==0.6.2`（当时安装器列出的可用版本最高为 0.4.8）→ 该次模型侧安装失败
  - B2 两侧 requirements 同时钉 `numpy==1.26.4` 与 `opencv-python==4.12.0.88`（py3.9+ 要求 numpy>=2）→ 解析必冲突
  - B3 模型侧缺 `accelerate` → server 加载 transformer 时 `from_pretrained` 必抛 ValueError
  - B4 仿真侧缺 `msgpack`/`websockets` → `eval_harness._load_client_policy` 启动即 ModuleNotFoundError
  - B5 三个社区套件权重目录无 vae/text_encoder/tokenizer，README 未说明装配 → 三套件（1500/2000 rollout）按文档无法启动
```
### 机制片段
```
title : 模型侧 requirements.txt 钉死不存在的 msgpack-numpy==0.6.2，安装必失败
file : manipulation/lingbot-va/infer_with_torch/requirements.txt:25
reproduce : pip install -r requirements.txt -> ERROR: No matching distribution found for msgpack-numpy==0.6.2（当时安装器列出的可用版本最高为 0.4.8）
expected : requirements.txt 可解析安装（模型侧实际使用上游 vendored msgpack_numpy.py，不依赖该 pip 包）
evidence_path : raw/validation/model_requirements_install.log
fix : 删除 msgpack-numpy==0.6.2 行（或改钉 0.4.8），实装 pip install -r requirements.txt 验证
```
### 机制片段
```
- 通过：py_compile 7/7；test_rope_shim 5/5（max_abs_err=2.384e-07，与 PR 声明一致）；test_kv_book 3/3（693 淘汰覆盖）；patch `install+assert_report` 本机 NPU（torch+torch_npu 2.9.0, 8×910B4）11/11 installed:true；recompute 在合成 2000 条明细上复现 Avg 96.10%/SR/唯一键；pre-commit 全过；权重/配置哈希与文档一致；diff 与冻结输入 sha256 一致。
```

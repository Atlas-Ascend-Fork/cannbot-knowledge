---
{
  "type": "Runbook",
  "title": "fp32 纯设备迁移 + CPU golden L0 余弦门禁的 NPU 迁移验证模式（Ascend950PR aclnn-only 环境装配）",
  "description": "无 GPU 环境下把 HF fp32 自定义模型迁到昇腾 NPU 的验证模式：CPU eager fp32 golden（与模型卡预期交叉验证）→ C0 纯设备迁移冒烟（text_sha16 比对）→ L0 门禁（逐条 logit 余弦 + 吐字可读硬 FAIL）→ P0 基线。含 Ascend950PR_9589（aclnn-only）特有的三要素环境装配：ASCEND_HOME_PATH 指系统 toolkit（compiler）、ASCEND_OPP_PATH 指用户级 950-ops 内核包、LD_LIBRARY_PATH 叠加用户级 lib64。实测 L0 8/8 PASS cos=1.000000。",
  "tags": [
    "task.implementation",
    "task.testing",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "950"
  ]
}
---

# fp32 纯设备迁移 + CPU golden L0 余弦门禁的 NPU 迁移验证模式（Ascend950PR aclnn-only 环境装配）

## 适用场景

- 无 GPU 环境下把 HF fp32 模型（含 trust_remote_code 自定义类）迁到昇腾 NPU（torch_npu 路线），并建立可信的精度/性能基线。
- 本例：imone/pangu_2_6B（GPTPanguForCausalLM 2.73B，fp32，32 层 × hidden 2560 × 32 头 head_dim=80，vocab 40000），Ascend950PR_9589 单卡。
- 关键前置：Ascend950PR 为 aclnn-only 芯片，系统 CANN 9.0.0/9.1.0 均无可用 950 内核（9.0.0 opp 4.9GB 无 ascend950；9.1.0 有 ascend950 目录但 opp 仅 46MB 空壳），须用户级安装 Ascend-cann-950-ops 后拆分环境变量。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

路径补充：`${WORK_ROOT}` 为本地推理迁移/性能实验工作根，包含文中 mia、venv 与 task-workspace 相对目录。按本地环境设置变量，保留文中的相对路径关系。

## 触发与观测

迁移前必须先打通运行时，本例的客观排障链条：

- CANN 9.0.0 下 aclnnMatmul 报 EZ9999 Parse dynamic kernel config fail（内核包不覆盖该 SoC）；ctypes 直查 aclrtGetSocName 实测 SoC 为 `Ascend950PR_9589`（事件 349）。
- torch_npu 2.12.0.post2 链接 libhccl.so，系统 9.1.0 只有 libhccl_v2.so → ImportError；用户级 950-ops 安装自带 libhccl.so（事件 459/466/470）。
- ASCEND_HOME_PATH 指向用户安装时 torch_npu 校验 ASCEND_COMPILER_PATH 不存在而拒绝启动（事件 474）→ 必须拆分：HOME 指系统 toolkit（compiler），OPP 指用户内核包。
- 组装后验证（事件 478 工具结果原文）：`aclnn matmul+rand OK, y.mean=0.0194`、`softmax OK, m.sum()=512.0000`、`peak mem GB: 0.033`。
- 环境快照（事件 491）：HBM 实测 123.2GB；npu-smi CLI 静默失败（exit 1 无输出），以 acl 运行时直查替代。

结论（装配判）：Ascend950PR_9589（aclnn-only）的 torch_npu 运行时装配须拆分三要素：ASCEND_HOME_PATH 指向含 compiler 的系统 CANN 9.1.0 toolkit、ASCEND_OPP_PATH 指向用户级 950-ops 9.1.0 内核包、LD_LIBRARY_PATH 叠加用户级 lib64（自带 libhccl.so），组装后 aclnn matmul/rand/softmax 全部通过。

## 探针与操作

验证模式四步（每步均有客观产物）：

1. CPU golden：CPU eager fp32 固定 8 条 prompt 逐条生成，存 logits npy + text_sha16 指纹（golden 交叉验证：s03 输出与 HF 模型卡公开预期文本逐字一致，事件 606）。
2. C0 纯设备迁移冒烟（单因子：仅 device move，不改计算语义），命令逐字（事件 663）：

```
. ${WORK_ROOT}/mia/scripts/setup_env.sh && cd ${WORK_ROOT} && venv/bin/python mia/scripts/migrate_npu.py task-workspace/models/pangu_2_6B 2>&1 | grep -vE "Warning|warn|GenerationMixin|owner|👉|auto class|related functions|trust_remote_code" | tail -15
```

3. L0 精度门禁：NPU vs CPU golden 逐条 logit 余弦 + 吐字可读硬 FAIL，命令逐字（事件 668）：

```
. ${WORK_ROOT}/mia/scripts/setup_env.sh && cd ${WORK_ROOT} && venv/bin/python mia/scripts/precision_l0.py task-workspace/models/pangu_2_6B 2>&1 | grep -vE "Warning|warn|GenerationMixin|owner|👉|auto class|related functions|trust_remote_code|jieba|prefix|Loading" | tail -25; echo "exit=$?"
```

4. P0 性能基线（warmup 3 + 10 轮中位数），建立后续候选的可比基线。

环境装配脚本（事件 481 写入的 newString 原文逐字；会话后期将 MIA_ROOT 硬编码为 ${LOCAL_PATH_1} 以规避 POSIX sh 下 $0/BASH_SOURCE 不可靠的问题，事件 530）：

```
# 事实来源: env_check.sh + 2026-10-14 排障记录
#  - SoC: Ascend950PR_9589 (aclnn-only 设备)
#  - 系统 toolkit 9.1.0 (compiler 完整) + 用户级 950-ops 9.1.0 (内核包 ${WORK_ROOT}/cann950ops)
#  - torch_npu 2.12.0.post2 需要 libhccl.so: 950-ops 用户安装自带
MIA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export ASCEND_HOME_PATH=/usr/local/Ascend/cann-9.1.0                       # compiler 所在（torch_npu 校验）
export ASCEND_OPP_PATH="$MIA_ROOT/cann950ops/cann-9.1.0/opp"               # 950 内核包（关键）
export LD_LIBRARY_PATH="$MIA_ROOT/cann950ops/cann-9.1.0/lib64:$ASCEND_HOME_PATH/x86_64-linux/lib64:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:${LD_LIBRARY_PATH:-}"
```

L0 门禁核心逻辑（事件 258 写入的 precision_l0.py 关键段原文逐字）：

```
    rows, hard_fail = [], False
    for item in mc.SMOKE_L0_V1:
        pid = item["id"]
        g = gmap[pid]
        input_ids, out_ids, text, logits_first, _ = mc.greedy_generate(
            model, tok, item["prompt"])
        g_logits = torch.from_numpy(np.load(os.path.join(gdir, g["logits_file"])))
        n = min(g_logits.shape[-1], logits_first.shape[-1])
        cos = mc.cosine(g_logits[..., :n], logits_first[..., :n])
        mae = mc.max_abs_err(g_logits[..., :n].numpy(), logits_first[..., :n].numpy())
        re_ = mc.rel_err(g_logits[..., :n].numpy(), logits_first[..., :n].numpy())
        fdiv = mc.first_divergence(g_logits[..., :n].numpy(), logits_first[..., :n].numpy())
        readable = mc.readable_ratio(text)
        text_match = mc.text_sha16(text) == g["text_sha16"]
        # 硬 FAIL: 不可读（NaN/乱码/空）。文本不一致本身不硬 FAIL（fp32 设备差异可容忍），
        # 但必须留痕（锚点⑦）。
        if readable < 0.95 or not (0.5 < cos <= 1.0):
            hard_fail = True
        rows.append({"id": pid, "n_in": int(input_ids.shape[1]),
                     "logit_cosine": round(cos, 6), "max_abs_err": round(mae, 5),
                     "rel_err": round(re_, 6), "first_divergence_pos": fdiv,
                     "text_match_golden": text_match,
                     "gen_text": text[:80], "readable": round(readable, 3),
                     "pass": bool(cos >= args.tol and readable >= 0.95),
                     "source": f"baseline/golden/{g['logits_file']} (cpu fp32 golden)"})
```

## 机制与判别

- golden 优先级取舍：本环境无 GPU → golden = CPU eager fp32（次优选择，任务契约显式声明该偏差）；golden 正确性用模型卡公开预期输出交叉验证（s03 逐字一致）。
- 门禁判据：`cos >= tol(0.999) 且 readable >= 0.95` 才 pass；吐字不可读（NaN/乱码/空）= 硬 FAIL 不可降级；文本不一致不硬 FAIL 但必须留痕——s06 因近并列 argmax 翻转文本不一致即属此类（余弦仍 1.000000）。
- transformers 4.46 加载 4.13 时代自定义类的两个地雷及绕法（本轨迹实际执行）：tokenizer 机制不兼容（'bool' object is not callable）→ 自实现 sentencepiece+jieba 等价薄封装；AutoModel config_class 注册失败 → importlib 直接构造 + load_state_dict 严格校验（missing/unexpected 均断言为空）。
- `torch.where` 掩码语义在本 SoC fp32 下无异常（cos=1.000000 实测），GPT-2 式 tril uint8 buffer 随模型迁移到 NPU 正常。

结论（门禁判）：fp32 原精度纯设备迁移（不改计算语义）通过 L0 门禁 8/8：logit 余弦 1.000000、max_abs_err≈3e-5、吐字可读；s06 因近并列 argmax 翻转致文本不一致但不判 FAIL（留痕）。

结论（基线判）：迁移后 NPU C0 基线（P0 协议 3 warmup + 10 轮）：TPOT 中位 29.433ms、TTFT 中位 28.255ms、吞吐 33.98 tok/s、显存峰值 9.994GB；同会话 CPU 基线 TPOT 中位 207.31ms（跨设备参考观测，不构成受控加速比声明）。

## 验证信号

- 事件 665：C0 冒烟 `text_sha16: 1eda420644d4dbfb` 与 CPU golden 完全一致（首步 773.9ms）。
- 事件 669：L0 门禁 8/8 PASS（cos=1.000000、mae≈3e-5、readable=1.00、exit=0）。
- 事件 675：NPU C0 基线（TPOT 中位 29.433ms / TTFT 中位 28.255ms / 33.98 tok/s / 峰值 9.994GB）。
- 参考对照：事件 659（CPU 基线 TPOT 中位 207.31ms，10 轮、48 线程 fp32）。
- 平台 Ascend950PR_9589 / CANN 9.1.0 + 950-ops / torch_npu 2.12.0.post2；单会话单卡观测。

## 适用与失效边界

- 环境装配是 950PR（aclnn-only）+ 双 CANN 共存场景的特定组合；换芯片/版本须重查 opp 内核覆盖与 libhccl 命名（torch_npu 严格配对 torch 版本，如 2.12.0.post2 ↔ torch 2.12.0）。
- npu-smi CLI 静默失败时用 acl 运行时直查（aclrtGetDeviceCount/aclrtGetSocName/aclrtGetMemInfo）替代，勿因 CLI 异常误判无卡。
- L0 仅 8 条自建 prompt、16 token 续写，是冒烟级门禁；量化/大改动后仍需 L1/L2 与逐层定位（本轨迹未执行，列为未竟）。
- bf16 化时 eager attention 的 -1e4 masked_bias dtype 转换路径是首要排查点（本轨迹 bf16 L0 也通过，但 mae 从 ~3e-5 升至 ~0.1）。
- CPU golden 与 NPU 的差异以余弦容差（0.999）+ 硬 FAIL 可读性双门槛控制；若追求更强保真须 GPU golden。

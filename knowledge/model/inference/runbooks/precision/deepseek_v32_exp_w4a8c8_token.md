---
{
  "type": "Runbook",
  "title": "DeepSeek-V3.2-Exp W4A8C8 空输出诊断：特殊 token 假设与待验证的生成/解码链路",
  "description": "DeepSeek-V3.2-Exp W4A8C8 在 A3 16 die 的推理日志中出现输出文本为空、每请求统计 257 个有效 token、MTP 接受率 1.0000。特殊 ID 解码探针和正常英文往返检查通过，但未 dump 实际生成 ID 或 get_valid_output 的返回列表，因此不能断言全为特殊 token，也未全面排除输入模板、截断或 tokenizer 链路。LMHead TP16 聚合与量化精度仍为待验证方向。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.memory",
    "topic.speculative_decoding"
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
# DeepSeek-V3.2-Exp W4A8C8 空输出诊断：特殊 token 假设与待验证的生成/解码链路

## 适用场景

- 模型/框架：DeepSeek-V3.2-Exp（W4A8C8 量化权重，${LOCAL_PATH_1}，71 分片完整），cann-recipes-infer 仓，离线推理入口 `executor/offline/infer.py`（经 `executor/scripts/infer.sh` 调起），MTP 投机解码（next_n=1/3，贪心 temperature=0.0）。
- 平台/版本：Atlas A3（Ascend 910_9362）单机 16 die；Docker 镜像 `cann9.0_pt2.8.0_dsv3.2_aarch_image:v0.1`（CANN 9.0.0、PyTorch 2.8.0+cpu、torch_npu、transformers 4.53.3、Python 3.11.12）。
- 负载：1cp+MTP1（rank_16_16ep_1cp_w4a8c8.yaml，input_truncated_len=4096）与 16cp+MTP3（缓解版，input_truncated_len=16384）两个 CI 样例，InfiniteBench longbook_qa_eng（351 条真实英文长文本）。
- 数据来源：2026-10-14 至 10-17 四天运行 + 本机 20260909 以来的全部历史运行（118 个 res 目录）扫描。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

所有成功运行（无 ERROR、跑满 max_new_tokens）的 rank 日志中 `Request N: outputs:` 后均为空行，但 token 统计正常。2026-10-14 1cp 样例（事件 227）：

```
[INFO][2026-10-14 00:53:44.929][infer.py:95] Request 0: outputs:

[INFO][2026-10-14 00:53:44.929][infer.py:123] Finished inference, the number of valid output tokens is 257, total number of draft tokens is 128, total accepted number is 128
[INFO][2026-10-14 00:53:44.929][infer.py:133] The speculation accept rate: 1.0000
```

2026-10-16 1cp 样例（事件 152）同样：`Request 0: outputs:` 为空、257 有效 token、MTP1 等效 23.41 ms/token、accept rate 1.0000；2026-10-15/16/17 的 16cp+MTP3 缓解运行（事件 313/163/170）4 个请求也全部为空（1028 = 4×257 有效 token、accept rate 1.0000）。全部 16 个 rank（使用不同 prompt）输出统计完全一致。

## 探针与操作

1. 特殊 token 解码探针（2026-10-15 事件 261，容器内 python：`AutoTokenizer.from_pretrained("${LOCAL_PATH_1}", trust_remote_code=True)`，对候选 id 逐个 `tok.decode([tid], skip_special_tokens=True)`；输出事件 262 逐字）：

```
0 ''
1 ''
2 ''
100 '�'
128795 ''
eos: 1 '<｜end▁of▁sentence｜>'
bos: 0 '<｜begin▁of▁sentence｜>'
```

2. 扩展探针（2026-10-16 事件 244/245，同型命令，id 集 [0, 1, 2, 3, 128798, 128799, 128800]；输出事件 245 逐字）：

```
0 ''
1 ''
2 ''
3 '!'
128798 '<think>'
128799 '</think>'
128800 '<｜fim▁hole｜>'
```
3. 输入侧探针（2026-10-15 事件 362/363，容器内 `from executor.utils.data_utils import load_infinitebench_dataset; prompts = load_infinitebench_dataset("dataset/InfiniteBench")`）：`num prompts: 351`，`prompt[0] head: 'Yes, of course, if it's fine to-morrow,' said Mrs Bronwyn. 'But you'll have to be up with the lark,`，`prompt[0] len: 381748`——输入为真实英文长文本，非空/非乱码；推理日志亦记录 `16 of 16 prompts have been tokenized...`（事件 281）。
4. tokenizer 往返探针（2026-10-15 事件 366/367，对正常英文句子 encode 后 decode；输出事件 367 逐字）：

```
ids: [671, 2339, 344, 943, 260, 4047, 71579, 9306, 18881, 16]
decoded: 'The book is about a young wizard named Harry.'
```

5. 历史扫描（2026-10-15 事件 276/277，对本机全部 res 目录 grep `Request 0: outputs: .+` 与 `outputs: [A-Za-z]`；输出事件 277 逐字）：

```
===COUNT-RUNS===
118
===NONEMPTY-SEARCH===
```


   即 118 个历史运行无任何非空输出命中。
6. 输出文本赋值链路（2026-10-16 事件 232/233，`sed -n '195,249p' executor/offline/offline_inference.py` 中的关键段逐字）：

```
223:             # Decode only the valid output segment truncated by max output length or EOS.
224:             valid_output_id_list = self.get_valid_output(request)
225:             output_text = self.engine.tokenizer.decode(
226:                 torch.tensor(valid_output_id_list), skip_special_tokens=True)
```

   即 output_text 由 `get_valid_output(request)` 返回的 token id 列表经 `skip_special_tokens=True` 解码而来——空文本与特殊 token 被过滤的解释相符，但也可能涉及有效输出切片为空、解码流程或其他异常；必须直接 dump 该列表及 skip_special_tokens=False 的结果后判别。

## 机制与判别

- 结论 1：DeepSeek-V3.2-Exp W4A8C8 权重在 A3 16 die 上所有成功运行（含本机 118 个历史运行）输出文本为空：每请求生成 257 个有效 token，但 tokenizer.decode(ids, skip_special_tokens=True) 结果为空字符串，提示特殊 token 占据输出的可能，尚未直接读取实际生成 ID，不能确定全部为特殊 token（tokenizer 对 id 0/1/2 解码均为空串，eos 为 id 1、bos 为 id 0）。
- 结论 2：输入侧与 tokenizer 的基础样本检查通过，但未全面排除相关问题：数据集加载正常（351 条真实英文长文本，prompt[0] 长 381748 字符），tokenizer 对正常英文句子 encode/decode 往返一致（ids: [671, 2339, 344, 943, 260, 4047, 71579, 9306, 18881, 16] 正确解码回 'The book is about a young wizard named Harry.'）。
- 结论 3：MTP 接受率恒等于 1.0000、接受长度恒等于 next_n+1（MTP1 为 2.0000、MTP3 为 4.0000），与贪心解码（temperature=0.0）下模型每步输出同一确定性 token 的模式吻合，是与空输出同时出现的辅助观测，不能独立证明恒定 token 或排除统计/切片问题。
- 结论 4：根因未闭合：候选方向为 LMHead TP16 聚合错误或 W4A8C8 量化精度问题（均未验证）；W8A8C8/BF16 权重的历史运行因 TransData 算子编译错误未能完成推理，无法横向对比量化方案。
- 可区分解释分支：① LMHead TP16 聚合（lmhead_tp_size=16，尚未验证的 logits 聚合问题）→ 需通过实际 argmax/ID 判断是否退化；② W4A8C8 量化 kernel 精度问题（npu_swiglu_clip_quant 等）→ 需与高精度路径做数值对照；③ prompt/chat-template 构造问题——未被排除但证据较弱（tokenizer 往返正常、模板应用未直接检验）。三者在 2026-10-15/16 轨迹内均未做 dump logits 或单测验证，列为待判别假设。
- 辅助判别信号：框架对空输出无任何 WARNING（`logger.info("Request %s: outputs: %s\n", i, res.output_text)` 仅 info 级）；本样本的 MTP 接受率为 1.0；真实文本也可能出现全部 draft 提议被接受，因此该比例不能单独判异常，应与空文本及实际 ID/logits 联合检查。

## 验证信号

- 观测信号（客观）：事件 262/245（id 0/1/2 解码空串）、事件 277（118 历史运行无非空输出）、事件 227/152（257 有效 token + accept rate 1.0000 + outputs 空）、事件 313/163/170（16cp MTP3 缓解运行同样空输出，4 请求 × 257 token）。
- 基础检查信号（客观，不能全面排除）：事件 363（输入正常）、事件 367（tokenizer 往返正常）、事件 281（prompt 正常 tokenized）。
- 证据等级：观测与基础检查在容器内同环境完成；根因（LMHead TP 聚合 / 量化精度）未验证，本卡不声称已定位根因。“全为特殊 token”只是由这些探针提示的假设，未直接 dump 生成 token id 列表（dump_data 目录为空，DUMP_PRECISION_PATH 机制未产出数据）。

## 适用与失效边界

- 适用：DeepSeek-V3.2-Exp W4A8C8、A3 16 die、ge_graph、enable_multi_streams、temperature=0.0、InfiniteBench 负载、MTP1/MTP3 的"运行成功但输出文本为空"现象判别。
- 失效/未知：BF16/W8A8C8 权重路径本机因 TransData 算子编译错误不可运行，无法对比；其他硬件（非 A3）与其他并行配置（lmhead_tp_size≠16）未验证；温度>0 采样下现象及实际 ID 分布未测。
- 后续判别建议（源自轨迹记录，未执行）：dump logits 或生成 token id（核对是否恒为 0/1/2 等特殊 id）；检查 LMHead TP16 聚合实现；W4A8C8 与高精度权重的小规模 kernel 精度对比；为 infer.py 增加空输出 WARNING。
- 停止条件：若 dump 出的 token id 含大量非特殊 id 而 decode 仍为空，则转向 tokenizer/解码链路（说明特殊 token 假设不成立，需重新检查）。

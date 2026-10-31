# 故障手册

- [编译故障](compilation/index.md)：共 11 张知识卡（如 AscendC 自定义算子的构建/打包/可用性坑：vendor 同名覆盖、build.sh op-name 不匹配、未编译则命名空间缺失、镜像滞后源码、逐 SoC AddConfig、并行编译提速、cann-recipes-infer ops/ascendc 自定义算子的跨平台 / 跨 CANN 版本构建与加载失败、AscendC 算子 host 侧未覆盖运行时可达配置空间：缺省可选输入被无条件读取、模板参数取值未全枚举 → 特定 config 崩溃 / npu fail / 无 tiling key 等）。
- [性能故障](performance/index.md)：共 10 张知识卡（如 AFD 后 FFN 侧成新瓶颈：Attention 侧 Recv EVENT_WAIT 拖尾 → 对 FFN 侧 MoE-GMM 权重做通信间隙预取、稳定图模式输入张量签名（shape/stride/dtype）避免 dynamo 重编译与缓存 miss、MoE 优化/并行在 decode 静默不生效的四类根因：硬编码 False / yaml 键名不匹配 / 漏切间接层 / 误挂 is_prefill 等）。
- [精度故障](precision/index.md)：共 22 张知识卡（如 激活 8bit 量化分支按精确 == 'W8A8' 门控会漏掉 W4A8：改 'a8' 子串判断，否则该量化模式静默不生效、compressed-tensors 量化加载器的方案识别门控陷阱：别假设总有激活量化、MX 与普通 fp8 靠 weight_block_size 区分、AWQ int4 走 W4A16、CP/DCP 在线-softmax 跨卡合并只 mask lse 不 mask out 污染归并——本卡对某序列无 KV 时须对 attn_out 施同一 batch_seq_mask 置 0 等）。
- [运行故障](runtime/index.md)：共 52 张知识卡（如 aclgraph 图捕获前 monkeypatch upstream graph_capture：用 __base__ 定位模块对多级子类失效，须沿 MRO 找 GPUModelRunner、aclgraph replay 静默挂死无报错时：用 acl_graph_print 图内打点二分定位挂点、aclgraph 图捕获报 Alloc sq cq fail / 207005 / EL0006：档位过多耗尽每卡 SQ/CQ 流资源 等）。

- [validations](validations/index.md)：共 5 张知识卡（如 LongBench 输入构造 input_max_len < system_prompt 长度 → 负索引尾切静默裁掉正文、纯 EP MoE decode 中 GMM 无条件执行（0 token 也跑）：profiling 里某卡缺 GMM 不能用「该卡没分到 token」解释，用 expert_token_num 诊断、MTP / 投机解码 decode 计时采集口径：累加每步全部 draft 前向、每 decode 步记一条完整耗时、分「每步」与「每 token」两指标 等）。

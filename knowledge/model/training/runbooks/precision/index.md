# 模型训练精度排障

- [torch_npu sigtrace golden/check 双跑定界引入 NaN 的 kernel（aten_lowering 白名单单变量）](torch_npu_sigtrace_golden_check_nan.md)：CANN 0923 的 torchtitan-npu 双跑中，摘掉 aten.sigmoid 白名单的 golden 梯度有限，原白名单 check 的 mul_934 出现 NaN；可按 FX 名找到其 producer。sum_30 两侧签名均有限，sigmoid_1 仅 check 侧有限、golden 签名缺失，不能称为双侧通过。需使用新缓存并核对 logger、FX 名和采集覆盖，缺失签名不得按 nan=0 处理。

- [aclnnGather error 161002 DT_COMPLEX64：ComplexRoPE complex64 cache 走 torch.gather 的定位](aclnngather_161002_complex64_rope_override.md)：torchtitan-npu deepseek_v3_2 模型 ComplexRoPE 路径在 NPU 上 gather complex64 cache 的算子 dtype 支持缺陷定位，面向真实训练启动排障。
- [DSV4 npu_rope interleaved cos/sin 预计算缓存（PR#407/issue#72）](dsv4_npu_rope_interleaved_cos_sin_cache_pr407.md)：torchtitan-npu 的 DeepSeek-V4 训练使用 npu_rope converter（npu_rotary_mul interleave 模式）且开启 activation checkpoint / recompute 的场景：原实现每次 forward 都从 complex cache 临时展开 cos/sin（repeat_interleave），在 full-size 模型（v4_flash 43 层、rope_head_dim=64）上造成 forward/recompute 劣化。合并 PR#401 global TND 后需重验证 rope cache 与 TND 路径的兼容性。

- [GMM1 行分块改造的 FIFO 风险：权重链不能随消费者循环重复](b1g1_e3_golden_fp4_bdn_fifo_order_fix.md)：fp4 权重预取链按 kb/half/nsub 顺序消费；把它放进额外行分块循环后需重审事务次数。记录的修正只闭合静态与编译检查，设备重跑未收口。
- [CPU offload 缩放分支：系数先转 bf16 可能改变舍入](cpu_offload_coefficient_dtype_branch_1ulp.md)：四象限探针显示该输入下 bf16 两条缩放路径有差异；不能据单个最大差值宣称所有输入最多一 ulp，分支条件也须与注释区分。

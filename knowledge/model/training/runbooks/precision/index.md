# 模型训练精度排障

- [torch_npu sigtrace golden/check 双跑定界引入 NaN 的 kernel（aten_lowering 白名单单变量）](torch_npu_sigtrace_golden_check_nan.md)：CANN 0923 的 torchtitan-npu 双跑中，摘掉 aten.sigmoid 白名单的 golden 梯度有限，原白名单 check 的 mul_934 出现 NaN；可按 FX 名找到其 producer。sum_30 两侧签名均有限，sigmoid_1 仅 check 侧有限、golden 签名缺失，不能称为双侧通过。需使用新缓存并核对 logger、FX 名和采集覆盖，缺失签名不得按 nan=0 处理。

- [aclnnGather error 161002 DT_COMPLEX64：ComplexRoPE complex64 cache 走 torch.gather 的定位](aclnngather_161002_complex64_rope_override.md)：torchtitan-npu deepseek_v3_2 模型 ComplexRoPE 路径在 NPU 上 gather complex64 cache 的算子 dtype 支持缺陷定位，面向真实训练启动排障。
- [DSV4 npu_rope interleaved cos/sin 预计算缓存（PR#407/issue#72）](dsv4_npu_rope_interleaved_cos_sin_cache_pr407.md)：torchtitan-npu 的 DeepSeek-V4 训练使用 npu_rope converter（npu_rotary_mul interleave 模式）且开启 activation checkpoint / recompute 的场景：原实现每次 forward 都从 complex cache 临时展开 cos/sin（repeat_interleave），在 full-size 模型（v4_flash 43 层、rope_head_dim=64）上造成 forward/recompute 劣化。合并 PR#401 global TND 后需重验证 rope cache 与 TND 路径的兼容性。

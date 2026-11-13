---
{
  "type": "Runbook",
  "title": "replace_input_embeds 的 s2_all_image_blind_copy 存档部署与 bit-exact 验证流程",
  "description": "TileLang（tilelang-deepseek，默认 bisheng 后端）replace_input_embeds（图像 token embedding 替换，vllm-ascend image_embed_ops.py）优化的 s2_all_image_blind_copy 存档按「模板优先」部署到工程位并完成 bit-exact 验证：部署后工程位与归档副本 SHA256 逐字节一致，冷编译后 pytest 3/3 PASS（1024/4096/16384，torch.equal bit-exact 断言，未改测试阈值）。 知识形态：validated_pattern（implementation + 轨迹内实际完成的 bit-exact 验证）。",
  "tags": [
    "task.implementation",
    "topic.data_movement"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# replace_input_embeds 的 s2_all_image_blind_copy 存档部署与 bit-exact 验证流程

## 适用场景

- TileLang（tilelang-deepseek，默认 bisheng 后端）replace_input_embeds（图像 token embedding 替换，vllm-ascend image_embed_ops.py）优化的 s2_all_image_blind_copy 存档按「模板优先」部署到工程位并完成 bit-exact 验证。

## 触发与观测

- 基线 kernel_time：1024→59.256us、4096→227.503us、16384→901.990us（Simt 原始实现）。
- 性能预期为同环境前期存档实测（vs Simt 基线 7.6~7.8x / 10.2x / 11.4x，s2 相对 s1 再 +3~6% 于 1024/4096），本轮任务范围为部署 + 编译 + 精度，未复测性能。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${SCRATCH_DIR}`：由复现者创建的本次实验临时目录。
- `${TILELANG_CACHE_DIR}`：本次实验专用的 TileLang 编译缓存目录。


- 部署与验证操作链：

```text
1. `cp operators/replace_input_embeds/final_optimized/image_embed_ops.py tile_kernels/vllm-ascend/image_embed_ops.py`
2. 部署后逐字节校验：工程位 / 本目录归档副本 SHA256 均为 19e85e87…（与存档一致）
3. `git diff f86c131 -- tile_kernels/vllm-ascend/image_embed_ops.py > s2_all_image_blind_copy.diff`（188 行 +/-）
```

```text
- 编译：`rm -rf ${TILELANG_CACHE_DIR}` 后全新编译通过（默认 bisheng 路径，
  未设 TILELANG_DEFAULT_TARGET），冷编译 pytest 全程 46.35s
- 精度：`python -m pytest "tile_kernels/vllm-ascend/image_embed_ops.py::test_replace_input_embeds" -v`
  → **3/3 PASS**（1024/4096/16384，torch.equal bit-exact 断言，未改测试阈值）
```

## 机制与判别

- 验证结论——来源结论：s2_all_image_blind_copy 按「模板优先」原样部署 final_optimized 存档（operators/replace_input_embeds/final_optimized/image_embed_ops.py，SHA256 19e85e87589ce8b3652407209c037aee95e325b11f548642ede98be2ae97b1c7）到工程位 tile_kernels/vllm-ascend/image_embed_ops.py，部署后工程位、归档副本 SHA256 逐字节一致；rm -rf ${TILELANG_CACHE_DIR} 冷编译后 python -m pytest "tile_kernels/vllm-ascend/image_embed_ops.py::test_replace_input_embeds" -v 得到 3/3 PASS（1024/4096/16384 三个 case，torch.equal bit-exact 断言，未改测试阈值，全程 46.35s）。

## 验证信号

  - 部署后工程位与归档副本 sha256 均为 ，diff 226 行落盘。
  - pytest 输出 3 passed（[1024]/[4096]/[16384] PASSED，46.35s，bit-exact torch.equal）。
- 工程位部署前基线 SHA256 （git 30dfe3d，s1 版本）与存档 区分清晰，回退可用 `git checkout 30dfe3d -- tile_kernels/vllm-ascend/image_embed_ops.py` 单文件回退（30dfe3d 是本记录已标识的部署前基线；先保存本地改动，不把两个 revision 用斜杠拼接）。
- 归档完整性（ARCHIVE_MANIFEST/IMPLEMENTATION.md）随后通过 docker cp 部署；注意 docker exec 内 ${SCRATCH_DIR} 与宿主机 ${SCRATCH_DIR} 不是同一文件系统，scp+mv 会误移容器残留旧文件，需用 docker cp 直达容器目标路径。

## 适用与失效边界

- 适用：图像 token embedding 替换类 kernel 的 bit-exact 精度门禁 + 冷编译验证流程可直接复用。
- 性能数字边界：7.6~11.4x 为同环境前期存档实测，非本轮复测；引用时需注明为存档值。任何后续改动必须重跑 bit-exact 3/3 与 msprof 复测才能宣称性能。

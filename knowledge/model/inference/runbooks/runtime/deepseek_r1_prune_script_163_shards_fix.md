---
{
  "type": "Runbook",
  "title": "GPU 版 DeepSeek-R1 裁剪脚本 163 分片异常修复：collect_weights + reshard_and_save 按体积重分片并重建索引",
  "description": "对 DeepSeek-R1（61 层 FP8）做层数/专家裁剪 + FP8→BF16 反量化生成可被 vLLM 加载的推理权重（GPU 版脚本流程），期望与 NPU 版脚本一致地按体积重新打包分片。",
  "tags": [
    "task.debugging",
    "topic.checkpointing"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# GPU 版 DeepSeek-R1 裁剪脚本 163 分片异常修复：collect_weights + reshard_and_save 按体积重分片并重建索引

## 适用场景

对 DeepSeek-R1（61 层 FP8）做层数/专家裁剪 + FP8→BF16 反量化生成可被 vLLM 加载的推理权重（GPU 版脚本流程），期望与 NPU 版脚本一致地按体积重新打包分片。

> 验证层级：end_to_end（裁剪脚本真实重跑产出正确分片结构；vLLM 服务级验证未在轨迹内捕获）

## 触发与观测

GPU 版 prune_deepseek_r1.py 裁剪 20 层后输出目录仍有 163 个 model-0000X-of-000163 分片结构（实际仅 29 个 safetensors 非空），而 NPU 版参考脚本产出 49 个分片；用户疑问脚本是否有问题。

## 探针与操作

1) 并读 GPU/NPU 两版脚本，对照 rewrite_shards 与重新分片两阶段的实现差异；2) 检查输出目录实际文件（ls + wc）。3) 替换实现并删除旧输出重跑（非空目录保护会拒绝直接运行）。

## 机制与判别

修复单元（weight_sort_key + reshard_and_save，含 TMP 分片写盘→重命名→索引重建完整流程）：


```
def weight_sort_key(name):
    if "embed_tokens" in name:
        return (0, name)
    elif name.startswith("model.layers."):
        layer_id = int(name.split(".")[2])
        return (layer_id + 1, name)
    elif "norm" in name and "layer" not in name:
        return (998, name)
    elif "lm_head" in name:
        return (999, name)
    else:
        return (100, name)


def reshard_and_save(dst_dir, extracted_weights, shard_gb):
    max_shard_size = int(shard_gb * 1024 * 1024 * 1024)

    sorted_weight_names = sorted(extracted_weights.keys(), key=weight_sort_key)

    current_shard = {}
    current_size = 0
    shard_idx = 1
    total_params = 0
    new_weight_map = {}

    for w_name in sorted_weight_names:
        tensor = extracted_weights[w_name]
        tensor_bytes = tensor.numel() * tensor.element_size()
        total_params += tensor.numel()

        if current_size + tensor_bytes > max_shard_size and current_shard:
            tmp_shard_name = f"model-{shard_idx:05d}-of-TMP.safetensors"
            save_file(current_shard, os.path.join(dst_dir, tmp_shard_name))
            for k in current_shard:
                new_weight_map[k] = tmp_shard_name
            shard_idx += 1
            current_shard = {}
            current_size = 0

        current_shard[w_name] = tensor
        current_size += tensor_bytes

    if current_shard:
        tmp_shard_name = f"model-{shard_idx:05d}-of-TMP.safetensors"
        save_file(current_shard, os.path.join(dst_dir, tmp_shard_name))
        for k in current_shard:
            new_weight_map[k] = tmp_shard_name

    total_shards = shard_idx
    logging.info(f"重新分片打包完成, 总分片数: {total_shards}")

    for idx in range(1, total_shards + 1):
        old_fp = os.path.join(dst_dir, f"model-{idx:05d}-of-TMP.safetensors")
        new_fp = os.path.join(dst_dir, f"model-{idx:05d}-of-{total_shards:05d}.safetensors")
        if os.path.exists(old_fp):
            os.rename(old_fp, new_fp)

    for w_name in new_weight_map:
        old_shard = new_weight_map[w_name]
        sid = int(old_shard.split("-")[1])
        new_shard_name = f"model-{sid:05d}-of-{total_shards:05d}.safetensors"
        new_weight_map[w_name] = new_shard_name

    new_total_size = sum(
        extracted_weights[wn].numel() * extracted_weights[wn].element_size()
        for wn in new_weight_map
    )

    new_index = {
        "metadata": {"total_size": new_total_size},
        "weight_map": new_weight_map
    }
    with open(os.path.join(dst_dir, "model.safetensors.index.json"), "w") as f:
        json.dump(new_index, f, indent=2, ensure_ascii=False)

    logging.info(f"索引文件已更新, BF16模型总大小: {new_total_size / 1024**3:.2f} GB")
    return total_shards, new_total_size, total_params
```

## 验证信号

验证信号（重跑日志与产物列表）：

  - 客观信号：
- 修复后重跑（--target-layers 20 --target-experts 256，1200s 超时）产出 75 个 model-00001-of-00075.safetensors … model-00075-of-00075.safetensors 分片、BF16 模型总大小 370.38 GB，命名与重建索引一致。
  - 客观信号：
  - 客观信号：
## 适用与失效边界

适用：任何裁剪/反量化后需要按体积重分片的 safetensors 权重导出（HuggingFace 格式 index 重建）。失效/边界：collect_weights 全量驻留内存，超大模型需评估内存；权重排序规则需与参考脚本一致（embed→layers 升序→norm→lm_head）；vLLM 加载与推理验证已启动但结果未在本轨迹内捕获，最终功能确认需以服务测试为准。

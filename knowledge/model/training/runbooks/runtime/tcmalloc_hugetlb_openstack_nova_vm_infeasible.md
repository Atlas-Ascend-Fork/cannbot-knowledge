---
{
  "type": "Runbook",
  "title": "tcmalloc 2.9.1 SysAllocator 链判别与强制 Hugetlb 路径的崩溃证据",
  "description": "Ascend NPU 训练主机侧 tcmalloc 显式大页（hugepages）优化的分配器链判别：tcmalloc 2.9.1 的 SysAllocator 链（MMap→Sbrk→Hugetlb）与强制 Hugetlb 路径的崩溃证据。",
  "tags": [
    "task.debugging",
    "topic.memory"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# tcmalloc 2.9.1 SysAllocator 链判别与强制 Hugetlb 路径的崩溃证据

tcmalloc 2.9.1 的显式大页（hugepages）方案在本环境下未被消费。本卡记录 SysAllocator 链判别与强制 Hugetlb 路径的崩溃证据。

## 适用场景

Ascend NPU 训练主机侧 tcmalloc 显式大页（hugepages）优化场景：判别 tcmalloc 是否真正消费 HugeTLB 池；适合在『分配器换大页没收益/崩溃』时的定界。route=training，area=runtime。

## 触发与观测

触发：前一轮方案（5000×2MB hugepages 池 + LD_PRELOAD libtcmalloc_minimal.so.4）失败——训练前后 HugePages_Free 均 5000（池完全未被消费），tcmalloc 从未调用 HugetlbSysAllocator。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${CANN_ROOT}`：该次实验实际使用的 CANN 安装根目录；版本以本卡适用条件为准。


可执行探针：

```bash
sudo docker exec ubuntu-npu bash -lc '
source ${CANN_ROOT}/set_env.sh 2>/dev/null
PYBIN=/opt/miniconda3/envs/torchtitan-npu/bin/python3
echo "=== Before ==="
grep HugePages_Free /proc/meminfo
LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libtcmalloc_minimal.so.4 \
TCMALLOC_SKIP_MMAP=true \
TCMALLOC_SKIP_SBRK=true \
$PYBIN -c "
import ctypes, sys
bufs = []
for i in range(100):
    bufs.append(ctypes.c_char_p(b\"x\" * (1024*1024)))
print(\"skip_mmap test ok, allocated ~100MB\")
" 2>&1
echo "=== After ==="
grep HugePages_Free /proc/meminfo
' 2>&1
```


配套探针：/proc/meminfo HugePages 计数前后对比、容器内 mmap(MAP_HUGETLB) 直测、宿主机 shmget(SHM_HUGETLB)/mmap(MAP_HUGETLB) 直测、dmesg 与 EulerOS 专有 sysctl（hugepage_mig_noalloc/hugepage_pmem_allocall 等）检查。

## 机制与判别

tcmalloc 2.9.1 的 SysAllocator 链为 MMap→Sbrk→Hugetlb（末位 fallback）：常规路径下 MMapSysAllocator 几乎不会失败，HugetlbSysAllocator 永不被调用，hugepages 池不会被消费；用 LD_PRELOAD libtcmalloc_minimal.so.4 + TCMALLOC_SKIP_MMAP=true + TCMALLOC_SKIP_SBRK=true 强制走 Hugetlb 路径时 python 直接崩溃：src/central_freelist.cc:330 tcmalloc: allocation failed 8192 → Fatal Python error: error evaluating initial values，且前后 HugePages_Free 均为 500（未消费）。

## 验证信号


来源试验前 `HugePages_Free: 500`；强制跳过 MMap/Sbrk 路径后报 `tcmalloc: allocation failed 8192` 和 `Fatal Python error: error evaluating initial values`；之后 HugePages_Free 仍为 500。只确认这次路径未成功消费大页，不能据此证明所有 OpenStack VM 或 tcmalloc 配置都不可行。

## 适用与失效边界

边界：结论绑定观测环境（华为云 OpenStack Nova VM + EulerOS kernel 5.10.0-182 hce2）；TCmemFS/TCMALLOC_MEMFS_MALLOC_PATH 等替代方案另行验证；此前同类环境观测到的收益应归因于 khugepaged THP 而非显式大页；本轨迹为只读分析轮，未实施替代方案。

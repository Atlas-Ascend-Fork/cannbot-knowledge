# 数据填充

- [AscDuplicate](asc_duplicate.md)：将src的最低位元素广播到dst中被mask筛选的位置，未被mask筛选的位置置为0。
- [AscDuplicateHighest](asc_duplicate_highest.md)：将src的最高位元素广播到dst中被mask筛选的位置，未被mask筛选的位置置为0。
- [AscDuplicateHighestMerge](asc_duplicate_highest_merge.md)：merge模式下将src的最高位元素广播到dst中被mask筛选的位置，未被筛选的元素保留原值。
- [AscDuplicateMerge](asc_duplicate_merge.md)：merge模式下将src的最低位元素广播到dst中被mask筛选的位置，未被筛选的元素保留原值。
- [AscDuplicateScalar](asc_duplicate_scalar.md)：将标量值value广播到dst寄存器，支持带mask和不带mask两种模式。
- [AscDuplicateScalarMerge](asc_duplicate_scalar_merge.md)：merge模式下将标量值value广播到dst中被mask筛选的位置，未被筛选的元素保留原值。
- [数据填充](data_fill.md)：寄存器侧数据填充类接口汇总，提供duplicate及其标量、合并、高位合并等多种数据广播填充能力。

# cache ctrl

- [asc_datacache_preload](asc_datacache_preload.md)：从GM地址预加载数据到Data Cache，每次调用预加载一个Cache Line大小的数据。
- [AscDcci](asc_dcci.md)：刷新Data Cache保证与GM一致性，支持单Cache Line刷新和整片刷新，用于多核数据一致性和Scalar写GM场景。
- [asc_dci（缓存控制）](asc_dci.md)：数据缓存失效，该指令用于使整个数据缓存无效化，且不会对处于“脏”状态的缓存行执行写回操作。换言之，所有缓存行将被直接标记为无效，其修改过但尚未同步至主存的数据将被丢弃。
- [AscGetIcachePreloadStatus](asc_get_icache_preload_status.md)：调试接口，在asc_icache_preload后调用获取ICache预加载状态，返回0表示完成，1表示未完成。
- [AscIcachePreload](asc_icache_preload.md)：从指令所在GM地址预加载指令到ICache中，支持配置预取长度。
- [缓存控制](cache_control.md)：缓存控制接口索引页，包含asc_datacache_preload、asc_dcci、asc_dci及asc_icache_preload等。

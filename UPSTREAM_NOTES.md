# 上游参考与源码来源

## 研究入口

- uFuzzy — https://github.com/leeoniya/uFuzzy — MIT（`LICENSE` 经 GitHub License API 核对，SPDX: MIT）
- Fuse.js — https://github.com/krisk/Fuse — Apache-2.0（SPDX: Apache-2.0）
- RapidFuzz — https://github.com/rapidfuzz/RapidFuzz — MIT（SPDX: MIT）

三者都已在各自仓库的 LICENSE 文件中核对过许可证。

## 源码来源声明

`src/fuzzyopt` 是独立编写的实现，使用的是公开的编辑距离与动态规划算法思想：

- 带状 DP（Ukkonen 1985 的编辑距离下界与对角线带思想）与「行最小值提前退出」是教科书级技巧，
  这里按 Python 的实现代价重新写了一遍；
- 长度分桶、NFC/NFKC 规范化、稳定排序都是通用工程做法，没有对应的上游源码。

没有把上述任一仓库的源码复制进本项目，因此这不是 fork，也不声称性能胜过这些成熟库。
与它们做公平对比需要相同数据、相同召回要求和相同机器，本项目目前不提供这种对比。

## 已知差异

- 只按 Unicode code point 比较，不做拼音/罗马字转写，也不做 CJK 分词；
- 候选生成只利用长度，不建倒排或删除索引，因此最坏情况仍是 O(n) 次距离计算；
- 没有序列化格式，索引不能落盘复用。

## 网络限制

打包环境无法直接 clone 上游仓库，以上信息来自各自官方仓库页面与 LICENSE 原文。
发布前如需最新状态，请重新打开链接核对。

# Kubernetes 电子书交付记录

本轮保留既有 14 章正文、3 个附录与 7 份 YAML，整理为统一在线阅读、EPUB 与可重复的真实 kind 实验。原稿经 AI 辅助整理，发布与维护为 Aias00。

## 仓库与运行边界

原 `Aias00/k8s-book` 保持 private。公共 `Aias00/k8s-book-reader` 使用审核后的白名单文件与独立历史，不公开原私有历史、官方网页缓存、旧截图或旧运行日志。

本机没有 Docker；真实集群检查在新 GitHub Actions Linux runner 内创建隔离 `kind-k8s-book` 上下文与独立 kubeconfig，结束后删除本次集群。静态 YAML 检查不作为运行证据。

## 已完成的验证

- 18 条官方资料重新访问成功，见 `research/source-revalidation.json`。
- kind 固定 v0.33.0；node 镜像使用该官方版本发布说明提供的 Kubernetes v1.37.0 与 SHA-256 摘要，kubectl 同为 v1.37.0，两个 CLI 下载均校验官方 SHA-256。
- 首轮 Actions `39574385558` 的 kind job `119136160482` 成功创建真实集群并完成 Service DNS/HTTP、宿主 HTTP、自愈/扩缩、HTTP 探针故障、坏镜像回滚与 ConfigMap 更新；验证器在空 EndpointSlice 的 `endpoints: null` 上失败，未声称整轮通过。
- 修复验证器兼容 null/空列表，并等待实际 Service 请求失败；私有维护仓库复验运行 `39575347931`、kind job `119139382891`（提交 `c81eff9`）已完整通过。最终运行 JSON 采用下述公共完整流水线的同一次产物，见 `research/runtime-validation.json`。
- 本地构建核对前言加 14 章、3 附录共 18 个阅读单元，书稿/EPUB/网页/搜索/实验包一致。EPUBCheck 5.4.0 为 0 错误、0 警告。
- Chromium 本地检查通过：浅色默认、共享深色与标签同步、目录、全文搜索、字号、存储关闭回退、所有 18 单元在 320/390px 无页面横向溢出，无 JavaScript 可阅读和翻页。

- 完整复验通过 PVC 相同 UID、Pod UID 改变且文件读回；CPU 请求过大与 nodeSelector 不匹配分别出现实际 Pending/Unschedulable 证据。

公共完整流水线在 ConfigMap 滚动重启后的一次立即 HTTP 请求中遇到超时，说明控制面 Ready 与数据面可达的观察时点不同。自动化现使用有 60 秒上限的实际内容恢复检查，持续失败仍会超时；相关观察已补入第 6 章。

## 已发布并完成公网验收

- 公共源码：<https://github.com/Aias00/k8s-book-reader>；实际发布产品提交为 `63c7ddcbddc95df0893c1a020374bbb7902b4a9b`。
- 最终公共完整流水线 [39578414258](https://github.com/Aias00/k8s-book-reader/actions/runs/39578414258) 已成功；构建与真实 kind 检查 job `119149642109`、Pages 部署 job `119151326179` 均成功。EPUBCheck 与阅读页浏览器检查同轮通过。
- 在线阅读：<https://aias00.github.io/k8s-book-reader/>；公网 Chromium 实际打开全部 18 单元，在 320/390px 检查无文档横向溢出，目录、搜索、字号、浅色默认、共享深色、跨标签同步、存储关闭回退、无 JavaScript 阅读与下载全部通过。
- [v1.0.0 Release](https://github.com/Aias00/k8s-book-reader/releases/tag/v1.0.0) 直接使用上述成功 CI 产物，附 EPUB、离线 HTML、实验 ZIP、SHA256SUMS、真实 kind JSON 与命令日志。命令日志为 302547 字节，随构建保留，未被阅读站清理步骤删除。
- 从 [Pages 下载](https://aias00.github.io/k8s-book-reader/downloads/k8s-book-reader.epub) 与 [Release 下载](https://github.com/Aias00/k8s-book-reader/releases/download/v1.0.0/k8s-book-reader.epub) 的 EPUB 均为 65610 字节，mimetype 有效，与 CI EPUB 字节一致；SHA-256 均为 `9da558f7457de99a426e7e9ccb22aef58fedcb25cbec6e7aaab63a28b81c2055`。
- 另将实际部署的 Pages artifact 解包后运行 `tools/reader_verify.py`，18 单元书稿、EPUB、静态网页、搜索与实验包一致性通过。完整发布和下载记录见 `research/publication-validation.json`，格式与浏览器范围见 `research/reader-validation.json`。

最终交付记录提交只补齐证据文档，不改变上述产品提交、已部署阅读文件或 Release 产物。

## 未实现或未测试

单节点 kind 不证明多节点容错或节点丢失后存储恢复。未验证生产 TLS/RBAC 安全基线、NetworkPolicy 实际执行、Metrics Server/HPA、OOM/CPU 限流负载和生产吞吐。PVC 跨 Pod 保留不等于备份；端口转发不代表 Service 负载均衡实测。探针故障检查使用独立测试 Pod，避免把就绪与存活的因果混淆。

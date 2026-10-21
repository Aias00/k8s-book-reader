# Kubernetes 电子书交付记录

本轮保留既有 14 章正文、3 个附录与 7 份 YAML，整理为统一在线阅读、EPUB 与可重复的真实 kind 实验。原稿经 AI 辅助整理，发布与维护为 Aias00。

## 仓库与运行边界

原 `Aias00/k8s-book` 保持 private。公共 `Aias00/k8s-book-reader` 将使用审核后的白名单文件与独立历史，不公开原私有历史、官方网页缓存、旧截图或旧运行日志。

本机没有 Docker；真实集群检查在新 GitHub Actions Linux runner 内创建隔离 `kind-k8s-book` 上下文与独立 kubeconfig，结束后删除本次集群。静态 YAML 检查不作为运行证据。

## 已验证与进行中

- 18 条官方资料重新访问成功，见 `research/source-revalidation.json`。
- kind 固定 v0.33.0；node 镜像使用该官方版本发布说明提供的 Kubernetes v1.37.0 与 SHA-256 摘要，kubectl 同为 v1.37.0，两个 CLI 下载均校验官方 SHA-256。
- 首轮 Actions `39574385558` 的 kind job `119136160482` 成功创建真实集群并完成 Service DNS/HTTP、宿主 HTTP、自愈/扩缩、HTTP 探针故障、坏镜像回滚与 ConfigMap 更新；验证器在空 EndpointSlice 的 `endpoints: null` 上失败，未声称整轮通过。
- 修复验证器兼容 null/空列表，并等待实际 Service 请求失败；复验运行 `39575347931`、kind job `119139382891`（提交 `c81eff9`）已完整通过，真实运行 JSON 已取回 `research/runtime-validation.json`。
- 本地构建核对前言加 14 章、3 附录共 18 个阅读单元，书稿/EPUB/网页/搜索/实验包一致。EPUBCheck 5.4.0 为 0 错误、0 警告。
- Chromium 本地检查通过：浅色默认、共享深色与标签同步、目录、全文搜索、字号、存储关闭回退、所有 18 单元在 320/390px 无页面横向溢出，无 JavaScript 可阅读和翻页。

- 完整复验通过 PVC 相同 UID、Pod UID 改变且文件读回；CPU 请求过大与 nodeSelector 不匹配分别出现实际 Pending/Unschedulable 证据。

公共完整流水线在 ConfigMap 滚动重启后的一次立即 HTTP 请求中遇到超时，说明控制面 Ready 与数据面可达的观察时点不同。自动化现使用有 60 秒上限的实际内容恢复检查，持续失败仍会超时；相关观察已补入第 6 章。

## 尚待验收

公共源码、完整发布 CI、Pages、公网阅读与 Release 下载。

## 未实现或未测试

单节点 kind 不证明多节点容错或节点丢失后存储恢复。未验证生产 TLS/RBAC 安全基线、NetworkPolicy 实际执行、Metrics Server/HPA、OOM/CPU 限流负载和生产吞吐。PVC 跨 Pod 保留不等于备份；端口转发不代表 Service 负载均衡实测。探针故障检查使用独立测试 Pod，避免把就绪与存活的因果混淆。

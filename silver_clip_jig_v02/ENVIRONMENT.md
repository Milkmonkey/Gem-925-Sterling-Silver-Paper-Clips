# 云端开发环境

当前实例已实际运行CAD重建和校验，不需要数据库、Web服务或额外密钥。

| 项目 | 本次实际版本/位置 |
|---|---|
| 系统 | Debian GNU/Linux 13，Linux |
| Python | 3.12.14 |
| OpenSCAD | 2021.01，`/usr/bin/openscad` |
| Python环境 | `/workspace/.venvs/silver-clip`，复用平台基础包并安装缺少依赖 |
| CadQuery / OpenCascade绑定 | 2.7.0 / cadquery-ocp 7.8.1.1.post1 |
| 数值/网格/截面 | numpy 2.3.5、trimesh 4.12.2、shapely 2.1.2、networkx 3.5 |
| 制图 | matplotlib 3.10.8、Pillow 12.3.0；实际渲染使用无X的CPU深度缓冲 |
| 工作目录 | `/workspace/Gem-925-Sterling-Silver-Paper-Clips/silver_clip_jig_v02` |

执行 `bash source/install_tools.sh` 可以刷新固定版本依赖；在本实例已重跑验证。OpenSCAD由当前基础环境提供，脚本检查其存在；没有关闭TLS、包签名或校验机制来安装依赖。

实际工作流见README：安装→`source/build.py`→`source/validate.py`→`source/design_review.py`。最终校验11个STL文件、11个导出孔截面、2163个名义动作姿态。`results.json`记录本次UTC时间、参数SHA-256及各STL的SHA-256，失败的检查不会保留旧的PASS结果文件。

安装命令封装和启动/检查说明已写入环境配置草稿的 `install_script`、`start_skill`。后者明确使用现有checkout、不另建worktree、无需后台进程，并提示不能将CAD通过等同于银丝功能通过。网络配置草稿增加 `patents.google.com`、`patentimages.storage.googleapis.com`；本实例已成功下载并阅读对应资料。

草稿保存不会自动执行脚本、应用运行时变更或发布环境。用户需在环境设置审阅并保存，再发布环境。未在新的发布后任务中验证恢复能力。仓库新文件及生成物均留在当前工作区供审阅，没有为了设置环境重置或推送仓库。

# GitHub Actions 云端 Windows 构建说明

## 这个方案不会影响本机 Windows

本项目的 Windows 可执行文件构建发生在 GitHub 云端的 GitHub-hosted Windows runner 上，不在你的 Windows 本机执行。

你的本机只需要做两件事之一：

- `git push` 代码到 GitHub
- 或者在 GitHub 网页手动点击 `Run workflow`

本方案不会在你的 Windows 本机安装 Python、pip package、PyInstaller、Inno Setup 或其他构建工具，也不需要写入 `C:\`、`Program Files`、注册表或 Windows PATH。

## Workflow

Workflow 名称：

`Build OKNG Inspector Windows`

Workflow 文件：

`.github/workflows/build-windows.yml`

当前使用：

- `runs-on: windows-2025`
- `actions/checkout@v6`
- `actions/setup-python@v6`
- `actions/upload-artifact@v4`
- Python 3.11 x64

这些 action tag 已通过 GitHub 官方仓库 tag 查询确认存在。如果未来 GitHub runner 不支持 `windows-2025`，可以把 workflow 改成 `windows-2022`，其他构建逻辑不需要改变。

## 手动运行方式

打开仓库页面：

https://github.com/binpengjie/acoustics

然后点击：

`Actions` → `Build OKNG Inspector Windows` → `Run workflow`

## Tag 触发方式

推送 `v*` tag 会自动触发构建，例如：

```bash
git tag v0.1.0
git push origin v0.1.0
```

## 构建成功后下载 artifact

进入对应的 Actions run 页面，在页面底部找到：

`Artifacts` → `OKNG_Inspector_Windows_v0.1`

下载后会得到云端构建出的 portable zip，其中主要文件是：

`OKNG_Inspector_Windows_v0.1.zip`

普通用户使用方式：

1. 下载 zip
2. 发给用户
3. 用户解压
4. 双击 `OKNG_Inspector.exe`

## portable zip 和 setup.exe 的区别

`zip` 是绿色便携版：

- 解压即用
- 不需要安装 Python
- 不写系统注册表
- 删除整个文件夹即可卸载

`setup.exe` 是未来可选的正式安装版：

- 可以创建桌面图标
- 可以创建开始菜单入口
- 可以提供 Windows 卸载入口
- 需要额外安装器脚本，例如 Inno Setup

当前优先产物是 portable zip。若以后 workflow 中生成 `dist/OKNG_Inspector_Setup_v0.1.exe`，也会作为 artifact 上传。

## Smoke test 覆盖内容

GitHub Actions 构建完成后会运行：

`python scripts/smoke_test_windows.py`

测试覆盖：

- 文件完整性检查：exe、dist 目录、models、configs、app.py、src、用户 README
- 依赖导入：numpy、scipy、sklearn、joblib、streamlit、pandas、matplotlib、PyWavelets、soundfile
- 模型加载：搜索并 `joblib.load` 所有 `models/**/*.joblib`
- 最小 wav 预测链路：如果没有样例 wav，自动生成 synthetic wav 并调用 `batch_predict.py`
- 输出文件检查：`smoke_test_outputs/smoke_test_summary.json`、日志、预测 CSV、HTML report
- Streamlit localhost 启动检查：优先启动打包后的 exe，访问 `http://127.0.0.1:8765`；若 exe 检测不稳定，则 fallback 到源码 `python -m streamlit run app.py`

## Smoke test 的限制

Smoke test 只证明云端构建出的核心链路没有立即崩溃，不等于完整真实用户测试。

正式发版前，仍建议在一台干净的 Windows 10/11、无 Python 环境的机器上人工测试：

1. 解压 artifact
2. 双击 `OKNG_Inspector.exe`
3. 上传真实音频
4. 运行 Balanced / High Recall 模式
5. 导出 CSV 和 HTML report

## Private repo 免费额度注意

Windows portable zip 可能比较大，因为里面包含 Python runtime、Streamlit、scikit-learn、scipy、模型文件和 PyInstaller 依赖。

Workflow 已设置：

`retention-days: 3`

这样 artifact 不会长期占用 GitHub Actions 存储额度。

## 如果模型文件太大

如果后续模型变大，普通 git 仓库可能不适合直接保存模型。可选方案：

- Git LFS
- private GitHub Release asset
- 构建时从受控下载地址获取模型
- 手动把模型放入 source package，再触发构建

当前模型文件体积较小，仍保留在仓库中，便于 GitHub Actions 直接构建。

## 生产使用警告

该 app 是可用的本地检测界面，但模型阈值必须在新的日期、产品类型和采集条件上重新验证。之前随机切分性能很好，但按日期/产品/条件分组留出时鲁棒性弱于随机切分结果。

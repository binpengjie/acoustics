# Windows 本地声学 OK/NG 检测 Web App

## 1. 软件用途
本软件用于工业产品声音检测。Windows 用户在本机启动后，通过浏览器上传单个音频或选择文件夹，得到 OK / NG / REVIEW 检测结果并导出 CSV。

## 2. 安装步骤
1. 安装 Windows Python 3.11。
2. 解压本软件文件夹。
3. 双击 `install_env.bat`。
4. 等待依赖安装完成。

## 3. 启动
双击 `run_app.bat`，浏览器会打开 `http://localhost:8501`。

## 4. 单文件检测
在“首页 / 单文件检测”上传 WAV 文件，点击“开始检测”。

## 5. 批量文件夹检测
在“批量检测”输入本地文件夹路径，例如 `C:\audio_batch`，点击运行。结果会保存到 `outputs/inference_history/`。

## 6. 输出列说明
- `lineB_pred`: 监督模型预测 OK/NG
- `lineB_score_or_probability`: Line B 的 NG 概率分数
- `lineA_anomaly_score`: Line A 到 OK 分布的 Mahalanobis 距离
- `lineA_threshold`: Line A 阈值
- `lineA_flag`: Line A 是否异常
- `final_decision`: OK / NG / REVIEW / FAILED
- `decision_reason`: 判定原因

## 7. OK / NG / REVIEW
- OK：正常
- NG：异常，建议拦截
- REVIEW：监督模型认为 OK，但异常监控发现偏离 OK 分布，建议人工复核
- FAILED：文件无法处理

## 8. 模型逻辑
Line B 是主分类器。Line A 是异常监控器和漂移检测器。

## 9. 阈值
默认 Line A 阈值为 162.18298627520178。降低阈值会增加 NG 检出，但也增加 OK 误报。

## 10. 推荐生产流程
默认使用融合模式；定期用“新批次校准 / 验证”页面检查近期批次；如果 NG 漏检增加，应重训 Line B 并重新校准 Line A。

## 11. 故障排查
- Python 找不到：安装 Python 3.11 并勾选 PATH。
- 模型加载失败：确认 `models/` 文件夹完整。
- 音频失败：优先使用 WAV；MP3/M4A 取决于本机音频解码支持。


## Python 安装器说明

新版 `install_env.bat` 不再只依赖 `py` 命令。它会依次尝试：

1. 用户指定的 `OKNG_PYTHON`
2. `py -3.11` / `py -3.10`
3. `python` / `python3`
4. 常见 Python 安装目录
5. `winget` 用户级自动安装 Python 3.11

如果所有方式都失败，请手动安装 Python 3.11，并勾选 `Add python.exe to PATH`、`pip` 和可选的 `py launcher`。

如果工厂电脑不能联网，可以在有网电脑下载依赖 wheel 文件，放入软件目录下的 `wheelhouse/` 文件夹，再运行 `install_env.bat`。安装日志保存在 `logs/install_env.log`。

如果 Python 装在特殊位置，可以这样运行：

```bat
set OKNG_PYTHON=C:\Path\To\python.exe
install_env.bat
```

# Windows 便携版构建说明

目标：生成一个用户无需安装 Python 的绿色便携文件夹。

## 重要区别

- 构建电脑：需要安装 Python 3.11，用来运行 PyInstaller 打包。
- 最终用户电脑：不需要安装 Python，只需要解压文件夹并双击 `OKNG_Inspector.exe`。

## 构建步骤

1. 在构建电脑安装 64 位 Python 3.11：

   https://www.python.org/downloads/windows/

2. 安装时勾选：

   `Add python.exe to PATH`

3. 打开新的命令提示符，确认：

```bat
python --version
```

4. 进入项目文件夹，运行：

```bat
build_windows.bat
```

5. 成功后得到：

```text
dist\OKNG_Inspector_Windows\OKNG_Inspector.exe
dist\OKNG_Inspector_Windows_v0.1.zip
```

## 用户如何使用

把 `OKNG_Inspector_Windows_v0.1.zip` 发给用户。用户解压后双击：

```text
OKNG_Inspector.exe
```

## 如何彻底删除

关闭程序后，删除整个文件夹即可：

```text
OKNG_Inspector_Windows
```

不会写注册表，不安装系统服务，不需要管理员权限。

## 大小预估

PyInstaller 会把 Python 运行时、Streamlit、scikit-learn、scipy、模型文件一起放进便携目录。

常见大小：

- 未压缩文件夹：约 400 MB 到 800 MB
- zip 后：约 150 MB 到 350 MB

实际大小以 Windows 构建结果为准。

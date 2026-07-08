# OKNG Inspector 真实 Windows 验收计划

## 当前服务器 KVM 检查结果

检查时间：2026-07-08

服务器：

```text
Linux seismiclab 6.8.0-124-generic x86_64 GNU/Linux
```

硬件虚拟化：

```text
egrep -c '(vmx|svm)' /proc/cpuinfo = 128
```

KVM 设备：

```text
/dev/kvm = crw-rw----+ 1 root kvm 10, 232
```

资源：

```text
Memory: 125 GiB total, about 113 GiB available
/data1: 73T total, 54T available
/data2: 73T total, 68T available
```

结论：服务器硬件支持 KVM，内存和磁盘足够运行 Windows VM。

## 当前 blocker

当前 `pengjie` 用户不能直接创建 KVM Windows VM：

```text
id = uid=1001(pengjie) gid=1001(pengjie) groups=1001(pengjie),100(users)
/dev/kvm readable = no
/dev/kvm writable = no
qemu-system-x86_64 = missing
qemu-img = missing
virt-install = missing
virsh = missing
sudo -n true = sudo password required
```

这意味着当前账号缺少：

- `/dev/kvm` 访问权限
- QEMU/libvirt 工具
- 免密码 sudo 安装权限
- Windows ISO / existing Windows VM image

因此现在不能在这台 Linux server 上直接完成真实 Windows VM 验收。

## 最小服务器授权方案

需要管理员执行以下命令，之后 `pengjie` 重新登录：

```bash
sudo apt-get update
sudo apt-get install -y qemu-system-x86 qemu-utils virtinst libvirt-daemon-system libvirt-clients ovmf swtpm
sudo usermod -aG kvm,libvirt pengjie
sudo setfacl -m u:pengjie:rw /dev/kvm
```

重新登录后验证：

```bash
id
test -r /dev/kvm && test -w /dev/kvm && echo KVM_OK
qemu-system-x86_64 --version
qemu-img --version
virsh list --all
```

还需要提供：

- Windows 10/11 或 Windows Server ISO
- VirtIO driver ISO，常用文件名 `virtio-win.iso`
- 可用 Windows license / evaluation license

建议 VM 路径：

```text
/data1/pengjie/vms/okng-windows/
```

## QEMU/KVM VM 建议配置

建议：

- CPU: 8 cores
- RAM: 16 GiB
- Disk: 120 GiB qcow2
- Network: user-mode NAT first; bridge only if需要局域网访问
- Firmware: OVMF UEFI
- TPM: Windows 11 需要 swtpm；Windows Server/Windows 10 可先不需要

创建磁盘：

```bash
mkdir -p /data1/pengjie/vms/okng-windows
qemu-img create -f qcow2 /data1/pengjie/vms/okng-windows/okng-windows.qcow2 120G
```

示例 `virt-install`：

```bash
virt-install \
  --name okng-windows \
  --memory 16384 \
  --vcpus 8 \
  --cpu host-passthrough \
  --disk path=/data1/pengjie/vms/okng-windows/okng-windows.qcow2,format=qcow2,bus=virtio \
  --cdrom /data1/pengjie/iso/Windows.iso \
  --disk /data1/pengjie/iso/virtio-win.iso,device=cdrom \
  --os-variant win11 \
  --network network=default,model=virtio \
  --graphics spice \
  --boot uefi
```

## Windows VM 验收步骤

在 Windows VM 里打开 PowerShell：

```powershell
git clone git@github.com:binpengjie/acoustics.git
cd acoustics
```

安装 Python 3.11 x64。可用 `winget`：

```powershell
winget install -e --id Python.Python.3.11
```

重新打开 PowerShell：

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements_windows.txt
```

构建：

```powershell
.\build_windows.bat
```

验收：

```powershell
.\.venv\Scripts\python.exe scripts\windows_acceptance_test.py --package-root dist\OKNG_Inspector_Windows --output-dir windows_acceptance_outputs
```

成功标准：

- `dist\OKNG_Inspector_Windows\OKNG_Inspector.exe` 存在
- `OKNG_Inspector.exe` 能启动
- `http://127.0.0.1:8765` 有 HTTP 响应
- synthetic WAV 可预测
- 生成 `predictions.csv`
- 生成 batch `report.html`
- 生成 standalone `standalone_report.html`
- `windows_acceptance_outputs\windows_acceptance_summary.json` 的 `status` 为 `passed`

## 现有 Windows 机器或云 Windows 替代方案

如果服务器暂时不能开 KVM，最小可执行替代方案是：

1. 使用一台干净 Windows 10/11 或 Windows Server 2022 机器。
2. 不在你的主力 Windows 主机上测试，避免污染。
3. 建议使用：
   - Azure Windows Server VM
   - AWS EC2 Windows Server
   - 腾讯云/阿里云 Windows Server
   - 一台可重装/可删除的测试 Windows PC
4. 按上面的 Windows VM 验收步骤执行。

## 修复优先级

如果 `OKNG_Inspector.exe` 在真实 Windows 中失败：

1. 先看 `windows_acceptance_outputs\windows_acceptance_summary.json`
2. 再看 `windows_acceptance_outputs\launcher_stdout_stderr.log`
3. 再看 portable folder 下的 `OKNG_launcher_error.log`
4. 优先修 `launcher.py` / `app.py` / packaging included files
5. 不继续盲目改 GitHub Actions workflow

只有在真实 Windows 验收通过后，再把同样逻辑同步回 GitHub Actions，或把 Windows VM 注册成 GitHub self-hosted runner。

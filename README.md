# BiliBili 视频下载工具

该项目包含两个 Python 脚本，用于下载 Bilibili 视频，支持单个视频、分 P 合集、用户投稿以及收藏夹下载。可选择保存纯视频画面、纯音频或合成后的视频文件。

## 功能特点

- 支持输入 **BV 号**、**视频链接**、**UID**（用户投稿）、**MLID**（收藏夹 ID）
- 自动识别目标类型并选择合适的下载方式
- 可选择下载模式：
  - 仅视频画面（不带声音）
  - 仅音频（MP3 格式）
  - 合成视频（音视频合并，需要 ffmpeg）
- 支持下载合集（分 P 视频、投稿列表、收藏夹列表）
- 自动过滤文件名中的非法字符，兼容 Windows 系统
- 使用彩色终端提示，提升使用体验

## 文件说明

| 文件名 | 说明 |
|--------|------|
| `hook_-.py` | 早期版本，通过页面解析获取视频信息，功能基本完善 |
| `hook_+.py` | 改进版本，使用 Bilibili API 获取视频/音频流地址，更稳定可靠，新增用户投稿和收藏夹下载功能 |

两个脚本均可独立使用，命令行参数兼容。推荐使用 `hook_+.py`。

## 环境要求

- Python 3.6+
- 依赖库：`requests`, `beautifulsoup4`
- [ffmpeg](https://ffmpeg.org/)（如需合成视频，必须将 `ffmpeg.exe` 放在脚本同一目录下，或加入系统 PATH）

## 安装依赖

```bash
pip install requests beautifulsoup4
```

## 获取 ffmpeg

1. 从 [ffmpeg 官网](https://ffmpeg.org/download.html) 下载适合你系统的版本（Windows 用户下载 `ffmpeg-release-full.7z`）。
2. 解压，将 `bin` 目录下的 `ffmpeg.exe` 复制到脚本所在文件夹，或将其所在目录添加到系统环境变量 PATH 中。

## 使用方法

### 命令行参数说明

```
usage: hook_+.py [-h] [-V] [-A] [-M] (-o | -s) [-f FILE] target

BiliBili视频爬取工具(慎用)

positional arguments:
  target                目标 BvID/Url/Uid(set)/Mlid(set)（请加引号）

options:
  -h, --help            显示帮助信息
  -V, --videoFile       保存视频文件（纯画面，无声音）
  -A, --audioFile       保存音频文件（MP3 格式）
  -M, --mixFile         保存合成后的视频文件（需要 ffmpeg）
  -o, --one             下载单个视频（适用于 BV 号/URL）
  -s, --set             下载合集（适用于分 P 视频、用户投稿、收藏夹）
  -f FILE, --file FILE  保存路径（默认上级目录，建议用绝对路径）
```

### 使用示例

#### 1. 下载单个视频（仅合成 MP4）

```bash
python hook_+.py "BV1xx411c7mD" -M -o
```

#### 2. 下载视频并同时保存视频画面和音频

```bash
python hook_+.py "https://www.bilibili.com/video/BV1xx411c7mD?p=2" -V -A -o
```

#### 3. 下载某个用户的所有投稿

```bash
python hook_+.py "https://space.bilibili.com/123456" -M -s -f "D:/downloads"
```
（`123456` 为 UID，脚本会自动创建以 `HL_UID` 命名的文件夹）

#### 4. 下载收藏夹中的所有视频

```bash
python hook_+.py "ml123456" -M -s
```
（`ml123456` 为收藏夹 ID，脚本会自动创建 `BK_123456` 文件夹）

#### 5. 下载分 P 合集（自动识别）

```bash
python hook_+.py "https://www.bilibili.com/video/BV1xx411c7mD" -M -s
```

## 注意事项

- 首次运行脚本会检查当前目录下是否存在 `ffmpeg.exe`，若不存在且选择了 `-M` 选项，合成将失败。
- 下载大量视频时请合理控制频率，避免触发 B站 的风控机制。
- 收藏夹和用户投稿接口可能存在请求频率限制，脚本已加入自动重试机制。
- 文件名中的非法字符（`\/:*?"<>|`）会被自动去除。
- 建议将目标参数用引号括起来，避免 shell 解析特殊字符。

## 常见问题

**Q: 为什么下载的视频没有声音？**  
A: 如果使用了 `-V` 选项，只保存视频画面。若想保留声音，请使用 `-M`（合成）或 `-A`（单独音频）。

**Q: 提示“请将ffmpeg.exe移动至此目录下”怎么办？**  
A: 下载 ffmpeg.exe 并放到脚本同一目录，或确保 ffmpeg 已加入系统 PATH。

**Q: 下载合集时部分视频失败怎么办？**  
A: 脚本会跳过出错的视频并继续下载，日志中会用红色提示。可手动重试失败的 BV 号。

## 免责声明

本工具仅供学习交流使用，请勿用于商业用途或大规模抓取。下载的视频请遵守版权法规，仅限个人研究。

## 许可证

MIT License
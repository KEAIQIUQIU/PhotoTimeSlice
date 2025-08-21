# 时间切片照片生成器 (Time Slice Photo Generator)

## 概述

时间切片照片生成器是一个强大的工具，用于从一系列连续拍摄的照片中创建时间切片(time slice)效果。
时间切片是一种将不同时间点的影像组合到同一张图片中的技术，可以创造出令人惊叹的视觉效果。


## 功能特点

- **多种切片模式**：
  - 垂直切片
  - 水平切片
  - 圆形扇形切片
  - 椭圆形扇形切片
  - 椭圆形环带切片
  - 矩形环带切片
  - 圆形环带切片
  - 垂直S型曲线
  - 水平S型曲线
  
- **模块化设计**：
  - 每种切片算法独立为一个模块
  - 易于扩展新的切片算法
  - 清晰的代码结构
  
- **双界面支持**：
  - 图形用户界面(GUI)
  - 命令行界面(CLI)
  
- **多语言支持**：
  - 中文
  - 英文
  
- **主题系统**：
  - 浅色模式
  - 深色模式
  - 跟随系统
  
- **其他特性**：
  - 线性模式控制
  - 逆序排序选项
  - 处理完成后自动打开图片
  - 实时进度显示和日志输出
  - 支持多种图片格式，包括RAW格式

## 安装指南

### 依赖项

- Python 3.10
- PyQt5
- Pillow (PIL)
- tqdm
- numpy
- rawpy (用于RAW格式支持)

### 安装步骤
1. 安装依赖：
   ```bash
   pip install pyqt5 pillow tqdm numpy rawpy
   ```

3. 运行应用程序：
   - **图形界面**：
     ```bash
     python gui.py
     ```
   - **命令行界面**：
     ```bash
     python cli.py -i input_dir -o output_dir -t slice_type [其他选项]
     ```

## 使用说明

### 图形界面(GUI)

1. 选择输入目录（包含一系列按时间顺序拍摄的图片）
2. 选择输出目录（用于保存生成的时间切片图片）
3. 选择切片类型
4. 根据需要调整其他选项（如位置、线性模式、逆序排序等）
5. 点击"生成时间切片"按钮开始处理
6. 处理完成后，结果图片将自动保存并在默认图片查看器中打开

### 命令行界面(CLI)

基本用法：
```bash
python cli.py -i input_dir -o output_dir -t slice_type [其他选项]
```

可用选项：
```
-i, --input      输入文件夹路径（默认为"input"）
-o, --output     输出文件夹路径（默认为"output"）
-t, --type       切片类型（必需）：
                 vertical, horizontal, circular_sector,
                 elliptical_sector, elliptical_band,
                 rectangular_band, circular_band,
                 vertical_s, horizontal_s
-p, --position   条带位置：left/center/right/top/bottom 或 0.0-1.0（默认为"center"）
-l, --linear     启用线性模式
-r, --reverse    逆序排序
```

示例：
```bash
python cli.py -i ./sunset_photos -o ./results -t vertical_s --position center --linear
```

### 支持的图片格式

- JPEG, PNG, TIFF
- RAW格式：NEF, DNG, CR2, CR3, ARW, RAF, ORF, RW2
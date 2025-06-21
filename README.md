# 时间切片照片生成器

这是一个用于创建时间切片(time slice)照片的Python工具，可以从一系列连续拍摄的照片中生成具有时间维度效果的合成图像。提供命令行界面(CLI)和图形用户界面(GUI)两种操作方式，满足不同用户的需求。

## 目录结构

```
Software/
├─ GUI/                 # 图形用户界面版本
│  └─ 2.1/             # GUI 2.1版本
│     ├─ gui.py         # GUI主程序
│     └─ timeslice_core.py # 核心功能模块
   └─ 2.2/             # GUI 2.2版本（最新版本）
│     ├─ gui.py         # GUI主程序
│     └─ timeslice_core.py # 核心功能模块
│
└─ CLI/                 # 命令行界面版本
   ├─ 1.0/             # CLI 1.0版本
   │  └─ timeslice.py   # 命令行程序
   └─ 1.1/             # CLI 1.1版本
   │  └─ timeslice.py   # 命令行程序
   └─ 1.2/             # CLI 1.2版本（最新版本）
      └─ timeslice.py   # 命令行程序
```

## 功能特点
- 支持多种时间切片模式：
  - **垂直切片**：纵向时间条带效果
  - **水平切片**：横向时间条带效果
  - **圆形切片**：径向时间切片效果
  - **圆形环带切片**：从中心向外扩散的圆形环带
  - **椭圆形扇形切片**：椭圆形径向时间切片
  - **椭圆形环带切片**：从中心向外扩散的椭圆形环带
  - **矩形环带切片**：从中心向外扩散的矩形环带（原"矩形切片"）
- **支持广泛的图像格式**：
  - 普通格式: JPG, JPEG, PNG, TIF, TIFF
  - RAW格式: NEF(Nikon), DNG(Adobe), CR2/CR3(Canon), ARW(Sony), RAF(Fujifilm), ORF(Olympus), RW2(Panasonic)
- 输出尺寸与输入图像一致
- 输出高质量无损JPEG图像
- 支持正序/逆序排序
- **图形用户界面(GUI)**：直观易用的操作界面
- **完成后自动打开图片**：可选功能，处理完成后自动打开生成的时间切片图片

## 安装依赖

### 核心功能依赖：
```
pip install Pillow tqdm
```

### RAW格式支持依赖：
```
pip install rawpy
```

### GUI界面依赖：
```
pip install PyQt5
```

## 命令行使用方式 (CLI)

```bash
python timeslice.py -t [切片类型] -i [输入目录] -o [输出目录] [选项]
```

### 基本参数

| 参数 | 简写 | 描述 | 默认值 |
|------|------|------|--------|
| `--input` | `-i` | 输入目录，包含源图片 | `input` |
| `--output` | `-o` | 输出目录，保存结果 | `output` |
| `--type` | `-t` | **必须**：切片类型 (`vertical`, `horizontal`, `circular`, `elliptical_sector`, `elliptical_band`, `rectangular_band`, `circular_band`) | 无 |

### 高级选项

| 选项 | 简写 | 描述 | 适用切片类型 |
|------|------|------|-------------|
| `--position` | `-p` | 条带位置 (`left`, `center`, `right`, `top`, `bottom` 或 0.0-1.0) | 垂直/水平 |
| `--linear` | `-l` | 启用线性模式：<br>- 垂直/水平切片：每张图片取不同部位<br>- 圆形切片：扇形大小随时间变化 | 所有类型 |
| `--reverse` | `-r` | 逆序排序（使用时间倒序的照片序列） | 所有类型 |

### 使用示例

1. **垂直时间切片（居中位置）**：
   ```bash
   python timeslice.py -t vertical -p center -i photos -o result
   ```

2. **水平时间切片（线性模式）**：
   ```bash
   python timeslice.py -t horizontal -p top -l -i photos -o result
   ```

3. **圆形时间切片（统一大小模式）**：
   ```bash
   python timeslice.py -t circular -i photos -o result
   ```

4. **圆形时间切片（变化大小模式）**：
   ```bash
   python timeslice.py -t circular -l -i photos -o result
   ```

5. **圆形环带时间切片**：
   ```bash
   python timeslice.py -t circular_band -i photos -o result
   ```
   
6. **逆序时间切片（时间倒流效果）**：
   ```bash
   python timeslice.py -t vertical -r -i photos -o result
   ```
   
7. **矩形环带时间切片**：
   ```bash
   python timeslice.py -t rectangular_band -i photos -o result
   ```
   
## GUI使用方式

```bash
python gui.py
```

### 使用流程
1. 设置输入目录（包含源图片）
2. 设置输出目录（保存结果）
3. 选择切片类型
4. 根据需要调整位置和其他选项
5. 勾选"完成后自动打开图片"（可选）
6. 点击"生成时间切片"按钮开始处理

处理完成后，如果勾选了"完成后自动打开图片"，系统会自动使用默认图片查看器打开生成的时间切片图片。

## 输入要求

1. 所有输入图片必须具有相同的尺寸
2. **支持格式**：
   - **普通格式**: JPG, JPEG, PNG, TIF, TIFF
   - **RAW格式**: 
     - Nikon: NEF
     - Canon: CR2, CR3
     - Sony: ARW
     - Fujifilm: RAF
     - Olympus: ORF
     - Panasonic: RW2
     - Adobe: DNG

## 输出结果

结果将保存为无损JPEG格式，文件名为 `timeslice.jpg`，位于指定的输出目录中。

## 注意事项

- 确保所有输入图片尺寸一致

## 版本历史

### CLI 版本历史
- **1.0**：
  - 支持垂直、水平和圆形切片
  - 基本位置控制
  - 支持JPG和部分RAW格式
- **1.1**：
  - 添加逆序排序功能
  - 支持更多图像格式（PNG、TIF、TIFF）
  - 支持更多RAW格式（佳能CR2/CR3、索尼ARW、富士RAF、奥林巴斯ORF、松下RW2）
- **1.2(当前版本)**：
  - 将"矩形切片"更名为"矩形环带切片"
  - 新增"圆形环带切片"功能
  - 新增"椭圆形扇形切片"功能
  - 新增"椭圆形环带切片"功能

### GUI 版本历史
- **2.1**：
  - 直观的图形界面
  - 实时进度显示
  - 详细的日志输出
  - "完成后自动打开图片"功能
- **2.2(当前版本)**：
  - 将"矩形切片"更名为"矩形环带切片"
  - 新增"圆形环带切片"功能
  - 新增"椭圆形扇形切片"功能
  - 新增"椭圆形环带切片"功能
  - 优化了操作逻辑

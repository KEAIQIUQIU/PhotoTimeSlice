import argparse
from PIL import Image, ImageDraw
from pathlib import Path
from tqdm import tqdm
import re
import sys
import math

# 检查是否在打包环境中
is_frozen = getattr(sys, 'frozen', False)


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    """自然排序键函数，支持数字顺序"""
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(str(s))]


def load_images(input_dir, reverse=False):
    """加载输入文件夹中的所有图片，支持多种格式，按文件名自然排序"""
    # 支持的图像格式扩展名
    image_extensions = [
        # 普通格式
        "*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff",
        # RAW格式
        "*.nef", "*.dng", "*.cr2", "*.cr3", "*.arw", "*.raf", "*.orf", "*.rw2"
    ]

    image_paths = []
    for ext in image_extensions:
        image_paths.extend(Path(input_dir).glob(ext))

    # 使用自然排序对文件名排序
    image_paths.sort(key=natural_sort_key)

    # 如果需要逆序排序
    if reverse:
        image_paths = list(reversed(image_paths))

    images = []
    if not is_frozen:
        print(f"加载 {len(image_paths)} 张图片...")

    for path in tqdm(image_paths, desc="加载图片", disable=is_frozen):
        if path.suffix.lower() in ['.nef', '.dng', '.cr2', '.cr3', '.arw', '.raf', '.orf', '.rw2']:
            try:
                import rawpy
                with rawpy.imread(str(path)) as raw:
                    rgb = raw.postprocess()
                img = Image.fromarray(rgb)
                images.append(img)
            except ImportError:
                raise ImportError("请安装rawpy库以处理RAW格式: pip install rawpy")
        else:
            images.append(Image.open(path))

    return images


def create_vertical_slice(images, position, linear=False):
    """创建纵向条形时间切片 - 输出尺寸与输入相同"""
    img_w, img_h = images[0].size
    num_images = len(images)

    # 创建输出图像 - 与输入相同尺寸
    result = Image.new('RGB', (img_w, img_h))

    # 条带宽度 = 总宽度 / 图片数量
    strip_width = max(1, img_w // num_images)

    print("生成纵向切片...")
    for i, img in enumerate(tqdm(images, desc="处理图片")):
        # 计算裁剪位置
        if linear:
            # 线性模式：每张图片取不同部位
            crop_x = int(i * (img_w - strip_width) / (num_images - 1)) if num_images > 1 else 0
        else:
            # 固定位置模式
            if position == "left":
                crop_x = 0
            elif position == "right":
                crop_x = img_w - strip_width
            elif position == "center":
                crop_x = (img_w - strip_width) // 2
            else:  # 自定义位置 (0.0-1.0)
                try:
                    pos = float(position)
                    crop_x = int((img_w - strip_width) * pos)
                except ValueError:
                    crop_x = (img_w - strip_width) // 2

        # 计算粘贴位置
        paste_x = i * strip_width

        # 裁剪条带
        strip = img.crop((crop_x, 0, crop_x + strip_width, img_h))

        # 如果条带宽度需要调整
        if strip.width < strip_width:
            strip = strip.resize((strip_width, img_h))
        elif strip.width > strip_width:
            strip = strip.crop((0, 0, strip_width, img_h))

        # 粘贴到结果图像
        result.paste(strip, (paste_x, 0))

    return result


def create_horizontal_slice(images, position, linear=False):
    """创建横向条形时间切片 - 输出尺寸与输入相同"""
    img_w, img_h = images[0].size
    num_images = len(images)

    # 创建输出图像 - 与输入相同尺寸
    result = Image.new('RGB', (img_w, img_h))

    # 条带高度 = 总高度 / 图片数量
    strip_height = max(1, img_h // num_images)

    print("生成横向切片...")
    for i, img in enumerate(tqdm(images, desc="处理图片")):
        # 计算裁剪位置
        if linear:
            # 线性模式：每张图片取不同部位
            crop_y = int(i * (img_h - strip_height) / (num_images - 1)) if num_images > 1 else 0
        else:
            # 固定位置模式
            if position == "top":
                crop_y = 0
            elif position == "bottom":
                crop_y = img_h - strip_height
            elif position == "center":
                crop_y = (img_h - strip_height) // 2
            else:  # 自定义位置 (0.0-1.0)
                try:
                    pos = float(position)
                    crop_y = int((img_h - strip_height) * pos)
                except ValueError:
                    crop_y = (img_h - strip_height) // 2

        # 计算粘贴位置
        paste_y = i * strip_height

        # 裁剪条带
        strip = img.crop((0, crop_y, img_w, crop_y + strip_height))

        # 如果条带高度需要调整
        if strip.height < strip_height:
            strip = strip.resize((img_w, strip_height))
        elif strip.height > strip_height:
            strip = strip.crop((0, 0, img_w, strip_height))

        # 粘贴到结果图像
        result.paste(strip, (0, paste_y))

    return result


def create_circular_slice(images, linear=False):
    """
    创建圆形时间切片 - 填满整个图像
    linear: 是否启用线性模式（控制扇形大小变化）
    """
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2
    radius = min(center_x, center_y)
    num_images = len(images)

    # 创建空白画布 - 与输入相同尺寸
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))

    # 计算角度步长
    angle_step = 360 / num_images

    print("生成圆形切片...")
    for i, src_img in enumerate(tqdm(images, desc="处理图片")):
        # 计算当前扇形的角度范围
        start_angle = i * angle_step
        end_angle = (i + 1) * angle_step

        # 统一扇形大小：所有扇形使用最大半径
        if not linear:
            r = radius
        # 线性变化：从中心到边缘均匀分布
        else:
            r = radius * (i / (num_images - 1)) if num_images > 1 else radius

        # 创建扇形蒙版
        mask = Image.new('L', (img_w, img_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.pieslice(
            [center_x - r, center_y - r,
             center_x + r, center_y + r],
            start_angle, end_angle, fill=255
        )

        # 应用蒙版并粘贴
        masked_img = Image.composite(src_img, result, mask)
        result.paste(masked_img, (0, 0))

    return result


def create_elliptical_sector_slice(images, linear=False):
    """
    创建椭圆形扇形时间切片 - 填满整个图像
    linear: 是否启用线性模式（控制扇形大小变化）
    """
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2

    # 计算椭圆的半长轴和半短轴
    a = img_w // 2  # 半长轴（宽度方向）
    b = img_h // 2  # 半短轴（高度方向）

    num_images = len(images)

    # 创建空白画布 - 与输入相同尺寸
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))

    # 计算角度步长
    angle_step = 360 / num_images

    print("生成椭圆形扇形切片...")
    for i, src_img in enumerate(tqdm(images, desc="处理图片")):
        # 计算当前扇形的角度范围
        start_angle = i * angle_step
        end_angle = (i + 1) * angle_step

        # 统一扇形大小：所有扇形使用最大椭圆
        if not linear:
            current_a = a
            current_b = b
        # 线性变化：从中心到边缘均匀分布
        else:
            scale = i / (num_images - 1) if num_images > 1 else 1.0
            current_a = a * scale
            current_b = b * scale

        # 计算椭圆边界框
        ellipse_bbox = [
            center_x - current_a, center_y - current_b,
            center_x + current_a, center_y + current_b
        ]

        # 创建扇形蒙版
        mask = Image.new('L', (img_w, img_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.pieslice(ellipse_bbox, start_angle, end_angle, fill=255)

        # 应用蒙版并粘贴
        masked_img = Image.composite(src_img, result, mask)
        result.paste(masked_img, (0, 0))

    return result


def create_elliptical_band_slice(images):
    """
    创建椭圆形环带时间切片 - 从中心向周围一层一层扩散
    """
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2
    num_images = len(images)

    # 计算最大和最小尺寸
    max_size = max(img_w, img_h)
    min_size = max_size // 20  # 最小尺寸为最大尺寸的1/20

    # 创建空白画布 - 与输入相同尺寸
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))

    # 计算环带尺寸增量（使用平方根增长，中心环带变化快，边缘变化慢）
    size_step = (max_size - min_size) / math.sqrt(num_images)

    # 从中心向外处理
    print("生成椭圆形环带切片...")
    for i in tqdm(range(num_images), desc="处理环带"):
        # 当前环带的尺寸（使用平方根增长）
        size = min_size + math.sqrt(i) * size_step

        # 确保尺寸不超过最大尺寸
        size = min(size, max_size)

        # 计算当前椭圆的宽度和高度（保持原始比例）
        width = size * (img_w / max_size)
        height = size * (img_h / max_size)

        # 计算当前椭圆的位置（居中）
        left = center_x - width // 2
        top = center_y - height // 2
        right = center_x + width // 2
        bottom = center_y + height // 2

        # 创建椭圆蒙版
        mask = Image.new('L', (img_w, img_h), 0)
        mask_draw = ImageDraw.Draw(mask)

        # 绘制外椭圆
        mask_draw.ellipse([left, top, right, bottom], fill=255)

        # 绘制内椭圆（挖空中心部分）
        if i > 0:  # 第一个环带是实心的，不需要挖空
            # 计算内椭圆尺寸（上一个环带的尺寸）
            prev_size = min_size + math.sqrt(i - 1) * size_step
            prev_width = prev_size * (img_w / max_size)
            prev_height = prev_size * (img_h / max_size)

            prev_left = center_x - prev_width // 2
            prev_top = center_y - prev_height // 2
            prev_right = center_x + prev_width // 2
            prev_bottom = center_y + prev_height // 2

            mask_draw.ellipse([prev_left, prev_top, prev_right, prev_bottom], fill=0)

        # 应用蒙版并粘贴（使用当前时间点的图片）
        masked_img = Image.composite(images[i], result, mask)
        result.paste(masked_img, (0, 0))

    return result


def create_rectangular_band_slice(images):
    """
    创建矩形环带时间切片 - 从中心到周围一圈一圈的长方形
    """
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2
    num_images = len(images)

    # 计算最大和最小尺寸
    max_size = max(img_w, img_h)
    min_size = max_size // 20  # 最小尺寸为最大尺寸的1/20

    # 创建空白画布 - 与输入相同尺寸
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))

    # 计算环带尺寸增量（使用平方根增长，中心环带变化快，边缘变化慢）
    size_step = (max_size - min_size) / math.sqrt(num_images)

    # 从中心向外处理
    print("生成矩形环带切片...")
    for i in tqdm(range(num_images), desc="处理环带"):
        # 当前环带的尺寸（使用平方根增长）
        size = min_size + math.sqrt(i) * size_step

        # 确保尺寸不超过最大尺寸
        size = min(size, max_size)

        # 计算当前矩形的宽度和高度（保持原始比例）
        width = size * (img_w / max_size)
        height = size * (img_h / max_size)

        # 计算当前矩形的位置（居中）
        left = center_x - width // 2
        top = center_y - height // 2
        right = center_x + width // 2
        bottom = center_y + height // 2

        # 创建矩形蒙版
        mask = Image.new('L', (img_w, img_h), 0)
        mask_draw = ImageDraw.Draw(mask)

        # 绘制外矩形
        mask_draw.rectangle([left, top, right, bottom], fill=255)

        # 绘制内矩形（挖空中心部分）
        if i > 0:  # 第一个环带是实心的，不需要挖空
            # 计算内矩形尺寸（上一个环带的尺寸）
            prev_size = min_size + math.sqrt(i - 1) * size_step
            prev_width = prev_size * (img_w / max_size)
            prev_height = prev_size * (img_h / max_size)

            prev_left = center_x - prev_width // 2
            prev_top = center_y - prev_height // 2
            prev_right = center_x + prev_width // 2
            prev_bottom = center_y + prev_height // 2

            mask_draw.rectangle([prev_left, prev_top, prev_right, prev_bottom], fill=0)

        # 应用蒙版并粘贴（使用当前时间点的图片）
        masked_img = Image.composite(images[i], result, mask)
        result.paste(masked_img, (0, 0))

    return result


def create_circular_band_slice(images):
    """
    创建圆形环带时间切片 - 从中心向周围一圈一圈的圆形环带
    """
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2
    num_images = len(images)

    # 计算最大半径（取图像宽高中的较小值的一半）
    max_radius = min(img_w, img_h) // 2
    min_radius = max_radius // 20  # 最小半径为最大半径的1/20

    # 创建空白画布 - 与输入相同尺寸
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))

    # 计算环带半径增量（使用平方根增长，中心环带变化快，边缘变化慢）
    radius_step = (max_radius - min_radius) / math.sqrt(num_images)

    # 从中心向外处理
    print("生成圆形环带切片...")
    for i in tqdm(range(num_images), desc="处理环带"):
        # 当前环带的半径（使用平方根增长）
        radius = min_radius + math.sqrt(i) * radius_step

        # 确保半径不超过最大半径
        radius = min(radius, max_radius)

        # 计算当前圆的位置（居中）
        left = center_x - radius
        top = center_y - radius
        right = center_x + radius
        bottom = center_y + radius

        # 创建圆形蒙版
        mask = Image.new('L', (img_w, img_h), 0)
        mask_draw = ImageDraw.Draw(mask)

        # 绘制外圆
        mask_draw.ellipse([left, top, right, bottom], fill=255)

        # 绘制内圆（挖空中心部分）
        if i > 0:  # 第一个环带是实心的，不需要挖空
            # 计算内圆半径（上一个环带的半径）
            prev_radius = min_radius + math.sqrt(i - 1) * radius_step

            prev_left = center_x - prev_radius
            prev_top = center_y - prev_radius
            prev_right = center_x + prev_radius
            prev_bottom = center_y + prev_radius

            mask_draw.ellipse([prev_left, prev_top, prev_right, prev_bottom], fill=0)

        # 应用蒙版并粘贴（使用当前时间点的图片）
        masked_img = Image.composite(images[i], result, mask)
        result.paste(masked_img, (0, 0))

    return result


def run_timeslice(input_dir, output_dir, slice_type, position, linear, reverse):
    """
    运行时间切片生成器
    """
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 确定输出路径
    output_path = Path(output_dir) / "timeslice.jpg"

    # 加载图像
    images = load_images(input_dir, reverse)
    if not images:
        raise Exception("输入目录中没有找到图片")

    # 检查所有图片尺寸是否一致
    base_size = images[0].size
    for img in images:
        if img.size != base_size:
            raise Exception("所有图片必须具有相同的尺寸")

    # 创建时间切片
    if slice_type == "vertical":
        result = create_vertical_slice(images, position, linear)
    elif slice_type == "horizontal":
        result = create_horizontal_slice(images, position, linear)
    elif slice_type == "circular":
        result = create_circular_slice(images, linear)
    elif slice_type == "elliptical_sector":
        result = create_elliptical_sector_slice(images, linear)
    elif slice_type == "elliptical_band":
        result = create_elliptical_band_slice(images)
    elif slice_type == "rectangular_band":
        result = create_rectangular_band_slice(images)
    elif slice_type == "circular_band":
        result = create_circular_band_slice(images)

    # 保存结果
    result.save(output_path, "JPEG", quality=100, subsampling=0)

    return str(output_path)


if __name__ == "__main__":
    # 命令行接口
    import sys

    parser = argparse.ArgumentParser(description="时间切片照片生成器")
    parser.add_argument("-i", "--input", default="input", help="输入文件夹路径")
    parser.add_argument("-o", "--output", default="output", help="输出文件夹路径")
    parser.add_argument("-t", "--type", required=True,
                        choices=["vertical", "horizontal", "circular",
                                 "elliptical_sector", "elliptical_band",
                                 "rectangular_band", "circular_band"],
                        help="切片类型: vertical, horizontal, circular, elliptical_sector, elliptical_band, rectangular_band, circular_band")
    parser.add_argument("-p", "--position", default="center",
                        help="条带位置: left/center/right/top/bottom 或 0.0-1.0")
    parser.add_argument("-l", "--linear", action="store_true",
                        help="启用线性模式：垂直/水平切片取不同部位；圆形/椭圆形扇形切片使用变化的扇形大小")
    parser.add_argument("-r", "--reverse", action="store_true",
                        help="逆序排序：使用时间倒序的照片序列")

    args = parser.parse_args()

    try:
        output_path = run_timeslice(
            input_dir=args.input,
            output_dir=args.output,
            slice_type=args.type,
            position=args.position,
            linear=args.linear,
            reverse=args.reverse
        )
        print(f"时间切片已保存至: {output_path}")
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)
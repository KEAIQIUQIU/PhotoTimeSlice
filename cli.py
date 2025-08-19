# cli.py
import argparse
from PIL import Image, ImageDraw
from pathlib import Path
from tqdm import tqdm
import re
import sys
import math
import numpy as np

is_frozen = getattr(sys, 'frozen', False)


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(str(s))]


def load_images(input_dir, reverse=False):
    image_extensions = [
        "*.jpg", "*.jpeg", "*.png", "*.tif", "*.tiff",
        "*.nef", "*.dng", "*.cr2", "*.cr3", "*.arw", "*.raf", "*.orf", "*.rw2"
    ]

    image_paths = []
    for ext in image_extensions:
        image_paths.extend(Path(input_dir).glob(ext))

    image_paths.sort(key=natural_sort_key)
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
    img_w, img_h = images[0].size
    num_images = len(images)
    result = Image.new('RGB', (img_w, img_h))
    strip_width = max(1, img_w // num_images)

    print("生成纵向切片...")
    for i, img in enumerate(tqdm(images, desc="处理图片")):
        if linear:
            crop_x = int(i * (img_w - strip_width) / (num_images - 1)) if num_images > 1 else 0
        else:
            if position == "left":
                crop_x = 0
            elif position == "right":
                crop_x = img_w - strip_width
            elif position == "center":
                crop_x = (img_w - strip_width) // 2
            else:
                try:
                    pos = float(position)
                    crop_x = int((img_w - strip_width) * pos)
                except ValueError:
                    crop_x = (img_w - strip_width) // 2

        paste_x = i * strip_width
        strip = img.crop((crop_x, 0, crop_x + strip_width, img_h))

        if strip.width < strip_width:
            strip = strip.resize((strip_width, img_h))
        elif strip.width > strip_width:
            strip = strip.crop((0, 0, strip_width, img_h))

        result.paste(strip, (paste_x, 0))

    return result


def create_horizontal_slice(images, position, linear=False):
    img_w, img_h = images[0].size
    num_images = len(images)
    result = Image.new('RGB', (img_w, img_h))
    strip_height = max(1, img_h // num_images)

    print("生成横向切片...")
    for i, img in enumerate(tqdm(images, desc="处理图片")):
        if linear:
            crop_y = int(i * (img_h - strip_height) / (num_images - 1)) if num_images > 1 else 0
        else:
            if position == "top":
                crop_y = 0
            elif position == "bottom":
                crop_y = img_h - strip_height
            elif position == "center":
                crop_y = (img_h - strip_height) // 2
            else:
                try:
                    pos = float(position)
                    crop_y = int((img_h - strip_height) * pos)
                except ValueError:
                    crop_y = (img_h - strip_height) // 2

        paste_y = i * strip_height
        strip = img.crop((0, crop_y, img_w, crop_y + strip_height))

        if strip.height < strip_height:
            strip = strip.resize((img_w, strip_height))
        elif strip.height > strip_height:
            strip = strip.crop((0, 0, img_w, strip_height))

        result.paste(strip, (0, paste_y))

    return result


# 更新函数名和描述
def create_circular_sector_slice(images, linear=False):
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2
    radius = min(center_x, center_y)
    num_images = len(images)
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))
    angle_step = 360 / num_images

    print("生成圆形扇形切片...")  # 更新描述
    for i, src_img in enumerate(tqdm(images, desc="处理图片")):
        start_angle = i * angle_step
        end_angle = (i + 1) * angle_step
        if not linear:
            r = radius
        else:
            r = radius * (i / (num_images - 1)) if num_images > 1 else radius

        mask = Image.new('L', (img_w, img_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.pieslice(
            [center_x - r, center_y - r,
             center_x + r, center_y + r],
            start_angle, end_angle, fill=255
        )
        masked_img = Image.composite(src_img, result, mask)
        result.paste(masked_img, (0, 0))

    return result


def create_elliptical_sector_slice(images, linear=False):
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2
    a = img_w // 2
    b = img_h // 2
    num_images = len(images)
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))
    angle_step = 360 / num_images

    print("生成椭圆形扇形切片...")
    for i, src_img in enumerate(tqdm(images, desc="处理图片")):
        start_angle = i * angle_step
        end_angle = (i + 1) * angle_step
        if not linear:
            current_a = a
            current_b = b
        else:
            scale = i / (num_images - 1) if num_images > 1 else 1.0
            current_a = a * scale
            current_b = b * scale

        ellipse_bbox = [
            center_x - current_a, center_y - current_b,
            center_x + current_a, center_y + current_b
        ]

        mask = Image.new('L', (img_w, img_h))
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.pieslice(ellipse_bbox, start_angle, end_angle, fill=255)
        masked_img = Image.composite(src_img, result, mask)
        result.paste(masked_img, (0, 0))

    return result


def create_elliptical_band_slice(images):
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2
    num_images = len(images)
    max_size = max(img_w, img_h)
    min_size = max_size // 20
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))
    size_step = (max_size - min_size) / math.sqrt(num_images)

    print("生成椭圆形环带切片...")
    for i in tqdm(range(num_images), desc="处理环带"):
        size = min_size + math.sqrt(i) * size_step
        size = min(size, max_size)
        width = size * (img_w / max_size)
        height = size * (img_h / max_size)
        left = center_x - width // 2
        top = center_y - height // 2
        right = center_x + width // 2
        bottom = center_y + height // 2

        mask = Image.new('L', (img_w, img_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([left, top, right, bottom], fill=255)

        if i > 0:
            prev_size = min_size + math.sqrt(i - 1) * size_step
            prev_width = prev_size * (img_w / max_size)
            prev_height = prev_size * (img_h / max_size)
            prev_left = center_x - prev_width // 2
            prev_top = center_y - prev_height // 2
            prev_right = center_x + prev_width // 2
            prev_bottom = center_y + prev_height // 2
            mask_draw.ellipse([prev_left, prev_top, prev_right, prev_bottom], fill=0)

        masked_img = Image.composite(images[i], result, mask)
        result.paste(masked_img, (0, 0))

    return result


def create_rectangular_band_slice(images):
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2
    num_images = len(images)
    max_size = max(img_w, img_h)
    min_size = max_size // 20
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))
    size_step = (max_size - min_size) / math.sqrt(num_images)

    print("生成矩形环带切片...")
    for i in tqdm(range(num_images), desc="处理环带"):
        size = min_size + math.sqrt(i) * size_step
        size = min(size, max_size)
        width = size * (img_w / max_size)
        height = size * (img_h / max_size)
        left = center_x - width // 2
        top = center_y - height // 2
        right = center_x + width // 2
        bottom = center_y + height // 2

        mask = Image.new('L', (img_w, img_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rectangle([left, top, right, bottom], fill=255)

        if i > 0:
            prev_size = min_size + math.sqrt(i - 1) * size_step
            prev_width = prev_size * (img_w / max_size)
            prev_height = prev_size * (img_h / max_size)
            prev_left = center_x - prev_width // 2
            prev_top = center_y - prev_height // 2
            prev_right = center_x + prev_width // 2
            prev_bottom = center_y + prev_height // 2
            mask_draw.rectangle([prev_left, prev_top, prev_right, prev_bottom], fill=0)

        masked_img = Image.composite(images[i], result, mask)
        result.paste(masked_img, (0, 0))

    return result


def create_circular_band_slice(images):
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2
    num_images = len(images)
    max_radius = min(img_w, img_h) // 2
    min_radius = max_radius // 20
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))
    radius_step = (max_radius - min_radius) / math.sqrt(num_images)

    print("生成圆形环带切片...")
    for i in tqdm(range(num_images), desc="处理环带"):
        radius = min_radius + math.sqrt(i) * radius_step
        radius = min(radius, max_radius)
        left = center_x - radius
        top = center_y - radius
        right = center_x + radius
        bottom = center_y + radius

        mask = Image.new('L', (img_w, img_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([left, top, right, bottom], fill=255)

        if i > 0:
            prev_radius = min_radius + math.sqrt(i - 1) * radius_step
            prev_left = center_x - prev_radius
            prev_top = center_y - prev_radius
            prev_right = center_x + prev_radius
            prev_bottom = center_y + prev_radius
            mask_draw.ellipse([prev_left, prev_top, prev_right, prev_bottom], fill=0)

        masked_img = Image.composite(images[i], result, mask)
        result.paste(masked_img, (0, 0))

    return result


def create_vertical_s_slice(images):
    """
    创建垂直S型曲线时间切片 - 完美S形无缝拼接
    """
    img_w, img_h = images[0].size
    num_images = len(images)
    result = Image.new('RGB', (img_w, img_h))
    strip_width = img_w / num_images

    print("生成垂直S型曲线切片...")
    for i, img in enumerate(tqdm(images, desc="处理图片")):
        # 计算当前条带位置
        x0 = i * strip_width
        x1 = (i + 1) * strip_width

        # 创建蒙版
        mask = Image.new('L', (img_w, img_h), 0)
        draw = ImageDraw.Draw(mask)

        # 计算S型曲线控制点 - 精确匹配图片边界
        start_point = (x0 + strip_width / 2, 0)
        control1 = (x0, img_h / 3)
        control2 = (x0 + strip_width, 2 * img_h / 3)
        end_point = (x0 + strip_width / 2, img_h)

        # 计算曲线路径点
        points = []
        t_values = np.linspace(0, 1, 200)  # 增加采样点
        for t in t_values:
            # 贝塞尔曲线公式
            x = (1 - t) ** 3 * start_point[0] + 3 * (1 - t) ** 2 * t * control1[0] + 3 * (1 - t) * t ** 2 * control2[
                0] + t ** 3 * end_point[0]
            y = (1 - t) ** 3 * start_point[1] + 3 * (1 - t) ** 2 * t * control1[1] + 3 * (1 - t) * t ** 2 * control2[
                1] + t ** 3 * end_point[1]
            points.append((x, y))

        # 创建S形路径
        path_points = []

        # 上边沿线 - 完全匹配S形
        for x, y in points:
            # 向外扩展一半条带宽度
            path_points.append((x + strip_width / 2, y))

        # 下边沿线 - 反向顺序保持连续性
        for x, y in reversed(points):
            # 向内收缩一半条带宽度
            path_points.append((x - strip_width / 2, y))

        # 闭合路径
        if path_points:
            path_points.append(path_points[0])

        # 填充S形路径 - 这将创建完美的S形蒙版
        if path_points:
            draw.polygon(path_points, fill=255)

        # 处理边界情况 - 对于第一张和最后一张图片
        if i == 0:
            # 左侧填充
            draw.polygon([(0, 0), (x0, 0), (x0, img_h), (0, img_h)], fill=255)
        elif i == num_images - 1:
            # 右侧填充
            draw.polygon([(x1, 0), (img_w, 0), (img_w, img_h), (x1, img_h)], fill=255)

        # 应用蒙版 - 只显示当前条带的S形部分
        masked_img = Image.composite(img, Image.new('RGB', (img_w, img_h), (0, 0, 0)), mask)

        # 将处理好的S形部分粘贴到结果图
        result.paste(masked_img, (0, 0), mask)

    return result


def create_horizontal_s_slice(images):
    """
    创建水平S型曲线时间切片 - 完美S形无缝拼接
    """
    img_w, img_h = images[0].size
    num_images = len(images)
    result = Image.new('RGB', (img_w,img_h))
    strip_height = img_h / num_images

    print("生成水平S型曲线切片...")
    for i, img in enumerate(tqdm(images, desc="处理图片")):
        # 计算当前条带位置
        y0 = i * strip_height
        y1 = (i + 1) * strip_height

        # 创建蒙版
        mask = Image.new('L', (img_w, img_h), 0)
        draw = ImageDraw.Draw(mask)

        # 计算S型曲线控制点
        start_point = (0, y0 + strip_height / 2)
        control1 = (img_w / 3, y0)
        control2 = (2 * img_w / 3, y0 + strip_height)
        end_point = (img_w, y0 + strip_height / 2)

        # 计算曲线路径点
        points = []
        t_values = np.linspace(0, 1, 200)  # 增加采样点
        for t in t_values:
            x = (1 - t) ** 3 * start_point[0] + 3 * (1 - t) ** 2 * t * control1[0] + 3 * (1 - t) * t ** 2 * control2[
                0] + t ** 3 * end_point[0]
            y = (1 - t) ** 3 * start_point[1] + 3 * (1 - t) ** 2 * t * control1[1] + 3 * (1 - t) * t ** 2 * control2[
                1] + t ** 3 * end_point[1]
            points.append((x, y))

        # 创建S形路径
        path_points = []

        # 左边沿线 - 完全匹配S形
        for x, y in points:
            path_points.append((x, y - strip_height / 2))

        # 右边沿线 - 反向顺序保持连续性
        for x, y in reversed(points):
            path_points.append((x, y + strip_height / 2))

        # 闭合路径
        if path_points:
            path_points.append(path_points[0])

        # 填充S形路径 - 这将创建完美的S形蒙版
        if path_points:
            draw.polygon(path_points, fill=255)

        # 处理边界情况 - 对于第一张和最后一张图片
        if i == 0:
            # 上边填充
            draw.polygon([(0, 0), (img_w, 0), (img_w, y0), (0, y0)], fill=255)
        elif i == num_images - 1:
            # 下边填充
            draw.polygon([(0, y1), (img_w, y1), (img_w, img_h), (0, img_h)], fill=255)

        # 应用蒙版 - 只显示当前条带的S形部分
        masked_img = Image.composite(img, Image.new('RGB', (img_w, img_h), (0, 0, 0)), mask)

        # 将处理好的S形部分粘贴到结果图
        result.paste(masked_img, (0, 0), mask)

    return result


def run_timeslice(input_dir, output_dir, slice_type, position, linear, reverse):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "timeslice.jpg"

    images = load_images(input_dir, reverse)
    if not images:
        raise Exception("输入目录中没有找到图片")

    base_size = images[0].size
    for img in images:
        if img.size != base_size:
            raise Exception("所有图片必须具有相同的尺寸")

    if slice_type == "vertical":
        result = create_vertical_slice(images, position, linear)
    elif slice_type == "horizontal":
        result = create_horizontal_slice(images, position, linear)
    elif slice_type == "circular_sector":  # 更新类型名称
        result = create_circular_sector_slice(images, linear)  # 更新函数调用
    elif slice_type == "elliptical_sector":
        result = create_elliptical_sector_slice(images, linear)
    elif slice_type == "elliptical_band":
        result = create_elliptical_band_slice(images)
    elif slice_type == "rectangular_band":
        result = create_rectangular_band_slice(images)
    elif slice_type == "circular_band":
        result = create_circular_band_slice(images)
    elif slice_type == "vertical_s":
        result = create_vertical_s_slice(images)
    elif slice_type == "horizontal_s":
        result = create_horizontal_s_slice(images)
    else:
        raise ValueError(f"未知切片类型: {slice_type}")

    result.save(output_path, "JPEG", quality=100, subsampling=0)
    return str(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="时间切片照片生成器")
    parser.add_argument("-i", "--input", default="input", help="输入文件夹路径")
    parser.add_argument("-o", "--output", default="output", help="输出文件夹路径")
    parser.add_argument("-t", "--type", required=True,
                        choices=["vertical", "horizontal", "circular_sector",  # 更新选项
                                 "elliptical_sector", "elliptical_band",
                                 "rectangular_band", "circular_band",
                                 "vertical_s", "horizontal_s"],
                        help="切片类型")
    parser.add_argument("-p", "--position", default="center",
                        help="条带位置: left/center/right/top/bottom 或 0.0-1.0")
    parser.add_argument("-l", "--linear", action="store_true",
                        help="启用线性模式")
    parser.add_argument("-r", "--reverse", action="store_true",
                        help="逆序排序")

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
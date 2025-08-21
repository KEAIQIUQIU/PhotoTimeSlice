from PIL import Image, ImageDraw
import numpy as np
from tqdm import tqdm

def create_horizontal_s_slice(images):
    """
    创建水平S型曲线时间切片 - 完美S形无缝拼接
    """
    img_w, img_h = images[0].size
    num_images = len(images)
    result = Image.new('RGB', (img_w, img_h))
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
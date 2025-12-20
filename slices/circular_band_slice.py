from PIL import Image, ImageDraw
import sys
import os

# 检查是否为打包环境
is_frozen = getattr(sys, 'frozen', False)

# 在打包环境中禁用 tqdm
if not is_frozen:
    from tqdm import tqdm
else:
    # 在打包环境中，创建一个简单的替代函数
    def tqdm(iterable=None, desc=None, **kwargs):
        if desc:
            print(f"{desc}...")
        return iterable

import math

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
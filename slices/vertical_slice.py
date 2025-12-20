from PIL import Image
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
from PIL import Image, ImageDraw
from tqdm import tqdm

def create_circular_sector_slice(images, linear=False):
    img = images[0]
    img_w, img_h = img.size
    center_x, center_y = img_w // 2, img_h // 2
    radius = min(center_x, center_y)
    num_images = len(images)
    result = Image.new('RGB', (img_w, img_h), (0, 0, 0))
    angle_step = 360 / num_images

    print("生成圆形扇形切片...")
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
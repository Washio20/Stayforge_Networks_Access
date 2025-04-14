"""
PDF417
"""
import pdf417gen
from PIL import Image
from io import BytesIO


class PDF417Generator:
    def __init__(self, data, columns=6, security_level=5, scale=3, ratio=3, padding=5, image_format="PNG"):
        self.data = data
        self.columns = columns
        self.security_level = security_level
        self.scale = scale
        self.ratio = ratio
        self.padding = padding
        self.image_format = image_format

    def generate(self) -> BytesIO:
        codes = pdf417gen.encode(self.data, columns=self.columns, security_level=self.security_level)
        image = pdf417gen.render_image(codes, scale=self.scale, ratio=self.ratio, padding=self.padding)
        buffer = BytesIO()
        image.save(buffer, format=self.image_format)
        buffer.seek(0)  # English: Reset the stream position to the beginning.
        return buffer


if __name__ == "__main__":
    generator = PDF417Generator("Hello, PDF417!")
    image_buffer = generator.generate()
    with open("output.pdf417.png", "wb") as f:
        f.write(image_buffer.getvalue())
"""
Standard QRCode
"""
import qrcode
from io import BytesIO


class QRCodeGenerator:
    def __init__(self, data, version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4,
                 image_format="PNG", fill_color="black", back_color="white"):
        self.data = data
        self.version = version
        self.error_correction = error_correction
        self.box_size = box_size
        self.border = border
        self.image_format = image_format
        self.fill_color = fill_color
        self.back_color = back_color

    def generate(self) -> BytesIO:

        qr = qrcode.QRCode(
            version=self.version,
            error_correction=self.error_correction,
            box_size=self.box_size,
            border=self.border,
        )

        qr.add_data(self.data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=self.fill_color, back_color=self.back_color)

        buffer = BytesIO()
        img.save(buffer, format=self.image_format)
        buffer.seek(0)  # English: Reset the stream position to the beginning.
        return buffer


if __name__ == "__main__":
    generator = QRCodeGenerator("Hello, QR Code!")
    image_buffer = generator.generate()

    with open("qrcode.png", "wb") as f:
        f.write(image_buffer.getvalue())
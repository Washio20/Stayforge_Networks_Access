"""
CodaBar, CODE128, CODE39, EAN, EAN13, EAN13-GUARD, EAN14, EAN8, EAN8-GUARD, GS1, GS1_128, GTIN, ISBN, ISBN10, ISBN13, ISSN, ITF, JAN, NW-7, PZN, UPC, UPCA
"""
import barcode
from barcode.writer import ImageWriter
from io import BytesIO


class CommonBarcodeGenerator:
    def __init__(self, barcode_type: str, data: str, writer_options: dict = None):
        self.barcode_type = barcode_type
        self.data = data
        self.writer_options = writer_options if writer_options is not None else {}

    def generate(self) -> BytesIO:
        BarcodeClass = barcode.get_barcode_class(self.barcode_type)
        barcode_instance = BarcodeClass(self.data, writer=ImageWriter())
        buffer = BytesIO()
        barcode_instance.write(buffer, options=self.writer_options)
        buffer.seek(0)  # English: Reset the stream position to the beginning.
        return buffer


if __name__ == "__main__":
    generator = CommonBarcodeGenerator("code128", "123456789012")
    image_buffer = generator.generate()

    with open("barcode_code128.png", "wb") as f:
        f.write(image_buffer.getvalue())
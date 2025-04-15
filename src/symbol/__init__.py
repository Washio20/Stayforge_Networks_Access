"""
Barcode generator
"""
import base64
from io import BytesIO
from typing import Optional

import barcode

from src.symbol.pdf417 import PDF417Generator

SUPPORT_SYMBOLS = ['pdf417', 'qrcode'] + barcode.PROVIDED_BARCODES
# SUPPORT_SYMBOLS = ['pdf417']


class Symbol:
    def __init__(self, data: str, symbol_type: Optional[str], image_format: str = "PNG", **kwargs):
        self.kwargs = kwargs

        self.data = data
        self.image_format = image_format.upper()

        if symbol_type not in SUPPORT_SYMBOLS:
            raise Exception('Symbol type not supported')

        self.type = symbol_type.lower()

    def render(self) -> BytesIO:
        result: BytesIO = BytesIO()

        if self.type == "pdf417":
            result = PDF417Generator(
                data=self.data, image_format=self.image_format, **self.kwargs
            ).generate()
        elif self.type == "qrcode":
            result = barcode.generate(
                self.data,
                image_format=self.image_format
            )
        elif self.type in barcode.PROVIDED_BARCODES:
            result = barcode.generate(
                self.type, self.data, writer_options=self.kwargs, output=result, image_format=self.image_format
            )
        else:
            raise Exception(f'Symbol type `{self.type}` are not supported')

        return result

    def render_to_base64(self) -> str:
        rendered = self.render()
        return base64.b64encode(rendered.getvalue()).decode('utf-8')

import board
import digitalio
from adafruit_rgb_display import st7735
from PIL import Image
import time

# Setup SPI
spi = board.SPI()
cs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D24)
rst = digitalio.DigitalInOut(board.D25)

# Ajuste fino ao redor de 24
offsets = [24, 25, 26, 27, 28]

for offset in offsets:
    display = st7735.ST7735R(
        spi, cs=cs, dc=dc, rst=rst,
        width=80, height=160,
        y_offset=0, x_offset=offset
    )
    
    img = Image.new('RGB', (80, 160), (255, 0, 0))
    display.image(img)
    print(f"x_offset={offset} - VERMELHO")
    time.sleep(2)
    
    img = Image.new('RGB', (80, 160), (0, 0, 0))
    display.image(img)
    print(f"x_offset={offset} - PRETO")
    time.sleep(3)

print("Qual foi o valor perfeito?")

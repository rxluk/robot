import board
import digitalio
import time
from adafruit_rgb_display.st7735 import ST7735R

# Pines
cs  = digitalio.DigitalInOut(board.CE0)
dc  = digitalio.DigitalInOut(board.D24)
rst = digitalio.DigitalInOut(board.D25)
bl  = digitalio.DigitalInOut(board.D18)

bl.switch_to_output()
bl.value = True

display = ST7735R(
    board.SPI(),
    cs=cs,
    dc=dc,
    rst=rst,
    rotation=0,
    width=80,
    height=160
)

# Cores
COLORS = [
    0xF800,  # vermelho
    0x07E0,  # verde
    0x001F,  # azul
    0xFFE0,  # amarelo
    0xF81F,  # roxo
    0x07FF,  # ciano
    0xFFFF,  # branco
]

display.fill(0x0000)
time.sleep(1)

print("Desenhando régua horizontal (eixo X)...")

step = 5  # largura de cada faixa em pixels
color_index = 0

for x in range(0, 160, step):
    color = COLORS[color_index % len(COLORS)]
    color_index += 1

    # desenha faixa vertical
    display.fill_rectangle(x, 0, step, 160, color)

    print(f"Faixa X = {x} até {x+step}")
    time.sleep(0.3)

print("Fim do teste.")

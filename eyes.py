import board
import digitalio
from adafruit_rgb_display import st7735
from PIL import Image, ImageDraw
import time
import random
import RPi.GPIO as GPIO

TOUCH_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(TOUCH_PIN, GPIO.IN)

spi = board.SPI()
cs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D24)
rst = digitalio.DigitalInOut(board.D25)

display = st7735.ST7735R(
    spi, cs=cs, dc=dc, rst=rst,
    width=80, height=160,
    y_offset=0, x_offset=26,
    rotation=90
)

BLACK = (255, 255, 255)
BLUE = (255, 120, 0)

class Eye:
    def __init__(self, x, y, width, height, radius):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.radius = radius
        self.current_height = height
        self.target_height = height

    def set_height(self, height):
        self.target_height = height

    def update(self):
        self.current_height = (self.current_height + self.target_height) // 2

    def get_y_offset(self):
        return (self.height - self.current_height) // 2

class Mood:
    def __init__(self):
        self.current = "default"

    def set(self, mood):
        self.current = mood

    def draw_eyelids(self, draw, left_eye, right_eye):
        ly = left_eye.y + left_eye.get_y_offset()
        ry = right_eye.y + right_eye.get_y_offset()

        if self.current == "tired":
            h = left_eye.current_height // 2
            draw.polygon([
                (left_eye.x, ly),
                (left_eye.x + left_eye.width, ly),
                (left_eye.x, ly + h)
            ], fill=BLACK)
            draw.polygon([
                (right_eye.x, ry),
                (right_eye.x + right_eye.width, ry),
                (right_eye.x + right_eye.width, ry + h)
            ], fill=BLACK)

        elif self.current == "angry":
            h = left_eye.current_height // 2
            draw.polygon([
                (left_eye.x, ly),
                (left_eye.x + left_eye.width, ly),
                (left_eye.x + left_eye.width, ly + h)
            ], fill=BLACK)
            draw.polygon([
                (right_eye.x, ry),
                (right_eye.x + right_eye.width, ry),
                (right_eye.x, ry + h)
            ], fill=BLACK)

        elif self.current == "happy":
            offset = left_eye.current_height // 2
            self._draw_rounded_rect(draw,
                left_eye.x - 1, ly + left_eye.current_height - offset,
                left_eye.width + 2, left_eye.height,
                left_eye.radius, BLACK)
            self._draw_rounded_rect(draw,
                right_eye.x - 1, ry + right_eye.current_height - offset,
                right_eye.width + 2, right_eye.height,
                right_eye.radius, BLACK)

    def _draw_rounded_rect(self, draw, x, y, w, h, r, fill):
        r = min(r, h // 2, w // 2)
        if r < 1:
            draw.rectangle([x, y, x+w, y+h], fill=fill)
            return
        draw.rectangle([x+r, y, x+w-r, y+h], fill=fill)
        draw.rectangle([x, y+r, x+w, y+h-r], fill=fill)
        draw.ellipse([x, y, x+2*r, y+2*r], fill=fill)
        draw.ellipse([x+w-2*r, y, x+w, y+2*r], fill=fill)
        draw.ellipse([x, y+h-2*r, x+2*r, y+h], fill=fill)
        draw.ellipse([x+w-2*r, y+h-2*r, x+w, y+h], fill=fill)

class RoboEyes:
    def __init__(self):
        eye_width = 30
        eye_height = 36
        eye_radius = 8
        space_between = 10

        left_x = (160 - (eye_width * 2 + space_between)) // 2
        left_y = (80 - eye_height) // 2
        right_x = left_x + eye_width + space_between

        self.left_eye = Eye(left_x, left_y, eye_width, eye_height, eye_radius)
        self.right_eye = Eye(right_x, left_y, eye_width, eye_height, eye_radius)
        self.mood = Mood()

        self.last_blink = time.time()
        self.mood_timer = 0
        self.was_touching = False

    def draw_rounded_rect(self, draw, x, y, w, h, r, fill):
        r = min(r, h // 2, w // 2)
        if r < 1:
            draw.rectangle([x, y, x+w, y+h], fill=fill)
            return
        draw.rectangle([x+r, y, x+w-r, y+h], fill=fill)
        draw.rectangle([x, y+r, x+w, y+h-r], fill=fill)
        draw.ellipse([x, y, x+2*r, y+2*r], fill=fill)
        draw.ellipse([x+w-2*r, y, x+w, y+2*r], fill=fill)
        draw.ellipse([x, y+h-2*r, x+2*r, y+h], fill=fill)
        draw.ellipse([x+w-2*r, y+h-2*r, x+w, y+h], fill=fill)

    def draw(self):
        img = Image.new('RGB', (160, 80), BLACK)
        draw = ImageDraw.Draw(img)

        self.left_eye.update()
        self.right_eye.update()

        ly = self.left_eye.y + self.left_eye.get_y_offset()
        self.draw_rounded_rect(draw,
            self.left_eye.x, ly,
            self.left_eye.width, self.left_eye.current_height,
            self.left_eye.radius, BLUE)

        ry = self.right_eye.y + self.right_eye.get_y_offset()
        self.draw_rounded_rect(draw,
            self.right_eye.x, ry,
            self.right_eye.width, self.right_eye.current_height,
            self.right_eye.radius, BLUE)

        self.mood.draw_eyelids(draw, self.left_eye, self.right_eye)
        display.image(img)

    def blink(self):
        self.left_eye.set_height(2)
        self.right_eye.set_height(2)
        self.draw()
        time.sleep(0.05)
        self.draw()
        time.sleep(0.1)
        self.left_eye.set_height(self.left_eye.height)
        self.right_eye.set_height(self.right_eye.height)
        self.draw()
        time.sleep(0.05)

    def handle_touch(self):
        is_touching = GPIO.input(TOUCH_PIN) == GPIO.HIGH
        current_time = time.time()

        if is_touching:
            if self.mood.current != "happy":
                self.mood.set("happy")
                print("Happy! 😊")
            self.mood_timer = current_time + 3

        elif not is_touching and self.was_touching:
            pass

        self.was_touching = is_touching

        if self.mood_timer > 0 and current_time > self.mood_timer and not is_touching:
            if self.mood.current == "happy":
                self.mood.set(random.choice(["angry", "tired"]))
                self.mood_timer = current_time + 5
                print(f"{self.mood.current.title()}!")
            elif self.mood.current in ["angry", "tired"]:
                self.mood.set("default")
                self.mood_timer = 0
                print("Normal")

    def update(self):
        current_time = time.time()

        self.handle_touch()

        if current_time - self.last_blink > random.uniform(2, 6):
            self.blink()
            self.last_blink = current_time

        self.draw()

eyes = RoboEyes()
print("Robot Eyes - Toque para interagir")
print("Press Ctrl+C to exit")

try:
    while True:
        eyes.update()
        time.sleep(0.033)
except KeyboardInterrupt:
    GPIO.cleanup()
    img = Image.new('RGB', (160, 80), BLACK)
    display.image(img)
    print("\nDone!")
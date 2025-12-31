import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN)

print("Sensor touch no GPIO 17")
print("Toque no sensor...")

try:
    while True:
        if GPIO.input(17) == GPIO.HIGH:
            print("TOCADO!")
            time.sleep(0.3)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nFinalizando...")
    GPIO.cleanup()
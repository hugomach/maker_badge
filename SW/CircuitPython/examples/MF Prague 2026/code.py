"""
Maker Badge - Maker Faire Prague 2026
CircuitPython example for rev. D board

Displays a name card on the e-ink display together with the current battery
level.  After the initial refresh the board enters deep sleep to preserve
battery life.  Press the BOOT button (D0) to wake up and refresh the display.

Board: Maker Badge rev. D (ESP32-S2, SSD1680 250x122 e-ink display)

MIT License
Copyright (c) 2026 Czech maker
"""

import alarm
import time
import terminalio
import board
import neopixel
import displayio
import adafruit_ssd1680
import analogio
from adafruit_display_text import label
from digitalio import DigitalInOut, Direction
from adafruit_simplemath import map_range

# ---------------------------------------------------------------------------
# User configuration — change these lines to your own name and project
# ---------------------------------------------------------------------------
JMENO = "Hugo"           # First name
PRIJMENI = "Mach"        # Last name / Surname
FIRMA = "Make more"      # Company or project name

# Battery voltage range for a single-cell LiPo (3.7 V empty, 4.2 V full)
BATTERY_MIN_VOLTAGE = 3.7
BATTERY_MAX_VOLTAGE = 4.2
# ---------------------------------------------------------------------------


# Helper: append a text label to the display group
def _addText(text, scale, color, x_cord, y_cord):
    text_group = displayio.Group(scale=scale, x=x_cord, y=y_cord)
    text_label = label.Label(terminalio.FONT, text=text, color=color)
    text_group.append(text_label)
    display_data.append(text_group)


# Helper: read battery voltage via the resistor-divider circuit
def get_voltage(pin):
    enable_battery_reading.value = False
    bat_value = (pin.value * 3.3) / 65536 * 2
    enable_battery_reading.value = True
    return bat_value


# --- Pin definitions -------------------------------------------------------
board_spi = board.SPI()          # SCK + MOSI
board_epd_cs = board.D41
board_epd_dc = board.D40
board_epd_reset = board.D39
board_epd_busy = board.D42

# Display power transistor (active-low)
enable_display = DigitalInOut(board.D16)
enable_display.direction = Direction.OUTPUT

# Battery measurement enable pin (active-low) and ADC
enable_battery_reading = DigitalInOut(board.D14)
enable_battery_reading.direction = Direction.OUTPUT
vbat_voltage = analogio.AnalogIn(board.D6)

# NeoPixels (4 LEDs)
led_pin = board.D18
led_matrix = neopixel.NeoPixel(led_pin, 4, brightness=0.1, auto_write=False)

# --- Colors ----------------------------------------------------------------
display_black = 0x000000
display_white = 0xFFFFFF
led_off = (0, 0, 0)

# --- Battery reading -------------------------------------------------------
battery_voltage = get_voltage(vbat_voltage)
battery_percentage = map_range(battery_voltage, BATTERY_MIN_VOLTAGE, BATTERY_MAX_VOLTAGE, 0, 100)
battery_percentage = max(0, min(100, battery_percentage))
print("VBat: {:.2f} V  /  {:.0f} %".format(battery_voltage, battery_percentage))

# --- Display setup ---------------------------------------------------------
display_width = 250
display_height = 122

displayio.release_displays()
display_bus = displayio.FourWire(
    board_spi,
    command=board_epd_dc,
    chip_select=board_epd_cs,
    reset=board_epd_reset,
    baudrate=1000000,
)
time.sleep(1)
display = adafruit_ssd1680.SSD1680(
    display_bus,
    width=display_width,
    height=display_height,
    rotation=270,
    busy_pin=board_epd_busy,
)

# --- Build display content -------------------------------------------------
display_data = displayio.Group()

# White background
display_background = displayio.Bitmap(display_width, display_height, 1)
display_color_palette = displayio.Palette(1)
display_color_palette[0] = display_white
display_data.append(
    displayio.TileGrid(display_background, pixel_shader=display_color_palette)
)

# Name card text
_addText(JMENO, 3, display_black, 70, 20)
_addText(PRIJMENI, 3, display_black, 50, 60)
_addText(FIRMA, 2, display_black, 45, 100)

# Battery info (top-right corner)
_addText("{:.0f}%".format(battery_percentage), 1, display_black, 223, 8)
_addText("{:.2f}V".format(battery_voltage), 1, display_black, 220, 28)

# Event label (bottom-right)
_addText("MF Prague 2026", 1, display_black, 158, 112)

# Turn off NeoPixels to save power
led_matrix.fill(led_off)
led_matrix.show()

# --- Refresh display -------------------------------------------------------
enable_display.value = False
display.show(display_data)
display.refresh()

# Wait for the display to finish refreshing before sleeping
time.sleep(10)

# --- Deep sleep (wake on BOOT button press) --------------------------------
pin_alarm = alarm.pin.PinAlarm(pin=board.D0, value=False, pull=True)
alarm.exit_and_deep_sleep_until_alarms(pin_alarm)

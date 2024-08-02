# This example uses a Pico W and a Pico Display Pack 2 with their Micropython 
# version to connect to a network and get the time and display on the screen.

import machine
import time
from pimoroni import RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2

# set up the hardware
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, rotate=0)
sensor_temp = machine.ADC(4)
led = RGBLED(6, 7, 8)

# set the display backlight to 50%
display.set_backlight(0.5)

button_a = machine.Pin(12, machine.Pin.IN, pull=machine.Pin.PULL_UP)
button_b = machine.Pin(13, machine.Pin.IN, pull=machine.Pin.PULL_UP)
button_x = machine.Pin(14, machine.Pin.IN, pull=machine.Pin.PULL_UP)
button_y = machine.Pin(15, machine.Pin.IN, pull=machine.Pin.PULL_UP)

# set up constants for drawing
WIDTH, HEIGHT = display.get_bounds()
display.set_font("bitmap8")

WHITE = display.create_pen(255, 255, 255)
BLACK = display.create_pen(0, 0, 0)
CYAN = display.create_pen(0, 255, 255)
MAGENTA = display.create_pen(255, 0, 255)
YELLOW = display.create_pen(255, 255, 0)
GREEN = display.create_pen(0, 255, 0)

display.set_pen(WHITE)
display.rectangle(0,0,WIDTH,HEIGHT)
display.set_pen(BLACK)

#RTC
rtc = machine.RTC()

cursors = ["hour", "minute", "year", "month", "day", "finish"]
set_clock = False
cursor = 0
last = 0

# From CPython Lib/colorsys.py
def hsv_to_rgb(h, s, v):
    if s == 0.0:
        return v, v, v
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q

def contrast_colour(colours):  # Colours input are rgb values given by the layer's default color, in the format R,G,B
        luminance = (0.299 * colours[0] + 0.587 * colours[1] + 0.114 * colours[2]) / 255

        if luminance > 0.5:
            return BLACK
        else:
            return WHITE

def days_in_month(month, year):
    if month == 2 and ((ear % 4 == 0 and year % 100 != 0) or year % 400 == 0):
        return 29
    return (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[month - 1]

# Button handling function
def button(pin):
    global last, set_clock, cursor, year, month, day, hour, minute
    
    adjust = 0
    changed = False
    
    time.sleep(0.01)
    if pin.value():
        return
    
    if pin == button_b and not set_clock:
        cursor = 0
        set_clock = True
        draw_clock()
        return
    
    if set_clock:
        if pin == button_b:
            cursor += 1
            cursor %= len(cursors)
            changed = True
            
        if pin == button_a:
            adjust = 1
            changed = True
            
        if pin == button_y:
            adjust = - 1
            changed = True
            
        if cursors[cursor] == "finish":
            if adjust != 0:
                set_clock = False
                changed = True
                if not set_clock:
                    rtc.datetime((year,month,day,0,hour,minute,second,0))
        if cursors[cursor] == "year":
            year += adjust
            year = max(year, 2022)
            day = min(day, days_in_month(month, year))
            
        if cursors[cursor] == "month":
            month += adjust
            month = min(max(month, 1), 12)
            day = min(day, days_in_month(month, year))
        
        if cursors[cursor] == "day":
            day += adjust
            day = min(max(day,1), days_in_month(month,year))
        
        if cursors[cursor] == "hour":
            hour += adjust
            hour %= 24
        
        if cursors[cursor] == "minute":
            minute += adjust
            minute %= 60
    
    if changed:
        draw_clock()
    
button_a.irq(trigger=machine.Pin.IRQ_FALLING, handler=button)
button_b.irq(trigger=machine.Pin.IRQ_FALLING, handler=button)
button_y.irq(trigger=machine.Pin.IRQ_FALLING, handler=button)


def draw_clock():
    hms = "{:02}:{:02}:{:02}".format(hour, minute, second)
    ymd = "{:04}/{:02}/{:02}".format(year,month,day)
    
    hms_width = display.measure_text(hms, 8)
    hms_offset = int((WIDTH / 2) - (hms_width / 2))
    h_width = display.measure_text(hms[0:2], 8)
    mi_width = display.measure_text(hms[3:5], 8)
    mi_offset = display.measure_text(hms[0:3], 8)

    ymd_width = display.measure_text(ymd, 3)
    ymd_offset = int((WIDTH / 2) - (ymd_width / 2))
    y_width = display.measure_text(ymd[0:4], 3)
    m_width = display.measure_text(ymd[5:7], 3)
    m_offset = display.measure_text(ymd[0:5], 3)
    d_width = display.measure_text(ymd[8:10], 3)
    d_offset = display.measure_text(ymd[0:8], 3)
    
    display.set_pen(RAINBOW)
    display.clear()
    display.set_pen(CONTRAST)
    
   # No "thickness" setting in PG so, uh, fake it!
    display.text(hms, hms_offset, 40, scale=8)
    display.text(hms, hms_offset, 41, scale=8)
    display.text(hms, hms_offset + 1, 40, scale=8)
    display.text(hms, hms_offset - 1, 40, scale=8)

    # Double up the text to fill out the lines
    display.text(ymd, ymd_offset, 100, scale=3)
    display.text(ymd, ymd_offset, 101, scale=3)

    if set_clock:
        if cursors[cursor] == "year":
            display.line(ymd_offset, 120, ymd_offset + y_width, 120)

        if cursors[cursor] == "month":
            display.line(ymd_offset + m_offset, 120, ymd_offset + m_offset + m_width, 120)

        if cursors[cursor] == "day":
            display.line(ymd_offset + d_offset, 120, ymd_offset + d_offset + d_width, 120)

        if cursors[cursor] == "hour":
            display.line(hms_offset, 70, hms_offset + h_width, 70)

        if cursors[cursor] == "minute":
            display.line(hms_offset + mi_offset, 70, hms_offset + mi_offset + mi_width, 70)

        done_width = display.measure_text("done", scale=3)
        display.text("done", WIDTH - done_width - 5, HEIGHT - 15, scale=3)
        if cursors[cursor] == "finish":
            display.line(WIDTH - done_width - 5, HEIGHT - 5, WIDTH - 5, HEIGHT - 5)
        
    display.update()

year, month, day, wd, hour, minute, second, _ = rtc.datetime()

if (year, month, day) == (2021,1,1):
    rtc.datetime((2022, 2, 28,0,12,0,0,0))
    
last_second = second

h = 0

while True:
    h += 1
    r,g,b = [int(255*c) for c in hsv_to_rgb(h / 360.0, 1.0, 1.0)] # rainbow magic
    led.set_rgb(r,g,b)
    global RAINBOW, CONTRAST
    RAINBOW = display.create_pen(r,g,b)
#     display.set_pen(RAINBOW)
#     display.clear()
#     display.set_pen(WHITE)
    CONTRAST = contrast_colour((r,g,b))
    if not set_clock:
        year, month, day, wd, hour, minute, second, _ = rtc.datetime()
        draw_clock()
#         if second != last_second:
#             draw_clock()
#             last_second = second
    time.sleep(0.01)
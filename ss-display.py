#!/usr/bin/env python3

from PIL import Image, ImageFont, ImageDraw
from time import sleep, monotonic
import os
import signal
import sys

from functions import (
    init_config, getdevice,
    cpu_percent, cpu_freq, cpu_max, cpu_count,
    core_temp, gpu_temp,
    load1, load5, load15,
    mem_used, mem_free, mem_total, mem_used_percent,
    swap_use, swap_percent,
    ext_ip,
    battery,
    get_local_disk_sensors, get_fan_sensors,
    load_image,
    draw_init, draw_text_3, draw_text_4,
)

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

config = init_config(os.path.join(SCRIPT_DIR, 'config.yaml'))
appearance = config.get('appearance') or {}
sensors = config.get('sensors') or {}
device_cfg = config.get('device') or {}

report_id = int(device_cfg.get('report_id', 0x61))
oled_width  = int(device_cfg.get('width',  128))
oled_height = int(device_cfg.get('height',  40))

font_file = os.path.join(SCRIPT_DIR, appearance.get('font') or 'SpaceMono-Regular.ttf')
font_size = appearance.get('size') or 12
delay = appearance.get('delay') or 2
lines_per_page = 3 if font_size >= 12 else 4
draw_fn = draw_text_3 if lines_per_page == 3 else draw_text_4

SENSOR_MAP = [
    ('cpu_percent',      'CPU: {:.0f}%',         cpu_percent),
    ('load1',            'Load1: {}',             load1),
    ('load5',            'Load5: {}',             load5),
    ('load15',           'Load15: {}',            load15),
    ('core_temp',        'CPU temp: {}C',         core_temp),
    ('gpu_temp',         'GPU temp: {}C',         gpu_temp),
    ('cpu_freq',         'CPU Freq: {:.0f}MHz',   cpu_freq),
    ('cpu_max',          'CPU Max: {:.0f}MHz',    cpu_max),
    ('cpu_count',        'CPU cores: {}',         cpu_count),
    ('mem_used',         'Mem: {}GiB',            mem_used),
    ('mem_free',         'MemFree: {}GiB',        mem_free),
    ('mem_total',        'MemTotal: {}GiB',       mem_total),
    ('mem_used_percent', 'Mem: {}%',              mem_used_percent),
    ('swap',             'Swap: {}MiB',           swap_use),
    ('swap_percent',     'Swap: {}%',             swap_percent),
    ('battery',          'Bat: {}',               battery),
    ('external_ip',      'IP: {}',                ext_ip),
]

enabled = [
    (fmt, fn)
    for key, fmt, fn in SENSOR_MAP
    if sensors.get(key, False)
]

if sensors.get('disk_usage', False):
    enabled.extend(get_local_disk_sensors())

if sensors.get('fan_speeds', False):
    enabled.extend(get_fan_sensors())

image_frames = []
image_sleeptime = 0
image_path = (appearance.get('image') or '').strip()
if image_path:
    image_path = os.path.join(SCRIPT_DIR, image_path)
    try:
        image_frames, image_sleeptime = load_image(image_path, oled_width, oled_height, report_id)
    except Exception as e:
        print("Could not load image: {}".format(e))

dev = getdevice(device_cfg)

_pixel_bytes = (oled_width * oled_height) // 8

# Blank the display and exit. SIGINT is Ctrl-C; SIGTERM is what systemd sends on stop.
def signal_handler(sig, frame):
    try:
        dev.send_feature_report(bytearray([report_id] + [0x00] * (_pixel_bytes + 1)))
        dev.close()
        print("\n")
        sys.exit(0)
    except Exception:
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if sys.stdout.isatty():
    print("Press Ctrl-C to exit.\n")

dev.open()

im = Image.new('1', (oled_width, oled_height))
draw = ImageDraw.Draw(im)
font = ImageFont.truetype(font_file, font_size)

# HID feature report: 1 byte report ID + pixel data + 1 byte terminator
def send_frame():
    dev.send_feature_report(bytearray([report_id]) + im.tobytes() + bytearray([0x00]))

def blank():
    dev.send_feature_report(bytearray([report_id] + [0x00] * (_pixel_bytes + 1)))

# Text starts 1px in from the left edge.
text_width = oled_width - 1

# A stat that is too wide for the display is broken after its first ':' and takes two lines.
def layout(text):
    if ':' not in text or font.getlength(text) <= text_width:
        return [text]
    label, value = text.split(':', 1)
    return [label + ':', value.strip()]

def read(sensor):
    fmt, fn = sensor
    val = fn()
    return layout(fmt.format(val)) if val is not None else [""]

def show(lines):
    lines = lines + [""] * (lines_per_page - len(lines))
    draw_init(draw, oled_width, oled_height)
    draw_fn(draw, font, *lines[:lines_per_page])
    send_frame()
    sleep(delay)
    blank()
    sleep(0.05)  # brief pause to let the HID report complete before the next send

while True:
    if not enabled and not image_frames:
        sleep(delay)
        continue

    # Pages are filled as the stats are read, because how many lines a stat takes depends on its value.
    lines = []
    i = 0
    while i < len(enabled):
        new = read(enabled[i])
        if lines and len(lines) + len(new) > lines_per_page:
            show(lines)
            lines = []
            continue  # read this stat again for the next page, so its value is not a page old
        lines.extend(new)
        i += 1
    if lines:
        show(lines)

    if image_frames:
        end = monotonic() + delay
        idx = 0
        while monotonic() < end:
            dev.send_feature_report(image_frames[idx % len(image_frames)])
            sleep(image_sleeptime)
            idx += 1
        blank()
        sleep(0.05)  # brief pause to let the HID report complete before the next send

dev.close()

#!/bin/bash
# Script chạy game Dungeon Crawler
# Thiết lập đầy đủ đường dẫn thư viện cho SDL2 và pygame

export LD_LIBRARY_PATH="/tmp/deps/usr/lib/x86_64-linux-gnu:/tmp/alsa/usr/lib/x86_64-linux-gnu:/tmp/sdl2-runtime/usr/lib/x86_64-linux-gnu/sdl2-classic:/tmp/opencode/sdl2/usr/lib/x86_64-linux-gnu:/tmp/gcc-install/usr/lib/x86_64-linux-gnu"
export PYTHONPATH="/tmp/pygame-extracted/usr/lib/python3/dist-packages:$PYTHONPATH"

cd /mnt/c/dungeon_crawler
python3 main.py "$@"

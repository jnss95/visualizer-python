#!/usr/bin/env python

import time
import struct
import collections
import serial

import numpy as np
import pyaudio

ser = serial.Serial('/dev/ttyUSB0')
lastChange = time.time()
chan = 1
trigger = False
nFFT = 512
BUF_SIZE = 4 * nFFT
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

blub = list()
peak_buffer = collections.deque(16 * [0], 16)

def animate(stream, MAX_y):
  global trigger
  global chan
  global maxi
  global lastChange
  # Read n*nFFT frames from stream, n > 0
  N = max(stream.get_read_available() / nFFT, 1) * nFFT
  data = stream.read(int(N))

  # Unpack data, LRLRLR...
  y = np.array(struct.unpack("%dh" % (N * CHANNELS), data)) / MAX_y
  y_L = y[::2]
  Y_L = np.fft.fft(y_L, nFFT)

  test = np.abs(Y_L) 
  peak_buffer.appendleft(min(255, int((test[0]/128)*255)))
  peak_buffer.appendleft(min(255, int((test[1]/128)*255)))

  col1 = int(sum(peak_buffer / len(peak_buffer))

  if (col1 > 90 and not trigger and (time.time() - lastChange) > 0.5 or (time.time() - lastChange > 5)):
    lastChange = time.time()
    trigger = True
    chan = chan +1
    if chan > 7:
      chan = 1
  if (col1 < 80 and trigger):
    trigger = False

  frame = bytearray()
  chred = col1 if (chan & (1 << 0)) else 0x00
  chgreen = col1 if (chan & (1 << 1)) else 0x00
  chblue = col1 if (chan & (1 << 2)) else 0x00
  ser.write(bytes([chred,chgreen,chblue]))

def main():
  p = pyaudio.PyAudio()
  # Used for normalizing signal. If use paFloat32, then it's already -1..1.
  # Because of saving wave, paInt16 will be easier.
  MAX_y = 2.0 ** (p.get_sample_size(FORMAT) * 8 - 1)
  print(MAX_y)
  stream = p.open(format=FORMAT,
                  channels=CHANNELS,
                  rate=RATE,
                  output_device_index=2,
                  input=True,
                  frames_per_buffer=BUF_SIZE)

  while True:
    animate(stream,MAX_y)
    time.sleep(0.01)

  stream.stop_stream()
  stream.close()
  p.terminate()

if __name__ == '__main__':
  main()

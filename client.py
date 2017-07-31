from gpiozero import MotionSensor
import sys
import io
import socket
import struct
import time
import picamera
import RPi.GPIO as GPIO
import pickle

def relay(delay):
  GPIO.output(18, GPIO.HIGH)
  time.sleep(delay)
  GPIO.output(18, GPIO.LOW)

def result():
    # Receive and process the result
    while True:
        result_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        if not result_len
            continue
        result_stream = io.BytesIO()
        result_stream.write(connection.read(result_len))
        result_stream.seek(0)
        result = pickle.loads(result_stream)
        print('RESULT FROM THE SERVER ::::  ', result)

# Set up GPIO for LED/Relay
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18, GPIO.OUT)
# Get hostname from command line arguement
server_hostname = sys.argv[1]
server_port = 8000
# Connect a client socket to hostname:8000 (your server)
client_socket = socket.socket()
client_socket.connect((server_hostname, server_port))
pir = MotionSensor(6)
# Make a file-like object out of the connection
connection = client_socket.makefile('wb')
# Create a thread for receiving the result
thread = Thread(target=result)
thread.start()
try:
    with picamera.PiCamera() as camera:
        camera.hflip = True
        camera.vflip = True
        camera.resolution = (640, 460)
        if pir.motion_detected:
            # Start the camera and let it stabilize for 2 seconds
            time.sleep(2)

            # Note the start time and construct a stream to hold image data temporarily
            # (instead of direcrly writing to the connection, we first find out the size)
            start = time.time()
            stream = io.BytesIO()
            for c in camera.capture_continuous(stream, 'jpeg'):
                # Write the length of the capture to the stream and flush to
                # ensure it was actually sent.
                connection.write(struct.pack('<L', stream.tell()))
                connection.flush()
                # Rewind the stream and send the image data over the wire
                stream.seek(0)
                connection.write(stream.read())
                # If we've been capturing for more than 30s then quit
                if time.time() - start > 10:
                    break
                # Reset the stream for next capture
                stream.seek(0)
                stream.truncate()
            # Write a length of 0 to the stream to signal that we are done
            connection.write(struct.pack('<L', 0))
finally:
    connection.close()
    client_socket.close()
    thread.stop()

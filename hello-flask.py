from flask import Flask, jsonify, render_template, request
import spidev
import time
import os
import threading
import sched
import json
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
relayPin = 26
GPIO.setup(relayPin,GPIO.OUT)
GPIO.output(relayPin,0)
light_history = []
moisture_history = []
nameLightDataFile = 'lightdata.json'
nameMoistureDataFile='moisturedata.json'
light_channel  = 0
moisture_channels=[1,2,3]
# Load the history
with open(nameMoistureDataFile) as data_file:
	moisture_history = json.load(data_file)
	
with open(nameLightDataFile) as data_file:
	light_history = json.load(data_file)
	
spi = spidev.SpiDev()
spi.open(0,0)

# Function to read SPI data from MCP3008 chip
# Channel must be an integer 0-7
def ReadChannel(channel):
  adc = spi.xfer2([1,(8+channel)<<4,0])
  data = ((adc[1]&3) << 8) + adc[2]
  return data

# Function to convert data to voltage level,
# rounded to specified number of decimal places. 
def ConvertVolts(data,places):
  volts = (data * 3.3) / float(1023)
  volts = round(volts,places)  
  return volts
  

def getJSON(currentValue, history):
  return jsonify({"id":currentValue,"message":"use /history for the complete history", "history":history})

def savehistory(history):
  with open(nameMoistureDataFile,'w') as outfile:
    json.dump(history,outfile) 

def saveLightHistory(history):
  with open(nameLightDataFile,'w') as outfile:
    json.dump(history,outfile) 



def turnMeasuringDevicesOn():
	GPIO.output(relayPin,1)
	print 'devices on'

def turnMeasuringDevicesOff():
	GPIO.output(relayPin,0)
	print 'devices off'

def measure_data():
  light_level = ReadChannel(light_channel)
  light_volts = ConvertVolts(light_level,2)
  moisture_channels=[1,2,3]
  voltsToReturn=[]
  voltsToReturn.append(light_volts)
  for channel in moisture_channels:
    moisture_level=ReadChannel(channel)
    moisture_volt =ConvertVolts(moisture_level,2)
    voltsToReturn.append(moisture_volt)
  return voltsToReturn
	
def foo():
  print(time.ctime())
  turnMeasuringDevicesOn()
  time.sleep(3) 
  data = measure_data()
  light_history.append(data[0])
  moisture_history.append(data[1::])
  savehistory(moisture_history)
  saveLightHistory(light_history)
  time.sleep(3) 
  turnMeasuringDevicesOff()
  threading.Timer(60,foo).start() # run every hour
foo()

app= Flask(__name__)



@app.route("/")
def hello():
  # Read the temperature sensor data
  return getJSON(0,light_history[-500::])
@app.route("/history")
def getHistory():
  return jsonify({"id":0, "history":history})

@app.route("/moisture")
def getMoisture():
  return jsonify({"id":0, "history":moisture_history})


if __name__=="__main__":
  app.run(host='0.0.0.0',port=8010,debug=True)


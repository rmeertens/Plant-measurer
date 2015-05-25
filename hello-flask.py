from flask import Flask, jsonify, render_template, request
import spidev
import time
import os
import threading
import sched
import json
history = []

# Load the history
with open('data.json') as data_file:
	history = json.load(data_file)
#	print 'loaded history'
#	print dir(data)
#	print data
#	
#	history = data['history']
#
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
  
temp_channel  = 1

# Function to calculate temperature from
# TMP36 data, rounded to specified
# number of decimal places.
def ConvertTemp(data,places):
  temp = ((data * 330)/float(1023))-50
  temp = round(temp,places)
  return temp

def getJSON(currentValue, history):
  return jsonify({"id":currentValue,"message":"use /history for the complete history", "history":history})

def savehistory(history):
  with open('data.json','w') as outfile:
    json.dump(history,outfile) 
 
def foo():
  print(time.ctime())
  history.append(ConvertVolts(ReadChannel(temp_channel),2))
  savehistory(history)
  threading.Timer(10,foo).start()
foo()

app= Flask(__name__)

@app.route("/")
def hello():
  # Read the temperature sensor data
  temp_level = ReadChannel(temp_channel)
  temp_volts = ConvertVolts(temp_level,2)
  temp       = ConvertTemp(temp_level,2)

  # Print out results
  return getJSON(temp_volts,history[-500::])
#jsonify({"id":temp_volts,"message":"use /history for the complete history", "history":history[-500::]})

@app.route("/history")
def getHistory():
  return jsonify({"id":0, "history":history})



if __name__=="__main__":
  app.run(host='0.0.0.0',port=8010,debug=True)


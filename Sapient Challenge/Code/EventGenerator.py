from kafka import KafkaProducer, KafkaClient
import csv
import json
import numpy as np
import time
from datetime import date
import pdb

class EventGenerator:
    def __init__(self,bootstrapServers,topicName):
        self.bootstrapServers = bootstrapServers
        self.topicName = topicName
           
    def readFile(self,filePath,indexRow = 0,secondsToAdd = 0):
        producer = KafkaProducer(bootstrap_servers=self.bootstrapServers)
        index = 0
        with open(filePath, 'r',) as csvfile:
            #reader =csv.reader(csvfile,delimiter = ",")
            fieldNames = ["house_id","household_id","eventtimestamp","value","timestamp"]
            reader = csv.DictReader(csvfile, fieldNames,delimiter = ",")
            next(reader)
            for row in reader: 
                if index >= indexRow:
                    ts = (np.int(row["eventtimestamp"]) + secondsToAdd) #np.int(row["timestamp"])
                    row["timestamp"] = ts
                    ts = ts * 1000
                    key = row["house_id"].encode('utf-8')
                    value =json.dumps(row).encode('utf-8')
                    #pdb.set_trace()
                    producer.send(self.topicName,value = value,key = key,timestamp_ms = ts)
                    if index %1000 == 0:
                        print("Index %i" % index)
                    #time.sleep(.001)
                index = index + 1
                
                
                    
    def createTopic(self,brokers,topicName):
        client = KafkaClient(brokers)
        client.ensure_topic_exists(topic=topicName)
    
brokerList = ["10.0.0.9","10.0.0.4","10.0.0.7"]
file = "F:\Sid\Learnings\Data Scientist\Analytics Vidhya\Sapient Challenge\household.csv"
topicName = "rawevents"

eventGen = EventGenerator(brokerList,topicName)
#eventGen.createTopic(brokerList,topicName)
"""
difference between Timestamp for 2018-07-10 09:19:09.607  and 
max timestamp (1380578340) in data is 150636009
"""
secondsToAdd = 150635894
eventGen.readFile(file,indexRow=0,secondsToAdd=secondsToAdd)

"""
import csv
file = "F:\Sid\Learnings\Data Scientist\Analytics Vidhya\Sapient Challenge\dummy.csv"
with open(file) as csvfile:
    reader = csv.reader(csvfile,delimiter = "\t")
    for row in reader:
        print(",".join(row[1:]))

    
""" 

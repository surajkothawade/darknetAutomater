import sys
import os
import glob
import convert
import datetime
from toXML import toXML
import map
import csv
import json
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
global pathToData

def lossPlot(logFilePath, trainingType):
    avg_loss= []
    itr = []
    with open(logFilePath, 'r') as file:
    	for line in file:
    		if "avg" in line:
    			val = line.split()
    			iter_num = val[0].rstrip(":")
    			avg = val[2]
    			try:
    				num = iter_num
    				if int(num) % 10 == 0:
    					avg_loss.append(float(avg))
    					itr.append(int(iter_num))
    			except:
    				print"skipping -> ",val[0]

    plt.rcParams["figure.figsize"] = [16,10]
    ax = plt.axes()
    print avg_loss,itr
    plt.plot(itr, avg_loss)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1000))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.3))
    plt.xticks(rotation = (45), fontsize = 15)
    plt.yticks(fontsize = 15)
    plt.title("Average Loss vs Iterations Plot",fontsize = 30)
    plt.legend(['Training Accuracy'],fontsize = 30)
    plt.xlabel("Iterations", fontsize = 25)
    plt.ylabel("Average loss", fontsize = 25)
    plot = trainingType+"LossPlot.jpg"
    plt.savefig(pathToData+plot)


if __name__ == "__main__":
    print "NOTE: Assuming darknet executable name to be darknet-cpp"
    if(len(sys.argv) != 9):
        print "ERROR: Invalid Number of Arguments"
        print "Usage: python main.py [pathToData] [pathToCfg] [pathToDarknet] [pathToProduction] [pathToValid] [pathToNames] [pathToAnnotations] [mAP_Threshold] \n \n [pathToData] (Should contain the subset train.txt file having paths pointing to Images directory of the Superset containing darknet labels as well) \n [pathToCfg] (Use the same configuration as Superset) \n [pathToDarknet] (Path to darknet) \n [pathToProduction] (Path to production containing trainable and off the shelf weights)  \n [pathToValid] (test.txt file of the Superset) \n [pathToNames] (Labels file used while training Superset) \n [pathToAnnotations] (Path to Annotations directory of Superset) \n [mAP_Threshold] (mAP_Threshold = 0.5 (Pascal VOC Standards))"
        sys.exit()

    #path to required files
    pathToData = sys.argv[1] # Should contain the subset train.txt file having paths pointing to Images directory of the Superset containing darknet labels as well
    pathToCfg = sys.argv[2] # Use the same configuration as Superset
    pathToDarknet = sys.argv[3] # Path to darknet
    pathToProduction = sys.argv[4] # Path to production containing trainable and off the shelf weights
    pathToValid = sys.argv[5] # test.txt file of the Superset
    namesFilePath = sys.argv[6] # Labels file used while training Superset
    pathToAnnotations = sys.argv[7] # Path to Annotations directory of Superset
    mAP_Threshold = float(sys.argv[8]) # mAP_Threshold = 0.5 (Pascal VOC Standards)

    numClasses = raw_input("Enter the number of classes")
    resultsList = ["weights"]
    csvResultsPath = os.path.join(pathToData, "results.csv")

    # Writing header row to csv
    with open(csvResultsPath, 'w') as resultsFile:
        wr = csv.writer(resultsFile, quoting=csv.QUOTE_ALL)
        wr.writerow(resultsList)

    while(True):
        # Training Darknet on required partial weights
        #modelChoice = int(raw_input("Enter 1 to train YOLO and 2 to train Tiny-YOLO"))
        modelChoice = 1 # Hardcoded to 1 for subset selection experiments
        if modelChoice == 1:
            trainingType = "yoloTraining"
        elif modelChoice == 2:
            trainingType = "tinyYoloTraining"
        else:
            continue

        trainingPath = os.path.join(pathToData,trainingType)
        if not os.path.exists(trainingPath):
        	os.mkdir(trainingPath)

        #Creating .data file
        dataFilePath = os.path.join(trainingPath, "obj.data")
        trainDatatxt = os.path.join(pathToData, "train.txt")
        testDatatxt = pathToValid
        backupDir = os.path.join(trainingPath, "backup")
        if not os.path.exists(backupDir):
            os.mkdir(backupDir)
        dataFile = open(dataFilePath, "w")
        dataFile.write("classes = " + numClasses + "\n")
        dataFile.write("train = " + trainDatatxt + "\n")
        dataFile.write("valid = " + testDatatxt + "\n")
        dataFile.write("names = " + namesFilePath + "\n")
        dataFile.write("backup = " + backupDir + "\n")
        dataFile.close()

        if modelChoice == 1:
            darknetTrain = os.path.join(pathToDarknet, "darknet-cpp") + " detector train " + dataFilePath + " " + pathToCfg + " " + os.path.join(pathToProduction, "TrainableWeights/YOLO/darknet19_448.conv.23")
            offDShelfWeights = os.path.join(pathToProduction, "OffDshelfWeights/YOLO/yolov2-voc.weights")
            offDShelfCfg = os.path.join(pathToProduction, "OffDshelfWeights/YOLO/yolo-voc.2.0.cfg")
            break
        elif modelChoice == 2:
            darknetTrain = os.path.join(pathToDarknet, "darknet-cpp") + " detector train " + dataFilePath + " " + pathToCfg + " " + os.path.join(pathToProduction, "TrainableWeights/Tiny-YOLO/tiny-yolo-voc.conv.13")
            offDShelfWeights = os.path.join(pathToProduction, "OffDshelfWeights/Tiny-YOLO/yolov2-tiny-voc.weights")
            offDShelfCfg = os.path.join(pathToProduction, "OffDshelfWeights/Tiny-YOLO/tiny-yolo-voc.cfg")
            break
        else:
            print "Incorrect choice!"
    logFilePath = os.path.join(trainingPath, "log.txt")
    print "Starting Darknet Training!"
    print("command: ", darknetTrain + " 2>&1 | tee " + logFilePath)
    darknetTrain += (" 2>&1 | tee " + logFilePath)
    os.system(darknetTrain)
    print "Completed Darknet Training!"

    # Converting darknet labels to VOC XML format - Setting path of Superset annotationsDir
    annotationsDir = pathToAnnotations

    cacheDir = os.path.join(pathToData, "cdir")
    if not os.path.exists(cacheDir):
        os.mkdir(cacheDir)

    # Validating Darknet Customized weights
    weights = os.listdir(backupDir)
    for weight in weights:
        if "final" in weight:
            weights.remove(weight)
    weights.sort(key=lambda x: int(x.split("_")[-1].split(".")[0]))

    # Making a new directory to store results this training session
    resultsPath = os.path.join(pathToData, "results")
    if not os.path.exists(resultsPath):
        os.mkdir(resultsPath)
    sessionResultsPath = os.path.join(resultsPath, str(datetime.datetime.now()).replace(" ","_"))
    if not os.path.exists(sessionResultsPath):
        os.mkdir(sessionResultsPath)

    ValidationlogFilePath = os.path.join(trainingPath, "validLog.txt")
    for weight in weights:
        customWeightsPath = os.path.join(backupDir, weight)
        darknetValid = os.path.join(pathToDarknet, "darknet-cpp") +" detector valid " + dataFilePath + " " + pathToCfg + " " + customWeightsPath
        darknetValid += (" 2>&1 | tee " + ValidationlogFilePath)
        print "Validation command: ", darknetValid
        print "Running validation on custom weights: ", weight
        os.system(darknetValid)
        print "Completed validation on custom weights: ", weight
        pushToCsv = [weight]
        # Making a new directory to store results of this weights file
        thisWeightResults = os.path.join(sessionResultsPath, weight.split(".")[0])
        os.mkdir(thisWeightResults)
        os.system("mv " + resultsPath + "/*.txt " + thisWeightResults)
        resultsList = map.calculateMAP(testDatatxt, namesFilePath, thisWeightResults, annotationsDir, cacheDir, mAP_Threshold)
        pushToCsv = pushToCsv + resultsList
        # Writing header row to csv
        with open(csvResultsPath, 'a') as resultsFile:
            wr = csv.writer(resultsFile, quoting=csv.QUOTE_ALL)
            wr.writerow(pushToCsv)

    #Validating weights using Pascal VOC
    VOCnamesFilePath = os.path.join(pathToProduction, "OffDshelfWeights", "voc.names")
    pushToCsv = ["VOC"]
    VOCdataFilePath = os.path.join(pathToData, "voc.data")
    dataFile = open(VOCdataFilePath, "w")
    dataFile.write("classes = " + "20" + "\n")
    dataFile.write("train = " + trainDatatxt + "\n")
    dataFile.write("valid = " + testDatatxt + "\n")
    dataFile.write("names = " + VOCnamesFilePath + "\n")
    dataFile.write("backup = " + backupDir + "\n")
    dataFile.close()
    VOCdarknetValid = os.path.join(pathToDarknet, "darknet-cpp") + " detector valid " + VOCdataFilePath + " " + offDShelfCfg + " " + offDShelfWeights
    print "Off the Shelf Validation command: ", VOCdarknetValid
    offDshelfResults = os.path.join(sessionResultsPath, "VOC")
    os.mkdir(offDshelfResults)
    os.system(VOCdarknetValid)
    os.system("mv " + resultsPath + "/*.txt " + offDshelfResults)
    resultsList = map.calculateMAP(testDatatxt, VOCnamesFilePath, offDshelfResults, annotationsDir, cacheDir, mAP_Threshold)
    pushToCsv = pushToCsv + resultsList
    # Writing header row to csv
    with open(csvResultsPath, 'a') as resultsFile:
        wr = csv.writer(resultsFile, quoting=csv.QUOTE_ALL)
        wr.writerow(pushToCsv)

    ##########Loss Plot#################
    lossPlot(logFilePath, trainingType)

import sys
import os
import shutil
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

def check(pathToImages, pathToLabels):
    pathToEmpty = os.path.join(pathToData,"Empty")
    os.system("rm -rf "+ pathToImages+"/*.txt")
    print(pathToImages, pathToLabels)
    if not os.path.exists(pathToEmpty):
        os.mkdir(pathToEmpty)
    openImagePath = pathToImages + "/"
    openLabelPath = pathToLabels + "/"
    files = sorted(os.listdir(openImagePath))
    i = 0
    for file in files:
        fname = file.split(".jpg")[0]
        if (not(os.path.exists(os.path.join(openImagePath, file)) and os.path.exists(os.path.join(openLabelPath, fname +'.txt')))):
            print("Error : ", os.path.join(openImagePath, file))
            print(os.path.join(openLabelPath, fname + '.txt'))
            if (os.path.exists(os.path.join(openImagePath, file))):
            	os.rename(os.path.join(openImagePath, file), os.path.join(pathToEmpty, fname +'.jpg'))
            elif (os.path.exists(os.path.join(openLabelPath, fname +'.txt'))):
                os.rename(os.path.join(openLabelPath, fname +'.txt'), os.path.join(pathToEmpty, fname +'.txt'))
    return pathToEmpty

def labelsDistribution(pathToImages, pathToLabels):
    i = 0
    labels = {}
    openPath = pathToLabels
    imagePath= pathToImages
    files = glob.glob(openPath+"/*")
    for file in files:
    	fname = file.split("/")[-1].split(".")[0]
    	img_path = imagePath + "/" + fname + ".jpg"
    	if os.path.exists(img_path):
    		label = open(file,'r')
    		for line in label:
    			l = line.split()
    			if (len(l)>3):
    				key = l[4].lower()
    				if key not in labels:
    					labels[key] = i+1
    				else:
    					labels[key] = labels[key]+1
    print(labels)
    with open(pathToData+"/labelDict.json",'w') as dictLabel:
    	json.dump(labels,dictLabel)


def labelCheck(l,m):
    if(l>m):
        l = m -1

def labelsCheck(pathToImages, pathToLabels):
    pathToImages = pathToLabels.split("Labels")[0]+"Images/"
    pathLabelsChecked = pathToLabels.split("Labels")[0]+"LabelsChecked/"
    if not os.path.exists(pathLabelsChecked):
    	os.mkdir(pathLabelsChecked)

    emptyPath = os.path.join(pathToData,"Empty")
    openPath = pathToLabels
    imagePath= pathToImages

    if not os.path.exists(pathLabelsChecked):
    	os.mkdir(pathLabelsChecked)
    files = glob.glob(openPath+"/*")
    for file in files:
    	fname = file.split("/")[-1].split(".")[0]
    	img_path = imagePath + fname + ".jpg"
    	if os.path.exists(img_path):
    		im = Image.open(img_path)
	        w = int(im.size[0])
	        h = int(im.size[1])
    		label = open(file,'r')
    		checkpath = pathLabelsChecked + "/" + fname
    		labels = label.readlines()
    		count = len(labels)
    		if ( count > 1):
    			checkLabel = open(checkpath+".txt",'w')
    			for line in labels:
    				l = line.split()
    				if (len(l)>3):
    					key = l[4].lower()
    					if (float (l[0]) > float(l[2])):
    						temp = l[0]
    						l[0] = l[2]
    						l[2] = temp
    					if ( float(l[1]) > float(l[3])):
    						temp = l[1]
    						l[1] = l[3]
    						l[3] = temp
    					labelCheck(l[0],w)
    					labelCheck(l[1],h)
    					labelCheck(l[2],w)
    					labelCheck(l[3],h)
    					checkLabel.write(l[0]+" "+l[1]+" "+l[2]+" "+l[3]+" "+key+"\n")
    				elif (len(line)>0):
    					checkLabel.write(line)
    				else:
    					print("Empty label file :", file)
    		else:
    			print("Empty label file :", file)
    			os.rename(file, emptyPath + "_" + fname + ".txt")
    			os.rename(img_path, emptyPath + "_" + fname + ".jpg")

def createTrainValid(trainDatatxt, testDatatxt):
    path = os.path.join(pathToData,"Images")
    val_path = os.path.join(pathToData, "ValidImages")
    if not os.path.exists(val_path):
        os.mkdir(val_path)

    dir = os.listdir(path)
    file_train = open(trainDatatxt, 'w')
    file_valid = open(testDatatxt, 'w')
    count = 0
    for image in dir:
        count += 1
        if (image.endswith(".jpg")):
            if(count % 10 == 0):
                file_valid.write(path + "/" + image + "\n")
                os.system("cp " + path + "/" + image + " " + val_path)
                os.system("cp " + path + "/" + image.split('.')
                          [0] + ".txt" + " " + val_path)
                continue
            else:
                file_train.write(path + "/" + image + "\n")
    print "Directory paths written succesfully"
    return val_path

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
    				if int(num) % 1000 == 0:
    					avg_loss.append(float(avg))
    					itr.append(int(iter_num))
    			except:
    				print"skipping -> ",val[0]

    plt.rcParams["figure.figsize"] = [16,10]
    ax = plt.axes()
    print avg_loss,itr
    plt.plot(itr, avg_loss)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(3000))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.3))
    plt.xticks(rotation = (45), fontsize = 15)
    plt.yticks(fontsize = 15)
    plt.title("Average Loss vs Iterations Plot",fontsize = 30)
    plt.legend(['Training Accuracy'],fontsize = 30)
    plt.xlabel("Iterations", fontsize = 25)
    plt.ylabel("Average loss", fontsize = 25)
    plt.savefig(os.path.join(pathToData,trainingType,"lossPlot.jpg"))

def resultPlot(csvResultsPath, trainingType):
    iter = []
    mAP  = []
    with open(csvResultsPath, 'r') as file:
    	results = file.readlines()
        del results[0]
        del results[-1] #not plotted voc mAP point
        for val in results:
            v = val.split(',')
            v[5] = v[5][1:-3]
            iter.append(int(v[0].split("_")[-1].split(".")[0]))
            mAP.append(float(v[5]))

    plt.rcParams["figure.figsize"] = [16,10]
    ax = plt.axes()
    plt.plot(iter, mAP)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(3000))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.3))
    plt.xticks(rotation = (45), fontsize = 15)
    plt.yticks(fontsize = 15)
    plt.title("Mean Average Precision vs Iterations Plot",fontsize = 30)
    plt.legend(['Mean Average Precision : mAP'],fontsize = 30)
    plt.xlabel("Iterations", fontsize = 25)
    plt.ylabel("Mean Average Precision : mAP", fontsize = 25)
    plt.savefig(os.path.join(pathToData,trainingType,"resultPlot.jpg"))

if __name__ == "__main__":
    print "NOTE: Assuming darknet executable name to be darknet-cpp"
    if(len(sys.argv) != 6):
        print "ERROR: Invalid Number of Arguments"
        print "Usage: python main.py [pathToData] [pathToCfg] [pathToDarknet] [pathToProduction] [mAP_Threshold]"
        sys.exit()

    #path to required files
    pathToData = sys.argv[1]
    pathToCfg = sys.argv[2]
    pathToDarknet = sys.argv[3]
    pathToProduction = sys.argv[4]
    mAP_Threshold = float(sys.argv[5])

    pathToImages = os.path.join(pathToData, "Images")
    pathToLabels = os.path.join(pathToData, "Labels")
    #cwd = os.getcwd()
    numClasses = raw_input("Enter the number of classes")
    resultsList = ["weights"]
    #Creating .names file
    namesFilePath = os.path.join(pathToData, "obj.names")
    namesFile = open(namesFilePath, "w")
    print "Enter the name of each class and press enter"
    for i in range(int(numClasses)):
        className = raw_input()
        resultsList.append(className)
        namesFile.write(className + "\n")
    namesFile.close()

    pathLabelsChecked = os.path.join(pathToLabels.split("Labels")[0], "LabelsChecked")
    darknetLabelPath = os.path.join(pathLabelsChecked.rsplit("/",1)[0], "LabelsDarknet")

    if not os.path.exists(darknetLabelPath):
        os.mkdir(darknetLabelPath)
    #Calling validation functions for images and labels
    print "Starting Images and Labels validation"
    pathToEmpty = check(pathToImages, pathToLabels)
    if(len(os.listdir(pathToEmpty)) > 0):
        print "ERROR! Images and Labels do not have a one to one mapping"
        sys.exit()
    labelsDistribution(pathToImages, pathToLabels)
    labelsCheck(pathToImages, pathToLabels)
    labelsDistribution(pathToImages, pathLabelsChecked)
    print "Images and Labels Validated Successfully"

    #Converting BBox/VATIC labels to darknet format
    convert.darknetLabelConverter(darknetLabelPath, namesFilePath, pathToImages, pathLabelsChecked)
    print("Converted Labels to Darknet Format Successfully")

    #Copying darknet labels to Images folder
    os.system("cp " + darknetLabelPath + "/*.txt " + pathToImages)

    while(True):
        # Training Darknet on required partial weights
        modelChoice = int(raw_input("Enter 1 to train YOLO and 2 to train Tiny-YOLO"))
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
        testDatatxt = os.path.join(pathToData, "test.txt")
        backupDir = os.path.join(trainingPath, "backup")
        if not os.path.exists(backupDir):
            os.mkdir(backupDir)
        validImagesPath = createTrainValid(trainDatatxt, testDatatxt)
        dataFile = open(dataFilePath, "w")
        dataFile.write("classes = " + numClasses + "\n")
        dataFile.write("train = " + trainDatatxt + "\n")
        dataFile.write("valid = " + testDatatxt + "\n")
        dataFile.write("names = " + namesFilePath + "\n")
        dataFile.write("backup = " + backupDir + "\n")
        dataFile.close()

        if modelChoice == 1:
            darknetTrain = os.path.join(pathToDarknet, "darknet") + " detector train " + dataFilePath + " " + pathToCfg + " " + os.path.join(pathToProduction, "TrainableWeights/YOLO/darknet53.conv.74")
            offDShelfWeights = os.path.join(pathToProduction, "OffDshelfWeights/YOLO/yolov3.weights")
            offDShelfCfg = os.path.join(pathToProduction, "OffDshelfWeights/YOLO/yolov3.cfg")
            break
        elif modelChoice == 2:
            darknetTrain = os.path.join(pathToDarknet, "darknet") + " detector train " + dataFilePath + " " + pathToCfg + " " + os.path.join(pathToProduction, "TrainableWeights/Tiny-YOLO/tiny-yolo-voc.conv.13")
            offDShelfWeights = os.path.join(pathToProduction, "OffDshelfWeights/Tiny-YOLO/yolov2-tiny-voc.weights")
            offDShelfCfg = os.path.join(pathToProduction, "OffDshelfWeights/Tiny-YOLO/tiny-yolo-voc.cfg")
            break
        else:
            print "Incorrect choice!"
    logFilePath = os.path.join(trainingPath, "trainLog.txt")
    print "Starting Darknet Training!"
    print("command: ", darknetTrain + " 2>&1 | tee " + logFilePath)
    darknetTrain += (" 2>&1 | tee " + logFilePath)
    os.system(darknetTrain)
    #process = subprocess.Popen(darknetTrain,stdout=subprocess.PIPE, shell=True)
    #process.wait()
    print "Completed Darknet Training!"

    csvResultsPath = os.path.join(pathToData, trainingType, "results.csv")
    # Writing header row to csv
    with open(csvResultsPath, 'w') as resultsFile:
        wr = csv.writer(resultsFile, quoting=csv.QUOTE_ALL)
        wr.writerow(resultsList)


    # Converting darknet labels to VOC XML format
    annotationsDir = os.path.join(pathToData, "Annotations")
    if os.path.exists(annotationsDir):
        shutil.rmtree(annotationsDir)
    os.mkdir(annotationsDir)

    cacheDir = os.path.join(pathToData, "cdir")
    if not os.path.exists(cacheDir):
        os.mkdir(cacheDir)
    toXML(namesFilePath, validImagesPath, annotationsDir)
    print "Converted all files to VOC XML format succesfully"

    # Validating Darknet Customized weights
    weights = os.listdir(backupDir)
    for weight in weights:
        if "final" in weight:
            weights.remove(weight)
    weights.sort(key=lambda x: int(x.split("_")[-1].split(".")[0]))

    # Making a new directory to store results this training session
    resultsPath = os.path.join(os.getcwd(), "results")
    if not os.path.exists(resultsPath):
        os.mkdir(resultsPath)
    sessionResultsPath = os.path.join(resultsPath, str(datetime.datetime.now()).replace(" ","_"))
    if not os.path.exists(sessionResultsPath):
        os.mkdir(sessionResultsPath)

    ValidationlogFilePath = os.path.join(trainingPath, "validLog.txt")
    for weight in weights:
        customWeightsPath = os.path.join(backupDir, weight)
        darknetValid = os.path.join(pathToDarknet, "darknet") +" detector valid " + dataFilePath + " " + pathToCfg + " " + customWeightsPath
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
    VOCdarknetValid = os.path.join(pathToDarknet, "darknet") + " detector valid " + VOCdataFilePath + " " + offDShelfCfg + " " + offDShelfWeights
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
    resultPlot(csvResultsPath, trainingType)

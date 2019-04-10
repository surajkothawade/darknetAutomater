Documentation for darknetAutomater:
 # Pre-requisites:
    1. Data folder containing Images(.jpg) folder and Labels folder.
    2. Labels folder should have annotations in BBox format.
    3. Darknet folder contains an executable built - "darknet-cpp".
    4. Aitoelabs production folder contains Trainable Weights and OffDShelf Weights folder.
    5. Configuration file (with modified classes and filters)
    6. Use python 2.7 and install requirements from requirements.txt


 # Usage:
    python darknetAutomater.py [pathToData] [pathToCfg] [pathToDarknet] [pathToProduction] [mAP_Threshold]

 # Results:
    1. A csv file "results.csv" will be created in the Data folder with each row containing mAP values for each trained checkpoint saved in the backup folder.
    2. A graph will be created depicting Average loss Versus Number of Training iterations.

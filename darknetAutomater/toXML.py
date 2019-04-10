import os
from PIL import Image
import sys
# print(os.getcwd())


# Preprocessing
# if(len(sys.argv) < 4):
#     print "ERROR: Invalid Number of Arguments"
#     print "Usage: python toXML.py [path_to_labels] [path_to_ValidImages] [path_to_XMLAnnotations]"
#     sys.exit()

#CLASS_NAME = {0: 'person'}  # A dictionary of class Names
# create a dictionary to map the class num to class name

def toXML(label_path, folder_name, annopath):
# label_path = sys.argv[1]
# folder_name = sys.argv[2]
# annopath = sys.argv[3]
    CLASS_NAME = {}
    labelcount = 0
    labelsFile = open(label_path, "r")
    for label in labelsFile:
        label = label.split()
        CLASS_NAME[labelcount] = label[0]
        labelcount += 1
    print CLASS_NAME
    # Folder where the custom test images and the bounding boxes(In YOLO format) are present
    #folder_name = "/home/aitoe/Suraj/darknet-YOLO-V2-example-master-wrapper/TinyYOLO/valid_images"

    for entry in os.listdir(folder_name):
        if entry.endswith("jpg"):

            # generate names for each file
            img_name = entry
            file_name = img_name[:-4]
            txt_name = file_name + ".txt"
            xml_name = file_name + ".xml"

            # get the size of the image
            im = Image.open(os.path.join(folder_name, img_name))
            img_size = im.size  # (width, height)
            im.close()

            width = img_size[0]
            height = img_size[1]

            # create a list to store the info in .txt file
            # bbinfo = [[0,x,y,w,h], [...], ...[...]]
            bbinfo = []
            with open(folder_name + "/" + txt_name, 'r') as f:
                line = f.readline()
                while line != "":
                    box = list(map(float, line.split()))
                    box[0] = int(box[0])
                    bbinfo.append(box)
                    line = f.readline()

            # write the bbinfo to .xml file
            # The address for the Annotations Folder
            with open((annopath + "/{0}").format(xml_name), 'a') as f:
                f.write("<annotation>\n")

                # write filename===========================================
                f.write("\t<filename>{0}</filename>\n".format(img_name))
                # =========================================================

                # write size===============================================
                f.write("\t<size>\n")
                #----------------------------------------------------------
                f.write("\t\t<width>{0}</width>\n".format(width))
                f.write("\t\t<height>{0}</height>\n".format(height))
                f.write("\t\t<depth>{0}</depth>\n".format(3))
                #----------------------------------------------------------
                f.write("\t</size>\n")
                #==========================================================

                # write object=============================================
                for box in bbinfo:
                    f.write("\t<object>\n")
                    # write bounding boxes-----------------------------------
                    f.write("\t\t<name>{0}</name>\n".format(CLASS_NAME[box[0]]))
                    f.write("\t\t<difficult>{0}</difficult>\n".format(0))
                    f.write("\t\t<bndbox>\n")

                    f.write(
                        "\t\t\t<xmin>{0}</xmin>\n".format(int((box[1] - 0.5 * box[3]) * width)))
                    f.write(
                        "\t\t\t<ymin>{0}</ymin>\n".format(int((box[2] - 0.5 * box[4]) * height)))
                    f.write(
                        "\t\t\t<xmax>{0}</xmax>\n".format(int((box[1] + 0.5 * box[3]) * width)))
                    f.write(
                        "\t\t\t<ymax>{0}</ymax>\n".format(int((box[2] + 0.5 * box[4]) * height)))

                    f.write("\t\t</bndbox>\n")
                    #--------------------------------------------------------
                    f.write("\t</object>\n")
                #==========================================================

                f.write("</annotation>")

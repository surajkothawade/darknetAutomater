import os
from os import walk
from PIL import Image


def convert(size, box):
    dw = 1./size[0]
    dh = 1./size[1]
    x = (box[0] + box[1])/2.0
    y = (box[2] + box[3])/2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x*dw
    w = w*dw
    y = y*dh
    h = h*dh
    return (x,y,w,h)

"""-------------------------------------------------------------------"""
""" Configure Paths"""
def darknetLabelConverter(darknetLabelPath, labelsFile, imagesFile, pathLabelsChecked):
	label = {}
	j = 0
	with open(labelsFile,'r') as l:
		keys = str.split(l.read(),'\n')

	for j in range(len(keys)):
		if(keys[j] != ""):
		    label[keys[j]] = j

	print label
	""" Get input text file list """
	txt_name_list = []
	for (dirpath, dirnames, filenames) in walk(pathLabelsChecked):
	    txt_name_list.extend(filenames)
	    break
	print txt_name_list
	print "No. of files :",len(txt_name_list)

	""" Process """
	for txt_name in txt_name_list:
	    """ Open input text files """
	    txt_path = pathLabelsChecked + "/" + txt_name
	    print("Input:" + txt_path)
	    with open(txt_path, "r") as txt_file:
		lines = txt_file.read().split('\r\n')   #for ubuntu, use "\r\n" instead of "\n"
	    print "This is the first print"
	    print lines
	    """ Open output text files """
	    txt_outpath = darknetLabelPath + "/" + txt_name
	    print("Output:" + txt_outpath)
	    txt_outfile = open(txt_outpath, "w")

	    lines = lines[0].split('\n')
	    del lines[0]
	    del lines[-1]
	    """ Convert the data to YOLO format """
	    for line in lines:
    		print line
    		if(len(line) >= 2):
    		    elems = line.split(' ')
    		    print(elems[-1])
    		    if (elems[-1] in keys):
    			print("key :",elems[-1])
    			print("value :",label[elems[-1]])
    		        cls_id = label[elems[-1]]
    		    print(elems)
    		    xmin = elems[0]
    		    print (elems)
    		    print "xmin ",xmin
    		    xmax = elems[2]
    		    ymin = elems[1]
    		    ymax = elems[3]
    		    img_path = str('%s/%s.jpg'%(imagesFile, os.path.splitext(txt_name)[0]))
                print(img_path)
                if(os.path.exists(img_path)):
                	im=Image.open(img_path)
                	w= int(im.size[0])
                	h= int(im.size[1])
                	print(w, h)
                	b = (float(xmin), float(xmax), float(ymin), float(ymax))
                	bb = convert((w,h), b)
                	print(bb)
                	txt_outfile.write(str(cls_id) + " " + " ".join([str(a) for a in bb]) + '\n')

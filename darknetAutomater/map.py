import xml.etree.ElementTree as ET
import os
import sys
#import cPickle
import numpy as np

# Preprocessing
# if(len(sys.argv) < 7):
#     print "ERROR: Invalid Number of Arguments"
#     print "Usage: python map.py [path_to_test] [path_to_labels] [path_to_ValidResults] [path_to_XMLAnnotations] [path_to_CacheDir] [mAP_Threshold]"
#     sys.exit()

def parse_rec(filename):
    """ Parse a PASCAL VOC xml file """
    tree = ET.parse(filename)
    objects = []
    for obj in tree.findall('object'):
        obj_struct = {}
        obj_struct['name'] = obj.find('name').text
        #obj_struct['pose'] = obj.find('pose').text
        #obj_struct['truncated'] = int(obj.find('truncated').text)
        obj_struct['difficult'] = int(obj.find('difficult').text)
        bbox = obj.find('bndbox')
        obj_struct['bbox'] = [int(bbox.find('xmin').text),
                              int(bbox.find('ymin').text),
                              int(bbox.find('xmax').text),
                              int(bbox.find('ymax').text)]
        objects.append(obj_struct)

    return objects


def voc_ap(rec, prec, use_07_metric=False):
    """ ap = voc_ap(rec, prec, [use_07_metric])
    Compute VOC AP given precision and recall.
    If use_07_metric is true, uses the
    VOC 07 11 point method (default:False).
    """
    if use_07_metric:
        # 11 point metric
        ap = 0.
        for t in np.arange(0., 1.1, 0.1):
            if np.sum(rec >= t) == 0:
                p = 0
            else:
                p = np.max(prec[rec >= t])
            ap = ap + p / 11.
    else:
        # correct AP calculation
        # first append sentinel values at the end
        mrec = np.concatenate(([0.], rec, [1.]))
        mpre = np.concatenate(([0.], prec, [0.]))

        # compute the precision envelope
        for i in range(mpre.size - 1, 0, -1):
            mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])

        # to calculate area under PR curve, look for points
        # where X axis (recall) changes value
        i = np.where(mrec[1:] != mrec[:-1])[0]

        # and sum (\Delta recall) * prec
        ap = np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1])
    return ap


def voc_eval(detpath,
             annopath,
             imagesetfile,
             classname,
             cachedir,
             ovthresh=0.5,
             use_07_metric=False):
    """rec, prec, ap = voc_eval(detpath,
                                annopath,
                                imagesetfile,
                                classname,
                                [ovthresh],
                                [use_07_metric])
    Top level function that does the PASCAL VOC evaluation.
    detpath: Path to detections
        detpath.format(classname) should produce the detection results file.
    annopath: Path to annotations
        annopath.format(imagename) should be the xml annotations file.
    imagesetfile: Text file containing the list of images, one image per line.
    classname: Category name (duh)
    cachedir: Directory for caching the annotations
    [ovthresh]: Overlap threshold (default = 0.5)
    [use_07_metric]: Whether to use VOC07's 11 point AP computation
        (default False)
    """
    # assumes detections are in detpath.format(classname) **Detections from YOLO
    # assumes annotations are in annopath.format(imagename) **Ground Truths in XML format
    # assumes imagesetfile is a text file with each line an image name
    # cachedir caches the annotations in a pickle file

    # first load gt
    if not os.path.isdir(cachedir):
        os.mkdir(cachedir)
    cachefile = os.path.join(cachedir, 'annots.pkl')
    imagenames = []
    # read list of images
    with open(imagesetfile, 'r') as f:
        lines = f.readlines()
        for image in lines:
            imagenames.append((image.split('/')[-1]).split('.')[0])
        # print imagenames
    #imagenames = [x.strip() for x in lines]

    if not os.path.isfile(cachefile):
        # load annots
        recs = {}
        for i, imagename in enumerate(imagenames):
            recs[imagename] = parse_rec(annopath.format(imagename))
            # if i % 100 == 0:
            #     print('Reading annotation for {:d}/{:d}'.format(
            #         i + 1, len(imagenames)))
        # save
        #print('Saving cached annotations to {:s}'.format(cachefile))
        # print recs
    #     with open(cachefile, 'w') as f:
    #         cPickle.dump(recs, f)
    # else:
    #     # load
    #     with open(cachefile, 'r') as f:
    #         recs = cPickle.load(f)

    # extract gt objects for this class ** These are the Ground Truth objects
    class_recs = {}
    npos = 0
    for imagename in imagenames:
        R = [obj for obj in recs[imagename] if obj['name'] == classname]
        bbox = np.array([x['bbox'] for x in R])
        difficult = np.array([x['difficult'] for x in R]).astype(np.bool)
        det = [False] * len(R)
        npos = npos + sum(~difficult)
        class_recs[imagename] = {'bbox': bbox,
                                 'difficult': difficult,
                                 'det': det}
    # print class_recs
    # read dets ** These are the detections from YOLO on the validations set
    detfile = detpath.format(classname)
    with open(detfile, 'r') as f:
        lines = f.readlines()

    splitlines = [x.strip().split(' ') for x in lines]
    # print splitlines
    # Trying to remove detections with lower thresholds
    # for x in splitlines:
    #     if float(x[1] > 0.4):
    #         splitlines.remove(x)

    image_ids = [x[0] for x in splitlines]
    confidence = np.array([float(x[1])
                           for x in splitlines])
    BB = np.array([[float(z) for z in x[2:]] for x in splitlines])

    # sort by confidence
    sorted_ind = np.argsort(-confidence)
    sorted_scores = np.sort(-confidence)
    BB = BB[sorted_ind, :]
    image_ids = [image_ids[x] for x in sorted_ind]
    # print image_ids
    # go down dets and mark TPs and FPs
    nd = len(image_ids)
    tp = np.zeros(nd)
    fp = np.zeros(nd)
    for d in range(nd):
        # print "Working on ", image_ids[d]
        R = class_recs[image_ids[d]]
        # print R
        bb = BB[d, :].astype(float)  # A Bounding box detected from YOLO
        ovmax = -np.inf
        BBGT = R['bbox'].astype(float)  # A Bounding Box Ground Truth

        #print "Comparison between BBoxes ", bb, BBGT
        if BBGT.size > 0:
            # compute overlaps
            # intersection
            ixmin = np.maximum(BBGT[:, 0], bb[0])
            iymin = np.maximum(BBGT[:, 1], bb[1])
            ixmax = np.minimum(BBGT[:, 2], bb[2])
            iymax = np.minimum(BBGT[:, 3], bb[3])
            iw = np.maximum(ixmax - ixmin + 1., 0.)
            ih = np.maximum(iymax - iymin + 1., 0.)
            inters = iw * ih

            # union
            uni = ((bb[2] - bb[0] + 1.) * (bb[3] - bb[1] + 1.) +
                   (BBGT[:, 2] - BBGT[:, 0] + 1.) *
                   (BBGT[:, 3] - BBGT[:, 1] + 1.) - inters)

            overlaps = inters / uni
            ovmax = np.max(overlaps)
            jmax = np.argmax(overlaps)

        if ovmax > ovthresh:
            if not R['difficult'][jmax]:
                if not R['det'][jmax]:
                    tp[d] = 1.
                    R['det'][jmax] = 1
                else:
                    fp[d] = 1.
        else:
            fp[d] = 1.

    # compute precision recall
    fp = np.cumsum(fp)
    tp = np.cumsum(tp)
    rec = tp / float(npos)
    # avoid divide by zero in case the first detection matches a difficult
    # ground truth
    prec = tp / np.maximum(tp + fp, np.finfo(np.float64).eps)
    ap = voc_ap(rec, prec, use_07_metric)

    return rec, prec, ap


# # Just the list of Image names not their entire address
# imagesetfile = '/home/aitoe/Suraj/darknet-YOLO-V2-example-master-wrapper/TinyYOLO/test.txt'
# classname = {0: 'person'}  # Dictionary for the classes
# # the format and the address where the ./darknet detector valid .. results are stored
# detpath = '/home/aitoe/Desktop/MORD_Suraj/darknet-YOLO-V2-example-master-wrapper/results/comp4_det_test_'


def do_python_eval(imagesetfile, label_path, detpath, annopath, cachedir, mAP_Threshold, output_dir='output'):
    # Change the annopath accordingly
    resultsList = []
    annopath = os.path.join(
        annopath,
        '{:s}.xml')
    # imagesetfile = os.path.join(
    #     '/home','aitoe', 'Suraj', 'darknet-YOLO-V2-example-master-wrapper', 'TinyYOLO', 'test' + '.txt')
    # # change accordingly
    # cachedir = '/home/aitoe/Suraj/darknet-YOLO-V2-example-master-wrapper/TinyYOLO/cdir'

    aps = []
    # The PASCAL VOC metric changed in 2010
    use_07_metric = False

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    for i, cls in classname.iteritems():
        # print cls
        if cls == '__background__' or cls == 'auto-rickshaw' or cls == 'rickshaw' : #or cls == 'truck' Remove truck if required
            continue
        filename = detpath + cls + '.txt'
        if(os.stat(filename).st_size == 0):
            continue
        print(filename)
        rec, prec, ap = voc_eval(
            filename, annopath, imagesetfile, cls, cachedir, ovthresh=mAP_Threshold)
        aps += [ap]
        print('AP for {} = {:.4f}'.format(cls, ap))
        #classResult = cls + ": " + str(ap)
        resultsList.append(ap)
        # with open(os.path.join(output_dir, cls + '_pr.pkl'), 'w') as f:
        #     cPickle.dump({'rec': rec, 'prec': prec, 'ap': ap}, f)
    print('Mean AP = {:.4f}'.format(np.mean(aps)))
    #meanAP = "Mean AP: " + str(np.mean(aps))
    resultsList.append(np.mean(aps))
    print('~~~~~~~~')
    print('Results:')
    for ap in aps:
        print('{:.3f}'.format(ap))
    print('{:.3f}'.format(np.mean(aps)))
    print('~~~~~~~~')
    return resultsList

def calculateMAP(imagesetfile, label_path, detpath, annopath, cachedir, mAP_Threshold):
    # imagesetfile = sys.argv[1]
    # label_path = sys.argv[2]
    detpath = detpath + "/comp4_det_test_"
    # annopath = sys.argv[4]
    # cachedir = sys.argv[5]
    # mAP_Threshold = float(sys.argv[6])
    global classname
    classname = {}
    labelsFile = open(label_path, "r")
    labelcount = 0
    for label in labelsFile:
        label = label.split()
        classname[labelcount] = label[0]
        labelcount += 1
    print "classname is : ", classname
    #print "Usage: python map.py [path_to_test] [path_to_labels] [path_to_ValidResults] [path_to_XMLAnnotations] [path_to_CacheDir] [mAP_Threshold]"
    resultsList = do_python_eval(imagesetfile, label_path, detpath, annopath, cachedir, mAP_Threshold, output_dir='output')
    return resultsList

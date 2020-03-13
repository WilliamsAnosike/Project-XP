import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import numpy as np 
from tqdm import tqdm
import matplotlib.pyplot as plt
import cv2
import math

device = torch.device("cuda: 0")
def forwardprop(model, error, optimizer, TrainLoader, ValLoader=None,count =0, loss_list=[], acc_list=[], training = False):
    correct = 0
    total = 0
    total_loss = 0
    
    for i, (images, labels) in enumerate(TrainLoader):
        train = Variable(images).view(-1,1,28,28)
        labels = Variable(labels)
        train = train.to(device)
        labels = labels.to(device)
        if training:
            optimizer.zero_grad()
        outputs = model(train)
        predicted = torch.max(outputs.data , 1)[1]
        correct += (predicted == labels).sum()
        total += len(labels)
        loss = error(outputs, labels)
        total_loss += loss
        if training:
            loss.backward()
            optimizer.step()
    if training:
        with torch.no_grad():
            val_acc, val_loss,a = forwardprop(model = model,error = error, optimizer = optimizer,TrainLoader =ValLoader)
            loss_list.append(val_loss.data)
            acc_list.append(val_acc)
            count+=1
    accuracy = correct *1.0 / total
    return accuracy , total_loss, count
    
def train(fold_id, model ,error, optimizer, TrainLoader, ValLoader):
    BATCH_SIZE = 1000
    EPOCHS = 50
    count = 0
    loss_list = []
    acc_list = []
    for epoch in range(EPOCHS):
        acc, loss, count = forwardprop(model = model,error = error,count = count, optimizer = optimizer,ValLoader = ValLoader,TrainLoader = TrainLoader, training=True, acc_list = acc_list, loss_list = loss_list)
        print("Fold: {}, Epoch: {}, Accuracy: {}, Loss: {} ".format(fold_id,epoch+1,acc, loss))
    
    return acc_list, loss_list, count

def plot(acc_list, loss_list, count):
    plt.subplot(2,1,1)
    plt.plot(range(count), acc_list)
    plt.xlabel("Iteration")
    plt.ylabel("Accuracy on Validate")
    plt.subplot(212)
    plt.plot(range(count), loss_list)
    plt.xlabel("Iteration")
    plt.ylabel("Loss on Validate")
    plt.show()

def predict(model, X):
    X = torch.Tensor(X).view(-1,28,28)
    X = X /255.0
    X = Variable(X).view(-1,1,28,28)
    X = X.to(device)
    output = model(X)
    label = torch.max(output.data,1)[1]
    
    pct = F.softmax(output.data,dim=1)
    pct = pct.cpu().numpy()[0]
   
    pct_list = [[i,j] for i,j in enumerate(pct)]
    pct_list.sort(key = lambda x: x[1], reverse=True)
    top_3_list = pct_list[:3]
    top_3_dict =dict(top_3_list)
    return label.cpu().numpy()[0], top_3_dict


def preprocess_image(img):
    #Apply threshold
    thresh = cv2.threshold(img, 100, 255, cv2.THRESH_BINARY)[1]
    #Find countor, bounding box
    cnts, tmp = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE) 
    if len(cnts) == 0:
        print "Sorry No contour Found."
    else:
        x,y,w,h = cv2.boundingRect(cnts[0])
        img_crop = img[y:(y+h), x:(x+w)]
        
        DIGITS_SIZE = 20
        #Resize image, keep ratio
        a,b=h,w
        d = int(max(h,w)/DIGITS_SIZE)
        if h > DIGITS_SIZE:
            a = int(h/d)
        if w > DIGITS_SIZE:
            b = int(w/d)
        a = 5 if a <= 0 else a
        b = 5 if b <= 0 else b
        img_crop = cv2.resize(img_crop,(b,a))
    
        horizontal = 28 - b
        vertical = 28 - a
        top = bot = int(vertical/2)
        left = right = int(horizontal/2)
        #Padding the image
        img_padding = cv2.copyMakeBorder(img_crop,top,bot,left,right,cv2.BORDER_CONSTANT)
        #Dilate
        kernel = np.ones((2,2), np.uint8) 
        img_dilation = cv2.dilate(img_padding,kernel=kernel,iterations = 1)
        
        img = cv2.resize(img_dilation,(28,28))
    return img

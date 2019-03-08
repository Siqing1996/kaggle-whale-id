
# coding: utf-8

# In[192]:


#get_ipython().run_line_magic('matplotlib', 'inline')

import os

import torch
import torch.nn.functional as F
import torch.nn as nn

from torch import optim
from torch.autograd import Variable

import torchvision
import torchvision.datasets as dset
import torchvision.models as models
import torchvision.transforms as transforms
import torchvision.utils
from torch.utils.data import DataLoader,Dataset
import albumentations
from albumentations import torch as AT

import matplotlib.pyplot as plt

import pandas as pd
import numpy as np

import random
import cv2
from PIL import Image
import PIL.ImageOps    


# In[193]:


#!pip install pretrainedmodels > /dev/null 2>&1


# ## Siamese Dataset

# In[194]:



class SiameseDataset(Dataset):
    
    def __init__(self,datafolder, df, bbox_df, datatype='train', transform = None):
        self.datafolder = datafolder
        self.df = df
        self.bbox_df = bbox_df
        self.datatype = datatype
        self.transform = transform
        
    def __getitem__(self,idx):
        # not selecting 'new_whale' for anchor image.
        img0_idx = random.choice(self.df[self.df.Id != 'new_whale'].index.values)
        
        # we need to make sure approx 50% of images are in the same class
        should_get_same_class = random.randint(0,1)
        if should_get_same_class:
            img1_idx = random.choice(self.df[self.df.Id == self.df.Id[img0_idx]].index.values) 
        else:
            img1_idx = random.choice(self.df[self.df.Id != self.df.Id[img0_idx]].index.values)
        
        img0_path = self.df.loc[img0_idx,'Image']
        img1_path = self.df.loc[img1_idx,'Image']
        
        bbox0 = bbox_df.loc[bbox_df.Image==img0_path,:].values[0,1:]
        bbox1 = bbox_df.loc[bbox_df.Image==img1_path,:].values[0,1:]
        img0_pil = Image.open(os.path.join(self.datafolder, img0_path)).crop(bbox0).convert('RGB')
        img1_pil = Image.open(os.path.join(self.datafolder, img1_path)).crop(bbox1).convert('RGB')
        #img0 = cv2.cvtColor(np.array(img0_pil), cv2.COLOR_BGR2RGB)
        img0 = np.array(img0_pil)
        img1 = np.array(img1_pil)
        
#         img0 = cv2.imread(os.path.join(self.datafolder, img0_path))#.crop(bbox0).convert('RGB')
#         img0 = cv2.cvtColor(img0, cv2.COLOR_BGR2RGB)
#         img0 = img0[bbox0[0]:bbox0[1], bbox0[2]: bbox0[3]]
        #img1 = cv2.imread(os.path.join(self.datafolder, img1_path))#.crop(bbox1).convert('RGB')
#         img1 = cv2.imread(os.path.join(self.datafolder, img1_path))#.crop(bbox0).convert('RGB')
#         img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
#         img1 = img1[bbox1[0]:bbox1[1], bbox1[2]: bbox1[3]]
        
        #image = self.normalize(self.to_tensor(self.scaler(image))).unsqueeze(0).to(self.device)
        
        image0 = self.transform(image=img0)['image']
        image1 = self.transform(image=img1)['image']
        #plt.imshow(image0)
        return image0, image1 , torch.from_numpy(np.array([int(self.df.Id[img0_idx] != self.df.Id[img1_idx])],dtype=np.float32))
    
    def __len__(self):
        return(self.df.shape[0])


# ## visualize the image pair in order to verify the function working

# In[195]:


# # not selecting 'new_whale' for anchor image.
# #index
# df = pd.read_csv("train.csv")
# bbox_df = pd.read_csv("bounding_boxes.csv")
# img0_idx = random.choice(df[df.Id != 'new_whale'].index.values)

# # we need to make sure approx 50% of images are in the same class
# should_get_same_class = random.randint(0,1)
# print(should_get_same_class)
# if should_get_same_class:
#     img1_idx = random.choice(df[df.Id == df.Id[img0_idx]].index.values) 
# else:
#     img1_idx = random.choice(df[df.Id != df.Id[img0_idx]].index.values)

# #print('0-',img0,'    1-',img1)
# img0_path = df.loc[img0_idx,'Image']
# img1_path = df.loc[img1_idx,'Image']

# bbox0 = bbox_df.loc[bbox_df.Image==img0_path,:].values[0,1:]
# bbox1 = bbox_df.loc[bbox_df.Image==img1_path,:].values[0,1:]
# img0_pil = Image.open(os.path.join("train", img0_path)).crop(bbox0).convert('RGB')
# img1_pil = Image.open(os.path.join("train", img1_path)).crop(bbox1).convert('RGB')
# #img0 = cv2.cvtColor(np.array(img0_pil), cv2.COLOR_BGR2RGB)
# img0 = np.array(img0_pil)
# img1 = np.array(img1_pil) 
# #img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)


# data_transforms = albumentations.Compose([
#     albumentations.Resize(RESIZE_H, RESIZE_W),
#     albumentations.HorizontalFlip(),
#     albumentations.OneOf([
#         albumentations.RandomContrast(),
#         albumentations.RandomBrightness(),
#         albumentations.Blur()
#     ]),
#     albumentations.ShiftScaleRotate(rotate_limit=10, scale_limit=0.15),
#     #albumentations.JpegCompression(80),
#     albumentations.HueSaturationValue(),
#     albumentations.Normalize(),
#     #AT.ToTensor()
# ])
# image0 = data_transforms(image=img0)['image']
# image1 = data_transforms(image=img1)['image']

# f = plt.figure()
# f.add_subplot(2,2, 1)
# plt.imshow(img0) 
# f.add_subplot(2,2, 2)
# plt.imshow(img1) 
# f.add_subplot(2,2, 3)
# plt.imshow(image0) 
# f.add_subplot(2,2, 4)
# plt.imshow(image1) 
# plt.show(block=True)


# ## EembeddingNet CNN

# In[196]:


# class EmbeddingNet(nn.Module):
#     def __init__(self):
#         super(EmbeddingNet, self).__init__()
#         self.convnet = nn.Sequential(nn.Conv2d(3, 32, 5), nn.PReLU(),
#                                      nn.MaxPool2d(2, stride=2),
#                                      nn.Conv2d(32, 64, 5), nn.PReLU(),
#                                      nn.MaxPool2d(2, stride=2))

#         self.fc = nn.Sequential(nn.Linear(64 * 53 * 53, 256), # 64 channels x 
#                                 nn.PReLU(),
#                                 nn.Linear(256, 256),
#                                 nn.PReLU(),
#                                 nn.Linear(256, 2)
#                                 )

#     def forward(self, x):
#         output = self.convnet(x)
#         output = output.view(output.size()[0], -1)
#         output = self.fc(output)
#         return output

#     def get_embedding(self, x):
#         return self.forward(x)


# ## EembeddingNet ResNet50

# In[197]:


# resnet_test = models.resnet50(pretrained=True)
# print(resnet_test)


# In[198]:


class EmbeddingNet(nn.Module):
#     def __init__(self):
#         super(EmbeddingNet, self).__init__()
#         self.convnet = nn.Sequential(nn.Conv2d(3, 32, 5), nn.PReLU(),
#                                      nn.MaxPool2d(2, stride=2),
#                                      nn.Conv2d(32, 64, 5), nn.PReLU(),
#                                      nn.MaxPool2d(2, stride=2))

#         self.fc = nn.Sequential(nn.Linear(64 * 53 * 53, 256), # 64 channels x 
#                                 nn.PReLU(),
#                                 nn.Linear(256, 256),
#                                 nn.PReLU(),
#                                 nn.Linear(256, 2)
#                                 )

#     def forward(self, x):
#         output = self.convnet(x)
#         output = output.view(output.size()[0], -1)
#         output = self.fc(output)
#         return output
    
    
    def __init__(self):
        super(EmbeddingNet, self).__init__()
        resnet = models.resnet50(pretrained=True)
        
        self.model = nn.Sequential(resnet.conv1, resnet.bn1,resnet.relu, resnet.maxpool,resnet.layer1,resnet.layer2,resnet.layer3,resnet.layer4,resnet.avgpool)#,resnet.fc)
        # Fix blocks
        fixed_blocks = 1
        for p in self.model[0].parameters(): p.requires_grad=False
        for p in self.model[1].parameters(): p.requires_grad=False
        if fixed_blocks >= 3:
            for p in self.model[6].parameters(): p.requires_grad=False
        if fixed_blocks >= 2:
            for p in self.model[5].parameters(): p.requires_grad=False
        if fixed_blocks >= 1:
            for p in self.model[4].parameters(): p.requires_grad=False

        def set_bn_fix(m):
            classname = m.__class__.__name__
            if classname.find('BatchNorm') != -1:
                for p in m.parameters(): p.requires_grad=False

        self.model.apply(set_bn_fix)
        
        resnet.fc = nn.Linear(2048, 5004, bias=True)
        self.last_layer = resnet.fc
        

    def forward(self, x):    
        x = self.model(x)
        x = x.view(-1, 2048)
        return self.last_layer(x)


# In[199]:


# from torchsummary import summary
# device = torch.device("cpu")
# model_device = EmbeddingNet().to(device)
# summary(model_device, (3,224,224))


# ## Siamese Net

# In[200]:


class SiameseNet(nn.Module):
    def __init__(self, embedding_net):
        super(SiameseNet, self).__init__()
        self.embedding_net = embedding_net

    def forward(self, x1, x2):
        output1 = self.embedding_net(x1)
        output2 = self.embedding_net(x2)
        return output1, output2


# ## ContrastiveLoss

# In[201]:


class ContrastiveLoss(nn.Module):
    """
    Contrastive loss
    Takes embeddings of two samples and a target label == 1 if samples are from the same class and label == 0 otherwise
    """

    def __init__(self, margin):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin
        self.eps = 1e-9

    def forward(self, output1, output2, target, size_average=True):
        distances = (output2 - output1).pow(2).sum(1)  # squared distances
        losses = 0.5 * (target.float() * distances +
                        (1 + -1 * target).float() * F.relu(self.margin - (distances + self.eps).sqrt()).pow(2))
        return losses.mean() if size_average else losses.sum()
    
    
# class ContrastiveLoss(torch.nn.Module):
#     """
#     Contrastive loss function.
#     Based on: http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
#     """

#     def __init__(self, margin=2.0):
#         super(ContrastiveLoss, self).__init__()
#         self.margin = margin

#     def forward(self, output1, output2, label):
#         euclidean_distance = F.pairwise_distance(output1, output2)
#         loss_contrastive = torch.mean((1-label) * torch.pow(euclidean_distance, 2) +
#                                       (label) * torch.pow(torch.clamp(self.margin - euclidean_distance, min=0.0), 2))


#         return loss_contrastive


# ## Data Path and Data Transforms

# In[202]:


# train_full = pd.read_csv("../input/humpback-whale-identification/train.csv")
# test_df = pd.read_csv("../input/humpback-whale-identification/sample_submission.csv")

# id_counts = train_full.Id.value_counts()

# valid_df = train_full.loc[train_full.Id.isin(id_counts[id_counts>5].index.values),:].sample(frac=0.3)

# train_df = train_full.loc[~train_full.index.isin(valid_df.index.values),:]

# test_df = pd.read_csv("../input/humpback-whale-identification/sample_submission.csv")

# bbox_df = pd.read_csv("../input/bounding-boxes/bounding_boxes.csv")

train_full = pd.read_csv("train.csv")
test_df = pd.read_csv("sample_submission.csv")

id_counts = train_full.Id.value_counts()

valid_df = train_full.loc[train_full.Id.isin(id_counts[id_counts>5].index.values),:].sample(frac=0.3)

train_df = train_full.loc[~train_full.index.isin(valid_df.index.values),:]

test_df = pd.read_csv("sample_submission.csv")

bbox_df = pd.read_csv("bounding_boxes.csv")

# data_transforms = transforms.Compose([
#     transforms.Resize((224, 224)), 
#     transforms.ToTensor(),
#     transforms.Normalize(mean=[0.485, 0.456, 0.406], 
#                          std=[0.229, 0.224, 0.225])
# ])

# data_transforms_test = transforms.Compose([
#     transforms.Resize((224, 224)), 
#     transforms.ToTensor(),
#     transforms.Normalize(mean=[0.485, 0.456, 0.406], 
#                          std=[0.229, 0.224, 0.225])
# ])

RESIZE_H = 224
RESIZE_W = 224

data_transforms = albumentations.Compose([
    albumentations.Resize(RESIZE_H, RESIZE_W),
    albumentations.HorizontalFlip(),
    albumentations.OneOf([
        albumentations.RandomContrast(),
        albumentations.RandomBrightness(),
        albumentations.Blur()
    ]),
    albumentations.ShiftScaleRotate(rotate_limit=10, scale_limit=0.15),
    albumentations.JpegCompression(80),
    albumentations.HueSaturationValue(),
    albumentations.Normalize(),
    AT.ToTensor()
])

data_transforms_test = albumentations.Compose([
    albumentations.Resize(RESIZE_H, RESIZE_W),
    albumentations.Normalize(),
    AT.ToTensor()
])


# ## Set up

# In[203]:


# train_dataset = SiameseDataset(datafolder="../input/humpback-whale-identification/train/", 
#                                  df=train_df, bbox_df=bbox_df, datatype='train', transform = data_transforms)

train_dataset = SiameseDataset(datafolder="train/", 
                                 df=train_df, bbox_df=bbox_df, datatype='train', transform = data_transforms)

train_dataloader = DataLoader(train_dataset,
                        shuffle=True,
                        num_workers=0,
                        batch_size=64)
# embed = EmbeddingNet().cuda()
# net = SiameseNet(embed).cuda()
embed = EmbeddingNet()#.cuda()
net = SiameseNet(embed)#.cuda()
criterion = ContrastiveLoss(margin=0.2)
optimizer = optim.Adam(net.parameters(),lr = 0.0005 )

counter = []
loss_history = [] 
iteration_number= 0


# In[204]:


net.train()
for epoch in range(0,50):
    for i, data in enumerate(train_dataloader,0):
        img0, img1 , label = data
#         img0, img1 , label = img0.cuda(), img1.cuda() , label.cuda()
        img0, img1 , label = img0, img1 , label
        optimizer.zero_grad()
        output1,output2 = net(img0,img1)
        loss_contrastive = criterion(output1,output2,label)
        loss_contrastive.backward()
        optimizer.step()
        if i %100 == 0 :
            print("Epoch number {} \t Iteration number {} \t Current loss {}\n".format(epoch,iteration_number,loss_contrastive.item()))
            iteration_number +=10
            counter.append(iteration_number)
            loss_history.append(loss_contrastive.item())
show_plot(counter,loss_history)

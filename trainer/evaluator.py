''' Incremental-Classifier Learning 
 Authors : Khurram Javed, Muhammad Talha Paracha
 Maintainer : Khurram Javed
 Lab : TUKL-SEECS R&D Lab
 Email : 14besekjaved@seecs.edu.pk '''

import logging

import numpy as np
import torch
import torch.nn.functional as F
from torch.autograd import Variable
from torchnet.meter import confusionmeter
from numpy.linalg import inv

logger = logging.getLogger('iCARL')


class EvaluatorFactory():
    '''
    This class is used to get different versions of evaluators
    '''

    def __init__(self):
        pass

    @staticmethod
    def get_evaluator(testType="nmc", classes=100):
        if testType == "trainedClassifier":
            return softmax_evaluator()
        if testType == "generativeClassifier":
            return GDA(classes)

class GDA():

    def __init__(self, classes):
        self.classes = classes
    
    def update_moment(self, model, train_loader, step_size):
        
        # Set the mean to zero
        tasknum = train_loader.dataset.t
        
        # compute means
        classes = step_size * (tasknum+1)
        class_means = np.zeros((classes, model.featureSize), dtype=np.float32)
        totalFeatures = np.zeros((classes, 1), dtype=np.float32)
        
        # Iterate over all train Dataset
        for data, y, target in train_loader:
            data, target = data.cuda(), target.cuda()
            _, features = model.forward(data, feature_return=True)
            
            if tasknum > 0:
                data_r, y_r, target_r = train_loader.dataset.sample_exemplar()
                data_r, target_r = data_r.cuda(), target_r.cuda()

                _,_,data_r_feature = model.forward(data_r, sample=True)

                features = torch.cat((features, data_r_feature))
                target = torch.cat((target,target_r))
            
            featuresNp = features.data.cpu().numpy()
            np.add.at(class_means, target.data.cpu().numpy(), featuresNp)
            np.add.at(totalFeatures, target.data.cpu().numpy(), 1)

        
        class_means = class_means / totalFeatures
        
        # compute precision
        covariance = np.zeros((model.featureSize, model.featureSize),dtype=np.float32)
        
        for data, y, target in train_loader:
            data, target = data.cuda(), target.cuda()
            _, features = model.forward(data, feature_return=True)
            
            if tasknum > 0:
                
                data_r, y_r, target_r = train_loader.dataset.sample_exemplar()
                data_r, target_r = data_r.cuda(), target_r.cuda()

                _,_,data_r_feature = model.forward(data_r, sample=True)

                features = torch.cat((features, data_r_feature))
                target = torch.cat((target,target_r))
            
            featuresNp = features.data.cpu().numpy()
            vec = featuresNp - class_means[target.data.cpu().numpy()]
            np.expand_dims(vec, axis=2)
            cov = np.matmul(np.expand_dims(vec, axis=2), np.expand_dims(vec, axis=1)).sum(axis=0)
            covariance += cov
        
        #avoid singular matrix
        covariance = covariance / totalFeatures.sum() + np.eye(model.featureSize, dtype=np.float32) * 1e-9
        precision = inv(covariance)
        
        self.class_means = torch.from_numpy(class_means).cuda()
        self.precision = torch.from_numpy(precision).cuda()
        
        return
    
    def evaluate(self, model, loader, tasknum, step_size, mode='train'):
        
        model.eval()

        correct = 0
        
        for data, y, target in loader:
            data, target = data.cuda(), target.cuda()
            _, features  = model(data, feature_return=True)
            
            # M_distance: NxC(start~end)
            # features: NxD
            # features - mean: NxC(start~end)xD
            start = 0
            if mode == 'train':
                start = tasknum * step_size
                target = target%step_size
            end = (tasknum+1) * step_size
            
#             batch_vec = (features.unsqueeze(1) - self.class_means[start:end].unsqueeze(0)).view(-1,features.shape[1])
            batch_vec = (features.unsqueeze(1) - self.class_means[start:end].unsqueeze(0))
            temp = torch.matmul(batch_vec, self.precision)
            Mahalanobis = torch.matmul(temp.unsqueeze(2),batch_vec.unsqueeze(3))
            _, pred = torch.min(Mahalanobis,1)
            correct += pred.eq(target.data.view_as(pred)).cpu().sum()
            self.class_means = self.class_means.squeeze()

        return 100. * correct / len(loader.dataset)

class softmax_evaluator():
    '''
    Evaluator class for softmax classification 
    '''

    def __init__(self):
        pass

    def evaluate(self, model, loader, start, end, mode='train', step_size=100):
        '''
        :param model: Trained model
        :param loader: Data iterator
        :return: 
        '''
        model.eval()
        correct = 0
        tempCounter = 0
        cp,epp,epn,cn,enn,enp,total = 0,0,0,0,0,0,0
        for data, y, target in loader:
            data, y, target = data.cuda(), y.cuda(), target.cuda()
            
            total += data.shape[0]
            
            if mode == 'test' and end > step_size:
                if target[0]<end-step_size: # prev
                    out = model(data)
                    pred = out.data.max(1, keepdim=True)[1].cpu().numpy()
                    
                    epn += (pred >= end-step_size).sum()
                    
                    output = out[:,start:end-step_size]
                    target = target % (end - start-step_size)
                    
                    pred = output.data.max(1, keepdim=True)[1]  # get the index of the max log-probability
                    ans = pred.eq(target.data.view_as(pred)).cpu().sum()
                    correct += ans
                    cp += ans
                    epp += (data.shape[0] - ans)
                    
                else: # new
                    out = model(data)
                    pred = out.data.max(1, keepdim=True)[1].cpu().numpy()
                    
                    enp += (pred < end-step_size).sum()
                    
                    output = out[:,end-step_size:end]
                    target = target % (step_size)
                    
                    pred = output.data.max(1, keepdim=True)[1]  # get the index of the max log-probability
                    ans = pred.eq(target.data.view_as(pred)).cpu().sum()
                    correct += ans
                    cn += ans
                    enn += (data.shape[0] - ans)
            else:
                output = model(data)[:,start:end]
                target = target % (end - start)
            
                pred = output.data.max(1, keepdim=True)[1]  # get the index of the max log-probability
                correct += pred.eq(target.data.view_as(pred)).cpu().sum()

        if mode == 'test' and end > step_size:
            return 100. * correct / len(loader.dataset), [cp,epp,epn,cn,enn,enp,total]
        return 100. * correct / len(loader.dataset)

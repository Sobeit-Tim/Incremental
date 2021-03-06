''' Incremental-Classifier Learning 
 Authors : Khurram Javed, Muhammad Talha Paracha
 Maintainer : Khurram Javed
 Lab : TUKL-SEECS R&D Lab
 Email : 14besekjaved@seecs.edu.pk '''

from __future__ import print_function

import copy
import logging

import numpy as np
import torch
import torch.nn.functional as F
from tqdm import tqdm

import networks
import trainer

class Trainer(trainer.GenericTrainer):
    def __init__(self, trainDataIterator, testDataIterator, dataset, model, args, optimizer):
        super().__init__(trainDataIterator, testDataIterator, dataset, model, args, optimizer)
        
        self.loss = torch.nn.CrossEntropyLoss(reduction='mean')

    def update_lr(self, epoch, schedule):
        for temp in range(0, len(schedule)):
            if schedule[temp] == epoch:
                for param_group in self.optimizer.param_groups:
                    self.current_lr = param_group['lr']
                    param_group['lr'] = self.current_lr * self.args.gammas[temp]
                    print("Changing learning rate from %0.4f to %0.4f"%(self.current_lr,
                                                                        self.current_lr * self.args.gammas[temp]))
                    self.current_lr *= self.args.gammas[temp]

    def increment_classes(self):
        
        self.train_data_iterator.dataset.update_exemplar()
        self.train_data_iterator.dataset.task_change()
        self.test_data_iterator.dataset.task_change()

    def setup_training(self, lr):
        
        for param_group in self.optimizer.param_groups:
            print("Setting LR to %0.4f"%lr)
            param_group['lr'] = lr
            self.current_lr = lr

    def update_frozen_model(self):
        self.model.eval()
        self.model_fixed = copy.deepcopy(self.model)
        self.model_fixed.eval()
        for param in self.model_fixed.parameters():
            param.requires_grad = False

    def train(self, epoch):
        
        self.model.train()
        print("Epochs %d"%epoch)
        
        tasknum = self.train_data_iterator.dataset.t
        end = self.train_data_iterator.dataset.end
        mid = end - self.args.step_size
        
        for data, target in tqdm(self.train_data_iterator):
            data, target = data.cuda(), target.cuda()
            
            output = self.model(data)
            
            if tasknum > 0 and self.args.prev_new:
                loss_CE_curr = 0
                loss_CE_prev = 0
                curr_mask = target >= mid
                prev_mask = target < mid
                curr_num = (curr_mask).sum().int()
                prev_num = (prev_mask).sum().int()
                batch_size = curr_num + prev_num
                
                loss_CE_curr = self.loss(output[curr_mask,mid:end], target[curr_mask]%(end-mid)) * curr_num
                loss_CE_prev = 0
                if prev_num > 0:
                    loss_CE_prev = self.loss(output[prev_mask,:mid], target[prev_mask]) * prev_num
                loss_CE = (loss_CE_curr + loss_CE_prev) / batch_size

            else:
                loss_CE = self.loss(output[:,:end], target)
            
            self.optimizer.zero_grad()
            (loss_CE).backward()
            self.optimizer.step()
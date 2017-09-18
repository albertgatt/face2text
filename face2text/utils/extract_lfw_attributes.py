#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 15:20:00 2017

@author: albertgatt
"""
import numpy as np

mapping_file = 'mapping.txt'
lfw_attributes = 'lfw_attributes.txt'
out_file = 'lfw_sample_attributes.txt'

attributes = ['Male', 
              'Asian', 'White', 'Black', 'Indian', 
              'Baby', 'Child', 'Youth', 'Middle Aged', 'Senior', 
              'Black Hair', 'Blond Hair', 'Brown Hair', 'Gray Hair', 'Bald', 
              'Eyeglasses', 'Sunglasses', 
              'Mustache', 
              'Smiling', 'Frowning', 
              'Chubby', 
              'Curly Hair', 'Wavy Hair', 'Straight Hair', 
              'Receding Hairline', 
              'Bangs', 
              'Sideburns', 
              'Bushy Eyebrows', 'Arched Eyebrows', 
              'Big Nose', 'Pointy Nose', 
              'Big Lips', 
              'Goatee', 
              'Round Jaw', 'Double Chin', 
              'Wearing Hat', 
              'Attractive Man', 'Attractive Woman', 
              'Bags Under Eyes', 
              'Heavy Makeup', 'Rosy Cheeks', 'Wearing Lipstick', 
              'High Cheekbones', 
              'Brown Eyes', 
              'Wearing Earrings', 'Wearing Necktie', 'Wearing Necklace']

lfw = {}
subset = {}

def get_best(att_slice, onset):
    best_index = np.argmax(np.array(att_slice))
    best_val = att_slice[best_index]
    
    if best_val > 0:
        return attributes[onset+best_index]
    
    return None
    

def atts_to_string(atts):
    string_atts = []
    
    string_atts.append('Female' if atts[0] < 0 else 'Male')
    
    #BEst guess for ethnicity    
    string_atts.append(get_best(atts[1:5], 1))
    
    #Best guess for age
    string_atts.append(get_best(atts[5:10], 5))
    
    #Best guess for hair colour
    string_atts.append(get_best(atts[10:15], 10))
    
    #Best guess for eyewear
    string_atts.append(get_best(atts[15:17], 15))
    
    #moustache
    string_atts.append('mustache' if atts[17] > 0 else None)
    
    #expression
    string_atts.append(get_best(atts[18:20], 18))
    
    #moustache
    string_atts.append('chubby' if atts[20] > 0 else None)
    
    #hair type: 21-24
    string_atts.append(get_best(atts[21:24], 21))
   
    #all the others are singletons
    for i in range(24,len(atts)):
        string_atts.append(attributes[i] if atts[i] > 0 else None)
    
    return string_atts
        

with open(lfw_attributes, 'r', encoding='utf-8') as lfw_file:
    for line in lfw_file.readlines():
        line = line.strip()
        atts = line.split('\t')
        name = atts[0]
        img_num = int(atts[1])
        
        if img_num > 1:
            continue
        
        numerics = [float(x) for x in atts[2:]]
        string_atts = atts_to_string(numerics)        
        lfw[name] = [x for x in string_atts if x is not None]

    
with open(mapping_file, 'r', encoding='utf-8') as mappings:
    with open(out_file, 'w', encoding='utf-8') as output_file:
        
        for line in mappings.readlines():
            line = line.strip()
            (sample, actual) = line.split('->')
            actual = actual.replace('_', ' ').replace('0001.bmp', '').strip()            
            attributes = lfw[actual]
            output_file.write(sample + '\t' + '\t'.join(attributes) + "\n")
        
        
    
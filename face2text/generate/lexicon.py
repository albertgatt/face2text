#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 21 12:05:42 2017

@author: albertgatt
"""
from nltk.corpus import wordnet as wn
from random import choice

class Attribute(object):
    def __init__(self, name, value=True, category=wn.ADJ, wn_synset='01', expression=None, semcat=None, confidence=1, syns=[]):
        self.name = name
        self.value = value
        self.category = category
        self.synset = name + '.' + category + '.' + wn_synset
        self.expression = expression
        self.semcat = semcat
        self.confidence = 1
        self.synonyms = syns                    
            
    @property         
    def synonyms(self):
        return self.__synonyms
    
    @synonyms.setter
    def synonyms(self, syns):        
        if len(syns) == 0 and self.synset is not None:
            try:
                syn = wn.synset(self.synset)
                self.__synonyms = [lemma.name() for lemma in syn.lemmas()]
            except:
                self.__synonyms = []
                
        elif len(syns) > 0:
            self.__synonyms = syns  
        
        else:
            self.__synonyms = []
    
    
    def __find_antonym(self):
        antonym = None
        
        try:
            syn = wn.synset(self.synset)
            antonyms = [ant.name() for lemma in syn.lemmas() for ant in lemma.antonyms() if ant]
            
            if len(antonyms) > 0:
                antonym = choice(antonyms)

        except:
            pass
        
        return antonym    
    
    
    def __syn_express(self, syn=True):
        expression = None
                    
        #In case this is false, try to find an antonym
        if not self.value:
            antonym = self.__find_antonym()
            expression = antonym if antonym else 'not ' + self.name
         
        elif syn:             
            synonym = None
                  
            if len(self.synonyms) > 0:
                synonym = choice(self.synonyms)

            expression = synonym if synonym else self.name
            
        else:
            expression = self.name
            
        return expression
    
    def express(self, syn=True):
        expression = None
                
        if self.expression:
            expression = self.expression if self.value else 'not ' + self.expression
   
        else:
            expression = self.__syn_express(syn)
        
        
        if not expression:
            if not self.value:
                expression = 'not ' + self.name
        
            else:
                expression = self.name
            
        return expression.replace('_', ' ')
    
    
class Lexicaliser(object):
    def __init__(self):  
        self.att_list = ['Male', 'Bald', 'Bangs', 'Black_Hair', 'Blond_Hair', 
                'Blurry', 'Brown_Hair', 'Bushy_Eyebrows', 'Chubby', 'Double_Chin', 
                'Eyeglasses', 'Goatee', 'Gray_Hair', 'Heavy_Makeup', 'Mustache', 
                'Narrow_Eyes', 'No_Beard', 'Pale_Skin', 'Receding_Hairline', 
                'Rosy_Cheeks', 'Sideburns', 'Smiling', 'Straight_Hair', 'Wavy_Hair', 
                'Wearing_Hat', 'Wearing_Lipstick', 'Wearing_Necktie', 'Young']
        
        self.attributes = {
            'Male': ('man', wn.NOUN, '01', 'GENDER', ['man', 'male']),
            'Female': ('woman', wn.NOUN, '01', 'GENDER', ['woman', 'female']),
            'Bald': ('bald', wn.ADJ, '02', 'BALDNESS', ['bald', 'bare-headed', 'bald-pated']),
            'Bangs': ('bangs', 'PP_with', None, None, []),
            'Black_Hair': ('black hair', 'PP_with', None, 'HAIRCOLOUR', ['dark', 'black']),
            'Blond_Hair': ('blond hair', 'PP_with', None, 'HAIRCOLOUR', ['light', 'light-coloured']),
            'Blurry': ('blurry', wn.ADJ, None, None, []),
            'Brown_Hair': ('brown hair', 'PP_with', None, 'HAIRCOLOUR', ['dark', 'brown']),
            'Bushy_Eyebrows': ('bushy eyebrows', 'PP_with', None, 'EYEBROWS', ['bushy eyebrows', 'thick eyebrows', 'luxurious eyebrows']),
            'Chubby': ('chubby', wn.ADJ, '01','SHAPE', ['chubby', 'plump', 'chubby-cheeked']),
            'Double_Chin': ('double chin', 'PP_with', None, None, []),
            'Eyeglasses': ('glasses', 'VP_wearing', None, 'CLOTHING', ['glasses', 'eyeglasses', 'specs']),
            'Goatee': ('goatee', 'PP_with', None, 'FHAIR', []),
            'Gray_Hair': ('grey hair', 'PP_with', None, 'HAIRCOLOUR', ['grey', 'greying']),
            'Heavy_Makeup': ('heavy makeup', 'VP_wearing', None, 'MAKEUP', ['makeup']),
            'Mustache': ('a moustache', 'PP_with', None, 'FHAIR', []),
            'Narrow_Eyes': ('narrowed eyes', 'PP_with', None, None, []),
            'No_Beard': ('no beard', 'PP_with', None, 'FHAIR', []),
            'Pale_Skin': ('pale skin', 'VP_have', None, 'COMPLEXION', ['pale skin', 'a light complexion']),
            'Receding_Hairline': ('a receding hairline', 'PP_with', None, 'HAIRLINE', ['receding', 'thinning', 'sparse']),
            'Rosy_Cheeks': ('rosy cheeks', 'PP_with', None, 'COMPLEXION', ['rosy cheeks']),
            'Sideburns': ('sideburns', 'PP_with', '01', 'SHAIR', []),
            'Smiling': ('smiling', wn.ADJ, '01', 'EXPRESSION', ['smiling', 'grinning']),
            'Straight_Hair': ('straight hair', 'PP_with', None, 'HAIRSTYLE', ['straight', 'smooth']),
            'Wavy_Hair': ('wavy hair', 'PP_with', None, 'HAIRSTYLE', ['wavy']),
            'Wearing_Hat': ('a hat', 'VP_wearing', None, 'CLOTHING', ['a hat', 'some kind of headgear']),
            'Wearing_Lipstick': ('lipstick', 'VP_wearing', None, 'MAKEUP', []),
            'Wearing_Necktie': ('a tie', 'VP_wearing', None, 'CLOTHING', ['a tie', 'a necktie', 'something around the neck']),
            'Young': ('young', wn.ADJ, None,'AGE', ['young', 'youngish', 'younger-looking', 'youthful']),
            }
        
        #Dictionary that specifies which attributes are excluded by the presence of others
        self.exclusion = {'Female':['Bald', 'Beard', 'Mustache', 'Goatee', 'Receding_Hairline', 'No_Beard', 'Sideburns'],
                             'Male': ['Bangs', 'Heavy_Makeup', 'Wearing_Lipstick'], 
                             'Receding_Hairline': ['Bald']}


    def lexicalise(self, string_atts, ignore_list=[], negations=False):
        '''Maps a dictionary of attribute strings with corresponding values (-1, 1) to Attribute objects'''
        attributes = {}       
        
        for a in string_atts:
            v = string_atts[a]

            #Non-male gets mapped to female            
            if a == 'Male' and v < 0:            
                attributes['Female'] = Attribute('woman', value=True, category=wn.NOUN, semcat='GENDER')

            elif a in ignore_list:
                continue

            elif v < 0 and not negations:
                continue
                        
            elif a in self.attributes:
                (exp, cat, sense, semcls, syns) = self.attributes[a]
                        
                if semcls is None:
                    continue
                        
                if sense is None:
                    sense  = '01'

                #For adjectives and nouns, we use the atribut name, its provided syns, or wordnet syns                        
                if cat in [wn.ADJ, wn.NOUN]:                            
                    if len(syns) > 0:                                
                        attributes[a] = Attribute(exp, value=True, category=cat, wn_synset=sense, semcat=semcls, syns=syns)
                    else:
                        attributes[a] = Attribute(exp, value=True, category=cat, wn_synset=sense, semcat=semcls)
                #for phrasal categories, we use the provided expression or provided syns
                else:
                    if len(syns)> 0:
                        attributes[a] = Attribute(exp, value=True, category=cat, wn_synset=sense, semcat=semcls, syns=syns)
                    else:
                        attributes[a] = Attribute(a, value=True, category=cat, wn_synset=sense, expression=exp, semcat=semcls)

        for a in self.exclusion:
            if a in attributes:
                attributes = {k:attributes[k] for k in attributes if k not in self.exclusion[a]}
            
        return attributes

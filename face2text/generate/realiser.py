#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 16 16:31:43 2017

@author: albertgatt
"""
from string import Template
import re
from random import choice
from nltk.corpus import wordnet as wn

class Realiser(object):
    def __init__(self, use_synonyms = True):
        self.syn = use_synonyms
        self.np = Template('$det $np.')
        self.np_adj = Template('$adj $n')
        self.pp = Template('$prep $np')
        self.vp = Template('$verb $np')
        self.sent_aux = Template('$subj $a $vp.')
        self.poss_sent = Template('$subj $n is $adj.')
        self.svo_sent = Template('$subj $v $np.')

    def conjoin(self, atts):
        atts = [a for a in atts if len(a) > 0]
        
        if len(atts) == 0:
            return ''
        
        elif len(atts) == 1:
            return atts[0]
        
        elif len(atts) == 2:    
            return ' and '.join(atts)
        
        else:
            return ', '.join(atts[:-1]) + ' and ' + atts[-1]        


    def adj_phrase(self, features, semtypes, punct=', '): 
        premodifiers = []
            
        for t in semtypes:
            if t in features:
                atts = [a.express(syn=self.syn) for a in features[t] if a.category == wn.ADJ]
                premodifiers = premodifiers + atts     
        
        return punct.join(premodifiers)
    
    
    def postmod_phrase(self, features, semtypes):
        #Postmodtypes can be of two kinds: PP and VP
        postmods = []
        
        for pmt in semtypes:
            if pmt in features:                                
                #Separate into those with vp or pp
                postmods.append(self.generate_pp([a for a in features[pmt] if a.category=='PP_with'], 'with'))
                postmods.append(self.generate_vp([a for a in features[pmt] if a.category=='VP_wearing'], 'wearing'))
                
        postmod_phrase = ' '.join(postmods).strip()
        return postmod_phrase        


    def head_noun(self, features):
        noun = None;
        
        if 'GENDER' in features:
            noun = features['GENDER'][0].express(syn=self.syn)
        else:
            noun = 'person'
        
        return noun


    def choice(self, attlist, random=False):
        '''Make a single choice of a set of attributes of the same type,
        by confidence level or randomly'''
        
        if random:
            return choice(attlist)
        else:
            sortatts = sorted(attlist, key=lambda a: a.confidence, reverse=True)
            return sortatts[0]        


    def get_article(self, np):
        if re.match('^[aeiou]', np):
            return 'an'
        else:
            return 'a'    

    def generate_vp(self, atts, v):
        result = '' 
        phrase = ''
        
        if len(atts) > 0:        
            expressed = [a.express(self.syn) for a in atts]    
                
            if len(expressed) > 1:
                phrase = self.conjoin(expressed)
            else:
                phrase = expressed[0]                        
                
            result = self.vp.substitute(verb=v, np=phrase)
            
        return result
        
    def generate_pp(self, atts, p):
        
        if len(atts) == 0:
            return ''
        
        expressed = [a.express(self.syn) for a in atts]
        phrase = '' 
        
        if len(expressed) > 1:
            phrase = self.conjoin(expressed)
        else:
            phrase = expressed[0]
            
        return self.pp.substitute(prep=p, np=phrase)
        

    def noun_phrase(self, features, premodtypes, postmodtypes, det=True):
        noun = self.head_noun(features)
        premodphrase = self.adj_phrase(features, premodtypes)
        postmodphrase = self.postmod_phrase(features, postmodtypes)
        full_phrase = ''
        
        if premodphrase is not None and len(premodphrase) > 0:
            full_phrase = self.np_adj.substitute(adj=premodphrase, n=noun).strip()
        else:
            full_phrase = noun            
                                   
        
        if postmodphrase is not None and len(postmodphrase) > 0:
            full_phrase = ' '.join([full_phrase, postmodphrase]).strip()
            
        article = self.get_article(full_phrase) if det else ''    
        
        return self.np.substitute(det=article, np=full_phrase).capitalize()  
    
    
    def state_sentence(self, gender, verb, features, semtypes):
        atts = []
        
        for a in semtypes:
            if a in features:
                atts = atts + features[a]
                
        pronoun = self.__pronoun(gender)
        aux = 'are'
        
        if pronoun == 'he':
            aux = 'is'
        elif pronoun == 'she':
            aux = 'is'
    
        phrase = self.generate_vp(atts, verb).strip()

        if phrase is not None and len(phrase) > 0:
            return self.sent_aux.substitute(subj=pronoun, a=aux, vp=phrase).strip().capitalize()
        else:
            return ''
    
    def __choose(self, features, semtypes):
        phrases = []
        
        for s in semtypes:
           if s in features:
               a = self.choice(features[s])
               
               if a:
                   exp = a.express()
           
                   if exp and len(exp.strip()) > 0:
                       phrases.append(exp.strip())

        return phrases      
    

    def __pronoun(self, gender, poss=False):
         #self.poss_sent = Template('$subj $n is $adj.')
        pronoun = 'their' if poss else 'they'   
        
        if gender == 'man':
            pronoun = 'his' if poss else 'he'

        elif gender == 'woman':
            pronoun = 'her' if poss else 'she'
        
        return pronoun
    
    
    def poss_sentence(self, gender, head, features, semtypes):        
        pronoun = self.__pronoun(gender, poss=True)        
        phrases = self.__choose(features, semtypes)                
 
        if len(phrases) > 0:                           
            sent = self.poss_sent.substitute(subj=pronoun, n=head, adj=self.conjoin(phrases))
            return sent.capitalize()
        else:
            return ''
    
    def svo_sentence(self, gender, verb, features, semtypes):
        pronoun = self.__pronoun(gender)
        phrases = self.__choose(features, semtypes)
        
        if len(phrases) > 0:                           
            sent = self.svo_sent.substitute(subj=pronoun, v=verb, np=self.conjoin(phrases))
            return sent.capitalize()
        else:
            return ''
        
        
        
            
                
        
    


    

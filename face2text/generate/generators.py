#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 21 11:10:20 2017

@author: albertgatt
"""
from random import choice
import realiser, lexicon
import gensim, math, json, re
import numpy as np
import nltk
from nltk.data import load as nltkload
from nltk.corpus import stopwords, wordnet as wn
from nltk import FreqDist, LaplaceProbDist
#from nltk.parse.stanford import StanfordDependencyParser
from scipy.stats import entropy
import abc


class Generator(object):
    def __init__(self):
        self.categories = [wn.NOUN, wn.ADJ, 'PP_with', 'VP_wearing']
        
    @abc.abstractmethod
    def generate(self, attributes):
        return ''
    
    
class SimpleGenerator(Generator):
    def __init__(self, synonyms=True, negation=False):
        #super().__init__()
        super(SimpleGenerator, self).__init__()
        self.__syn = synonyms
        self.realiser = realiser.Realiser(use_synonyms=self.__syn)
        self.lexicaliser = lexicon.Lexicaliser()
        self.negation = negation
        self.__ignore_list = []


    @property
    def synonyms(self):
        return self.__syn
    
    @synonyms.setter
    def synonyms(self, syn):
        self.__syn= syn
        self.realiser = realiser.Realiser(use_synonyms =self.__syn)

    @property
    def ignore_list(self):
        return self.__ignore_list
    
    @ignore_list.setter
    def ignore_list(self, atts):
        self.__ignore_list = atts
                
        
    def generate(self, atts):
        '''Generate a description based on the input attributes. Attributes are assumed
        to be mapped to positive or negative values.'''
        
        #MAp these attributes to lexicalisable expressions
        #Apply exclusions based on gender etc
        attributes = self.lexicaliser.lexicalise(atts, ignore_list=self.ignore_list, negations=self.negation)            
        features = {}
        
        #Choose which attributes to use
        for k in attributes:
            a = attributes[k]
            if a.semcat in features:
                features[a.semcat].append(a)                
            else:
                features[a.semcat] = [a]                                   
            
        #We need to know the gender (determines pronouns and attributes)
        if 'GENDER' in features:
            gender = features['GENDER'][0].name.lower()   
        else:
            gender = 'person'         
        
        #The semantic types included in the first description:
        premod_types = ['AGE', 'BALDNESS', 'EXPRESSION', 'SHAPE'] #Things we express as premodifiers
        postmod_types = ['EYEBROWS', 'MAKEUP'] #Things we express as postmodifiers
        
        #Sentence 2:semantic types
        sent2_types = ['CLOTHING'] 
        
        #Sentence 3: semantic types
        sent3_types = ['HAIRLINE', 'HAIRCOLOUR', 'HAIRSTYLE']
        
        #Sentence 4: expression
        sent4_types = ['FHAIR', 'SHAIR', 'COMPLEXION']
               
        np1 = self.realiser.noun_phrase(features, premod_types, postmod_types)
        sent2 = self.realiser.state_sentence(gender, 'wearing', features, sent2_types)
        sent3 = self.realiser.poss_sentence(gender, 'hair', features, sent3_types)
        sent4 = self.realiser.svo_sentence(gender, 'has', features, sent4_types)
        return ' '.join( [np1, sent2, sent3, sent4] )
        
     
        
class RetrievalGenerator(Generator):
    '''Abstract class for retrieval-based generation. Requries a json file with texts for a given set of attributes.'''
    
    def __init__(self, json_file, stopwords=stopwords.words("english"), min_length=5):
        #super().__init__()
        super(RetrievalGenerator, self).__init__()
        self.min_text_length = min_length
        self.sentence_splitter = nltkload('tokenizers/punkt/{0}.pickle'.format('english'))
        self.__stopwords = []
        
        if stopwords is not None:
            self.stopwords = stopwords     
            
        self.__json_data = None                
        self.__texts = []
        self.full_texts = []
        self.__weighted_terms = {}
        
        self.json_data = json_file
        self.__stopwords = []
                
    
    @property
    def stopwords(self):
        return self.__stopwords
    
    @stopwords.setter
    def stopwords(self, stopwords):
        self.__stopwords.extend(stopwords)
        
    
    @property
    def texts(self):
        return self.__texts
    
    @property
    def weighted_terms(self):
        return self.__weighted_terms
    
    @property
    def json_data(self):
        return self.__json
    
    @json_data.setter
    def json_data(self, json_file, term_weight=10):
        with open(json_file, 'r', encoding='utf-8') as im_search:
            js = json.loads(im_search.read())                    

            for resultset in js:
                if resultset == 'query':
                    continue                           
            
                if 'text' in js[resultset]:                                               
                    t = self.__clean_text(js[resultset]['text'])
                    self.full_texts.append(t)
                    sents = self.sentence_splitter.tokenize(t)            
                    self.__texts.extend(sents)                
                
                if 'similar_img_text' in js[resultset]:
                    for i in js[resultset]['similar_img_text']:
                        t = js[resultset]['similar_img_text'][i]
                        
                        if t is not None and len(t) >= self.min_text_length: 
                            t = self.__clean_text(t)
                            self.full_texts.append(t)
                            sents = self.sentence_splitter.tokenize(t)
                            self.__texts.extend(sents)                                        
                
                if 'ranked_google_rel_tags' in js[resultset]:
                    for d in js[resultset]['ranked_google_rel_tags']:
                        self.__weighted_terms[d['text']] = term_weight/int(d['rank']) 
                                        
            self.__json = js
            
    def __clean_text(self, text):
        text = re.sub(r'[\r\n]+', '. ', text)
        return text.lower()
    
    
    def cosine(self, vec1, vec2):       
        cosine_similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

        try:
            if math.isnan(cosine_similarity):
                cosine_similarity=0
        except:
            cosine_similarity=0        
            
        return cosine_similarity
    

class Phrase2VecGenerator(RetrievalGenerator):
    def __init__(self, json_file, path_to_w2vec=None):
        #super().__init__(json_file)
        super(Phrase2VecGenerator, self).__init__(json_file)
        self.__path = None
        self.__model = None        
        
        if path_to_w2vec is not None:
            self.model = path_to_w2vec
    
    @property
    def model(self):
        return self.__path
    
    @model.setter
    def model(self, path):
        print("Loading vector model. This might take a while...")
        self.__path = path
        self.__model = gensim.models.KeyedVectors.load_word2vec_format(path, binary=True)
        print("done!\n")
    
    
    def __average_vector(self, vectors, ignore=[]):
        '''Flatten a vector of vectors to a single vector'''
        
        if len(ignore) == 0: 
            return np.mean(vectors, axis = 0)
        
        else: 
            return np.dot(np.transpose(vectors),ignore)/sum(ignore)    
    
    
    def __phrase2vec(self, phrase):          
        phrase = phrase.lower()
        words = [word for word in nltk.word_tokenize(phrase) if word not in self.stopwords]
        vectors = []

        for w in words:
            try:
                w_vector = self.__model[w]
                vectors.append(w_vector)
            except:
                pass
            
        return self.__average_vector(vectors)
    
    
    def generate(self, attributes, nbest=5):
        attribute_vector = []
        results = {}
        
        if isinstance(attributes, str):
            attribute_vector = self.__phrase2vec(attributes)
        else:
            attribute_vector = self.__phrase2vec(' '.join([a.name.replace("_", ' ') for a in attributes]))

        for t in self.texts:
            if t not in results: #in case we have duplicate texts
                text_vector = self.__phrase2vec(t)    
                results[t] = self.cosine(attribute_vector, text_vector)
        
        sorted_texts = sorted(results, key=results.__getitem__, reverse=True)
        return [(t, results[t]) for t in sorted_texts[:nbest]]



class FrequencyDistGenerator(RetrievalGenerator):
    
    def __init__(self, json_file):
        #super().__init__(json_file)
        super(FrequencyDistGenerator, self).__init__(json_file)
        self.__global_dist = FreqDist()
        self.__text_smoothed_dists = []
        self.__global_smoothed_dist = None
        self.__vocab =set([])
        
    def __build_distributions(self, attributes):    
        if isinstance(attributes, str):
            attributes = nltk.word_tokenize(attributes)
        
        for text in self.full_texts:
            tokens = [w for w in nltk.word_tokenize(text.lower()) if w not in self.stopwords]
            
#            if len(tokens) <= self.min_text_length:
#                continue
            
            self.__vocab = self.__vocab.union(tokens)

            #build frequency dist for this text
            text_freq_dist = FreqDist(tokens)

            #add weights from google tags
            for w in self.weighted_terms:
                if w in text_freq_dist:
                    text_freq_dist[w] += self.weighted_terms[w]

            #combine vocab from this text to the global
            self.__global_dist += text_freq_dist

            #store the tokens for this text
            self.__text_smoothed_dists.append(LaplaceProbDist(text_freq_dist))

        self.__global_smoothed_dist = LaplaceProbDist(self.__global_dist)


    def __best_text(self, func='jsd'):
        results = np.empty(len(self.full_texts))

        #build the overall probability distribution    
        global_probs = np.array([self.__global_smoothed_dist.prob(w) for w in self.__vocab])
        selector = np.argmin if func in ['kld', 'jsd'] else np.argmax

        #individual text distributions: set 0 freq for all words in global but not in text
        for i in range(len(self.full_texts)):
            
            if len(self.full_texts[i]) < self.min_text_length:
                continue
            
            text_probs = np.array([self.__text_smoothed_dists[i].prob(w) for w in self.__vocab])
    
            if func == 'kld':
                results[i] = entropy(text_probs, global_probs)    
            elif func == 'jsd':
                m = 0.5 * (text_probs + global_probs)            
                results[i] = 0.5 * (entropy(text_probs, m) + entropy(global_probs, m))        
            elif func == 'mult':
                results[i] = np.sum(np.multiply(text_probs, global_probs))
            else:
                raise RuntimeError('Unknown function: ' + func)

        best = selector(results)
        return (self.full_texts[best], results[best])
        

    def generate(self, attributes, length_norm=False, func='jsd', nbest=5):
        self.__build_distributions(attributes)
        (best_text, best_prob) = self.__best_text(func)
        sents = self.sentence_splitter.tokenize(best_text)
        num_sents = len(sents)
        probs = np.empty(num_sents)        
    
        for i in range(num_sents):
            toks = [w for w in nltk.word_tokenize(sents[i]) if w not in self.stopwords]
            tok_probs = [self.__global_smoothed_dist.prob(w) for w in toks]
            sent_prob = np.sum(tok_probs)/len(toks) if length_norm else np.sum(tok_probs)
            probs[i] = sent_prob
    
        return [(sents[si], probs[si]) for si in np.argpartition(probs,-nbest)[-nbest:]]
            
    

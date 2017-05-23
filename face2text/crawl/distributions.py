import gensim

wv = gensim.models.KeyedVectors.load_word2vec_format('../models/GoogleNews-vectors-negative300.bin', binary=True)  


print(wv['computer'])  # numpy vector of a word)

#most similar 
print(wv.most_similar(positive=['woman', 'king'], negative=['man']))
print(wv.most_similar_cosmul(positive=['woman', 'king'], negative=['man']))


print(wv.similarity('woman', 'man'))


#Probability of a text under the model:
#print(model.score(["The fox jumped over a lazy dog".split()]))
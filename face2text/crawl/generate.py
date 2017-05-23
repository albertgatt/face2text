import nltk
from nltk import FreqDist, LaplaceProbDist
from nltk.parse.stanford import StanfordDependencyParser
from nltk.corpus import stopwords
import json
import numpy as np
from scipy.stats import entropy
import re

text = '''This is a sample text'''


def dist(text, stopwords=[], terms = {}, term_weight=10):
	tokens = nltk.word_tokenize(text.lower())
	tokens = [w for w in tokens if w not in stopwords]
	total = len(tokens)
	f = FreqDist(tokens)

	#weight frequencies from ranked list
	[f[w] + term_weight/terms[w] for w in terms if w in f]

	lpd = LaplaceProbDist(f)
	return (f, lpd)

def build_distributions(json_file_in, stoplist = [], terms={}, term_weight = 10):
	global_freq_dist = FreqDist()
	img_lpd = {}	
	texts = {}
	vocab = set([])
	text_search_paths = ['text_query_results', 'similar_img_text']
	num_texts = 0

	with open(json_file_in, 'r', encoding='utf-8') as im_search:
		js = json.loads(im_search.read())

		for resultset in js:
			jsdict = resultset['results']
			
			for result in jsdict:
				if 'expanded_search' in result:
					expanded_search = result['expanded_search']
					
					#google tags 
					weighted_terms = {}
					for d in expanded_search['ranked_google_rel_tags']:
						weighted_terms[d['text']] = term_weight/int(d['rank'])		


					for path in text_search_paths:

						#text from similar images
						if path in expanded_search:
							#num_ranks = len(expanded_search['similar_img_text'])

							for rank in expanded_search[path]:
								text = expanded_search[path][rank]['text']					
								tokens = [w for w in nltk.word_tokenize(text.lower()) if w not in stoplist]
								vocab = vocab.union(tokens)

								#build frequency dist for this text
								text_freq_dist = FreqDist(tokens)

								#add weights from google tags
								for w in weighted_terms:
									if w in text_freq_dist:
										text_freq_dist[w] += weighted_terms[w]

								#combine vocab from this text to the global
								global_freq_dist += text_freq_dist

								#store the tokens for this text
								img_lpd[num_texts] = LaplaceProbDist(text_freq_dist)

								#and store the text
								texts[num_texts] = text

								#increment text counter
								num_texts += 1


	return (list(vocab), LaplaceProbDist(global_freq_dist), img_lpd, texts)


def best_text(vocab, global_lpd, img_lpd, num_texts, func='kld'):
	results = np.empty(num_texts)

	#build the overall probability distribution	
	global_probs = np.array([global_lpd.prob(w) for w in vocab])
	selector = np.argmin if func in ['kld', 'jsd'] else np.argmax


	#individual text distributions: set 0 freq for all words in global but not in text
	for text in img_lpd:
		img_probs = np.array([img_lpd[text].prob(w) for w in vocab])

		if func == 'kld':
			results[text] = entropy(img_probs, global_probs)	
		elif func == 'jsd':
			m = 0.5 * (img_probs + global_probs)			
			results[text] = 0.5 * (entropy(img_probs, m) + entropy(global_probs, m))		
		else:
			results[text] = np.sum(np.multiply(img_probs, global_probs))

	best = selector(results)
	return (best, results[best])


def best_sentence(sentences, global_lpd, stoplist=[], length_norm=False):
	probs = np.empty(len(sentences))

	for i in range(len(sentences)):
		toks = [w for w in nltk.word_tokenize(sentences[i]) if w not in stoplist]
		tok_probs = [global_lpd.prob(w) for w in toks]
		sent_prob = np.sum(tok_probs)/len(toks) if length_norm else np.sum(tok_probs)
		probs[i] = sent_prob

	best_si = np.argmax(probs)
	return(sentences[best_si], probs[best_si])


def dependency_parse(sentence):
	parser_jar = '/home/albert/STANFORD_PARSER/stanford-parser.jar'
	model_jar = '/home/albert/STANFORD_PARSER/stanford-english-corenlp-2016-10-31-models.jar' #'stanford-parser-3.7.0-models.jar'
	dep_parser = StanfordDependencyParser(path_to_jar=parser_jar, path_to_models_jar=model_jar)
	result = dep_parser.raw_parse(sentence)
	return list(next(result).triples())

if __name__ == '__main__':
	stoplist = stopwords.words('english')

	#probability distribbutiosn for individual texts and globally
	(vocab, global_lpd, img_lpd, texts) = build_distributions('../output/test_out.json', stoplist=stoplist)


	#best text = text with lowest KLD to global distribution
	(bestrank, best_entropy) = best_text(vocab, global_lpd, img_lpd, len(texts), func='prob')

	#get ranked sentences from the best text
	sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
	parags = [par for par in re.split('\r?\n', texts[bestrank])]
	sentences = [x for par in parags for x in sent_detector.tokenize(par)]
	# sentences = sent_detector.tokenize(texts[bestrank])
	(best_s, best_s_prob) = best_sentence(sentences, global_lpd, stoplist, length_norm=False)
	print(best_s_prob, best_s)
	print(dependency_parse(best_s))



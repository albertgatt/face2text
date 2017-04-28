#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from GoogleScraper import scrape_with_config, GoogleSearchError
from selenium.webdriver.common.keys import Keys
#from boilerpipe.extract import Extractor
from selenium import webdriver
from subprocess import call
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup, Comment
import threading,requests, os, urllib, sys, json, re


# simulating a image search for all search engines that support image search.
# Then download all found images :)

# In our case we want to download the
# images as fast as possible, so we use threads.
class FetchResource(threading.Thread):
	"""Grabs a web resource and stores it in the target directory.

	Args:
		target: A directory where to save the resource.
		urls: A bunch of urls to grab

	"""
	def __init__(self, name, urls, target=None, get_text=True):
		super().__init__()
		self.name = name
		self.target = target
		self.urls = urls
		self.std_naming = False #change to True if we want standardised filenames: Ti_qj
		self.results = {}
		self.get_text = get_text


	def _visibile_text(self, soup):
		# kill all script, style, comment etc elements
		[s.extract() for s in soup(["script", "style", '[document]', 'head', 'meta'])]
		[c.extract() for c in soup.findAll(text=lambda text:isinstance(text, Comment))]

		# get text
		text = soup.get_text()

		# break into lines and remove leading and trailing space on each
		lines = (line.strip() for line in text.splitlines())

		# break multi-headlines into a line each
		chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
		
		# drop blank lines and replace newlines with single space
		text = ' '.join(chunk for chunk in chunks if chunk)

		return text.encode('utf-8').decode('utf-8', 'ignore')

	def run(self):
		self.results = {}
		i = 0
		for url in self.urls:
			i+=1
			url = urllib.parse.unquote(url)
			
			try:				
				content = requests.get(url).content

				if self.get_text:
					soup = BeautifulSoup(content, 'lxml', from_encoding='utf-8')
					text = self._visibile_text(soup)
					
					if text and len(text) > 0:					
						self.results[i] = {}
						self.results[i]['url'] = url
						self.results[i]['text'] = str(text)

				if self.target:
					self.save(url, content)
			except Exception as e:
				pass

		return self.results 

	def save(self, url, content):

			if self.std_naming:
				fname = self.name + "_" + str(i)
			else:
				fname = url.split("/")[-1]
			
			with open(os.path.join(self.target, fname), 'wb') as f:
				try:
					content = requests.get(url).content
					f.write(content)
					self.fnames[fname] = url
				except Exception as e:
					pass
				# print('[+] Fetched {}'.format(url))


class ImageCaptionScraper(object):
	def __init__(self):
		self.__target_dir = ''
		self.search_engines = ['google', 'bing', 'yahoo'] #yandex
		self.__unsupported = ['duckduckgo']
		self.browser = None
		self.phantom_path = '~/phantomjs-2.1.1-linux-x86_64/bin'

	def init_browser(self):
		#create a selenium browser
		desired_cap = dict(webdriver.DesiredCapabilities.PHANTOMJS)
		user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'
		desired_cap['phantomjs.page.settings.userAgent'] = user_agent
		self.browser =  webdriver.PhantomJS(desired_capabilities=desired_cap)

	@property
	def phantom_path(self, ph):
		return os.environ['PHANTOMJS']

	@phantom_path.setter
	def phantom_path(self, ph):
		os.environ['PHANTOMJS'] = ph
		os.environ['PATH'] += ph
		

	@property
	def target_directory(self):
		return self.__target_dir

	@target_directory.setter
	def target_directory(self, targ_dir):
		# make a directory for the results
		try:
			os.mkdir(targ_dir)			
		except FileExistsError:
			pass
		self.__target_dir = targ_dir

	@property
	def search_engines(self):
		return self.__search_engines

	@search_engines.setter
	def search_engines(self, engines):
		self.__search_engines = []

		for e in engines:
			# if e in self.unsupported:
			# 	raise RuntimeError(e + ' is not a supported search engine')
			# if e not in self.__search_engines:
			self.__search_engines.append(e)

		
	def __make_threads(self, urls, save_to_target, get_text, num_threads=100):
		threads = [FetchResource('', [], 
							target=(self.target_directory if save_to_target else None), get_text=get_text) 
							for i in range(num_threads)]
		while urls:
			for t in threads:
				try:
					t.urls.append(urls.pop())
				except IndexError as e:
					break

		threads = [t for t in threads if t.urls]

		for t in threads:
			t.start()

		for t in threads:
			t.join()

		return threads

	def _merge_results(self, fetchresources):
		#Put results in order
		i = 0
		results = {}

		for t in fetchresources:
			for j in t.results:
				i += 1
				results[i] = {}
				results[i]['url'] = t.results[j]['url']
				results[i]['text'] =  t.results[j]['text']

		return results

	def _parse_filename(self, url):
		try:
			filename = url.split("/")[-1]
			return os.path.join(self.target_directory, filename)
		except:
			return None

	def _search_by_image_url(self, img_url):
		"""Uploads the query image to Google search by image service"""
		
		#go to google image search and choose to upload an image
		self.browser.get('https://images.google.com')
		qbi = self.browser.find_element_by_id('qbi')
		qbi.click()
		uit = self.browser.find_element_by_id('qbpiu')
		uit.click()

		#send the query image file
		current_url = self.browser.current_url
		qburl = self.browser.find_element_by_id('qbui')
		qburl.send_keys(img_url)
		qburl.send_keys(Keys.RETURN)
		
		# waiting to upload image
		while current_url == self.browser.current_url:
			pass

		# wait to find text in google search box
		input_text = ''
		keep_trying = True

		i = 0
		while input_text == '' and keep_trying:
			try:
				input_text = self.browser.find_element_by_id('lst-ib').get_attribute('value')
				i += 1
				if input_text != '' or i > 500:
					keep_trying = False
			except NoSuchElementException:
				pass	    

		try:
			#Google's guess about the input text related to the query image
			# adding stock photos in google search datasets field
			self.browser.find_element_by_id('lst-ib').clear()
			#input_text = input_text.encode('utf-8')
		except:
			pass	     

		try:
			# locating the 'visually similar images' link
			visually_similar_link = self.browser.find_element_by_link_text('Visually similar images')
			return (visually_similar_link.get_attribute("href"), input_text)

		except NoSuchElementException:
			return (0, input_text)


	def find_pages(self, save_to_target, *keywords ):
		kw = ' '.join(keywords)

		config = {
			'use_own_ip': True,
			'keyword': kw,
			'search_engines': self.search_engines,
			'num_pages_for_keyword': 1,
			'scrape_method': 'selenium',
			'sel_browser': 'Phantomjs',	
			'print_results': 'summarize',		
		}

		try:
			search = scrape_with_config(config)
		except GoogleSearchError as e:
			print(e)

		# let's inspect what we got
		image_urls = []

		for serp in search.serps:
			image_urls.extend(
				[link.link for link in serp.links]
			)
				
		threads = self.__make_threads(image_urls, save_to_target, True)
		return self._merge_results(threads)


	def find_images(self, json_file, *keywords):
		kw = ' '.join(keywords)

		# See in the config.cfg file for possible values
		config = {
			'keyword': kw, # :D hehe have fun my dear friends
			'search_engines': self.search_engines, # duckduckgo not supported
			'search_type': 'image',
			'scrape_method': 'selenium',
			'do_caching': False,
			'output_filename': json_file,

		}

		try:
			search = scrape_with_config(config)
		except GoogleSearchError as e:
			print(e)

		image_urls = []

		for serp in search.serps:
			image_urls.extend(
				[link.link for link in serp.links]
			)

		# print('[i] Going to scrape {num} images and saving them in "{dir}"'.format(
		# 	num=len(image_urls),
		# 	dir=self.target_directory
		# ))
		threads = self.__make_threads(image_urls, True, False)
		return self._merge_results(threads)
		

	def google_similar_image_text(self, link):
		self.browser.get(link) #access similar images url
		similar_images = self.browser.find_elements_by_class_name('rg_i')
		results = {}
		threads = []
		urls = []

		i = 0

		# looping over the visually similar images
		for image in similar_images:	
			try:        
				image.click()			
				visits = self.browser.find_elements_by_xpath("//span[contains(text(), 'Visit page')]")

				for v in visits:
					# go to the parent element
					page_link_node = v.find_element_by_xpath('..')

					# check if current visit is opened after the image was clicked
					if page_link_node.get_attribute('tabindex') == '0':
						# get corresponding page url
						page_link = page_link_node.get_attribute('href')
						urls.append(page_link)
			except:
				continue

		threads = self.__make_threads(urls, False, True)		
		return self._merge_results(threads)	


	def extract_related_google_tags(self, link):
		'''Extract related tags given by google images for visually similar images to a queryimage'''
		self.browser.get(link)
		spans = self.browser.find_elements_by_class_name('sq')
		results = []
		rank = 0

		for span in spans:	
			text = span.text
			parent_a = span.find_element_by_xpath("./..")
			link = parent_a.get_attribute("href")

			if text:
				text = text.strip()

				if len(text) > 0:
					rank += 1
					results.append({'rank': rank, 'text': text, 'link': link})

		return results


	def find_text_for_images(self, json_file, out_file, related_tags=True, visit_similar=False):
		
		with open(json_file, 'r', encoding='utf-8') as im_search:
			js = json.loads(im_search.read())
			
			#jsfile is a list of dicts
			for resultset in js:
				jsdict = resultset['results']

				for result in jsdict:
					im_search_results = {} #store text results here
					link = result['link']												

					#Get google's guess for the actual search query, plus similar images					
					(vis_sim, google_exp) = self._search_by_image_url(link) #google's best guess for the images found
					google_exp = google_exp.strip()
					im_search_results['google_expansion'] = google_exp				
					im_search_results['similar_img_url'] = vis_sim

					if related_tags:
						im_search_results['ranked_google_rel_tags'] = self.extract_related_google_tags(vis_sim)
					
					if visit_similar:
						sim_texts = self.google_similar_image_text(vis_sim)
						im_search_results['similar_img_text'] = sim_texts
					
					if len(google_exp) == 0:
						im_search_results['success'] = False

					else:
						#3. Now, we search for the google expansion and retrieve text
						text_results = self.find_pages(False, google_exp)
						im_search_results['text_query_results'] = text_results
						im_search_results['success'] = len(text_results) > 0
						print("\t Retrieved related text")
					
					# #4 And now save the text results
					result['expanded_search'] = im_search_results

		with open(out_file, 'w', encoding="utf-8") as outfile:
			json.dump(js, outfile, indent=4)


if __name__ == "__main__":
	ics = ImageCaptionScraper()
	ics.init_browser()
	ics.target_directory = '../images/'
	ics.search_engines = ['google', 'bing', 'yahoo'] #yandex
	ics.find_text_for_images('../output/test.json', '../output/test_out.json', related_tags=True, visit_similar=True)
	




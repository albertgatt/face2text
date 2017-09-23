#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import time, os, json
from fetch import GoogleImage, FetchResource



class ImageCaptionScraper(object):
    def __init__(self):
        self.__target_dir = ''
        self.stock_photo_keyword = 'stock photos'
        self.image_search_engine = 'https://images.google.com'
        self.search_engines = ['google', 'bing', 'yahoo'] #yandex
        self.__unsupported = ['duckduckgo']
        self.browser = None
        

    def init_browser(self, phantompath):
        self.phantom_path = phantompath
        #create a selenium browser
        desired_cap = dict(webdriver.DesiredCapabilities.PHANTOMJS)
        user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'
        desired_cap['phantomjs.page.settings.userAgent'] = user_agent
        self.browser =  webdriver.PhantomJS(self.phantom_path, desired_capabilities=desired_cap)

    @property
    def phantom_path(self):
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
            #     raise RuntimeError(e + ' is not a supported search engine')
            # if e not in self.__search_engines:
            self.__search_engines.append(e)

        
    def __make_threads(self, image_objects, mode='text', target=None, num_threads=100):
        threads = [FetchResource([], mode, target) for i in range(num_threads)]
        images = [x for x in image_objects]
        
        while images:
            for t in threads:
                try:
                    t.images.append(images.pop())
                except IndexError as e:
                    break

        threads = [t for t in threads if t.images]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        return threads
       

    def __google_tags(self, link):
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

     
    def find_images_by_url(self, img_url):
        """Uploads the query image to Google search by image service"""
        
        #go to google image search and choose to upload an image
        self.browser.get(self.image_search_engine)
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
            return (None, input_text)


    def extend_img_search(self, img_url, related_tags=True, visit_similar=True):
        '''Extend the results of an image search by finding related images'''
        im_search_results = {}
        
        try:                                        
            #Get google's guess for the actual search query, plus similar images                    
            (vis_sim, google_exp) = self.find_images_by_url(img_url) #google's best guess for the images found            
            google_exp = google_exp.strip()
            im_search_results['google_expansion'] = google_exp                
            im_search_results['similar_img_url'] = vis_sim

            if vis_sim is not None:

                if related_tags:
                    im_search_results['ranked_google_rel_tags'] = self.__google_tags(vis_sim)
            
                if visit_similar:                    
                    self.browser.get(vis_sim) #access similar images url
                    similar_images = [GoogleImage(img, self.browser) for img in self.browser.find_elements_by_class_name('rg_i')]
                    self.__make_threads(similar_images)
                    im_search_results['similar_img_text'] = {}
                    
                    s = 0
                    for sim_img in similar_images:
                        s += 1
                        im_search_results['similar_img_text'][s] = sim_img.text
    
    #            else:
    #                #3. Now, we search for the google expansion and retrieve text
    #                text_results = self.find_pages(False, google_exp)
    #                im_search_results['text_query_results'] = text_results                                   
        except Exception as e:
            pass
            
        return im_search_results


    def find_images_by_keyword(self, json_file, keywords, stock_photo=True, 
                               download_image=False, download_text=True, 
                               expand_search=True, max_results=10):
        '''Search for images and related text given a set of keywords'''

        kw = ' '.join(keywords)               

        #Hold results here
        results = {}
        results['search'] = {'query': kw, 'engine': self.image_search_engine} 

         #Only search for stock photography?                  
        if stock_photo:
            kw += ' ' + self.stock_photo_keyword                  
        
        try:
            #Pass keywowrds to google search
            self.browser.get(self.image_search_engine)
            search_box = self.browser.find_element_by_id('lst-ib')
            search_box.click()
            search_box.send_keys(kw)
            search_box.send_keys(Keys.RETURN)        
            time.sleep(5)
            
            #list of retrieved images
            images = [GoogleImage(img, self.browser) for img in self.browser.find_elements_by_class_name('rg_ic')]
            
            if len(images) > max_results:
                images = images[0:max_results]
  
        except Exception as e:            
            pass


        #Thread to handle searches: no image retrieval, just text
        self.__make_threads(images)

        i = 0
        
        for img in images:
            i += 1    
            results[i] = {}
            results[i]['img_url'] = img.img_url
            results[i]['page_url'] = img.page_url
            results[i]['text'] = img.text
            
            #We can expand the search
            if expand_search:
#                print("Extending search for result " + str(i))
                time.sleep(2)
                extended_results = self.extend_img_search(img.img_url)

                for k in extended_results:
                    results[i][k] = extended_results[k]
        
        #Write all results in json format
        with open(json_file, 'w', encoding='utf-8') as outfile:
            json.dump(results, outfile, indent=4)


def web_crawl(att_file):
    print("Initialising Web Scraper...")
    ics = ImageCaptionScraper()
    ics.init_browser('/Users/albertgatt/bin/phantomjs/bin/phantomjs')
    ics.target_directory = '../output'    
    ics.search_engines = ['google', 'bing', 'yahoo'] #yandex
    print("done\n")

    with open(att_file, 'r', encoding='utf-8') as input_file:
        for line in input_file.readlines():
            line = line.strip()
            atts = line.split('\t')
            image = atts[0]
            keywords = ["'" + x + "'" for x in atts[1:]] #add quotes for multiword

            #Procedure:
            #1. Find images for tags
            #2. Extract text for images
            #3. (optional) Visit similar images and extract tags  and text for those           
            print("Crawling for: " + image + '...')            
            filename = '../output/' + image + '.json'
            ics.find_images_by_keyword(filename, keywords)
            print('done\n')

web_crawl('../utils/lfw_sample_attributes.txt')
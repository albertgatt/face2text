#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 12:31:57 2017

@author: albertgatt
"""
import threading,requests, os, urllib, jpype
from boilerpipe.extract import Extractor

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
    def __init__(self, images, mode, target_dir):
        #super().__init__()
        super( FetchResource, self).__init__()
        self.mode = mode
        self.images = images
        self.target_dir = target_dir
        
    def run(self):
        if self.mode == 'text':
            for image in self.images:
                image.get_text()
                
        elif self.mode == 'img' and self.target_dir:                       
            for image in self.images:
                image.save_img(self.target_dir)
                
            

class GoogleImage(object):
    def __init__(self, image_element, browser):
        self.element = image_element
        self.page_url = None
        self.img_url = None
        self.text = None        
        self.__set_urls(browser)
    
    def __set_urls(self, browser):
        try:
            self.element.click()                    
            visit_pages = browser.find_elements_by_xpath("//span[contains(text(), 'Visit page')]")            
            
            for v in visit_pages:
                page_link_node = v.find_element_by_xpath('..')
             
                #check if current visit is opened after the image was clicked
                if page_link_node.get_attribute('tabindex') == '0':
                    self.page_url = urllib.parse.unquote(page_link_node.get_attribute('href'))
                    break

            visit_images = browser.find_elements_by_xpath("//span[contains(text(), 'View image')]")
            
            for im in visit_images:
                img_link_node = im.find_element_by_xpath('..')
                
                #check if current visit is opened after the image was clicked
                if img_link_node.get_attribute('tabindex') == '0':
                    self.img_url = urllib.parse.unquote(img_link_node.get_attribute('href'))
                    break
                    
        except Exception as e:
            pass
    
    
    def get_text(self):
        
        try:                                       
            url = urllib.parse.unquote(self.page_url)     
            #Monkey patch for JVM crash
            #See: https://github.com/misja/python-boilerpipe/issues/17
            if not jpype.isThreadAttachedToJVM():           
                jpype.attachThreadToJVM()

            ext = Extractor(extractor='DefaultExtractor', url=url)
            # soup = BeautifulSoup(content, 'lxml', from_encoding='utf-8')
            # text = self._visibile_text(soup)
            self.text = ext.getText()
               
        except Exception as e:
            pass
        
    def save_img(self, target):
        try:                
            # content = requests.get(url).content
            content = requests.get(self.img_url).content
            fname = self.img_url.rsplit("/", 1)[-1]
            
            if content and len(content) > 0:                
                with open(os.path.join(target, fname), 'wb') as f:
                    f.write(content)   
                    
        except Exception as e:
            pass
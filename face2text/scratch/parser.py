"""
Created on Jul 6, 2016

@author: brandon
"""

from ids import Object
from translate import translate
from selenium.webdriver.common.keys import Keys
#from boilerpipe.extract import Extractor
from selenium import webdriver
from subprocess import call
from selenium.common.exceptions import NoSuchElementException
from objects import get_description_from_json

import os
import time
import urllib2
import traceback
import sys
import pandas as pd

replace_text = False
headless = True
num_of_images = 10
enable_object_detection = False
enable_stock_photos = False

configuration = 'double_objects'

# path strings
folder_query_images = os.path.abspath('/home/brandbir/Documents/datasets/mscoco/val2014')

image_files_path = '/home/brandbir/Documents/bitbucket/msc/ImageDescriptor/out/object_detection/' + configuration + '.csv'
image_files = pd.read_csv(image_files_path)['image_name']

if enable_object_detection:
    folder_text_str = '../out/with_rcnn/visen' + configuration + '_' + str(num_of_images)

else:
    folder_text_str = '../out/without_rcnn/visen' + configuration + '_' + str(num_of_images)

if enable_stock_photos:
    folder_text_str += '_stock_photos/'
else:
    folder_text_str += '_no_stock_photos/'


def image_name(filename):
    """Returns the name of the image from the file name"""
    end_position = filename.find('.')
    return filename[0:end_position]


def empty_dir(dir_path):
    """Removed the contents of a directory"""
    file_list = os.listdir(dir_path)
    for file_name in file_list:
        os.remove(os.path.join(dir_path, file_name))

# Assigning the user agent string for PhantomJS
desired_cap = dict(webdriver.DesiredCapabilities.PHANTOMJS)
user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'
desired_cap['phantomjs.page.settings.userAgent'] = user_agent


def set_browser():
    """set PhantomJS or Firefox browser"""
    if headless:
        print 'opening PhantomJS'
        browser = webdriver.PhantomJS(desired_capabilities=desired_cap)

    else:
        print 'opening Firefox'
        browser = webdriver.Firefox()

    return browser


def translate_text_to_english(text):
    """translates a given text to english"""
    translated_text = ''

    # translating each word to english
    for word in text.split():
        if word != '':
            word = word.encode('utf-8')

        translated_text += translate(word, 'en') + ' '

    return translated_text.strip()


def upload_query_image(query_image_file_path, browser):
    """Uploads the query image to Google search by image service"""
    print 'opening google search by image web page'
    browser.get('https://images.google.com')

    print 'clicking on query-by-image icon'
    qbi = browser.find_element_by_id('qbi')
    qbi.click()

    print 'switch to upload an image tab'
    uit = browser.find_element_by_link_text('Upload an image')
    uit.click()

    current_url = browser.current_url
    qbfile = browser.find_element_by_id('qbfile')
    qbfile.send_keys(query_image_file_path)

    print 'uploading ' + query_image_file_path + '...'

    if 'mscoco' in folder_query_images:
        coco_val = 'COCO_val2014_'
        start_im_id = query_image_file_path.find(coco_val)
        end_im_id = query_image_file_path.find('.')
        im_id = int(query_image_file_path[start_im_id+len(coco_val)+1:end_im_id].lstrip('0'))
        objects_detected = get_description_from_json(im_id)
        print 'objects_detected: ' + objects_detected

    # waiting to upload image
    while current_url == browser.current_url:
        pass

    print query_image_file_path + ' is uploaded'

    # wait to find text in google search box
    input_text = ''
    keep_trying = True

    i = 0
    while input_text == '' and keep_trying:
        try:
            input_text = browser.find_element_by_id('lst-ib').get_attribute('value')
            i += 1
            if input_text != '' or i > 500:
                keep_trying = False
        except NoSuchElementException:
            pass

    print 'input_text: ' + input_text

    try:
        input_text = translate_text_to_english(input_text).encode('utf-8')

        # adding stock photos in google search datasets field
        browser.find_element_by_id('lst-ib').clear()
        input_text = input_text.encode('utf-8')

        if enable_object_detection:
            input_text = objects_detected

        if enable_stock_photos:
            input_text += ' stock photos'

        browser.find_element_by_id('lst-ib').send_keys(input_text)
        modified_input_text = browser.find_element_by_id('lst-ib').get_attribute('value')

        print 'modified text: ' + modified_input_text

        # pressing enter
        browser.find_element_by_id('lst-ib').send_keys(Keys.ENTER)
    except UnicodeDecodeError:
        print 'not adding stock photos in query'

    try:
        # locating the 'visually similar images' link
        visually_similar_link = browser.find_element_by_link_text('Visually similar images')
        return [visually_similar_link, input_text]

    except NoSuchElementException:
        return [0, input_text]


def visit_page(browser, image_count):
    """Visiting the webpage from where the image was retrieved from"""
    error = False

    visits = browser.find_elements_by_xpath("//span[contains(text(), 'Visit page')]")

    # looping through all the visits and check the one that is currently opened
    for v in visits:
        # go to the parent element
        page_link_node = v.find_element_by_xpath('..')

        # check if current visit is opened after the image was clicked
        if page_link_node.get_attribute('tabindex') == '0':
            # get corresponding page url
            page_link = page_link_node.get_attribute('href')
            print str(image_count) + ' - ' + page_link
            text = ''

            try:
                # extract text only from webpage
                extractor = Extractor(extractor='KeepEverythingExtractor', url=page_link)
                text = extractor.getText().encode('utf-8')

            except urllib2.HTTPError as error:
                print '    HTTP error ' + str(error.code)
                error = True

            except UnicodeDecodeError:
                print '    Unicode Decode error'
                error = True

            except Exception:
                print '    Page ignored: text was not parsed successfully'

            if not error:
                f = open(folder_text + '/' + str(image_count) + '.txt', 'w')
                f.write(text)
                f.close()
                image_count += 1

            break

    return image_count


def traverse_similar_images(browser, number_of_images):
    """visiting all the corresponding webpages of the similar related images"""
    similar_images = browser.find_elements_by_class_name('rg_i')
    images_found = len(similar_images)
    print 'found ' + str(images_found) + ' visually similar related images'

    # setting number of images in case few similar images were found
    if images_found < number_of_images:
        number_of_images = images_found

    print 'going to crawl text from ' + str(number_of_images) + ' images'
    image_count = 0

    # looping over the visually similar images
    for image in similar_images:
        if image_count < number_of_images:
            image.click()

            # visiting the corresponding web page and setting current image counter
            image_count = visit_page(browser, image_count)


def crawl_pages(browser, query_image_file_path, number_of_images):
    """Crawls websites of visually similar related images"""
    if has_text and not replace_text:
        print 'text was already fetched'

    else:
        if has_text and replace_text:
            print 'deleting current text'
            empty_dir(folder_text)
        elif not os.path.exists(folder_text):
            print 'creating ' + folder_text + ' folder'
            os.makedirs(folder_text)

        [visually_similar_link, keywords] = upload_query_image(query_image_file_path, browser)

        if visually_similar_link == 0:
            print 'No visually similar images were found'
            print 'Keywords: ' + keywords
            output_file = open(folder_text + '/' + 'out.txt', 'w')
            output_file.write(keywords)

        else:
            visually_similar_link.click()
            traverse_similar_images(browser, number_of_images)


start = time.time()
print 'Going to traverse images found in ' + folder_query_images + ' directory'

if os.path.exists(folder_query_images):
    total_images = str(len(image_files))
    print 'Images found: ' + total_images
    counter = 1

    # setting browser
    browser = set_browser()
    for image_file in image_files:
        print '\n' + str(counter) + ' of ' + total_images + ': crawling text for: ' + image_file
        image_path = os.path.join(folder_query_images, image_file)
        folder_text = folder_text_str + image_file
        has_text = os.path.exists(folder_text) and len(os.listdir(folder_text)) != 0

        try:
            crawl_pages(browser, image_path, num_of_images)
            counter += 1
        except Exception as err:
            print 'Unable to crawl websites for ' + image_path
            print 'Error: ' + str(err)
            print traceback.print_exc(file=sys.stdout)

    browser.close()

    # killing all phantomjs processes
    if headless:
        call(['killall', 'phantomjs'])

else:
    print folder_query_images + ' does not exist'

end = time.time()

print 'Execution in: ' + str(end - start)
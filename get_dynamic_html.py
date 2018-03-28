# coding=utf-8
from selenium import webdriver

fireFoxOptions = webdriver.FirefoxOptions()
# fireFoxOptions.set_headless()

def get_profile():
    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.dir', '/home/xudi/tmp/selenium_download')
    profile.set_preference('browser.download.folderList', 2)
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    return profile

profile = get_profile()
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/html')
brower_default = webdriver.Firefox(firefox_profile= profile,firefox_options=fireFoxOptions)

profile = get_profile()
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/msword')
brower_msword = webdriver.Firefox(firefox_profile= profile,firefox_options=fireFoxOptions)

profile = get_profile()
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/msword')
brower_msword2 = webdriver.Firefox(firefox_profile= profile,firefox_options=fireFoxOptions)

profile = get_profile()
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
brower_stream = webdriver.Firefox(firefox_profile= profile,firefox_options=fireFoxOptions)

profile = get_profile()
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/x-xls')
brower_xls = webdriver.Firefox(firefox_profile= profile,firefox_options=fireFoxOptions)

profile = get_profile()
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/pdf')
profile.set_preference("plugin.disable_full_page_plugin_for_types", "application/pdf")
profile.set_preference("pdfjs.disabled", True)
brower_pdf = webdriver.Firefox(firefox_profile= profile,firefox_options=fireFoxOptions)

brower_dict = {}
brower_dict['text/html'] = brower_default
brower_dict['text/msword'] = brower_msword2
brower_dict['application/msword'] = brower_msword
brower_dict['application/octet-stream'] = brower_stream
brower_dict['application/x-xls'] = brower_xls
brower_dict['application/pdf'] = brower_pdf


def get_js_html(url):
    r = brower_default.get(url)
    return brower_default.page_source.encode('utf-8')

def download_js(url,href_text,content_type):
    brower = brower_dict[content_type]
    brower.get(url)    
    button = brower.find_element_by_link_text(href_text)
    print button.get_attribute("href")
    button.click()
        
if __name__ == '__main__':
    html = get_js_html(url = r'http://beijing.pbc.gov.cn/beijing/132030/132052/132059/3057739/2016050511180799765.doc')
    print html
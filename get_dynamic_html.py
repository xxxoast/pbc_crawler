# coding=utf-8
from selenium import webdriver

fireFoxOptions = webdriver.FirefoxOptions()
fireFoxOptions.set_headless()

def get_profile():
    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.dir', '/home/xudi/tmp/selenium_download')
    profile.set_preference('browser.download.folderList', 2)
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference("plugin.disable_full_page_plugin_for_types", "application/pdf")
    profile.set_preference("pdfjs.disabled", True)
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 
                           "application/zip,text/plain,application/vnd.ms-excel,application/vnd.ms-word,text/csv,\
                           text/comma-separated-values,\
                           application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,\
                           application/vnd.openxmlformats-officedocument.wordprocessingml.document,\
                           application/msword,application/msexcel,\
                           application/octet-stream,\
                           application/x-xls,application/pdf,\
                           image/tiff,image/jpeg")
    return profile

profile = get_profile()
brower = webdriver.Firefox(firefox_profile= profile,firefox_options=fireFoxOptions)

def get_js_html(url):
    r = brower.get(url)
    return brower.page_source.encode('utf-8')

def download_js(url,href_text,content_type = None):
    brower.get(url)    
    button = brower.find_element_by_link_text(href_text)
    button.click()
        
if __name__ == '__main__':
    url = r'http://shanghai.pbc.gov.cn/fzhshanghai/113577/114832/114918/3008150/index.html'
    download_js(url, u'（第13期）行政处罚信息公示表.pdf', None)
    
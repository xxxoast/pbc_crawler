# coding=utf-8
from selenium import webdriver

fireFoxOptions = webdriver.FirefoxOptions()
fireFoxOptions.set_headless()

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
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
brower_pdf = webdriver.Firefox(firefox_profile= profile,firefox_options=fireFoxOptions)

profile = get_profile()
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')
brower_excel = webdriver.Firefox(firefox_profile= profile,firefox_options=fireFoxOptions)

def get_js_html(url):
    r = brower_default.get(url)
    return brower_default.page_source.encode('utf-8')

def download_js(url,href_text):
    if href_text.endswith('doc') or href_text.endswith('docx'):
        brower = brower_msword
    elif href_text.endswith('xls') or href_text.endswith('xlsx'):
        brower = brower_excel
    else:
        brower = brower_pdf
    r = brower.get(url)    
    button = brower.find_element_by_link_text(href_text)
    button.click()
        
if __name__ == '__main__':
    html = get_js_html(url = r'http://beijing.pbc.gov.cn/beijing/132030/132052/132059/3057739/2016050511180799765.doc')
    print html
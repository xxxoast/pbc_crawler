# coding=utf-8
from selenium import webdriver
from selenium.webdriver.common.by import By

fireFoxOptions = webdriver.FirefoxOptions()
fireFoxOptions.set_headless()
brower = webdriver.Firefox(firefox_options=fireFoxOptions)

def get_js_html(url):
    r = brower.get(url)
    return brower.page_source.encode('utf-8')
        
        
if __name__ == '__main__':
    html = get_js_html(url = r'http://www.pbc.gov.cn/rmyh/105226/105442/index.html')
    print html
import streamlit as st
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options

import random
import os
from urllib.parse import quote
import datetime
import time
import pandas as pd
import MeCab

tagger = MeCab.Tagger('-d ./mecab-ko-dic')

def separate_word(text):
    node = tagger.parseToNode(text)
    s = ""
    while node:
        s += f"{node.surface} "
        node = node.next
    return s.strip()

def get_driver(url, headless=True):
    if headless:
        options = Options()
        user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
              'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        ]
        user_agent = random.choice(user_agents)
        options.add_argument(f'--user-agent={user_agent}')
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")        
        driver = webdriver.Chrome('chromedriver', chrome_options=options)
    else:
        driver = webdriver.Chrome('chromedriver')
    driver.get(url)    
    return driver

def google_translate_driver():
    driver = get_driver("https://translate.google.co.jp/?hl=ja&sl=ko&tl=ja&op=translate")
    return driver

def google_translate(driver, ko_text):
    try: driver.find_element_by_id("tw-cst").click()
    except: pass    
    input_elem = driver.find_element_by_xpath("//span[@lang='ko']//textarea")
    input_elem.clear()
    input_elem.send_keys(ko_text)        
    
    time.sleep(2.0)
    if driver.find_element_by_xpath("//span[@lang='ja']").text == "翻訳":
        time.sleep(1.0)
    while driver.find_element_by_xpath("//span[@lang='ja']").text == "翻訳しています...":
        time.sleep(0.5)
        
    ja_text = driver.find_element_by_xpath("//span[@lang='ja']").text
    return ja_text.strip()

def markdown_table(ko_ja_texts):
    markdown = """
    | 韓国語 | 分割 | 日本語 | 
    | --- | --- | --- |
    """
    row_text = ""
    for ko_ja_text in ko_ja_texts:
        ko_text, ja_text = ko_ja_text
        if ko_text == "": continue
        row_text += f"|[{ko_text}](https://www.kpedia.jp/s/1/{ko_text})|{separate_word(ko_text)}|{ja_text}|\n"
    return markdown + row_text + "<br />"
        
st.set_page_config(page_title="韓日翻訳 -単語ごとに翻訳-", layout="wide")
st.title("韓日翻訳")

st.markdown("<h4>原文</h4>", unsafe_allow_html=True)
ko_text = st.text_area("", "처음 뵙겠습니다. 여기에 문장을 입력하세요.")

translation = st.button("翻訳する")
if not translation: st.stop()

st.markdown("<h4>文全体の翻訳</h4>", unsafe_allow_html=True)
with st.spinner():
    driver = google_translate_driver()
    translated_text = google_translate(driver, ko_text)
st.code(translated_text)

st.markdown("<h4>分かち書きごとの翻訳（Kpediaへのリンク付き）</h4>", unsafe_allow_html=True)
sentences = ".".join([t for t in ko_text.splitlines()]).split(".")
for sentence in sentences:
    if len(sentence) == 0: continue
    st.markdown(f"<li>{sentence}</li>", unsafe_allow_html=True)
    with st.spinner():
        ko_ja_texts = [[splitted, google_translate(driver, splitted)] for splitted in sentence.split(" ")]
    st.markdown(markdown_table(ko_ja_texts), unsafe_allow_html=True)

driver.close()
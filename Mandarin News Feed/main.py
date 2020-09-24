from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.utils import rgba
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.network.urlrequest import UrlRequest
from kivy.uix.popup import Popup
from kivy.config import Config
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.core.audio import SoundLoader

from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.bottomsheet import MDGridBottomSheet
from kivymd.uix.button import MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import ThreeLineListItem, OneLineListItem

from anki_deck_export import export_deck
from main_screen_str import helper_string

import jieba
import pinyin
from newspaper import Article
from cedict.pinyin import pinyinize
from hanziconv import HanziConv
from googletrans import Translator

import webbrowser
import xmltodict
import certifi
import os
import json
import urllib
import random

import asyncio
from aiohttp import ClientSession, ClientConnectionError
from aiogtts import aiogTTS, aiogTTSError

if platform == 'android':
    from jnius import autoclass

    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path


class MainScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass


class FavoriteScreen(Screen):
    pass


class NewsScreen(Screen):
    pass


class NewsReaderScreen(Screen):
    pass


class CustomWordPopup(Popup):
    pass


class NoTitleDialog(CustomWordPopup):
    pass


class NewsCard(MDCard):
    pass


class ChangeDefaultRSSFeedPopup(Popup):
    pass


class CustomPopup(Popup):
    pass


class WordCard(MDCard):
    pass


class CustomFontName(MDLabel):
    pass


store = JsonStore('app_config.json')


class MainApp(MDApp):

    def build(self):
        self.custom_app_font = store['font']['name']
        self.font_name_in_json = self.custom_app_font[0:14] + "..."  # for settings label
        if self.custom_app_font != 'DroidSansFallback.ttf':
            self.change_app_font(self.custom_app_font)

        if store['theme']['name'] == "Dark":
            self.theme_cls.theme_style = "Dark"
            self.restart_app_require = False
        else:
            self.restart_app_require = True

        Config.set('kivy', 'exit_on_escape', '0')
        Window.bind(on_keyboard=self.on_back_press)

        self.news_loaded = False
        self.hsk_level = store['hsk']['level']

        os.environ['SSL_CERT_FILE'] = certifi.where()

        self.news_data_array = []
        self.card_num_i = 1
        self.back_btn_press_count = 0

        self.news_reader_font_size = 24

        self.sm = Builder.load_string(helper_string)
        return self.sm

    def on_start(self):
        # word of the day to main screen
        if self.theme_cls.theme_style == "Dark":
            self.change_to_dark_mode()

        self.get_words()
        self.change_hsk_level_settings_text()

        if store['tts']['name'] == "Online":
            self.load_tts_online = True
            self.sm.ids.settings_screen_id.ids.settings_tts_switcher.active = True
        else:
            self.load_tts_online = False
            self.sm.ids.settings_screen_id.ids.settings_tts_switcher.active = False

    def on_back_press(self, window, key, *args):
        if key == 27:  # the esc key
            if self.sm.current == "main_screen":
                self.back_btn_press_count += 1

                if self.back_btn_press_count > 1:
                    MDApp.get_running_app().stop()
                else:
                    toast('Press again to exit')

            elif self.sm.current == "news_reader_screen":
                self.sm.current = "news_screen"
                self.back_btn_press_count = 0

            else:
                self.sm.current = "main_screen"
                self.back_btn_press_count = 0

    def quit_app(self, btn):
        MDApp.get_running_app().stop()

    def change_app_font(self, ft):
        # print(ft)
        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
            SD_CARD = primary_external_storage_path()
            font = os.path.join(SD_CARD, 'Mandarin News Feed', 'fonts', ft)
        else:
            font = os.path.join('Mandarin News Feed', 'fonts', ft)

        if not os.path.exists(font):
            font = 'DroidSansFallback.ttf'
            self.custom_app_font = font
            store.put('font', name=font)
        else:
            self.custom_app_font = font

    def callback_for_main_menu_items(self, *args):
        # toast(args[0])
        if args[0] == 'News':
            self.sm.current = "news_screen"
            self.sm.ids.news_screen_id.ids.news_loading_spinner.active = True
            self.change_rss_feed_topic()
        if args[0] == 'Favorite':
            self.sm.current = "favorite_screen"
            self.fav_screen_words()
        if args[0] == 'Settings':
            self.sm.current = "settings_screen"

    def show_main_grid_bottom_sheet(self):
        self.bottom_sheet_main_menu = MDGridBottomSheet()

        data = {
            "News": "newspaper",
            "Favorite": "heart",
            "Settings": "settings",
        }
        for item in data.items():
            self.bottom_sheet_main_menu.add_item(
                item[0],
                lambda x, y=item[0]: self.callback_for_main_menu_items(y),
                icon_src=item[1]
            )
        self.bottom_sheet_main_menu.open()

    def get_meaning_g_translate(self, word):
        """
        Function to translate chinese characters
        """
        toast('Translated word')

        self.custom_word_popup.ids.popup_ch_trad.text = HanziConv.toTraditional(word)
        self.custom_word_popup.ids.popup_ch_pin.text = pinyin.get(word)

        translator = Translator()
        t = translator.translate(word, src='zh-cn', dest="en")
        meaning = t.text
        self.custom_word_popup.ids.popup_ch_mean.text = str(meaning)

        if t != "" or t != "Loading...":
            self.custom_word_popup.ids.btn_save_word_to_news_list.disabled = False

    def show_word_dialog(self, word):
        """
        When a word clicked inside news reader screen then it will load words data [simplified, traditional, pinyin, meaning] from
        local directory 'Mandarin News Feed/saved_words_json' or 'Mandarin News Feed/words_json_data'. If not found in local directory
        then it will fetch from https://cdn.jsdelivr.net/gh/infinyte7/cedict-json/data/. If still not found then it will
        call get_meaning_g_translate().
        """
        word_json = word + '.json'

        self.custom_word_popup = CustomWordPopup()
        self.custom_word_popup = NoTitleDialog()

        if self.theme_cls.theme_style == "Light":
            self.custom_word_popup.background = ""

        self.custom_word_popup.ids.popup_ch_sim.text = word
        self.custom_word_popup.ids.popup_ch_mean.text = "Loading..."
        self.custom_word_popup.open()

        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
            SD_CARD = primary_external_storage_path()
            local_word_path = os.path.join(SD_CARD, 'Mandarin News Feed', 'words_json_data', word_json)
            save_word_path = os.path.join(SD_CARD, 'Mandarin News Feed', 'saved_words_json', word_json)
        else:
            local_word_path = os.path.join('Mandarin News Feed', 'words_json_data', word_json)
            save_word_path = os.path.join('Mandarin News Feed', 'saved_words_json', word_json)

        self.word_found_locally = False
        if os.path.exists(local_word_path):
            try:
                fp = open(local_word_path, 'r', encoding='utf-8')
                data = json.load(fp)
                self.word_found_locally = True
            except PermissionError:
                toast("File permission required.")
            except FileNotFoundError:
                toast("Word data not found.")

        elif os.path.exists(save_word_path):
            try:
                fp = open(save_word_path, 'r', encoding='utf-8')
                data = json.load(fp)
                self.word_found_locally = True
            except PermissionError:
                toast("File permission required.")
            except FileNotFoundError:
                toast("Word data not found.")
        else:
            self.word_found_locally = False
            toast('Not found locally, fetching online...')
            req = UrlRequest(
                url='https://cdn.jsdelivr.net/gh/infinyte7/cedict-json/data/' + urllib.parse.quote(word) + '.json',
                on_error=lambda *args: toast('Error occurred...'),  # print('error:', args),
                on_failure=lambda *args: self.get_meaning_g_translate(word),  # print('fail:', args),
                on_redirect=lambda *args: print('redir:', args),
                on_success=lambda *args: self.word_data(req.result, word))

        if self.word_found_locally:
            # print('word exist: ', data)
            self.custom_word_popup.ids.popup_ch_trad.text = str(data['traditional'])
            self.custom_word_popup.ids.popup_ch_pin.text = pinyinize(str(data['pinyin']))

            if isinstance(data['definitions'], list):
                data['definitions'] = ", ".join(data['definitions'])
            self.custom_word_popup.ids.popup_ch_mean.text = data['definitions']

            self.custom_word_popup.ids.btn_save_word_to_news_list.disabled = False

    def word_data(self, result, word):
        self.custom_word_popup.ids.popup_ch_trad.text = str(result['traditional'])
        self.custom_word_popup.ids.popup_ch_pin.text = pinyinize(str(result['pinyin']))

        if isinstance(result['definitions'], list):
            result['definitions'] = ", ".join(result['definitions'])
        self.custom_word_popup.ids.popup_ch_mean.text = result['definitions']

        self.custom_word_popup.ids.btn_save_word_to_news_list.disabled = False

    def print_news(self, result):
        """
        It print google rss feed headlines
        """
        # print('News Data')
        # print(result)

        self.sm.ids.news_screen_id.ids.news_loading_spinner.active = False
        self.sm.ids.news_screen_id.ids.news_loading_spinner.size = [dp(0), dp(0)]

        # if not self.news_loaded:
        d = xmltodict.parse(result, encoding='utf-8')
        try:
            self.headlines = d['rss']['channel']['item']

            for h in self.headlines:
                # print(h)
                # print(h['title'])
                # print(h['link'])
                # print(h['source']['@url'])
                # print(h['pubDate'])

                data = [h['link'], h['source']['@url'], h['pubDate']]
                self.news_data_array.append(data)

                card = NewsCard()
                card.ids.news_card_num.text: str = str(self.card_num_i)
                card.ids.news_card_link.text = h['source']['@url']

                card.bind(on_touch_down=self.news_card_clicked)

                if len(h['title']) > 25:
                    h['title'] = h['title'][0:20]
                    h['title'] = h['title'] + " ..."

                card.ids.news_card_title.text = h['title']
                card.ids.news_card_time.text = h['pubDate']

                if self.theme_cls.theme_style == "Dark":
                    card.ids.news_card_title.text_color = rgba('ffffff')
                    card.ids.news_card_time.text_color = rgba('9c9c9c')
                    card.ids.news_card_link.text_color = rgba('8b8b8b')

                self.card_num_i = self.card_num_i + 1
                self.sm.ids.news_screen_id.ids.news_box_layout.add_widget(card)
        except:
            toast('Error occurred... Try again')

    def get_news(self, topic, search_by_query):
        """
        Get news from google rss feed by topic and search query
        """
        # 'https://news.google.com/rss/news/headlines/section/topic/TECHNOLOGY?hl=zh-CN&gl=CN&ceid=CN:zh-Hans'
        topic_list = ['WORLD', 'BUSINESS', 'TECHNOLOGY', 'MOVIES', 'SPORTS', 'SCIENCE', 'ENTERTAINMENT']

        base_url = 'https://news.google.com/rss/news/headlines/section/topic/'
        suffix_url = '?hl=zh-CN&gl=CN&ceid=CN:zh-Hans'

        search_url = 'https://news.google.com/rss/search?hl=zh-CN&pz=1&q=' + topic.lower() + '&gl=CN&ceid=CN:zh-Hans'

        try:

            if search_by_query:
                url = search_url

            else:
                topic = topic.upper()
                if topic == 'DEFAULT':
                    url = 'https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans'

                elif topic in topic_list:
                    import requests
                    url = base_url + topic + suffix_url
                    url = requests.head(url, allow_redirects=True).url

                else:
                    url = search_url

            req = UrlRequest(
                url=url,
                on_error=lambda *args: toast('Error Occurred... Check Internet connection.'),    # print('error:', args),
                on_failure=lambda *args: print('fail:', args),
                on_redirect=lambda *args: print('redir:', args),
                on_success=lambda *args: self.print_news(req.result)  # print('success:', args)
            )
        # req.wait(0.5)
        except:
            toast('Error occurred. Try again')

    def word_clicked(self, label, touch_word):
        """
        Open popup with characters, pinyin and meaning for the touched word inside news reader screen
        """
        # print('value: ', touch_word)
        self.show_word_dialog(touch_word)
        self.word = touch_word

    def news_card_clicked(self, card, touch):
        """
        Open news reader screen
        """
        if card.collide_point(*touch.pos):
            # print('clicked on', card.children[2].children[1].text)

            card_num = int(card.children[2].children[1].text) - 1  # card number started with 1, but index start with 0
            # print(self.headlines[card_num]['link'])

            # print(self.news_data_array[card_num])

            self.news_card_url = self.news_data_array[card_num][0]
            self.news_card_src_url = self.news_data_array[card_num][1]
            self.news_card_pub_date = self.news_data_array[card_num][2]

            self.sm.current = 'news_reader_screen'
            scroll = ScrollView()

            self.confirm_extract_dialog = CustomPopup(title="Click OK and wait to load",
                                                      size_hint=(0.9, 0.4), content=scroll)

            grid = GridLayout(cols=1, size_hint=(1, 1))
            scroll.add_widget(grid)
            grid.bind(minimum_height=grid.setter('height'))

            lable_title = MDLabel(text=card.children[1].text)
            lable_title.font_name = self.custom_app_font
            lable_title.halign = 'center'
            lable_title.size_hint_y = 1
            lable_title.font_size = '24sp'

            label_url = MDLabel(text=self.news_card_src_url)

            btn_confirm = MDFlatButton(text="OK")
            btn_confirm.size_hint_x = 1
            # btn_confirm.bind(on_press=self.extract_article)
            btn_confirm.bind(on_press=self.load_article)

            grid.add_widget(label_url)
            grid.add_widget(lable_title)
            grid.add_widget(btn_confirm)

            if self.theme_cls.theme_style == "Light":
                self.confirm_extract_dialog.background = ""
            else:
                lable_title.theme_text_color = "Custom"
                lable_title.text_color = rgba('ffffff')

                label_url.theme_text_color = "Custom"
                label_url.text_color = rgba('ffffff')
            self.confirm_extract_dialog.open()

    # https://github.com/aio-libs/aiohttp/issues/3390#issuecomment-440641365

    def load_article(self, btn):
        """
        Load news article for the selected card, first resolve the redirected link then open the original source link
        kivy using UrlRequest
        """
        url = self.news_card_url

        async def fetch(url):
            async with ClientSession() as session:
                async with session.get(url, allow_redirects=True,
                                       headers={'User-Agent': 'python-requests/2.20.0'}) as response:
                    # print('url: ', response.url)
                    # print('status: ', response.status)
                    # print('history: ', response.history)

                    req = UrlRequest(
                        url=str(response.url),
                        on_error=lambda *args: print('error:', args),
                        on_failure=lambda *args: print('fail:', args),
                        on_redirect=lambda *args: print('redir:', args),
                        on_success=lambda *args: self.extract_article(req.result, url)
                        # print('success:', args)
                    )

        self.confirm_extract_dialog.dismiss()
        try:
            asyncio.get_event_loop().run_until_complete(fetch(url))
        except ClientConnectionError:
            toast('Connection Error')

    # https://stackoverflow.com/questions/56677636/how-to-use-newspaper3k-library-without-downloading-articles

    def extract_article(self, result, url):
        """
        News article saved to news.html file and then using 'newspaper3k' it get parsed. Also using 'jieba' the article text
        split into words and kivy ref markup applied. So when any word click then popup will open.
        """
        try:
            self.open_in_browser_url = url
            article = Article(url, language="zh")
            with open('news.html', 'w', encoding='utf-8') as f:
                f.write(str(result))

            with open('news.html', 'r', encoding='utf-8') as fh:
                article.html = fh.read()

            article.download_state = 2
            article.parse()

            article_seg_list = jieba.cut(article.text)
            self.article_text_for_tts = article.title + article.text
            ref_news_article = ""
            for s in article_seg_list:
                ref_news_article += "[ref=" + s + "]" + s + "[/ref]"
            # print(ref_news)
            # print('\n')
            # print(t.text)

            title_seg_list = jieba.cut(article.title)
            ref_news_title = ""
            for ts in title_seg_list:
                ref_news_title += "[ref=" + ts + "]" + ts + "[/ref]"

            if self.theme_cls.theme_style == "Dark":
                self.sm.ids.news_screen_reader_id.ids.news_reader_time.text_color = rgba('9c9c9c')
                self.sm.ids.news_screen_reader_id.ids.news_screen_reader_url.text_color = rgba('8b8b8b')
                self.sm.ids.news_screen_reader_id.ids.news_reader_header.text_color = rgba('ffffff')
                self.sm.ids.news_screen_reader_id.ids.news_reader_article.text_color = rgba('ffffff')
                self.sm.ids.news_screen_reader_id.ids.news_reader_authors.text_color = rgba('ffffff')

            self.sm.ids.news_screen_reader_id.ids.news_reader_loading_spinner.active = False
            self.sm.ids.news_screen_reader_id.ids.news_reader_loading_spinner.size = [dp(0), dp(0)]

            self.sm.ids.news_screen_reader_id.ids.news_reader_time.text = self.news_card_pub_date
            self.sm.ids.news_screen_reader_id.ids.news_screen_reader_url.text = self.news_card_src_url

            self.sm.ids.news_screen_reader_id.ids.news_reader_header.text = ref_news_title
            self.sm.ids.news_screen_reader_id.ids.news_reader_article.text = ref_news_article
            self.sm.ids.news_screen_reader_id.ids.news_reader_authors.text = str(article.authors)

            self.sm.ids.news_screen_reader_id.ids.news_reader_header.bind(on_ref_press=self.word_clicked)
            self.sm.ids.news_screen_reader_id.ids.news_reader_article.bind(on_ref_press=self.word_clicked)

        except:
            toast('Error occurred... Try again')

    def open_in_browser(self):
        """
        Open current link in opened in news reader screen to default browser
        """
        webbrowser.open(self.open_in_browser_url)

    def go_to_news_screen(self):
        self.sm.current = "news_screen"

    def go_to_main_screen(self):
        self.sm.current = "main_screen"

    def get_words(self):
        """
        Fetch hsk word lists from app directory and display at main screen. The word get change for every new start of app
        """
        # print(store['hsk']['level'])
        level = store['hsk']['level']
        file_name = 'hsk/hsk' + str(level) + '.txt'

        f = open(file_name, encoding='utf-8')
        lines = f.readlines()

        random_word = random.choice(lines)
        random_word = random_word.split("\t")

        # print(random_word[0], random_word[1], random_word[2], random_word[3], random_word[4])

        self.sm.ids.main_screen_id.ids.main_screen_ch_sim.text = random_word[0]
        self.sm.ids.main_screen_id.ids.main_screen_ch_trad.text = random_word[1]
        self.sm.ids.main_screen_id.ids.main_screen_ch_pin.text = pinyinize(random_word[3])
        self.sm.ids.main_screen_id.ids.main_screen_ch_mean.text = random_word[4]

    def save_words_to_file(self, s):
        """
        Save words to local directory for offline viewing while reading news.
        """
        # print('save to db ', s)

        if s == 'main':
            # save word from main screen
            ch_sim = self.sm.ids.main_screen_id.ids.main_screen_ch_sim.text
            ch_trad = self.sm.ids.main_screen_id.ids.main_screen_ch_trad.text
            ch_pin = self.sm.ids.main_screen_id.ids.main_screen_ch_pin.text
            ch_mean = str(self.sm.ids.main_screen_id.ids.main_screen_ch_mean.text).rstrip()

            data = ch_sim + "\t" + ch_trad + "\t" + ch_pin + "\t" + ch_mean + "\n"
            self.write_word_to_file('daily_words_data.txt', data, ch_sim)

        elif s == 'reader':
            # save word from news reader screen
            ch_sim = self.custom_word_popup.ids.popup_ch_sim.text
            ch_trad = self.custom_word_popup.ids.popup_ch_trad.text
            ch_pin = self.custom_word_popup.ids.popup_ch_pin.text
            ch_mean = self.custom_word_popup.ids.popup_ch_mean.text

            data = ch_sim + "\t" + ch_trad + "\t" + ch_pin + "\t" + ch_mean + "\n"
            self.write_word_to_file('news_words_data.txt', data, ch_sim)

            if not self.word_found_locally:
                new_word_json = {
                    "definitions": ch_mean,
                    "pinyin": ch_pin,
                    "simplified": ch_sim,
                    "traditional": ch_trad
                }

                if platform == 'android':
                    request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
                    SD_CARD = primary_external_storage_path()
                    new_word_path = os.path.join(SD_CARD, 'Mandarin News Feed', 'saved_words_json')
                else:
                    new_word_path = os.path.join('Mandarin News Feed', 'saved_words_json')

                if not os.path.exists(new_word_path):
                    os.makedirs(new_word_path)

                fn = ch_sim + ".json"
                fp = os.path.join(new_word_path, fn)
                fout = open(fp, 'w', encoding='utf-8')
                json.dump(new_word_json, fout, indent=4, ensure_ascii=False)


    def write_word_to_file(self, fname, data, ch_sim):
        """
        Write the words to 'news_words_data.txt' or 'daily_words_data.txt'
        """
        # print('write to ', fname)
        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
            SD_CARD = primary_external_storage_path()
            wordslist_path = os.path.join(SD_CARD, 'Mandarin News Feed', 'wordslist')
        else:
            wordslist_path = os.path.join('Mandarin News Feed', 'wordslist')

        if not os.path.exists(wordslist_path):
            os.makedirs(wordslist_path)
        else:
            wordslist_file = fname
            fp = os.path.join(wordslist_path, wordslist_file)
            if not os.path.exists(fp):
                open(fp, 'w', encoding='utf-8')

            found = False
            with open(fp, 'r+', encoding='utf-8') as fn:
                lines = fn.readlines()
                for l in lines:
                    if ch_sim in l:
                        toast('Already saved the word')
                        found = True
                        break
                if not found:
                    fn.write(data)
                    toast('Saved to ' + fname)

    def text_to_speech(self, text):
        """
        Text to speech offline and online.
        Offline: using android tts engine, for windows not implemented
        Online: using gtts
        """
        if platform == "android":
            Locale = autoclass('java.util.Locale')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
            MediaPlayer = autoclass("android.media.MediaPlayer")

        # print('tts: ', text)
        if store['tts']['name'] == "Online":
            self.load_tts_online = True
        else:
            self.load_tts_online = False

        if not self.load_tts_online:
            if platform == 'android':
                # stop if tts speaking
                self.stop_tts()

                self.android_tts = TextToSpeech(PythonActivity.mActivity, None)
                # Putting these lines below, make tts work
                print("ch_trad: ", self.android_tts.setLanguage(Locale.TRADITIONAL_CHINESE))
                print("ch_sim: ", self.android_tts.setLanguage(Locale.SIMPLIFIED_CHINESE))
                print("ch: ", self.android_tts.setLanguage(Locale.CHINESE))
                # self.android_tts.setLanguage(Locale.SIMPLIFIED_CHINESE)
                self.android_tts.speak(text, TextToSpeech.QUEUE_FLUSH, None)

            else:
                toast('Not implemented')

        elif self.load_tts_online:
            if platform == 'android':
                request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
                SD_CARD = primary_external_storage_path()
                audio_path = os.path.join(SD_CARD, 'Mandarin News Feed', 'saved_audio')
            else:
                audio_path = os.path.join('Mandarin News Feed', 'saved_audio')

            if not os.path.exists(audio_path):
                os.makedirs(audio_path)

            if len(text) >= 10:
                text = text[:10]
            tts_file = "cmn-" + text + ".mp3"
            tts_file = os.path.join(audio_path, tts_file)
            aiogtts = aiogTTS()

            # function to save audio asynchronously
            async def play_audio():
                await aiogtts.save(text, tts_file, lang='zh-cn')
                if platform == "android":
                    mp = MediaPlayer()
                    mp.setDataSource(tts_file)
                    mp.prepare()
                    mp.start()
                else:
                    sound = SoundLoader.load(filename=tts_file)
                    sound.play()

            if not os.path.exists(tts_file):
                try:
                    asyncio.get_event_loop().run_until_complete(play_audio())
                except ClientConnectionError:
                    toast('Connection error')
                except FileNotFoundError:
                    toast('Audio file not found')
                except aiogTTSError:
                    toast('Failed to load. Check internet connection and try again')
            else:
                if platform == "android":
                    mp = MediaPlayer()
                    mp.setDataSource(tts_file)
                    mp.prepare()
                    mp.start()
                else:
                    sound = SoundLoader.load(filename=tts_file)
                    sound.play()
        else:
            toast('Change settings to use system text to speech engine')

    def stop_tts(self):
        """
        Stop current playing tts
        """
        if platform == "android":
            try:
                if self.android_tts != None:
                    self.android_tts.stop()
            except AttributeError:
                    print('tts not instantiated')

    def on_change_tts_settings(self, checkbox, value):
        # print(value)
        if value:
            store.put('tts', name='Online')
        else:
            store.put('tts', name='Offline')

    def change_to_dark_mode(self):
        self.sm.ids.main_screen_id.ids.main_screen_top_toolbar.md_bg_color = rgba('424242')
        self.sm.ids.main_screen_id.ids.main_screen_bottom_toolbar.md_bg_color = rgba('424242')

        self.sm.ids.settings_screen_id.ids.settings_screen_top_toolbar.md_bg_color = rgba('424242')
        self.sm.ids.settings_screen_id.ids.settings_screen_bottom_toolbar.md_bg_color = rgba('424242')

        self.sm.ids.settings_screen_id.ids.label_settings_night_theme.text_color = rgba('ffffff')
        self.sm.ids.settings_screen_id.ids.label_settings_hsk_level.text_color = rgba('ffffff')
        self.sm.ids.settings_screen_id.ids.label_settings_current_font.text_color = rgba('ffffff')
        self.sm.ids.settings_screen_id.ids.label_settings_tts.text_color = rgba('ffffff')

        self.sm.ids.settings_screen_id.ids.theme_switcher.active = True
        self.sm.ids.settings_screen_id.ids.theme_switcher.thumb_color = rgba('a6a6a6')
        self.sm.ids.settings_screen_id.ids.theme_switcher.thumb_color_down = rgba('a6a6a6')

        self.sm.ids.fav_screen_id.ids.favorite_screen_top_toolbar.md_bg_color = rgba('424242')
        self.sm.ids.fav_screen_id.ids.favorite_screen_bottom_toolbar.md_bg_color = rgba('424242')

        self.sm.ids.news_screen_id.ids.news_screen_top_toolbar.md_bg_color = rgba('424242')
        self.sm.ids.news_screen_id.ids.news_screen_bottom_toolbar.md_bg_color = rgba('424242')

        self.sm.ids.news_screen_reader_id.ids.news_reader_top_toolbar.md_bg_color = rgba('424242')
        self.sm.ids.news_screen_reader_id.ids.news_reader_bottom_toolbar.md_bg_color = rgba('424242')

        self.sm.ids.main_screen_id.ids.main_screen_ch_pin.text_color = rgba('ffffff')

    def on_theme_checkbox_active(self, checkbox, value):
        if value:
            store.put('theme', name='Dark')
            # print(store['theme']['name'])

        else:
            store.put('theme', name="Light")
            # print(store['theme']['name'])

        if self.restart_app_require:
            toast('Restart the app to view the changes')
        self.restart_app_require = True

    def change_hsk_level(self):
        """
        Change level of word displayed at main screen
        """
        self.hsk_level += 1
        if self.hsk_level == 1:
            ic = 'numeric-1'
            store.put('hsk', level=1)

        if self.hsk_level == 2:
            ic = 'numeric-2'
            store.put('hsk', level=2)

        if self.hsk_level == 3:
            ic = 'numeric-3'
            store.put('hsk', level=3)

        if self.hsk_level == 4:
            ic = 'numeric-4'
            store.put('hsk', level=4)

        if self.hsk_level == 5:
            ic = 'numeric-5'
            store.put('hsk', level=5)

        if self.hsk_level == 6:
            ic = 'numeric-6'
            store.put('hsk', level=6)

        if self.hsk_level > 6:
            ic = 'numeric-1'
            self.hsk_level = 1
            store.put('hsk', level=1)

        self.sm.ids.settings_screen_id.ids.hsk_level_t_button.icon = ic

    def change_hsk_level_settings_text(self):
        l = store['hsk']['level']
        if l == 1:
            ic = 'numeric-1'
        if l == 2:
            ic = 'numeric-2'
        if l == 3:
            ic = 'numeric-3'
        if l == 4:
            ic = 'numeric-4'
        if l == 5:
            ic = 'numeric-5'
        if l == 6:
            ic = 'numeric-6'
        self.sm.ids.settings_screen_id.ids.hsk_level_t_button.icon = ic

    def on_get_feed_by_query(self, checkbox, value):
        if value:
            self.rss_popup.ids.tf_rss_feed_popup.hint_text = 'Enter query'
        else:
            self.rss_popup.ids.tf_rss_feed_popup.hint_text = 'Enter topic'

    def change_rss_feed_topic(self):
        self.rss_popup = ChangeDefaultRSSFeedPopup()
        if self.theme_cls.theme_style == "Light":
            self.rss_popup.background = ""
        else:
            self.rss_popup.ids.label_rss_popup_get_feed.text_color = rgba('ffffff')
            self.rss_popup.ids.label_rss_popup_wait_feed.text_color = rgba('ffffff')
        self.rss_popup.open()

    def ok_button_rss_feed(self):
        self.rss_popup.dismiss()
        # print(self.rss_popup.ids.tf_rss_feed_popup.text)
        topic = self.rss_popup.ids.tf_rss_feed_popup.text

        search_by_query = False
        if self.rss_popup.ids.checkbox_rss_popup_get_feed.active:
            search_by_query = True

        if topic == "":
            topic = 'all'
            self.get_news('default', search_by_query)
        else:
            self.get_news(topic, search_by_query)

        btn_as_label = MDFlatButton(text=topic)
        btn_as_label.disabled = True
        btn_as_label.theme_text_color = "Custom"
        btn_as_label.text_color = rgba('f44336')
        self.sm.ids.news_screen_id.ids.news_box_layout.add_widget(btn_as_label)
        toast('Loading...')

    def close_button_rss_feed(self):
        if self.rss_popup:
            self.rss_popup.dismiss()
            if len(self.news_data_array) == 0:
                # self.get_news('default', False)
                self.sm.ids.news_screen_id.ids.news_loading_spinner.active = False
                # toast('Loading...')

    def view_app_license(self):
        scroll = ScrollView()
        popup = CustomPopup(size_hint=(0.9, 0.8), content=scroll)

        grid = GridLayout(cols=1, size_hint=(1, None))
        scroll.add_widget(grid)
        grid.bind(minimum_height=grid.setter('height'))

        with open('app_license.json') as f:
            li = json.load(f)

        lic_len = len(li)
        for i in range(0, lic_len):
            lic_list = ThreeLineListItem()
            lic_list.text = li[i]['Name']
            lic_list.secondary_text = li[i]['License']
            lic_list.tertiary_text = li[i]['Author'] + " : " + li[i]['Source']
            lic_list.bind(on_touch_down=self.on_license_list_click)
            grid.add_widget(lic_list)
        if self.theme_cls.theme_style == "Light":
            popup.background = ""
        popup.open()

    def on_license_list_click(self, list, touch):
        if list.collide_point(*touch.pos):
            # print(list.tertiary_text)
            t = list.tertiary_text
            t2 = " : "
            url = t.split(t2, 1)[1]
            # print(url)
            webbrowser.open(url)

    def on_about_app(self):
        scroll = ScrollView()
        popup = CustomPopup(title="", size_hint=(0.9, 0.5), content=scroll)

        grid = GridLayout(cols=1, size_hint=(1, None))
        scroll.add_widget(grid)
        grid.bind(minimum_height=grid.setter('height'))

        lb_name = MDLabel(text="Mandarin News Feed", halign='center',
                          theme_text_color='Custom', text_color=rgba('6495ed'))
        lb_ver = MDLabel(text="Version 1.0.0", halign='center', theme_text_color='Custom', text_color=rgba('fb8c00'))
        grid.add_widget(lb_name)
        grid.add_widget(lb_ver)

        if self.theme_cls.theme_style == "Light":
            popup.background = ""

        popup.open()

    def fav_screen_words(self):
        self.view_word_dialog = MDDialog(
            text="Select word list to view",
            size_hint=[0.9, None],
            auto_dismiss=False,
            buttons=[
                MDFlatButton(
                    text="Daily Words", text_color=self.theme_cls.primary_color,
                    on_press=self.view_word_list
                ),
                MDFlatButton(
                    text="News Words", text_color=self.theme_cls.primary_color,
                    on_press=self.view_word_list
                ),
            ],
        )
        self.view_word_dialog.open()

    def view_word_list(self, btn):
        self.view_word_dialog.dismiss()
        # print(btn.text)
        self.view_fav_words_btn_selected = btn.text

        fname = ''
        if btn.text == 'Daily Words':
            fname = 'daily_words_data.txt'
            self.sm.ids.fav_screen_id.ids.favorite_screen_top_toolbar.title = 'Daily Words'
        elif btn.text == 'News Words':
            fname = 'news_words_data.txt'
            self.sm.ids.fav_screen_id.ids.favorite_screen_top_toolbar.title = 'News Words'

        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
            SD_CARD = primary_external_storage_path()
            wordslist = os.path.join(SD_CARD, 'Mandarin News Feed', 'wordslist', fname)
        else:
            wordslist = os.path.join('Mandarin News Feed', 'wordslist', fname)

        if not os.path.exists(wordslist):
            toast('Add some words to view...')
        else:
            if len(self.sm.ids.fav_screen_id.ids.fav_words_box_layout.children) > 0:
                self.sm.ids.fav_screen_id.ids.fav_words_box_layout.clear_widgets()

            with open(wordslist, 'r', encoding='utf-8') as f:
                lines = f.readlines()

                for l in lines:
                    l = l.split('\t')

                    word_card = WordCard()

                    word_card.ids.word_card_ch_sim.text = l[0]
                    word_card.ids.word_card_ch_trad.text = l[1]
                    word_card.ids.word_card_ch_pin.text = l[2]
                    word_card.ids.word_card_ch_mean.text = l[3]

                    self.sm.ids.fav_screen_id.ids.fav_words_box_layout.add_widget(word_card)

    def fav_word_card_click(self, card, touch):
        if card.collide_point(*touch.pos):
            # print('clicked on', card.children[3].text)
            self.text_to_speech(card.children[3].text)

    def export_as_anki_deck(self):
        # print('export anki deck')
        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
            SD_CARD = primary_external_storage_path()
            fpath = os.path.join(SD_CARD, 'Mandarin News Feed', 'Export')
        else:
            fpath = os.path.join('Mandarin News Feed', 'Export')

        if not os.path.exists(fpath):
            os.makedirs(fpath)

        fname = ""
        if self.view_fav_words_btn_selected == "Daily Words":
            fname = 'daily_words_data.txt'
        elif self.view_fav_words_btn_selected == "News Words":
            fname = 'news_words_data.txt'

        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
            SD_CARD = primary_external_storage_path()
            fname = os.path.join(SD_CARD, 'Mandarin News Feed', 'wordslist', fname)
        else:
            fname = os.path.join('Mandarin News Feed', 'wordslist', fname)

        export_deck(fpath, fname)

    def change_font_list_view(self):
        """
        Fonts can be changed by putting news fonts to 'Mandarin News Feed/fonts' folder
        """
        # print('clicked')
        scroll = ScrollView()
        lang_dialog = CustomPopup(title='Select font', size_hint=[0.9, 0.9], content=scroll)

        grid = GridLayout(cols=1, size_hint=(1, None))
        scroll.add_widget(grid)
        grid.bind(minimum_height=grid.setter('height'))

        if platform == 'android':
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])
            SD_CARD = primary_external_storage_path()
            fpath = os.path.join(SD_CARD, 'Mandarin News Feed', 'fonts')

        else:
            fpath = os.path.join('Mandarin News Feed', 'fonts')

        try:
            fonts = os.listdir(fpath)
            fonts_in_dir = False
            for i in fonts:
                if i.endswith(".ttf") or i.endswith(".otf") or i.endswith(".OTF") or i.endswith(".TTF"):
                    lb = OneLineListItem(text=i, size_hint_x=1, on_press=lambda btn: font_clicked(btn))
                    grid.add_widget(lb)

            if len(fonts) > 0:
                fonts_in_dir = True

        except FileNotFoundError:
            # print("file / folder not found")
            os.makedirs(fpath)
            fonts_in_dir = False

        if self.theme_cls.theme_style == "Light":
            lang_dialog.background = ""

        if fonts_in_dir:
            lang_dialog.open()
        else:
            toast("Download chinese fonts and put it in 'Mandarin News Feed/fonts' folder")

        def font_clicked(btn):
            # print(btn.text)
            store.put('font', name=btn.text)
            lang_dialog.dismiss()
            toast('Font applied. Restart app to view changes')

            self.sm.ids.settings_screen_id.ids.settings_current_font_name.text = btn.text

    def change_news_reader_font_size(self, text):
        factor = 4
        if text == 'increase':
            self.news_reader_font_size += factor
            if self.news_reader_font_size <= 80:
                self.sm.ids.news_screen_reader_id.ids.news_reader_article.font_size = str(
                    self.news_reader_font_size) + "sp"
            else:
                self.news_reader_font_size = 80
        elif text == 'decrease':
            self.news_reader_font_size -= factor
            if self.news_reader_font_size >= 10:
                self.sm.ids.news_screen_reader_id.ids.news_reader_article.font_size = str(
                    self.news_reader_font_size) + "sp"
            else:
                self.news_reader_font_size = 10
        else:
            self.sm.ids.news_screen_reader_id.ids.news_reader_article.font_size = str(26) + "sp"


if __name__ == '__main__':
    MainApp().run()

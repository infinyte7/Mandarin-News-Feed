helper_string = """
<MenuButton@MDIconButton>:
    icon: "menu"
    theme_text_color: "Custom"
    text_color: 1,0,0,1
    halign: 'bottom'  
    on_press: app.show_main_grid_bottom_sheet()

<TButton@MDIconButton>:
    icon: "menu"
    theme_text_color: "Custom"
    text_color: 1,0,0,1
    halign: 'center'  
    
<TitleText@MDLabel>
    pos_hint: {"center_y": .95}
    halign: "center"
    theme_text_color: "Custom"
    text_color: 0, 0, 1, 1
    font_style: "Subtitle1"

<WordMeaningDialog@MDDialog>
    id: word_meaning_dialog

ScreenManager:
    id: screen_manager
    MainScreen:
        id: main_screen_id
    SettingsScreen:
        id: settings_screen_id
    FavoriteScreen:
        id: fav_screen_id
    NewsScreen:
        id: news_screen_id
    NewsReaderScreen:
        id: news_screen_reader_id

<MainScreen>:
    name: 'main_screen'
    BoxLayout:
        orientation: "vertical"
        spacing: "5dp"
            
        MDToolbar:
            id: main_screen_top_toolbar
            title: "Mandarin News Feed"
            elevation: 5
            pos_hint: {'top': 1}
                            
        ScrollView:              
            MDBoxLayout:
                orientation: 'vertical'
                adaptive_height: True
                padding: dp(28)
                spacing: dp(15)
                
                MDCard:
                    ripple_behavior: True
                    size_hint: 1, None
                    size: "200dp", "300dp"
                    orientation: "vertical"
                    padding: "8dp"
                    spacing: "8dp"
                    
                    MDLabel:
                        text: "Daily Words"
                        theme_text_color: "Secondary"
                        size_hint_y: None
                        height: self.texture_size[1]
            
                    MDSeparator:
                        height: "1dp"
            
                    MDLabel:
                        id: main_screen_ch_sim
                        font_size: '38sp'
                        font_name: app.custom_app_font
                        halign: 'center'
                        theme_text_color: "Custom"
                        text_color: rgba('6495ed')
                    
                    MDLabel:
                        id: main_screen_ch_pin
                        font_size: '16sp'
                        font_name: app.custom_app_font
                        halign: 'center'
                        size_hint_y: 0.4
                        theme_text_color: "Custom"
                        text_color: rgba('5f5f5f')
                        
                    MDLabel:
                        id: main_screen_ch_trad
                        font_size: '30sp'
                        font_name: app.custom_app_font
                        halign: 'center'
                        theme_text_color: "Custom"
                        text_color: rgba('27b46e')
                                         
                    MDLabel:
                        id: main_screen_ch_mean
                        font_name: app.custom_app_font
                        halign: 'center'
                        theme_text_color: "Custom"
                        text_color: rgba('fb8c00')
                        font_size: '22sp'
                    
                    MDBoxLayout:
                        orientation: 'horizontal'
                        size_hint: 1, 0.8
                        
                        MDIconButton:
                            size_hint_x: 0.33
                            icon: 'volume-high'
                            on_press: app.text_to_speech(main_screen_ch_sim.text)
                            theme_text_color: "Custom"
                            text_color: rgba('2196f3')
                        
                        MDIconButton:
                            size_hint_x: 0.33
                            icon: 'heart'
                            on_press: app.save_words_to_file('main')
                            theme_text_color: "Custom"
                            text_color: rgba('ea2322')
                            
                        MDIconButton:
                            size_hint_x: 0.33
                            icon: 'refresh'
                            on_press: app.get_words()
                            theme_text_color: "Custom"
                            text_color: rgba('4caf50')
                        
        MDToolbar:
            id: main_screen_bottom_toolbar
            pos_hint: {'bottom': 1}
            # right_action_items: [["menu", lambda x: app.view_from_local()]]
            left_action_items: [["menu", lambda x: app.show_main_grid_bottom_sheet()]]   
    
<SettingsScreen>:
    name: 'settings_screen'
    BoxLayout:
        orientation: "vertical"
        spacing: "5dp"
        
        MDToolbar:
            id: settings_screen_top_toolbar
            title: "Settings"
            elevation: 5
            pos_hint: {'top': 1}
            left_action_items: [["arrow-left", lambda x: app.go_to_main_screen()]]
            
        ScrollView:                
            MDBoxLayout:
                orientation: 'vertical'
                adaptive_height: True
                padding: dp(18)
                spacing: dp(5) 
                                       
                MDGridLayout:
                    cols: 2
                    
                    MDLabel:
                        id: label_settings_night_theme
                        text: 'Night Theme'
                        theme_text_color: "Custom"
                    MDSwitch:
                        id: theme_switcher
                        on_active: app.on_theme_checkbox_active(*args)
                        
                    MDLabel:
                        id: label_settings_tts
                        text: 'Load text to speech online'
                        theme_text_color: "Custom"
                    MDSwitch:
                        id: settings_tts_switcher
                        on_active: app.on_change_tts_settings(*args)
                    
                    MDLabel:
                        id: label_settings_hsk_level
                        text: 'Daily words HSK Level'
                        theme_text_color: "Custom"
                    TButton:
                        id: hsk_level_t_button
                        icon: 'numeric-1'
                        on_press: app.change_hsk_level()
                                                
                    MDLabel:
                        size_hint_y: None 
                        id: label_settings_current_font
                        text: 'Current font'
                        theme_text_color: "Custom"
    
                    MDFlatButton:
                        size_hint: 0.2, 1
                        id: settings_current_font_name
                        text: app.font_name_in_json
                        on_press: app.change_font_list_view()
                        theme_text_color: "Custom"
                        text_color: rgba('2196f3')

        MDFlatButton:
            text: 'Licence'
            size_hint_x: 1
            on_press: app.view_app_license()
            
        MDToolbar:
            id: settings_screen_bottom_toolbar
            pos_hint: {'bottom': 1}
            right_action_items: [["information-variant", lambda x: app.on_about_app()]]
            left_action_items: [["menu", lambda x: app.show_main_grid_bottom_sheet()]]   
    
<FavoriteScreen>:
    name: 'favorite_screen'   
    BoxLayout:
        orientation: "vertical"
        spacing: "5dp"
        
        MDToolbar:
            id: favorite_screen_top_toolbar
            title: "Favorite"
            elevation: 5
            pos_hint: {'top': 1}
            # right_action_items: [["delete", lambda x: app.delete_word_list()]]
            left_action_items: [["arrow-left", lambda x: app.go_to_main_screen()]]
            
        ScrollView:                
            MDBoxLayout:
                id: fav_words_box_layout
                orientation: 'vertical'
                adaptive_height: True
                padding: dp(18)
                spacing: dp(15)
            
        MDToolbar:
            id: favorite_screen_bottom_toolbar
            pos_hint: {'bottom': 1}
            right_action_items: [["folder-zip", lambda x: app.export_as_anki_deck()]]
            left_action_items: [["menu", lambda x: app.show_main_grid_bottom_sheet()]]   
   
<NewsScreen>:
    name: 'news_screen'
    news_box_layout: news_box_layout.__self__
    BoxLayout:
        id: news_box
        orientation: "vertical"
        spacing: "5dp"
        
        MDToolbar:
            id: news_screen_top_toolbar
            title: "News"
            elevation: 5
            pos_hint: {'top': 1}
            left_action_items: [["arrow-left", lambda x: app.go_to_main_screen()]]
                    
        ScrollView:                
            MDBoxLayout:
                id: news_box_layout
                orientation: 'vertical'
                adaptive_height: True
                padding: dp(15)
                spacing: dp(5)
                
                MDSpinner:
                    id: news_loading_spinner
                    size_hint: None, None
                    size: dp(46), dp(46)
                    pos_hint: {'center_x': .5, 'center_y': .5}
                    active: True
                
            
        MDToolbar:
            id: news_screen_bottom_toolbar
            pos_hint: {'bottom': 1}
            #right_action_items: [["dots-vertical", lambda x: app.show_main_grid_bottom_sheet()]]
            left_action_items: [["menu", lambda x: app.show_main_grid_bottom_sheet()]] 

<NewsReaderScreen>:
    name: 'news_reader_screen'
    news_reader_box_layout: news_reader_box_layout.__self__
    news_reader_article: news_reader_article.__self__
    BoxLayout:
        orientation: "vertical"
        spacing: "5dp"
        
        MDToolbar:
            id: news_reader_top_toolbar
            title: "News"
            elevation: 5
            pos_hint: {'top': 1}
            left_action_items: [["arrow-left", lambda x: app.go_to_news_screen()]] 
            right_action_items: [["play", lambda x: app.text_to_speech(app.article_text_for_tts)], ["stop", lambda x: app.stop_tts()], ["web", lambda x: app.open_in_browser()]]

                
        ScrollView:                
            MDBoxLayout:
                id: news_reader_box_layout
                orientation: 'vertical'
                adaptive_height: True
                padding: dp(8)
                spacing: dp(6)
                
                MDSpinner:
                    id: news_reader_loading_spinner
                    size_hint: None, None
                    size: dp(46), dp(46)
                    pos_hint: {'center_x': .5, 'center_y': .5}
                    active: True
                                
                MDLabel:
                    font_style: 'Subtitle2'
                    id: news_screen_reader_url
                    size_hint_y: None
                    height: self.texture_size[1]
                    theme_text_color: "Hint"
                                                     
                MDLabel:
                    markup: True
                    font_size: '31sp'
                    font_name: app.custom_app_font
                    id: news_reader_header
                    size_hint_y: None
                    height: self.texture_size[1]
                    theme_text_color: "Custom"
                    
                MDLabel:
                    font_style: 'Subtitle2'
                    id: news_reader_time
                    size_hint_y: None
                    height: self.texture_size[1]
                    theme_text_color: "Secondary"                
                
                MDLabel:
                    markup: True
                    font_name: app.custom_app_font
                    id: news_reader_article
                    size_hint_y: None
                    height: self.texture_size[1]
                    font_size: '24sp'
                    theme_text_color: "Custom"
                    text_color: rgba('2f2f2f')
                
                MDLabel:
                    id: news_reader_authors
                    font_name: app.custom_app_font
                    size_hint_y: None
                    height: self.texture_size[1]
            
        MDToolbar:
            id: news_reader_bottom_toolbar
            pos_hint: {'bottom': 1}
            left_action_items: [["menu", lambda x: app.show_main_grid_bottom_sheet()]]
            right_action_items: [["format-font-size-increase", lambda x: app.change_news_reader_font_size('increase')], ["format-font", lambda x: app.change_news_reader_font_size('reset')], ["format-font-size-decrease", lambda x: app.change_news_reader_font_size('decrease')]]
    
<NewsCard>:
    id: news_card_id
    orientation: 'vertical'
    padding: dp(8)
    ripple_behavior: True
    size_hint: 1, None
    size: dp(200), dp(180)
    
    BoxLayout:
        orientation: 'horizontal'
        padding: dp(8)
        
        MDLabel:
            id: news_card_num
            font_style: 'Subtitle2'
            size_hint_x: 0.1
            theme_text_color: "Custom"
            text_color: rgba('ee5c35')
            halign: 'center'
            
        MDLabel:
            id: news_card_link
            font_style: 'Caption'
            size_hint_x: 0.9
            theme_text_color: "Custom"
            text_color: rgba('5f5f5f')
            halign: 'left'
            
    MDLabel:
        id: news_card_title
        font_size: "24sp"
        font_name: app.custom_app_font
        theme_text_color: "Custom"
        text_color: rgba('2f3338')
            
    MDLabel:
        id: news_card_time
        font_style: "Overline"
        theme_text_color: "Custom"
        text_color: rgba('899097')

<WordCard>:
    id: word_card_id
    orientation: 'vertical'
    padding: dp(8)
    ripple_behavior: True
    size_hint: 1, None
    size: dp(220), dp(180)
    on_touch_down: app.fav_word_card_click(*args)

    MDLabel:
        id: word_card_ch_sim
        theme_text_color: "Custom"
        text_color: rgba('6495ed')
        font_size: "24sp"
        font_name: app.custom_app_font
        
    MDLabel:
        id: word_card_ch_trad
        font_size: "24sp"
        font_name: app.custom_app_font
        theme_text_color: "Custom"
        text_color: rgba('27b46e')
            
    MDLabel:
        id: word_card_ch_pin
        theme_text_color: "Custom"
        text_color: rgba('899097')
        font_name: app.custom_app_font
 
    MDLabel:
        id: word_card_ch_mean
        theme_text_color: "Custom"
        text_color: rgba('fb8c00')
        font_name: app.custom_app_font
 
<CustomWordPopup>:
    id: custom_pop_up
    title : ""
    separator_height: 0
    title_color: 1, 0, 0, 1
    size_hint: 0.9, 0.5

    BoxLayout:
        orientation: "vertical"

        MDGridLayout:
            cols: 1
            
            MDLabel:
                id: popup_ch_sim
                font_size: '28sp'
                font_name: app.custom_app_font
                halign: 'center'
                theme_text_color: "Custom"
                text_color: rgba('6495ed')
                            
            MDLabel:
                id: popup_ch_pin
                font_size: '18sp'
                font_name: app.custom_app_font
                halign: 'center'
                theme_text_color: "Custom"
                text_color: rgba('5f5f5f')
                         
            MDLabel:
                id: popup_ch_trad
                font_size: '24sp'
                font_name: app.custom_app_font
                halign: 'center'
                theme_text_color: "Custom"
                text_color: rgba('27b46e')
                          
            MDLabel:
                id: popup_ch_mean
                font_size: '20sp'
                font_name: app.custom_app_font
                halign: 'center'
                theme_text_color: "Custom"
                text_color: rgba('fb8c00')
                        
            BoxLayout:
                orientation: 'horizontal'
                TButton:
                    icon: 'volume-high'
                    size_hint: 1, None
                    pos_hint: {'center_x':0.5}
                    on_press: app.text_to_speech(popup_ch_sim.text)
                    theme_text_color: "Custom"
                    text_color: rgba('2196f3')                    
                    
                TButton:
                    id: btn_save_word_to_news_list
                    icon: 'heart'
                    size_hint: 1, None
                    pos_hint: {'center_x':0.5}
                    on_press: app.save_words_to_file('reader')
                    theme_text_color: "Custom"
                    text_color: rgba('ea2322')
                    disabled: True
                         
<ChangeDefaultRSSFeedPopup>:
    id: change_rss_feed_popup
    title : "Change RSS feed topic"
    separator_height: 0
    title_color: rgba('2196f3')
    size_hint: 0.9, 0.6
    auto_dismiss: False
    
    BoxLayout:
        orientation: "vertical"
        MDTextField:
            id: tf_rss_feed_popup
            hint_text: 'Enter topic'
            helper_text: "business, technology, sports, movies..."
            helper_text_mode: "persistent"
            
        FloatLayout:
            
            MDLabel:
                id: label_rss_popup_get_feed
                text: 'Get news feed by search query'
                pos_hint: {'center_x': .7, 'center_y': .5}
                theme_text_color: "Custom"
        
            Check:
                id: checkbox_rss_popup_get_feed
                pos_hint: {'center_x': .1, 'center_y': .5}
                theme_text_color: "Custom"
                on_active: app.on_get_feed_by_query(*args)
        
        MDLabel:
            id: label_rss_popup_wait_feed
            theme_text_color: "Custom"
            text: 'Press OK and wait to load feed'
            halign: 'center'
            font_size: '12sp'
        
        GridLayout:
            cols: 2   
            MDFlatButton:
                text: 'OK'
                size_hint_x: 1
                theme_text_color: "Custom"
                text_color: rgba('2196f3')
                on_press: app.ok_button_rss_feed()
                
            MDFlatButton:
                text: 'CLOSE'
                size_hint_x: 1
                theme_text_color: "Custom"
                text_color: rgba('ff5722')
                on_press: app.close_button_rss_feed()
                               
<Check@MDCheckbox>:
    group: 'group'
    size_hint: None, None
    size: dp(48), dp(48)
    
<CustomPopup>:
    id: license_popup
    title : "License"
    separator_height: 0
    title_color: rgba('2196f3')
    size_hint: 0.9, 0.6        
"""
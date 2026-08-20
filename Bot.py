import os
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

# زانیارییەکانی بۆتی تلگرامەکەت و ئایدییەکەی تۆ
BOT_TOKEN = "8667887809:AAE8BpyPP9ehPEs0czgimcLiryYXHgryZYw"
CHAT_ID = "8734106005"

class TelegramAppUI(BoxLayout):
    def init(self, **kwargs):
        super(TelegramAppUI, self).init(**kwargs)
        self.orientation = 'vertical'
        self.padding = 50
        self.spacing = 20

        # دیزاینی پەنجەرەکە
        self.label = Label(
            text="ئایا دەتەوێت گەلەری مۆبایلی خۆت بکەیتەوە؟", 
            font_size=18,
            halign='center'
        )
        self.add_widget(self.label)

        # دوگمەی بەڵێ
        self.btn_yes = Button(text="بەڵێ", size_hint=(1, 0.3))
        self.btn_yes.bind(on_press=self.on_yes_clicked)
        self.add_widget(self.btn_yes)

        # دوگمەی نەخێر
        self.btn_no = Button(text="نەخێر", size_hint=(1, 0.3))
        self.btn_no.bind(on_press=self.exit_app)
        self.add_widget(self.btn_no)

    def on_yes_clicked(self, instance):
        self.label.text = "تکایە چاوەڕوان بە..."
        try:
            # ناردنی پەیام بۆ بۆت کە بەکارهێنەر ڕەزامەندی داوە
            message = "بەکارهێنەر دوگمەی (بەڵێ)ـی داگرت و گەلەری کرایەوە!"
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message}
            requests.post(url, data=payload)
            
            self.label.text = "سوپاس بۆ بەکارهێنان!"
        except Exception as e:
            self.label.text = "هەڵەیەک ڕوویدا لە پەیوەندیکردن."

    def exit_app(self, instance):
        App.get_running_app().stop()

class MyApp(App):
    def build(self):
        return TelegramAppUI()

if name == 'main':
    MyApp().run()

# -*- coding: utf-8 -*-
import urllib.request
import json
import os
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {'script', 'style', 'img', 'meta', 'link', 'noscript'}
        self.current_tag = ''
        self.counter = 1
        
        # ফিল্টারিং টার্গেট নাম্বারসমূহ
        self.target_numbers = {
            12, 13, 15, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 42, 
            51, 52, 53, 54, 56, 57, 59
        }
        
        self.temp_12 = ""
        self.temp_51 = ""

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                if self.counter in self.target_numbers:
                    if self.counter == 12:
                        self.temp_12 = text
                    elif self.counter == 13:
                        combined_text = f"{self.temp_12} {text}".strip()
                        self.text_parts.append({"12+13": combined_text})
                    elif self.counter == 51:
                        self.temp_51 = text
                    elif self.counter == 52:
                        combined_text = f"{self.temp_51} {text}".strip()
                        self.text_parts.append({"51+52": combined_text})
                    else:
                        self.text_parts.append({str(self.counter): text})
                self.counter += 1

def fetch_prayer_times(country_code, city_name):
    url = f"https://muslimbangla.com/world/{country_code}/prayer-times-{city_name}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
        
        parser = TextExtractor()
        parser.feed(html)
        return parser.text_parts
    except Exception as e:
        print(f"Error fetching data for {country_code}/{city_name}: {e}")
        return None

if __name__ == "__main__":
    # এখানে আপনি যত খুশি দেশ ও শহরের নাম যুক্ত করতে পারবেন (সঠিক URL ফরম্যাট অনুযায়ী)
    locations = [
        {"country": "BD", "city": "Dhaka"},
        {"country": "SA", "city": "Makkah"},
        {"country": "SA", "city": "Madinah"},
        {"country": "BE", "city": "Brussels"} # উদাহরণস্বরূপ দেওয়া হলো
    ]

    for loc in locations:
        country = loc["country"]
        city = loc["city"]
        
        print(f"Processing: {country}/{city}...")
        data = fetch_prayer_times(country, city)
        
        if data:
            # কান্ট্রি কোড অনুযায়ী ফোল্ডার তৈরি করা (যেমন: BD/, SA/)
            os.makedirs(country, exist_ok=True)
            
            # শহরের নাম অনুযায়ী ফাইল তৈরি করা (যেমন: BD/Dhaka.json)
            file_path = os.path.join(country, f"{city}.json")
            
            with open(file_path, "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
                
    print("সব দেশের ডেটা সফলভাবে আপডেট হয়েছে!")

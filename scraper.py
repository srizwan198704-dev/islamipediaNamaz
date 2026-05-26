# -*- coding: utf-8 -*-
import urllib.request
import json
import os
import time
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
    # ইউআরএল-এর স্পেস বা ফরম্যাট ঠিক করার জন্য (যেমন: Cox's Bazar বা New York)
    formatted_city = city_name.lower().replace(" ", "%20")
    url = f"https://muslimbangla.com/world/{country_code}/prayer-times-{formatted_city}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
        
        parser = TextExtractor()
        parser.feed(html)
        return parser.text_parts
    except Exception as e:
        print(f"Error fetching data for {country_code}/{city_name}: {e}")
        return None

if __name__ == "__main__":
    locations = []

    # ১. drs.json ফাইল থেকে বাংলাদেশের সব ডিস্ট্রিক্টের নাম রিড করা
    json_file_name = "drs.json"
    if os.path.exists(json_file_name):
        try:
            with open(json_file_name, "r", encoding="utf-8") as f:
                districts = json.load(f)
                for dist in districts:
                    if "name" in dist and dist["name"]:
                        locations.append({"country": "BD", "city": dist["name"]})
            print(f"সফলভাবে {json_file_name} থেকে {len(districts)}টি জেলার নাম লোড করা হয়েছে।")
        except Exception as e:
            print(f"{json_file_name} ফাইলটি পড়তে সমস্যা হয়েছে: {e}")
    else:
        print(f"সতর্কতা: {json_file_name} ফাইলটি পাওয়া যায়নি! ডিফল্ট ব্যাকআপ লিস্ট ব্যবহার করা হচ্ছে।")
        # ফাইলটি কোনো কারণে মিস হলে ব্যাকআপ হিসেবে ঢাকা ও মক্কা রানিং রাখার জন্য:
        locations.append({"country": "BD", "city": "Dhaka"})

    # ২. অন্যান্য আন্তর্জাতিক প্রধান শহরসমূহ (ইচ্ছা হলে এখানে আরও বাড়াতে পারেন)
    other_locations = [
        {"country": "SA", "city": "Makkah"},
        {"country": "SA", "city": "Madinah"},
        {"country": "BE", "city": "Brussels"}
    ]
    locations.extend(other_locations)

    # ৩. লুপ চালিয়ে সব ডেটা স্ক্র্যাপ এবং সেভ করা
    for loc in locations:
        country = loc["country"]
        city = loc["city"]
        
        print(f"Processing: {country}/{city}...")
        data = fetch_prayer_times(country, city)
        
        if data and len(data) > 0:
            os.makedirs(country, exist_ok=True)
            
            # ফাইলের নাম ছোট হাতের অক্ষরে সেভ হবে (যেমন: BD/dhaka.json)
            file_path = os.path.join(country, f"{city.lower()}.json")
            
            with open(file_path, "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            
            # গিটহাব ও সার্ভার সেফটির জন্য ছোট বিরতি
            time.sleep(0.5)
                
    print("সব দেশ ও জেলার ডেটা সফলভাবে আপডেট হয়েছে!")

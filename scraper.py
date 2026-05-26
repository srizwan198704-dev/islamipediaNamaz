# -*- coding: utf-8 -*-
import urllib.request
import json
import os
import time
from html.parser import HTMLParser

class PrayerTimeExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.raw_texts = []
        self.skip_tags = {'script', 'style', 'img', 'meta', 'link', 'noscript'}
        self.current_tag = ''

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_data(self, data):
        # সাইটের স্ক্রিপ্ট বা স্টাইল ট্যাগ বাদে সব দৃশ্যমান টেক্সট আগে সংগ্রহ করি
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                self.raw_texts.append(text)

    def get_filtered_data(self):
        filtered_results = {}
        
        # নামাযের ওয়াক্ত এবং ডেটা ট্র্যাকিংয়ের জন্য কী-ওয়ার্ড ম্যাপিং
        prayer_keywords = {
            "ফজর": "Fajr",
            "সূর্যোদয়": "Sunrise",
            "যোহর": "Dhuhr",
            "আসর": "Asr",
            "সূর্যাস্ত": "Sunset",
            "মাগরিব": "Maghrib",
            "ইশা": "Isha",
            "তাহাজ্জুদ": "Tahajjud"
        }

        # পুরো টেক্সট লিস্টের ওপর লুপ চালিয়ে সুনির্দিষ্ট ডেটা খোঁজা
        for i, text in enumerate(self.raw_texts):
            # ১. হিজরী তারিখ ফিল্টার (টেক্সটে 'হিজরী' শব্দটা থাকলে এবং তার পরের টেক্সটটি তারিখ হলে)
            if "হিজরী" in text:
                filtered_results["Hijri_Date"] = text
                # অনেক সময় "হিজরী" শব্দের ঠিক পরেই আসল তারিখের টেক্সট থাকে, সেটা চেক করা
                if i + 1 < len(self.raw_texts) and any(char.isdigit() for char in self.raw_texts[i+1]):
                    filtered_results["Hijri_Date"] = f"{text} {self.raw_texts[i+1]}".strip()

            # ২. নামাযের সময়সূচি ফিল্টার (যেমন: টেক্সট যদি হয় "ফজর" এবং তার পরের টেক্সট যদি হয় সময় "৪:১৫")
            if text in prayer_keywords:
                key_name = prayer_keywords[text]
                if i + 1 < len(self.raw_texts):
                    time_value = self.raw_texts[i+1]
                    # নিশ্চিত হয়ে নেওয়া যে পরের টেক্সটটি আসলেই একটা সময় (যেমন ক্লোন ':' আছে)
                    if ":" in time_value:
                        filtered_results[key_name] = time_value

        return filtered_results

def fetch_prayer_times(country_code, city_name):
    # ইউআরএল-এর স্পেস বা ফরম্যাট ঠিক করার জন্য
    formatted_city = city_name.lower().replace(" ", "%20")
    url = f"https://muslimbangla.com/world/{country_code}/prayer-times-{formatted_city}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
        
        parser = PrayerTimeExtractor()
        parser.feed(html)
        return parser.get_filtered_data()
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
        locations.append({"country": "BD", "city": "Dhaka"})

    # ২. অন্যান্য আন্তর্জাতিক প্রধান শহরসমূহ
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
        
        # ডেটা পাওয়া গেলে এবং সেটিতে অন্তত নামাযের কিছু ফিল্ড থাকলে সেভ করবে
        if data and len(data) > 0:
            os.makedirs(country, exist_ok=True)
            
            # ফাইলের নাম ছোট হাতের অক্ষরে সেভ হবে (যেমন: BD/dhaka.json)
            file_path = os.path.join(country, f"{city.lower()}.json")
            
            with open(file_path, "w", encoding="utf-8") as json_file:
                # সুন্দর ও ক্লিন কি-ভ্যালু স্ট্রাকচারে ডাটা রাইট হবে
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            
            # গিটহাব ও সার্ভার সেফটির জন্য ছোট বিরতি
            time.sleep(0.5)
                
    print("সব দেশ ও জেলার সুনির্দিষ্ট ডেটা সফলভাবে আপডেট হয়েছে!")

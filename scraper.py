# -*- coding: utf-8 -*-
import urllib.request
import json
import os
import time
from html.parser import HTMLParser

class DynamicTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.raw_texts = []
        self.skip_tags = {'script', 'style', 'img', 'meta', 'link', 'noscript'}
        self.current_tag = ''

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                self.raw_texts.append(text)

    def extract_with_sample_structure(self):
        # পেজ থেকে সংগ্রহ করা সমস্ত টেক্সটের একটি কপি
        texts = self.raw_texts
        extracted_list = []
        
        # ১. হিজরি তারিখ খুঁজে বের করা (যা আপনার স্যাম্পলে "12+13" পজিশনে ছিল)
        hijri_index = -1
        for idx, t in enumerate(texts):
            if "হিজরি" in t or "হিজরীর" in t:
                hijri_index = idx
                break
        
        # হিজরি তারিখের আগের অংশ (যেমন: ৯ যিলহজ্ব, ১৪৪৭) এবং "হিজরি" শব্দটা জোড়া দেওয়া
        if hijri_index != -1 and hijri_index > 0:
            combined_hijri = f"{texts[hijri_index-1]} {texts[hijri_index]}".strip()
            extracted_list.append({"12+13": combined_hijri})
            
            # ২. বাংলা তারিখ খুঁজে বের করা (যা হিজরির ঠিক ২ পজিশন পরে থাকে - "15" নম্বর পজিশন)
            bangla_idx = hijri_index + 2
            if bangla_idx < len(texts) and "বঙ্গাব্দ" in texts[bangla_idx]:
                extracted_list.append({"15": texts[bangla_idx]})

        # ৩. নামাযের ওয়াক্ত এবং নিষিদ্ধ সময়সূচী ট্র্যাক করা (যা আপনার স্যাম্পলের মূল কাঠামো)
        # আপনার স্যাম্পল অনুযায়ী যে ওয়াক্তগুলোর নাম এবং তাদের নির্দিষ্ট পজিশন দরকার:
        prayer_targets = [
            {"name": "ফজর", "pos_key": "24", "time_key": "25"},
            {"name": "যুহর", "pos_key": "26", "time_key": "27"},
            {"name": "আসর", "pos_key": "28", "time_key": "30"}, # আসরের পর 'বর্তমান' স্কিপ করে সরাসরি সময়
            {"name": "মাগরিব", "pos_key": "31", "time_key": "32"}, # আপনার স্যাম্পল অনুযায়ী মাগরিব ৩১
            {"name": "ইশা", "pos_key": "33", "time_key": "34"},   # ইশা ৩৩ এবং তার সময় ৩৪ (মাঝের 'বর্তমান' স্কিপড)
            {"name": "সূর্যোদয়", "pos_key": "36", "time_key": "37"},
            {"name": "দুপুর", "pos_key": "38", "time_key": "39"},
            {"name": "সূর্যাস্ত", "pos_key": "40", "time_key": "42"},
        ]

        # ওয়াক্তগুলোর নাম খুঁজে তার সাপেক্ষে ডাইনামিক্যালি আপনার স্যাম্পল কি (Key) বসানো
        for target in prayer_targets:
            for idx, t in enumerate(texts):
                if t == target["name"]:
                    # ওয়াক্তের নাম যুক্ত করা
                    extracted_list.append({target["pos_key"]: t})
                    
                    # ওয়াক্তের সময় খুঁজে বের করা (নামের পর প্রথম যে টেক্সটে সময়সূচী বা '০৩:৪৭' এর মতো ক্লোন থাকবে)
                    for time_idx in range(idx + 1, min(idx + 5, len(texts))):
                        if ":" in texts[time_idx]:
                            extracted_list.append({target["time_key"]: texts[time_idx]})
                            break
                    break

        # ৪. নফল নামাযের সময়সূচী (তাহাজ্জুদ, ইশরাক, চাশত)
        # তাহাজ্জুদ ও সাহরী(শেষ) জোড়া লাগানো (যা আপনার স্যাম্পলে "51+52")
        tahajjud_idx = -1
        for idx, t in enumerate(texts):
            if t == "তাহাজ্জুদ":
                tahajjud_idx = idx
                break
                
        if tahajjud_idx != -1 and tahajjud_idx + 1 < len(texts):
            if "সাহরী" in texts[tahajjud_idx+1]:
                combined_tahajjud = f"{texts[tahajjud_idx]} {texts[tahajjud_idx+1]}".strip()
                extracted_list.append({"51+52": combined_tahajjud})
                
                # তাহাজ্জুদের সময় ("53")
                if tahajjud_idx + 2 < len(texts) and ":" in texts[tahajjud_idx+2]:
                    extracted_list.append({"53": texts[tahajjud_idx+2]})

        # ইশরাক ("54") এবং তার সময় ("56")
        for idx, t in enumerate(texts):
            if t == "ইশরাক":
                extracted_list.append({"54": t})
                for time_idx in range(idx + 1, min(idx + 4, len(texts))):
                    if ":" in texts[time_idx]:
                        extracted_list.append({"56": texts[time_idx]})
                        break
                break

        # চাশত ("57") এবং তার সময় ("59")
        for idx, t in enumerate(texts):
            if t == "চাশত":
                extracted_list.append({"57": t})
                for time_idx in range(idx + 1, min(idx + 4, len(texts))):
                    if ":" in texts[time_idx]:
                        extracted_list.append({"59": texts[time_idx]})
                        break
                break

        return extracted_list

def fetch_prayer_times(country_code, city_name):
    formatted_city = city_name.lower().replace(" ", "%20")
    url = f"https://muslimbangla.com/world/{country_code}/prayer-times-{formatted_city}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
        
        parser = DynamicTextExtractor()
        parser.feed(html)
        return parser.extract_with_sample_structure()
    except Exception as e:
        print(f"Error fetching data for {country_code}/{city_name}: {e}")
        return None

if __name__ == "__main__":
    locations = []

    # drs.json থেকে ডিস্ট্রিক্ট লোড করা
    json_file_name = "drs.json"
    if os.path.exists(json_file_name):
        try:
            with open(json_file_name, "r", encoding="utf-8") as f:
                districts = json.load(f)
                for dist in districts:
                    if "name" in dist and dist["name"]:
                        locations.append({"country": "BD", "city": dist["name"]})
            print(f"Loaded {len(districts)} districts from {json_file_name}")
        except Exception as e:
            print(f"Error reading {json_file_name}: {e}")
    else:
        locations.append({"country": "BD", "city": "Dhaka"})

    # আন্তর্জাতিক শহরসমূহ
    other_locations = [
        {"country": "SA", "city": "Makkah"},
        {"country": "SA", "city": "Madinah"},
        {"country": "BE", "city": "Brussels"}
    ]
    locations.extend(other_locations)

    # রান এবং সেভ করা
    for loc in locations:
        country = loc["country"]
        city = loc["city"]
        
        print(f"Processing: {country}/{city}...")
        data = fetch_prayer_times(country, city)
        
        if data and len(data) > 0:
            os.makedirs(country, exist_ok=True)
            file_path = os.path.join(country, f"{city.lower()}.json")
            with open(file_path, "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            time.sleep(0.5)
                
    print("আপনার দেওয়া স্যাম্পল স্ট্রাকচার অনুযায়ী সব ডেটা ডাইনামিক্যালি আপডেট হয়েছে!")

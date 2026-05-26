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
        texts = self.raw_texts
        extracted_list = []
        
        # ১. হিজরি তারিখ খুঁজে বের করা
        hijri_index = -1
        for idx, t in enumerate(texts):
            if "হিজরি" in t or "হিজরীর" in t:
                hijri_index = idx
                break
        
        if hijri_index != -1 and hijri_index > 0:
            combined_hijri = f"{texts[hijri_index-1]} {texts[hijri_index]}".strip()
            extracted_list.append({"hijri_date": combined_hijri})
            
            # ২. বাংলা তারিখ খুঁজে বের করা
            bangla_idx = hijri_index + 2
            if bangla_idx < len(texts) and "বঙ্গাব্দ" in texts[bangla_idx]:
                extracted_list.append({"bangla_date": texts[bangla_idx]})

        # ৩. ফরজ ওয়াক্ত এবং প্রধান সময়সূচী ট্র্যাক করা (অর্থবহ Text Key সহ)
        prayer_targets = [
            {"name": "ফজর", "name_key": "fajr", "time_key": "fajr_time"},
            {"name": "যুহর", "name_key": "johor", "time_key": "johor_time"},
            {"name": "আসর", "name_key": "asr", "time_key": "asr_time"},
            {"name": "মাগরিব", "name_key": "maghrib", "time_key": "maghrib_time"},
            {"name": "ইশা", "name_key": "isha", "time_key": "isha_time"},
            {"name": "সূর্যোদয়", "name_key": "sunrise", "time_key": "sunrise_time"},
            {"name": "দুপুর", "name_key": "midday", "time_key": "midday_time"},
            {"name": "সূর্যাস্ত", "name_key": "sunset", "time_key": "sunset_time"},
        ]

        for target in prayer_targets:
            for idx, t in enumerate(texts):
                if t == target["name"]:
                    # ওয়াক্তের নাম যুক্ত করা
                    extracted_list.append({target["name_key"]: t})
                    
                    # ওয়াক্তের সময় খুঁজে বের করা
                    for time_idx in range(idx + 1, min(idx + 5, len(texts))):
                        if ":" in texts[time_idx]:
                            extracted_list.append({target["time_key"]: texts[time_idx]})
                            break
                    break

        # ৪. নফল নামায ও সাহরীর সময়সূচী
        tahajjud_idx = -1
        for idx, t in enumerate(texts):
            if t == "তাহাজ্জুদ":
                tahajjud_idx = idx
                break
                
        if tahajjud_idx != -1 and tahajjud_idx + 1 < len(texts):
            if "সাহরী" in texts[tahajjud_idx+1]:
                combined_tahajjud = f"{texts[tahajjud_idx]} {texts[tahajjud_idx+1]}".strip()
                extracted_list.append({"tahajjud_sehri": combined_tahajjud})
                
                if tahajjud_idx + 2 < len(texts) and ":" in texts[tahajjud_idx+2]:
                    extracted_list.append({"tahajjud_sehri_time": texts[tahajjud_idx+2]})

        # ইশরাক
        for idx, t in enumerate(texts):
            if t == "ইশরাক":
                extracted_list.append({"ishrak": t})
                for time_idx in range(idx + 1, min(idx + 4, len(texts))):
                    if ":" in texts[time_idx]:
                        extracted_list.append({"ishrak_time": texts[time_idx]})
                        break
                break

        # চাশত
        for idx, t in enumerate(texts):
            if t == "চাশত":
                extracted_list.append({"chasht": t})
                for time_idx in range(idx + 1, min(idx + 4, len(texts))):
                    if ":" in texts[time_idx]:
                        extracted_list.append({"chasht_time": texts[time_idx]})
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
                
    print("সব দেশের নির্দিষ্ট ডেটা টেক্সট ফরম্যাট কি (Key) অনুযায়ী আপডেট হয়েছে!")

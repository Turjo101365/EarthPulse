# 🌍 EarthPulse 3D: Camera-Driven Interactive 3D Earth

> **NASA MODIS ও VIIRS স্যাটেলাইট হটস্পট ও ওয়াইল্ডফায়ার মনিটরিং সিস্টেম (CesiumJS + FastAPI)**

---

## 🚀 এক নজরে (Overview)

এটি সাধারণ কোনো স্ট্যাটিক 3D গ্লোব নয়। এটি একটি **Camera-Driven Dynamic 3D Earth** আর্কিটেকচার। 
ইউজার ক্যামেরা দিয়ে যখন গ্লোব ঘোরাবেন, জুম ইন/আউট করবেন বা যেকোনো দেশে যাবেন, ব্রাউজারের ক্যামেরা সাথে সাথে তার **Visible Geographic Bounding Box (North, South, East, West)** এবং **Altitude (উচ্চতা)** ট্র্যাক করে FastAPI ব্যাকএন্ডে পাঠায়। ব্যাকএন্ড কেবল সেই বর্তমান দৃশ্যমান অঞ্চলের ডেটা ডায়নামিকালি লোড করে এবং ইউজার ইন্টারফেসে লাইভ পরিসংখ্যান আপডেট করে।

---

## 🏗️ Architecture Flow

```text
                    USER CAMERA (CesiumJS)
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Zoom Level      Camera Position   View Bounds (BBox)
    (Altitude km)    (Lat, Lon, Pitch)   (North, South, East, West)
          │              │              │
          └──────────────┼──────────────┘
                         ▼
             viewer.camera.changed / moveEnd
                         │
                         ▼ (Debounced REST API)
       GET /api/hotspots?north=..&south=..&east=..&west=..&altitude=..
                         │
                         ▼
                   FastAPI Backend
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
   Spatial BBox Filter             ML Harmonization Model
   (Dynamic LOD Clustering)     (MODIS 1km + VIIRS 375m fusion)
          │                             │
          └──────────────┬──────────────┘
                         ▼
        { summary: {...}, items: [...] }
                         │
                         ▼
         Cesium 3D Globe + Glassmorphism HUD
```

---

## 🔍 Level of Detail (LOD) স্তরসমূহ

| LOD লেভেল | উচ্চতা (Altitude) | দৃশ্যমান তথ্য (Visual Rendering) | UI পরিসংখ্যান (HUD Stats) |
|---|---|---|---|
| **LOD 1: Space View** | > 3,500 km | পুরো পৃথিবীর ম্যাক্রো ক্লাস্টার ও ডেনসিটি নোড | গ্লোবাল সামারি (~12,800+ হটস্পট, MODIS vs VIIRS অনুপাত) |
| **LOD 2: Continental View** | 1,200 - 3,500 km | সাব-মহাদেশীয় ক্লাস্টার সার্কেল ও হটস্পট কাউন্ট | আঞ্চলিক আগুন প্রবণতা ও গড় FRP |
| **LOD 3: Country View** | 300 - 1,200 km | দেশের বিভিন্ন বিভাগ/অঞ্চলের ক্লাস্টার (যেমন: বাংলাদেশ) | জাতীয় বিশ্লেষণ (বাংলাদেশ: ~183 হটস্পট, গড় FRP 42.7 MW) |
| **LOD 4: City / Local View** | 50 - 300 km | পৃথক পৃথক স্যাটেলাইট ডিটেকশন পয়েন্ট (MODIS 1km & VIIRS 375m) | স্থানীয় মেট্রো এলাকা (যেমন: ঢাকা অঞ্চল: ~25-27 হটস্পট) |
| **LOD 5: High-Precision View** | < 50 km | হাই-রেজোলিউশন পালসিং 3D মার্কার ও ক্লিকযোগ্য ইন্সপেকশন কার্ড | সম্পূর্ণ সেন্সর ডেটা (FRP, ব্রাইটনেস টেম্পারেচার, কনফিডেন্স, ML প্রবাবিলিটি) |

---

## 📦 প্রজেক্ট স্ট্রাকচার

```text
interactive-3d-earth/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI সার্ভার, REST এন্ডপয়েন্ট ও স্ট্যাটিক ফাইল হোস্টিং
│   ├── spatial_index.py     # স্প্যাশিয়াল বাউন্ডিং বক্স ফিল্টারিং ও ডায়নামিক LOD অ্যালগরিদম
│   ├── data_generator.py    # বিশ্বস্ত ও বাস্তবসম্মত স্যাটেলাইট হটস্পট ডেটাসেট (বাংলাদেশ ও গ্লোবাল)
│   ├── ml_harmonization.py  # MODIS ও VIIRS ক্রসিং-সেন্সর ML হারমোনাইজেশন মডেল
│   └── requirements.txt     # পাইথন ডিপেন্ডেন্সি (FastAPI, Uvicorn, ইত্যাদি)
├── frontend/
│   ├── index.html           # আধুনিক গ্লাসইউআই HUD ও Cesium কন্টেইনার
│   ├── css/
│   │   └── styles.css       # নাসার কমান্ড-সেন্টার অনুপ্রাণিত ডার্ক থিম স্টাইলিং
│   └── js/
│       ├── app.js               # মূল CesiumJS ইঞ্জিন ও অর্কেস্ট্রেশন
│       ├── camera_controller.js # ক্যামেরা বাউন্ডিং বক্স ট্র্যাকার ও ফ্লাই-টু কন্ট্রোলার
│       ├── data_service.js      # ব্যাকএন্ড API হ্যান্ডলার ও রিকোয়েস্ট ডিবউন্স
│       └── ui_controller.js     # লাইভ টেলিমেট্রি, চার্ট ও মোডাল কন্ট্রোলার
├── run.sh                   # স্বয়ংক্রিয় ওয়ান-ক্লিক স্টার্টআপ স্ক্রিপ্ট
└── README.md                # প্রজেক্ট ডকুমেন্টেশন
```

---

## ⚡ কীভাবে চালাবেন (How to Run)

### পদ্ধতি ১: সহজ ওয়ান-ক্লিক স্ক্রিপ্ট (One-Click Launch)

টার্মিনাল ওপেন করে প্রজেক্ট ফোল্ডারে যান এবং রান করুন:

```bash
cd /Users/turjo/Desktop/interactive-3d-earth
./run.sh
```

স্ক্রিপ্টটি স্বয়ংক্রিয়ভাবে ভার্চুয়াল এনভায়রনমেন্ট তৈরি করে ডিপেন্ডেন্সি ইনস্টল করবে এবং সার্ভার চালু করবে।

### পদ্ধতি ২: ম্যানুয়াল রান (Manual Start)

```bash
cd /Users/turjo/Desktop/interactive-3d-earth
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8050 --reload
```

সার্ভার চালু হলে ব্রাউজারে প্রবেশ করুন:
👉 **[http://localhost:8050](http://localhost:8050)**

---

## 🎮 ক্যামেরা কন্ট্রোল গাইড (Camera Controls)

* 🖱️ **মাউসের বাম ক্লিক + ড্র্যাগ (Left Drag):** পুরো পৃথিবী ঘোরানো (Rotate Globe / Pan).
* 🎡 **মাউস স্ক্রল হুইল / ডান ক্লিক + ড্র্যাগ (Right Drag / Scroll):** ক্যামেরা জুম ইন ও জুম আউট (Zoom In / Out).
* 🔄 **মাউসের মধ্যম বাটন / Ctrl + মাউস ড্র্যাগ (Middle Drag):** ক্যামেরা টিল্ট এবং অ্যাঙ্গেল পরিবর্তন (Tilt / Pitch).
* 🎯 **Quick Fly-To বাটনসমূহ:**
  * **Whole Earth:** গ্লোবাল স্পেস ভিউতে ফিরে যাওয়া।
  * **Bangladesh:** বাংলাদেশ কান্ট্রি লেভেল ভিউতে সরাসরি উড়ে যাওয়া (LOD 3)।
  * **Dhaka:** ঢাকা মেট্রো এলাকায় হাই-ডিটেইল জুম (LOD 4/5)।
  * **Hill Tracts / Sundarbans:** পার্বত্য চট্টগ্রাম ও সুন্দরবন ফ্রিন্জ জোন।
  * **California / Amazon / Australia:** গ্লোবাল ওয়াইল্ডফায়ার অঞ্চলসমূহ।
* 🔍 **হটস্পটে ক্লিক:** যেকোনো একক আগুনের মার্কারের উপর ক্লিক করলে তার বিস্তারিত সেন্সর ও ML মেটাডেটা মোডাল কার্ড ওপেন হবে।

---

## 🗺️ NASA FIRMS View Mode ও গ্লোবাল এনভায়রনমেন্টাল অ্যানালিটিক্স (New)

অফিসিয়াল **NASA FIRMS (Fire Information for Resource Management System)**-এর অনুকরণে যুক্ত করা নতুন ফিচারসমূহ:

1. **View Mode Switcher (টপ নেভিগেশন বার):**
   * **`[🌐 3D Globe]`**: বিদ্যমান ফটোরিয়্যালিস্টিক ৩ডি অরবিটাল গ্লোব ভিউ।
   * **`[🗺️ NASA FIRMS 2D]`**: কোনো রিলোড ছাড়াই ৩ডি গ্লোবকে মসৃণভাবে আনরোল করে ফ্ল্যাট ২ডি GIS ইক্যুইরেকট্যাঙ্গুলার ম্যাপে রূপান্তর করে (Cesium Native `morphTo2D`)।
   * **`[📊 Earth Impact]`**: বিশ্বব্যাপী পরিবেশগত প্রভাব ও অ্যানালিটিক্স ড্রয়ার ওপেন করে।
2. **NASA FIRMS Timeline Controller & অ্যানিমেশন প্লেয়ার:**
   * **Time Range:** `[24h]`, `[48h]`, এবং `[7 Days]` আর্কিভ ফিল্টার।
   * **Day-by-Day Scrubber:** গত ৭ দিনের (`T-6` থেকে `Today`) প্রতিটি দিনের ডেটা স্লাইড করে দেখার সুবিধা।
   * **`▶ Play` টাইম-ল্যাপস অ্যানিমেশন:** দিনভিত্তিক বিশ্বব্যাপী আগুনের পরিবর্তন স্বয়ংক্রিয়ভাবে অ্যানিমেট করে দেখায়।
3. **ব্রডার আর্থ ইমপ্যাক্ট ড্যাশবোর্ড (Global Environmental Analytics Drawer):**
   * **পোড়া মোট আয়তন (Burned Area):** $km^2$ এবং হেক্টর এককে লাইভ ক্যালকুলেশন।
   * **বায়ুমণ্ডলে নির্গত কার্বন (Carbon Emissions):** মেগাটনে $CO_2$ এবং কিলোটনে $CH_4$ মিথেন হিসাব।
   * **মোট নির্গত তাপশক্তি (Radiative Energy):** গিগাওয়াট ($GW$) এককে পরিমাপ।
   * **টপ কান্ট্রি লিডারবোর্ড:** সর্বাধিক আগুন আক্রান্ত দেশের র‍্যাঙ্কিং এবং সরাসরি সেই দেশে উড়ে যাওয়ার বাটন (`✈️ Fly`)।
   * **৭ দিনের ট্রেন্ড বার চার্ট:** গত এক সপ্তাহের আগুন বৃদ্ধির গ্রাফ।
   * **Diurnal Solar Cycle:** দিনের এবং রাতের স্যাটেলাইট ওভারপাস অনুপাত।
4. **স্মোক প্লুম ও থার্মাল হিটম্যাপ লেয়ার (FIRMS Layers):**
   * **Smoke Plumes & Aerosols:** আমাজন, কঙ্গো, ক্যালিফোর্নিয়া, ইন্দোনেশিয়া ও বাংলাদেশে আগুনের ধোঁয়ার বিস্তার সিমুলেশন।
   * **Thermal Density Heatmap:** চরম আগুনযুক্ত অঞ্চলে গ্লোয়িং থার্মাল ডেনসিটি ক্লাউড।
   * **NASA Day/Night কালার মোড:** অফিসিয়াল FIRMS কালার স্কিম (দিনের জন্য সোনালী হলুদ `#ffd600`, রাতের জন্য ইনফ্রারেড লাল `#ff1744`)।


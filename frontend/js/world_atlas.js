/**
 * Complete World Atlas: Continents, Countries, BD Divisions & Landmarks
 */
(function() {
    const CONTINENTS = [
        { id: "all", name: "All Continents", icon: "🌐" },
        { id: "asia", name: "Asia & Pacific", icon: "🌏" },
        { id: "europe", name: "Europe", icon: "🌍" },
        { id: "africa", name: "Africa", icon: "🌍" },
        { id: "north_america", name: "North America", icon: "🌎" },
        { id: "south_america", name: "South America", icon: "🌎" },
        { id: "oceania", name: "Oceania", icon: "🌏" },
        { id: "polar", name: "Polar & Space", icon: "❄️" }
    ];

    const WORLD_AREAS = [
        { id: "global", name: "Whole Earth (Space View)", query: "global", continent: "polar", flag: "🌎", lat: 15.0, lon: 25.0, alt: 27500000, keywords: ["world", "space", "shob"] },
        { id: "arctic", name: "Arctic Circle & North Pole", query: "polar_north", continent: "polar", flag: "❄️", lat: 82.0, lon: 0.0, alt: 8000000, keywords: ["ice", "greenland"] },
        { id: "antarctica", name: "Antarctica & South Pole", query: "polar_south", continent: "polar", flag: "🧊", lat: -82.0, lon: 0.0, alt: 8000000, keywords: ["ice"] },
        { id: "bd_dhaka", name: "Dhaka Division & Capital", nativeName: "ঢাকা বিভাগ", continent: "asia", flag: "📍", lat: 23.8103, lon: 90.4125, alt: 85000, keywords: ["capital", "gazipur"] },
        { id: "bd_chittagong", name: "Chittagong (Chattogram)", nativeName: "চট্টগ্রাম", continent: "asia", flag: "⛰️", lat: 22.3569, lon: 92.1831, alt: 110000, keywords: ["hill tracts", "coxs"] },
        { id: "bd_sundarbans", name: "Sundarbans Mangrove Reserve", nativeName: "সুন্দরবন", continent: "asia", flag: "🌲", lat: 22.15, lon: 89.6, alt: 95000, keywords: ["tiger", "khulna"] },
        { id: "bd_sylhet", name: "Sylhet Division", nativeName: "সিলেট", continent: "asia", flag: "🍵", lat: 24.8949, lon: 91.8687, alt: 110000, keywords: ["tea", "sreemangal"] },
        { id: "bd_rajshahi", name: "Rajshahi Division", nativeName: "রাজশাহী", continent: "asia", flag: "🥭", lat: 24.3745, lon: 88.6042, alt: 110000, keywords: ["mango", "silk"] },
        { id: "bd_khulna", name: "Khulna Division", nativeName: "খুলনা", continent: "asia", flag: "⚓", lat: 22.8456, lon: 89.5403, alt: 110000, keywords: ["mongla"] },
        { id: "bd_barisal", name: "Barisal Division", nativeName: "বরিশাল", continent: "asia", flag: "🌾", lat: 22.701, lon: 90.3535, alt: 110000, keywords: ["kuakata"] },
        { id: "bd_rangpur", name: "Rangpur Division", nativeName: "রংপুর", continent: "asia", flag: "🚜", lat: 25.7439, lon: 89.2752, alt: 110000, keywords: ["teesta"] },
        { id: "bd_mymensingh", name: "Mymensingh Division", nativeName: "ময়মনসিংহ", continent: "asia", flag: "🏞️", lat: 24.7471, lon: 90.4203, alt: 110000, keywords: ["garo"] },
        { id: "bd_coxs_bazar", name: "Cox's Bazar Sea Beach", nativeName: "কক্সবাজার", continent: "asia", flag: "🏖️", lat: 21.4272, lon: 92.0058, alt: 65000, keywords: ["sea", "beach"] },
        { id: "bd", name: "Bangladesh", nativeName: "বাংলাদেশ", continent: "asia", flag: "🇧🇩", lat: 23.85, lon: 90.35, alt: 750000, keywords: ["dhaka", "bangla"] },
        { id: "in", name: "India", nativeName: "ভারত", continent: "asia", flag: "🇮🇳", lat: 20.5937, lon: 78.9629, alt: 3200000, keywords: ["delhi", "mumbai"] },
        { id: "pk", name: "Pakistan", nativeName: "پاکستان", continent: "asia", flag: "🇵🇰", lat: 30.3753, lon: 69.3451, alt: 2200000, keywords: ["islamabad", "karachi"] },
        { id: "cn", name: "China", nativeName: "中国", continent: "asia", flag: "🇨🇳", lat: 35.8617, lon: 104.1954, alt: 4500000, keywords: ["beijing", "shanghai"] },
        { id: "jp", name: "Japan", nativeName: "日本", continent: "asia", flag: "🇯🇵", lat: 36.2048, lon: 138.2529, alt: 2200000, keywords: ["tokyo", "nippon"] },
        { id: "id", name: "Indonesia", nativeName: "Indonesia", continent: "asia", flag: "🇮🇩", lat: -0.7893, lon: 113.9213, alt: 3500000, keywords: ["jakarta", "bali"] },
        { id: "my", name: "Malaysia", nativeName: "Malaysia", continent: "asia", flag: "🇲🇾", lat: 4.2105, lon: 101.9758, alt: 1500000, keywords: ["kuala lumpur"] },
        { id: "sg", name: "Singapore", nativeName: "Singapore", continent: "asia", flag: "🇸🇬", lat: 1.3521, lon: 103.8198, alt: 90000, keywords: ["singapore"] },
        { id: "th", name: "Thailand", nativeName: "ประเทศไทย", continent: "asia", flag: "🇹🇭", lat: 15.87, lon: 100.9925, alt: 1800000, keywords: ["bangkok"] },
        { id: "vn", name: "Vietnam", nativeName: "Việt Nam", continent: "asia", flag: "🇻🇳", lat: 14.0583, lon: 108.2772, alt: 1800000, keywords: ["hanoi", "saigon"] },
        { id: "ph", name: "Philippines", nativeName: "Pilipinas", continent: "asia", flag: "🇵🇭", lat: 12.8797, lon: 121.774, alt: 2000000, keywords: ["manila"] },
        { id: "kr", name: "South Korea", nativeName: "대한민국", continent: "asia", flag: "🇰🇷", lat: 35.9078, lon: 127.7669, alt: 1200000, keywords: ["seoul"] },
        { id: "kp", name: "North Korea", nativeName: "조선", continent: "asia", flag: "🇰🇵", lat: 40.3399, lon: 127.5101, alt: 1100000, keywords: ["pyongyang"] },
        { id: "sa", name: "Saudi Arabia", nativeName: "المملكة العربية السعودية", continent: "asia", flag: "🇸🇦", lat: 23.8859, lon: 45.0792, alt: 2600000, keywords: ["riyadh", "mecca"] },
        { id: "ae", name: "United Arab Emirates", nativeName: "الإمارات", continent: "asia", flag: "🇦🇪", lat: 23.4241, lon: 53.8478, alt: 1100000, keywords: ["dubai", "abu dhabi"] },
        { id: "qa", name: "Qatar", nativeName: "قطر", continent: "asia", flag: "🇶🇦", lat: 25.3548, lon: 51.1839, alt: 450000, keywords: ["doha"] },
        { id: "kw", name: "Kuwait", nativeName: "الكويت", continent: "asia", flag: "🇰🇼", lat: 29.3117, lon: 47.4818, alt: 450000, keywords: ["kuwait city"] },
        { id: "om", name: "Oman", nativeName: "عُمان", continent: "asia", flag: "🇴🇲", lat: 21.4735, lon: 55.9754, alt: 1400000, keywords: ["muscat"] },
        { id: "bh", name: "Bahrain", nativeName: "البحرين", continent: "asia", flag: "🇧🇭", lat: 26.0667, lon: 50.5577, alt: 300000, keywords: ["manama"] },
        { id: "tr", name: "Turkey", nativeName: "Türkiye", continent: "asia", flag: "🇹🇷", lat: 38.9637, lon: 35.2433, alt: 1800000, keywords: ["istanbul", "ankara"] },
        { id: "ir", name: "Iran", nativeName: "ایران", continent: "asia", flag: "🇮🇷", lat: 32.4279, lon: 53.688, alt: 2200000, keywords: ["tehran"] },
        { id: "iq", name: "Iraq", nativeName: "العراق", continent: "asia", flag: "🇮🇶", lat: 33.2232, lon: 43.6793, alt: 1500000, keywords: ["baghdad"] },
        { id: "il", name: "Israel", nativeName: "ישראל", continent: "asia", flag: "🇮🇱", lat: 31.0461, lon: 34.8516, alt: 600000, keywords: ["jerusalem", "tel aviv"] },
        { id: "ps", name: "Palestine", nativeName: "فلسطين", continent: "asia", flag: "🇵🇸", lat: 31.9522, lon: 35.2332, alt: 450000, keywords: ["gaza", "ramallah"] },
        { id: "jo", name: "Jordan", nativeName: "الأردن", continent: "asia", flag: "🇯🇴", lat: 30.5852, lon: 36.2384, alt: 700000, keywords: ["amman", "petra"] },
        { id: "lb", name: "Lebanon", nativeName: "لبنان", continent: "asia", flag: "🇱🇧", lat: 33.8547, lon: 35.8623, alt: 350000, keywords: ["beirut"] },
        { id: "sy", name: "Syria", nativeName: "سوريا", continent: "asia", flag: "🇸🇾", lat: 34.8021, lon: 38.9968, alt: 1000000, keywords: ["damascus"] },
        { id: "ye", name: "Yemen", nativeName: "اليمن", continent: "asia", flag: "🇾🇪", lat: 15.5527, lon: 48.5164, alt: 1300000, keywords: ["sanaa"] },
        { id: "np", name: "Nepal", nativeName: "नेपाल", continent: "asia", flag: "🇳🇵", lat: 28.3949, lon: 84.124, alt: 850000, keywords: ["kathmandu", "everest"] },
        { id: "bt", name: "Bhutan", nativeName: "འབྲུག", continent: "asia", flag: "🇧🇹", lat: 27.5142, lon: 90.4336, alt: 550000, keywords: ["thimphu"] },
        { id: "lk", name: "Sri Lanka", nativeName: "ශ්‍රී ලංකා", continent: "asia", flag: "🇱🇰", lat: 7.8731, lon: 80.7718, alt: 850000, keywords: ["colombo"] },
        { id: "mv", name: "Maldives", nativeName: "ދިވެހިރާއްޖެ", continent: "asia", flag: "🇲🇻", lat: 3.2028, lon: 73.2207, alt: 450000, keywords: ["male"] },
        { id: "mm", name: "Myanmar", nativeName: "မြန်မာ", continent: "asia", flag: "🇲🇲", lat: 21.9162, lon: 95.956, alt: 1800000, keywords: ["yangon", "burma"] },
        { id: "af", name: "Afghanistan", nativeName: "افغانستان", continent: "asia", flag: "🇦🇫", lat: 33.9391, lon: 67.71, alt: 1600000, keywords: ["kabul"] },
        { id: "kz", name: "Kazakhstan", nativeName: "Қазақстан", continent: "asia", flag: "🇰🇿", lat: 48.0196, lon: 66.9237, alt: 3200000, keywords: ["astana"] },
        { id: "uz", name: "Uzbekistan", nativeName: "Oʻzbekiston", continent: "asia", flag: "🇺🇿", lat: 41.3775, lon: 64.5853, alt: 1600000, keywords: ["tashkent"] },
        { id: "tm", name: "Turkmenistan", nativeName: "Türkmenistan", continent: "asia", flag: "🇹🇲", lat: 38.9697, lon: 59.5563, alt: 1500000, keywords: ["ashgabat"] },
        { id: "kg", name: "Kyrgyzstan", nativeName: "Кыргызстан", continent: "asia", flag: "🇰🇬", lat: 41.2044, lon: 74.7661, alt: 1100000, keywords: ["bishkek"] },
        { id: "tj", name: "Tajikistan", nativeName: "Тоҷикистон", continent: "asia", flag: "🇹🇯", lat: 38.861, lon: 71.2761, alt: 950000, keywords: ["dushanbe"] },
        { id: "mn", name: "Mongolia", nativeName: "Монгол", continent: "asia", flag: "🇲🇳", lat: 46.8625, lon: 103.8467, alt: 2500000, keywords: ["ulaanbaatar"] },
        { id: "kh", name: "Cambodia", nativeName: "កម្ពុជា", continent: "asia", flag: "🇰🇭", lat: 12.5657, lon: 104.991, alt: 1200000, keywords: ["phnom penh"] },
        { id: "la", name: "Laos", nativeName: "ປະເທດລາວ", continent: "asia", flag: "🇱🇦", lat: 19.8563, lon: 102.4955, alt: 1200000, keywords: ["vientiane"] },
        { id: "tw", name: "Taiwan", nativeName: "台灣", continent: "asia", flag: "🇹🇼", lat: 23.6978, lon: 120.9605, alt: 750000, keywords: ["taipei"] },
        { id: "bn", name: "Brunei", nativeName: "Brunei", continent: "asia", flag: "🇧🇳", lat: 4.5353, lon: 114.7277, alt: 450000, keywords: ["bandar seri begawan"] },
        { id: "tl", name: "Timor-Leste", nativeName: "Timor-Leste", continent: "asia", flag: "🇹🇱", lat: -8.8742, lon: 125.7275, alt: 450000, keywords: ["dili"] },
        { id: "ge", name: "Georgia", nativeName: "საქართველო", continent: "asia", flag: "🇬🇪", lat: 42.3154, lon: 43.3569, alt: 750000, keywords: ["tbilisi"] },
        { id: "am", name: "Armenia", nativeName: "Հայաստան", continent: "asia", flag: "🇦🇲", lat: 40.0691, lon: 45.0382, alt: 600000, keywords: ["yerevan"] },
        { id: "az", name: "Azerbaijan", nativeName: "Azərbaycan", continent: "asia", flag: "🇦🇿", lat: 40.1431, lon: 47.5769, alt: 800000, keywords: ["baku"] },
        { id: "cy", name: "Cyprus", nativeName: "Κύπρος", continent: "asia", flag: "🇨🇾", lat: 35.1264, lon: 33.4299, alt: 450000, keywords: ["nicosia"] },
        { id: "gb", name: "United Kingdom", nativeName: "UK", continent: "europe", flag: "🇬🇧", lat: 55.3781, lon: -3.436, alt: 1300000, keywords: ["london", "england", "britain"] },
        { id: "de", name: "Germany", nativeName: "Deutschland", continent: "europe", flag: "🇩🇪", lat: 51.1657, lon: 10.4515, alt: 1200000, keywords: ["berlin"] },
        { id: "fr", name: "France", nativeName: "France", continent: "europe", flag: "🇫🇷", lat: 46.2276, lon: 2.2137, alt: 1400000, keywords: ["paris"] },
        { id: "it", name: "Italy", nativeName: "Italia", continent: "europe", flag: "🇮🇹", lat: 41.8719, lon: 12.5674, alt: 1300000, keywords: ["rome", "milan"] },
        { id: "es", name: "Spain", nativeName: "España", continent: "europe", flag: "🇪🇸", lat: 40.4637, lon: -3.7492, alt: 1300000, keywords: ["madrid", "barcelona"] },
        { id: "ru", name: "Russia", nativeName: "Россия", continent: "europe", flag: "🇷🇺", lat: 61.524, lon: 105.3188, alt: 6500000, keywords: ["moscow", "siberia"] },
        { id: "ua", name: "Ukraine", nativeName: "Україна", continent: "europe", flag: "🇺🇦", lat: 48.3794, lon: 31.1656, alt: 1500000, keywords: ["kyiv"] },
        { id: "pl", name: "Poland", nativeName: "Polska", continent: "europe", flag: "🇵🇱", lat: 51.9194, lon: 19.1451, alt: 1200000, keywords: ["warsaw"] },
        { id: "nl", name: "Netherlands", nativeName: "Nederland", continent: "europe", flag: "🇳🇱", lat: 52.1326, lon: 5.2913, alt: 600000, keywords: ["amsterdam", "holland"] },
        { id: "be", name: "Belgium", nativeName: "België", continent: "europe", flag: "🇧🇪", lat: 50.5039, lon: 4.4699, alt: 500000, keywords: ["brussels"] },
        { id: "ch", name: "Switzerland", nativeName: "Schweiz", continent: "europe", flag: "🇨🇭", lat: 46.8182, lon: 8.2275, alt: 600000, keywords: ["zurich", "geneva", "alps"] },
        { id: "se", name: "Sweden", nativeName: "Sverige", continent: "europe", flag: "🇸🇪", lat: 60.1282, lon: 18.6435, alt: 1800000, keywords: ["stockholm"] },
        { id: "no", name: "Norway", nativeName: "Norge", continent: "europe", flag: "🇳🇴", lat: 60.472, lon: 8.4689, alt: 1800000, keywords: ["oslo", "fjords"] },
        { id: "dk", name: "Denmark", nativeName: "Danmark", continent: "europe", flag: "🇩🇰", lat: 56.2639, lon: 9.5018, alt: 650000, keywords: ["copenhagen"] },
        { id: "fi", name: "Finland", nativeName: "Suomi", continent: "europe", flag: "🇫🇮", lat: 61.9241, lon: 25.7482, alt: 1600000, keywords: ["helsinki"] },
        { id: "ie", name: "Ireland", nativeName: "Éire", continent: "europe", flag: "🇮🇪", lat: 53.4129, lon: -8.2439, alt: 800000, keywords: ["dublin"] },
        { id: "pt", name: "Portugal", nativeName: "Portugal", continent: "europe", flag: "🇵🇹", lat: 39.3999, lon: -8.2245, alt: 950000, keywords: ["lisbon"] },
        { id: "gr", name: "Greece", nativeName: "Ελλάδα", continent: "europe", flag: "🇬🇷", lat: 39.0742, lon: 21.8243, alt: 900000, keywords: ["athens"] },
        { id: "at", name: "Austria", nativeName: "Österreich", continent: "europe", flag: "🇦🇹", lat: 47.5162, lon: 14.5501, alt: 650000, keywords: ["vienna"] },
        { id: "cz", name: "Czech Republic", nativeName: "Česko", continent: "europe", flag: "🇨🇿", lat: 49.8175, lon: 15.473, alt: 700000, keywords: ["prague"] },
        { id: "ro", name: "Romania", nativeName: "România", continent: "europe", flag: "🇷🇴", lat: 45.9432, lon: 24.9668, alt: 1100000, keywords: ["bucharest"] },
        { id: "hu", name: "Hungary", nativeName: "Magyarország", continent: "europe", flag: "🇭🇺", lat: 47.1625, lon: 19.5033, alt: 750000, keywords: ["budapest"] },
        { id: "by", name: "Belarus", nativeName: "Беларусь", continent: "europe", flag: "🇧🇾", lat: 53.7098, lon: 27.9534, alt: 1100000, keywords: ["minsk"] },
        { id: "bg", name: "Bulgaria", nativeName: "България", continent: "europe", flag: "🇧🇬", lat: 42.7339, lon: 25.4858, alt: 850000, keywords: ["sofia"] },
        { id: "rs", name: "Serbia", nativeName: "Србија", continent: "europe", flag: "🇷🇸", lat: 44.0165, lon: 21.0059, alt: 750000, keywords: ["belgrade"] },
        { id: "hr", name: "Croatia", nativeName: "Hrvatska", continent: "europe", flag: "🇭🇷", lat: 45.1, lon: 15.2, alt: 750000, keywords: ["zagreb"] },
        { id: "sk", name: "Slovakia", nativeName: "Slovensko", continent: "europe", flag: "🇸🇰", lat: 48.669, lon: 19.699, alt: 650000, keywords: ["bratislava"] },
        { id: "si", name: "Slovenia", nativeName: "Slovenija", continent: "europe", flag: "🇸🇮", lat: 46.1512, lon: 14.9955, alt: 500000, keywords: ["ljubljana"] },
        { id: "ba", name: "Bosnia and Herzegovina", nativeName: "BiH", continent: "europe", flag: "🇧🇦", lat: 43.9159, lon: 17.6791, alt: 650000, keywords: ["sarajevo"] },
        { id: "al", name: "Albania", nativeName: "Shqipëria", continent: "europe", flag: "🇦🇱", lat: 41.1533, lon: 20.1683, alt: 550000, keywords: ["tirana"] },
        { id: "mk", name: "North Macedonia", nativeName: "Северна Македонија", continent: "europe", flag: "🇲🇰", lat: 41.6086, lon: 21.7453, alt: 500000, keywords: ["skopje"] },
        { id: "is", name: "Iceland", nativeName: "Ísland", continent: "europe", flag: "🇮🇸", lat: 64.9631, lon: -19.0208, alt: 900000, keywords: ["reykjavik"] },
        { id: "ee", name: "Estonia", nativeName: "Eesti", continent: "europe", flag: "🇪🇪", lat: 58.5953, lon: 25.0136, alt: 650000, keywords: ["tallinn"] },
        { id: "lv", name: "Latvia", nativeName: "Latvija", continent: "europe", flag: "🇱🇻", lat: 56.8796, lon: 24.6032, alt: 650000, keywords: ["riga"] },
        { id: "lt", name: "Lithuania", nativeName: "Lietuva", continent: "europe", flag: "🇱🇹", lat: 55.1694, lon: 23.8813, alt: 650000, keywords: ["vilnius"] },
        { id: "lu", name: "Luxembourg", nativeName: "Lëtzebuerg", continent: "europe", flag: "🇱🇺", lat: 49.8153, lon: 6.1296, alt: 300000, keywords: ["luxembourg"] },
        { id: "mt", name: "Malta", nativeName: "Malta", continent: "europe", flag: "🇲🇹", lat: 35.9375, lon: 14.3754, alt: 250000, keywords: ["valletta"] },
        { id: "md", name: "Moldova", nativeName: "Moldova", continent: "europe", flag: "🇲🇩", lat: 47.4116, lon: 28.3699, alt: 550000, keywords: ["chisinau"] },
        { id: "me", name: "Montenegro", nativeName: "Crna Gora", continent: "europe", flag: "🇲🇪", lat: 42.7087, lon: 19.3744, alt: 450000, keywords: ["podgorica"] },
        { id: "mc", name: "Monaco", nativeName: "Monaco", continent: "europe", flag: "🇲🇨", lat: 43.7384, lon: 7.4246, alt: 120000, keywords: ["monaco"] },
        { id: "va", name: "Vatican City", nativeName: "Vaticano", continent: "europe", flag: "🇻🇦", lat: 41.9029, lon: 12.4534, alt: 50000, keywords: ["vatican", "rome"] },
        { id: "za", name: "South Africa", nativeName: "South Africa", continent: "africa", flag: "🇿🇦", lat: -30.5595, lon: 22.9375, alt: 2400000, keywords: ["cape town", "joburg"] },
        { id: "eg", name: "Egypt", nativeName: "مصر", continent: "africa", flag: "🇪🇬", lat: 26.8206, lon: 30.8025, alt: 1800000, keywords: ["cairo", "nile", "pyramids"] },
        { id: "ng", name: "Nigeria", nativeName: "Nigeria", continent: "africa", flag: "🇳🇬", lat: 9.082, lon: 8.6753, alt: 1800000, keywords: ["lagos", "abuja"] },
        { id: "cd", name: "DR Congo", nativeName: "Congo (RDC)", continent: "africa", flag: "🇨🇩", lat: -4.0383, lon: 21.7587, alt: 2800000, keywords: ["kinshasa", "congo basin"] },
        { id: "cg", name: "Republic of the Congo", nativeName: "Congo (Brazzaville)", continent: "africa", flag: "🇨🇬", lat: -0.228, lon: 15.8277, alt: 1500000, keywords: ["brazzaville"] },
        { id: "ke", name: "Kenya", nativeName: "Kenya", continent: "africa", flag: "🇰🇪", lat: -0.0236, lon: 37.9062, alt: 1600000, keywords: ["nairobi", "rift valley"] },
        { id: "et", name: "Ethiopia", nativeName: "ኢትዮጵያ", continent: "africa", flag: "🇪🇹", lat: 9.145, lon: 40.4897, alt: 1800000, keywords: ["addis ababa"] },
        { id: "ma", name: "Morocco", nativeName: "المغرب", continent: "africa", flag: "🇲🇦", lat: 31.7917, lon: -7.0926, alt: 1500000, keywords: ["casablanca", "rabat"] },
        { id: "dz", name: "Algeria", nativeName: "الجزائر", continent: "africa", flag: "🇩🇿", lat: 28.0339, lon: 1.6596, alt: 2500000, keywords: ["algiers", "sahara"] },
        { id: "tn", name: "Tunisia", nativeName: "تونس", continent: "africa", flag: "🇹🇳", lat: 33.8869, lon: 9.5375, alt: 1100000, keywords: ["tunis", "carthage"] },
        { id: "ly", name: "Libya", nativeName: "ليبيا", continent: "africa", flag: "🇱🇾", lat: 26.3351, lon: 17.2283, alt: 2200000, keywords: ["tripoli"] },
        { id: "sd", name: "Sudan", nativeName: "السودان", continent: "africa", flag: "🇸🇩", lat: 12.8628, lon: 30.2176, alt: 2200000, keywords: ["khartoum"] },
        { id: "ss", name: "South Sudan", nativeName: "South Sudan", continent: "africa", flag: "🇸🇸", lat: 6.877, lon: 31.307, alt: 1600000, keywords: ["juba"] },
        { id: "gh", name: "Ghana", nativeName: "Ghana", continent: "africa", flag: "🇬🇭", lat: 7.9465, lon: -1.0232, alt: 1100000, keywords: ["accra"] },
        { id: "tz", name: "Tanzania", nativeName: "Tanzania", continent: "africa", flag: "🇹🇿", lat: -6.369, lon: 34.8888, alt: 1800000, keywords: ["kilimanjaro", "dar es salaam"] },
        { id: "ug", name: "Uganda", nativeName: "Uganda", continent: "africa", flag: "🇺🇬", lat: 1.3733, lon: 32.2903, alt: 1100000, keywords: ["kampala", "victoria"] },
        { id: "ao", name: "Angola", nativeName: "Angola", continent: "africa", flag: "🇦🇴", lat: -11.2027, lon: 17.8739, alt: 1800000, keywords: ["luanda"] },
        { id: "mz", name: "Mozambique", nativeName: "Moçambique", continent: "africa", flag: "🇲🇿", lat: -18.6657, lon: 35.5296, alt: 1800000, keywords: ["maputo"] },
        { id: "zw", name: "Zimbabwe", nativeName: "Zimbabwe", continent: "africa", flag: "🇿🇼", lat: -19.0154, lon: 29.1549, alt: 1200000, keywords: ["harare", "victoria falls"] },
        { id: "zm", name: "Zambia", nativeName: "Zambia", continent: "africa", flag: "🇿🇲", lat: -13.1339, lon: 27.8493, alt: 1500000, keywords: ["lusaka"] },
        { id: "sn", name: "Senegal", nativeName: "Sénégal", continent: "africa", flag: "🇸🇳", lat: 14.4974, lon: -14.4524, alt: 1100000, keywords: ["dakar"] },
        { id: "ci", name: "Ivory Coast", nativeName: "Cote d Ivoire", continent: "africa", flag: "🇨🇮", lat: 7.54, lon: -5.5471, alt: 1200000, keywords: ["abidjan"] },
        { id: "cm", name: "Cameroon", nativeName: "Cameroun", continent: "africa", flag: "🇨🇲", lat: 7.3697, lon: 12.3547, alt: 1400000, keywords: ["yaounde"] },
        { id: "mg", name: "Madagascar", nativeName: "Madagasikara", continent: "africa", flag: "🇲🇬", lat: -18.7669, lon: 46.8691, alt: 1800000, keywords: ["antananarivo"] },
        { id: "na", name: "Namibia", nativeName: "Namibia", continent: "africa", flag: "🇳🇦", lat: -22.9576, lon: 18.4904, alt: 1600000, keywords: ["windhoek", "namib desert"] },
        { id: "bw", name: "Botswana", nativeName: "Botswana", continent: "africa", flag: "🇧🇼", lat: -22.3285, lon: 24.6849, alt: 1400000, keywords: ["gaborone", "kalahari"] },
        { id: "ml", name: "Mali", nativeName: "Mali", continent: "africa", flag: "🇲🇱", lat: 17.5707, lon: -3.9962, alt: 2200000, keywords: ["bamako", "timbuktu"] },
        { id: "ne", name: "Niger", nativeName: "Niger", continent: "africa", flag: "🇳🇪", lat: 17.6078, lon: 8.0817, alt: 2200000, keywords: ["niamey"] },
        { id: "td", name: "Chad", nativeName: "Tchad", continent: "africa", flag: "🇹🇩", lat: 15.4542, lon: 18.7322, alt: 2200000, keywords: ["ndjamena"] },
        { id: "so", name: "Somalia", nativeName: "Soomaaliya", continent: "africa", flag: "🇸🇴", lat: 5.1521, lon: 46.1996, alt: 1800000, keywords: ["mogadishu"] },
        { id: "rw", name: "Rwanda", nativeName: "Rwanda", continent: "africa", flag: "🇷🇼", lat: -1.9403, lon: 29.8739, alt: 500000, keywords: ["kigali"] },
        { id: "mu", name: "Mauritius", nativeName: "Maurice", continent: "africa", flag: "🇲🇺", lat: -20.3484, lon: 57.5522, alt: 350000, keywords: ["port louis"] },
        { id: "us", name: "United States", nativeName: "USA", continent: "north_america", flag: "🇺🇸", lat: 37.0902, lon: -95.7129, alt: 5000000, keywords: ["america", "washington", "new york"] },
        { id: "ca", name: "Canada", nativeName: "Canada", continent: "north_america", flag: "🇨🇦", lat: 56.1304, lon: -106.3468, alt: 4800000, keywords: ["ottawa", "toronto"] },
        { id: "mx", name: "Mexico", nativeName: "México", continent: "north_america", flag: "🇲🇽", lat: 23.6345, lon: -102.5528, alt: 2800000, keywords: ["mexico city"] },
        { id: "br", name: "Brazil", nativeName: "Brasil", continent: "south_america", flag: "🇧🇷", lat: -14.235, lon: -51.9253, alt: 4500000, keywords: ["brasilia", "rio", "sao paulo", "amazon"] },
        { id: "ar", name: "Argentina", nativeName: "Argentina", continent: "south_america", flag: "🇦🇷", lat: -38.4161, lon: -63.6167, alt: 3500000, keywords: ["buenos aires", "patagonia"] },
        { id: "co", name: "Colombia", nativeName: "Colombia", continent: "south_america", flag: "🇨🇴", lat: 4.5709, lon: -74.2973, alt: 1800000, keywords: ["bogota"] },
        { id: "cl", name: "Chile", nativeName: "Chile", continent: "south_america", flag: "🇨🇱", lat: -35.6751, lon: -71.543, alt: 2800000, keywords: ["santiago", "atacama"] },
        { id: "pe", name: "Peru", nativeName: "Perú", continent: "south_america", flag: "🇵🇪", lat: -9.19, lon: -75.0152, alt: 1800000, keywords: ["lima", "machu picchu"] },
        { id: "ve", name: "Venezuela", nativeName: "Venezuela", continent: "south_america", flag: "🇻🇪", lat: 6.4238, lon: -66.5897, alt: 1600000, keywords: ["caracas"] },
        { id: "ec", name: "Ecuador", nativeName: "Ecuador", continent: "south_america", flag: "🇪🇨", lat: -1.8312, lon: -78.1834, alt: 1100000, keywords: ["quito", "galapagos"] },
        { id: "bo", name: "Bolivia", nativeName: "Bolivia", continent: "south_america", flag: "🇧🇴", lat: -16.2902, lon: -63.5887, alt: 1600000, keywords: ["la paz"] },
        { id: "py", name: "Paraguay", nativeName: "Paraguay", continent: "south_america", flag: "🇵🇾", lat: -23.4425, lon: -58.4438, alt: 1200000, keywords: ["asuncion"] },
        { id: "uy", name: "Uruguay", nativeName: "Uruguay", continent: "south_america", flag: "🇺🇾", lat: -32.5228, lon: -55.7658, alt: 950000, keywords: ["montevideo"] },
        { id: "gy", name: "Guyana", nativeName: "Guyana", continent: "south_america", flag: "🇬🇾", lat: 4.8604, lon: -58.9302, alt: 950000, keywords: ["georgetown"] },
        { id: "sr", name: "Suriname", nativeName: "Suriname", continent: "south_america", flag: "🇸🇷", lat: 3.9193, lon: -56.0278, alt: 850000, keywords: ["paramaribo"] },
        { id: "cu", name: "Cuba", nativeName: "Cuba", continent: "north_america", flag: "🇨🇺", lat: 21.5218, lon: -77.7812, alt: 950000, keywords: ["havana"] },
        { id: "do", name: "Dominican Republic", nativeName: "República Dominicana", continent: "north_america", flag: "🇩🇴", lat: 18.7357, lon: -70.1627, alt: 650000, keywords: ["santo domingo"] },
        { id: "ht", name: "Haiti", nativeName: "Haïti", continent: "north_america", flag: "🇭🇹", lat: 18.9712, lon: -72.2852, alt: 600000, keywords: ["port-au-prince"] },
        { id: "gt", name: "Guatemala", nativeName: "Guatemala", continent: "north_america", flag: "🇬🇹", lat: 15.7835, lon: -90.2308, alt: 750000, keywords: ["guatemala city"] },
        { id: "cr", name: "Costa Rica", nativeName: "Costa Rica", continent: "north_america", flag: "🇨🇷", lat: 9.7489, lon: -83.7534, alt: 600000, keywords: ["san jose"] },
        { id: "pa", name: "Panama", nativeName: "Panamá", continent: "north_america", flag: "🇵🇦", lat: 8.5379, lon: -80.7821, alt: 700000, keywords: ["panama canal"] },
        { id: "jm", name: "Jamaica", nativeName: "Jamaica", continent: "north_america", flag: "🇯🇲", lat: 18.1096, lon: -77.2975, alt: 450000, keywords: ["kingston"] },
        { id: "tt", name: "Trinidad and Tobago", nativeName: "Trinidad", continent: "north_america", flag: "🇹🇹", lat: 10.6918, lon: -61.2225, alt: 400000, keywords: ["port of spain"] },
        { id: "au", name: "Australia", nativeName: "Australia", continent: "oceania", flag: "🇦🇺", lat: -25.2744, lon: 133.7751, alt: 3500000, keywords: ["sydney", "melbourne", "outback"] },
        { id: "nz", name: "New Zealand", nativeName: "Aotearoa", continent: "oceania", flag: "🇳🇿", lat: -40.9006, lon: 174.886, alt: 1800000, keywords: ["auckland", "wellington"] },
        { id: "pg", name: "Papua New Guinea", nativeName: "Papua New Guinea", continent: "oceania", flag: "🇵🇬", lat: -6.315, lon: 143.9555, alt: 1400000, keywords: ["port moresby"] },
        { id: "fj", name: "Fiji", nativeName: "Viti", continent: "oceania", flag: "🇫🇯", lat: -17.7134, lon: 178.065, alt: 600000, keywords: ["suva"] },
        { id: "ws", name: "Samoa", nativeName: "Sāmoa", continent: "oceania", flag: "🇼🇸", lat: -13.759, lon: -172.1046, alt: 350000, keywords: ["apia"] },
        { id: "to", name: "Tonga", nativeName: "Tonga", continent: "oceania", flag: "🇹🇴", lat: -21.1789, lon: -175.1982, alt: 350000, keywords: ["nukualofa"] },
        { id: "vu", name: "Vanuatu", nativeName: "Vanuatu", continent: "oceania", flag: "🇻🇺", lat: -15.3767, lon: 166.9592, alt: 500000, keywords: ["port vila"] },
        { id: "sb", name: "Solomon Islands", nativeName: "Solomons", continent: "oceania", flag: "🇸🇧", lat: -9.6457, lon: 160.1562, alt: 700000, keywords: ["honiara"] },
    ];

    window.WORLD_ATLAS = {
        CONTINENTS: CONTINENTS,
        AREAS: WORLD_AREAS,

        getAreasByContinent: function(continentId) {
            if (!continentId || continentId === 'all') {
                return WORLD_AREAS;
            }
            return WORLD_AREAS.filter(a => a.continent === continentId);
        },

        search: function(query, maxResults = 10) {
            if (!query || !query.trim()) return [];
            const q = query.trim().toLowerCase();

            const scored = [];
            for (const area of WORLD_AREAS) {
                let score = 0;
                const name = area.name.toLowerCase();
                const nativeName = (area.nativeName || '').toLowerCase();
                const id = area.id.toLowerCase();
                const cont = area.continent.toLowerCase();

                if (name === q || id === q || nativeName === q) {
                    score = 100;
                } else if (name.startsWith(q) || nativeName.startsWith(q)) {
                    score = 80;
                } else if (name.includes(q) || nativeName.includes(q)) {
                    score = 50;
                } else if (cont.includes(q)) {
                    score = 30;
                } else if (area.keywords && area.keywords.some(k => k.toLowerCase().includes(q))) {
                    score = 25;
                }

                if (score > 0) {
                    scored.push({ area, score });
                }
            }

            scored.sort((a, b) => b.score - a.score);
            return scored.slice(0, maxResults).map(s => s.area);
        }
    };
})();

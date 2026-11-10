"""Sample data for a small Egyptian transport + rental company ("Nile Transport").

Pure data, no Frappe imports. Dates are offsets in days from the day the loader runs (negative = past),
so the demo always shows a realistic mix: valid, expiring-soon and expired documents, overdue services...
"""

BRANCHES = ["فرع القاهرة", "فرع الإسكندرية", "فرع أسوان"]  # become Cost Centers

SUPPLIERS = [
	"ورشة الأمل للصيانة",
	"محطة وطنية للوقود",
	"الإطارات الحديثة",
	"مصر للتأمين - وكيل",
]

CUSTOMERS = [
	"شركة النيل للمقاولات",
	"مصنع الدلتا للأغذية",
	"مجموعة السلام التجارية",
	"فندق الأهرام",
	"عميل تأجير - أحمد سمير",
]

# item_code, item_name, rate
ITEMS = [
	("FLT-OIL-5L", "زيت محرك 5 لتر", 650),
	("FLT-OILFILTER", "فلتر زيت", 180),
	("FLT-AIRFILTER", "فلتر هواء", 220),
	("FLT-BRAKEPAD", "تيل فرامل أمامي", 900),
	("FLT-TIRE-315", "إطار 315/80 R22.5", 9500),
	("FLT-BATTERY", "بطارية 12 فولت 100 أمبير", 4200),
]

# name, vehicle type, tasks: (task, category, km, days, cost)
SERVICE_PLANS = [
	("صيانة الشاحنات الثقيلة", "Heavy Truck", [
		("تغيير زيت المحرك والفلتر", "Oil and Filters", 15000, 180, 1200),
		("فحص الفرامل", "Brakes", 30000, 365, 1500),
		("فحص الإطارات والترصيص", "Tires", 20000, 180, 600),
		("فحص شامل", "Inspection", 60000, 365, 2500),
	]),
	("صيانة السيارات الصغيرة", "Sedan", [
		("تغيير زيت المحرك والفلتر", "Oil and Filters", 8000, 180, 700),
		("فحص الفرامل", "Brakes", 20000, 365, 800),
		("فحص شامل", "Inspection", 40000, 365, 1200),
	]),
]

# full_name, phone, license_no, license_expiry_offset_days, branch_index
DRIVERS = [
	("محمد عبد الله إبراهيم", "01001234501", "CAI-2019-44521", 400, 0),
	("أحمد حسن علي", "01001234502", "CAI-2018-33210", 25, 0),      # expiring soon
	("محمود السيد فتحي", "01001234503", "ALX-2020-11893", 900, 1),
	("خالد مصطفى رمضان", "01001234504", "ALX-2017-90021", -20, 1),  # expired
	("عمر يوسف سليمان", "01001234505", "ASW-2021-55120", 1200, 2),
	("إبراهيم جمال عطية", "01001234506", "CAI-2022-77340", 700, 0),
]

# plate, make, model, year, vehicle type, fuel, odometer, value, color, branch_index, service plan, tank L, payload kg, ownership
VEHICLES = [
	("أ ب ج 4821", "Mercedes", "Actros 1844", 2021, "Heavy Truck", "Diesel", 182000, 4200000, "White", 0, "صيانة الشاحنات الثقيلة", 400, 18000, "Owned"),
	("د هـ و 3377", "Volvo", "FH 460", 2020, "Heavy Truck", "Diesel", 245000, 4600000, "Blue", 0, "صيانة الشاحنات الثقيلة", 450, 20000, "Owned"),
	("ز ح ط 9012", "MAN", "TGS 26.440", 2019, "Heavy Truck", "Diesel", 310000, 3900000, "White", 1, "صيانة الشاحنات الثقيلة", 400, 19000, "Owned"),
	("ي ك ل 1156", "Isuzu", "NPR", 2022, "Light Truck", "Diesel", 96000, 1100000, "White", 1, "", 100, 3500, "Owned"),
	("م ن س 6604", "Toyota", "Hilux", 2023, "Pickup", "Diesel", 54000, 1250000, "Silver", 2, "", 80, 1000, "Leased"),
	("ع ف ص 2290", "Hyundai", "H1 Van", 2022, "Van", "Diesel", 88000, 1050000, "White", 0, "", 75, 1000, "Owned"),
	("ق ر ش 7745", "Toyota", "Corolla", 2023, "Sedan", "Petrol", 41000, 950000, "Grey", 0, "صيانة السيارات الصغيرة", 50, 0, "Owned"),
	("ت ث خ 5538", "Hyundai", "Elantra", 2024, "Sedan", "Petrol", 22000, 1050000, "Black", 0, "صيانة السيارات الصغيرة", 50, 0, "Owned"),
	("ذ ض ظ 8821", "Kia", "Cerato", 2022, "Sedan", "Petrol", 67000, 880000, "White", 1, "صيانة السيارات الصغيرة", 50, 0, "Owned"),
	("غ أ ب 1903", "Toyota", "Coaster", 2021, "Minibus", "Diesel", 134000, 2300000, "White", 2, "", 90, 0, "Owned"),
]

# vehicle index -> {document type: (days since issue, days to expiry)}
# Document types come from the seeded defaults.
VEHICLE_DOCS = {
	0: {"Vehicle Registration": (200, 165), "Vehicle Insurance": (200, 165), "Technical Inspection": (100, 265)},
	1: {"Vehicle Registration": (300, 65), "Vehicle Insurance": (335, 20), "Technical Inspection": (100, 265)},   # insurance expiring soon
	2: {"Vehicle Registration": (370, -5), "Vehicle Insurance": (200, 165), "Technical Inspection": (100, 265)},   # registration EXPIRED
	3: {"Vehicle Registration": (100, 265), "Vehicle Insurance": (100, 265), "Technical Inspection": (100, 265)},
	4: {"Vehicle Registration": (100, 265), "Vehicle Insurance": (100, 265), "Technical Inspection": (60, 305)},
	5: {"Vehicle Registration": (100, 265), "Vehicle Insurance": (100, 265), "Technical Inspection": (100, 265)},
	6: {"Vehicle Registration": (50, 315), "Vehicle Insurance": (50, 315), "Technical Inspection": (50, 315)},
	7: {"Vehicle Registration": (30, 335), "Vehicle Insurance": (30, 335), "Technical Inspection": (30, 335)},
	8: {"Vehicle Registration": (340, 25), "Vehicle Insurance": (340, 25), "Technical Inspection": (340, 25)},      # three expiring soon
	9: {"Vehicle Registration": (100, 265), "Vehicle Insurance": (100, 265), "Technical Inspection": (100, 265)},
}

# driver index -> vehicle index (assignment starting 90 days ago)
ASSIGNMENTS = [(0, 0), (1, 1), (2, 2), (4, 4), (5, 5)]

GPS_DEVICES = [("GPS-860123456780001", 0), ("GPS-860123456780002", 1), ("GPS-860123456780003", 3), ("GPS-860123456780004", 6)]

# serial, brand, size, vehicle index or None, position, cost
TIRES = [
	("TIRE-0001", "Michelin", "315/80 R22.5", 0, "Front Left", 9500),
	("TIRE-0002", "Michelin", "315/80 R22.5", 0, "Front Right", 9500),
	("TIRE-0003", "Bridgestone", "315/80 R22.5", 1, "Front Left", 9200),
	("TIRE-0004", "Bridgestone", "315/80 R22.5", 1, "Front Right", 9200),
	("TIRE-0005", "Michelin", "315/80 R22.5", None, "", 9500),   # in stock
	("TIRE-0006", "Pirelli", "215/55 R17", 6, "Front Left", 3200),
]

# vehicle index, offsets (days ago), litres, rate (EGP/L), odometer step (km since previous)
FUEL_LOGS = [
	(0, 40, 380, 17.5, 450), (0, 25, 360, 17.5, 1900), (0, 10, 390, 17.5, 2000),
	(1, 35, 400, 17.5, 500), (1, 15, 410, 17.5, 2100),
	(3, 30, 70, 17.5, 600), (3, 12, 75, 17.5, 1900),
	(6, 28, 38, 17.25, 500), (6, 9, 40, 17.25, 600),
]

# vehicle index, type, priority, status, days ago opened, tasks [(desc, cost)], parts [(item, qty)], other cost, submitted?
WORK_ORDERS = [
	(0, "Preventive", "Medium", "Completed", 20, [("تغيير زيت المحرك والفلتر", 400)], [("FLT-OIL-5L", 3), ("FLT-OILFILTER", 1)], 0, True),
	(1, "Corrective", "High", "In Progress", 2, [("إصلاح تسريب الفرامل", 800)], [("FLT-BRAKEPAD", 2)], 150, False),
	(2, "Inspection", "Low", "Open", 0, [("فحص قبل تجديد الترخيص", 0)], [], 0, False),
]

# vehicle idx, driver idx, type, customer idx, from, to, rate basis, rate, cargo kg, cargo text, km, days ago start (0 = future), submit
TRIPS = [
	(0, 0, "Customer Haulage", 0, "القاهرة", "الإسكندرية", "Fixed", 18000, 16000, "حديد تسليح", 220, 18, True),
	(3, 5, "Customer Haulage", 1, "العاشر من رمضان", "القاهرة", "Per Km", 28, 2800, "مواد غذائية", 60, 10, True),
	(5, 5, "Internal", None, "القاهرة", "السويس", "Fixed", 0, 0, "نقل معدات للفرع", 140, 5, False),
	(4, 4, "Internal", None, "أسوان", "الأقصر", "Fixed", 0, 0, "تنقل موظفين", 220, -3, False),
]

# vehicle idx, customer idx, start offset days, end offset days, daily rate, free km/day, extra km rate, submit
RENTALS = [
	(7, 4, -2, 3, 1400, 200, 5, True),
	(9, 3, 7, 10, 3200, 0, 0, True),
]

# vehicle idx, days ago, violation, amount, authority, who pays
FINES = [
	(0, 50, "تجاوز السرعة المقررة", 900, "المرور", "Driver"),
	(3, 22, "الانتظار في مكان ممنوع", 300, "المرور", "Company"),
	(7, 4, "تجاوز السرعة المقررة", 500, "المرور", "Customer"),
]

# vehicle idx, driver idx, days ago, type, severity, fault, description
INCIDENTS = [
	(1, 1, 60, "Collision", "Moderate", "Third Party", "اصطدام من الخلف عند إشارة المرور - أضرار في الصدام الخلفي"),
	(8, None, 15, "Breakdown", "Minor", "Unknown", "تعطل في الطريق الصحراوي - عطل في طلمبة الوقود"),
]

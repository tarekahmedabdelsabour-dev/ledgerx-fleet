# بيانات تجريبية لشركة نقل وتأجير (Nile Transport)

## الطريقة الأولى (الأسرع): تحميل كل شيء مرة واحدة
```
cd ~/frappe-bench-v16/apps/ledgerx_fleet && git pull origin main
cd ~/frappe-bench-v16
bench --site mysite.localhost backup
bench --site mysite.localhost execute ledgerx_fleet.demo.loader.load --kwargs "{'company': 'اسم شركتك بالظبط'}"
cat sites/mysite.localhost/private/files/fleet-demo-report.txt
```
الترتيب اللي بيتنفذ: الإعدادات ← مراكز التكلفة (3 فروع) ← موردين وعملاء وقطع غيار ← خطط الصيانة ← السائقين ← المركبات (10) ← المستندات (فيها منتهي وقريب الانتهاء) ← التكليفات والتتبع والإطارات ← الوقود ← أوامر الشغل ← الرحلات ← التأجير ← المخالفات والحوادث.
تقدر تشغله مرتين: اللي موجود بيتخطاه. التقرير بيوضح اللي اتعمل واللي فشل.
لو عاوزه كمسودات بدون اعتماد: أضف `'submit': 0`.

## الطريقة الثانية: Data Import يدويا (للجداول البسيطة)
ملفات في مجلد `demo_csv`: driver.csv و vehicle.csv.
1. افتح Data Import ← New.
2. Document Type: Driver (ثم Vehicle). Import Type: Insert New Records.
3. Download Template لو عاوز تشوف الأعمدة، وارفع الملف.
4. Start Import وراجع Status والأخطاء.
ملاحظة: الجداول اللي فيها جداول فرعية (أوامر الشغل، الرحلات، العقود) الأفضل تتعمل بالطريقة الأولى. رتّب الاستيراد: Driver ← Vehicle ← Fleet Document.

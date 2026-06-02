# Jarvis Telegram Bot - Shaxsiy Yordamchi

Ushbu loyiha sizning shaxsiy Telegram yordamchingiz bo'lib, quyidagi integratsiyalarni amalga oshiradi:
* **Google Calendar:** Uchrashuvlarni ko'rish va rejalashtirish.
* **Gmail:** Pochtangizdagi yangi xatlarni avtomatik saralash va qisqa mazmunini yuborish.
* **Notion:** Rejalar va vazifalarni boshqarish.
* **Google Drive:** Fayllarni izlash, yuklab olish va yuklash.

---

## 🛠️ O'rnatish va Sozlash Ko'rsatmalari

### 1. Dasturni Tayyorlash (Python)
Agar kompyuteringizda Python o'rnatilmagan bo'lsa, uni [python.org](https://www.python.org/) saytidan yuklab oling va o'rnating. Mac tizimida Xcode Command Line Tools o'rnatish orqali ham Python'ga ega bo'lishingiz mumkin:
```bash
xcode-select --install
```

Loyiha papkasiga o'ting va zarur kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

---

### 2. Telegram Botini Yaratish
1. Telegram'da [@BotFather](https://t.me/BotFather) botiga o'ting va `/newbot` buyrug'ini bering.
2. Botga nom va username bering, so'ngra **API Token**'ni nusxalab oling.
3. Shaxsiy Telegram ID raqamingizni aniqlash uchun [@userinfobot](https://t.me/userinfobot) botiga start bosing va ID raqamingizni oling.

---

### 3. Google API Kalitlarini Olish (Calendar, Gmail, Drive)
1. [Google Cloud Console](https://console.cloud.google.com/) sahifasiga kiring.
2. Yangi loyiha yarating (Create Project).
3. **API & Services -> Library** bo'limiga kiring va quyidagilarni faollashtiring (Enable):
   * **Google Calendar API**
   * **Gmail API**
   * **Google Drive API**
4. **OAuth Consent Screen** (Ruxsat berish ekrani) bo'limiga kiring:
   * **User Type:** External (Tashqi)
   * App name va Email manzilini kiriting.
   * **Test Users** bo'limiga o'z shaxsiy Gmail manzilingizni qo'shing (bu juda muhim, aks holda bot hisobingizga kira olmaydi).
5. **Credentials** (Kirish ma'lumotlari) bo'limiga o'ting:
   * **Create Credentials -> OAuth Client ID** ni tanlang.
   * **Application Type:** Desktop App (Ish stoli ilovasi) qilib belgilang.
   * Yaratilgandan so'ng, konfiguratsiyani JSON formatida yuklab oling.
   * Yuklab olingan fayl nomini `credentials.json` deb o'zgartirib, bot loyihasining **asosiy papkasiga** joylashtiring.

---

### 4. Notion Integratsiyasini Sozlash
1. [Notion My Integrations](https://www.notion.so/my-integrations) sahifasiga kiring va yangi integratsiya yarating (**Create new integration**).
2. Integratsiya uchun ruxsatnomani (Secret Token) nusxalab oling.
3. Notion'da yangi ma'lumotlar bazasi (Database) yarating. Bazada kamida quyidagi ustunlar (Properties) bo'lishi kerak:
   * **Name** (turi: Title) - reja nomi uchun.
   * **Status** (turi: Checkbox yoki Status) - rejaning bajarilgan holati uchun.
4. Bazaning sozlamalaridan integratsiyangizga ruxsat bering (**Connect to** bo'limidan yaratgan integratsiyangizni tanlang).
5. Ma'lumotlar bazasining ID raqamini oling. Buning uchun bazani brauzerda oching va URL manzildan ID'ni oling:
   `https://www.notion.so/workspace_name/DATABASE_ID?v=...` (DATABASE_ID qismi 32 ta belgidan iborat).

---

### 5. Muhit Sozlamalari (.env)
Loyihaning asosiy papkasidagi `.env.template` faylini nusxalab, yangi `.env` faylini yarating:
```bash
cp .env.template .env
```
Faylni matn muharririda oching va nusxalangan ma'lumotlarni kiriting:
```env
TELEGRAM_BOT_TOKEN=sizning_bot_tokeningiz
TELEGRAM_OWNER_ID=sizning_telegram_idingiz
NOTION_TOKEN=sizning_notion_integration_secretingiz
NOTION_DATABASE_ID=sizning_notion_database_idingiz

# Sun'iy intellekt orqali xatlarni saralash (Ixtiyoriy)
GEMINI_API_KEY=sizning_gemini_api_kalitingiz
```

---

## 🚀 Botni Ishga Tushirish

Botni quyidagi buyruq orqali ishga tushiring:
```bash
python bot.py
```

> [!NOTE]
> **Birinchi marta ishga tushirishda:** Bot Google hisobingizga kirish uchun brauzerni avtomatik ochadi. Google hisobingizga kiring va botga Calendar, Gmail hamda Drive fayllaringizni boshqarish uchun ruxsat bering. Tasdiqlangandan so'ng, loyihada `token.json` fayli yaratiladi va keyingi safar ruxsat so'ramaydi.

---

## 🔒 Xavfsizlik Eslatmasi (Security TODO)
* `credentials.json`, `token.json` va `.env` fayllari shaxsiy kalitlaringizni saqlaydi. Ularni hech qachon GitHub yoki ochiq tarmoqlarga yuklamang (`.gitignore` fayliga qo'shilganiga ishonch hosil qiling).
* Bot faqat `.env` da belgilangan `TELEGRAM_OWNER_ID` egasigagina javob beradi. Chet ellik/begona foydalanuvchilar buyruq yuborganida ruxsat berilmaydi.

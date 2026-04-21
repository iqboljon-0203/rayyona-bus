# 🚌 Rayyona Bus Bot

Toshkent — Moskva va boshqa yo'nalishlar bo'yicha avtobus xizmati uchun Telegram bot.

## 🚀 Funksiyalar
- Yo'nalishlar va narxlarni ko'rish.
- Onlayn buyurtma berish.
- Admin panel (narxlarni o'zgartirish, statistikani ko'rish).
- Avtomatik reklamalarni guruhlarga yuborish (Scheduler).

## 🛠 O'rnatish

1.  Loyihani yuklab oling:
    ```bash
    git clone <repository_url>
    cd rayyona-bus
    ```

2.  Kutubxonalarni o'rnating:
    ```bash
    pip install -r requirements.txt
    ```

3.  `.env` faylini yarating va quyidagi ma'lumotlarni to'ldiring:
    ```env
    BOT_TOKEN=Sizning_bot_tokeningiz
    ADMIN_IDS=Sizning_telegram_id_yingiz
    ORDERS_GROUP_ID=Buyurtmalar_tushadigan_gruppa_id
    ```

4.  Botni ishga tushiring:
    ```bash
    python bot.py
    ```

## 📝 Muallif
- [@iqboljon](https://t.me/iqboljon)

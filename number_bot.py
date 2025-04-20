# -*- coding: utf-8 -*-
import telebot
from telebot import types
from telebot.types import ReplyParameters, ChatMember # Додано ChatMember та ReplyParameters
import logging
import time
import re
import requests # Додано для можливого майбутнього використання API курсів
import traceback
import decimal # Використовуємо Decimal для фінансових розрахунків

# --- Константи та налаштування ---
# ВАШ ТОКЕН (ЗАМІНІТЬ СПРАВЖНІМ ТОКЕНОМ ПЕРЕД ЗАПУСКОМ)
BOT_TOKEN = "7533433379:AAFRvJMWalyoK2dNa_027V2I-hsXIJZ49J0" # !!! ЗАМІНІТЬ ЦЕ СПРАВЖНІМ ТОКЕНОМ !!!

# !!! ВАЖЛИВО: ВКАЖІТЬ ID АБО @USERNAME ВАШОГО КАНАЛУ !!!
CHANNEL_ID = "@VirtualNumberNews" # Наприклад: "@my_cool_channel" або -1001234567890
# !!! ВАЖЛИВО: ВКАЖІТЬ ПОВНЕ ПОСИЛАННЯ НА ВАШ КАНАЛ !!!
CHANNEL_URL = "https://t.me/VirtualNumberNews" # Наприклад: "https://t.me/my_cool_channel"

SUPPORT_CHAT_ID = -1002434683387      # ID чату підтримки
CONFIRMATION_CHAT_ID = -1002562104639 # ID чату для підтвердження платежів
ADMIN_ID = 1602736674            # ID головного адміна (власника) - може бути не потрібним, якщо керування йде через чати

PAYMENT_DETAILS = {
    'Privat24': '4149 6090 5872 2077',
    'Mono': '4441 1110 0101 3626',
    'Pumb': '5355 4252 1235 0423',
    'Abank': '4149 2504 4820 0252',
    'Crypto': 'USDT (TRC-20): TJWSS4QGKtqzNfUDasVrjAtZ6p25ucFrB7',
}

# !!! ВАЖЛИВО: Оновіть ці курси реальними значеннями! !!!
# Рекомендована структура для конвертації через UAH:
# Скільки одиниць ЦІЄЇ валюти коштує 1 UAH
EXCHANGE_RATES_FROM_UAH = {
    'UAH': decimal.Decimal('1.0'),
    'USD': decimal.Decimal('1.0') / decimal.Decimal('40.50'), # ~0.02469 (Приклад!)
    'RUB': decimal.Decimal('1.0') / decimal.Decimal('0.45'),  # ~2.22222 (Приклад!)
}
# Скільки UAH коштує 1 одиниця ЦІЄЇ валюти
EXCHANGE_RATES_TO_UAH = {
    'UAH': decimal.Decimal('1.0'),
    'USD': decimal.Decimal('40.50'), # (Приклад!)
    'RUB': decimal.Decimal('0.45'),  # (Приклад!)
}


ABOUT_TEXT_RU = "Мы предоставляем услуги виртуальных номеров."
ABOUT_TEXT_UK = "Ми надаємо послуги віртуальних номерів."
ABOUT_TEXT_EN = "We provide virtual number services."

DB_NAME = 'user_data.db' # Назва файлу бази даних (якщо використовується SQLite)
logger = telebot.logger
telebot.logger.setLevel(logging.INFO) # Рівень логування

# Спеціальний символ для відхилення без причини
REJECT_WITHOUT_REASON_SYMBOL = "-"

texts = {
    'ru': {
        'start_greeting': "👋 Привет! Я твой бот для работы с номерами.\nБаланс: {balance} {currency}\nID: {user_id}",
        'main_menu': "Главное меню:",
        'profile': "👤 Профиль",
        'about': "ℹ️ О нас",
        'settings': "⚙️ Настройки",
        'support': "💬 Поддержка",
        'buy_number': "🛒 Купить номер",
        'deposit': "💰 Пополнить",
        'profile_info': "👤 Ваш профиль:\nID: {user_id}\nБаланс: {balance} {currency}",
        'settings_menu': "⚙️ Настройки:",
        'change_lang': "🌐 Сменить язык",
        'change_curr': "💱 Сменить валюту",
        'select_lang': "Выберите язык:",
        'lang_changed': "✅ Язык изменен на Русский.",
        'select_curr': "Выберите валюту:",
        'curr_changed': "✅ Валюта изменена на {currency}. Баланс сконвертирован: {balance} {currency_symbol}", # Оновлено
        'support_request': "✍️ Напишите ваше сообщение для поддержки:",
        'support_sent': "✅ Ваше сообщение отправлено в поддержку.",
        'support_reply': "✉️ Ответ от поддержки:\n\n{reply_text}",
        'support_message_to_admin': "📌 Support Request:\nUser ID: {user_id}\nUser Tag: @{username}\n\nMessage:\n{message_text}",
        'choose_country': "🌍 Выберите страну для номера:",
        'country_selected': "Вы выбрали {country}. Функционал покупки пока в разработке.",
        'back': "⬅️ Назад",
        'lang_ru': "🇷🇺 Русский",
        'lang_uk': "🇺🇦 Українська",
        'lang_en': "🇬🇧 English",
        'curr_usd': "🇺🇸 USD",
        'curr_uah': "🇺🇦 UAH",
        'curr_rub': "🇷🇺 RUB",
        'country_ua': "🇺🇦 Украина",
        'country_de': "🇩🇪 Германия",
        'country_pl': "🇵🇱 Польша",
        'request_deposit_amount': "➡️ Введите сумму для пополнения в UAH (только число, например 100 или 50.5):", # Уточнено валюту
        'invalid_deposit_amount': "❌ Неверная сумма. Пожалуйста, введите положительное число (например, 100 или 50.5).",
        'select_payment_method': "👇 Выберите способ оплаты для суммы {amount} {currency}:",
        'payment_instructions': """
✅ **Для пополнения на {amount} {currency} через {method}:**

Реквизиты: `{details}`

❗️ **ВАЖНО:**
1. Совершите перевод ТОЧНОЙ суммы.
2. После оплаты **обязательно** отправьте скриншот/фото чека сюда в бот.
3. Оплата обрабатывается вручную, ожидайте подтверждения.

💬 Не проходит оплата?
- Выберите другой банк или напишите в поддержку ('Поддержка').
        """,
        'awaiting_screenshot_message': "⏳ Ожидаю скриншот/фото подтверждения оплаты...",
        'screenshot_received_admin_notification': "✅ Скриншот получен! Отправил администратору на проверку. Ожидайте зачисления.",
        'admin_confirmation_message': """
🧾 **Запрос на пополнение!**

User: {user_id} (@{username})
Заявлено: {amount} {currency}
Метод: {method}

⏳ *Ожидает подтверждения...*
        """,
        'admin_approve_prompt': "✍️ Введите точную сумму зачисления в {currency} для пользователя {user_id} ({username}).\nЗаявлено: {requested_amount} {currency}.\n(Баланс будет пополнен в валюте пользователя: {user_currency})", # Оновлено
        'admin_reject': "❌ Отклонить",
        'admin_reject_comment': "📝 Отклонить с причиной", # Змінено назву кнопки
        'admin_approve': "✅ Зачислить", # Змінено назву кнопки
        'deposit_approved_user': "✅ Ваше пополнение на сумму {amount} {currency} подтверждено! Баланс обновлен.", # Оновлено текст
        'deposit_rejected_user': "❌ Ваше пополнение отклонено администратором (заявка: {amount} {currency}).", # Додано суму заявки
        'deposit_rejected_with_comment_user': "❌ Ваше пополнение отклонено (заявка: {amount} {currency}).\nПричина: {reason}", # Додано суму заявки
        'admin_rejection_reason_prompt': "✍️ Введите причину отклонения для пользователя {user_id}.\nОтправьте '{symbol}' (минус), если причина не нужна.",
        'admin_action_confirmed_approve': "✅ Платеж одобрен. Пользователю {user_id} зачислено {credited_amount} {currency}.", # Оновлено
        'admin_action_confirmed_reject': "❌ Платеж отклонен (без причины). Пользователь {user_id} уведомлен.",
        'admin_action_confirmed_reject_comment': "📝 Платеж отклонен с комментарием. Пользователь {user_id} уведомлен.",
        'deposit_cancelled': "🚫 Процесс пополнения отменен.",
        'invalid_step': "😕 Похоже, вы пытаетесь сделать что-то не то. Попробуйте начать заново или используйте /cancel.", # Додано про /cancel
        'callback_error': "⚠️ Произошла ошибка при обработке вашего выбора. Попробуйте еще раз.",
        'payment_method_Privat24': "Privat24",
        'payment_method_Mono': "Monobank",
        'payment_method_Pumb': "ПУМБ",
        'payment_method_Abank': "А-Банк",
        'payment_method_Crypto': "Crypto",
        'cancel_deposit': "🚫 Отменить пополнение",
        'back_to_methods': "⬅️ К выбору метода",
        'unknown_command': "😕 Неизвестная команда или текст.",
        'error_sending_support': "❌ Произошла ошибка при отправке сообщения. Попробуйте позже.",
        'support_reply_failed': "⚠️ Не удалось отправить ответ пользователю {user_id}: {e}",
        'support_user_not_found': "⚠️ Не удалось найти исходного пользователя для этого ответа.",
        'support_reply_sent': "✅ Ответ отправлен пользователю {user_id}",
        'start_needed': "Пожалуйста, введите /start для начала работы.",
        'callback_user_not_found': "Пожалуйста, нажмите /start",
        'admin_not_awaiting_reason': "Вы не находитесь в процессе отклонения с причиной.", # Оновлено
        'admin_not_awaiting_approve_amount': "Вы не находитесь в процессе ввода суммы зачисления.", # NEW
        'admin_not_awaiting_support_reply': "Вы не находитесь в процессе ответа пользователю.", # NEW
        'invalid_approve_amount': "❌ Неверная сумма. Введите положительное число (например, 100 или 50.5).", # NEW
        'balance_update_failed_admin': "⚠️ Не удалось обновить баланс пользователя {user_id}.", # NEW
        'currency_conversion_error': "⚠️ Ошибка конвертации валюты из {from_curr} в {to_curr}. Проверьте курсы.", # NEW
        'admin_support_reply_prompt': "✍️ Введите текст ответа для пользователя {user_id} (@{username}):", # NEW
        'support_reply_button': "✉️ Ответить", # NEW
        'cancel_action': "🚫 Действие отменено.", # NEW - Текст для /cancel
        'action_cancelled_user': "🚫 Действие отменено.", # NEW - Текст для /cancel користувача
        'no_active_action': "Нет активного действия для отмены.", # NEW - Текст для /cancel адміна без стану
        'ABOUT_TEXT_RU': ABOUT_TEXT_RU,
        # --- Тексти для перевірки підписки ---
        'subscribe_prompt': "❗️ Для использования бота необходимо подписаться на наш канал.",
        'subscribe_button': "➡️ Подписаться",
        'check_subscription_button': "✅ Я подписался / Проверить подписку",
        'subscription_needed': "❌ Подписка не найдена. Пожалуйста, подпишитесь на канал и нажмите кнопку проверки.",
        'subscription_verified': "✅ Спасибо за подписку! Теперь вы можете пользоваться ботом.",
    },
    'uk': {
        'start_greeting': "👋 Привіт! Я твій бот для роботи з номерами.\nБаланс: {balance} {currency}\nID: {user_id}",
        'main_menu': "Головне меню:",
        'profile': "👤 Профіль",
        'about': "ℹ️ Про нас",
        'settings': "⚙️ Налаштування",
        'support': "💬 Підтримка",
        'buy_number': "🛒 Купити номер",
        'deposit': "💰 Поповнити",
        'profile_info': "👤 Ваш профіль:\nID: {user_id}\nБаланс: {balance} {currency}",
        'settings_menu': "⚙️ Налаштування:",
        'change_lang': "🌐 Змінити мову",
        'change_curr': "💱 Змінити валюту",
        'select_lang': "Виберіть мову:",
        'lang_changed': "✅ Мову змінено на Українську.",
        'select_curr': "Виберіть валюту:",
        'curr_changed': "✅ Валюту змінено на {currency}. Баланс сконвертовано: {balance} {currency_symbol}", # Оновлено
        'support_request': "✍️ Напишіть ваше повідомлення для підтримки:",
        'support_sent': "✅ Ваше повідомлення відправлено до підтримки.",
        'support_reply': "✉️ Відповідь від підтримки:\n\n{reply_text}",
        'support_message_to_admin': "📌 Запит до підтримки:\nUser ID: {user_id}\nUser Tag: @{username}\n\nПовідомлення:\n{message_text}",
        'choose_country': "🌍 Виберіть країну для номера:",
        'country_selected': "Ви обрали {country}. Функціонал купівлі поки в розробці.",
        'back': "⬅️ Назад",
        'lang_ru': "🇷🇺 Російська",
        'lang_uk': "🇺🇦 Українська",
        'lang_en': "🇬🇧 English",
        'curr_usd': "🇺🇸 USD",
        'curr_uah': "🇺🇦 UAH",
        'curr_rub': "🇷🇺 RUB",
        'country_ua': "🇺🇦 Україна",
        'country_de': "🇩🇪 Німеччина",
        'country_pl': "🇵🇱 Польща",
        'request_deposit_amount': "➡️ Введіть суму для поповнення в UAH (число, наприклад 100 або 255.5):", # Уточнено валюту
        'invalid_deposit_amount': "❌ Невірна сума. Будь ласка, введіть додатне число (наприклад, 100 або 255.5).",
        'select_payment_method': "👇 Виберіть спосіб оплати для суми {amount} {currency}:",
        'payment_instructions': """
✅ **Для поповнення на {amount} {currency} через {method}:**

Реквізити: `{details}`

❗️ **ВАЖЛИВО:**
1. Здійсніть переказ ТОЧНОЇ суми.
2. Після оплати **обов'язково** надішліть скріншот/фото чека сюди в бот.
3. Оплата обробляється вручну, очікуйте на підтвердження.

💬 Не проходить оплата?
- Оберіть інший банк або напишіть у підтримку (кнопка 'Підтримка').
        """,
        'awaiting_screenshot_message': "⏳ Очікую на скріншот/фото підтвердження оплати...",
        'screenshot_received_admin_notification': "✅ Скріншот отримано! Відправив адміністратору на перевірку. Очікуйте на зарахування.",
        'admin_confirmation_message': """
🧾 **Запит на поповнення!**

User: {user_id} (@{username})
Заявлено: {amount} {currency}
Метод: {method}

⏳ *Очікує підтвердження...*
        """,
        'admin_approve_prompt': "✍️ Введіть точну суму зарахування в {currency} для користувача {user_id} (@{username}).\nЗаявлено: {requested_amount} {currency}.\n(Баланс буде поповнено у валюті користувача: {user_currency})", # Оновлено
        'admin_reject': "❌ Відхилити",
        'admin_reject_comment': "📝 Відхилити з причиною", # Змінено назву кнопки
        'admin_approve': "✅ Зарахувати", # Змінено назву кнопки
        'deposit_approved_user': "✅ Ваше поповнення на суму {amount} {currency} підтверджено! Баланс оновлено.", # Оновлено текст
        'deposit_rejected_user': "❌ Ваше поповнення відхилено адміністратором (заявка: {amount} {currency}).", # Додано суму заявки
        'deposit_rejected_with_comment_user': "❌ Ваше поповнення відхилено (заявка: {amount} {currency}).\nПричина: {reason}", # Додано суму заявки
        'admin_rejection_reason_prompt': "✍️ Введіть причину відхилення для користувача {user_id}.\nНадішліть '{symbol}' (мінус), якщо причина не потрібна.",
        'admin_action_confirmed_approve': "✅ Платіж схвалено. Користувачу {user_id} зараховано {credited_amount} {currency}.", # Оновлено
        'admin_action_confirmed_reject': "❌ Платіж відхилено (без причини). Користувача {user_id} сповіщено.",
        'admin_action_confirmed_reject_comment': "📝 Платіж відхилено з коментарем. Користувача {user_id} сповіщено.",
        'deposit_cancelled': "🚫 Процес поповнення скасовано.",
        'invalid_step': "😕 Схоже, ви намагаєтеся зробити щось не те. Спробуйте почати заново або використайте /cancel.", # Додано про /cancel
        'callback_error': "⚠️ Сталася помилка при обробці вашого вибору. Спробуйте ще раз.",
        'payment_method_Privat24': "Privat24",
        'payment_method_Mono': "Monobank",
        'payment_method_Pumb': "ПУМБ",
        'payment_method_Abank': "А-Банк",
        'payment_method_Crypto': "Crypto",
        'cancel_deposit': "🚫 Скасувати поповнення",
        'back_to_methods': "⬅️ До вибору методу",
        'unknown_command': "😕 Невідома команда або текст.",
        'error_sending_support': "❌ Сталася помилка під час надсилання повідомлення. Спробуйте пізніше.",
        'support_reply_failed': "⚠️ Не вдалося надіслати відповідь користувачу {user_id}: {e}",
        'support_user_not_found': "⚠️ Не вдалося знайти початкового користувача для цієї відповіді.",
        'support_reply_sent': "✅ Відповідь надіслано користувачу {user_id}",
        'start_needed': "Будь ласка, введіть /start для початку роботи.",
        'callback_user_not_found': "Будь ласка, натисніть /start",
        'admin_not_awaiting_reason': "Ви не перебуваєте в процесі відхилення з причиною.", # Оновлено
        'admin_not_awaiting_approve_amount': "Ви не перебуваєте в процесі введення суми зарахування.", # NEW
        'admin_not_awaiting_support_reply': "Ви не перебуваєте в процесі відповіді користувачу.", # NEW
        'invalid_approve_amount': "❌ Невірна сума. Введіть додатне число (наприклад, 100 або 50.5).", # NEW
        'balance_update_failed_admin': "⚠️ Не вдалося оновити баланс користувача {user_id}.", # NEW
        'currency_conversion_error': "⚠️ Помилка конвертації валюти з {from_curr} в {to_curr}. Перевірте курси.", # NEW
        'admin_support_reply_prompt': "✍️ Введіть текст відповіді для користувача {user_id} (@{username}):", # NEW
        'support_reply_button': "✉️ Відповісти", # NEW
        'cancel_action': "🚫 Дію скасовано.", # NEW - Текст для /cancel
        'action_cancelled_user': "🚫 Дію скасовано.", # NEW - Текст для /cancel користувача
        'no_active_action': "Немає активної дії для скасування.", # NEW - Текст для /cancel адміна без стану
        'ABOUT_TEXT_UK': ABOUT_TEXT_UK,
        # --- Тексти для перевірки підписки ---
        'subscribe_prompt': "❗️ Для користування ботом необхідно підписатися на наш канал.",
        'subscribe_button': "➡️ Підписатись",
        'check_subscription_button': "✅ Я підписався / Перевірити підписку",
        'subscription_needed': "❌ Підписку не знайдено. Будь ласка, підпишіться на канал та натисніть кнопку перевірки.",
        'subscription_verified': "✅ Дякуємо за підписку! Тепер ви можете користуватися ботом.",
    },
    'en': {
        'start_greeting': "👋 Hi! I'm your number bot.\nBalance: {balance} {currency}\nID: {user_id}",
        'main_menu': "Main Menu:",
        'profile': "👤 Profile",
        'about': "ℹ️ About Us",
        'settings': "⚙️ Settings",
        'support': "💬 Support",
        'buy_number': "🛒 Buy Number",
        'deposit': "💰 Deposit",
        'profile_info': "👤 Your Profile:\nID: {user_id}\nBalance: {balance} {currency}",
        'settings_menu': "⚙️ Settings:",
        'change_lang': "🌐 Change Language",
        'change_curr': "💱 Change Currency",
        'select_lang': "Select language:",
        'lang_changed': "✅ Language changed to English.",
        'select_curr': "Select currency:",
        'curr_changed': "✅ Currency changed to {currency}. Balance converted: {balance} {currency_symbol}", # Updated
        'support_request': "✍️ Write your message for support:",
        'support_sent': "✅ Your message has been sent to support.",
        'support_reply': "✉️ Reply from support:\n\n{reply_text}",
        'support_message_to_admin': "📌 Support Request:\nUser ID: {user_id}\nUser Tag: @{username}\n\nMessage:\n{message_text}",
        'choose_country': "🌍 Choose country for the number:",
        'country_selected': "You selected {country}. Purchase functionality is under development.",
        'back': "⬅️ Back",
        'lang_ru': "🇷🇺 Russian",
        'lang_uk': "🇺🇦 Ukrainian",
        'lang_en': "🇬🇧 English",
        'curr_usd': "🇺🇸 USD",
        'curr_uah': "🇺🇦 UAH",
        'curr_rub': "🇷🇺 RUB",
        'country_ua': "🇺🇦 Ukraine",
        'country_de': "🇩🇪 Germany",
        'country_pl': "🇵🇱 Poland",
        'request_deposit_amount': "➡️ Enter the amount to deposit in UAH (numbers only, e.g., 100 or 50.5):", # Clarified currency
        'invalid_deposit_amount': "❌ Invalid amount. Please enter a positive number (e.g., 100 or 50.5).",
        'select_payment_method': "👇 Choose payment method for {amount} {currency}:",
        'payment_instructions': """
✅ **To deposit {amount} {currency} via {method}:**

Details: `{details}`

❗️ **IMPORTANT:**
1. Transfer the EXACT amount.
2. After payment, **must** send a screenshot/photo of the receipt here in the bot.
3. Payment is processed manually, please wait for confirmation.

💬 Payment issues?
- Choose another bank or contact support ('Support' button).
        """,
        'awaiting_screenshot_message': "⏳ Waiting for the payment confirmation screenshot/photo...",
        'screenshot_received_admin_notification': "✅ Screenshot received! Sent to the administrator for verification. Please wait for the credit.",
        'admin_confirmation_message': """
🧾 **Deposit Request!**

User: {user_id} (@{username})
Requested: {amount} {currency}
Method: {method}

⏳ *Awaiting confirmation...*
        """,
        'admin_approve_prompt': "✍️ Enter the exact credit amount in {currency} for user {user_id} ({username}).\nRequested: {requested_amount} {currency}.\n(Balance will be credited in user's currency: {user_currency})", # Updated
        'admin_reject': "❌ Reject",
        'admin_reject_comment': "📝 Reject with reason", # Changed button text
        'admin_approve': "✅ Credit", # Changed button text
        'deposit_approved_user': "✅ Your deposit of {amount} {currency} has been confirmed! Balance updated.", # Updated text
        'deposit_rejected_user': "❌ Your deposit was rejected by the administrator (request: {amount} {currency}).", # Added request amount
        'deposit_rejected_with_comment_user': "❌ Your deposit was rejected (request: {amount} {currency}).\nReason: {reason}", # Added request amount
        'admin_rejection_reason_prompt': "✍️ Enter the rejection reason for user {user_id}.\nSend '{symbol}' (minus) if no reason is needed.",
        'admin_action_confirmed_approve': "✅ Payment approved. User {user_id} credited with {credited_amount} {currency}.", # Updated
        'admin_action_confirmed_reject': "❌ Payment rejected (no reason provided). User {user_id} notified.",
        'admin_action_confirmed_reject_comment': "📝 Payment rejected with comment. User {user_id} notified.",
        'deposit_cancelled': "🚫 Deposit process cancelled.",
        'invalid_step': "😕 It seems you're trying to do something out of sequence. Please try starting again or use /cancel.", # Added /cancel hint
        'callback_error': "⚠️ An error occurred while processing your selection. Please try again.",
        'payment_method_Privat24': "Privat24",
        'payment_method_Mono': "Monobank",
        'payment_method_Pumb': "PUMB",
        'payment_method_Abank': "A-Bank",
        'payment_method_Crypto': "Crypto",
        'cancel_deposit': "🚫 Cancel Deposit",
        'back_to_methods': "⬅️ Back to Methods",
        'unknown_command': "😕 Unknown command or text.",
        'error_sending_support': "❌ An error occurred while sending the message. Please try again later.",
        'support_reply_failed': "⚠️ Failed to send reply to user {user_id}: {e}",
        'support_user_not_found': "⚠️ Could not find the original user for this reply.",
        'support_reply_sent': "✅ Reply sent to user {user_id}",
        'start_needed': "Please type /start to begin.",
        'callback_user_not_found': "Please press /start",
        'admin_not_awaiting_reason': "You are not currently in the process of rejecting with reason.", # Updated
        'admin_not_awaiting_approve_amount': "You are not currently in the process of entering the crediting amount.", # NEW
        'admin_not_awaiting_support_reply': "You are not currently in the process of replying to a user.", # NEW
        'invalid_approve_amount': "❌ Invalid amount. Enter a positive number (e.g., 100 or 50.5).", # NEW
        'balance_update_failed_admin': "⚠️ Failed to update user's balance {user_id}.", # NEW
        'currency_conversion_error': "⚠️ Currency conversion error from {from_curr} to {to_curr}. Please check exchange rates.", # NEW
        'admin_support_reply_prompt': "✍️ Enter the reply text for user {user_id} (@{username}):", # NEW
        'support_reply_button': "✉️ Reply", # NEW
        'cancel_action': "🚫 Action cancelled.", # NEW - Текст для /cancel
        'action_cancelled_user': "🚫 Action cancelled.", # NEW - Текст для /cancel user
        'no_active_action': "No active action to cancel.", # NEW - Текст для /cancel admin no state
        'ABOUT_TEXT_EN': ABOUT_TEXT_EN,
         # --- Texts for subscription check ---
        'subscribe_prompt': "❗️ To use the bot, you need to subscribe to our channel.",
        'subscribe_button': "➡️ Subscribe",
        'check_subscription_button': "✅ I subscribed / Check subscription",
        'subscription_needed': "❌ Subscription not found. Please subscribe to the channel and click the check button.",
        'subscription_verified': "✅ Thank you for subscribing! You can now use the bot.",
    }
}


currencies = {
    'USD': '$',
    'UAH': '₴',
    'RUB': '₽'
}

# --- Функції ---
def get_text(key, lang='uk'):
    """Отримує текст за ключем та мовою."""
    lang_dict = texts.get(lang, texts['uk']) # За замовчуванням uk
    text = lang_dict.get(key)
    # Якщо ключ не знайдено в поточній мові, спробувати знайти в uk
    if text is None and lang != 'uk':
        lang_dict_fallback = texts.get('uk', {})
        text = lang_dict_fallback.get(key)
    # Якщо все ще не знайдено, повернути маркер помилки
    if text is None:
        text = f"<'{key}'_not_found>"
        logger.warning(f"Text key '{key}' not found for language '{lang}' or default 'uk'.")
    return text

def get_currency_symbol(curr_code='UAH'):
    """Отримує символ валюти за її кодом."""
    return currencies.get(curr_code, '¤') # Повертає '¤' якщо код невідомий

# --- База даних та Стан Користувача/Адміна ---
temp_user_db = {} # Словник для зберігання даних користувачів (замість БД)
support_message_map = {} # Словник для зв'язку повідомлень підтримки {message_id_в_чаті_підтримки: {'user_id': ..., 'username': ...}}
user_states = {} # Словник для зберігання поточного стану користувача {user_id: {'state': 'some_state', 'data': {...}}}
confirmation_message_map = {} # Словник для підтвердження платежів {text_message_id_в_чаті_підтвердження: {'user_id': ..., 'amount': ..., ...}}
admin_states = {} # Словник для зберігання стану адміністратора {admin_id: {'state': '...', 'data': {...}}}

def initialize_db():
    logger.info("DB Initialized (In-memory Placeholder)")

def add_user_if_not_exists(user_id, username):
    """Додає користувача, якщо його немає, або оновлює username."""
    username_str = str(username) if username is not None else "None"
    if user_id not in temp_user_db:
        temp_user_db[user_id] = {
            'username': username_str,
            'balance': decimal.Decimal('0.00'), # Використовуємо Decimal
            'language': 'uk',
            'currency': 'UAH'
        }
        logger.info(f"Added user {user_id} (@{username_str})")
        return True
    else:
        # Оновлення username та перевірка наявності інших полів
        updated = False
        if temp_user_db[user_id].get('username') != username_str:
            temp_user_db[user_id]['username'] = username_str
            updated = True
        if 'language' not in temp_user_db[user_id]:
            temp_user_db[user_id]['language'] = 'uk'
            updated = True
        if 'currency' not in temp_user_db[user_id]:
            temp_user_db[user_id]['currency'] = 'UAH'
            updated = True
        if 'balance' not in temp_user_db[user_id]:
            # Перетворюємо існуючий float на Decimal, якщо потрібно
            current_balance = temp_user_db[user_id].get('balance', 0.0)
            try:
                temp_user_db[user_id]['balance'] = decimal.Decimal(str(current_balance))
            except decimal.InvalidOperation:
                temp_user_db[user_id]['balance'] = decimal.Decimal('0.00')
            updated = True
        elif not isinstance(temp_user_db[user_id]['balance'], decimal.Decimal):
            # Перетворюємо існуючий float на Decimal, якщо потрібно
            try:
                temp_user_db[user_id]['balance'] = decimal.Decimal(str(temp_user_db[user_id]['balance']))
            except decimal.InvalidOperation:
                temp_user_db[user_id]['balance'] = decimal.Decimal('0.00')
            updated = True

        if updated:
            logger.info(f"Checked/Updated user data for user {user_id} (@{username_str})")
    return False


def get_user_data(user_id):
    """Отримує дані користувача."""
    user_data = temp_user_db.get(user_id)
    if user_data:
        # Перевірка та встановлення значень за замовчуванням
        if 'language' not in user_data: user_data['language'] = 'uk'
        if 'currency' not in user_data: user_data['currency'] = 'UAH'
        if 'username' not in user_data: user_data['username'] = "None"
        # Перетворення балансу на Decimal, якщо він ще не є ним
        if 'balance' not in user_data:
            user_data['balance'] = decimal.Decimal('0.00')
        elif not isinstance(user_data['balance'], decimal.Decimal):
            try:
                user_data['balance'] = decimal.Decimal(str(user_data['balance']))
            except decimal.InvalidOperation:
                logger.error(f"Failed to convert balance to Decimal for user {user_id}. Resetting to 0.")
                user_data['balance'] = decimal.Decimal('0.00')
    return user_data

def update_user_language(user_id, lang_code):
    """Оновлює мову користувача."""
    if user_id in temp_user_db:
        temp_user_db[user_id]['language'] = lang_code
        logger.info(f"Updated language for {user_id} to {lang_code}")
        return True
    logger.warning(f"Attempt to update language for non-existent user {user_id}")
    return False

def convert_currency(amount: decimal.Decimal, from_curr: str, to_curr: str) -> decimal.Decimal | None:
    """Конвертує суму з однієї валюти в іншу через UAH."""
    if from_curr == to_curr:
        return amount

    try:
        # 1. Конвертувати з from_curr в UAH
        if from_curr == 'UAH':
            amount_in_uah = amount
        else:
            rate_to_uah = EXCHANGE_RATES_TO_UAH.get(from_curr)
            if rate_to_uah is None:
                raise KeyError(f"Missing exchange rate TO UAH for currency: {from_curr}")
            amount_in_uah = amount * rate_to_uah

        # 2. Конвертувати з UAH в to_curr
        if to_curr == 'UAH':
            final_amount = amount_in_uah
        else:
            rate_from_uah = EXCHANGE_RATES_FROM_UAH.get(to_curr)
            if rate_from_uah is None:
                raise KeyError(f"Missing exchange rate FROM UAH for currency: {to_curr}")
            final_amount = amount_in_uah * rate_from_uah

        # Округлення до 2 знаків після коми
        return final_amount.quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)

    except KeyError as e:
        logger.error(f"Currency conversion error ({from_curr} -> {to_curr}): {e}. Check EXCHANGE_RATES dictionaries.")
        return None
    except (ValueError, TypeError, decimal.InvalidOperation, ZeroDivisionError) as e:
        logger.error(f"Currency conversion error ({from_curr} -> {to_curr}): {e}")
        return None


def update_user_currency(user_id, new_curr_code):
    """Оновлює валюту користувача ТА КОНВЕРТУЄ БАЛАНС."""
    user_data = get_user_data(user_id)
    if not user_data:
        logger.warning(f"Attempt to update currency for non-existent user {user_id}")
        return False, None # Повертаємо False та None для балансу

    old_curr_code = user_data.get('currency', 'UAH')
    current_balance = user_data.get('balance', decimal.Decimal('0.00'))

    if old_curr_code == new_curr_code:
        logger.info(f"Currency for user {user_id} is already {new_curr_code}. No conversion needed.")
        # Переконуємось, що баланс - Decimal
        if not isinstance(current_balance, decimal.Decimal):
            try:
                temp_user_db[user_id]['balance'] = decimal.Decimal(str(current_balance))
            except decimal.InvalidOperation:
                temp_user_db[user_id]['balance'] = decimal.Decimal('0.00')
        return True, temp_user_db[user_id]['balance'] # Повертаємо True та поточний баланс

    new_balance = convert_currency(current_balance, old_curr_code, new_curr_code)

    if new_balance is not None:
        temp_user_db[user_id]['currency'] = new_curr_code
        temp_user_db[user_id]['balance'] = new_balance
        logger.info(f"Updated currency for {user_id} to {new_curr_code}. Balance converted from {current_balance} {old_curr_code} to {new_balance} {new_curr_code}")
        return True, new_balance # Повертаємо True та новий баланс
    else:
        # Помилка конвертації сталася всередині convert_currency і вже залогована
        return False, current_balance # Повертаємо False та старий баланс


def update_user_balance(user_id, amount_change, currency_code):
    """Оновлює баланс користувача. Сума `amount_change` має бути у валюті `currency_code`."""
    user_data = get_user_data(user_id)
    if not user_data:
        logger.warning(f"Attempt to update balance for non-existent user {user_id}")
        return False

    user_currency = user_data.get('currency', 'UAH')

    # Переконуємось, що поточний баланс - Decimal
    current_balance = user_data.get('balance', decimal.Decimal('0.00'))
    if not isinstance(current_balance, decimal.Decimal):
        try:
            current_balance = decimal.Decimal(str(current_balance))
        except decimal.InvalidOperation:
            logger.error(f"Invalid current balance format for user {user_id}. Resetting to 0.")
            current_balance = decimal.Decimal('0.00')

    try:
        # Переконуємось, що сума зміни - Decimal
        amount_to_add_decimal = decimal.Decimal(str(amount_change))

        # Конвертуємо суму поповнення до валюти користувача, якщо потрібно
        if currency_code != user_currency:
            converted_amount = convert_currency(amount_to_add_decimal, currency_code, user_currency)
            if converted_amount is None:
                # Помилка конвертації вже залогована в convert_currency
                logger.error(f"Failed to convert deposit amount for user {user_id} from {currency_code} to {user_currency}.")
                return False # Помилка конвертації
            amount_in_user_currency = converted_amount
            logger.info(f"Converted balance update amount {amount_to_add_decimal} {currency_code} to {amount_in_user_currency} {user_currency} for user {user_id}")
        else:
            amount_in_user_currency = amount_to_add_decimal # Конвертація не потрібна

        new_balance = (current_balance + amount_in_user_currency).quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
        temp_user_db[user_id]['balance'] = new_balance

        logger.info(f"Updated balance for {user_id} by {amount_in_user_currency:.2f} {user_currency}. New balance: {new_balance:.2f} {user_currency}")
        return True
    except (ValueError, TypeError, decimal.InvalidOperation) as e:
        logger.error(f"Invalid amount type or value for balance update for {user_id}: {amount_change}. Error: {e}")
        return False


def set_user_state(user_id, state, data=None):
    """Встановлює стан для користувача."""
    if data is None:
        data = {}
    user_states[user_id] = {'state': state, 'data': data}
    logger.info(f"Set user state for {user_id} to {state} with data {data}")

def get_user_state(user_id):
    """Отримує стан користувача."""
    return user_states.get(user_id)

def clear_user_state(user_id):
    """Очищує стан користувача."""
    if user_id in user_states:
        del user_states[user_id]
        logger.info(f"Cleared user state for {user_id}")

def set_admin_state(admin_id, state, data=None):
    """Встановлює стан для адміністратора."""
    if data is None: data = {}
    admin_states[admin_id] = {'state': state, 'data': data}
    logger.info(f"Set admin state for {admin_id} to {state} with data {data}")

def get_admin_state(admin_id):
    """Отримує стан адміністратора."""
    return admin_states.get(admin_id)

def clear_admin_state(admin_id):
    """Очищує стан адміністратора."""
    if admin_id in admin_states:
        del admin_states[admin_id]
        logger.info(f"Cleared admin state for {admin_id}")

# --- Ініціалізація бота ---
bot = telebot.TeleBot(BOT_TOKEN)

# --- Функції перевірки підписки ---
def check_subscription(user_id):
    """Перевіряє, чи підписаний користувач на канал CHANNEL_ID."""
    if not CHANNEL_ID:
        logger.warning("CHANNEL_ID is not set. Skipping subscription check.")
        return True # Якщо канал не вказано, вважаємо, що перевірка не потрібна
    try:
        member = bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        logger.debug(f"Checked subscription for user {user_id}. Status: {member.status}")
        # Дозволені статуси: creator, administrator, member
        return member.status not in ['left', 'kicked']
    except telebot.apihelper.ApiTelegramException as e:
        # Можливі помилки:
        # - "Bad Request: user not found" (користувач не взаємодіяв з ботом або заблокував його?)
        # - "Bad Request: chat not found" (неправильний CHANNEL_ID або бот не в каналі)
        # - "Forbidden: bot is not a member of the channel chat" (бот не адмін каналу)
        logger.error(f"Could not check subscription for user {user_id} in channel {CHANNEL_ID}: {e}")
        return False # В разі помилки вважаємо, що не підписаний
    except Exception as e:
        logger.error(f"Unexpected error checking subscription for user {user_id}: {e}")
        return False # В разі помилки вважаємо, що не підписаний

def get_subscribe_keyboard(lang='uk'):
    """Повертає клавіатуру для запиту підписки."""
    markup = types.InlineKeyboardMarkup()
    subscribe_btn = types.InlineKeyboardButton(
        text=get_text('subscribe_button', lang),
        url=CHANNEL_URL
    )
    check_btn = types.InlineKeyboardButton(
        text=get_text('check_subscription_button', lang),
        callback_data='check_subscription_callback'
    )
    markup.add(subscribe_btn)
    markup.add(check_btn)
    return markup

def send_subscribe_prompt(chat_id, lang):
    """Надсилає повідомлення з вимогою підписатися."""
    try:
        bot.send_message(
            chat_id,
            get_text('subscribe_prompt', lang),
            reply_markup=get_subscribe_keyboard(lang),
            parse_mode='Markdown' # Або HTML, якщо використовуєте відповідну розмітку
        )
        logger.info(f"Sent subscription prompt to user {chat_id}")
    except Exception as e:
        logger.error(f"Failed to send subscription prompt to user {chat_id}: {e}")

def send_subscribe_prompt_in_callback(call, lang):
    """Надсилає повідомлення з вимогою підписатися у відповідь на callback."""
    try:
        # Спочатку відповідаємо на callback, щоб кнопка перестала "крутитися"
        bot.answer_callback_query(call.id, get_text('subscription_needed', lang), show_alert=True)
        # Потім надсилаємо повідомлення (або редагуємо існуюче, якщо можливо)
        # У цьому випадку краще надіслати нове, бо старе могло бути не тим, що треба
        send_subscribe_prompt(call.message.chat.id, lang)
        # Спробуємо видалити старе повідомлення з кнопками, на яке натиснули
        # try:
        #     bot.delete_message(call.message.chat.id, call.message.message_id)
        # except Exception as e_del:
        #     logger.warning(f"Could not delete original message {call.message.message_id} after failed subscription check callback: {e_del}")

    except Exception as e:
        logger.error(f"Failed to send subscription prompt in callback for user {call.from_user.id}: {e}")

# --- Клавіатури ---
def get_main_keyboard(lang='uk'):
    """Повертає головну клавіатуру."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_profile = types.KeyboardButton(get_text('profile', lang))
    btn_settings = types.KeyboardButton(get_text('settings', lang))
    btn_buy = types.KeyboardButton(get_text('buy_number', lang))
    btn_deposit = types.KeyboardButton(get_text('deposit', lang))
    btn_support = types.KeyboardButton(get_text('support', lang))
    btn_about = types.KeyboardButton(get_text('about', lang))
    markup.add(btn_profile, btn_settings)
    markup.add(btn_buy, btn_deposit)
    markup.add(btn_support, btn_about)
    return markup

def get_settings_keyboard(lang='uk'):
    """Повертає клавіатуру налаштувань."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_lang = types.InlineKeyboardButton(get_text('change_lang', lang), callback_data='settings_change_lang')
    btn_curr = types.InlineKeyboardButton(get_text('change_curr', lang), callback_data='settings_change_curr')
    btn_back = types.InlineKeyboardButton(get_text('back', lang), callback_data='settings_back')
    markup.add(btn_lang, btn_curr, btn_back)
    return markup

def get_language_keyboard(lang='uk'):
    """Повертає клавіатуру вибору мови."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_ru = types.InlineKeyboardButton(get_text('lang_ru', lang), callback_data='set_lang_ru')
    btn_uk = types.InlineKeyboardButton(get_text('lang_uk', lang), callback_data='set_lang_uk')
    btn_en = types.InlineKeyboardButton(get_text('lang_en', lang), callback_data='set_lang_en')
    btn_back = types.InlineKeyboardButton(get_text('back', lang), callback_data='lang_back')
    markup.add(btn_ru, btn_uk, btn_en, btn_back)
    return markup

def get_currency_keyboard(lang='uk'):
    """Повертає клавіатуру вибору валюти."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_usd = types.InlineKeyboardButton(get_text('curr_usd', lang), callback_data='set_curr_USD')
    btn_uah = types.InlineKeyboardButton(get_text('curr_uah', lang), callback_data='set_curr_UAH')
    btn_rub = types.InlineKeyboardButton(get_text('curr_rub', lang), callback_data='set_curr_RUB')
    btn_back = types.InlineKeyboardButton(get_text('back', lang), callback_data='curr_back')
    markup.add(btn_usd, btn_uah, btn_rub, btn_back)
    return markup

def get_country_keyboard(lang='uk'):
    """Повертає клавіатуру вибору країни (для купівлі)."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_ua = types.InlineKeyboardButton(get_text('country_ua', lang), callback_data='buy_country_UA')
    btn_de = types.InlineKeyboardButton(get_text('country_de', lang), callback_data='buy_country_DE')
    btn_pl = types.InlineKeyboardButton(get_text('country_pl', lang), callback_data='buy_country_PL')
    btn_back = types.InlineKeyboardButton(get_text('back', lang), callback_data='buy_back')
    markup.add(btn_ua, btn_de, btn_pl, btn_back)
    return markup

def get_back_button(callback_data, lang='uk'):
    """Повертає Inline клавіатуру з однією кнопкою "Назад"."""
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton(get_text('back', lang), callback_data=callback_data)
    markup.add(btn_back)
    return markup

def get_payment_method_keyboard(lang='uk'):
    """Повертає клавіатуру вибору методу оплати."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for method_code, _ in PAYMENT_DETAILS.items():
        buttons.append(types.InlineKeyboardButton(
            get_text(f'payment_method_{method_code}', lang),
            callback_data=f'select_method_{method_code}'
        ))
    markup.add(*buttons)
    markup.row(types.InlineKeyboardButton(get_text('cancel_deposit', lang), callback_data='cancel_deposit_amount'))
    return markup

# --- Клавіатури для чатів Адміністрації ---

def get_admin_confirmation_keyboard(lang='uk', text_msg_id=None):
    """Повертає клавіатуру для адміна (Зарахувати/Відхилити/Відхилити з причиною)."""
    if text_msg_id is None:
        logger.error("Cannot create admin confirmation keyboard without text_msg_id")
        return None
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn_approve = types.InlineKeyboardButton(
        get_text('admin_approve', lang), # "✅ Зарахувати"
        callback_data=f'confirm_{text_msg_id}_approve_prompt' # Змінено для запиту суми
    )
    btn_reject = types.InlineKeyboardButton(
        get_text('admin_reject', lang), # "❌ Відхилити"
        callback_data=f'confirm_{text_msg_id}_reject_now' # Змінено для ясності
    )
    btn_reject_comment = types.InlineKeyboardButton(
        get_text('admin_reject_comment', lang), # "📝 Відхилити з причиною"
        callback_data=f'confirm_{text_msg_id}_reject_comment' # Залишається
    )
    markup.add(btn_approve, btn_reject, btn_reject_comment)
    return markup

def get_support_reply_keyboard(lang='uk', target_user_id=None, support_msg_id=None):
    """Повертає клавіатуру з кнопкою 'Відповісти' для чату підтримки."""
    if target_user_id is None or support_msg_id is None:
        logger.error("Cannot create support reply keyboard without target_user_id and support_msg_id")
        return None
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_reply = types.InlineKeyboardButton(
        get_text('support_reply_button', lang), # "✉️ Відповісти"
        callback_data=f'reply_support_{target_user_id}_{support_msg_id}'
    )
    markup.add(btn_reply)
    return markup

# -----------------------------------------

def get_cancel_deposit_keyboard(lang='uk'):
    """Повертає клавіатуру скасування/назад для етапу скріншоту."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_cancel = types.InlineKeyboardButton(get_text('cancel_deposit', lang), callback_data='cancel_deposit_screenshot')
    btn_back = types.InlineKeyboardButton(get_text('back_to_methods', lang), callback_data='back_to_methods')
    markup.add(btn_cancel, btn_back)
    return markup

# --- Обробники ---

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обробник команди /start."""
    user = message.from_user
    user_id = user.id
    username = user.username
    logger.info(f"User {user_id} (@{username}) started the bot.")

    # Додаємо/оновлюємо користувача
    add_user_if_not_exists(user_id, username)
    clear_user_state(user_id)
    # Адмінський стан НЕ чистимо тут, бо адмін може бути в іншому чаті

    user_data = get_user_data(user_id)
    if not user_data:
        logger.error(f"Failed to get user data for {user_id} even after adding.")
        try:
            bot.send_message(message.chat.id, "Виникла помилка ініціалізації. Спробуйте /start ще раз.")
        except Exception as e:
            logger.error(f"Failed to send error message to user {user_id}: {e}")
        return

    lang = user_data.get('language', 'uk')

    # --- Перевірка підписки ---
    if not check_subscription(user_id):
        send_subscribe_prompt(message.chat.id, lang)
        return # Не продовжуємо, поки користувач не підпишеться
    # --- Кінець перевірки підписки ---

    currency_code = user_data.get('currency', 'UAH')
    balance = user_data.get('balance', decimal.Decimal('0.00')) # Decimal
    currency_symbol = get_currency_symbol(currency_code)

    greeting_text = get_text('start_greeting', lang).format(
        balance=f"{balance:.2f}", # Форматуємо Decimal для виводу
        currency=currency_symbol,
        user_id=user_id
    )
    try:
        bot.send_message(
            message.chat.id,
            greeting_text,
            reply_markup=get_main_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Failed to send start message to user {user_id}: {e}")

@bot.message_handler(commands=['cancel'])
def cancel_command(message):
    """Обробник команди /cancel для скасування поточних дій користувача або адміна."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    admin_lang = 'uk' # Мова для відповідей адміну

    cancelled_user_state = False
    cancelled_admin_state = False

    # --- Скасування стану користувача (тільки в приватному чаті) ---
    if chat_id == user_id:
        user_data = get_user_data(user_id) # Потрібно для мови
        lang = user_data.get('language', 'uk') if user_data else 'uk'

        # Перевірка підписки перед скасуванням (щоб не показувати меню, якщо не підписаний)
        if not check_subscription(user_id):
            send_subscribe_prompt(chat_id, lang)
            # Видаляємо команду /cancel
            try:
                 bot.delete_message(chat_id, message.message_id)
            except Exception as e_del:
                 logger.warning(f"Could not delete /cancel message on failed subscription check: {e_del}")
            return

        current_state = get_user_state(user_id)
        if current_state and 'state' in current_state and current_state['state'].startswith('awaiting_'):
            state_name = current_state['state']
            clear_user_state(user_id)
            cancelled_user_state = True
            logger.info(f"User {user_id} cancelled state {state_name} via /cancel")
            try:
                # Повідомлення користувачу про скасування
                bot.send_message(chat_id, get_text('action_cancelled_user', lang), reply_markup=get_main_keyboard(lang))
            except Exception as e:
                logger.error(f"Failed to send user cancel message to user {user_id}: {e}")
            return # Завершуємо тут, якщо скасували стан користувача

    # --- Скасування стану адміністратора (незалежно від чату, де введено /cancel) ---
    current_admin_state = get_admin_state(user_id) # user_id тут == admin_id
    if current_admin_state and 'state' in current_admin_state and current_admin_state['state'].startswith('awaiting_'):
        state_name = current_admin_state['state']
        prompt_message_id = current_admin_state.get('data', {}).get('prompt_message_id') # ID повідомлення-запиту

        clear_admin_state(user_id)
        cancelled_admin_state = True
        logger.info(f"Admin {user_id} cancelled state {state_name} via /cancel in chat {chat_id}")

        # Повідомлення адміну про скасування
        try:
            sent_msg = bot.send_message(chat_id, get_text('cancel_action', admin_lang))
            # Спробувати видалити повідомлення /cancel адміна та повідомлення-запит, якщо воно було
            try:
                bot.delete_message(chat_id, message.message_id)
                if prompt_message_id:
                    bot.delete_message(chat_id, prompt_message_id)
                    logger.info(f"Deleted prompt message {prompt_message_id} for admin {user_id} on cancel")
                # Видаляємо повідомлення про скасування через 5 секунд
                time.sleep(5)
                bot.delete_message(chat_id, sent_msg.message_id)
            except Exception as e_del:
                logger.warning(f"Could not delete messages on admin cancel: {e_del}")
        except Exception as e:
            logger.error(f"Failed to send admin cancel confirmation to admin {user_id} in chat {chat_id}: {e}")
        return # Завершуємо, якщо скасували стан адміна

    # --- Якщо жоден стан не було скасовано ---
    if not cancelled_user_state and not cancelled_admin_state:
        if chat_id == user_id: # Приватний чат користувача
            user_data = get_user_data(user_id) # Потрібно для мови
            lang = user_data.get('language', 'uk') if user_data else 'uk'
            # Перевірка підписки
            if not check_subscription(user_id):
                send_subscribe_prompt(chat_id, lang)
                # Видаляємо команду /cancel
                try:
                    bot.delete_message(chat_id, message.message_id)
                except Exception as e_del:
                    logger.warning(f"Could not delete /cancel message on failed subscription check (no state): {e_del}")
                return

            logger.info(f"User {user_id} used /cancel, but no active state found. Sending main menu.")
            try:
                bot.send_message(chat_id, get_text('main_menu', lang), reply_markup=get_main_keyboard(lang))
            except Exception as e:
                logger.error(f"Failed to send main menu message on inactive cancel to user {user_id}: {e}")
        else: # Адмінський чат, але адмін не був у стані очікування
            logger.info(f"Admin {user_id} used /cancel in chat {chat_id} but wasn't in an awaiting state.")
            try:
                sent_msg = bot.send_message(chat_id, get_text('no_active_action', admin_lang))
                # Видаляємо /cancel адміна і повідомлення через 5 секунд
                try:
                    bot.delete_message(chat_id, message.message_id)
                    time.sleep(5)
                    bot.delete_message(chat_id, sent_msg.message_id)
                except Exception as e_del:
                    logger.warning(f"Failed to delete admin's inactive /cancel message: {e_del}")
            except Exception as e:
                logger.error(f"Failed to send 'no active action' message to admin {user_id} in chat {chat_id}: {e}")


# --- Функції для обробки кнопок головного меню ---

def show_profile(message, lang, user_data):
    """Показує інформацію профілю."""
    user_id = message.from_user.id
    currency_code = user_data.get('currency', 'UAH')
    balance = user_data.get('balance', decimal.Decimal('0.00')) # Decimal
    currency_symbol = get_currency_symbol(currency_code)
    profile_text = get_text('profile_info', lang).format(
        user_id=user_id,
        balance=f"{balance:.2f}", # Форматуємо Decimal
        currency=currency_symbol
    )
    try:
        bot.send_message(message.chat.id, profile_text)
    except Exception as e:
        logger.error(f"Failed to send profile info to user {user_id}: {e}")

def show_about(message, lang):
    """Показує інформацію "Про нас"."""
    if lang == 'ru': about_text_key = 'ABOUT_TEXT_RU'
    elif lang == 'en': about_text_key = 'ABOUT_TEXT_EN'
    else: about_text_key = 'ABOUT_TEXT_UK' # Default to uk

    about_text = get_text(about_text_key, lang)
    try:
        bot.send_message(message.chat.id, about_text)
    except Exception as e:
        logger.error(f"Failed to send about info to user {message.from_user.id}: {e}")

def show_settings(message, lang):
    """Показує меню налаштувань з inline кнопками."""
    try:
        bot.send_message(
            message.chat.id,
            get_text('settings_menu', lang),
            reply_markup=get_settings_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Failed to send settings menu to user {message.from_user.id}: {e}")

def request_support_message(message, lang):
    """Запитує у користувача повідомлення для підтримки."""
    user_id = message.from_user.id
    set_user_state(user_id, 'awaiting_support_message')
    try:
        bot.send_message(
            message.chat.id,
            get_text('support_request', lang),
            reply_markup=types.ForceReply(selective=True)
        )
    except Exception as e:
        logger.error(f"Failed to request support message from user {user_id}: {e}")
        clear_user_state(user_id)
        try:
            bot.send_message(user_id, get_text('error_sending_support', lang), reply_markup=get_main_keyboard(lang))
        except Exception as e2:
            logger.error(f"Also failed to send error message to user {user_id}: {e2}")

def show_buy_options(message, lang):
    """Показує опції купівлі номера (заглушка)."""
    try:
        bot.send_message(
            message.chat.id,
            get_text('choose_country', lang),
            reply_markup=get_country_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Failed to send buy options to user {message.from_user.id}: {e}")

def request_deposit_amount(message, lang):
    """Запитує суму поповнення (завжди в UAH)."""
    user_id = message.from_user.id
    clear_user_state(user_id)
    set_user_state(user_id, 'awaiting_deposit_amount')
    try:
        bot.send_message(
            message.chat.id,
            get_text('request_deposit_amount', lang), # Текст вже вказує UAH
            reply_markup=types.ForceReply(selective=True)
        )
    except Exception as e:
        logger.error(f"Failed to request deposit amount from user {user_id}: {e}")
        clear_user_state(user_id)
        try:
            bot.send_message(user_id, get_text('callback_error', lang), reply_markup=get_main_keyboard(lang))
        except Exception as e2:
            logger.error(f"Also failed to send error message to user {user_id}: {e2}")


# --- Функції для обробки кроків (станів) ---

def process_deposit_amount_step(message):
    """Обробляє введену користувачем суму поповнення (в UAH)."""
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    state_info = get_user_state(user_id)

    if not user_data or not state_info or state_info.get('state') != 'awaiting_deposit_amount':
        logger.warning(f"User {user_id} sent amount but not in awaiting_deposit_amount state ({state_info})")
        lang = user_data.get('language', 'uk') if user_data else 'uk'
        # Перевірка підписки перед надсиланням помилки
        if not check_subscription(user_id):
             send_subscribe_prompt(message.chat.id, lang)
             return
        try:
            bot.send_message(message.chat.id, get_text('invalid_step', lang), reply_markup=get_main_keyboard(lang))
        except Exception as e:
            logger.error(f"Failed to send invalid step message to user {user_id}: {e}")
        clear_user_state(user_id)
        return

    lang = user_data.get('language', 'uk')
    # --- Перевірка підписки ---
    if not check_subscription(user_id):
        send_subscribe_prompt(message.chat.id, lang)
        # Не очищуємо стан, щоб після підписки можна було продовжити
        # clear_user_state(user_id)
        return
    # --- Кінець перевірки підписки ---

    # Валюта поповнення ЗАВЖДИ UAH
    deposit_currency_code = 'UAH'
    deposit_currency_symbol = get_currency_symbol(deposit_currency_code)

    try:
        # Використовуємо Decimal для суми
        deposit_amount = decimal.Decimal(message.text.replace(',', '.'))
        if deposit_amount <= 0:
            raise ValueError("Amount must be positive")

        # Округлюємо до 2 знаків
        deposit_amount = deposit_amount.quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)

        set_user_state(user_id, 'awaiting_payment_method', {'amount': deposit_amount, 'currency': deposit_currency_code})
        bot.send_message(
            message.chat.id,
            get_text('select_payment_method', lang).format(amount=f"{deposit_amount:.2f}", currency=deposit_currency_symbol),
            reply_markup=get_payment_method_keyboard(lang)
        )

    except (ValueError, decimal.InvalidOperation):
        logger.warning(f"Invalid deposit amount entered by user {user_id}: {message.text}")
        error_message = get_text('invalid_deposit_amount', lang)
        try:
            # Повторно запитуємо суму, не очищуючи стан
            bot.send_message(message.chat.id, error_message, reply_markup=types.ForceReply(selective=True))
        except Exception as e:
            logger.error(f"Failed to send invalid amount message or reregister step for user {user_id}: {e}")
            clear_user_state(user_id) # Очищуємо стан, якщо навіть запитати не вдалось
            try:
                bot.send_message(user_id, get_text('callback_error', lang), reply_markup=get_main_keyboard(lang))
            except Exception as e2:
                logger.error(f"Also failed to send error message to user {user_id}: {e2}")
    except Exception as e:
        logger.error(f"Error processing deposit amount for user {user_id}: {e}")
        clear_user_state(user_id)
        try:
            bot.send_message(user_id, get_text('callback_error', lang), reply_markup=get_main_keyboard(lang))
        except Exception as e2:
            logger.error(f"Also failed to send error message to user {user_id}: {e2}")

def process_support_message_step(message):
    """Обробляє введене користувачем повідомлення для підтримки."""
    user = message.from_user
    user_id = user.id
    support_message_text = message.text
    user_data = get_user_data(user_id)
    lang = user_data.get('language', 'uk') if user_data else 'uk'

    # --- Перевірка підписки ---
    if not check_subscription(user_id):
        send_subscribe_prompt(message.chat.id, lang)
        # Не очищуємо стан, щоб після підписки можна було надіслати повідомлення
        # clear_user_state(user_id)
        return
    # --- Кінець перевірки підписки ---

    original_username = user_data.get('username', "None") if user_data else "None"

    # Команда /cancel обробляється окремим хендлером

    logger.info(f"User {user_id} (@{original_username}) sent support message: {support_message_text}")

    text_to_admin = get_text('support_message_to_admin', 'uk').format( # Завжди адміну українською
        user_id=user_id,
        username=original_username,
        message_text=support_message_text
    )
    try:
        # Надсилаємо повідомлення в чат підтримки
        sent_message = bot.send_message(
            SUPPORT_CHAT_ID,
            text_to_admin,
            # Додаємо кнопку "Відповісти"
            reply_markup=get_support_reply_keyboard('uk', target_user_id=user_id, support_msg_id='{msg_id}') # {msg_id} буде замінено нижче
        )
        logger.info(f"Support message forwarded to chat {SUPPORT_CHAT_ID} with message_id {sent_message.message_id}")

        # Тепер оновлюємо кнопку з правильним ID повідомлення
        new_markup = get_support_reply_keyboard('uk', target_user_id=user_id, support_msg_id=sent_message.message_id)
        if new_markup:
            bot.edit_message_reply_markup(
                chat_id=SUPPORT_CHAT_ID,
                message_id=sent_message.message_id,
                reply_markup=new_markup
            )

        # Зберігаємо ID користувача та його username для відповіді через кнопку або reply
        support_message_map[sent_message.message_id] = {'user_id': user_id, 'username': original_username}
        logger.info(f"Saved support map: {sent_message.message_id} -> user {user_id} (@{original_username})")

        # Повідомляємо користувача
        bot.send_message(
            message.chat.id,
            get_text('support_sent', lang),
            reply_markup=get_main_keyboard(lang)
        )
        clear_user_state(user_id)

    except Exception as e:
        logger.error(f"Failed to send support message to {SUPPORT_CHAT_ID} or notify user {user_id}: {e}")
        try:
            bot.send_message(
                message.chat.id,
                get_text('error_sending_support', lang),
                reply_markup=get_main_keyboard(lang)
            )
        except Exception as e2:
            logger.error(f"Also failed to send error to user {user_id}: {e2}")
        # Стан НЕ очищуємо, щоб користувач міг спробувати ще раз або скасувати


# --- Універсальний обробник текстових повідомлень ---

@bot.message_handler(func=lambda message: message.chat.type == 'private' and not message.text.startswith('/'), content_types=['text'])
def handle_text_message(message):
    """Обробляє текстові повідомлення в приватному чаті, які не є командами."""
    user_id = message.from_user.id
    text = message.text
    user_data = get_user_data(user_id)

    if not user_data:
        logger.warning(f"User {user_id} not found in DB, requesting /start")
        try:
            # Навіть якщо користувача немає, перевіримо підписку (можливо, це перша взаємодія)
            # і надішлемо відповідний запит або помилку
            if not check_subscription(user_id):
                send_subscribe_prompt(message.chat.id, 'uk') # Використовуємо мову за замовчуванням
            else:
                 bot.send_message(message.chat.id, get_text('start_needed', 'uk'))
        except Exception as e:
            logger.error(f"Failed to send start_needed/subscribe message to user {user_id}: {e}")
        return

    lang = user_data.get('language', 'uk')

    # --- Перевірка підписки ---
    if not check_subscription(user_id):
        send_subscribe_prompt(message.chat.id, lang)
        return
    # --- Кінець перевірки підписки ---

    current_state_info = get_user_state(user_id)
    current_state = current_state_info.get('state') if current_state_info else None

    # 1. Перевірка стану користувача
    if current_state == 'awaiting_deposit_amount':
        process_deposit_amount_step(message)
        return
    elif current_state == 'awaiting_support_message':
        process_support_message_step(message)
        return

    # 2. Обробка кнопок головного меню (якщо користувач не в якомусь стані)
    if current_state is None:
        try:
            if text == get_text('profile', lang): show_profile(message, lang, user_data)
            elif text == get_text('about', lang): show_about(message, lang)
            elif text == get_text('settings', lang): show_settings(message, lang)
            elif text == get_text('support', lang): request_support_message(message, lang)
            elif text == get_text('buy_number', lang): show_buy_options(message, lang)
            elif text == get_text('deposit', lang): request_deposit_amount(message, lang)
            else:
                logger.info(f"Unknown text command from {user_id} (no state): {text}")
                bot.send_message(message.chat.id, get_text('unknown_command', lang), reply_markup=get_main_keyboard(lang)) # Додано клавіатуру
        except Exception as e:
            logger.error(f"Error processing text command '{text}' for user {user_id}: {e}")
            try:
                bot.send_message(message.chat.id, get_text('callback_error', lang), reply_markup=get_main_keyboard(lang))
            except Exception as e2:
                logger.error(f"Also failed to send error message to user {user_id}: {e2}")
    # 3. Якщо користувач в іншому стані (наприклад, awaiting_screenshot) і надсилає текст
    else:
        logger.warning(f"User {user_id} sent text '{text}' while in unexpected state {current_state}.")
        try:
            # Надсилаємо повідомлення про невірний крок
            bot.send_message(message.chat.id, get_text('invalid_step', lang))
            # Якщо очікували скріншот, нагадуємо про це
            if current_state == 'awaiting_screenshot':
                bot.send_message(message.chat.id, get_text('awaiting_screenshot_message', lang),
                                 reply_markup=get_cancel_deposit_keyboard(lang))
            # Можна додати нагадування для інших станів, якщо потрібно
        except Exception as e:
            logger.error(f"Failed to send invalid_step/reminder message to user {user_id} in state {current_state}: {e}")


# --- Обробник отримання фото (для скріншоту) ---

@bot.message_handler(content_types=['photo'], func=lambda message: message.chat.type == 'private')
def handle_screenshot(message):
    """Обробляє отримання фотографії (очікується скріншот оплати)."""
    user_id = message.from_user.id
    logger.info(f"Entered handle_screenshot for user {user_id}")

    user_data = get_user_data(user_id)
    lang = user_data.get('language', 'uk') if user_data else 'uk'

    # --- Перевірка підписки ---
    if not check_subscription(user_id):
        send_subscribe_prompt(message.chat.id, lang)
        return
    # --- Кінець перевірки підписки ---

    current_state_info = get_user_state(user_id)
    current_state = current_state_info.get('state') if current_state_info else None


    if not user_data or not current_state_info or current_state != 'awaiting_screenshot':
        logger.warning(f"User {user_id} sent a photo but not in 'awaiting_screenshot' state. Current state info: {current_state_info}")
        try:
            bot.send_message(message.chat.id, get_text('invalid_step', lang), reply_markup=get_main_keyboard(lang))
        except Exception as e:
            logger.error(f"Failed to send invalid step message on photo to user {user_id}: {e}")
        return

    logger.info(f"User {user_id} is in correct state 'awaiting_screenshot'. Processing photo.")
    deposit_info = current_state_info.get('data', {})
    amount = deposit_info.get('amount') # Decimal
    method_code = deposit_info.get('method')
    # Валюта заявки завжди UAH
    currency_code = deposit_info.get('currency', 'UAH') # За замовчуванням UAH
    username = user_data.get('username', 'N/A')

    if amount is None or not method_code or not currency_code:
        logger.error(f"Missing data in state 'awaiting_screenshot' for user {user_id}. Data: {deposit_info}")
        try:
            bot.send_message(user_id, get_text('callback_error', lang), reply_markup=get_main_keyboard(lang))
        except Exception as e:
            logger.error(f"Failed to send error message to user {user_id} due to missing state data: {e}")
        clear_user_state(user_id)
        return

    currency_symbol = get_currency_symbol(currency_code)

    try:
        photo_id = message.photo[-1].file_id
        logger.info(f"Received screenshot from user {user_id} (photo_id: {photo_id}) for {amount} {currency_code} via {method_code}")

        admin_text = get_text('admin_confirmation_message', 'uk').format( # Завжди укр для адміна
            user_id=user_id,
            username=username,
            amount=f"{amount:.2f}", # Форматуємо Decimal
            currency=currency_symbol,
            method=get_text(f'payment_method_{method_code}', 'uk')
        )

        logger.info(f"Attempting to send photo to confirmation chat {CONFIRMATION_CHAT_ID}")
        # 1. Надсилаємо фото
        sent_photo_msg = bot.send_photo(CONFIRMATION_CHAT_ID, photo_id)
        logger.info(f"Photo sent to confirmation chat. Photo Message ID: {sent_photo_msg.message_id}")

        # 2. Надсилаємо текст як відповідь на фото (використовуючи reply_parameters)
        reply_params = ReplyParameters(message_id=sent_photo_msg.message_id)
        sent_admin_msg = bot.send_message(
            CONFIRMATION_CHAT_ID,
            admin_text,
            reply_parameters=reply_params
        )
        text_msg_id = sent_admin_msg.message_id
        logger.info(f"Confirmation text sent. Text Message ID: {text_msg_id}")

        # 3. Генеруємо клавіатуру підтвердження
        admin_keyboard = get_admin_confirmation_keyboard('uk', text_msg_id)

        if admin_keyboard:
            # 4. Редагуємо текстове повідомлення, додаючи кнопки
            bot.edit_message_reply_markup(
                chat_id=CONFIRMATION_CHAT_ID,
                message_id=text_msg_id,
                reply_markup=admin_keyboard
            )
            logger.info(f"Added confirmation buttons to text message {text_msg_id}")

            # Зберігаємо дані про запит, використовуючи ID текстового повідомлення
            confirmation_message_map[text_msg_id] = {
                'user_id': user_id,
                'username': username, # Зберігаємо username для зручності
                'requested_amount': amount, # Зберігаємо заявлену суму (Decimal)
                'method': method_code,
                'currency': currency_code, # Валюта заявки (завжди UAH)
                'photo_msg_id': sent_photo_msg.message_id,
                'user_lang': lang # Зберігаємо мову користувача
            }
            logger.info(f"Saved confirmation map: TEXT msg_id {text_msg_id} -> user {user_id} (requested: {amount} {currency_code})")
        else:
            logger.error("Failed to create admin confirmation keyboard.")
            reply_params_error = ReplyParameters(message_id=sent_photo_msg.message_id)
            bot.send_message(CONFIRMATION_CHAT_ID, "Помилка: Не вдалося створити кнопки підтвердження.", reply_parameters=reply_params_error)

        # 5. Повідомляємо користувача
        logger.info(f"Notifying user {user_id} about screenshot received.")
        bot.send_message(
            user_id,
            get_text('screenshot_received_admin_notification', lang),
            reply_markup=get_main_keyboard(lang)
        )
        logger.info(f"User {user_id} notified.")

        # 6. Очищуємо стан користувача
        clear_user_state(user_id)

    except Exception as e:
        logger.error(f"Failed processing screenshot for user {user_id}. Error: {e}")
        logger.exception("Traceback for handle_screenshot error:")
        clear_user_state(user_id)
        try:
            bot.send_message(user_id, get_text('error_sending_support', lang), reply_markup=get_main_keyboard(lang))
        except Exception as e2:
            logger.error(f"Also failed to send error message to user {user_id}: {e2}")

# --- Функції для обробки відповідей Адміністратора ---

def process_rejection_reason(message):
    """Обробляє текст причини відхилення, надісланий адміном."""
    admin_id = message.from_user.id
    reason_text = message.text.strip()
    admin_state_info = get_admin_state(admin_id)
    admin_lang = 'uk' # Мова для відповідей адміну

    # 1. Перевірка стану адміна
    if not admin_state_info or admin_state_info.get('state') != 'awaiting_rejection_reason':
        logger.warning(f"Admin {admin_id} sent text '{reason_text}' but not in 'awaiting_rejection_reason' state.")
        # Перевіряємо, чи це відповідь на повідомлення бота про запит причини
        if message.reply_to_message and message.reply_to_message.from_user.is_bot:
            try:
                reply_params = ReplyParameters(message_id=message.message_id)
                bot.send_message(message.chat.id, get_text('admin_not_awaiting_reason', admin_lang), reply_parameters=reply_params)
            except Exception as e:
                logger.error(f"Failed to send state error to admin {admin_id}: {e}")
        return

    # 2. Обробка /cancel - обробляється окремим хендлером

    # 3. Отримання даних зі стану адміна
    state_data = admin_state_info.get('data', {})
    prompt_message_id = state_data.get('prompt_message_id') # ID повідомлення-запиту
    target_user_id = state_data.get('user_id')
    # Сума і валюта тут - це *заявлені* користувачем (з confirmation_message_map)
    requested_amount = state_data.get('requested_amount') # Decimal
    currency_code = state_data.get('currency') # UAH
    clicked_text_msg_id = state_data.get('clicked_text_msg_id')
    original_admin_message_text = state_data.get('original_caption')
    photo_msg_id = state_data.get('photo_msg_id')
    method_code = state_data.get('method')

    # 4. Перевірка даних
    if not all([target_user_id, requested_amount is not None, currency_code, clicked_text_msg_id, original_admin_message_text, photo_msg_id]):
        logger.error(f"Incomplete data found in admin state 'awaiting_rejection_reason' for admin {admin_id}. Data: {state_data}")
        try:
            reply_params = ReplyParameters(message_id=clicked_text_msg_id) if clicked_text_msg_id else None
            bot.send_message(CONFIRMATION_CHAT_ID,
                             "⚠️ Помилка: Недостатньо даних для обробки відхилення. Дія скасована.",
                             reply_parameters=reply_params)
        except Exception as e:
            logger.error(f"Failed to send data error message to admin chat: {e}")
        clear_admin_state(admin_id)
        # Спробувати видалити повідомлення-запит та відповідь адміна
        try:
            if prompt_message_id: bot.delete_message(message.chat.id, prompt_message_id)
            bot.delete_message(message.chat.id, message.message_id)
        except: pass
        return

    # 5. Отримання мови користувача та символу валюти заявки (UAH)
    currency_symbol = get_currency_symbol(currency_code) # Символ UAH
    target_user_data = get_user_data(target_user_id)
    user_lang = target_user_data.get('language', 'uk') if target_user_data else 'uk'

    try:
        # 6. Визначення, чи надано причину
        reject_with_reason = reason_text != REJECT_WITHOUT_REASON_SYMBOL and bool(reason_text)

        if reject_with_reason:
            # --- Відхилення З причиною ---
            logger.info(f"Admin {admin_id} rejected deposit for {target_user_id} with reason: {reason_text}")
            user_notification_key = 'deposit_rejected_with_comment_user'
            admin_confirm_key = 'admin_action_confirmed_reject_comment'
            user_notification_text = get_text(user_notification_key, user_lang).format(
                # Сума в повідомленні користувачу - заявлена сума
                amount=f"{requested_amount:.2f}", # Форматуємо Decimal
                currency=currency_symbol, # UAH
                reason=reason_text
            )
            admin_confirm_text = get_text(admin_confirm_key, admin_lang).format(user_id=target_user_id)
            final_admin_text = f"{original_admin_message_text}\n\n---\n{admin_confirm_text}\nПричина: {reason_text}"
        else:
            # --- Відхилення БЕЗ причини ---
            logger.info(f"Admin {admin_id} rejected deposit for {target_user_id} without explicit reason.")
            user_notification_key = 'deposit_rejected_user'
            admin_confirm_key = 'admin_action_confirmed_reject'
            user_notification_text = get_text(user_notification_key, user_lang).format(
                # Сума в повідомленні користувачу - заявлена сума
                amount=f"{requested_amount:.2f}", # Форматуємо Decimal
                currency=currency_symbol # UAH
            )
            admin_confirm_text = get_text(admin_confirm_key, admin_lang).format(user_id=target_user_id)
            final_admin_text = f"{original_admin_message_text}\n\n---\n{admin_confirm_text}"

        # 7. Надсилання повідомлення користувачу
        try:
            bot.send_message(
                target_user_id,
                user_notification_text,
                reply_markup=get_main_keyboard(user_lang)
            )
            logger.info(f"Rejection notification sent to user {target_user_id}")
        except telebot.apihelper.ApiTelegramException as e:
            logger.error(f"Failed to send rejection notification to user {target_user_id}: {e}")
            final_admin_text += f"\n\n⚠️ Не вдалося сповістити користувача: {e.error_code}"
        except Exception as e:
            logger.error(f"Unexpected error sending rejection notification to user {target_user_id}: {e}")
            final_admin_text += f"\n\n⚠️ Не вдалося сповістити користувача (інша помилка)."

        # 8. Оновлення повідомлення в чаті підтверджень
        bot.edit_message_text(
            final_admin_text,
            chat_id=CONFIRMATION_CHAT_ID,
            message_id=clicked_text_msg_id,
            reply_markup=None # Видаляємо кнопки
        )
        logger.info(f"Admin confirmation message {clicked_text_msg_id} updated for rejection.")

        # 9. Видалення запиту з карти підтверджень
        if clicked_text_msg_id in confirmation_message_map:
            del confirmation_message_map[clicked_text_msg_id]
            logger.info(f"Removed confirmation data for message {clicked_text_msg_id}")

    except Exception as e:
        logger.error(f"Error processing rejection reason from admin {admin_id}: {e}")
        try:
            reply_params = ReplyParameters(message_id=clicked_text_msg_id) if clicked_text_msg_id else None
            bot.send_message(
                CONFIRMATION_CHAT_ID,
                f"⚠️ Сталася помилка при обробці відхилення: {str(e)}",
                reply_parameters=reply_params
            )
        except Exception as e2:
            logger.error(f"Also failed to send error message to admin chat: {e2}")
    finally:
        # 10. Очищення стану адміна
        clear_admin_state(admin_id)

        # 11. Видалення повідомлення-запиту причини та відповіді адміна
        try:
            if prompt_message_id: # Видаляємо запит, ID якого зберегли
                bot.delete_message(message.chat.id, prompt_message_id)
            bot.delete_message(message.chat.id, message.message_id) # Видаляємо відповідь адміна
            logger.info(f"Deleted reason prompt and admin reply message in chat {message.chat.id}")
        except Exception as e:
            logger.warning(f"Could not delete reason messages in chat {message.chat.id}: {e}")

def process_approve_amount(message):
    """Обробляє введену адміном суму для зарахування (в UAH)."""
    admin_id = message.from_user.id
    amount_text = message.text.strip()
    admin_state_info = get_admin_state(admin_id)
    admin_lang = 'uk'

    # 1. Перевірка стану адміна
    if not admin_state_info or admin_state_info.get('state') != 'awaiting_approve_amount':
        logger.warning(f"Admin {admin_id} sent text '{amount_text}' but not in 'awaiting_approve_amount' state.")
        if message.reply_to_message and message.reply_to_message.from_user.is_bot:
            try:
                reply_params = ReplyParameters(message_id=message.message_id)
                bot.send_message(message.chat.id, get_text('admin_not_awaiting_approve_amount', admin_lang), reply_parameters=reply_params)
            except Exception as e:
                logger.error(f"Failed to send state error to admin {admin_id}: {e}")
        return

    # 2. Обробка /cancel - обробляється окремим хендлером

    # 3. Отримання даних зі стану адміна
    state_data = admin_state_info.get('data', {})
    prompt_message_id = state_data.get('prompt_message_id')
    target_user_id = state_data.get('user_id')
    # Заявлена сума і валюта (UAH)
    requested_amount = state_data.get('requested_amount') # Decimal
    currency_code = state_data.get('currency') # UAH (валюта заявки і суми, яку вводить адмін)
    clicked_text_msg_id = state_data.get('clicked_text_msg_id')
    original_admin_message_text = state_data.get('original_caption')
    photo_msg_id = state_data.get('photo_msg_id')
    method_code = state_data.get('method')

    # 4. Перевірка даних
    if not all([target_user_id, requested_amount is not None, currency_code, clicked_text_msg_id, original_admin_message_text, photo_msg_id]):
        logger.error(f"Incomplete data found in admin state 'awaiting_approve_amount' for admin {admin_id}. Data: {state_data}")
        try:
            reply_params = ReplyParameters(message_id=clicked_text_msg_id) if clicked_text_msg_id else None
            bot.send_message(CONFIRMATION_CHAT_ID,
                             "⚠️ Помилка: Недостатньо даних для обробки зарахування. Дія скасована.",
                             reply_parameters=reply_params)
        except Exception as e:
            logger.error(f"Failed to send data error message to admin chat: {e}")
        clear_admin_state(admin_id)
        # Спробувати видалити повідомлення-запит та відповідь адміна
        try:
            if prompt_message_id: bot.delete_message(message.chat.id, prompt_message_id)
            bot.delete_message(message.chat.id, message.message_id)
        except: pass
        return

    # 5. Отримання даних користувача (мова, поточна валюта)
    target_user_data = get_user_data(target_user_id)
    if not target_user_data:
        logger.error(f"Cannot find target user {target_user_id} data for approval.")
        try:
            reply_params = ReplyParameters(message_id=clicked_text_msg_id) if clicked_text_msg_id else None
            bot.send_message(CONFIRMATION_CHAT_ID,
                             f"⚠️ Помилка: Не знайдено дані користувача {target_user_id}.",
                             reply_parameters=reply_params)
        except Exception as e:
            logger.error(f"Failed to send user not found error message to admin chat: {e}")
        clear_admin_state(admin_id)
        # Спробувати видалити повідомлення-запит та відповідь адміна
        try:
            if prompt_message_id: bot.delete_message(message.chat.id, prompt_message_id)
            bot.delete_message(message.chat.id, message.message_id)
        except: pass
        return

    user_lang = target_user_data.get('language', 'uk')
    user_currency_code = target_user_data.get('currency', 'UAH') # Поточна валюта користувача
    user_currency_symbol = get_currency_symbol(user_currency_code)

    try:
        # 6. Парсинг та валідація введеної суми (яка має бути в UAH)
        credited_amount_uah = decimal.Decimal(amount_text.replace(',', '.'))
        if credited_amount_uah <= 0:
            raise ValueError("Amount must be positive")

        # Округлення до 2 знаків
        credited_amount_uah = credited_amount_uah.quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)

        # 7. Оновлення балансу користувача
        # Функція update_user_balance сама виконає конвертацію credited_amount_uah (в UAH) до user_currency_code
        if update_user_balance(target_user_id, credited_amount_uah, 'UAH'):
            # --- Успішне зарахування ---
            logger.info(f"Admin {admin_id} approved deposit for {target_user_id}. Credited {credited_amount_uah} UAH (will be converted if needed).")

            # Потрібно отримати оновлений баланс і валюту користувача для повідомлень
            updated_user_data = get_user_data(target_user_id)
            # Щоб отримати, *скільки саме* було додано У ВАЛЮТІ КОРИСТУВАЧА, треба конвертувати credited_amount_uah
            amount_credited_in_user_currency = convert_currency(credited_amount_uah, 'UAH', user_currency_code)
            if amount_credited_in_user_currency is None:
                # Якщо конвертація не вдалася вже ПІСЛЯ оновлення балансу (дуже малоймовірно),
                # показуємо хоча б суму в UAH
                logger.error(f"Could not convert credited amount {credited_amount_uah} UAH to {user_currency_code} for notifications, though balance update succeeded.")
                amount_credited_in_user_currency = credited_amount_uah # Fallback to UAH amount
                notify_currency_symbol = get_currency_symbol('UAH')
                notify_currency_code = 'UAH'
            else:
                notify_currency_symbol = user_currency_symbol
                notify_currency_code = user_currency_code


            # Повідомлення для користувача (показуємо зараховану суму у ВАЛЮТІ КОРИСТУВАЧА)
            user_notification_text = get_text('deposit_approved_user', user_lang).format(
                amount=f"{amount_credited_in_user_currency:.2f}",
                currency=notify_currency_symbol
            )
            # Повідомлення для адміна
            admin_confirm_text = get_text('admin_action_confirmed_approve', admin_lang).format(
                user_id=target_user_id,
                credited_amount=f"{amount_credited_in_user_currency:.2f}", # У валюті користувача (або UAH як fallback)
                currency=notify_currency_symbol # Символ валюти користувача (або UAH)
            )
            # Якщо валюта користувача відрізняється від UAH і конвертація вдалася, додаємо інформацію про оригінальну суму в UAH
            if currency_code != user_currency_code and notify_currency_code == user_currency_code:
                admin_confirm_text += f" (з {credited_amount_uah:.2f} {get_currency_symbol('UAH')})" # В дужках сума, яку ввів адмін (в UAH)

            final_admin_text = f"{original_admin_message_text}\n\n---\n{admin_confirm_text}"

            # Надсилаємо повідомлення користувачу
            try:
                bot.send_message(target_user_id, user_notification_text, reply_markup=get_main_keyboard(user_lang))
                logger.info(f"Approval notification sent to user {target_user_id}")
            except telebot.apihelper.ApiTelegramException as e:
                logger.error(f"Failed to send approval notification to user {target_user_id}: {e}")
                final_admin_text += f"\n\n⚠️ Не вдалося сповістити користувача: {e.error_code}"
            except Exception as e:
                logger.error(f"Unexpected error sending approval notification to user {target_user_id}: {e}")
                final_admin_text += f"\n\n⚠️ Не вдалося сповістити користувача (інша помилка)."

            # Оновлення повідомлення в чаті підтверджень
            bot.edit_message_text(
                final_admin_text,
                chat_id=CONFIRMATION_CHAT_ID,
                message_id=clicked_text_msg_id,
                reply_markup=None # Видаляємо кнопки
            )
            logger.info(f"Admin confirmation message {clicked_text_msg_id} updated for approval.")

            # Видалення запиту з карти підтверджень
            if clicked_text_msg_id in confirmation_message_map:
                del confirmation_message_map[clicked_text_msg_id]
                logger.info(f"Removed confirmation data for message {clicked_text_msg_id}")

            # Очищення стану адміна
            clear_admin_state(admin_id)

            # Видалення повідомлення-запиту суми та відповіді адміна
            try:
                if prompt_message_id:
                    bot.delete_message(message.chat.id, prompt_message_id)
                bot.delete_message(message.chat.id, message.message_id)
                logger.info(f"Deleted amount prompt and admin reply message in chat {message.chat.id}")
            except Exception as e:
                logger.warning(f"Could not delete amount messages in chat {message.chat.id}: {e}")

        else:
            # --- Помилка оновлення балансу ---
            # Причина помилки (ймовірно, помилка конвертації) вже залогована в update_user_balance/convert_currency
            logger.error(f"Failed to update balance for user {target_user_id} during approval process by admin {admin_id}.")
            try:
                reply_params = ReplyParameters(message_id=clicked_text_msg_id) if clicked_text_msg_id else None
                admin_error_text = get_text('balance_update_failed_admin', admin_lang).format(user_id=target_user_id)
                # Спробуємо додати текст помилки конвертації, якщо вона була
                if currency_code != user_currency_code:
                    admin_error_text += f" ({get_text('currency_conversion_error', admin_lang).format(from_curr=currency_code, to_curr=user_currency_code)})"

                bot.send_message(CONFIRMATION_CHAT_ID,
                                 admin_error_text,
                                 reply_parameters=reply_params)
            except Exception as e_msg:
                logger.error(f"Failed to send balance update error message to admin chat: {e_msg}")

            # Не чистимо стан адміна, щоб він міг використати /cancel або спробувати знову
            # Повторно запитуємо суму
            try:
                error_msg_reply = get_text('invalid_approve_amount', admin_lang) + f"\n({get_text('balance_update_failed_admin', admin_lang).format(user_id=target_user_id)})"
                if currency_code != user_currency_code:
                    error_msg_reply += f"\n({get_text('currency_conversion_error', admin_lang).format(from_curr=currency_code, to_curr=user_currency_code)})"
                reply_params_force = ReplyParameters(message_id=message.message_id) # Відповідаємо на повідомлення адміна
                prompt_msg = bot.send_message(message.chat.id, error_msg_reply, reply_markup=types.ForceReply(selective=True), reply_parameters=reply_params_force)
                admin_states[admin_id]['data']['prompt_message_id'] = prompt_msg.message_id # Оновлюємо ID запиту
            except Exception as e_prompt:
                logger.error(f"Failed to re-prompt admin for amount after balance update error: {e_prompt}")
                clear_admin_state(admin_id) # Якщо навіть запитати не вдалося, чистимо стан


    except (ValueError, decimal.InvalidOperation):
        # --- Невірна сума введена адміном ---
        logger.warning(f"Invalid approve amount entered by admin {admin_id}: {amount_text}")
        try:
            # Повторно запитуємо суму, зберігаючи ID нового запиту
            error_msg = get_text('invalid_approve_amount', admin_lang)
            reply_params_force = ReplyParameters(message_id=message.message_id) # Відповідаємо на невірне повідомлення адміна
            prompt_msg = bot.send_message(message.chat.id, error_msg, reply_markup=types.ForceReply(selective=True), reply_parameters=reply_params_force)
            admin_states[admin_id]['data']['prompt_message_id'] = prompt_msg.message_id # Оновлюємо ID запиту
        except Exception as e:
            logger.error(f"Failed to resend invalid amount message to admin {admin_id}: {e}")
            clear_admin_state(admin_id) # Очищуємо стан, якщо навіть запитати не вдалося
            try:
                reply_p = ReplyParameters(message_id=clicked_text_msg_id) if clicked_text_msg_id else None
                bot.send_message(CONFIRMATION_CHAT_ID, get_text('callback_error', admin_lang), reply_parameters=reply_p)
            except: pass
    except Exception as e:
        # --- Інша помилка ---
        logger.error(f"Error processing approve amount from admin {admin_id}: {e}")
        logger.exception("Traceback:")
        try:
            reply_params = ReplyParameters(message_id=clicked_text_msg_id) if clicked_text_msg_id else None
            bot.send_message(
                CONFIRMATION_CHAT_ID,
                f"⚠️ Сталася помилка при обробці зарахування: {str(e)}",
                reply_parameters=reply_params
            )
        except Exception as e2:
            logger.error(f"Also failed to send error message to admin chat: {e2}")
        # Залишаємо стан адміна для можливого /cancel

def process_support_reply(message):
    """Обробляє текст відповіді адміністратора на запит користувача в чаті підтримки."""
    admin_id = message.from_user.id
    reply_text = message.text.strip()
    admin_state_info = get_admin_state(admin_id)
    admin_lang = 'uk'

    # 1. Перевірка стану адміна
    if not admin_state_info or admin_state_info.get('state') != 'awaiting_support_reply':
        logger.warning(f"Admin {admin_id} sent text '{reply_text}' but not in 'awaiting_support_reply' state.")
        if message.reply_to_message and message.reply_to_message.from_user.is_bot:
            try:
                reply_params = ReplyParameters(message_id=message.message_id)
                bot.send_message(message.chat.id, get_text('admin_not_awaiting_support_reply', admin_lang), reply_parameters=reply_params)
            except Exception as e:
                logger.error(f"Failed to send state error to admin {admin_id}: {e}")
        return

    # 2. Обробка /cancel - обробляється окремим хендлером

    # 3. Отримання даних зі стану адміна
    state_data = admin_state_info.get('data', {})
    prompt_message_id = state_data.get('prompt_message_id') # ID запиту відповіді
    original_support_msg_id = state_data.get('support_msg_id') # ID оригінального повідомлення від бота в чаті підтримки
    target_user_id = state_data.get('target_user_id')

    # 4. Перевірка даних
    if not target_user_id or not original_support_msg_id:
        logger.error(f"Incomplete data found in admin state 'awaiting_support_reply' for admin {admin_id}. Data: {state_data}")
        try:
            reply_params = ReplyParameters(message_id=original_support_msg_id) if original_support_msg_id else None
            bot.send_message(SUPPORT_CHAT_ID,
                             "⚠️ Помилка: Недостатньо даних для надсилання відповіді. Дія скасована.",
                             reply_parameters=reply_params)
        except Exception as e:
            logger.error(f"Failed to send data error message to support chat: {e}")
        clear_admin_state(admin_id)
        # Спробувати видалити повідомлення-запит та відповідь адміна
        try:
            if prompt_message_id: bot.delete_message(message.chat.id, prompt_message_id)
            bot.delete_message(message.chat.id, message.message_id)
        except: pass
        return

    # 5. Надсилання відповіді користувачу
    try:
        target_user_data = get_user_data(target_user_id)
        user_lang = target_user_data.get('language', 'uk') if target_user_data else 'uk'
        reply_message_to_user = get_text('support_reply', user_lang).format(reply_text=reply_text)

        bot.send_message(target_user_id, reply_message_to_user, reply_markup=get_main_keyboard(user_lang))
        logger.info(f"Support reply successfully sent to user {target_user_id} by admin {admin_id}")

        # Повідомлення адміну про успішну відправку (відповідь на його повідомлення)
        reply_params_admin = ReplyParameters(message_id=message.message_id)
        bot.send_message(message.chat.id, get_text('support_reply_sent', admin_lang).format(user_id=target_user_id), reply_parameters=reply_params_admin)

    except telebot.apihelper.ApiTelegramException as e:
        logger.error(f"Failed to send support reply to user {target_user_id}: {e}")
        error_text_for_admin = get_text('support_reply_failed', admin_lang).format(user_id=target_user_id, e=f"{e.error_code} - {e.description}")
        try:
            reply_params_err = ReplyParameters(message_id=message.message_id)
            bot.send_message(message.chat.id, error_text_for_admin, reply_parameters=reply_params_err)
        except Exception as e2:
            logger.error(f"Also failed to send error reply to admin {admin_id} in support chat: {e2}")
    except Exception as e:
        logger.error(f"Unexpected error sending support reply to user {target_user_id}: {e}")
        error_text_for_admin = get_text('support_reply_failed', admin_lang).format(user_id=target_user_id, e=str(e))
        try:
            reply_params_err = ReplyParameters(message_id=message.message_id)
            bot.send_message(message.chat.id, error_text_for_admin, reply_parameters=reply_params_err)
        except Exception as e2:
            logger.error(f"Also failed to send error reply to admin {admin_id} in support chat: {e2}")
    finally:
        # 6. Очищення стану адміна
        clear_admin_state(admin_id)
        # 7. Видалення повідомлення-запиту та відповіді адміна
        try:
            if prompt_message_id:
                bot.delete_message(message.chat.id, prompt_message_id)
            bot.delete_message(message.chat.id, message.message_id) # Видаляємо відповідь адміна
            logger.info(f"Deleted support reply prompt and admin reply message in chat {message.chat.id}")
        except Exception as e:
            logger.warning(f"Could not delete support reply messages in chat {message.chat.id}: {e}")


# --- Обробник натискань Inline кнопок ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """Обробляє натискання на Inline кнопки."""
    user_id = call.from_user.id # ID користувача, що натиснув кнопку
    callback_data = call.data
    message = call.message
    chat_id = message.chat.id

    admin_lang = 'uk' # Мова для повідомлень в адмін чатах

    try:
        # Відповідаємо на callback одразу, крім випадку перевірки підписки
        # де ми хочемо показати alert
        if callback_data != 'check_subscription_callback':
             bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"Error answering callback query {call.id}: {e}")

    # --- Обробка дій адміна в чаті ПІДТВЕРДЖЕННЯ ---
    if chat_id == CONFIRMATION_CHAT_ID:
        logger.info(f"Admin {user_id} initiated callback in confirmation chat: {callback_data}")

        match = re.match(r"confirm_(\d+)_(approve_prompt|reject_now|reject_comment)", callback_data)
        if match:
            clicked_text_msg_id = int(match.group(1))
            action = match.group(2)
            logger.info(f"Admin action: {action} for text message {clicked_text_msg_id}")

            deposit_data = confirmation_message_map.get(clicked_text_msg_id)

            if not deposit_data:
                logger.warning(f"Confirmation data not found or already processed for message_id {clicked_text_msg_id}. Callback from admin {user_id}")
                try:
                    bot.edit_message_text(
                        f"{message.text}\n\n---\n⚠️ Запит вже оброблено або дані не знайдено.",
                        chat_id=CONFIRMATION_CHAT_ID,
                        message_id=clicked_text_msg_id,
                        reply_markup=None
                    )
                except Exception as e:
                    logger.error(f"Failed to edit message {clicked_text_msg_id} to show 'already processed': {e}")
                return

            # Дані, отримані з confirmation_message_map
            target_user_id = deposit_data['user_id']
            requested_amount = deposit_data['requested_amount'] # Decimal
            currency_code = deposit_data['currency'] # UAH (валюта заявки)
            photo_msg_id = deposit_data['photo_msg_id']
            method_code = deposit_data.get('method')
            target_username = deposit_data.get('username', 'N/A')
            target_user_lang = deposit_data.get('user_lang', 'uk')
            original_admin_message_text = message.text # Зберігаємо оригінальний текст

            # Отримуємо поточну валюту користувача для відображення в запиті адміну
            target_user_info = get_user_data(target_user_id)
            target_user_currency = target_user_info.get('currency', 'UAH') if target_user_info else 'UAH'

            try:
                if action == 'approve_prompt':
                    # --- Запит суми для зарахування ---
                    logger.info(f"Admin {user_id} chose 'approve' for user {target_user_id}. Prompting for amount.")
                    prompt_text = get_text('admin_approve_prompt', admin_lang).format(
                        user_id=target_user_id,
                        username=target_username,
                        currency=currency_code, # Завжди UAH тут (валюта, в якій вводить адмін)
                        requested_amount=f"{requested_amount:.2f}", # Форматуємо Decimal
                        user_currency=target_user_currency # Поточна валюта користувача
                    )
                    # Надсилаємо запит суми як відповідь на повідомлення з кнопками
                    reply_params_force = ReplyParameters(message_id=clicked_text_msg_id)
                    prompt_msg = bot.send_message(
                        CONFIRMATION_CHAT_ID,
                        prompt_text,
                        reply_parameters=reply_params_force,
                        reply_markup=types.ForceReply(selective=True)
                    )
                    # Зберігаємо стан адміна (user_id - це ID адміна, що натиснув кнопку)
                    admin_data = deposit_data.copy() # Копіюємо дані
                    admin_data['clicked_text_msg_id'] = clicked_text_msg_id
                    admin_data['original_caption'] = original_admin_message_text
                    admin_data['prompt_message_id'] = prompt_msg.message_id # Зберігаємо ID запиту
                    set_admin_state(user_id, 'awaiting_approve_amount', admin_data)
                    # Обробка продовжиться в process_approve_amount

                elif action == 'reject_now':
                    # --- Відхилення без коментаря ---
                    logger.info(f"Admin {user_id} rejected deposit for {target_user_id} (no comment - reject_now)")
                    # Повідомлення користувачу (сума заявлена)
                    user_notification_text = get_text('deposit_rejected_user', target_user_lang).format(
                        amount=f"{requested_amount:.2f}",
                        currency=get_currency_symbol(currency_code) # UAH
                    )
                    # Повідомлення адміну
                    admin_confirm_text = get_text('admin_action_confirmed_reject', admin_lang).format(
                        user_id=target_user_id
                    )
                    final_admin_text = f"{original_admin_message_text}\n\n---\n{admin_confirm_text}"
                    # Надсилаємо користувачу
                    try:
                        bot.send_message(target_user_id, user_notification_text, reply_markup=get_main_keyboard(target_user_lang))
                        logger.info(f"Sent 'reject_now' notification to user {target_user_id}")
                    except Exception as e:
                        logger.error(f"Failed to send 'reject_now' notification to user {target_user_id}: {e}")
                        final_admin_text += f"\n\n⚠️ Не вдалося сповістити користувача: {e}"
                    # Оновлюємо повідомлення адміна
                    bot.edit_message_text(
                        final_admin_text,
                        chat_id=CONFIRMATION_CHAT_ID,
                        message_id=clicked_text_msg_id,
                        reply_markup=None
                    )
                    if clicked_text_msg_id in confirmation_message_map: # Перевірка перед видаленням
                         del confirmation_message_map[clicked_text_msg_id]
                         logger.info(f"Removed confirmation data for message {clicked_text_msg_id} after reject_now")
                    else:
                         logger.warning(f"Attempted to delete confirmation data for {clicked_text_msg_id}, but it was already removed.")


                elif action == 'reject_comment':
                    # --- Запит причини відхилення ---
                    logger.info(f"Admin {user_id} chose 'reject with comment' for user {target_user_id}. Prompting for reason.")
                    prompt_text = get_text('admin_rejection_reason_prompt', admin_lang).format(
                        user_id=target_user_id,
                        symbol=REJECT_WITHOUT_REASON_SYMBOL
                    )
                    reply_params_force = ReplyParameters(message_id=clicked_text_msg_id)
                    prompt_msg = bot.send_message(
                        CONFIRMATION_CHAT_ID,
                        prompt_text,
                        reply_parameters=reply_params_force,
                        reply_markup=types.ForceReply(selective=True)
                    )
                    # Зберігаємо стан адміна (user_id - це ID адміна, що натиснув кнопку)
                    admin_data = deposit_data.copy()
                    admin_data['clicked_text_msg_id'] = clicked_text_msg_id
                    admin_data['original_caption'] = original_admin_message_text
                    admin_data['prompt_message_id'] = prompt_msg.message_id # Зберігаємо ID запиту
                    set_admin_state(user_id, 'awaiting_rejection_reason', admin_data)
                    # Обробка продовжиться в process_rejection_reason

            except telebot.apihelper.ApiTelegramException as e:
                logger.error(f"Telegram API error during admin action '{action}' for msg {clicked_text_msg_id}: {e}")
                final_admin_text_on_error = f"{original_admin_message_text}\n\n---\n⚠️ Помилка обробки: {e.error_code}"
                try:
                    bot.edit_message_text(final_admin_text_on_error, chat_id=CONFIRMATION_CHAT_ID, message_id=clicked_text_msg_id, reply_markup=None)
                except Exception as e_edit:
                    logger.error(f"Failed even to edit message {clicked_text_msg_id} with error notice: {e_edit}")
            except Exception as e:
                logger.error(f"Unexpected error during admin action '{action}' for msg {clicked_text_msg_id}: {e}")
                logger.exception("Traceback for admin action error:")
                final_admin_text_on_error = f"{original_admin_message_text}\n\n---\n⚠️ Неочікувана помилка обробки!"
                try:
                    bot.edit_message_text(final_admin_text_on_error, chat_id=CONFIRMATION_CHAT_ID, message_id=clicked_text_msg_id, reply_markup=None)
                except Exception as e_edit:
                    logger.error(f"Failed even to edit message {clicked_text_msg_id} with error notice: {e_edit}")
        else:
             logger.warning(f"Unknown callback format received in confirmation chat: {callback_data}")
        return # Завершуємо обробку для цього чату

    # --- Обробка дій адміна в чаті ПІДТРИМКИ ---
    elif chat_id == SUPPORT_CHAT_ID:
        logger.info(f"Admin {user_id} initiated callback in support chat: {callback_data}")
        reply_match = re.match(r"reply_support_(\d+)_(\d+)", callback_data)
        if reply_match:
            target_user_id = int(reply_match.group(1))
            support_msg_id = int(reply_match.group(2)) # ID оригінального повідомлення від бота в чаті підтримки
            logger.info(f"Admin {user_id} clicked 'Reply' button for user {target_user_id} on support message {support_msg_id}")

            # Отримуємо username користувача з мапи, якщо є
            support_info = support_message_map.get(support_msg_id)
            target_username = support_info.get('username', 'N/A') if support_info else 'N/A'

            # Запитуємо текст відповіді
            prompt_text = get_text('admin_support_reply_prompt', admin_lang).format(
                user_id=target_user_id,
                username=target_username
            )
            try:
                # Відповідаємо на оригінальне повідомлення бота в підтримці
                reply_params_force = ReplyParameters(message_id=support_msg_id)
                prompt_msg = bot.send_message(
                    SUPPORT_CHAT_ID,
                    prompt_text,
                    reply_parameters=reply_params_force,
                    reply_markup=types.ForceReply(selective=True)
                )
                # Зберігаємо стан адміна (user_id - ID адміна, що натиснув)
                admin_data = {
                    'target_user_id': target_user_id,
                    'support_msg_id': support_msg_id, # ID оригінального повідомлення
                    'prompt_message_id': prompt_msg.message_id # ID запиту відповіді
                }
                set_admin_state(user_id, 'awaiting_support_reply', admin_data)
                logger.info(f"Set admin state to 'awaiting_support_reply' for admin {user_id}")
            except Exception as e:
                logger.error(f"Failed to prompt admin {user_id} for support reply: {e}")
                # Повідомляємо адміна про помилку в чаті підтримки
                bot.send_message(SUPPORT_CHAT_ID, get_text('callback_error', admin_lang))
        else:
             logger.warning(f"Unknown callback format received in support chat: {callback_data}")
        return # Завершуємо обробку для цього чату

    # --- Обробка дій користувача в ПРИВАТНОМУ чаті ---
    elif chat_id == user_id:
        logger.info(f"User {user_id} initiated callback in private chat: {callback_data}")
        user_data = get_user_data(user_id)
        if not user_data:
            logger.warning(f"Callback query from unknown or uninitialized user {user_id}: {callback_data}")
            try:
                # Навіть якщо даних немає, спробуємо надіслати запит на підписку
                # Мова за замовчуванням 'uk'
                if not check_subscription(user_id):
                    send_subscribe_prompt_in_callback(call, 'uk')
                else:
                    # Якщо підписаний, але даних немає, просимо /start
                    bot.answer_callback_query(call.id)
                    bot.edit_message_text(get_text('callback_user_not_found', 'uk'), chat_id=chat_id, message_id=message.message_id, reply_markup=None)
            except Exception as e:
                logger.error(f"Error handling callback for unknown user {user_id}: {e}")
            return

        lang = user_data.get('language', 'uk')

        # --- Перевірка підписки ---
        # Перевіряємо перед обробкою будь-якого callback від користувача
        if callback_data != 'check_subscription_callback': # Не перевіряємо саму кнопку перевірки
            if not check_subscription(user_id):
                send_subscribe_prompt_in_callback(call, lang)
                return
        # --- Кінець перевірки підписки ---


        user_state_info = get_user_state(user_id)
        state_name = user_state_info.get('state') if user_state_info else None
        state_data = user_state_info.get('data', {}) if user_state_info else {}

        try:
            # --- Обробка кнопки перевірки підписки ---
            if callback_data == 'check_subscription_callback':
                if check_subscription(user_id):
                    # Підписка є, видаляємо повідомлення і показуємо головне меню
                    bot.answer_callback_query(call.id, get_text('subscription_verified', lang))
                    try:
                        bot.delete_message(chat_id, message.message_id)
                    except Exception as e_del:
                         logger.warning(f"Could not delete subscribe prompt message {message.message_id} after successful check: {e_del}")
                    # Надіслати стартове повідомлення знову
                    start_command(message) # Викликаємо /start логіку
                else:
                    # Підписки немає, повідомляємо користувача
                    bot.answer_callback_query(call.id, get_text('subscription_needed', lang), show_alert=True)
                return # Завершуємо обробку цього callback

            # --- Флоу поповнення ---
            elif callback_data.startswith('select_method_'):
                if state_name != 'awaiting_payment_method':
                    logger.warning(f"User {user_id} clicked payment method '{callback_data}' but not in correct state ({state_name}). Ignoring.")
                    bot.send_message(chat_id, get_text('invalid_step', lang), reply_markup=get_main_keyboard(lang))
                    clear_user_state(user_id)
                    try: bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                    except: pass
                    return

                method_code = callback_data.split('_')[-1]
                if method_code in PAYMENT_DETAILS:
                    amount = state_data.get('amount') # Decimal
                    currency_code = state_data.get('currency') # UAH

                    if amount is None or currency_code is None:
                        logger.error(f"Missing amount/currency in state 'awaiting_payment_method' for user {user_id}. State: {state_data}")
                        bot.send_message(chat_id, get_text('callback_error', lang), reply_markup=get_main_keyboard(lang))
                        clear_user_state(user_id)
                        try: bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                        except: pass
                        return

                    currency_symbol = get_currency_symbol(currency_code)
                    details = PAYMENT_DETAILS[method_code]
                    method_name = get_text(f'payment_method_{method_code}', lang)

                    state_data['method'] = method_code
                    set_user_state(user_id, 'awaiting_screenshot', state_data)

                    instructions = get_text('payment_instructions', lang).format(
                        amount=f"{amount:.2f}", # Format Decimal
                        currency=currency_symbol,
                        method=method_name,
                        details=details
                    )
                    bot.edit_message_text(
                        instructions,
                        chat_id=chat_id,
                        message_id=message.message_id,
                        reply_markup=get_cancel_deposit_keyboard(lang),
                        parse_mode='Markdown'
                    )
                else:
                    logger.error(f"Invalid payment method code in callback: {method_code} from user {user_id}")
                    bot.send_message(chat_id, get_text('callback_error', lang))
                    clear_user_state(user_id)
                    try: bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                    except: pass

            elif callback_data == 'cancel_deposit_amount':
                if state_name == 'awaiting_payment_method':
                    clear_user_state(user_id)
                    bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                    bot.send_message(chat_id, get_text('deposit_cancelled', lang), reply_markup=get_main_keyboard(lang))
                else:
                    logger.warning(f"User {user_id} clicked cancel_deposit_amount but not in correct state ({state_name})")
                    try: bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                    except: pass

            elif callback_data == 'cancel_deposit_screenshot':
                if state_name == 'awaiting_screenshot':
                    clear_user_state(user_id)
                    bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                    bot.send_message(chat_id, get_text('deposit_cancelled', lang), reply_markup=get_main_keyboard(lang))
                else:
                    logger.warning(f"User {user_id} clicked cancel_deposit_screenshot but not in correct state ({state_name})")
                    try: bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                    except: pass

            elif callback_data == 'back_to_methods':
                if state_name == 'awaiting_screenshot':
                    amount = state_data.get('amount') # Decimal
                    currency_code = state_data.get('currency') # UAH

                    if amount is None or currency_code is None:
                        logger.error(f"Missing amount/currency in state 'awaiting_screenshot' for user {user_id} when going back. State: {state_data}")
                        bot.send_message(chat_id, get_text('callback_error', lang), reply_markup=get_main_keyboard(lang))
                        clear_user_state(user_id)
                        try: bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                        except: pass
                        return

                    if 'method' in state_data: del state_data['method']
                    set_user_state(user_id, 'awaiting_payment_method', state_data)

                    currency_symbol = get_currency_symbol(currency_code)
                    bot.edit_message_text(
                        get_text('select_payment_method', lang).format(amount=f"{amount:.2f}", currency=currency_symbol),
                        chat_id=chat_id,
                        message_id=message.message_id,
                        reply_markup=get_payment_method_keyboard(lang)
                    )
                else:
                    logger.warning(f"User {user_id} clicked back_to_methods but not in correct state ({state_name})")
                    try: bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                    except: pass

            # --- Налаштування ---
            elif callback_data == 'settings_change_lang':
                bot.edit_message_text(
                    get_text('select_lang', lang),
                    chat_id=chat_id,
                    message_id=message.message_id,
                    reply_markup=get_language_keyboard(lang)
                )
            elif callback_data == 'settings_change_curr':
                bot.edit_message_text(
                    get_text('select_curr', lang),
                    chat_id=chat_id,
                    message_id=message.message_id,
                    reply_markup=get_currency_keyboard(lang)
                )
            elif callback_data == 'settings_back':
                try:
                    bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                except Exception as e:
                    logger.warning(f"Could not delete settings message {message.message_id}: {e}")
                # Головна клавіатура вже повинна бути видима

            elif callback_data.startswith('set_lang_'):
                new_lang = callback_data.split('_')[-1]
                if new_lang in texts:
                    if update_user_language(user_id, new_lang):
                        try:
                            # --- КЛЮЧОВА ЗМІНА: Редагуємо повідомлення, показуючи меню налаштувань НОВОЮ мовою ---
                            bot.edit_message_text(
                                get_text('settings_menu', new_lang), # Текст меню налаштувань новою мовою
                                chat_id=chat_id,
                                message_id=message.message_id,
                                reply_markup=get_settings_keyboard(new_lang) # Клавіатура налаштувань новою мовою
                            )
                            # --- КЛЮЧОВА ЗМІНА: Надсилаємо підтвердження З ОНОВЛЕНОЮ ReplyKeyboard ---
                            bot.send_message(
                                chat_id,
                                get_text('lang_changed', new_lang), # Повідомлення про зміну мови
                                reply_markup=get_main_keyboard(new_lang) # Надсилаємо з головною клавіатурою новою мовою
                            )
                        except telebot.apihelper.ApiTelegramException as e:
                            if "message is not modified" in str(e).lower():
                                # Якщо повідомлення не змінилося (наприклад, клацнули ту саму мову)
                                # все одно надішлемо підтвердження для оновлення клавіатури
                                logger.info(f"Language message not modified for user {user_id}, sending confirmation anyway.")
                                try:
                                    bot.send_message(
                                        chat_id,
                                        get_text('lang_changed', new_lang),
                                        reply_markup=get_main_keyboard(new_lang)
                                    )
                                except Exception as send_e:
                                     logger.error(f"Failed to send lang_changed confirmation after 'not modified' error for user {user_id}: {send_e}")
                            else:
                                logger.error(f"Error editing language message or sending confirmation for user {user_id}: {e}")
                                try:
                                    # Використовуємо new_lang, бо стара вже могла бути оновлена в БД
                                    bot.send_message(chat_id, get_text('callback_error', new_lang))
                                except Exception as send_e:
                                     logger.error(f"Failed even to send callback error message after edit/send failure for user {user_id}: {send_e}")
                        except Exception as e:
                             logger.error(f"Unexpected error after updating language for user {user_id}: {e}")
                             try:
                                 bot.send_message(chat_id, get_text('callback_error', new_lang))
                             except Exception as send_e:
                                 logger.error(f"Failed even to send callback error message after unexpected error for user {user_id}: {send_e}")
                    else:
                        logger.error(f"Failed to update language for user {user_id} to {new_lang} in DB.")
                        try:
                             bot.edit_message_text(
                                 get_text('callback_error', lang), # Використовуємо СТАРУ мову
                                 chat_id=chat_id,
                                 message_id=message.message_id,
                                 reply_markup=None
                             )
                        except Exception as e_edit:
                            logger.error(f"Failed to edit language message with DB error notice for user {user_id}: {e_edit}")
                else:
                    logger.warning(f"Invalid language code in callback: {new_lang} from user {user_id}")
                    try:
                        bot.edit_message_text(get_text('callback_error', lang), chat_id=chat_id, message_id=message.message_id, reply_markup=None)
                    except Exception as e_edit:
                         logger.error(f"Failed to edit language message with invalid code error notice for user {user_id}: {e_edit}")

            elif callback_data.startswith('set_curr_'):
                new_curr = callback_data.split('_')[-1]
                if new_curr in currencies:
                    success, new_balance = update_user_currency(user_id, new_curr) # Оновлює валюту і конвертує баланс
                    if success and new_balance is not None:
                        new_currency_symbol = get_currency_symbol(new_curr)
                        confirmation_text = get_text('curr_changed', lang).format(
                            currency=new_curr, # Код валюти
                            balance=f"{new_balance:.2f}", # Новий баланс
                            currency_symbol=new_currency_symbol # Символ валюти
                        )
                        # Повертаємо до меню налаштувань
                        bot.edit_message_text(
                            confirmation_text + "\n\n" + get_text('settings_menu', lang),
                            chat_id=chat_id,
                            message_id=message.message_id,
                            reply_markup=get_settings_keyboard(lang) # Клавіатура налаштувань залишається на старій мові тут, але ReplyKeyboard оновлена
                        )
                    else:
                        # Помилка вже залогована в update_user_currency/convert_currency
                        error_msg = get_text('callback_error', lang) + f"\n{get_text('currency_conversion_error', lang).format(from_curr=user_data.get('currency', 'N/A'), to_curr=new_curr)}"
                        try:
                            # Спочатку видаляємо старе повідомлення, потім надсилаємо нове
                            bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                            bot.send_message(chat_id, error_msg, reply_markup=get_main_keyboard(lang))
                            # Показуємо меню налаштувань знову (або головне меню)
                            # show_settings(message, lang) # Це не спрацює, бо message тут - це callback query message
                            bot.send_message(chat_id, get_text('main_menu', lang), reply_markup=get_main_keyboard(lang))
                        except Exception as e_err:
                            logger.error(f"Failed to send currency conversion error to user {user_id}: {e_err}")

                else:
                    logger.warning(f"Invalid currency code in callback: {new_curr}")
                    bot.send_message(chat_id, get_text('callback_error', lang))

            elif callback_data == 'lang_back' or callback_data == 'curr_back':
                bot.edit_message_text(
                    get_text('settings_menu', lang),
                    chat_id=chat_id,
                    message_id=message.message_id,
                    reply_markup=get_settings_keyboard(lang)
                )

            # --- Купівля номера (заглушка) ---
            elif callback_data.startswith('buy_country_'):
                country_code = callback_data.split('_')[-1]
                country_name_key = f'country_{country_code.lower()}'
                country_name = get_text(country_name_key, lang)
                bot.edit_message_text(
                    get_text('country_selected', lang).format(country=country_name),
                    chat_id=chat_id,
                    message_id=message.message_id,
                    reply_markup=get_back_button('buy_back', lang)
                )
            elif callback_data == 'buy_back':
                bot.edit_message_text(
                    get_text('choose_country', lang),
                    chat_id=chat_id,
                    message_id=message.message_id,
                    reply_markup=get_country_keyboard(lang)
                )

            else:
                logger.warning(f"Unhandled callback_data from user {user_id} in private chat: {callback_data}")

        # --- Обробка специфічних помилок Telegram API ---
        except telebot.apihelper.ApiTelegramException as e:
            error_message = str(e).lower()
            if "message to edit not found" in error_message: logger.warning(f"Message {message.message_id} not found for editing (callback {callback_data}).")
            elif "message is not modified" in error_message: logger.info(f"Message {message.message_id} not modified (callback {callback_data}).")
            elif "message to delete not found" in error_message: logger.warning(f"Message {message.message_id} not found for deleting (callback {callback_data}).")
            elif "chat not found" in error_message or "bot was blocked" in error_message or "user is deactivated" in error_message: logger.warning(f"Cannot interact with user {user_id} (callback {callback_data}): {e}")
            else:
                logger.error(f"Telegram API error on callback {callback_data} from user {user_id}: {e}")
                # Повідомляємо тільки користувача в приватному чаті
                try: bot.send_message(user_id, get_text('callback_error', lang))
                except Exception as send_e: logger.error(f"Failed even to send callback error message to user {user_id}: {send_e}")
        # --- Обробка інших помилок ---
        except Exception as e:
            logger.error(f"Error processing callback {callback_data} from user {user_id}: {e}")
            logger.exception("Traceback for callback processing error:")
            # Повідомляємо тільки користувача в приватному чаті
            try: bot.send_message(user_id, get_text('callback_error', lang))
            except Exception as send_e: logger.error(f"Failed even to send callback error message to user {user_id}: {send_e}")

    # --- Якщо callback прийшов з невідомого чату ---
    else:
        logger.warning(f"Callback {callback_data} received in unexpected chat {chat_id} from user {user_id}. Ignoring.")

# --- Обробник відповідей адміністратора в чаті підтримки (ЧЕРЕЗ REPLY) ---
@bot.message_handler(func=lambda message: message.chat.id == SUPPORT_CHAT_ID and \
                                         message.reply_to_message is not None and \
                                         message.reply_to_message.from_user.is_bot and \
                                         # Перевіряємо, чи є ID повідомлення в нашій мапі
                                         message.reply_to_message.message_id in support_message_map,
                       content_types=['text'])
def handle_support_reply_via_reply(message):
    """Обробляє текстову відповідь адміна на повідомлення користувача в чаті підтримки (через функцію 'reply')."""
    admin = message.from_user
    reply_text = message.text # Текст відповіді адміна
    original_bot_message_id = message.reply_to_message.message_id
    admin_lang = 'uk'

    # Перевірка, чи адмін не в стані відповіді через кнопку (щоб уникнути подвійної обробки)
    admin_state = get_admin_state(admin.id)
    if admin_state and admin_state.get('state') == 'awaiting_support_reply' and admin_state.get('data', {}).get('support_msg_id') == original_bot_message_id:
        logger.info(f"Admin {admin.id} replied via REPLY to support message {original_bot_message_id}, but state 'awaiting_support_reply' is active. Letting state handler process it.")
        return # Дозволяємо обробнику стану process_support_reply спрацювати

    logger.info(f"Admin {admin.id} replied VIA REPLY in support chat to bot message {original_bot_message_id}")
    logger.debug(f"Looking for message_id {original_bot_message_id} in support map: {support_message_map}")

    # Знаходимо ID користувача та username
    support_info = support_message_map.get(original_bot_message_id)

    if support_info and 'user_id' in support_info:
        target_user_id = support_info['user_id']
        try:
            user_data = get_user_data(target_user_id)
            lang = user_data.get('language', 'uk') if user_data else 'uk'
            reply_message_to_user = get_text('support_reply', lang).format(reply_text=reply_text)

            bot.send_message(target_user_id, reply_message_to_user, reply_markup=get_main_keyboard(lang))
            logger.info(f"Support reply (via reply) successfully sent to user {target_user_id}")

            reply_params = ReplyParameters(message_id=message.message_id)
            bot.send_message(message.chat.id, get_text('support_reply_sent', admin_lang).format(user_id=target_user_id), reply_parameters=reply_params)
        except telebot.apihelper.ApiTelegramException as e:
            logger.error(f"Failed to send support reply (via reply) to user {target_user_id}: {e}")
            error_text_for_admin = get_text('support_reply_failed', admin_lang).format(user_id=target_user_id, e=f"{e.error_code} - {e.description}")
            try:
                reply_params_err = ReplyParameters(message_id=message.message_id)
                bot.send_message(message.chat.id, error_text_for_admin, reply_parameters=reply_params_err)
            except Exception as e2: logger.error(f"Also failed to send error reply to admin {admin.id}: {e2}")
        except Exception as e:
            logger.error(f"Unexpected error sending support reply (via reply) to user {target_user_id}: {e}")
            error_text_for_admin = get_text('support_reply_failed', admin_lang).format(user_id=target_user_id, e=str(e))
            try:
                reply_params_err = ReplyParameters(message_id=message.message_id)
                bot.send_message(message.chat.id, error_text_for_admin, reply_parameters=reply_params_err)
            except Exception as e2: logger.error(f"Also failed to send error reply to admin {admin.id}: {e2}")
    else:
        logger.warning(f"Could not find original user_id for replied message {original_bot_message_id} in support chat (via reply). Map: {support_message_map}")
        try:
            reply_params = ReplyParameters(message_id=message.message_id)
            bot.send_message(message.chat.id, get_text('support_user_not_found', admin_lang), reply_parameters=reply_params)
        except Exception as e: logger.error(f"Failed to notify admin about user not found for msg {original_bot_message_id}: {e}")


# --- Обробники текстових повідомлень від Адміністратора (стани) ---
@bot.message_handler(func=lambda message: message.chat.id in [SUPPORT_CHAT_ID, CONFIRMATION_CHAT_ID] and \
                                         message.reply_to_message is not None and \
                                         message.reply_to_message.from_user.is_bot,
                       content_types=['text'])
def handle_admin_state_replies(message):
      """Обробляє відповіді адміністратора на повідомлення-запити від бота (причина відхилення, сума зарахування, відповідь підтримки)."""
      admin_id = message.from_user.id
      admin_state = get_admin_state(admin_id)
      prompt_message_id = message.reply_to_message.message_id # ID повідомлення, на яке адмін відповів

      if not admin_state:
            logger.debug(f"Admin {admin_id} replied to bot message {prompt_message_id}, but no active admin state found.")
            # Додатково перевіряємо, чи це не відповідь на повідомлення підтримки (для reply flow)
            if message.chat.id == SUPPORT_CHAT_ID and prompt_message_id in support_message_map:
                handle_support_reply_via_reply(message) # Спробувати обробити як звичайний reply
            return # Адмін не в стані очікування

      current_state = admin_state.get('state')
      state_prompt_id = admin_state.get('data', {}).get('prompt_message_id')

      # Перевіряємо, чи відповідь дійсно на те повідомлення, яке ми очікували в поточнму стані
      if state_prompt_id != prompt_message_id:
            logger.warning(f"Admin {admin_id} replied to message {prompt_message_id}, but expected reply to {state_prompt_id} for state {current_state}. Ignoring state handler.")
            # Додатково перевіряємо, чи це не відповідь на повідомлення підтримки (для reply flow)
            if message.chat.id == SUPPORT_CHAT_ID and prompt_message_id in support_message_map:
                handle_support_reply_via_reply(message) # Спробувати обробити як звичайний reply
            return

      logger.info(f"Processing admin {admin_id} reply for state {current_state} to prompt {prompt_message_id}")

      if current_state == 'awaiting_rejection_reason' and message.chat.id == CONFIRMATION_CHAT_ID:
            process_rejection_reason(message)
      elif current_state == 'awaiting_approve_amount' and message.chat.id == CONFIRMATION_CHAT_ID:
            process_approve_amount(message)
      elif current_state == 'awaiting_support_reply' and message.chat.id == SUPPORT_CHAT_ID:
            process_support_reply(message)
      else:
            logger.warning(f"Admin {admin_id} is in state {current_state}, but reply came from unexpected chat {message.chat.id} or state not handled here.")


# --- Головна функція запуску ---
def main():
    """Ініціалізація та запуск бота."""
    logger.info("Initializing database...")
    initialize_db()
    logger.info(f"Bot Owner Admin ID: {ADMIN_ID}")
    logger.info(f"Support Chat ID: {SUPPORT_CHAT_ID}")
    logger.info(f"Confirmation Chat ID: {CONFIRMATION_CHAT_ID}")
    logger.info(f"Payment Details Loaded: {list(PAYMENT_DETAILS.keys())}")
    logger.info(f"Exchange Rates To UAH: {EXCHANGE_RATES_TO_UAH}")
    logger.info(f"Exchange Rates From UAH: {EXCHANGE_RATES_FROM_UAH}")

    try:
        me = bot.get_me()
        logger.info(f"Starting bot polling for: @{me.username} (ID: {me.id})...")
    except Exception as e:
        logger.error(f"Could not get bot info. Check token or network. Error: {e}")
        return

    while True:
        try:
            logger.info("Starting long polling...")
            bot.infinity_polling(logger_level=logging.INFO, # Можна змінити на logging.DEBUG для детальніших логів
                                 timeout=30,
                                 long_polling_timeout=30)
        except telebot.apihelper.ApiTelegramException as e:
            logger.error(f"Telegram API Exception during polling: {e}")
            if "Unauthorized" in str(e):
                logger.error("BOT TOKEN IS INVALID. Stopping.")
                break
            elif "Too Many Requests" in str(e) or "Flood control" in str(e):
                sleep_time = 30
                logger.warning(f"Too Many Requests/Flood control error. Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
            elif "Conflict: terminated by other getUpdates" in str(e):
                logger.warning("Conflict detected. Another instance might be running. Waiting 60 seconds before retry.")
                time.sleep(60)
            else:
                sleep_time = 15
                logger.warning(f"Restarting polling in {sleep_time} seconds due to API exception: {e}")
                time.sleep(sleep_time)
        except requests.exceptions.ReadTimeout as e:
            logger.warning(f"Polling ReadTimeout: {e}. Retrying after 5 seconds.")
            time.sleep(5)
        except requests.exceptions.ConnectionError as e:
            sleep_time = 30
            logger.warning(f"Polling ConnectionError: {e}. Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
        except Exception as e:
            logger.error(f"Bot polling failed with unexpected error: {e}")
            logger.error(traceback.format_exc())
            sleep_time = 60
            logger.info(f"Restarting polling in {sleep_time} seconds...")
            time.sleep(sleep_time)
        else:
            logger.info("Infinity polling finished gracefully (should not happen). Restarting after 10 seconds.")
            time.sleep(2000)

if __name__ == "__main__":
    main()
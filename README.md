# 🤖 Аксиома Закупки Бот

Telegram-бот для учёта покупок с сохранением в Airtable.
Позволяет авторизованным пользователям добавлять записи: наименование, количество, примечание, срок выполнения.
Автоматически сохраняет отправителя.


## Технологии

- **Язык**: Python 3.11+
- **Фреймворк**: aiogram 3.x
- **HTTP-клиент**: httpx
- **Хранилище**: Airtable (через REST API)
- **Конфигурация**: python-dotenv
- **Логирование**: logging

## Установка и запуск (локально)

### Настройка Airtable

Перед запуском бота убедитесь, что ваша таблица в Airtable имеет следующие поля:

- **Наименование** (Single line text) - для наименования покупки.
- **Количество** (Number) - для количества.
- **Примечание** (Long text) - для примечаний.
- **Срок выполнения** (Date) - для срока выполнения (deadline).
- **Отправитель** (Single line text) - для имени пользователя Telegram.

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/alex-ivanenko/aksioma-purchases-bot.git
cd aksioma-purchases-bot
```
### 2. Создайте виртуальное окружение
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# или
.venv\Scripts\activate     # Windows
```
### 3. Установите зависимости
```bash
pip install -r requirements.txt
```
### 4. Настройте .env
Создайте файл `.env` в корне проекта на основе `.env.example` и заполните его своими данными:

- `TELEGRAM_BOT_TOKEN`: Токен вашего бота, полученный от [@BotFather](https://t.me/BotFather) в Telegram.
- `AIRTABLE_API_KEY`: Ваш персональный API-ключ от Airtable.
- `AIRTABLE_BASE_ID`: ID вашей базы в Airtable (обычно начинается с `app...`).
- `AIRTABLE_TABLE_NAME`: Название или ID таблицы, в которую будут сохраняться записи.
- `AUTHORIZED_USERS`: ID пользователей Telegram, которым разрешено использовать бота.

### 5. Запустите бота
```bash
python -m bot.main
```
Бот запустится в режиме polling (если не задан WEBHOOK_HOST).

## Webhook (опционально)
Для запуска в режиме webhook добавьте в `.env`:
- `WEBHOOK_HOST=https://ваш-домен.ngrok.io`
- `PORT=8080`

Бот автоматически переключится в режим webhook.

## Логирование
Бот ведёт логи в файл `logs/bot.log` (с ротацией: 5 МБ, 2 архива).
Также логи выводятся в консоль при запуске.

## Структура проекта
```text
aksioma-purchases-bot/
├── bot/                   # Основной код бота
│   ├── main.py            # Точка входа
│   ├── config.py          # Загрузка конфигурации
│   ├── states.py          # Состояния FSM
│   ├── handlers.py        # Обработчики сообщений
│   └── airtable_client.py # Клиент для работы с Airtable
├── .env.example           # Шаблон конфигурации
├── .gitignore             # Файлы, исключённые из Git
├── requirements.txt       # Зависимости
└── README.md              # Документация
```

## License
This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.




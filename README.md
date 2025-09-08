# 🤖 Aksioma Purchases Bot

Telegram-бот для учёта покупок с сохранением в Airtable.
Позволяет авторизованным пользователям добавлять записи: наименование, количество, примечание.
Автоматически сохраняет отправителя и дату создания.


## Технологии

- **Язык**: Python 3.11+
- **Фреймворк**: aiogram 3.x (асинхронный)
- **HTTP-клиент**: httpx (асинхронный)
- **Хранилище**: Airtable (через REST API)
- **Конфигурация**: python-dotenv
- **Логирование**: logging

## Установка и запуск (локально)

### 1. Клонируй репозиторий

```bash
git clone https://github.com/alex-ivanenko/aksioma_purchases_bot.git
cd aksioma_purchases_bot
```
### 2. Создай виртуальное окружение
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# или
.venv\Scripts\activate     # Windows
```
### 3. Установи зависимости
```bash
pip install -r requirements.txt
```
### 4. Настрой .env
Создай файл .env на основе .env.example — заполни своими данными.
### 5. Запусти бота
```bash
python -m bot.main
```
Бот запустится в режиме polling (если не задан WEBHOOK_HOST).

## License
This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.



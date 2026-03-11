# 🎓 Stepenin.ru Bot → Telegram

**Бесплатная автоматизация тестов stepenin.ru с отправкой ответов в Telegram**

---

## 🚀 Быстрый старт

### 1. Создайте репозиторий на GitHub

1. GitHub → **New repository**
2. Название: `stepenin-bot`
3. **Private** (рекомендуется)
4. **Create**

### 2. Загрузите файлы

Нужны 4 файла:
- `bot.py`
- `config.json`
- `requirements.txt`
- `.github/workflows/run_bot.yml`

### 3. Настройте Telegram бота

#### Создайте бота:
1. Откройте [@BotFather](https://t.me/BotFather)
2. `/newbot`
3. Введите имя (например: `Stepenin Helper`)
4. Введите username (например: `stepenin_test_bot`)
5. **Скопируйте токен** (выглядит как `123456:ABC-DEF...`)

#### Узнайте chat_id:
1. Откройте [@userinfobot](https://t.me/userinfobot)
2. **Start**
3. **Скопируйте chat_id** (число, например: `123456789`)

### 4. Добавьте Secrets в GitHub

1. Репозиторий → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**:

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | Токен из BotFather |
| `TELEGRAM_CHAT_ID` | Ваш chat_id |
| `STEPENIN_PHONE` | Телефон VK (например, `9100979615`) |

### 5. Включите Actions

1. Репозиторий → **Actions**
2. **I understand my workflows, go ahead and enable them**

---

## 📱 Использование

### Запуск через Issues (с iPhone):

1. Откройте приложение **GitHub** на iPhone
2. Ваш репозиторий → **Issues** → **New issue**
3. Заголовок: `run 2042` (или `run https://stepenin.ru/...`)
4. **Submit**
5. Через 1-5 минут получите ответы в Telegram!

### Запуск через GitHub UI:

1. **Actions** → **Run Stepenin Bot** → **Run workflow**
2. Введите URL (опционально)
3. **Run workflow**

---

## 📬 Как выглядят ответы

В Telegram придёт сообщение:

```
📚 Задание №10 ЕГЭ. Номенклатура

Вопрос 26: 1423
Вопрос 27: 3142
Вопрос 28: 2413
Вопрос 29: 4231
...

✅ Готово!
Всего ответов: 50
Диапазон: 26 - 75
```

---

## ⚙️ Настройки

### config.json
```json
{
  "telegram_bot_token": "",  // Можно не заполнять, если используете Secrets
  "telegram_chat_id": "",    // Можно не заполнять, если используете Secrets
  "phone": "9100979615",
  "start_url": "https://stepenin.ru/tasks/common/test2042/26",
  "max_questions": null,
  "default_answer": "0000"
}
```

---

## 🔧 Решение проблем

### Бот не отправляет сообщения
1. Проверьте что токен и chat_id правильные
2. Напишите боту `/start` в Telegram
3. Проверьте Secrets в GitHub

### Ошибка авторизации VK
1. Войдите на stepenin.ru вручную через браузер
2. После входа запустите бота снова

### Workflow не запускается
1. Проверьте что Actions включены
2. Посмотрите логи во вкладке **Actions**

---

## 💰 Лимиты GitHub Actions

- **2000 минут/месяц** (бесплатно)
- Один запуск ≈ 2-5 минут
- **~400-1000 запусков в месяц**

---

## 📁 Файлы

```
stepenin-bot/
├── bot.py                       # Скрипт бота
├── config.json                  # Настройки
├── requirements.txt             # Зависимости
└── .github/workflows/
    └── run_bot.yml             # GitHub Actions
```

---

**Готово!** 🎉

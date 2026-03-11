# -*- coding: utf-8 -*-
"""
Stepenin.ru Bot - GitHub Actions + Telegram
Полная автоматизация тестов stepenin.ru с отправкой в Telegram
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import os
import json
import sys
import requests
from datetime import datetime
from pathlib import Path

# Пути
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

# Глобальные переменные для ответов
answers_buffer = {}
topic_name = "Неизвестно"


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(Colors.HEADER + Colors.BOLD + "\n=== " + text + " ===" + Colors.ENDC)


def print_success(text):
    print(Colors.OKGREEN + "✓ " + text + Colors.ENDC)


def print_error(text):
    print(Colors.FAIL + "✗ " + text + Colors.ENDC)


def print_info(text):
    print(Colors.OKCYAN + "ℹ " + text + Colors.ENDC)


def send_to_telegram(message):
    """Отправить сообщение в Telegram"""
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # Приоритет: environment variables > config file
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or config.get("telegram_bot_token")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or config.get("telegram_chat_id")
    
    if not bot_token or not chat_id:
        print_error("Telegram не настроен. Укажите TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print_success("Отправлено в Telegram")
            return True
        else:
            print_error(f"Telegram API error: {response.text}")
            return False
    except Exception as e:
        print_error(f"Ошибка отправки в Telegram: {e}")
        return False


def send_answers_to_telegram(topic, answers):
    """Отправить все ответы в Telegram"""
    # Форматируем сообщение
    message = f"📚 *{topic}*\n\n"
    
    # Сортируем по номеру вопроса
    sorted_answers = sorted(answers.items(), key=lambda x: x[0])
    
    # Разбиваем на сообщения по 50 вопросов (лимит Telegram ~4000 символов)
    batch_size = 50
    for i in range(0, len(sorted_answers), batch_size):
        batch = sorted_answers[i:i + batch_size]
        batch_message = message
        
        for q_num, answer in batch:
            batch_message += f"Вопрос {q_num}: `{answer}`\n"
        
        if i + batch_size < len(sorted_answers):
            batch_message += f"\n_...продолжение следует..._"
        
        send_to_telegram(batch_message)
        time.sleep(0.5)  # Пауза чтобы не превысить лимиты
    
    # Финальное сообщение
    if len(sorted_answers) > 0:
        final_msg = f"✅ *Готово!*\n\nВсего ответов: `{len(answers)}`\nДиапазон: `{min(answers.keys())}` - `{max(answers.keys())}`"
        send_to_telegram(final_msg)


class StepениnBot:
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.answers = {}  # Буфер ответов
        self.topic_name = "Неизвестно"
        
    def setup_driver(self):
        """Настроить Chrome в headless режиме"""
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Для GitHub Actions
        if os.environ.get("GITHUB_ACTIONS"):
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-setuid-sandbox")
        
        self.driver = webdriver.Chrome(options=options)
        print_info("Chrome запущен в headless режиме")
    
    def get_question_number(self, url):
        """Извлечь номер вопроса из URL"""
        match = re.search(r'/(\d+)(?:\?|$|/)', url)
        return int(match.group(1)) if match else 0
    
    def get_topic_name(self):
        """Извлечь название темы со страницы"""
        try:
            topic_div = self.driver.find_element(
                By.XPATH, 
                "//div[contains(@class, 'text-xl') and contains(@class, 'font-medium') and contains(@class, 'mr-auto')]"
            )
            topic_text = topic_div.text.strip()
            # Удаляем недопустимые символы
            topic_text = re.sub(r'[<>:"/\\|?*]', '', topic_text)
            topic_text = re.sub(r'\s+', ' ', topic_text)
            return topic_text[:100]  # Ограничиваем длину
        except Exception as e:
            print_info(f"Не удалось извлечь тему: {e}")
            return "Задание"
    
    def save_answer(self, question_num, answer):
        """Сохранить ответ в буфер"""
        self.answers[question_num] = answer
        print_success(f"Ответ получен: Вопрос {question_num} = {answer}")
    
    def login_via_vk(self):
        """Авторизация через VK"""
        print_header("Авторизация через VK")
        
        # Переходим на страницу авторизации
        vk_url = "https://stepenin.ru/vk"
        self.driver.get(vk_url)
        time.sleep(3)
        
        # Проверяем, не авторизованы ли уже
        current_url = self.driver.current_url
        if "vk" not in current_url.lower():
            print_success("Уже авторизован")
            return True
        
        # Ввод телефона
        phone = self.config.get("phone", "9100979615")
        print_info(f"Ввод телефона: {phone}")
        
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Ищем поле логина
            login_field = wait.until(EC.presence_of_element_located((By.NAME, "login")))
            self.driver.execute_script("arguments[0].value = '';", login_field)
            login_field.send_keys(phone)
            
            # Кнопка "Продолжить"
            continue_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(), 'Продолжить')]")
            ))
            continue_btn.click()
            print_info("Телефон введён, ожидаем код...")
            
            time.sleep(2)
            
            # Проверяем, есть ли поле для OTP
            otp_fields = self.driver.find_elements(By.NAME, "otp-cell")
            if otp_fields:
                print_info("Требуется код подтверждения. Проверьте VK.")
                # В GitHub Actions нельзя ввести код вручную
                # Используем сохранённую сессию
                print_error("Автоматическая авторизация невозможна без кода.")
                print_info("Используйте сохранённые cookies или войдите вручную.")
                return False
            
            print_success("Авторизация выполнена")
            return True
            
        except Exception as e:
            print_error(f"Ошибка авторизации: {e}")
            return False
    
    def extract_correct_answer(self):
        """Извлечь правильный ответ из страницы"""
        try:
            correct_div = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'text-slate-400') and contains(text(), 'Правильная последовательность')]"
            )
            correct_text = correct_div.text
            match = re.search(r':\s*(\d+)', correct_text)
            if match:
                return match.group(1)
        except:
            pass
        return None
    
    def submit_answer(self, answer):
        """Отправить ответ"""
        try:
            wait = WebDriverWait(self.driver, 5)
            
            # Поле ответа
            answer_field = wait.until(EC.presence_of_element_located((By.NAME, "answer")))
            self.driver.execute_script(f"arguments[0].value = '{answer}';", answer_field)
            
            # Кнопка "Ответить"
            submit_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Ответить')]")
            ))
            submit_btn.click()
            print_info(f"Ответ {answer} отправлен")
            
            time.sleep(1)
            return True
        except Exception as e:
            print_error(f"Ошибка отправки: {e}")
            return False
    
    def run(self, start_url=None, max_questions=None):
        """Основной цикл работы"""
        print_header("Stepenin.ru Bot - Telegram")
        
        # Настройки из параметров или конфига
        if not start_url:
            start_url = self.config.get("start_url", "https://stepenin.ru/tasks/common/test2042/26")
        if max_questions is None:
            max_questions = self.config.get("max_questions", None)
        
        # Запускаем браузер
        self.setup_driver()
        
        try:
            # Переходим на стартовую страницу
            print_info(f"Открываем: {start_url}")
            self.driver.get(start_url)
            time.sleep(3)
            
            # Проверяем авторизацию
            if "login" in self.driver.current_url.lower() or "vk" in self.driver.current_url.lower():
                print_info("Требуется авторизация")
                if not self.login_via_vk():
                    print_error("Авторизация не удалась. Прерывание.")
                    return
            
            # Извлекаем тему
            self.topic_name = self.get_topic_name()
            
            print_success(f"Тема: {self.topic_name}")
            
            # Основной цикл
            current_url = start_url
            question_num = self.get_question_number(current_url)
            start_question = question_num  # Запоминаем начальный вопрос
            
            while True:
                print_header(f"Вопрос {question_num}")
                
                # Переходим на страницу вопроса
                self.driver.get(current_url)
                time.sleep(2)
                
                # Проверяем правильный ответ
                correct_answer = self.extract_correct_answer()
                
                if correct_answer:
                    print_success(f"Правильный ответ: {correct_answer}")
                    self.save_answer(question_num, correct_answer)
                else:
                    # Нужно отправить ответ
                    answer_value = self.config.get("default_answer", "0000")
                    print_info(f"Отправляю ответ: {answer_value}")
                    
                    if self.submit_answer(answer_value):
                        time.sleep(1)
                        # Получаем правильный ответ после отправки
                        correct_answer = self.extract_correct_answer()
                        if correct_answer:
                            print_success(f"Правильный ответ: {correct_answer}")
                            self.save_answer(question_num, correct_answer)
                
                # Проверка достижения максимума
                if max_questions and question_num >= max_questions:
                    print_success(f"Достигнут максимум: №{max_questions}")
                    break
                
                # Переход к следующему
                next_url = current_url.rsplit('/', 1)[0] + '/' + str(question_num + 1)
                
                # Проверяем существует ли следующий
                self.driver.get(next_url)
                time.sleep(2)
                
                if "404" in self.driver.title or self.get_question_number(next_url) != question_num + 1:
                    print_info("Следующий вопрос не найден")
                    break
                
                current_url = next_url
                question_num += 1
                
                # Лимит на количество вопросов за сессию
                if question_num - start_question >= 50:
                    print_info("Достигнут лимит сессии (50 вопросов)")
                    break
            
            # Отправляем все ответы в Telegram
            print_header("Отправка в Telegram")
            send_answers_to_telegram(self.topic_name, self.answers)
            
            print_header("Завершено!")
            print_success(f"Всего ответов: {len(self.answers)}")
            print_info(f"Диапазон вопросов: {start_question} - {question_num}")
            
        except Exception as e:
            print_error(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()
            
            # Отправляем ошибку в Telegram
            send_to_telegram(f"❌ *Ошибка бота*\n\n```\n{str(e)[:1000]}\n```")
        finally:
            if self.driver:
                self.driver.quit()
                print_info("Браузер закрыт")


def main():
    """Точка входа"""
    # Загружаем конфиг
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # Параметры из environment (для GitHub Actions)
    if os.environ.get("START_URL"):
        config["start_url"] = os.environ["START_URL"]
    if os.environ.get("MAX_QUESTIONS"):
        config["max_questions"] = int(os.environ["MAX_QUESTIONS"])
    if os.environ.get("PHONE"):
        config["phone"] = os.environ["PHONE"]
    
    # Запускаем бота
    bot = StepениnBot(config)
    bot.run()


if __name__ == "__main__":
    main()

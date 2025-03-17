# Календарь рабочих дней по графику 2/2

Веб-приложение для отображения календаря рабочих и выходных дней по графику 2/2. Приложение позволяет просматривать календарь на любой месяц и год, начиная с заданной даты начала цикла (17.03.2025).

## Особенности

- Интерактивный календарь с возможностью выбора месяца и года
- Визуальное отображение рабочих и выходных дней
- Адаптивный дизайн с использованием Bootstrap
- Готовая конфигурация для развертывания в продакшн с использованием Docker и Nginx

## Технологии

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5, Font Awesome
- **Инфраструктура**: Docker, Nginx, Gunicorn

## Требования

- Docker
- Docker Compose

## Установка и запуск

### Разработка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/work-schedule-calendar.git
   cd work-schedule-calendar
   ```

2. Запустите приложение в режиме разработки:
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

3. Откройте браузер и перейдите по адресу: http://localhost:5000

### Продакшн

1. Создайте необходимые директории:
   ```bash
   mkdir -p nginx/conf.d nginx/logs static
   ```

2. Запустите приложение в продакшн-режиме:
   ```bash
   docker-compose up -d
   ```

3. Откройте браузер и перейдите по адресу: http://localhost или http://ваш_ip_адрес

## Структура проекта 

work-schedule-calendar/
├── app.py                  # Основной файл приложения Flask
├── requirements.txt        # Зависимости Python
├── Dockerfile              # Инструкции для сборки Docker-образа
├── docker-compose.yml      # Конфигурация Docker Compose для продакшн
├── docker-compose.dev.yml  # Конфигурация Docker Compose для разработки
├── .gitignore              # Файлы, игнорируемые Git
├── .dockerignore           # Файлы, игнорируемые Docker
├── .env.example            # Пример файла с переменными окружения
├── templates/              # HTML-шаблоны
│   └── calendar.html       # Шаблон календаря
├── static/                 # Статические файлы (если есть)
└── nginx/                  # Конфигурация Nginx
    ├── nginx.conf          # Основная конфигурация Nginx
    └── conf.d/             # Дополнительные конфигурации
        └── app.conf        # Конфигурация для приложения 
# Програма для збору даних про товари

**Контактна інформація виконавця:**

- Ім'я: Ігор Клим
- Email: igorklym03@gmail.com
- Телефон: +380950107757
- telegram: @klym303

## Опис проекту

Цей проект є веб-скрейпером, який призначений для збору інформації про товари з онлайн-магазину IGEFA. Зібрані дані зберігаються у базі даних PostgreSQL та можуть бути експортовані у CSV-файл.

## Налаштування середовища

1. Клонуйте репозиторій:

   ```bash
   git clone https://your-repository-url.git
   cd your-repository-name
2. Налаштуйте базу даних PostgreSQL.

    Створіть файл .env у каталозі проекту та додайте налаштування вашої бази даних:
    
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
DB_HOST=localhost
DB_PORT=5432
3. Встановіть залежності:

    ```bash
    pip install -r requirements.txt
4. Щоб запустити скрейпер, виконайте наступну команду:

    ```bash
    python main.py

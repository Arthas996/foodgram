# Foodgram
**Foodgram** — это веб-приложение для публикации рецептов, где пользователи
могут делиться своими кулинарными шедеврами, добавлять рецепты в избранное,
подписываться на авторов и формировать список покупок. Проект выполнен в рамках
учебного курса Яндекс Практикума.

[![CI](https://github.com/Arthas996/foodgram/actions/workflows/main.yml/badge.svg)]
(https://github.com/Arthas996/foodgram/actions)

---

## Деплой

Проект развёрнут и доступен по адресу:  
(https://foodgram96.work.gd)

---

## Стек технологий

**Бэкенд:**
- Python 3.12
- Django 4.2.16
- Django REST Framework 3.15.2
- Djoser (аутентификация через токены)
- PostgreSQL
- Gunicorn
- Docker и Docker Compose

**Фронтенд:**
- React
- Node.js
- Nginx

**CI/CD:**
- GitHub Actions
- Docker Hub

---

### Как развернуть проект локально

1. Клонируйте репозиторий
```bash
git clone https://github.com/Arthas996/foodgram.git
cd foodgram
2. Настройте бэкенд
bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
3. Создайте файл .env в папке backend/ (подставьте свои значения):
env
SECRET_KEY=ваш-секретный-ключ
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=ваш-пароль
DB_HOST=localhost
DB_PORT=5432
Если вы используете SQLite (для разработки), измените настройки базы данных

4. Выполните миграции и загрузите ингредиенты
bash
python manage.py migrate
python manage.py load_ingredients ../data/ingredients.json
python manage.py createsuperuser
5. Запустите сервер разработки
bash
python manage.py runserver
Бэкенд будет доступен по адресу http://127.0.0.1:8000.

6. Установите и запустите фронтенд
bash
cd ../frontend
npm install
npm start
Фронтенд запустится на http://localhost:3000.

Запуск через Docker
Убедитесь, что у вас установлены Docker и Docker Compose.
В корне проекта выполните:

bash
docker compose -f docker-compose.production.yml up -d
Приложение будет доступно по адресу http://localhost:9001 (порт можно изменить)

Документация API
Спецификация API доступна по адресу:
http://127.0.0.1:8000/api/docs/
https://foodgram96.work.gd/api/docs/


Коллекция Postman для тестирования лежит в папке postman_collection/.

Автор
Беликов Анатолий — студент Яндекс Практикума
GitHub: Arthas996

Лицензия
Проект выполнен в учебных целях.

# Проект API

В проекте представлен API, который собирает отзывы пользователей на произведения.
Реализованный API позволяет создать базу с информацией о произведениях, разбив их на жанры и категории. 
Также возможно регистрировать пользователей через API с аутентификацией.
Пользователи имеют возможность оставлять отзывы на произведение (одно произведение - один отзыв).
Пользователи также могут взаимодействовать друг с другом, оставляя комментарии к отзывам.

## Содержание
- [Установка](#установка)
- [Примеры запросов](#примеры-запросов)
- [API Документация](#api-документация)
---

## Установка:

- На Windows вы можете использовать `python`.
- На Linux можно использовать `python3`.


1. Клонируйте репозиторий и перейдите в него в терминале:
```
git clone git@github.com:zerin2/api_project.git
cd api_yamdb
```
2. Cоздайте и активируйте виртуальное окружение:
```
python -m venv venv
```
```
source venv/scripts/activate
```
3. Установите зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
4. Выполните миграции:
```
python manage.py migrate
```
5. Для запуска скрипта импортирования базы данных, используйте команду:
```
python manage.py import_csv
```
6. Запустите проект с помощью команды в терминале:
```
python manage.py runserver
```

---

## Примеры запросов:

### Регистрация и авторизация нового пользователя
На эндпоинт api/v1/auth/signup/ отправляется запрос вида:
```
{
"email": "user@example.com",
"username": "^w\\Z"
}
```
На email пользователю приходит код подтверждения.
Для получения JWT-токена, пользователь отправляет на эндпоинт api/v1/auth/token/ запрос с этим кодом вида:
```
{
"username": "^w\\Z",
"confirmation_code": "string"
}
```
В ответ он получает токен для пользования ресурсами проекта:
```
{
"token": "string"
}
```

### Получение информации без токена

Без токена возможно получить информацию о списках всех категорий, жанров, произведений, отзывов и комментариев, а также о каждом произведении, отзыве и комментарии отдельно.

### Написание отзыва на произведение

На эндпоинт api/v1/titles/{title_id}/reviews/ авторизованный пользователь отправляет POST-запрос вида:
```
{
"text": "string",
"score": 1
}
```
В запросе text - текст отзыва, а score - пользовательская оценка произведения от 1 до 10.
Пользователю можно оставить только один отзыв к каждому произведению.
В ответ пользователь получит информацию о созданном отзыве:
```
{
"id": 0,
"text": "string",
"author": "string",
"score": 1,
"pub_date": "2019-08-24T14:15:22Z"
}
```
Автору отзыва доступно редактирование отзыва по эндпоинту api/v1/titles/{title_id}/reviews/{review_id}/ с запросом PATCH, а также удаление своего отзыва с запросом DELETE на тот же эндпоинт.

### Написание комментария на отзыв

На эндпоинт api/v1/titles/{title_id}/reviews/{review_id}/comments/ аутентифицированный пользователь может отправить POST-запрос вида:
```
{
"text": "string"
}
```
Где text - комментарий пользователя на отзыв к произведению.
В ответ пользователь получит информацию о созданном комментарии:
```
{
"id": 0,
"text": "string",
"author": "string",
"pub_date": "2019-08-24T14:15:22Z"
}
```
Автору комментария по эндпоинту api/v1/titles/{title_id}/reviews/{review_id}/comments/{comment_id}/ доступно редактирование отзыва с PATCH-запросом и удаление с DELETE-запросом.

### Получение данных своей учетной записи

На эндпоинт api/v1/users/me/ авторизованный пользователь может отправить PATCH-запрос вида:
```
{
"username": "^w\\Z",
"email": "user@example.com",
"first_name": "string",
"last_name": "string",
"bio": "string",
"role": "user"
}
```
Поля email и username должны быть уникальными.

---

## API Документация:

Когда вы запустите проект, по адресу  [http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/) будет доступна документация для API. 
Документация представлена в формате Redoc.

---

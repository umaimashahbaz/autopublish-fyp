POST http://127.0.0.1:8000/api/token/
Content-Type: application/json
Body:
{
  "username": "your_username",
  "password": "your_password"
}

Response:
{
  "refresh": "string",
  "access": "string"
}


POST http://127.0.0.1:8000/api/token/refresh/
Body:
{
  "refresh": "your_refresh_token"
}

Response:
{
  "access": "new_access_token"
}

API на FastAPI  
- Агент на LangGraph с фейковой маршрутизацией по LLM  
- MCP-сервер (FastMCP) запускается как подпроцесс через stdio


### Запуск через Docker Compose

docker compose up --build


### API

Метод: POST
Путь: /api/v1/agent/query

# Показать все товары в категории Электроника
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Покажи все продукты в категории Электроника"}'
Bash# Средняя цена по всем товарам
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Какая средняя цена продуктов?"}'
Bash# Добавить новый товар
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Добавь новый продукт: Мышка, цена 1500, категория Электроника"}'
Bash# Посчитать скидку на конкретный товар
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Посчитай скидку 15% на товар с ID 1"}'

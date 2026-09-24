FROM node:20-alpine

WORKDIR /app

# Копируем файлы зависимостей
COPY package.json package-lock.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем остальной код
COPY . .

# Открываем порт, который использует Vite по умолчанию
EXPOSE 5173

# Запускаем dev-сервер (как вы и делали в терминале)
CMD ["npm", "run", "dev", "--", "--host"]
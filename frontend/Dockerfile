FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

# Запускаємо Vite напряму (а не через `npm run dev`), щоб він був PID 1 і
# отримував SIGTERM від Docker — інакше сигнал губиться в обгортках npm/node і
# контейнер завершується з ненульовим кодом. Exec-форма CMD без шела.
CMD ["node", "node_modules/vite/bin/vite.js", "--host"]

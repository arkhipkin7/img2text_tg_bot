# Руководство по развертыванию

## Обзор

Данное руководство описывает различные способы развертывания Telegram бота для генерации контента товаров.

## Предварительные требования

- Docker и Docker Compose
- Telegram Bot Token (получить у @BotFather)
- Доступ к серверу или облачной платформе

## 1. Развертывание с Docker Compose (рекомендуется)

### Локальное развертывание

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd img2text_tg_bot
```

2. **Настройте переменные окружения:**
```bash
# Создайте файл .env с вашими настройками
# Отредактируйте .env файл
```

3. **Запустите сервисы:**
```bash
docker-compose up -d
```

4. **Проверьте статус:**
```bash
docker-compose ps
docker-compose logs -f
```

### Продакшн развертывание

1. **Настройте продакшн переменные:**
```bash
# .env.prod
BOT_TOKEN=your_production_bot_token
API_BASE_URL=https://your-domain.com
LOG_LEVEL=WARNING
API_DEBUG=False
```

2. **Запустите с продакшн конфигурацией:**
```bash
docker-compose -f docker-compose.yml --env-file .env.prod up -d
```

3. **Настройте reverse proxy (nginx):**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 2. Развертывание на VPS/Сервере

### Ubuntu/Debian

1. **Установите Docker:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

2. **Установите Docker Compose:**
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

3. **Клонируйте и запустите:**
```bash
git clone <repository-url>
cd img2text_tg_bot
# Создайте файл .env с вашими настройками
# Отредактируйте .env
docker-compose up -d
```

### CentOS/RHEL

1. **Установите Docker:**
```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
```

2. **Остальные шаги аналогичны Ubuntu**

## 3. Облачные платформы

### Heroku

1. **Создайте Procfile:**
```
web: cd api && uvicorn main:app --host 0.0.0.0 --port $PORT
worker: cd bot && python main.py
```

2. **Создайте requirements.txt в корне:**
```
-r api/requirements.txt
-r bot/requirements.txt
```

3. **Разверните:**
```bash
heroku create your-app-name
heroku config:set BOT_TOKEN=your_token
heroku config:set API_BASE_URL=https://your-app-name.herokuapp.com
git push heroku main
```

### Railway

1. **Подключите GitHub репозиторий**
2. **Настройте переменные окружения в Railway Dashboard**
3. **Railway автоматически развернет приложение**

### DigitalOcean App Platform

1. **Создайте app в DigitalOcean Dashboard**
2. **Подключите GitHub репозиторий**
3. **Настройте переменные окружения**
4. **Укажите команды запуска:**
   - API: `cd api && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Bot: `cd bot && python main.py`

### AWS ECS

1. **Создайте ECR репозиторий:**
```bash
aws ecr create-repository --repository-name img2text-bot
aws ecr create-repository --repository-name img2text-api
```

2. **Соберите и загрузите образы:**
```bash
docker build -t img2text-api -f api/Dockerfile .
docker build -t img2text-bot -f bot/Dockerfile .

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com

docker tag img2text-api:latest your-account.dkr.ecr.us-east-1.amazonaws.com/img2text-api:latest
docker tag img2text-bot:latest your-account.dkr.ecr.us-east-1.amazonaws.com/img2text-bot:latest

docker push your-account.dkr.ecr.us-east-1.amazonaws.com/img2text-api:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/img2text-bot:latest
```

3. **Создайте ECS кластер и сервисы**

## 4. Kubernetes

### Namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: img2text
```

### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: img2text-config
  namespace: img2text
data:
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  API_DEBUG: "false"
  LOG_LEVEL: "INFO"
  MAX_FILE_SIZE: "20971520"
  MAX_TEXT_LENGTH: "5000"
```

### Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: img2text-secrets
  namespace: img2text
type: Opaque
data:
  BOT_TOKEN: <base64-encoded-token>
  ADMIN_IDS: <base64-encoded-admin-ids>
```

### API Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: img2text-api
  namespace: img2text
spec:
  replicas: 2
  selector:
    matchLabels:
      app: img2text-api
  template:
    metadata:
      labels:
        app: img2text-api
    spec:
      containers:
      - name: api
        image: your-registry/img2text-api:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: img2text-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Bot Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: img2text-bot
  namespace: img2text
spec:
  replicas: 1
  selector:
    matchLabels:
      app: img2text-bot
  template:
    metadata:
      labels:
        app: img2text-bot
    spec:
      containers:
      - name: bot
        image: your-registry/img2text-bot:latest
        envFrom:
        - configMapRef:
            name: img2text-config
        - secretRef:
            name: img2text-secrets
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: img2text-api-service
  namespace: img2text
spec:
  selector:
    app: img2text-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: img2text-ingress
  namespace: img2text
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: api.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: img2text-api-service
            port:
              number: 80
```

## 5. Мониторинг и логирование

### Prometheus + Grafana

1. **Добавьте метрики в API:**
```python
from prometheus_client import Counter, Histogram, generate_latest

requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
```

2. **Настройте Grafana дашборд**

### ELK Stack

1. **Настройте Filebeat для сбора логов**
2. **Создайте Elasticsearch индексы**
3. **Настройте Kibana дашборды**

### Локальное логирование

```bash
# Просмотр логов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f api
docker-compose logs -f bot

# Логи с временными метками
docker-compose logs -f --timestamps
```

## 6. Безопасность

### SSL/TLS

1. **Получите SSL сертификат (Let's Encrypt):**
```bash
sudo certbot --nginx -d your-domain.com
```

2. **Настройте автоматическое обновление:**
```bash
sudo crontab -e
# Добавьте строку:
0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# iptables (CentOS)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### Обновления

```bash
# Автоматические обновления Docker образов
docker-compose pull
docker-compose up -d

# Обновление системы
sudo apt update && sudo apt upgrade -y
```

## 7. Резервное копирование

### База данных (если используется)

```bash
# Создание бэкапа
docker exec -t your-db-container pg_dumpall -c -U your-user > dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql

# Восстановление
cat your_dump.sql | docker exec -i your-db-container psql -U your-user -d your-database
```

### Конфигурация

```bash
# Бэкап конфигурации
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml
```

## 8. Troubleshooting

### Частые проблемы

1. **Бот не отвечает:**
   - Проверьте токен бота
   - Убедитесь, что API доступен
   - Проверьте логи: `docker-compose logs bot`

2. **API недоступен:**
   - Проверьте порты: `netstat -tulpn | grep 8000`
   - Проверьте логи: `docker-compose logs api`
   - Убедитесь в правильности конфигурации

3. **Проблемы с файлами:**
   - Проверьте права доступа к папке temp
   - Убедитесь в достаточном месте на диске
   - Проверьте формат файлов

### Полезные команды

```bash
# Перезапуск сервисов
docker-compose restart

# Пересборка образов
docker-compose build --no-cache

# Очистка неиспользуемых ресурсов
docker system prune -a

# Проверка использования ресурсов
docker stats

# Просмотр переменных окружения
docker-compose config
``` 
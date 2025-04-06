# Deployment Guide for Scraper Service

This guide explains how to deploy the Scraper Service permanently using different methods.

## Method 1: Docker Deployment

### Prerequisites
- Docker and Docker Compose installed on your server
- A server with at least 2GB RAM and 1 CPU core

### Steps

1. Clone the repository to your server:
```bash
git clone https://github.com/yourusername/scraper-service.git
cd scraper-service
```

2. Build and start the Docker container:
```bash
docker-compose up -d
```

3. The service will be available at http://your-server-ip:8000

4. To view logs:
```bash
docker-compose logs -f
```

5. To stop the service:
```bash
docker-compose down
```

## Method 2: Deployment to a Cloud Provider

### Option A: Deploying to Heroku

1. Install the Heroku CLI and login:
```bash
npm install -g heroku
heroku login
```

2. Create a new Heroku app:
```bash
heroku create scraper-service
```

3. Add a Procfile to the project root:
```
web: uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-8000}
```

4. Deploy to Heroku:
```bash
git push heroku main
```

5. The service will be available at https://scraper-service.herokuapp.com

### Option B: Deploying to AWS Elastic Beanstalk

1. Install the AWS CLI and EB CLI:
```bash
pip install awscli awsebcli
```

2. Configure AWS credentials:
```bash
aws configure
```

3. Initialize EB application:
```bash
eb init -p docker scraper-service
```

4. Create an environment and deploy:
```bash
eb create scraper-service-env
```

5. The service will be available at the URL provided by Elastic Beanstalk

## Method 3: Deployment to a VPS with Nginx and Systemd

1. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

3. Create a systemd service file at `/etc/systemd/system/scraper-service.service`:
```
[Unit]
Description=Scraper Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/path/to/scraper-service
ExecStart=/path/to/scraper-service/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
StandardOutput=file:/path/to/scraper-service/logs/service.log
StandardError=file:/path/to/scraper-service/logs/service.err

[Install]
WantedBy=multi-user.target
```

4. Set up Nginx as a reverse proxy by creating a file at `/etc/nginx/sites-available/scraper-service`:
```
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

5. Enable the Nginx site:
```bash
sudo ln -s /etc/nginx/sites-available/scraper-service /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

6. Start and enable the systemd service:
```bash
sudo systemctl start scraper-service
sudo systemctl enable scraper-service
```

7. The service will be available at http://your-domain.com

## SSL Configuration

For production deployments, it's recommended to set up SSL:

1. Install Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
```

2. Obtain and configure SSL certificate:
```bash
sudo certbot --nginx -d your-domain.com
```

3. The service will now be available securely at https://your-domain.com

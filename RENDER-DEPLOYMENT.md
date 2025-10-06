# 🚀 Deploy NASA Skynet Backend to Render (Docker)

## ✅ Docker Setup Complete
Your backend is now configured with an optimized Docker setup for Render deployment.

## 📋 Step-by-Step Render Deployment with Docker

### 1. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Connect your GitHub repository: `eshu3104/nasa-hackathon-2025`

### 2. Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your repository: `eshu3104/nasa-hackathon-2025`
3. Select branch: `name`

### 3. Configure Service Settings (Docker)
```
Name: skynet-nasa-backend
Environment: Docker
Region: Ohio (US East) - recommended for speed
Branch: name
Root Directory: (leave empty)
Dockerfile Path: ./Dockerfile
Docker Build Context: .
```

### 4. Set Environment Variables
In the Render dashboard, add these environment variables:
```
OPENAI_API_KEY=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
PORT=10000
```

### 5. Advanced Settings
```
Instance Type: Starter ($7/month) - recommended for Docker
Auto-Deploy: Yes (deploys automatically on git push)
Health Check Path: /health
```

## � Docker Configuration

### Files Created:
- **`Dockerfile`** - Optimized Python 3.11 container
- **`.dockerignore`** - Excludes unnecessary files from build
- **`docker-compose.yml`** - For local testing
- **`render.yaml`** - Infrastructure as code (optional)
- **Updated `build.sh`** - Enhanced build script with checks

### Docker Features:
- ✅ Multi-stage optimized build
- ✅ Non-root user for security
- ✅ Health checks built-in
- ✅ Production gunicorn configuration
- ✅ Efficient layer caching

## 🧪 Local Testing (Optional)

### Test with Docker Compose:
```bash
# Set your OpenAI API key
$env:OPENAI_API_KEY="your-api-key-here"

# Build and run locally
docker-compose up --build

# Test the endpoints
Invoke-WebRequest -Uri "http://localhost:5000/health"
```

### Test with Docker directly:
```bash
# Build the image
docker build -t skynet-backend .

# Run the container
docker run -p 5000:5000 -e OPENAI_API_KEY="your-key" skynet-backend
```

## � Deployment Steps

### 1. Commit and Push Docker Files
```bash
git add .
git commit -m "Add Docker configuration for Render deployment"
git push
```

### 2. Deploy on Render
1. **Create Web Service** using Docker environment
2. **Set environment variables** (OPENAI_API_KEY, PORT)
3. **Deploy** - Render will build the Docker image
4. **Get your URL** like: `https://skynet-nasa-backend.onrender.com`

### 3. Update Frontend
Once deployed, update your frontend files:
```javascript
const API_BASE = 'https://skynet-nasa-backend.onrender.com/api';
```

## 🔧 Docker Benefits

### Why Docker for Render?
- **Consistent Environment** - Same runtime locally and in production
- **Better Control** - Fine-tune Python version, system dependencies
- **Faster Builds** - Layer caching speeds up deployments
- **Security** - Non-root user, minimal attack surface
- **Scalability** - Easier to scale and manage

### Production Optimizations:
- Gunicorn with optimized worker settings
- Health checks for reliability
- Proper logging configuration
- Memory and CPU optimizations

## 🚨 Important Notes

### Resource Requirements:
- **Memory**: Docker containers need more RAM (recommend Starter plan)
- **Build Time**: Docker builds take 3-5 minutes
- **Storage**: Model files must fit in container

### Troubleshooting:
- **Build Fails**: Check Dockerfile syntax and dependencies
- **Out of Memory**: Upgrade to higher tier or optimize model size
- **Slow Cold Starts**: Docker containers have ~30s cold start time

## 📊 Expected Performance

### Build Process:
1. **Docker Image Build**: 3-5 minutes
2. **Dependency Installation**: 2-3 minutes
3. **Model Loading**: 30-60 seconds
4. **Service Ready**: Total ~5-8 minutes

### Runtime Performance:
- **Cold Start**: 30-45 seconds (first request)
- **Warm Requests**: 1-3 seconds
- **Memory Usage**: ~800MB-1.5GB
- **CPU Usage**: Low (except during AI processing)

Your NASA hackathon backend is now ready for professional Docker deployment! 🌟
# 🚀 Deploy NASA Skynet Backend to Render

## ✅ Code Reverted & Ready
Your frontend code has been reverted to use `localhost:5000` and optimized Render deployment files have been created.

## 📋 Step-by-Step Render Deployment

### 1. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Connect your GitHub repository: `eshu3104/nasa-hackathon-2025`

### 2. Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your repository: `eshu3104/nasa-hackathon-2025`
3. Select branch: `name`

### 3. Configure Service Settings
```
Name: skynet-nasa-backend
Region: Ohio (US East) - recommended for speed
Branch: name
Root Directory: (leave empty)
Runtime: Python 3
Build Command: ./build.sh
Start Command: gunicorn render_app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

### 4. Set Environment Variables
In the Render dashboard, add these environment variables:
```
OPENAI_API_KEY=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
PORT=10000
```

### 5. Advanced Settings (Optional)
```
Instance Type: Starter (Free) or Starter+ ($7/month for better performance)
Auto-Deploy: Yes (deploys automatically on git push)
```

## 📁 Files Created for Render

### 1. `render_app.py`
- Optimized Flask app for Render
- Better error handling
- Debug endpoint for troubleshooting

### 2. `requirements_render.txt`
- Streamlined dependencies
- Added `gunicorn` for production server
- Optimized for Render's environment

### 3. `build.sh`
- Custom build script for Render
- Installs dependencies
- Checks model files

### 4. `Procfile`
- Updated to use gunicorn
- Configured for better performance

## 🔧 After Deployment

### 1. Get Your Render URL
Once deployed, you'll get a URL like:
```
https://skynet-nasa-backend.onrender.com
```

### 2. Update Frontend Configuration
Update both frontend files to use your Render URL:

**File: `Frontendwebsetup/results.html`**
```javascript
const API_BASE = 'https://your-app-name.onrender.com/api';
```

**File: `frontend/search.html`**
```javascript
const API_BASE = 'https://your-app-name.onrender.com/api';
```

### 3. Test Your Deployment
1. **Health Check**: `https://your-app-name.onrender.com/health`
2. **Debug Info**: `https://your-app-name.onrender.com/debug`
3. **Search Test**: Use the frontend or test-integration.html

## 🚨 Important Notes

### Free Tier Limitations
- **Sleep Mode**: Free services sleep after 15 minutes of inactivity
- **Cold Starts**: First request after sleep takes 30+ seconds
- **Monthly Hours**: 750 hours per month (enough for development)

### Upgrade Benefits ($7/month)
- **No Sleep**: Always-on service
- **Faster**: Better performance
- **More Memory**: 1GB vs 512MB

### Model Files Issue
Your `models/` directory with embeddings might be too large for Render's build process. If deployment fails:

1. **Option A**: Use smaller model files (emb_small.npy instead of emb_full.npy)
2. **Option B**: Host model files on cloud storage (AWS S3, Google Cloud Storage)
3. **Option C**: Upgrade to paid plan for more build resources

## 🛠️ Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Ensure all dependencies are in requirements_render.txt
- Verify model files aren't too large

### Search Returns "Service Not Available"
- Check debug endpoint: `/debug`
- Verify OPENAI_API_KEY is set correctly
- Check if model files loaded properly

### Slow Response Times
- First request after sleep is always slow (cold start)
- Consider upgrading to paid plan
- Optimize model loading in code

## 🎯 Next Steps

1. **Deploy to Render** using the steps above
2. **Get your Render URL** from the dashboard
3. **Update frontend files** with the new URL
4. **Test the integration** using your frontend
5. **Share your NASA hackathon project** with the world!

## 📞 Support

If you encounter issues:
- Render has excellent documentation and support
- Check Render's build logs for detailed error messages
- The debug endpoint will help diagnose search service issues

Your NASA Skynet Knowledge Engine is ready for the cloud! 🚀
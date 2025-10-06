# Railway Deployment Guide for Skynet Knowledge Engine

## Prerequisites
- Railway account (https://railway.app)
- OpenAI API key
- Git repository

## Quick Deploy to Railway

### Method 1: Deploy from GitHub (Recommended)

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin main
   ```

2. **Connect to Railway**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your repository
   - Select your repository

3. **Configure Environment Variables**
   In the Railway dashboard, go to Variables and add:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `FLASK_ENV` - production
   - `DEBUG` - False
   - `PORT` - (Leave blank, Railway will auto-assign)
   - `CORS_ORIGINS` - * (or your frontend domain)

4. **Deploy**
   - Railway will automatically detect the Procfile and deploy
   - Wait for the build to complete
   - Your app will be available at the Railway-generated URL

### Method 2: Deploy using Railway CLI

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```

3. **Initialize Project**
   ```bash
   railway init
   ```

4. **Add Environment Variables**
   ```bash
   railway variables set OPENAI_API_KEY=your_key_here
   railway variables set FLASK_ENV=production
   railway variables set DEBUG=False
   ```

5. **Deploy**
   ```bash
   railway up
   ```

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes | - |
| `FLASK_ENV` | Flask environment | No | production |
| `DEBUG` | Enable debug mode | No | False |
| `PORT` | Server port | No | Auto-assigned by Railway |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No | * |

## Post-Deployment

### 1. Test Your Deployment
```bash
# Check health endpoint
curl https://your-app.railway.app/api/health

# Expected response:
# {"status": "healthy"}
```

### 2. Monitor Logs
In the Railway dashboard:
- Go to your project
- Click "Deployments"
- View real-time logs

### 3. Custom Domain (Optional)
In Railway dashboard:
- Go to Settings
- Click "Generate Domain" or add your custom domain
- Update DNS records as instructed

## Troubleshooting

### Build Failures
- Check that `requirements.txt` is up to date
- Verify Python version in `runtime.txt` matches your local version
- Review build logs in Railway dashboard

### Runtime Errors
- Check environment variables are set correctly
- Review application logs
- Verify OpenAI API key is valid
- Ensure model files are included in deployment

### Memory Issues
Railway free tier has memory limits:
- Consider upgrading to Pro plan
- Optimize model loading
- Reduce concurrent workers in Procfile

### Slow Startup
The app loads 11,460 chunks on startup:
- First request may be slow
- Consider implementing lazy loading
- Use Railway's always-on feature (Pro plan)

## Performance Optimization

### 1. Increase Workers
Edit `Procfile`:
```
web: gunicorn backend:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120
```

### 2. Add Caching
Consider adding Redis for caching search results (Railway addon available)

### 3. CDN for Static Files
Consider using a CDN for images and static assets

## Security Notes

- Never commit `.env` file
- Always use environment variables for secrets
- Keep dependencies updated
- Monitor API usage and costs
- Set appropriate CORS origins in production

## Estimated Costs

Railway Pricing (as of 2024):
- Free tier: $0/month (500 hours, then usage-based)
- Pro: $20/month (includes usage credits)

OpenAI API costs depend on usage:
- Embedding generation: ~$0.0001/1K tokens
- GPT-4o-mini completions: ~$0.15/1M input tokens, ~$0.60/1M output tokens

## Support

For issues:
1. Check Railway documentation: https://docs.railway.app
2. Review application logs
3. Check OpenAI API status
4. Contact Railway support via dashboard

## Rollback

If deployment fails:
1. Go to Railway dashboard
2. Click "Deployments"
3. Select previous successful deployment
4. Click "Redeploy"

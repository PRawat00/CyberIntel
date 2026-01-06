// PM2 Ecosystem Configuration for CyberIntel Summarizer
// Oracle Cloud A1 Deployment - cd.prwt.dev
//
// Usage:
//   pm2 start ecosystem.config.js
//   pm2 start ecosystem.config.js --only cyberintel-api
//   pm2 start ecosystem.config.js --only cyberintel-web

module.exports = {
  apps: [
    {
      name: 'cyberintel-api',
      cwd: '/home/ubuntu/CyberIntel',
      script: 'venv/bin/uvicorn',
      args: 'api.main:app --host 0.0.0.0 --port 8001',
      interpreter: 'none',
      env: {
        PATH: '/home/ubuntu/CyberIntel/venv/bin:' + process.env.PATH
      },
      watch: false,
      instances: 1,
      autorestart: true,
      max_memory_restart: '500M',
      error_file: '/home/ubuntu/CyberIntel/logs/api-error.log',
      out_file: '/home/ubuntu/CyberIntel/logs/api-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },
    {
      name: 'cyberintel-web',
      cwd: '/home/ubuntu/CyberIntel/frontend',
      script: 'node_modules/.bin/next',
      args: 'start -p 3001',
      interpreter: 'none',
      watch: false,
      instances: 1,
      autorestart: true,
      max_memory_restart: '300M',
      error_file: '/home/ubuntu/CyberIntel/logs/web-error.log',
      out_file: '/home/ubuntu/CyberIntel/logs/web-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};

  Start/Restart the Reasoning Loop

  # Reload the entire ecosystem (all services)
  pm2 reload ecosystem.config.js

  # Or start just the reasoning loop
  pm2 start ecosystem.config.js --only groq-reasoning-loop

  # Restart just the reasoning loop
  pm2 restart groq-reasoning-loop

  Monitor the Reasoning Loop

  # View all running processes
  pm2 list

  # View real-time logs
  pm2 logs groq-reasoning-loop

  # View logs with timestamps
  pm2 logs groq-reasoning-loop --timestamp

  # View last 100 lines
  pm2 logs groq-reasoning-loop --lines 100

  Stop/Delete the Reasoning Loop

  # Stop the reasoning loop
  pm2 stop groq-reasoning-loop

  # Delete from PM2
  pm2 delete groq-reasoning-loop

  # Fix and delet pm2 all
  pm2 stop all
  pm2 delete all
  pm2 save
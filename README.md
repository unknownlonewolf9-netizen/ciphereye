# ciphereye
Modular OSINT intelligence platform with FastAPI backend



## 🛡️ How to become Admin
1. Start the platform: `./start.sh`
2. Go to http://localhost:8501 and **Register** a new account.
3. Run this command in your terminal to promote yourself:
   ```bash
   docker compose exec backend python -m app.manage your-email

   to register a new user go to http://localhost:8502

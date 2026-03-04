# SWE_GR_2
-Tristan test line


  cd ~/School/CSE3026/git_stuff
  source test/swe/bin/activate (Or whatever you venv is at)
  pip install fastapi uvicorn (Once)
  
  uvicorn backend.main:app --reload --port 8000

  You should see: "Application startup complete."
  Leave this terminal running.

--Termial 2----------------------------------------------

  cd ~/School/CSE3026/git_stuff/recipe-search
  npm install
  npm run dev
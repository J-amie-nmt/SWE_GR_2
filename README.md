# Dr. Dan's Cookbook

## Local Testing Guide

Navigate to the repo folder:

`cd .../SWE_GR_2`

Activate your Python virtual environment:

`source [your venv here]/bin/activate`

Install requirements (once):

`pip3 install -r requirements.txt`

Run the backend on Uvicorn:

`uvicorn backend.main:app --reload --port 8000`

You should see: "Application startup complete."

Leave this terminal running, then in another terminal, run:

`cd .../SWE_GR_2/recipe-search`

`npm install`

`npm run dev`

Then the website should be locally running on http://localhost:3000/

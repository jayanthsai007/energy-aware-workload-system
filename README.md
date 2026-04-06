# Energy Aware Workload System

## Dev

Open two terminals, in the first one, run the commands shown for backend. In the second, run the commands shown for frontend

### Backend

Make sure you have python installed, and some form of virtual environment setup
Then, run the following commands:

```shell
cd backend
pip install -r requirements.txt
python ./ml/training/train.py
uvicorn app.main:app --reload
```

### Frontend

Make sure you have node installed
Then, run the following commands:

```shell
cd frontend
npm install
npm run dev
```

then visit https://localhost:5173

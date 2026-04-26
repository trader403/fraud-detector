FROM python:3.11-slim
WORKDIR /app

# 安装 LightGBM 所需的底层依赖
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]

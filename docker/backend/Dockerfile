FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY backend/requirements.txt .
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

# 复制源代码
COPY backend/ .

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]

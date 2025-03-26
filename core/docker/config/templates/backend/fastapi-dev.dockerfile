FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境目录
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# 安装基础依赖
COPY backend/requirements.txt .
RUN pip install --trusted-host mirrors.aliyun.com -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 5000

# 启动应用（使用开发模式）
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "5000"] 
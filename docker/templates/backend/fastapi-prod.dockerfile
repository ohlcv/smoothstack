FROM python:3.9-slim as build

WORKDIR /app

# 安装构建依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir build wheel

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有源代码
COPY . .

# 最终镜像
FROM python:3.9-slim

WORKDIR /app

# 复制依赖
COPY --from=build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# 复制应用代码
COPY --from=build /app /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# 暴露API端口
EXPOSE 8000

# 运行应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"] 
FROM node:16-alpine as build

WORKDIR /app

# 复制 package.json 和 package-lock.json 文件
COPY package*.json ./

# 安装依赖
RUN npm ci --silent

# 复制所有源代码
COPY . .

# 构建生产环境应用
RUN npm run build

# 生产环境使用 nginx 作为静态文件服务器
FROM nginx:alpine

# 复制构建结果到 nginx 服务目录
COPY --from=build /app/dist /usr/share/nginx/html

# 复制 nginx 配置文件
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口
EXPOSE 80

# 在容器启动时运行 nginx
CMD ["nginx", "-g", "daemon off;"] 
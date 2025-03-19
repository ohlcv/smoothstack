FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy source code
COPY frontend/ ./

# Build for production
RUN npm run build

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "run", "serve"] 
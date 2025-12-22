FROM node:18-alpine

# Install yarn
RUN apk add --no-cache yarn

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/yarn.lock* frontend/package-lock.json* ./

# Install dependencies
RUN yarn install --frozen-lockfile || npm install --legacy-peer-deps

# Copy frontend code
COPY frontend /app

# Expose port
EXPOSE 3000

# Start development server
CMD ["yarn", "start"]


FROM node:18-alpine

# Install yarn
RUN apk add --no-cache yarn

# Set working directory
WORKDIR /app

# Copy package files first (for better layer caching)
COPY package.json yarn.lock* package-lock.json* ./

# Install dependencies
RUN yarn install --frozen-lockfile || npm install --legacy-peer-deps

# Copy frontend source code (exclude node_modules via .dockerignore)
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["yarn", "start"]


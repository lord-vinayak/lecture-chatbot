FROM node:16-alpine

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install --legacy-peer-deps && \
    mkdir -p /app/node_modules/.cache /app/build && \
    chmod -R 777 /app/node_modules/.cache /app/build

# Copy app code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "start"]

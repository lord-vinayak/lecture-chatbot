FROM node:16-alpine

# npm drops root to "nobody" for lifecycle scripts by default, which then can't
# write into root-owned dirs it creates itself (e.g. node_modules/.cache) — keep it root
ENV NPM_CONFIG_UNSAFE_PERM=true

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy app code
COPY . .

# Expose port
EXPOSE 3000

# Bind-mounted volumes overwrite build-time permissions, so fix them at container start instead
CMD ["sh", "-c", "mkdir -p node_modules/.cache build && chmod -R 777 node_modules/.cache build && npm start"]

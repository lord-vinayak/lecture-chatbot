FROM node:16-alpine

ENV NPM_CONFIG_UNSAFE_PERM=true

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies, and pre-create the cache/build dirs with open perms so
# the anonymous /app/node_modules volume gets these baked in on first copy-up
# (an existing anonymous volume is never re-populated by a later image rebuild)
RUN npm install --legacy-peer-deps && \
    mkdir -p node_modules/.cache build && \
    chmod -R 777 node_modules/.cache build

# Copy app code
COPY . .

# Expose port
EXPOSE 3000

# Self-heal at start too, in case a bind mount or stale volume shadows the above
CMD ["sh", "-c", "mkdir -p node_modules/.cache build && chmod -R 777 node_modules/.cache build && npm start"]

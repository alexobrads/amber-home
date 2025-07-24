# Docker Setup for Next.js Frontend

This directory contains Docker configurations for both development and production environments.

## Development Setup (Hot Reloading)

The development setup uses volume mounting to enable live editing with hot reloading.

### Quick Start

1. **Create environment file:**
```bash
cp .env.example .env.local
# Edit .env.local with your DATABASE_URL
```

2. **Start development container:**
```bash
docker-compose -f docker-compose.dev.yml up --build
```

The application will be available at `http://localhost:3000` with hot reloading enabled.

### Development Features

- **Hot Reloading**: File changes are automatically detected and the app reloads
- **Volume Mounting**: Your local files are mounted into the container
- **Port Forwarding**: Port 3000 is exposed for access
- **Environment Variables**: Loaded from `.env.local`

### File Structure

```
nextjs-frontend/
├── Dockerfile.dev           # Development Dockerfile
├── docker-compose.dev.yml   # Development compose config
├── Dockerfile              # Production Dockerfile  
├── .dockerignore           # Files to exclude from build
└── README.docker.md        # This file
```

### Development Commands

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Rebuild and start
docker-compose -f docker-compose.dev.yml up --build

# Stop the container
docker-compose -f docker-compose.dev.yml down

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Shell into container
docker-compose -f docker-compose.dev.yml exec nextjs-frontend sh
```

## Production Setup

For production deployment:

```bash
# Build production image
docker build -t nextjs-frontend:prod .

# Run production container
docker run -p 3000:3000 \
  -e DATABASE_URL="your-db-url" \
  nextjs-frontend:prod
```

## Environment Variables

Set these in your `.env.local` file:

```env
DATABASE_URL=postgresql://amber_user:amber_password@host.docker.internal:5432/amber_home
```

**Note**: Use `host.docker.internal` instead of `localhost` when connecting to services running on your host machine from within Docker.

## Connecting to Database

If your PostgreSQL database is running:

- **On host machine**: Use `host.docker.internal:5432`
- **In another container**: Use the container name as hostname
- **Railway/Cloud**: Use the provided connection string

## Troubleshooting

**Hot reloading not working?**
- Check that files are being mounted correctly: `docker-compose -f docker-compose.dev.yml exec nextjs-frontend ls -la`
- Ensure you're editing files in the mounted directory

**Database connection issues?**
- Verify DATABASE_URL in `.env.local`
- Check that database is accessible from container
- Use `host.docker.internal` for host machine databases

**Port conflicts?**
- Change the port mapping in `docker-compose.dev.yml`: `"3001:3000"`

**Permission issues?**
- The container runs as non-root user `nextjs` (uid 1001)
- Ensure your local files have appropriate permissions
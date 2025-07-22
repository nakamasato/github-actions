# Build and Push to GAR (Google Artifact Registry)

Build Docker images and push to Google Artifact Registry with intelligent caching strategies optimized for different runner types and use cases. Features 2025-compatible GitHub Actions Cache API v2 support.

## ✨ Features

- 🚀 **Intelligent Cache Strategies**: Auto-detects optimal cache configuration based on runner type
- 🏃‍♂️ **Multi-Runner Support**: Optimized for both GitHub-hosted and self-hosted runners  
- 📈 **Performance Boost**: Up to 90% build time reduction with proper caching
- 🔄 **2025-Ready**: Compatible with GitHub Actions Cache API v2
- 🛠️ **Flexible Configuration**: 6 different cache strategies to choose from

## 📥 Inputs

### Required Inputs
| Input | Description |
|-------|-------------|
| `project` | GCP project ID |
| `image` | Docker image name |
| `workload_identity_provider` | Workload Identity Provider |
| `service_account` | Service Account |

### Optional Inputs
| Input | Description | Default |
|-------|-------------|--------|
| `region` | GCP region | `asia-northeast1` |
| `repository` | GAR repository name | `cloud-run-source-deploy` |
| `image_tag` | Image tag | `latest` |
| `dockerfile` | Dockerfile path | `Dockerfile` |
| `context` | Docker build context | `.` |
| `build-args` | Docker build arguments | |
| `driver` | Docker buildx driver | `docker-container` |

### Cache Strategy Inputs
| Input | Description | Default |
|-------|-------------|--------|
| `cache_strategy` | Cache strategy (see strategies below) | `auto` |
| `cache_scope` | Cache scope for multi-image builds | Image name |
| `local_cache_path` | Local cache path for self-hosted runners | `/tmp/.buildx-cache` |
| `registry_cache_tag` | Registry cache image tag | `buildcache` |
| `use_registry_cache` | *(Legacy)* Enable registry cache fallback | `false` |

## 📤 Outputs

| Output | Description |
|--------|-------------|
| `imageid` | Docker image ID |
| `digest` | Image digest |
| `metadata` | Build metadata |
| `full_image_name` | Complete image name with registry |

## 🚀 Cache Strategies

Choose the optimal cache strategy based on your setup:

### `auto` (Recommended)
**Best for**: Most use cases  
**Description**: Automatically selects the best strategy based on runner type
- GitHub-hosted runners → `gha` or `hybrid`
- Self-hosted runners → `local`

### `gha` - GitHub Actions Cache
**Best for**: GitHub-hosted runners, standard workflows  
**Features**: Fast access, 10GB limit, branch-scoped
```yaml
cache_strategy: gha
```

### `local` - Local Filesystem Cache
**Best for**: Self-hosted runners, dedicated build machines  
**Features**: Fastest access, no size limit, persistent across builds
```yaml
cache_strategy: local
local_cache_path: /var/cache/docker-buildx  # Optional custom path
```

### `registry` - GAR Registry Cache  
**Best for**: Multi-runner environments, cross-branch caching
**Features**: Persistent, shareable, no GitHub limits
```yaml
cache_strategy: registry
registry_cache_tag: buildcache  # Optional custom tag
```

### `hybrid` - GHA + Registry Cache
**Best for**: GitHub-hosted with fallback resilience  
**Features**: Fast GHA with registry backup
```yaml
cache_strategy: hybrid
```

### `triple` - Local + GHA + Registry
**Best for**: High-frequency builds, maximum performance  
**Features**: All cache types for optimal hit rates
```yaml
cache_strategy: triple
local_cache_path: /var/cache/docker-buildx
```

## 📊 Performance Comparison

| Strategy | GitHub-hosted | Self-hosted | Multi-Image | Cross-Branch | Setup Complexity |
|----------|---------------|-------------|-------------|--------------|------------------|
| `auto` | ✅ Best | ✅ Best | ✅ Good | ✅ Good | 🟢 Minimal |
| `gha` | ✅ Excellent | ❌ Slow | ✅ Good | ⚠️ Limited | 🟢 Minimal |
| `local` | ❌ None | ✅ Excellent | ✅ Excellent | ✅ Good | 🟡 Medium |
| `registry` | ✅ Good | ✅ Good | ✅ Excellent | ✅ Excellent | 🟡 Medium |
| `hybrid` | ✅ Excellent | ✅ Good | ✅ Excellent | ✅ Good | 🟡 Medium |
| `triple` | ✅ Good | ✅ Excellent | ✅ Excellent | ✅ Excellent | 🔴 High |

## 📚 Usage Examples

### Basic Usage (Auto Strategy)
```yaml
name: Build and Push
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Build and Push
        uses: nakamasato/github-actions/build-and-push-to-gar@main
        with:
          project: my-gcp-project
          image: my-app
          workload_identity_provider: projects/123/locations/global/workloadIdentityPools/pool/providers/provider
          service_account: build-sa@my-gcp-project.iam.gserviceaccount.com
          # cache_strategy: auto (default)
```

### Self-Hosted Runner with Local Cache
```yaml
name: Build and Push
on: [push]

jobs:
  build:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - name: Build and Push
        uses: nakamasato/github-actions/build-and-push-to-gar@main
        with:
          project: my-gcp-project
          image: my-app
          workload_identity_provider: ${{ secrets.WIP }}
          service_account: ${{ secrets.SA }}
          cache_strategy: local
          local_cache_path: /data/docker-cache
```

### Multi-Image Project
```yaml
name: Build Multiple Images
jobs:
  build-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Frontend
        uses: nakamasato/github-actions/build-and-push-to-gar@main
        with:
          project: my-gcp-project
          image: frontend
          cache_scope: frontend-app
          dockerfile: frontend/Dockerfile
          context: frontend/
          # ... other inputs
          
  build-backend:
    runs-on: ubuntu-latest 
    steps:
      - uses: actions/checkout@v4
      - name: Build Backend
        uses: nakamasato/github-actions/build-and-push-to-gar@main
        with:
          project: my-gcp-project
          image: backend
          cache_scope: backend-app
          dockerfile: backend/Dockerfile
          context: backend/
          # ... other inputs
```

### High-Performance Setup
```yaml
name: High-Performance Build
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build with Triple Cache
        uses: nakamasato/github-actions/build-and-push-to-gar@main
        with:
          project: my-gcp-project
          image: high-perf-app
          cache_strategy: triple
          registry_cache_tag: cache-v2
          # ... other inputs
```

## 🔧 Migration from Legacy

If you're using the legacy `use_registry_cache: true` parameter:

**Before:**
```yaml
use_registry_cache: true
```

**After:**
```yaml
cache_strategy: hybrid  # or auto
```

## ⚡ 2025 Compatibility

This action is fully compatible with GitHub Actions Cache API v2 (effective April 15, 2025). Requires:
- Docker Engine >= v28.0.0
- Docker Buildx >= v0.13.0  
- BuildKit >= v0.13.0

## 🎯 Best Practices

1. **Use `auto` strategy** for most cases - it's smart enough to pick the right approach
2. **Set `cache_scope`** for multi-image projects to avoid cache conflicts
3. **Use `local` strategy** on self-hosted runners for best performance
4. **Monitor cache hit rates** in action logs to optimize your strategy
5. **Clean up old caches** periodically in long-running projects

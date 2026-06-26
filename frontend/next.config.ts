import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
    ]
  },
  images: {
    domains: ['localhost'],
  },
  experimental: {
    typedRoutes: false,
  },
}

export default nextConfig

/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb',
    },
  },
  async rewrites() {
		return [
			{
				source: '/api/:path*',
				destination: `https://playground.aelf.com/:path*`,
			},
		]
	},
};

export default nextConfig;

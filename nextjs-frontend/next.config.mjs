import ForkTsCheckerWebpackPlugin from 'fork-ts-checker-webpack-plugin';

/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_VWORLD_API_KEY:
      process.env.NEXT_PUBLIC_VWORLD_API_KEY ?? "911F93C0-1397-3872-8B45-1FF34FA707B2",
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.plugins.push(
        new ForkTsCheckerWebpackPlugin({
          async: true, // Run type checking synchronously to block the build
          typescript: {
            configOverwrite: {
              compilerOptions: {
                skipLibCheck: true,
              },
            },
          },
        })
      );
    }
    return config;
  },
};

export default nextConfig;
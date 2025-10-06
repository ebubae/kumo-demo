/** @type {import('next').NextConfig} */

const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "kumo-public-datasets.s3.us-west-2.amazonaws.com",
        port: "",
        search: "",
      },
    ],
  },
  rewrites: async () => {
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://0.0.0.0:8000/api/:path*"
            : "/api/",
      },
    ];
  },
};

export default nextConfig;

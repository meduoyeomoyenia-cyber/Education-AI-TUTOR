/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  output: 'export', // fully static site: Netlify serves web/out, no Next server needed
};

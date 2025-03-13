const { defineConfig } = require('@vue/cli-service')
const path = require('path')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    allowedHosts: "all",
    static: {
      directory: path.join(__dirname, 'public'),
      publicPath: '/'
    }
  }
})

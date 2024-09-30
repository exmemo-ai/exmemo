const { defineConfig } = require('@vue/cli-service')
const { devServer } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    allowedHosts: "all"
  }
})


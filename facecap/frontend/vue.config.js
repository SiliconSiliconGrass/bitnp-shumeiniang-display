// config for facecap frontend
const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 9235 // facecap frontend port
  }
})

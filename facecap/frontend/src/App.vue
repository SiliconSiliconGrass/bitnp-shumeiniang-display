<template>
  <canvas class="live2d_canvas" id="main-canvas"></canvas>
</template>

<script>
import { live2d_setup } from './live2d_display/script.js'

export default {
  name: 'App',
  components: {
    // HelloWorld
  },
  mounted() {
    const MODEL_URL = "/DAver3.0/DAnew_version.model3.json";
    const CANVAS = document.getElementById("main-canvas");

    if (CANVAS) {
      live2d_setup(CANVAS, MODEL_URL).then(() => {
        console.log('live2d_setup done');
      });
    } else {
      console.error('Canvas element not found');
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

.live2d_canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
  border: none;
  z-index: 9999;
}
</style>

<template>
  <canvas class="live2d_canvas" id="main-canvas"></canvas>

  <!-- param visualization -->
  <div class="slider-area-left" v-if="debug">
    <div class="slider-container" v-for="(item, index) in modelSliders" v-bind:key="index">
      <input
        type="range" 
        v-model="modelSliders[index].value" 
        :min="item.min" 
        :max="item.max" 
        :step="item.step" 
        @input="onInput"
      />
      <div>{{ item.name }} = {{ item.value.toFixed(3) }}</div>
    </div>
  </div>

  <div class="slider-area-right" v-if="debug && faceSliders.length > 0">
    <div v-for="(item, index) in faceSliders" v-bind:key="index" class="slider-container">
      <input
        type="range" 
        v-model="faceSliders[index].value" 
        :min="item.min" 
        :max="item.max" 
        :step="item.step" 
        @input="onInput"
      />
      <div>{{ item.name }} = {{ item.value.toFixed(3) }}</div>
    </div>
  </div>

</template>

<script>
import { live2d_setup } from './live2d_display/script.js'

export default {
  name: 'App',
  components: {
    // HelloWorld
  },
  data() {
    return {
      debug: false,
      modelSliders: [],
      faceSliders: [],
      model: null,
      coreModel: null
    }
  },
  mounted() {
    const MODEL_URL = "/DAver3.0/DAnew_version.model3.json";
    const CANVAS = document.getElementById("main-canvas");
    const self = this;
    setTimeout(() => {
      if (CANVAS) {
        live2d_setup(CANVAS, MODEL_URL, self).then(() => {
          console.log('live2d_setup done');
        });
      } else {
        console.error('Canvas element not found');
      }
    }, 100);
    
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

.slider-area-left {
  position: fixed;
  z-index: 999999999;
  overflow-y: scroll;
  height: 80vh;
  top: 0;
  left: 0;
  margin-top: 10vh;
}

.slider-area-right {
  position: fixed;
  z-index: 999999999;
  overflow-y: scroll;
  height: 80vh;
  top: 0;
  right: 0;
  margin-top: 10vh;
}

.slider-container {
  display: flex;
}
</style>

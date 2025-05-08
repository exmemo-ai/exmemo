<template>
  <el-dialog v-model="visible" :title="t('img.imgTitle')" :width="dialogWidth">
    <div class="image-process-container">
      <canvas ref="canvas" style="border: 1px solid #ccc;"></canvas>
      <div class="controls">
        <el-tabs v-model="activeTab">
          <el-tab-pane :label="t('img.adjustment')" name="adjust">
            <el-button-group>
              <el-button @click="resetImage">
                <el-icon>
                  <Refresh />
                </el-icon>
              </el-button>
              <el-button @click="rotateRight">
                <el-icon>
                  <RefreshRight />
                </el-icon>
              </el-button>
              <el-button @click="convertToGrayscale">
                {{ t('img.grayscale') }}
              </el-button>
            </el-button-group>
            <div class="slider-row">
              <span class="slider-label">{{ t('img.brightness') }}</span>
              <el-slider v-model="brightness" :min="-100" :max="100" @change="handleImageAdjust" />
            </div>
            <div class="slider-row">
              <span class="slider-label">{{ t('img.contrast') }}</span>
              <el-slider v-model="contrast" :min="-100" :max="100" @change="handleImageAdjust" />
            </div>
          </el-tab-pane>
          <el-tab-pane :label="t('img.ocr')" name="ocr">
            <el-button @click="handleOCR">{{ t('img.extractText') }}</el-button>
            <el-input v-model="ocrText" type="textarea" :rows="4" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="visible = false">{{ t('cancel') }}</el-button>
        <el-button type="primary" @click="handleConfirm('imageOnly')" v-if="activeTab !== 'ocr'">
          {{ t('img.insertImage') }}
        </el-button>
        <el-button type="primary" @click="handleConfirm('imageAndText')" v-if="activeTab === 'ocr'">
          {{ t('img.insertBoth') }}
        </el-button>
        <el-button type="primary" @click="handleConfirm('textOnly')" v-if="activeTab === 'ocr'">
          {{ t('img.insertText') }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onBeforeUnmount, nextTick, computed, onMounted } from 'vue';
import { RefreshRight, Refresh } from '@element-plus/icons-vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { getURL, setDefaultAuthHeader, parseBackendError } from '@/components/support/conn'
import { Canvas, FabricImage, filters } from 'fabric';
import { ElMessage } from 'element-plus';

let fabricCanvas = null;
let fabricImage = null;
let originalImageData = null;

let dialogWidth = computed(() => {
  return window.innerWidth <= 768 ? '90%' : '60%'
})

let dialogHeight = computed(() => {
  return window.innerWidth <= 768 ? '70%' : '70%'
})

onMounted(() => {
  window.addEventListener('resize', () => {
    dialogWidth.value = window.innerWidth <= 768 ? '90%' : '60%'
    dialogHeight.value = window.innerWidth <= 768 ? '70%' : '70%'
  })
})

const props = defineProps({
  modelValue: Boolean,
  imageUrl: String
});

const emit = defineEmits(['update:modelValue', 'confirm']);
const { t } = useI18n();

const visible = ref(false);
const previewUrl = ref('');
const activeTab = ref('adjust');
const brightness = ref(0);
const contrast = ref(0);
const ocrText = ref('');
const isGrayscale = ref(false);
let callbackFn = null;
const canvas = ref(null);

const initCanvas = async () => {
  if (!canvas.value) {
    console.warn('Canvas element not found');
    return;
  }

  try {
    if (fabricCanvas) {
      fabricCanvas.dispose();
      fabricCanvas = null;
    }

    fabricCanvas = new Canvas(canvas.value, {
      width: parseInt(dialogWidth.value * 0.8),
      height: parseInt(dialogHeight.value * 0.6),
      selection: false
    });

    if (previewUrl.value) {
      loadImage(previewUrl.value);
    }
  } catch (error) {
    console.error('Failed to initialize fabric canvas:', error);
  }
};

const loadImage = async (url) => {
  if (!fabricCanvas) {
    console.warn('Canvas not initialized');
    return;
  }

  try {
    fabricImage = await FabricImage.fromURL(url, {
      crossOrigin: 'anonymous'
    });

    fabricCanvas.clear();

    const scale = Math.min(
      (fabricCanvas.width / fabricImage.width),
      (fabricCanvas.height / fabricImage.height)
    );

    fabricImage.scale(scale);
    fabricImage.set({
      left: (fabricCanvas.width - fabricImage.width * scale) / 2,
      top: (fabricCanvas.height - fabricImage.height * scale) / 2
    });
    fabricCanvas.add(fabricImage);
    fabricCanvas.requestRenderAll();

    originalImageData = {
      angle: fabricImage.angle,
      filters: [],
      scale: scale,
      left: fabricImage.left,
      top: fabricImage.top
    };

  } catch (error) {
    console.error('Failed to load image:', error);
  }
};

const rotateRight = () => {
  if (!fabricImage) return;
  fabricImage.rotate(fabricImage.angle + 90);
  fabricCanvas.renderAll();
};

const convertToGrayscale = () => {
  if (!fabricImage) return;
  isGrayscale.value = !isGrayscale.value;
  applyFilters();
};

const handleImageAdjust = () => {
  if (!fabricImage) return;
  applyFilters();
};

const applyFilters = () => {
  if (!fabricImage) return;
  fabricImage.filters = [];

  if (isGrayscale.value) {
    fabricImage.filters.push(new filters.Grayscale());
  }

  if (brightness.value !== 0) {
    fabricImage.filters.push(new filters.Brightness({
      brightness: brightness.value / 100
    }));
  }

  if (contrast.value !== 0) {
    fabricImage.filters.push(new filters.Contrast({
      contrast: contrast.value / 100
    }));
  }

  fabricImage.applyFilters();
  fabricCanvas.renderAll();
};

const resetImage = () => {
  if (!fabricImage || !originalImageData) return;

  fabricImage.set({
    angle: originalImageData.angle,
    left: originalImageData.left,
    top: originalImageData.top,
    scaleX: originalImageData.scale,
    scaleY: originalImageData.scale
  });

  fabricImage.filters = [];
  fabricImage.applyFilters();
  fabricCanvas.renderAll();

  brightness.value = 0;
  contrast.value = 0;
  isGrayscale.value = false;
};

const open = async (url, callback) => {
  try {
    if (fabricCanvas) {
      fabricCanvas.dispose();
      fabricCanvas = null;
    }

    previewUrl.value = url;
    visible.value = true;
    callbackFn = callback;
    brightness.value = 0;
    contrast.value = 0;
    ocrText.value = '';
    activeTab.value = 'adjust';
    originalImageData = null;
    await nextTick();
    await initCanvas();
  } catch (error) {
    console.error('Failed to open image process dialog:', error);
    callback?.(null);
  }
};

const getProcessedImage = async () => {
  console.log('getProcessedImage', fabricCanvas, fabricImage);
  if (!fabricCanvas || !fabricImage) return null;

  try {
    const img = new Image();
    const imageLoadPromise = new Promise((resolve, reject) => {
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.crossOrigin = 'anonymous';
      img.src = previewUrl.value;
    });
    const loadedImg = await imageLoadPromise;

    const originalWidth = loadedImg.naturalWidth || 800;
    const originalHeight = loadedImg.naturalHeight || 600;
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = originalWidth;
    tempCanvas.height = originalHeight;
    
    const tempFabricCanvas = new Canvas(tempCanvas);    
    const tempImage = new FabricImage(loadedImg, {
      scaleX: 1,
      scaleY: 1,
      left: 0,
      top: 0,
      originX: 'left',
      originY: 'top',
      angle: fabricImage.angle
    });

    tempImage.filters = [...fabricImage.filters];    
    tempImage.applyFilters();
    tempFabricCanvas.add(tempImage);
    tempFabricCanvas.renderAll();
    
    const dataURL = tempFabricCanvas.toDataURL({
      format: 'png',
      quality: 1
    });
    tempFabricCanvas.dispose();
    return dataURL;
  } catch (error) {
    console.error('get image failed:', error);
    return null;
  }
};

const handleConfirm = async (mode = 'imageOnly') => {
  try {
    if (callbackFn) {
      const processedImageData = await getProcessedImage();
      if (!processedImageData && mode !== 'textOnly') {
        throw new Error('Failed to get processed image');
      }

      switch (mode) {
        case 'imageOnly':
          callbackFn({ file: processedImageData });
          visible.value = false;
          break;
        case 'textOnly':
          if (!ocrText.value || ocrText.value.trim() === '') {
            ElMessage.error(t('img.noTextPleaseExtract'));
            return;
          }
          callbackFn({ text: ocrText.value });
          visible.value = false;
          break;
        case 'imageAndText':
          if (!ocrText.value || ocrText.value.trim() === '') {
            ElMessage.error(t('img.noTextPleaseExtract'));
            return;
          }
          callbackFn({
            text: ocrText.value,
            file: processedImageData
          });
          visible.value = false;
          break;
      }
    }
  } catch (error) {
    console.error('Confirm failed:', error);
    callbackFn?.(null);
  }
};

const handleOCR = async () => {
  const processedImageData = await getProcessedImage();
  if (!processedImageData) {
    console.error('Failed to get processed image');
    return;
  }

  const base64Data = processedImageData.split(',')[1];
  const blob = await fetch(`data:image/png;base64,${base64Data}`).then(res => res.blob());

  const formData = new FormData();
  formData.append('file', blob, 'processed_image.png');
  formData.append('rtype', 'processimage');
  formData.append('opt', 'ocr');

  try {
    setDefaultAuthHeader();
    const response = await axios.post(getURL() + 'api/entry/tool/', formData);
    const data = await response.data;
    if (data.status === 'success') {
      ocrText.value = data.text;
    }
  } catch (error) {
    console.error('OCR failed:', error);
  }
};

onBeforeUnmount(() => {
  if (fabricCanvas) {
    fabricCanvas.dispose();
  }
});

const close = () => {
  visible.value = false;
  if (fabricCanvas) {
    fabricCanvas.dispose();
    fabricCanvas = null;
  }
  previewUrl.value = '';
  fabricImage = null;
};

defineExpose({
  open,
  close
});
</script>

<style scoped>
.image-process-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

canvas {
  max-width: 100%;
  height: auto;
}

.controls {
  width: 100%;
  max-width: 500px;
}

.el-button-group {
  margin-bottom: 15px;
}

.el-slider {
  margin: 0;
}

.slider-row {
  display: flex;
  align-items: center;
  margin: 5px 0;
}

.slider-label {
  min-width: 70px;
  margin-right: 16px;
  text-align: right;
  color: #606266;
  font-size: 14px;
}
</style>

<template>
  <el-dialog v-model="visible" :title="t('imageProcess.title')" width="80%">
    <div class="image-process-container">
      <div class="preview-container">
        <canvas ref="canvas" style="border: 1px solid #ccc;"></canvas>
      </div>
      <div class="controls">
        <el-tabs v-model="activeTab">
          <el-tab-pane :label="t('imageProcess.adjustment')" name="adjust">
            <el-button-group>
              <el-button @click="rotateLeft">
                <el-icon><Refresh /></el-icon>
              </el-button>
              <el-button @click="rotateRight">
                <el-icon><RefreshRight /></el-icon>
              </el-button>
              <el-button @click="invertColors">
                {{ t('imageProcess.invert') }}
              </el-button>
              <el-button @click="convertToGrayscale">
                {{ t('imageProcess.grayscale') }}
              </el-button>
            </el-button-group>
            <el-slider v-model="brightness" :min="-100" :max="100" @change="handleImageAdjust">
              {{ t('imageProcess.brightness') }}
            </el-slider>
            <el-slider v-model="contrast" :min="-100" :max="100" @change="handleImageAdjust">
              {{ t('imageProcess.contrast') }}
            </el-slider>
          </el-tab-pane>
          <el-tab-pane :label="t('imageProcess.ocr')" name="ocr">
            <el-button @click="handleOCR">{{ t('imageProcess.extractText') }}</el-button>
            <el-input v-model="ocrText" type="textarea" rows="4" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
    <template #footer>
      <el-button @click="visible = false">{{ t('cancel') }}</el-button>
      <el-button type="primary" @click="handleConfirm">{{ t('confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { Refresh, RefreshRight } from '@element-plus/icons-vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { getURL, setDefaultAuthHeader, parseBackendError } from '@/components/support/conn'
import { Canvas, FabricImage, filters } from 'fabric';

let fabricCanvas = null;
let fabricImage = null;

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
let callbackFn = null;

const canvas = ref(null);

const onDialogOpen = async () => {
  await nextTick();
  await initCanvas();
};

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

    canvas.value.width = 400;
    canvas.value.height = 300;
    
    fabricCanvas = new Canvas(canvas.value, {
      width: 400,
      height: 300,
      selection: false
    });
    console.log('Canvas initialized successfully');

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
      (fabricCanvas.width / fabricImage.width) * 0.9,
      (fabricCanvas.height / fabricImage.height) * 0.9
    );
    
    fabricImage.scale(scale);
    //fabricImage.center(); // later
    fabricCanvas.add(fabricImage);
    fabricCanvas.requestRenderAll();

  } catch (error) {
    console.error('Failed to load image:', error);
  }
};

const rotateLeft = () => {
  if (fabricImage) {
    fabricImage.rotate(fabricImage.angle - 90);
    fabricCanvas.renderAll();
  }
};

const rotateRight = () => {
  if (fabricImage) {
    fabricImage.rotate(fabricImage.angle + 90);
    fabricCanvas.renderAll();
  }
};

const invertColors = () => {
  if (!fabricImage) return;
  const filter = new filters.Invert();
  fabricImage.filters.push(filter);
  fabricImage.applyFilters();
  fabricCanvas.renderAll();
};

const convertToGrayscale = () => {
  if (!fabricImage) return;
  const filter = new filters.Grayscale();
  fabricImage.filters.push(filter);
  fabricImage.applyFilters();
  fabricCanvas.renderAll();
};

const handleImageAdjust = () => {
  if (!fabricImage) return;
  fabricImage.filters = [];
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

const open = async (url, callback) => {
  console.log('Opening image process dialog with URL:', url);
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
    
    await nextTick();
    await initCanvas();
    if (fabricCanvas) {
      loadImage(url);
    }
  } catch (error) {
    console.error('Failed to open image process dialog:', error);
    callback?.(null);
  }
};

const getProcessedImage = () => {
  if (!fabricCanvas) return null;
  return fabricCanvas.toDataURL({
    format: 'png',
    quality: 1
  });
};

const handleConfirm = () => {
  try {
    visible.value = false;
    if (callbackFn) {
      if (activeTab.value === 'ocr') {
        callbackFn({
          needServerProcess: true,
          file: ocrText.value,
          params: { ocr: true }
        });
      } else {
        const processedImageData = getProcessedImage();
        if (!processedImageData) {
          throw new Error('Failed to get processed image');
        }
        callbackFn({
          needServerProcess: false,
          file: processedImageData
        });
      }
    }
  } catch (error) {
    console.error('Confirm failed:', error);
    callbackFn?.(null);
  }
};

const handleOCR = async () => {
  const formData = new FormData();
  const response = await fetch(previewUrl.value);
  const blob = await response.blob();
  formData.append('file', blob);
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
  visible,
  close
});
</script>

<style scoped>
.image-process-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.preview-container {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  min-height: 300px;
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
  margin: 10px 0;
}
</style>

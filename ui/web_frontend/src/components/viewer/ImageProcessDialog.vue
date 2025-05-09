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
              <el-button @click="toggleCropMode" :type="cropMode ? 'primary' : 'default'">
                <el-icon v-if="!cropMode">
                  <Crop />
                </el-icon>
                <span v-if="cropMode">{{ t('img.exitCrop') }}</span>
                <span v-else>{{ t('img.crop') }}</span>
              </el-button>
              <el-button @click="confirmCrop" v-if="cropMode">
                {{ t('img.applyCrop') }}
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
import { RefreshRight, Refresh, Crop } from '@element-plus/icons-vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { getURL, setDefaultAuthHeader, parseBackendError } from '@/components/support/conn'
import { Canvas, FabricImage, filters, Rect, Path } from 'fabric';
import { ElMessage } from 'element-plus';

let fabricCanvas = null;
let fabricImage = null;
let originalImageData = null;
let cropRect = null;
let cropOverlay = null;
const cropMode = ref(false);

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
const baseUrl = ref('');
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
      await loadImage(previewUrl.value);
      saveInfo();
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
    const newImage = await FabricImage.fromURL(url, {
      crossOrigin: 'anonymous'
    });
    if (fabricImage) {
      fabricCanvas.remove(fabricImage);
      fabricImage.dispose();
    }    
    fabricImage = newImage;
    fabricImage.selectable = false;
    fabricImage.evented = false;
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
  } catch (error) {
    console.error('Failed to load image:', error);
  }
};

const saveInfo = () => {
  if (!fabricImage) return;
  originalImageData = {
      angle: fabricImage.angle,
      filters: [],
      scale: fabricImage.scaleX,
      left: fabricImage.left,
      top: fabricImage.top
    };
}

const rotateRight = async () => {
  if (!fabricImage) return;
  
  try {
    await applyRotation(90);
  } catch (error) {
    console.error('Rotation failed:', error);
  }
};

const applyRotation = async (angle) => {
  if (!fabricCanvas || !fabricImage) return;

  try {
    const imgElement = fabricImage.getElement();
    const originalWidth = imgElement.width;
    const originalHeight = imgElement.height;

    const tempCanvas = document.createElement('canvas');
    if (angle % 180 === 0) {
      tempCanvas.width = originalWidth;
      tempCanvas.height = originalHeight;
    } else {
      tempCanvas.width = originalHeight;
      tempCanvas.height = originalWidth;
    }

    const ctx = tempCanvas.getContext('2d');
    ctx.translate(tempCanvas.width / 2, tempCanvas.height / 2);
    ctx.rotate(angle * Math.PI / 180);

    const drawX = -originalWidth / 2;
    const drawY = -originalHeight / 2;
    console.log('drawX', drawX, 'drawY', drawY, 'originalWidth', originalWidth, 'originalHeight', originalHeight);
    ctx.drawImage(imgElement, drawX, drawY, originalWidth, originalHeight);

    const rotatedDataURL = tempCanvas.toDataURL('image/png');
    previewUrl.value = rotatedDataURL;
    await loadImage(previewUrl.value);
  } catch (error) {
    console.error('Rotation failed:', error);
    throw error;
  }
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

  if (previewUrl.value !== baseUrl.value) {
    previewUrl.value = baseUrl.value;
    loadImage(previewUrl.value);
  } else {
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
  }
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

    cropMode.value = false;
    previewUrl.value = url;
    baseUrl.value = url;
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
  if (cropMode.value) {
    endCropping(true);
    cropMode.value = false;
  }
  
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

const toggleCropMode = () => {
  if (!fabricImage) return;
  
  cropMode.value = !cropMode.value;
  if (cropMode.value) {
    startCropping();
  } else {
    endCropping(false);
  }
};

function throttle(func, wait) {
  let timeout = null;
  let lastCall = 0;
  
  return function(...args) {
    const now = Date.now();
    const remaining = wait - (now - lastCall);
    
    if (remaining <= 0 || remaining > wait) {
      if (timeout) {
        clearTimeout(timeout);
        timeout = null;
      }
      lastCall = now;
      func.apply(this, args);
    } else if (!timeout) {
      timeout = setTimeout(() => {
        lastCall = Date.now();
        timeout = null;
        func.apply(this, args);
      }, remaining);
    }
  };
}

const startCropping = () => {
  if (!fabricCanvas || !fabricImage) return;
  
  const imgBounds = fabricImage.getBoundingRect();
  fabricCanvas.clear();
  fabricCanvas.add(fabricImage);
  
  cropRect = new Rect({
    left: imgBounds.left + imgBounds.width * 0.1,
    top: imgBounds.top + imgBounds.height * 0.1,
    width: imgBounds.width * 0.8,
    height: imgBounds.height * 0.8,
    fill: 'transparent',
    stroke: 'white',
    strokeDashArray: [5, 5],
    strokeWidth: 2,
    transparentCorners: false,
    cornerColor: 'white',
    cornerStrokeColor: 'black',
    cornerSize: 10,
    lockRotation: true,
  });
  
  updateCropOverlay();
  fabricCanvas.add(cropRect);
  fabricCanvas.setActiveObject(cropRect);
  
  const throttledUpdateCropOverlay = throttle(updateCropOverlay, 100);
  cropRect.on('moving', throttledUpdateCropOverlay);
  cropRect.on('scaling', throttledUpdateCropOverlay);  
  
  cropRect.on('moving', function(e) {
    const obj = this;
    const imgBounds = fabricImage.getBoundingRect();    
    const objWidth = obj.width * obj.scaleX;
    const objHeight = obj.height * obj.scaleY;
    
    if (obj.left < imgBounds.left) {
      obj.set('left', imgBounds.left);
    }
    if (obj.top < imgBounds.top) {
      obj.set('top', imgBounds.top);
    }
    if (obj.left + objWidth > imgBounds.left + imgBounds.width) {
      obj.set('left', imgBounds.left + imgBounds.width - objWidth);
    }
    if (obj.top + objHeight > imgBounds.top + imgBounds.height) {
      obj.set('top', imgBounds.top + imgBounds.height - objHeight);
    }
  });
  
  cropRect.on('scaling', function(e) {
    const obj = this;
    const imgBounds = fabricImage.getBoundingRect();
    
    const objWidth = obj.width * obj.scaleX;
    const objHeight = obj.height * obj.scaleY;
    
    if (obj.left < imgBounds.left) {
      const newScaleX = obj.scaleX - (imgBounds.left - obj.left) / obj.width;
      obj.set('scaleX', newScaleX > 0.1 ? newScaleX : 0.1);
      obj.set('left', imgBounds.left);
    }
    
    if (obj.top < imgBounds.top) {
      const newScaleY = obj.scaleY - (imgBounds.top - obj.top) / obj.height;
      obj.set('scaleY', newScaleY > 0.1 ? newScaleY : 0.1);
      obj.set('top', imgBounds.top);
    }
    
    if (obj.left + objWidth > imgBounds.left + imgBounds.width) {
      const rightOverflow = (obj.left + objWidth) - (imgBounds.left + imgBounds.width);
      const newScaleX = obj.scaleX - rightOverflow / obj.width;
      obj.set('scaleX', newScaleX > 0.1 ? newScaleX : 0.1);
    }
    
    if (obj.top + objHeight > imgBounds.top + imgBounds.height) {
      const bottomOverflow = (obj.top + objHeight) - (imgBounds.top + imgBounds.height);
      const newScaleY = obj.scaleY - bottomOverflow / obj.height;
      obj.set('scaleY', newScaleY > 0.1 ? newScaleY : 0.1);
    }
  });
  
  fabricCanvas.renderAll();
};

const createCropOverlayPath = (imgBounds, cropRect) => {
  const cropLeft = Math.max(cropRect.left, imgBounds.left);
  const cropTop = Math.max(cropRect.top, imgBounds.top);
  const cropRight = Math.min(cropRect.left + cropRect.width * cropRect.scaleX, imgBounds.left + imgBounds.width);
  const cropBottom = Math.min(cropRect.top + cropRect.height * cropRect.scaleY, imgBounds.top + imgBounds.height);
  
  const outerPath = [
    'M', imgBounds.left, imgBounds.top,
    'L', imgBounds.left + imgBounds.width, imgBounds.top,
    'L', imgBounds.left + imgBounds.width, imgBounds.top + imgBounds.height,
    'L', imgBounds.left, imgBounds.top + imgBounds.height,
    'z'
  ];

  const innerPath = [
    'M', cropLeft, cropTop,
    'L', cropLeft, cropBottom,
    'L', cropRight, cropBottom,
    'L', cropRight, cropTop,
    'z'
  ];
  return outerPath.concat(innerPath).join(' ');
};

const updateCropOverlay = () => {
  if (!cropRect || !fabricImage) return;
  
  const imgBounds = fabricImage.getBoundingRect();
  const pathData = createCropOverlayPath(imgBounds, cropRect);
  const newOverlay = new Path(pathData, {
    fill: 'rgba(0,0,0,0.5)',
    selectable: false,
    evented: false
  });
  if (cropOverlay) {
    fabricCanvas.remove(cropOverlay);
    cropOverlay.dispose();
  }
  fabricCanvas.add(newOverlay);
  cropOverlay = newOverlay;
};

const endCropping = (apply = false) => {
  if (!fabricCanvas || !fabricImage) return;
  
  if (apply && cropRect) {
    applyCrop();
  }
  
  if (cropRect) {
    fabricCanvas.remove(cropRect);
    cropRect = null;
  }
  
  if (cropOverlay) {
    fabricCanvas.remove(cropOverlay);
    cropOverlay = null;
  }
    
  fabricCanvas.renderAll();
  cropMode.value = false;
};

const confirmCrop = () => {
  endCropping(true);
};

const applyCrop = async () => {
  if (!fabricCanvas || !fabricImage || !cropRect) return;
  
  try {
    const imgElement = fabricImage.getElement();
    const cropRectScaled = {
      left: (cropRect.left - fabricImage.left) / fabricImage.scaleX,
      top: (cropRect.top - fabricImage.top) / fabricImage.scaleY,
      width: cropRect.width * cropRect.scaleX / fabricImage.scaleX,
      height: cropRect.height * cropRect.scaleY / fabricImage.scaleY
    };
    
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = cropRectScaled.width;
    tempCanvas.height = cropRectScaled.height;
    const ctx = tempCanvas.getContext('2d');
    
    ctx.drawImage(
      imgElement, 
      cropRectScaled.left, 
      cropRectScaled.top, 
      cropRectScaled.width, 
      cropRectScaled.height, 
      0, 0, 
      cropRectScaled.width, 
      cropRectScaled.height
    );
    
    const croppedDataURL = tempCanvas.toDataURL('image/png');
    previewUrl.value = croppedDataURL;

    loadImage(previewUrl);
    const newImage = await FabricImage.fromURL(croppedDataURL);
    
    fabricCanvas.remove(fabricImage);
    fabricImage = newImage;
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
    fabricCanvas.renderAll();
    ElMessage.success(t('img.cropSuccess'));
  } catch (error) {
    console.error('Crop failed:', error);
    ElMessage.error(t('img.cropFailed'));
  }
};

onBeforeUnmount(() => {
  if (fabricCanvas) {
    fabricCanvas.dispose();
  }
});

const close = () => {
  visible.value = false;
  cropMode.value = false;
  if (fabricCanvas) {
    fabricCanvas.dispose();
    fabricCanvas = null;
  }
  previewUrl.value = '';
  baseUrl.value = '';
  fabricImage = null;
  cropRect = null;
  cropOverlay = null;
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

<template>
  <div>
    <div class="player-toggle" @click="setPlayer">
      <el-icon>
        <VideoPlay v-if="!showPlayer" />
        <Close v-else />
      </el-icon>
    </div>
    <div v-if="showPlayer" class="player-footer">
      <div class="player-controls">
        <el-button-group>
          <el-button :icon="Setting" @click="showSettingDialog"></el-button>
          <el-button :icon="Prev2Icon" @click="player?.prevParagraph()" :disabled="!playerStatus.canGoPrevPara">
            </el-button>
          <el-button :icon="Prev1Icon" @click="player?.prevSentence()" :disabled="!playerStatus.canGoPrevSentence">
            </el-button>
          <el-button :icon="playIcon" @click="togglePlay">
          </el-button>
          <el-button :icon="Next1Icon" @click="player?.nextSentence()" :disabled="!playerStatus.canGoNextSentence">
          </el-button>
          <el-button :icon="Next2Icon" @click="player?.nextParagraph()" :disabled="!playerStatus.canGoNextPara">
          </el-button>
          <el-button :icon="StopIcon" @click="player?.stop()"></el-button>
        </el-button-group>
      </div>
    </div>
  </div>

  <el-dialog v-model="showSettings" width="66%" :close-on-click-modal="false">
    <setting-t-t-s ref="settingsRef" />
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="cancelSettings">{{ t('cancel') }}</el-button>
        <el-button type="primary" @click="confirmSettings">{{ t('confirm') }}</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import {  Setting, Close, VideoPause, VideoPlay } from '@element-plus/icons-vue'
import PlayIcon from '@/components/icons/PlayIcon.vue'
import PauseIcon from '@/components/icons/PauseIcon.vue'
import StopIcon from '@/components/icons/StopIcon.vue'
import Prev1Icon from '@/components/icons/Prev1Icon.vue'
import Prev2Icon from '@/components/icons/Prev2Icon.vue'
import Next1Icon from '@/components/icons/Next1Icon.vue'
import Next2Icon from '@/components/icons/Next2Icon.vue'
import { TextPlayerManager } from './TextPlayerManager'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import SettingTTS from '@/components/settings/SettingTTS.vue'
import SettingService from '@/components/settings/settingService'

const { t } = useI18n()
const props = defineProps({
  text: {
    type: String,
    required: true
  },
  lang: {
    type: String,
    default: 'zh-CN'
  },
  getContentCallback: {
    type: Function,
    required: true
  }
})

const showPlayer = ref(true)
const player = ref(null)
const playerStatus = ref({
  isPlaying: false,
  isPaused: false,
  currentIndex: 0,
  sentencesCount: 0,
  canGoPrevPara: false,
  canGoNextPara: false,
  canGoPrevSentence: false,
  canGoNextSentence: false
})

const showSettings = ref(false)
const playIcon = computed(() => playerStatus.value.isPlaying ? PauseIcon : PlayIcon)

const formatProgress = () => {
  if (playerStatus.value.sentencesCount === 0) return '0/0'
  return `${(playerStatus.value.currentIndex + 1)}/${playerStatus.value.sentencesCount}`
}

const updateStatus = () => {
  if (player.value) {
    playerStatus.value = player.value.getStatus()
  }
}

const emit = defineEmits(['onSpeak'])

watch(() => props.text, () => {
  if (player.value) {
    player.value.stop()
  }
  player.value = new TextPlayerManager(props.text, props.lang)
  updateStatus()
}, { immediate: true })

onMounted(() => {
  player.value = new TextPlayerManager(props.text, props.lang)
  player.value.setOnSpeakCallback((text, index, node) => {
    emit('onSpeak', text, index, node)
  })
  updateStatus()

  const statusInterval = setInterval(updateStatus, 100)
  onBeforeUnmount(() => {
    clearInterval(statusInterval)
    player.value?.stop()
  })
})

const togglePlay = () => {
  console.log("togglePlay")
  if (player.value) {
    if (playerStatus.value.isPlaying) {
      player.value.pause()
    } else {
      const currentText = player.value.getText()
      console.log("resume", currentText)
      if (!currentText || currentText.length === 0) {
        playSetText()
      }
      player.value.resume()
    }
  }
}

const playSetText = () => {
  const content = props.getContentCallback() || {}
  if (content && player.value) {
    player.value.setContent(content)
  }
}

const showSettingDialog = () => {
  showSettings.value = true
  settingsRef.value?.reload();
}

const settingsRef = ref(null)

const cancelSettings = () => {
  showSettings.value = false
  SettingService.getInstance().resetPendingSetting()
}

const confirmSettings = async () => {
  await SettingService.getInstance().saveSetting()
  showSettings.value = false
}

const setPlayer = () => {
    try {
        if (showPlayer.value) {
            player.value?.stop();
            showPlayer.value = false;
            return;
        }
        showPlayer.value = true;
    } catch (error) {
        console.error('TTS error:', error);
        ElMessage.error(t('speakError') + error);
    }
}

defineExpose({
  speak: (index) => player.value?.speak(index),
  stop: () => player.value?.stop(),
  togglePlay: () => player.value?.togglePlay(),
  getStatus: () => player.value?.getStatus(),
  setContent: (content) => player.value?.setContent(content),
  resume: () => player.value?.resume()
})
</script>

<style scoped>
.text-speaker-player {
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
}

.player-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}

.player-controls :deep(.el-button) {
  min-width: 36px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
}

.player-controls :deep(.el-button i) {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.player-controls :deep(.el-button-group .el-button) {
  border: none;
}

.progress-text {
  color: #606266;
  font-size: 14px;
  min-width: 45px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.player-footer {
    flex-shrink: 1;
    position: relative;
    left: 0;
    right: 0;
    bottom: 0;
    background: #fff;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    padding: 0;
    min-height: 40px;
}

.player-toggle {
    position: fixed;
    left: 5px;
    bottom: 5px;
    width: 32px;
    height: 32px;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    opacity: 0.6;
    transition: all 0.3s;
    z-index: 1000;
    font-size: 14px;
    line-height: 1;
}

.player-toggle:hover {
    opacity: 1;
    transform: scale(1.1);
}

</style>

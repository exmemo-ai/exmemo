<template>
  <div class="player-controls">
    <el-button-group>
      <el-button :icon="DocumentParagraph" @click="player?.prevParagraph()"
        :disabled="!playerStatus.canGoPrevPara"> {{t("player.prevPara")}} </el-button>
      <el-button :icon="ArrowLeft" @click="player?.prevSentence()"
        :disabled="!playerStatus.canGoPrevSentence"> {{t("player.prevSentence")}}</el-button>
      <el-button :icon="playIcon" @click="togglePlay">
        {{ playerStatus.isPlaying ? t("player.pause") : t("player.play") }}
      </el-button>
      <el-button :icon="ArrowRight" @click="player?.nextSentence()"
        :disabled="!playerStatus.canGoNextSentence"> {{t("player.nextSentence")}} </el-button>
      <el-button :icon="DocumentParagraph" @click="player?.nextParagraph()"
        :disabled="!playerStatus.canGoNextPara"> {{t("player.nextPara")}} </el-button>
      <el-button @click="player?.stop()">{{t("player.stop")}}</el-button>
      <el-button :icon="Setting" @click="showSettingDialog"></el-button>
    </el-button-group>
  </div>

  <el-dialog
    v-model="showSettings"
    width="66%"
    :close-on-click-modal="false"
  >
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
import { DocumentParagraph, ArrowLeft, ArrowRight, VideoPlay, VideoPause, Setting } from '@element-plus/icons-vue'
import { TextPlayerManager } from './TextPlayerManager'
import { useI18n } from 'vue-i18n'
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
const playIcon = computed(() => playerStatus.value.isPlaying ? VideoPause : VideoPlay)

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

defineExpose({
  speak: (index) => player.value?.speak(index),
  stop: () => player.value?.stop(),
  togglePlay: () => player.value?.togglePlay(),
  getStatus: () => player.value?.getStatus(),
  setText: (content) => player.value?.setText(content),
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
</style>

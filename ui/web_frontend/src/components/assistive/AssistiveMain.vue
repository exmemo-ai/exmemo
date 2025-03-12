<template>
  <div class="full-container">
    <el-container style="flex: 0; width: 100%;">
      <app-navbar :title="$t('toolTitle')" :info="'SupportTools'" />
    </el-container>
    
    <el-container style="flex: 1; width: 100%; overflow: hidden;">
      <el-aside class="aside-menu" :class="{ 'collapse-aside': isCollapse, 'mobile-aside': isMobile }">
        <div class="toggle-button-collapse" @click="toggleCollapse">
          <el-icon>
            <Fold v-if="!isCollapse"/>
            <Expand v-else/>
          </el-icon>
        </div>
        <el-menu
          :default-active="activeView"
          :collapse="isCollapse"
          @select="handleMenuSelect">
          <el-menu-item index="paper">
            <span>{{ $t('paperAnalysis') }}</span>
          </el-menu-item>
          <!--
          <el-menu-item index="web">
            <span>{{ $t('webTools') }}</span>
          </el-menu-item>
          <el-menu-item index="tts">
            <span>{{ $t('voiceReading') }}</span>
          </el-menu-item>
          -->
        </el-menu>
      </el-aside>

      <el-main>
        <div v-show="activeView === 'paper'">
          <paper-analysis />
        </div>

        <div v-show="activeView === 'web'">
          <web-tools />
        </div>

        <div v-show="activeView === 'tts'">
          <voice-reader />
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { Fold, Expand } from '@element-plus/icons-vue'
import AppNavbar from '@/components/support/AppNavbar.vue'
import VoiceReader from './VoiceReader.vue'
import PaperAnalysis from './PaperAnalysis.vue'
import WebTools from './WebTools.vue'

export default {
  components: {
    AppNavbar,
    VoiceReader,
    PaperAnalysis,
    WebTools,
    Fold,
    Expand
  },
  data() {
    return {
      isMobile: false,
      isLogin: true,
      activeView: 'paper',
      login_user: '',
      isCollapse: false,
    };
  },
  methods: {
    handleMenuSelect(key) {
      this.activeView = key;
    },
    toggleCollapse() {
      this.isCollapse = !this.isCollapse;
    },
    handleResize() {
      this.isMobile = window.innerWidth < 768;
    }
  },
  mounted() {
    this.handleResize();
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
  }
}
</script>

<style>
.file-content {
  text-align: left;
  white-space: pre-wrap;
  word-wrap: break-word;
}

</style>
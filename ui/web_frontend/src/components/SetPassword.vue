<template>
  <div class="user-container">
    <el-card class="user-card">
      <h3 v-if="password_type === 'none'" class="user-title">{{ $t('initialLoginPrompt') }}</h3>
      <h2 v-else class="user-title">{{ $t('setPassword') }}</h2>

      <form @submit.prevent="set_password" class="user-form">
        <el-form-item v-if="password_type !== 'none'" :label="$t('oldPassword')">
          <el-input type="password" v-model="password_old" required></el-input>
        </el-form-item>

        <el-form-item :label="$t('newPassword')">
          <el-input type="password" v-model="password1" required></el-input>
        </el-form-item>

        <el-form-item :label="$t('confirmPassword')">
          <el-input type="password" v-model="password2" required></el-input>
        </el-form-item>

        <div class="button-group">
          <el-button type="primary" @click="set_password" class="user-button">
            {{ $t('submit') }}
          </el-button>
        </div>
      </form>
    </el-card>
  </div>
</template>

<script>
import axios from "axios";
import { getURL, setDefaultAuthHeader } from './conn'

export default {
  created() {
    if (this.$route.query.user_id && this.$route.query.user_id != "") {
      this.username = this.$route.query.user_id;
      this.password_type = this.$route.query.password_type;
    }
  },
  data() {
    return {
      username: "",
      password_old: "",
      password1: "",
      password2: "",
    };
  },
  methods: {
    async set_password() {
      if (this.password1 == "" || this.password2 == "") {
        this.$message({
          type: 'error',
          message: this.$t('passwordCannotBeEmpty'),
        });
        return;
      }
      if (this.password1 != this.password2) {
        this.$message({
          type: 'error',
          message: this.$t('passwordMismatch'),
        });
        return;
      }
      try {
        const formData = new FormData();
        formData.append('rtype', 'set_password');
        formData.append('user_id', this.username);
        formData.append('password_new', this.password1);
        if (this.password_old != "") {
          formData.append('password_old', this.password_old);
        }
        setDefaultAuthHeader();
        const response = await axios.post(getURL() + "api/user/", formData);
        if (response.data.status == "success") {
          this.$router.push("/login?user_name=" + this.username);
          this.$message({
            type: 'success',
            message: response.data.info,
          });
        } else {
          this.$message({
            type: 'error',
            message: response.data.info,
          });
        }
      } catch (error) {
        console.log(error);
      }
    },
  },
};
</script>

<style scoped>
</style>

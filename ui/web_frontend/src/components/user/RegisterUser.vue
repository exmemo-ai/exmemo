<template>
  <div class="user-container">
    <el-card class="user-card">
      <h2 class="user-title">{{ $t('userRegistration') }}</h2>
      <el-form @submit.native.prevent="register" class="user-form">
        <el-form-item :label="$t('username')">
          <el-input v-model="username" placeholder="请输入用户名"></el-input>
        </el-form-item>
        <el-form-item :label="$t('newPassword')">
          <el-input type="password" v-model="password1" placeholder="请输入密码" show-password></el-input>
        </el-form-item>
        <el-form-item :label="$t('confirmPassword')">
          <el-input type="password" v-model="password2" placeholder="请确认密码" show-password></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="register" style="width: 100%">{{ $t('submit') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import axios from "axios";
import { getURL } from '@/components/support/conn';

export default {
  data() {
    return {
      username: "",
      password1: "",
      password2: "",
    };
  },
  methods: {
    async register() {
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
        formData.append('rtype', 'register');
        formData.append('user_id', this.username);
        formData.append('password', this.password1);
        delete axios.defaults.headers.common['Authorization'];
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
        this.$message({
          type: 'error',
          message: error,
        });
      }
    },
  },
};
</script>

<style scoped>
</style>

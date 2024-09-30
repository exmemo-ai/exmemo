<template>
  <form @submit.prevent="register">
    <div class="register-container">
      <h2>{{ $t('userRegistration') }}</h2>
      <el-container class="register-form-container">
        <el-form-item :label="$t('username')">
          <el-input v-model="username" required></el-input>
        </el-form-item>
      </el-container>
      <el-container class="register-form-container">
        <el-form-item :label="$t('newPassword')">
          <el-input type="password" v-model="password1" required></el-input>
        </el-form-item>
      </el-container>
      <el-container class="register-form-container">
        <el-form-item :label="$t('confirmPassword')">
          <el-input type="password" v-model="password2" required></el-input>
        </el-form-item>
      </el-container>
      <el-container class="register-form-container">
        <el-button type="primary" @click="register">{{ $t('submit') }}</el-button>
      </el-container>
    </div>
  </form>
</template>

<script>
import axios from "axios";
import { getURL } from './conn'

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
      console.log("Set password button clicked!");
      console.log("Username:", this.username);
      console.log("Password:", this.password1, this.password2);
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
        console.log(response.data);
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
.register-container {
  justify-content: center;
  align-items: center;
  height: 100vh;
}

.register-form-container {
  display: flex;
  justify-content: center;
  align-items: center;
  max-width: full-width;
  padding: 10px;
  border-radius: 5px;
}
</style>

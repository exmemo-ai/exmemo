<template>
  <form @submit.prevent="login">
    <div class="login-container">
      <h1>{{ $t('login') }}</h1>
      <el-container class="login-form-container">
        <el-form-item :label="$t('username')">
          <el-input v-model="username" required></el-input>
        </el-form-item>
      </el-container>
      <el-container class="login-form-container">
        <el-form-item :label="$t('password')">
          <el-input type="password" v-model="password" required></el-input>
        </el-form-item>
      </el-container>
      <el-container class="login-form-container">
        <el-button type="primary" @click="login">{{ $t('login') }}</el-button>
        <el-button type="primary" @click="register">{{ $t('register') }}</el-button>
      </el-container>
    </div>
  </form>
</template>
  
<script>
import axios from "axios";
import { ElMessage } from "element-plus";
import { getURL } from './conn'

export default {
  created() {
    console.log('created login', this.$route.query);
    if (this.$route.query.user_name && this.$route.query.user_name != "") {
      this.check_password_set(this.$route.query.user_name);
    }
  },
  data() {
    return {
      username: "",
      password: "",
    };
  },
  methods: {
    async check_password_set(user_name) {
      // check if a password has been set.
      try {
        const response = await axios.get(getURL() + "api/user/",
          { params: { user_id: user_name, rtype: 'check_password' } });
        console.log(response.data.user_status)
        if (response.data.user_status == "set") {
          this.username = this.$route.query.user_name;
          return
        }
      } catch (error) {
        console.log(error);
      }
      this.$router.push("/set_password?user_name=" + this.$route.query.user_name + "&password_type=none");
    },
    async register() {
      console.log("Register button clicked!");
      this.$router.push("/register");
    },
    async login() {
      console.log("Login button clicked!");
      console.log("Username:", this.username);
      console.log("Password:", this.password);
      try {
        const formData = new FormData();
        formData.append("username", this.username);
        formData.append("password", this.password);
        const response = await axios.post(getURL() + "api/auth/login/", formData);
        console.log(response.data.message);
        ElMessage({
          type: 'success',
          message: this.$t('loginSuccess'),
        })
        console.log('@@@@', response.data.token)
        localStorage.setItem("token", response.data.token);
        localStorage.setItem("username", this.username);
        axios.defaults.headers.common['Authorization'] = 'Token ' + localStorage.getItem('token');
        this.$router.push("/");
      } catch (error) {
        if (error.response != undefined && error.response.status == 400) {
          ElMessage({
            type: 'error',
            message: this.$t('loginFailed400'),
          })
        } else {
          ElMessage({
            type: 'error',
            message: this.$t('loginFailed', { error: error.message }),
          })
        }
      }
    },
  },
};
</script>

<style scoped>
.login-container {
  justify-content: center;
  align-items: center;
  height: 100vh;
}

.login-form-container {
  display: flex;
  justify-content: center;
  align-items: center;
  max-width: full-width;
  padding: 10px;
  border-radius: 5px;
}
</style>

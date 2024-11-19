<template>
  <div class="user-container">
    <el-card class="user-card">
      <h1 class="user-title">{{ $t('login') }}</h1>
      <el-form @submit.prevent="login" class="user-form">
        <el-form-item :label="$t('username')">
          <el-input 
            v-model="username" 
            required
            prefix-icon="User"
          ></el-input>
        </el-form-item>
        
        <el-form-item :label="$t('password')">
          <el-input 
            type="password" 
            v-model="password" 
            required
            prefix-icon="Lock"
          ></el-input>
        </el-form-item>

        <div class="button-group">
          <el-button type="primary" @click="login" class="user-button">
            {{ $t('login') }}
          </el-button>
          <el-button @click="register" class="user-button">
            {{ $t('register') }}
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import axios from "axios";
import { ElMessage } from "element-plus";
import { getURL } from '@/components/support/conn';

export default {
  created() {
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
      this.$router.push("/register");
    },
    async login() {
      try {
        const formData = new FormData();
        formData.append("username", this.username);
        formData.append("password", this.password);
        const response = await axios.post(getURL() + "api/auth/login/", formData);
        ElMessage({
          type: 'success',
          message: this.$t('loginSuccess'),
        })
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
</style>

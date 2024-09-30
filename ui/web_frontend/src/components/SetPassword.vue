<template>
  <form @submit.prevent="set_password">
    <div class="setpasswd-container">
      <h3 v-if="password_type === 'none'">{{ $t('initialLoginPrompt') }}</h3>
      <h2 v-else>{{ $t('setPassword') }}</h2>
      <el-container v-if="password_type !== 'none'" class="setpasswd-form-container">
        <el-form-item :label="$t('oldPassword')">
          <el-input type="password" v-model="password_old" required></el-input>
        </el-form-item>
      </el-container>
      <el-container class="setpasswd-form-container">
        <el-form-item :label="$t('newPassword')">
          <el-input type="password" v-model="password1" required></el-input>
        </el-form-item>
      </el-container>
      <el-container class="setpasswd-form-container">
        <el-form-item :label="$t('confirmPassword')">
          <el-input type="password" v-model="password2" required></el-input>
        </el-form-item>
      </el-container>
      <el-container class="setpasswd-form-container">
        <el-button type="primary" @click="set_password">{{ $t('submit') }}</el-button>
      </el-container>
    </div>
  </form>
</template>

<script>
import axios from "axios";
import { getURL, setDefaultAuthHeader } from './conn'

export default {
  created() {
    console.log('created set_password', this.$route.query);
    if (this.$route.query.user_name && this.$route.query.user_name != "") {
      this.username = this.$route.query.user_name;
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
        formData.append('rtype', 'set_password');
        formData.append('user_id', this.username);
        formData.append('password_new', this.password1);
        if (this.password_old != "") {
          formData.append('password_old', this.password_old);
        }
        setDefaultAuthHeader();
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
      }
    },
  },
};
</script>

<style scoped>
.setpasswd-container {
  justify-content: center;
  align-items: center;
  height: 100vh;
}

.setpasswd-form-container {
  display: flex;
  justify-content: center;
  align-items: center;
  max-width: full-width;
  padding: 10px;
  border-radius: 5px;
}
</style>

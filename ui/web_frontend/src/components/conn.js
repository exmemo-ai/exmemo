import axios from 'axios';
import config from './config.js';

export function getURL() {
  let url = config.baseURL;
  if (url.length > 0 && url[url.length - 1] !== '/') {
    url += '/';
  }
  return url;
}

export function setDefaultAuthHeader() {
  const token = localStorage.getItem('token');
  if (token) {
    axios.defaults.headers.common['Authorization'] = 'Token ' + token;
  }
}

// 登录相关操作
export function checkLogin(obj) {
  setDefaultAuthHeader();
  console.log('Checking login status');
  if (localStorage.getItem('username') !== null) {
    console.log('Logged in');
    obj.login_user = localStorage.getItem('username');
    obj.isLogin = true;
    return true;
  } else {
    console.log('Not logged in');
    obj.isLogin = false;
    return false;
  }
}

export function realLoginFunc(obj) {
  obj.$router.push('/login');
}

export function realLogoutFunc(obj) {
  console.log("Logout button clicked!");
  if (localStorage.getItem('username') === null) {
    obj.$message({
      type: 'error',
      message: obj.$t('notLoggedIn')
    })
    return;
  }
  try {
    axios.post(getURL() + "api/auth/logout/");
    obj.$message({
      type: 'success',
      message: obj.$t('logoutSuccess'),
    })
  } catch (error) {
    obj.$message({
      type: 'warning',
      message: obj.$t('logoutFailed', { error: error.response.data }),
    })
  }
  localStorage.removeItem('username');
  delete axios.defaults.headers.common['Authorization'];
  obj.isLogin = false;
  obj.$router.push('/login');
}

export function parseBackendError(obj, err) {
  console.log(err);
  if (err.response === undefined) {
    obj.$message({
      message: obj.$t('loginExpired'),
      type: 'warning'
    });
  } else if (err.response.status === 401) {
    if (localStorage.getItem('token') !== null) {
      localStorage.setItem("token", null);
      obj.$message({
        message: obj.$t('loginExpired'),
        type: 'warning'
      });
      obj.$router.push('/login');
    }
  } else {
    obj.$message({
      message: obj.$t('operationFailed') + err,
      type: 'warning'
    });
  }
}

export function gotoAssistantPage(obj) {
  obj.$router.push('/support_tools');
}

export function gotoReaderPage(obj) {
  obj.$router.push('/enreader');
}

export function gotoSetting(obj) {
  obj.$router.push('/user_setting');
}

export function gotoDataPage(obj) {
  obj.$router.push('/');
}

export function realExportRecord(obj) { // later move to record ui
  let func = 'api/record/'
  let params = { rtype: 'export' }
  axios.get(getURL() + func, {
    responseType: 'blob',
    params: params
  })
    .then(response => {
      if (response.data.status == 'success') {
        parseBlobData(response, obj, 'export.xlsx');
      } else {
        obj.$message({
          type: 'error',
          message: this.$t('exportFail'),
        });
      }
    })
    .catch(error => {
      parseBackendError(obj, error);
    });
}

export function parseBlobData(response, obj, default_filename) {
  /* download file */
  console.log('download data', response.data.length);
  console.log(response.data);

  if (response.headers['content-type'].includes('application/json') || response.headers['content-type'].includes('text/html')) {
    const fileReader = new FileReader();
    fileReader.onload = (event) => {
      const text = event.target.result;
      let info = JSON.parse(text);
      if ('info' in info) {
        obj.$message({
          type: 'error',
          message: info['info'],
        });
      }
    }
    fileReader.readAsText(response.data);
    return;
  }

  try {
    let fileName = default_filename;
    const contentDisposition = response.headers['content-disposition'];
    console.log("contentDisposition" + contentDisposition)
    let encodedFileName = contentDisposition.split('?')[3];
    if (encodedFileName == undefined) {
      fileName = contentDisposition.split(';')[1].split('=')[1];
    } else {
      console.log("encodedFileName" + encodedFileName)
      let decodedFileName = decodeURIComponent(escape(window.atob(encodedFileName)));
      const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
      const matches = filenameRegex.exec(decodedFileName);
      if (matches != null && matches[1]) {
        fileName = matches[1].replace(/['"]/g, '');
      }
    }
    // regular file name
    fileName = fileName.replace(/"/g, '');
    console.log("*" + fileName + "*")
    // download file
    const blob = new Blob([response.data]);
    if ('download' in document.createElement('a')) { // not IE
      const elink = document.createElement('a');
      elink.download = fileName;
      elink.style.display = 'none';
      elink.href = URL.createObjectURL(blob);
      document.body.appendChild(elink);
      elink.click();
      URL.revokeObjectURL(elink.href);
      document.body.removeChild(elink);
    } else { // IE10+
      navigator.msSaveBlob(blob, fileName);
    }
  } catch (e) {
    console.log(e);
    obj.$message({
      type: 'error',
      message: this.$t('downloadFail'),
    });
  }
}

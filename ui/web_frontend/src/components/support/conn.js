import axios from 'axios';
import config from '@/components/support/config';
import { t } from '@/utils/i18n'
import { ElMessage } from 'element-plus';
import router from '@/main';

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

export function parseBackendError(err) {
  console.log(err);
  if (err.response === undefined) {
    ElMessage({
      message: t('loginExpired'),
      type: 'warning'
    });
  } else if (err.response.status === 401) {
    if (localStorage.getItem('token') !== null) {
      localStorage.setItem("token", null);
      ElMessage({
        message: t('loginExpired'),
        type: 'warning'
      });
      router.push('/login');
    }
  } else {
    ElMessage({
      message: t('operationFailed') + err,
      type: 'warning'
    });
  }
}

export function realExportRecord(obj) {
  let func = 'api/record/'
  let params = { rtype: 'export' }
  axios.get(getURL() + func, {
    responseType: 'blob',
    params: params
  })
    .then(response => {
      if (response.data.status == 'success') {
        parseBlobData(response, 'export.xlsx');
      } else {
        obj.$message({
          type: 'error',
          message: this.$t('exportFail'),
        });
      }
    })
    .catch(error => {
      parseBackendError(error);
    });
}

export function parseBlobData(response, default_filename) {
  /* download file */
  console.log('download data', response.data.length);
  console.log(response.data);

  if (response.headers['content-type'].includes('application/json') || response.headers['content-type'].includes('text/html')) {
    const fileReader = new FileReader();
    fileReader.onload = (event) => {
      const text = event.target.result;
      let info = JSON.parse(text);
      if ('info' in info) {
        ElMessage({
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

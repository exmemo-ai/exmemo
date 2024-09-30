const config = {
    baseURL: process.env.VUE_APP_K_BACKEND_ADDR.replace(/"/g, '').replace(/'/g, ''),
    langCode: process.env.VUE_APP_K_LANGUAGE_CODE.replace(/"/g, '').replace(/'/g, '')
};

export default config;
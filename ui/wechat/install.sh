PLUGIN_DIR='../../../chatgpt-on-wechat/plugins'
EXMEMO_DIR=${PLUGIN_DIR}/exmemo
echo 'copy to' ${EXMEMO_DIR}
mkdir ${EXMEMO_DIR} -p
cp exmemo.py ${EXMEMO_DIR}/
cp req.py ${EXMEMO_DIR}/
cp __init__.py ${EXMEMO_DIR}/
cp plugins.json ${PLUGIN_DIR}/

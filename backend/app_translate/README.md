## 代码
translate.py 对外接口
root_finder.py 查找词根的工具
word_root.py 一些词根工具，效果一般
dict.py	字典工具，查词用效果不错

## TODO
有一些代码没用到，一些路径写死了，还需要进一步整理

## SOURCE
需要安装 nltk 以及字典相关资源

cd /exports/data/
tar xvzf stardict.tgz 
cd /root/
tar xvzf nltk_data.tgz

字典压缩后 24M，最多减到 10M 左右
nltk压缩后需要 76M 左右空间，一部分能去掉
数据比较大，先放我笔记本的/exports/data目录了
# 執行方法

```
python main.py -o <output_dir> 

# 更新model /dataset repo list (在temp folder)
python main.py -o <output_dir> -r
```

To-Do
- 目前基於 https://huggingface.co/api/models 和 https://huggingface.co/api/datasets 這兩條連接爬，或沒找到方法去第2頁
- save file < 500 mb 
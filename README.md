## 项目介绍

项目名: 海贼王山治.

简介: 开发中常用到的工具函数或类.

## 代码介绍

### util

`util/normal.py` 只依赖标准库的工具.

`util/third_{package_name}.py` 依赖第三方的工具.

`util/demo.py` demo 级别的工具. (一些不经常使用但有一定参考价值的工具)

### test

`test/test_{util_module_name}.py` 对应工具的测试用例.

其中比较特殊的是 `test_third_requests`, 由于此测试中需要借助到服务器, 因此
默认测试用例是关闭的. 如果要开启此测试需要改变 `test_third_requests.CLOSE`.
并且手动开启一个 flask server. 例如:

```bash
export FLASK_APP=test/server:app
export FLASK_ENV=development
flask run
```

另一个类似的是 `test_third_cryptography` 中的一小部分测试用例. 由于密码学中 key 的生成
需要耗费大量的计算力, 因此用 `test_third_cryptography.CLOSE` 标记是否开启这些耗时的测试.

目前缺少单元测试的工具:

  - `util/third_peewee` 所有工具.

## 一些相关的仓库

有的工具不适合用函数或类来表现, 因此这些工具都单独有一个仓库.

- [html 转 pdf](https://github.com/dyq666/sanji_pdf)

## 一些有用的笔记

1. 什么是 timestamp ?

timestamp 是当前的 utc 时间与 1970-01-01 (即, epoch time 或 unix 时间) 相差的秒数 (浮点数).
下例中 `time.time()` 是标准库提供的 timestamp, 而后面的式子是我们手动计算的 timestamp.

```python
import time
from datetime import datetime
time.time(), (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()
```

2. 找一个 ua 解析库.

需要知道以下信息:

- 设备类型 (安卓 ios 等)
- 当前 App 的版本号 ?

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

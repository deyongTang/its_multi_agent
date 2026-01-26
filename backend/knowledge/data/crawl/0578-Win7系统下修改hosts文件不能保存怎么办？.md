# 知识库 578

## 标题
Win7系统下修改hosts文件不能保存怎么办？

## 问题描述
Win7系统下修改hosts文件不能保存的解决办法。

## 分类
主类别: 操作系统故障
子类别: 系统应用操作

## 关键词
win7, hosts, 无法保存, 上网

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
由于各种原因，有时我们需要更改[host](/detail/kd_17528.html)s文件来防止[服务器](/detail/kd_17589.html)验证，但却发现在修改完成之后保存不了。

1、首先打开该文件所在的文件，路径是：c:[windows](/detail/kd_17391.html)[sys](/detail/kd_17769.html)tem32driversetc；

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447831536245_536.jpg)

2、然后我们在该文件上面右键，选择属性选项；

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447831536245_423.jpg)

3、然后在打开的属性窗口中，我们切换到安全[选项卡](/detail/kd_17796.html)下；

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447831536245_101.jpg)

4、然后我们选择安全选项卡的高级按钮；

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447831536245_897.jpg)

5、在打开的新窗口中，我们选择更改权限的按钮；

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447831536245_455.jpg)

6、然后在打开的新窗口中去除包括可从该对像的父项继承的权限，然后再单击添加按钮；

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447831536245_487.jpg)

7、单击添加按钮之后，我们回到窗口中，单击确定按钮，弹出windows安全窗口，我们单击是按钮即可。

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447831536245_768.jpg)

8、然后我们再单击确定按钮，回到一开始的属性窗口中，然后选择我们当前用户所有的管理员组，并按编辑按钮；

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447831536245_510.jpg)

9、在弹出的窗口中，我们勾选当前用户所在的管理组、给予完全控制的权限；

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447831536245_463.jpg)

10、修改完成之后单击确定按钮，再单击确定按钮即可，这样就可以对Hosts文件进行修改了。

<!-- 文档主题：Win7系统下修改hosts文件不能保存怎么办？ (知识库库编号: 578) -->
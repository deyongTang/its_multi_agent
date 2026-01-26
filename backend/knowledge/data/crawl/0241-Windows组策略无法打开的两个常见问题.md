# 知识库 241

## 标题
Windows组策略无法打开的两个常见问题

## 问题描述
Windows组策略无法打开的两个常见问题，并指导该如何操作。

## 分类
主类别: 操作系统故障
子类别: 系统应用操作

## 关键词
XP, 查看, IP地址, 设置, 管理, Windows, 组策略

## 元信息
创建时间:2024-12-15|版本:2.0

## 解决方案
1、如果运行命令后提示，由于限制而被取消，请与系统管理员联系，而无法打开。此问题是由于组策略程序中的：“**只运行许可的Windows应用程序**”策略，被启用导致，把这个策略设置为“**未配置**”即可。

方法如下：  
  
（1）进入[安全模式](/detail/kd_17783.html)”[启动](/detail/kd_17514.html)，在运行窗口输入“**mmc c:[windows](/detail/kd_17391.html)[sys](/detail/kd_17769.html)tem32gpedit.msc**”（“C”为系统盘符）回车。即可运行组策略程序。

![](https://chinakb.lenovo.com.cn/chinakb/prod-api/file/downloadFile?key=uniko/IMAGE/140271c29cb165e8acedf6dcffbf552e-1714283375953.png&name=mceclip0.png)

![](https://chinakb.lenovo.com.cn/chinakb/prod-api/file/downloadFile?key=uniko/IMAGE/049272ca02e14bc2db190f0310125c6c-1714283401189.png&name=mceclip1.png)

（2）在组策略中展开“**用户配置-管理模版-系统**”，在右侧找到“**只运行许可的Windows应用程序**”策略，设置成“**未配置**”，再“**确定**”，这样下次正常运行。按“**Alt+Ctrl+ｄｅｌｅｔｅ**”[组合键](/detail/kd_17502.html)，点击左下角电源按钮选择[重启](/detail/kd_17977.html)，即可进入正常模式

2、如果运行命令后提示，您没有权限执行此操作，拒绝访问。此问题是由于是登录系统的帐号不是管理员权限导致，请使用管理员帐号登录即可。用[有管理员权限的Windows帐号](http://Robot.lenovo.com.cn/Rdata/Rfiles/105.html)登录系统，再运行组策略程序即可。

<!-- 文档主题：Windows组策略无法打开的两个常见问题 (知识库库编号: 241) -->
# 知识库 348

## 标题
Windows 7下如何实现共享上网

## 问题描述
共享上网，在资源有限的情况下，可以让更多的计算机联网。下面将指导Windows XP下如何实现共享上网。

## 分类
主类别: 网络问题
子类别: 共享上网

## 关键词
共享, 管理, 设置, 显示, 硬件, Windows, 查看, 上网

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**通过[共享](/detail/kd_17685.html)[本地连接](/detail/kd_17639.html)（有线，无线）的方式共享上网**

说明：确认共享本地连接的电脑即网关电脑有两块网卡（其中一块是有线或无线网卡），并且有交换机或集线器等网络设备，电脑与电脑之间通过网络设备或无线局域网连接。

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/303.files/image002.jpg)

**一、配置网关电脑**  
  
1、打开其中一个网卡的属性，必须保证此网卡可以正常连接到互联网。如下图：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/303.files/image004.jpg)

2、单击“**共享**”[选项卡](/detail/kd_17796.html)，然后选中“**允许其他网络用户通过此计算机的 Internet 连接来连接**”复选框，点**确定**退出。

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/303.files/image006.jpg)

注意：如果只有一个网卡，则“**共享**”选项卡将不可用。  
 

3、设置本地连接完成后则在本地连接图标上会出现共享标志，如下图：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/303.files/image008.jpg)

4、本地连接设置完成之后，另外一个网卡（有线，无线）[IP](/detail/kd_17443.html)地址已经被系统自动手动指定，如下图：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/303.files/image010.jpg)

**二、配置客户端电脑**  
  
1、打开客户端电脑的网络连接属性，如下图：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/303.files/image012.jpg)

2、双击上图中的“**Internet [协议](/detail/kd_17810.html) （[TCP](/detail/kd_17428.html)/IP）**”打开Internet 协议 （TCP/IP）属性窗口，选择“**自动获取IP地址**”点击“**确定**”退出。

3、如果客户端是无线网卡，在搜索到的无线网络列表中选择对应的[SSID](/detail/kd_17711.html)名称后点击“**连接**”即可实现无线共享上网。

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/303.files/image014.jpg)

<!-- 文档主题：Windows 7下如何实现共享上网 (知识库库编号: 348) -->
# 知识库 350

## 标题
在Windows XP下如何建立无线局域网

## 问题描述
本文详细介绍了在Windows XP下如何建立无线局域网的指导方法。

## 分类
主类别: 网络问题
子类别: 共享上网

## 关键词
软件, 功能, 技巧, Windows, 无线局域网, 在线

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**说明：**

1、如果是利用第三方的管理软件进行无线网络连接的设置，请在“无线网络连接属性”对话框中单击“无线网络配置标签”，并将“用Windows来配置我的无线网络配置”前的复选框对勾去掉，以关闭Windows XP自带的无线网络管理，其设置与上述Windows XP自带的无线网络管理大同小异，具体请参考相应的使用说明。

**操作步骤：**

1、启用无线网卡：请首先确认无线网卡的驱动程序已经正确安装，并打开无线网卡天线开关。联想笔记本大部分是FN＋F5（或F4）开启。

2、打开网络连接：依次打开“开始-控制面板-网络和Internet连接-网络连接”，右键单击“无线网络连接”选择“属性”，进入无线网络连接属性对话框，如下图所示：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/305.files/image001.jpg)

3、设置IP地址：双击“Internet协议（TCP/IP）”打开Internet协议（TCP/IP）属性对话框，如下图所示：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/305.files/image002.jpg)

设置IP地址可以通过两种方式：自动获得和指定固定IP，但所要互联的机器必须采取相同的IP设置方式，如果设置成指定固定IP，则这些机器的IP地址必须设置在同一网段内。建议使用自动获得IP地址。

4、启用Windows无线管理：在无线网络连接属性对话框中单击“无线网络配置标签”，在“用Windows来配置我的无线网络配置”前的复选框打勾，以启用Windows XP自带的无线网络管理。如下图所示：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/305.files/image003.jpg)

5、选定网络类型：单击对话框右下角的“高级”按钮，打开无线网络的高级选项，如下图所示，选择“任何可用的网络（首选访问点）”，也可以根据实际的连接方式选择其它方式，单击“关闭”退出。

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/305.files/image004.jpg)

6、添加无线网络：单击“无线网络配置”中的“添加”按钮，如下图所示：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/305.files/image005.jpg)

7、设置服务设置标识（SSID）：在打开的“无线网络属性”对话框中输入一个服务设置标识（SSID），例如“lenovo”，SSID必须和您想要连接的计算机或无线AP设置的SSID保持一致。如果您访问的是其它计算机，没有使用无线AP，将“这是一个计算机到计算机（特定的）网络；没有使用无线访问点”前打勾，如下图所示：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/305.files/image006.jpg)

而如果您使用了无线AP作为无线访问点，将“这是一个计算机到计算机（特定的）网络；没有使用无线访问点”前的对勾去掉，如下图所示：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/305.files/image007.jpg)

然后单击“确定”退出，在“无线网络配置属性”对话框下部的首选网络中会出现所设置的网络名称，如下图所示：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/305.files/image008.jpg)

8、连接网络：由于Windows默认的连接方式为“一旦检测到此网络，Windows可以自动连接”，当在有效范围内找到所设置的无线网络后，电脑将会成功连接到“lenovo”网络，即可实现双机或多机互联，如下图所示：

![](http://robotterm.ecare365.com/ZmptY2NtYW5hZ2Vy/p4data/Rdata/Rfiles/305.files/image009.jpg)

至此，无线局域网设置完成。

<!-- 文档主题：在Windows XP下如何建立无线局域网 (知识库库编号: 350) -->
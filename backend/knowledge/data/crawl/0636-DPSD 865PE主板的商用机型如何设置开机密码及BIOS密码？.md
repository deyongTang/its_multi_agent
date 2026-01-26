# 知识库 636

## 标题
DPSD 865PE主板的商用机型如何设置开机密码及BIOS密码？

## 问题描述
DPSD 865PE主板的商用机型设置开机密码及BIOS密码的操作方法指导。

## 分类
主类别: 预装软件
子类别: 其他随机软件

## 关键词
关机, 开机, 运行, 报错, 设置, BIOS, Windows, 密码

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
DPSD 865[PE](/detail/kd_17728.html)[主板](/detail/kd_17352.html)使用的是AMI [BI](/detail/kd_17343.html)[OS](/detail/kd_17441.html)，在其BIOS设置中没有SEC[URI](/detail/kd_17953.html)TY OPT[ION](/detail/kd_17884.html) 选项，BIOS设置中有一项Supervisor Pass[word](/detail/kd_17356.html) & User Password，可以进行开机密码及BIOS密码的设置。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/J8jA3r1TMjTE21yD.jpg)

进入该项设置中会有Supervisor Password和User Password两个状态项和两个设置项，两个状态项会根据设置的情况显示出Supervisor Password和User Password的设置状态，例如：Not Installed或Installed，两个设置项的设置会有几种搭配情况实现不同的功能。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/2UU49O67yTGPp8I2.jpg)

1、在只设置Supervisor Password而不设置User Password的情况下，则Supervisor Password为BIOS密码，没有系统开机密码。设置过程如下图：

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/9hU8Oro9JY1C2Ij6.jpg)

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/Qgm3Y4qgt4QJ1GJN.jpg)

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/laBqta6fDdpgbEz0.jpg)

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/4AOMsemV1T1mBOmq.jpg)

在设置了Supervisor Password之后，页面中会增加一项User Access Level设置项，该项中有四个可选项分别是NO Access、View Only、Limited、Full，这四个可选项是对以User Password登录BIOS设置的用户级权限的定义。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/HBPQjrz9T0SGefa7.jpg)

2、在只设置User Password不设置Supervisor Password的情况下，系统开机密码与BIOS密码相同，都为User Password，并且在设置了User Password之后，设置页面中会增加一项Clear User Password项，该项是用来清除User Password的。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/z6beu0bjnHFP3XwO.jpg)

系统开机登录界面如下图：

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/LnWndap4472W2xfd.jpg)

在只设置User Password不设置Supervisor Password的情况下，保存退出BIOS设置后，再次登录BIOS设置页面，进入Supervisor Password & User Password设置页面会发现Supervisor Password设置项没有了，Supervisor Password状态项显示为：Not Installed。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/VCDakuy4aGeBKqe9.jpg)

这时如果需要设置Supervisor Password,只有在使用Clear User Password项清除User Password后保存退出再重新登录BIOS设置页面，再进入Supervisor Password & User Password设置页面才能进行Supervisor Password的设置。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/h7Y6GW4847G2vXd9.jpg)

3、在同时设置了Supervisor Password和User Password的情况下，Supervisor Password和User Password都可以作为系统开机密码登录系统，而对于以User Password登录BIOS设置可以进行不同的权限分配。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2004-08-02/2rLRhg9JdSPpKMe6.jpg)

前面提到在设置了Supervisor Password之后，页面中会增加一项User Access Level设置项，该项中有四个可选项分别是NO Access、View Only、Limited、Full，这四个可选项是对以User Password登录BIOS设置的用户级权限的定义。四个可选项的含义分别是：

NO Access  禁止用户级权限对BIOS设置界面的访问

View Only  用户级权限只能查看BIOS设置中的设置值，但不能进行更改设置

Limited    用户级权限只能更改BIOS设置中的有限选项

Full       用户级权限可以更改除Supervisor Password之外的所有项

需要注意的是：在设置的Supervisor Password与User Password相同的情况下，登录BIOS设置页面，系统默认为Supervisor登录，User Access Level的设置不起作用，只有在设置了与Supervisor Password不同的User Password后，以User Password登录BIOS设置，这个User Access Level设置项的设置才会起作用。

<!-- 文档主题：DPSD 865PE主板的商用机型如何设置开机密码及BIOS密码？ (知识库库编号: 636) -->
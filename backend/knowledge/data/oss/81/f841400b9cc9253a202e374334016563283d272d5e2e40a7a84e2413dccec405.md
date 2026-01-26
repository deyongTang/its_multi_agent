# 知识库 81

## 标题
Lenovo G485 USB3.0驱动程序安装不上的解决方法

## 问题描述
若需要安装USB3.0驱动程序，首先要确保您使用的是Windows 7或Windows 8系统，XP系统不支持USB3.0接口。

## 分类
主类别: 其他硬件相关知识
子类别: 驱动相关

## 关键词
G485, USB3.0, USB驱动

## 元信息
创建时间:2024-12-15|版本:2.0

## 解决方案
**故障现象：**

当USB3.0接口无法使用，USB2.0接口正常，且设备管理器有“通用串行总线控制器”的驱动程序没有安装，如下图所示：

在设备管理器中出现：

 

![](https://webdoc.lenovo.com.cn/lenovowsi/20131010/1381375985928_821.jpg)

说明本机的USB3.0驱动程序未正常安装。目前驱动网站中，没有提供单独USB3.0设备驱动程序下载链接，而是与显卡驱动、主板芯片组驱动等集成在一起。

 

**解决方案：**

**方法一：**

可尝试重新安装官网提供的主板芯片组及显卡驱动程序，安装过程中选择“自定义”，确保USB3.0选项勾选。如下图所示：

 

![](https://webdoc.lenovo.com.cn/lenovowsi/20131010/1381375985928_263.jpg)

选择下一步，确认“USB3.0”项目勾选上；

 

![](https://webdoc.lenovo.com.cn/lenovowsi/20131010/1381375985928_368.jpg)

然后按照提示安装驱动即可。

 

**方法二：**

若方法一无效，可手动打开解压出来安装程序，双击：

 

![](https://webdoc.lenovo.com.cn/lenovowsi/20131010/1381375985928_329.jpg)

默认解压缩到桌面，点击安装后，桌面会出现文件夹1.Chipset\_VGA。打开后，找到“Packages---Drivers---SBDrv---hseries---USB3..0”目录，手动打开里面“amdhub\\W764A”文件夹下“amdhub30.msi”程序手动安装。（32位系统可选择“amdhub\\W7”目录下安装程序安装）

 

![](https://webdoc.lenovo.com.cn/lenovowsi/20131010/1381375985928_79.jpg)

![](https://webdoc.lenovo.com.cn/lenovowsi/20131010/1381375985928_447.jpg)

![](https://webdoc.lenovo.com.cn/lenovowsi/20131010/1381375985928_660.jpg)

![](https://webdoc.lenovo.com.cn/lenovowsi/20131010/1381375985928_367.jpg)

![](https://webdoc.lenovo.com.cn/lenovowsi/20131010/1381375985928_935.jpg)

![](https://webdoc.lenovo.com.cn/lenovowsi/20131010/1381375985928_803.jpg)

![](https://webdoc.lenovo.com.cn/lenovowsi/20131010/1381375985928_796.jpg)

<!-- 文档主题：Lenovo G485 USB3.0驱动程序安装不上的解决方法 (知识库库编号: 81) -->
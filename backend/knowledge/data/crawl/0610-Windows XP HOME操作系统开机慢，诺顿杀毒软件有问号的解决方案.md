# 知识库 610

## 标题
Windows XP HOME操作系统开机慢，诺顿杀毒软件有问号的解决方案

## 问题描述
Windows XP HOME操作系统开机慢，诺顿杀毒软件有问号的解决方案。

## 分类
主类别: 操作系统故障
子类别: 系统应用操作

## 关键词
Windows XP, 诺顿, 开机慢, 问号

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
 此现象通常是系统检测网络连接造成的，如果操作系统使用自动获取[IP](/detail/kd_17443.html)的宽带方式上网，此上网方式包括小区宽带和[ADSL](/detail/kd_17429.html) 宽带，就可能出现这种现象。

解决方法如下：将[TCP](/detail/kd_17428.html)/IP属性的“自动获取地址”改成“手动配置”，然后加入一个IP地址，如：192.168.0.1。这样开机速度就不会慢了，由于WINXP对DHCP有一定优化功能，因此不会影响正常的上网。如果修改后出现不能上网的情况，建议联系当地的网络服务提供商询问具体需要修改的IP地址和[子网掩码](/detail/kd_17531.html)。

具体操作如下：

1、   打开操作系统的[控制面板](/detail/kd_18077.html)

（[开始]菜单下控制面板选择页面）

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2005-06-22/2WK3Un64688JzG4i.JPG)  
  
（经典[开始]菜单下控制面板选择页面）  
  
![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2005-06-22/wgVLPYNri19BD0f0.JPG)

2、 选择网络连接

（分类视图下的网络连接选择页面）  
  
![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2005-06-22/s2jj1uCrB41N9oSu.JPG)

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2005-06-22/ac5F2CJEXl7oz1Bb.JPG)  
  
（经典视图下的网络连接选择页面）

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2005-06-22/agB8N4Wjy5h4U3Dp.JPG)

3、进入网络连接选项，选择[本地连接](/detail/kd_17639.html)属性

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2005-06-22/v21JEqvpm0AaUu06.JPG)

 

4、进入本地连接属性

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2005-06-22/o0IOdwsUNs728UEw.JPG)

5、选择进入Internet 协议（TCP/IP）属性，IP地址及子网掩码如图所示

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2005-06-22/jdf6J20PYusDhbt5.JPG)

<!-- 文档主题：Windows XP HOME操作系统开机慢，诺顿杀毒软件有问号的解决方案 (知识库库编号: 610) -->
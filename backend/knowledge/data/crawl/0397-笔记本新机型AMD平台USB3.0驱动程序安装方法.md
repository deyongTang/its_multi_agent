# 知识库 397

## 标题
笔记本新机型AMD平台USB3.0驱动程序安装方法

## 问题描述
笔记本新机型AMD平台USB3.0驱动程序安装方法.其实驱动程序安装包含有USB3.0设备驱动程序，由于某些原因导致安装失败。可尝试重新安装网站提供主板芯片组及显卡驱动程序，安装过程中选择“自定义”，确保usb3.0选项勾选

## 分类
主类别: 其他硬件相关知识
子类别: 驱动相关

## 关键词
联想, AMD, USB3.0, 驱动

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**相关文档：**

[Win8](/detail/kd_17986.html)改装为[Win7](/detail/kd_17983.html)后不能识别USB

[主板](/detail/kd_17352.html)芯片组及[显卡](/detail/kd_17348.html)驱动程序，安装过程中选择“**自定义**”，确保usb3.0选项勾选。如下图所示：

![](https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160411/1460360948146170.jpg)

确认“**USB3.0**”项目勾选上，如下图所示：

![](https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160411/1460360948732609.jpg)

若无效，可手动打开解压出来[安装程序](/detail/kd_17506.html)，找到“**PackagesDriversSBDrvhseriesUSB30**”目录即USB3.0芯片驱动程序，可手动打开里面“**[amd](/detail/kd_17354.html)hubW764A**”文件夹下“**amdhub30.msi**”程序手动安装。（32位系统可选择“**amdhubW7**”目录下安装程序安装）。如下图所示：

![](https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160411/1460360948776538.jpg)

另外可尝试手动更新[设备管理器](/detail/kd_17549.html)未能安装驱动程序的“**通用串行[总线](/detail/kd_17591.html)控制器**”，搜索路径选择到以上目录下。以上以“**Y485**”机型驱动程序为例，其他AMD机型参考查找USB3.0驱动程序所在文件夹即可。  
  
**适用AMD平台机型：**Y485;Y585;Z485;Z585;G485;G585;G405;G505;Z505;S415;S405等。

<!-- 文档主题：笔记本新机型AMD平台USB3.0驱动程序安装方法 (知识库库编号: 397) -->
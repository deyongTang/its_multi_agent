# 知识库 457

## 标题
Windows 7系统下任务栏通知区域里的电源图标消失如何处理

## 问题描述
Windows 7系统任务栏通知区域里的电源图标消失，打开通知区域图标管理，电源选项那块是灰色的。此情况可能与组策略被更改有关。

## 分类
主类别: 操作系统故障
子类别: 系统应用操作

## 关键词
win7, 任务栏, 通知区域, 图标, 电源图标, 消失

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**问题描述：**

[Windows 7](/detail/kd_17984.html)系统任务栏通知区域里的电源图标消失，打开通知区域图标管理，电源选项那块是灰色的。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2011-05-30/I9ykVigSE5CPmdEV.JPG)

**问题分析：**

此情况可能与组策略被更改有关。

**使用机器：**家庭基础版以外的WINODWS 7

**解决方案：**

在开始搜索框中键入gpedit.msc然后按回车键，打开本地组策略编辑器。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2011-05-30/UEDLrGeE3BoFf1l8.jpg)

在“用户配置”下依次打开“管理模板”->“[开始菜单](/detail/kd_18062.html)和任务栏”；在右边细节窗口，找到并双击“删除操作中心图标”选项。

[![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2011-05-30/C89x593HpGdjrGu4.JPG)](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2011-05-30/C89x593HpGdjrGu4.JPG)

将其配置为“未配置”或“已禁用”，然后按“确定”退出。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2011-05-30/dBnN12USryHsx71s.JPG)

现在，重新回到桌面。右键点击“显示隐藏的图标”，选择“属性”。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2011-05-30/07F6jYKr5JHdYVc5.JPG)

将电源图标打开。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2011-05-30/Dwtw8Pe4N51HsI33.JPG)

图标已经恢复正常。

![](https://webdoc.lenovo.com.cn/lenovowsi/uploadimages/2011-05-30/kNt9LXx2D3koWUTy.jpg)

<!-- 文档主题：Windows 7系统下任务栏通知区域里的电源图标消失如何处理 (知识库库编号: 457) -->
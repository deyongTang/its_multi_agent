# 知识库 24

## 标题
将Outlook设为Mac默认程序后为何仍弹出Apple Mail？

## 问题描述
把 Outlook 设置为 Mac 的默认应用程序后，从 Word/Excel/PowerPoint 中将文件作为附件发出，但弹出的却仍是 Apple Mail 的解决办法。

## 分类
主类别: 预装软件
子类别: Office软件

## 关键词
Outlook, Mac, 默认程序, 弹出, Apple Mail

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**故障现象：**

把 Outlook 设置为 Mac 的默认应用程序后，从 Word/Excel/PowerPoint 中将文件作为附件发出，但弹出的却仍是 Apple Mail。

**解决方案：**

打开 Finder，找到 User（当前出问题的账户）/Library/Preference，在 Preference 下找到并删除这两个文件：

com.apple.LaunchServices.plist

com.microsoft.Outlook.plist

![](https://webdoc.lenovo.com.cn/lenovowsi/20120604/1338800044859_817.png)

![](https://webdoc.lenovo.com.cn/lenovowsi/20120604/1338800044859_938.png)

重启系统，然后重新将 Outlook 设为默认应用程序。具体如下：

打开 Outlook，单击“Outlook-偏好设置”；

![](https://webdoc.lenovo.com.cn/lenovowsi/20120604/1338800044859_237.png)

在“个人设置”部分单击“常规”；

![](https://webdoc.lenovo.com.cn/lenovowsi/20120604/1338800044859_7.png)

单击“设为默认”按钮将 Outlook 设为电子邮件、日历和联系人的默认应用程序。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120604/1338800044859_603.png)

<!-- 文档主题：将Outlook设为Mac默认程序后为何仍弹出Apple Mail？ (知识库库编号: 24) -->
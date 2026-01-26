# 知识库 9

## 标题
禁止Office的上传中心和OneNote开机自启动的方法

## 问题描述
禁止Office 2010的上传中心和 OneNote 2010 开机自启动的方法。

## 分类
主类别: 预装软件
子类别: Office软件

## 关键词
OneNote, Office, 上传中心, 开机自启动

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**故障现象：**

开机时会自动启动黄色图标的Office2010上传中心和OneNote2010，不怎么常用还耽搁开机时间。  
  
![](https://webdoc.lenovo.com.cn/lenovowsi/20120412/1334223364359_856.png)  
  
**解决方案：**

单击「**开始**」在“**开始搜索**”框中，键入**msconfig**，然后按**Enter**。

或直接在键盘上按“**Win+R**”调出运行命令框，键入**msconfig**，然后按**Enter**。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120412/1334223364359_709.png)

切换到“**启动**”选项卡，在对话框中找到并清除以下复选框：

Microsoft OneNote

位置C:\\Users\\username\\AppData\\Roaming\\Microsoft\\Windows\\StartMenu\\Programs\\Startup

Microsoft Office2010

位置HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120412/1334223364359_398.png)

最后重启计算机。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120412/1334223364359_44.png)

<!-- 文档主题：禁止Office的上传中心和OneNote开机自启动的方法 (知识库库编号: 9) -->
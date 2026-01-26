# 知识库 7

## 标题
在 PowerPoint 2007 中无法输入中文怎么办？

## 问题描述
通过关闭高级文字服务和修改注册表来解决 PowerPoint 2007 中无法输入中文问题的方法。

## 分类
主类别: 预装软件
子类别: Office软件

## 关键词
office, PowerPoint, ppt, 无法输入中文, 输入中文

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**故障现象：**

遇到一个奇怪的问题，没办法在PowerPoint2007幻灯片里输入汉字了，但数字、英文的输入都很正常。怎么回事？我使用的是WindowsXP操作系统。  
  
**解决方案：**

我们可以检查一下这个问题是不是因“高级文字服务”被关闭而导致的。

从开始菜单找到“控制面板”，双击“区域和语言选项”。

  
![](https://webdoc.lenovo.com.cn/lenovowsi/20120412/1334222147593_550.png)

![](https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160111/1452505550130674.png)  
  
在弹出的窗口中，切换到“**语言”**[选项卡](http://iknow.lenovo.com/knowledgeDetail.html?knowledgeId=17796)，单击"**详细信息**"按钮。  
  
![](https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160111/1452505550779025.png)  
  
进入"**文字服务和输入语言**"设置窗口，单击"**高级**"选项卡，默认状态下“**关闭高级文字服务”**复选框前是没有勾选的，如果有，请将其清除。然后退出设置窗口。  
  
![](https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160111/1452505551281325.png)

PS:如果高级文字服务总是被关闭，且无法取消。可以这么做：

到同版本的操作系统的系统盘目录windows/system32找到文件ctfmon.exe复制到对应目录。

然后到注册表中找到“HKEY\_CURRENT\_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run”项，在右栏里点击右键“新建→字符串值”命名为ctfmon.exe，赋值为“C:\\WINDOWS\\system32\\ctfmon.exe”。

<!-- 文档主题：在 PowerPoint 2007 中无法输入中文怎么办？ (知识库库编号: 7) -->
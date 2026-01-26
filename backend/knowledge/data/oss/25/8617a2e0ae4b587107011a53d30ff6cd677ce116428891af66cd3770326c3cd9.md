# 知识库 25

## 标题
Excel文件菜单及相关功能灰色不可用怎么办？

## 问题描述
删除自动记忆文件来解决使用 Excel 的时候，发现“文件”菜单下的“新建”“打开”“保存”“打印文件”等功能都显示为灰色，无法正常使用的问题。

## 分类
主类别: 预装软件
子类别: Office软件

## 关键词
Excel, 菜单, 灰色, 不可用

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
· [打开excel文件速度慢](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20150805170755726.html)                                                   · [Excel如何冻结首行首列 多行多列](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_1436496385140.html)

· [“自动保存未保存文档”功能使用简介](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20150128160017914.html)                          · [Excel 2010批量求和的应用操作](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20150128151455250.html)

· [快速处理 Excel表格中的重复数据](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20140724110937910.html)                                 · [确定当前的计算模式的说明](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20140724130914047.html)

**故障现象：**  
在使用 Excel 的时候，发现“文件”菜单下的“新建”“打开”“保存”“打印文件”等功能都显示为灰色，无法正常使用。

**解决方案：**

我们知道对于计算机来说，所有的改动都要保存，如果不保存的话电脑是不会自动记忆用户做的改动的。Excel 也一样，虽然它没有弹出保存提示，但实际上它已经在一个文件中写下了这个改动，这个文件就是“Excelxx.xlb”。在 Excel 2010 中该文件名为 Excel14.xlb；如果是 Excel 2007，文件名则为 Excel12.xlb。

对于 Windows 7/Vista 操作系统，在地址栏中输入 C:\\Users\\xxx\\AppData\\Roaming\\Microsoft\\Excel （这里的XXX指代的是您的账户名称）

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341993086125_404.png)

提示：AppData 文件夹默认为隐藏状态，您可以在 Windows Explorer 中单击“组织-文件夹和搜索选项”，在“文件夹选项”的“查看”选项卡中选择“显示隐藏的文件、文件夹和驱动器”。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341993086125_337.png)

对于 Windows XP 操作系统，在地址栏输入 C:\\Documents and Settings\\Administrator\\Application Data\\Microsoft\\Excel，找到.xlb 文件，将其删除后重启 Excel 就可以了。这个方法可以帮助我们解决一些不良操作引起的问题。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341993086125_225.png)  
来源：[微软知识库](http://support.microsoft.com/kb/2724096/zh-cn)

<!-- 文档主题：Excel文件菜单及相关功能灰色不可用怎么办？ (知识库库编号: 25) -->
# 知识库 34

## 标题
Excel表导入 Access 2010 后时间显示错误怎么办?

## 问题描述
在 Access 2010 中导入了一个 Excel 表，导入时选择的是“通过创建链接表来链接到数据源”。导入后发现原本在 Excel 中正确显示的日期和时间都变成了数值，且数据类型无法修改。通过下面这篇文章教您如何操作…

## 分类
主类别: 预装软件
子类别: Office软件

## 关键词
Excel, 导入, Access, 时间, 显示错误, 2010

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**相关文章：**

[打开excel文件速度慢](http://support.lenovo.com.cn/lenovo/wsi/htmls/detail_20150805170755726.html)

[Excel如何冻结首行首列 多行多列](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_1436496385140.html)

[“自动保存未保存文档”功能使用简介](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20150128160017914.html)

[Excel 2010批量求和的应用操作](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20150128151455250.html)

[快速处理 Excel表格中的重复数据](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20140724110937910.html)

[确定当前的计算模式的说明](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20140724130914047.html)

**故障现象：**

Excel 表导入 Access 2010 后时间显示错误。

**解决方案：**

在 Access 2010 中导入了一个 Excel 表，导入时选择的是“通过创建链接表来链接到数据源”。导入后发现原本在 Excel 中正确显示的日期和时间都变成了数值，且数据类型无法修改。如下图所示：

![](https://webdoc.lenovo.com.cn/lenovowsi/new_cskb/uploadfile/20130313145619001.gif)

为了正确显示出时间格式，我们可以在 Excel 文件里手动更改时间字段的格式。

在 Excel 文件时间格式的字段后面插入两列如下图中的C列、D列，在C列里输入公式：=IF（B1=""""TEXT（B1"hh:mm"））

回车后，C列会显示相同的时间，但是该单元格的格式已经不是“时间”格式了。拖拽选中的C1单元格右下方的“十”字，使整列都更改格式。如下图：

![](https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160111/1452505503609330.png)

选中C列，复制到D列。此时D列显示的时间也不是“时间”格式的。最后，删除B列和C列。

![](https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160111/1452505503425733.png)

然后用 Access 链接该 Excel 文件，就可以正常显示时间了。

来源：[**微软知识库>>**](https://support.microsoft.com/zh-cn/kb/2730403)

<!-- 文档主题：Excel表导入 Access 2010 后时间显示错误怎么办? (知识库库编号: 34) -->
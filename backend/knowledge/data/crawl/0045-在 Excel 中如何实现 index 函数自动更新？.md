# 知识库 45

## 标题
在 Excel 中如何实现 index 函数自动更新？

## 问题描述
宏表函数 GET.WORKBOOK（1） 在数据变动时不会自动重算，目录无法自动更新。怎么办呢？下文将指导实现在 Excel 中如何实现 index 函数自动更新的方法。

## 分类
主类别: 预装软件
子类别: Office软件

## 关键词
Excel, index, 函数, 自动更新

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**相关文章：**

[打开excel文件速度慢](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20150805170755726.html)

[Excel如何冻结首行首列 多行多列](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_1436496385140.html)

[“自动保存未保存文档”功能使用简介](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20150128160017914.html)

[Excel 2010批量求和的应用操作](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20150128151455250.html)

[快速处理 Excel表格中的重复数据](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20140724110937910.html)

[确定当前的计算模式的说明](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_20140724130914047.html)

  以工作簿目录为例，如果要为工作表（sheet）做一个目录，我们会使用函数：=INDEX（GET.WORKBOOK（1）,!$A1）

公式中 GET.WORKBOOK（1） 用于提取当前工作簿中所有工作表名称，INDEX 函数会按 A1 中的数字决定要显示第几张工作表的名称。

但由于宏表函数 GET.WORKBOOK（1） 在数据变动时不会自动重算，目录无法自动更新。怎么办呢？

这时，我们可以使用易失性函数。例如表示当前时间的函数 NOW（），借助于当前时间的不断变化来实现对任何变化的强制计算。再加上函数 T（），将 NOW（） 产生的数值转为空文本以免影响原公式结果。

所以改进后的 index 函数表现为：=INDEX（GET.WORKBOOK（1）,!$A1）&T（NOW（））

注：宏表函数 GET.WORKBOOK，不能直接在单元格公式中使用，必须通过才能起作用。

具体如下：

1. 如图所示，选中 B1 单元格，切换到“**公式**”选项卡，单击“**定义名称**”。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344242244805_87.png)

  2.在弹出的新建名称窗口中输入名称，如“**目录**”。在引用位置中则输入公式=INDEX（GET.WORKBOOK（1）,!$A1）&T（NOW（）），单击“**确定**”即可定义出一个名为“**目录**”的名称。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344242244805_841.png)

  3.回到当前页面后，选中 B1 单元格，在“**用于公式**”下拉菜单中，单击刚刚新建的“**目录**”公式。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344242244805_307.png)

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344242244805_295.png)

  4.单击单元格右下角的十字形图标下拉拖出很多行（有几个 sheet 就拖出几行）。这时候在 B1 到 Bn 行，会显示出每个 sheet 的字符串名称。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344242244805_639.png)

来源：[微软知识库](http://support.microsoft.com/kb/2739262/zh-cn)

<!-- 文档主题：在 Excel 中如何实现 index 函数自动更新？ (知识库库编号: 45) -->
# 知识库 313

## 标题
Microsoft Visual C++运行库下载与安装方法

## 问题描述
Microsoft Visual C++是非常常用的运行库，下文将指导Microsoft Visual C++运行库下载与安装方法。

## 分类
主类别: 操作系统故障
子类别: 系统应用操作

## 关键词
显示屏, 管理, 设置, 显示, 硬件, Windows, 查看, Visual C++, 运行库

## 元信息
创建时间:2024-12-15|版本:3.0

## 解决方案
微软官方下载链接：<https://learn.microsoft.com/zh-cn/cpp/windows/latest-supported-vc-redist?view=msvc-170>

正常仅安装X86和X64即可，详见红框

![Microsoft Visual C++-1.png](https://chinakb.lenovo.com.cn/chinakb/prod-api/file/downloadFile?key=uniko/IMAGE/9cc5118a92fdc3355f38d26aad14af82-1728525463487.png&name=Microsoft Visual C++-1.png)

**注意：**

若机器已经安装Microsoft Visual C++ 2015、2015-2017、2015-2019则无法直接安装Microsoft Visual C++2015-2022，需卸载当前冲突的版本后重新安装最新的2015-2022；

此下载链接内也有Microsoft Visual C++2013、2012、2010、2008等早期版本，如需下载这些版本，下拉查找需要的即可；

Microsoft Visual C++组件并不需要都安装，相关软件检测组件缺失时会进行提示，安装对应版本即可；

**说明：**

以VC++2013为例，以下组件缺少，均为VC++2013异常（140缺少VC++2015-2022、120缺少VC++2013、110缺少VC++2012、100缺少VC++2010、90缺少VC++2008）

msvcr120.dll

msvcp120.dll

vcamp120.dll

vcomp120.dll

vccorlib120.dll

mfc120.dll

mfc120u.dll

mfc120chs.dll

mfc120cht.dll

mfc120deu.dll

mfc120enu.dll

mfc120esn.dll

mfc120fra.dll

mfc120ita.dll

mfc120jpn.dll

mfc120kor.dll

mfc120rus.dll

**安装步骤：**

1、勾选“我同意许可条款和条件”后点击“安装”按钮。

**![Microsoft Visual C++-2.png](https://chinakb.lenovo.com.cn/chinakb/prod-api/file/downloadFile?key=uniko/IMAGE/0f6a1f9d336739a942ef5c1a69a2c004-1728525485269.png&name=Microsoft Visual C++-2.png)**

2、自动安装过程，显示设置成功后点击“关闭”按钮就完成了安装。

![Microsoft Visual C++-3.png](https://chinakb.lenovo.com.cn/chinakb/prod-api/file/downloadFile?key=uniko/IMAGE/1fbeb4aee99351106997a120b4242283-1728525587037.png&name=Microsoft Visual C++-3.png)

![Microsoft Visual C++-4.png](https://chinakb.lenovo.com.cn/chinakb/prod-api/file/downloadFile?key=uniko/IMAGE/15228393a36e430e90582afb3b13591c-1728525595590.png&name=Microsoft Visual C++-4.png)

<!-- 文档主题：Microsoft Visual C++运行库下载与安装方法  (知识库库编号: 313) -->
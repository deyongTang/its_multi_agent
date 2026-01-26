# 知识库 437040

## 标题
如何查看Windows 10/11系统密钥

## 问题描述
Windows 密钥查询避坑指南！明确预装与当前系统密钥差异，分别给出 PowerShell 命令、注册表路径两种查询方式，重点强调密钥保密原则及注册表操作的数据备份要点，规避操作风险。

## 分类
主类别: 操作系统故障
子类别: 系统应用操作

## 关键词
系统密钥, 密钥, OA3, 产品密钥, 激活码

## 元信息
创建时间:2026-01-16|版本:1.0

## 解决方案
**注意事项**
--------

Windows产品密钥非必要无需单独读取或查询，***请谨慎提供Windows系统激活密钥给他人***

查看系统密钥分预装系统密钥和当前系统密钥，预装系统密钥一般为OEM厂商将密钥信息直接写入主板信息中，当前系统密钥为当前安装的Windows系统使用的密钥，密钥为25位字母数字组合；

**操作方案涉及注册表或相关命令，请谨慎操作，可备份数据后再操作，以免操作错误导致数据丢失；**

**预装密钥**
--------

右击开始菜单，或者使用Win+X快捷键，找到终端/PowerShell打开，输入以下字符后回车即可查询主板密钥，注意大小写、空格以及相关字符格式，建议直接复制；

***(Get-WmiObject -query ‘select \* from SoftwareLicensingService’).OA3xOriginalProductKey***

![](https://chinakb.lenovo.com.cn/chinakb/prod-api/file/downloadFile?key=uniko/IMAGE/17dba203d97f55775f6ddc78e02fdb9b-1768544896498.png&name=mceclip0.png)

**当前密钥**
--------

Win+R输入regedit打开注册表或直接在搜索栏搜索“注册表”打开

复制以下路径展开注册表

***计算机\HKEY\_LOCAL\_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform***

找到BackupProductKeyDefault字段，后面的内容就是当前系统密钥

***![](https://chinakb.lenovo.com.cn/chinakb/prod-api/file/downloadFile?key=uniko/IMAGE/b4f4a3e71d14c6e654836bbd824b7cb9-1768545093682.png&name=mceclip1.png)***

<!-- 文档主题：如何查看Windows 10/11系统密钥 (知识库库编号: 437040) -->